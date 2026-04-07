"""
The Oracle Protocol - Smart Contract SmartPy
Marché de prédictions avec système ELO et niveaux de confiance.
Déploiement cible : Ghostnet (testnet Tezos)
"""

import smartpy as sp


# ---------------------------------------------------------------------------
# Types & Constantes
# ---------------------------------------------------------------------------

CONFIDENCE_LEVELS = {50: 1, 75: 2, 95: 3}   # niveau → multiplicateur ELO
PLATFORM_FEE_PCT  = sp.nat(2)                 # 2 % alimentant le pool de bonus
ELO_INITIAL       = sp.int(1000)
ELO_K_FACTOR      = sp.int(32)               # amplitude maximale d'un changement ELO

# Statuts d'une prédiction
STATUS_OPEN     = sp.nat(0)
STATUS_CLOSED   = sp.nat(1)   # deadline dépassée, en attente de résolution
STATUS_RESOLVED = sp.nat(2)


# ---------------------------------------------------------------------------
# Types enregistrés
# ---------------------------------------------------------------------------

TBet = sp.TRecord(
    bettor     = sp.TAddress,
    choice     = sp.TNat,        # index de l'option choisie
    amount     = sp.TMutez,
    confidence = sp.TNat,        # 50 | 75 | 95
    claimed    = sp.TBool,
)

TPrediction = sp.TRecord(
    creator      = sp.TAddress,
    description  = sp.TString,
    deadline     = sp.TTimestamp,
    options      = sp.TList(sp.TString),
    status       = sp.TNat,
    winning_option = sp.TOption(sp.TNat),
    total_pool   = sp.TMutez,
    bets         = sp.TMap(sp.TNat, TBet),   # bet_index → Bet
    bet_count    = sp.TNat,
)


# ---------------------------------------------------------------------------
# Contrat principal
# ---------------------------------------------------------------------------

class OracleProtocol(sp.Contract):
    def __init__(self, admin: sp.TAddress):
        self.init(
            admin            = admin,
            elo_scores       = sp.cast(sp.map(), sp.TMap(sp.TAddress, sp.TInt)),
            predictions      = sp.cast(sp.map(), sp.TMap(sp.TNat, TPrediction)),
            prediction_count = sp.nat(0),
            bonus_pool       = sp.mutez(0),
            oracle_address   = admin,   # adresse autorisée à résoudre les prédictions
        )

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    @sp.private(with_storage="read-write")
    def _get_or_init_elo(self, addr: sp.TAddress) -> sp.TInt:
        """Retourne le score ELO d'une adresse, l'initialise à 1000 si nouveau."""
        if addr not in self.data.elo_scores:
            self.data.elo_scores[addr] = ELO_INITIAL
        return self.data.elo_scores[addr]

    @sp.private(with_storage="read-write")
    def _update_elo(self, params: sp.TRecord(
        addr       = sp.TAddress,
        won        = sp.TBool,
        confidence = sp.TNat,
    )):
        """
        Mise à jour ELO après résolution.

        Formule simplifiée :
          delta = K * multiplier * (actual - expected)
          actual  = 1.0 si gagné, 0.0 si perdu
          expected = 0.5 (adversaire théorique à force égale)
          multiplier = confidence / 50  (1x, 1.5x, 1.9x)
        """
        current_elo = self._get_or_init_elo(params.addr)

        # Multiplier en base 100 pour éviter les flottants
        # confidence 50 → mult=100, 75 → mult=150, 95 → mult=190
        multiplier = sp.compute(sp.to_int(params.confidence) * 2)

        # K * multiplier (base 100) / 100
        k_scaled = sp.compute(ELO_K_FACTOR * multiplier)

        # actual : 100 si gagné, 0 si perdu  (base 100)
        actual = sp.int(100) if params.won else sp.int(0)

        # expected = 50 (base 100)
        expected = sp.int(50)

        # delta = K_scaled * (actual - expected) / 100 / 100
        delta = (k_scaled * (actual - expected)) // sp.int(10000)

        self.data.elo_scores[params.addr] = current_elo + delta

    # ------------------------------------------------------------------
    # Entrypoint : create_prediction
    # ------------------------------------------------------------------

    @sp.entrypoint
    def create_prediction(self, params: sp.TRecord(
        description = sp.TString,
        deadline    = sp.TTimestamp,
        options     = sp.TList(sp.TString),
    )):
        """Crée une nouvelle prédiction."""
        assert sp.len(params.options) >= sp.nat(2), "Au moins 2 options requises"
        assert params.deadline > sp.now, "La deadline doit être dans le futur"

        prediction_id = self.data.prediction_count

        new_prediction = sp.record(
            creator        = sp.sender,
            description    = params.description,
            deadline       = params.deadline,
            options        = params.options,
            status         = STATUS_OPEN,
            winning_option = None,
            total_pool     = sp.mutez(0),
            bets           = sp.cast(sp.map(), sp.TMap(sp.TNat, TBet)),
            bet_count      = sp.nat(0),
        )

        self.data.predictions[prediction_id] = new_prediction
        self.data.prediction_count += sp.nat(1)

    # ------------------------------------------------------------------
    # Entrypoint : place_bet
    # ------------------------------------------------------------------

    @sp.entrypoint
    def place_bet(self, params: sp.TRecord(
        prediction_id = sp.TNat,
        choice        = sp.TNat,
        confidence    = sp.TNat,
    )):
        """Place une mise sur une prédiction."""
        assert params.confidence == sp.nat(50) or \
               params.confidence == sp.nat(75) or \
               params.confidence == sp.nat(95), \
               "Confiance invalide : 50, 75 ou 95 uniquement"

        assert sp.amount > sp.mutez(0), "La mise doit être > 0"

        pred = self.data.predictions[params.prediction_id]

        assert pred.status == STATUS_OPEN, "La prédiction n'est plus ouverte"
        assert pred.deadline > sp.now, "La deadline est dépassée"

        # Vérifier que le choix est un index d'option valide
        options_list = sp.compute(pred.options)
        assert params.choice < sp.len(options_list), "Choix invalide"

        # Prélèvement de la plateforme (2%)
        fee_mutez = sp.split_tokens(sp.amount, PLATFORM_FEE_PCT, sp.nat(100))
        bet_amount = sp.amount - fee_mutez

        self.data.bonus_pool += fee_mutez

        bet_index = pred.bet_count
        new_bet = sp.record(
            bettor     = sp.sender,
            choice     = params.choice,
            amount     = bet_amount,
            confidence = params.confidence,
            claimed    = False,
        )

        self.data.predictions[params.prediction_id].bets[bet_index]   = new_bet
        self.data.predictions[params.prediction_id].bet_count        += sp.nat(1)
        self.data.predictions[params.prediction_id].total_pool       += bet_amount

    # ------------------------------------------------------------------
    # Entrypoint : resolve_prediction
    # ------------------------------------------------------------------

    @sp.entrypoint
    def resolve_prediction(self, params: sp.TRecord(
        prediction_id  = sp.TNat,
        winning_option = sp.TNat,
    )):
        """Résout une prédiction (oracle uniquement)."""
        assert sp.sender == self.data.oracle_address, "Accès non autorisé"

        pred = self.data.predictions[params.prediction_id]
        assert pred.status == STATUS_OPEN or pred.status == STATUS_CLOSED, \
               "Prédiction déjà résolue"

        options_list = sp.compute(pred.options)
        assert params.winning_option < sp.len(options_list), "Option gagnante invalide"

        self.data.predictions[params.prediction_id].status = STATUS_RESOLVED
        self.data.predictions[params.prediction_id].winning_option = sp.Some(
            params.winning_option
        )

        # Mise à jour ELO pour chaque parieur
        with sp.for_("bet_idx", sp.range(sp.nat(0), pred.bet_count)) as bet_idx:
            bet = pred.bets[bet_idx]
            won = bet.choice == params.winning_option
            self._update_elo(sp.record(
                addr       = bet.bettor,
                won        = won,
                confidence = bet.confidence,
            ))

    # ------------------------------------------------------------------
    # Entrypoint : claim_reward
    # ------------------------------------------------------------------

    @sp.entrypoint
    def claim_reward(self, params: sp.TRecord(
        prediction_id = sp.TNat,
        bet_index     = sp.TNat,
    )):
        """Réclame les gains d'un pari gagnant."""
        pred = self.data.predictions[params.prediction_id]
        assert pred.status == STATUS_RESOLVED, "Prédiction non résolue"

        bet = pred.bets[params.bet_index]
        assert bet.bettor == sp.sender, "Ce pari ne vous appartient pas"
        assert not bet.claimed, "Gains déjà réclamés"

        winning_option = sp.compute(pred.winning_option.open_some("Pas de gagnant"))
        assert bet.choice == winning_option, "Pari perdant"

        # Calcul du pool gagné
        # Somme des mises gagnantes
        winning_pool = sp.local("winning_pool", sp.mutez(0))
        with sp.for_("b_idx", sp.range(sp.nat(0), pred.bet_count)) as b_idx:
            b = pred.bets[b_idx]
            if b.choice == winning_option:
                winning_pool.value += b.amount

        # Part proportionnelle + multiplicateur de confiance
        # reward_base = total_pool * (bet.amount / winning_pool)
        # reward      = reward_base * confidence_multiplier / base_multiplier
        #
        # Multiplicateurs : 50→1, 75→2, 95→3
        conf_mult = sp.local("conf_mult", sp.nat(1))
        if bet.confidence == sp.nat(75):
            conf_mult.value = sp.nat(2)
        if bet.confidence == sp.nat(95):
            conf_mult.value = sp.nat(3)

        # base reward (sans bonus de confiance)
        # = total_pool * bet.amount / winning_pool
        base_reward = sp.split_tokens(
            pred.total_pool,
            sp.utils.mutez_to_nat(bet.amount),
            sp.utils.mutez_to_nat(winning_pool.value),
        )

        # bonus de confiance : on ajoute (conf_mult - 1) * base_reward / 2
        # issu du bonus_pool pour ne pas déséquilibrer le pool principal
        extra_bonus = sp.split_tokens(base_reward, conf_mult.value - sp.nat(1), sp.nat(2))

        # S'assurer que le bonus pool est suffisant
        actual_bonus = sp.local("actual_bonus", sp.mutez(0))
        if self.data.bonus_pool >= extra_bonus:
            actual_bonus.value = extra_bonus
            self.data.bonus_pool -= extra_bonus

        total_reward = base_reward + actual_bonus.value

        # Marquer comme réclamé
        self.data.predictions[params.prediction_id].bets[params.bet_index].claimed = True

        # Envoi des gains
        sp.send(sp.sender, total_reward)

    # ------------------------------------------------------------------
    # Entrypoint : close_prediction (automatisable via oracle)
    # ------------------------------------------------------------------

    @sp.entrypoint
    def close_prediction(self, prediction_id: sp.TNat):
        """Marque une prédiction comme fermée (deadline dépassée)."""
        assert sp.sender == self.data.oracle_address, "Accès non autorisé"
        pred = self.data.predictions[prediction_id]
        assert pred.status == STATUS_OPEN, "Prédiction non ouverte"
        assert pred.deadline <= sp.now, "Deadline pas encore dépassée"
        self.data.predictions[prediction_id].status = STATUS_CLOSED

    # ------------------------------------------------------------------
    # Entrypoint : update_oracle (admin)
    # ------------------------------------------------------------------

    @sp.entrypoint
    def update_oracle(self, new_oracle: sp.TAddress):
        """Met à jour l'adresse de l'oracle résolveur."""
        assert sp.sender == self.data.admin, "Admin uniquement"
        self.data.oracle_address = new_oracle

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    @sp.onchain_view()
    def get_elo(self, addr: sp.TAddress) -> sp.TInt:
        """Retourne le score ELO d'une adresse."""
        if addr in self.data.elo_scores:
            return self.data.elo_scores[addr]
        return ELO_INITIAL

    @sp.onchain_view()
    def get_prediction(self, prediction_id: sp.TNat) -> TPrediction:
        """Retourne les données d'une prédiction."""
        return self.data.predictions[prediction_id]

    @sp.onchain_view()
    def get_prediction_count(self) -> sp.TNat:
        """Retourne le nombre total de prédictions."""
        return self.data.prediction_count

    @sp.onchain_view()
    def get_bonus_pool(self) -> sp.TMutez:
        """Retourne le montant du pool de bonus."""
        return self.data.bonus_pool


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------

if "templates" not in __name__:
    admin_address = sp.address("tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb")
    sp.add_compilation_target(
        "oracle_protocol",
        OracleProtocol(admin=admin_address),
    )
