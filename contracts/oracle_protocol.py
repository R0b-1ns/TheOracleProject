"""
The Oracle Protocol - Smart Contract SmartPy
Marché de prédictions avec système ELO et niveaux de confiance.
Déploiement cible : Ghostnet (testnet Tezos)
"""

import smartpy as sp


# ---------------------------------------------------------------------------
# Constantes (valeurs Python pures — pas de sp.nat/sp.int au niveau module)
# ---------------------------------------------------------------------------

PLATFORM_FEE_NUM = 2    # numérateur frais 2 %
PLATFORM_FEE_DEN = 100
ELO_INITIAL_VAL  = 1000
ELO_K_FACTOR_VAL = 32

# Statuts d'une prédiction (nats Python)
STATUS_OPEN     = 0
STATUS_CLOSED   = 1
STATUS_RESOLVED = 2


# ---------------------------------------------------------------------------
# Types enregistrés
# ---------------------------------------------------------------------------

TBet = sp.TRecord(
    bettor     = sp.TAddress,
    choice     = sp.TNat,
    amount     = sp.TMutez,
    confidence = sp.TNat,   # 50 | 75 | 95
    claimed    = sp.TBool,
)

TPrediction = sp.TRecord(
    creator        = sp.TAddress,
    description    = sp.TString,
    deadline       = sp.TTimestamp,
    options        = sp.TList(sp.TString),
    status         = sp.TNat,
    winning_option = sp.TOption(sp.TNat),
    total_pool     = sp.TMutez,
    bets           = sp.TMap(sp.TNat, TBet),
    bet_count      = sp.TNat,
)


# ---------------------------------------------------------------------------
# Contrat principal
# ---------------------------------------------------------------------------

class OracleProtocol(sp.Contract):
    def __init__(self, admin):
        self.init(
            admin            = admin,
            elo_scores       = sp.cast(sp.map(), sp.TMap(sp.TAddress, sp.TInt)),
            predictions      = sp.cast(sp.map(), sp.TMap(sp.TNat, TPrediction)),
            prediction_count = sp.nat(0),
            bonus_pool       = sp.mutez(0),
            oracle_address   = admin,
        )

    # ------------------------------------------------------------------
    # Helper : mise à jour ELO (méthode Python ordinaire)
    # ------------------------------------------------------------------

    def _update_elo(self, addr, won, confidence):
        """
        delta = K(32) × (confidence×2/100) × (résultat − 0.5)
        Tout en entiers base-10000 pour éviter les flottants.
        """
        # Initialiser l'ELO si c'est un nouveau joueur
        if ~self.data.elo_scores.contains(addr):
            self.data.elo_scores[addr] = sp.int(ELO_INITIAL_VAL)

        current_elo = self.data.elo_scores[addr]

        # multiplier = confidence * 2  (50→100, 75→150, 95→190)
        multiplier = sp.compute(sp.to_int(confidence) * sp.int(2))

        # k_scaled = K * multiplier
        k_scaled = sp.compute(sp.int(ELO_K_FACTOR_VAL) * multiplier)

        # actual : 100 si gagné, 0 si perdu (base 100)
        actual = sp.local("actual", sp.int(0))
        if won:
            actual.value = sp.int(100)

        # expected = 50 (base 100)
        # delta = k_scaled * (actual - 50) / 10000
        delta = sp.compute(
            (k_scaled * (actual.value - sp.int(50))) // sp.int(10000)
        )

        self.data.elo_scores[addr] = current_elo + delta

    # ------------------------------------------------------------------
    # Entrypoint : create_prediction
    # ------------------------------------------------------------------

    @sp.entrypoint
    def create_prediction(self, params):
        """Crée une nouvelle prédiction.
        params : { description: string, deadline: timestamp, options: list(string) }
        """
        sp.cast(params, sp.TRecord(
            description = sp.TString,
            deadline    = sp.TTimestamp,
            options     = sp.TList(sp.TString),
        ))
        assert sp.len(params.options) >= 2, "Au moins 2 options requises"
        assert params.deadline > sp.now, "La deadline doit etre dans le futur"

        prediction_id = self.data.prediction_count

        self.data.predictions[prediction_id] = sp.record(
            creator        = sp.sender,
            description    = params.description,
            deadline       = params.deadline,
            options        = params.options,
            status         = sp.nat(STATUS_OPEN),
            winning_option = sp.none,
            total_pool     = sp.mutez(0),
            bets           = sp.cast(sp.map(), sp.TMap(sp.TNat, TBet)),
            bet_count      = sp.nat(0),
        )
        self.data.prediction_count += 1

    # ------------------------------------------------------------------
    # Entrypoint : place_bet
    # ------------------------------------------------------------------

    @sp.entrypoint
    def place_bet(self, params):
        """Place une mise sur une prédiction.
        params : { prediction_id: nat, choice: nat, confidence: nat }
        """
        sp.cast(params, sp.TRecord(
            prediction_id = sp.TNat,
            choice        = sp.TNat,
            confidence    = sp.TNat,
        ))
        assert (
            (params.confidence == sp.nat(50)) |
            (params.confidence == sp.nat(75)) |
            (params.confidence == sp.nat(95))
        ), "Confiance invalide : 50, 75 ou 95"

        assert sp.amount > sp.mutez(0), "La mise doit etre > 0"

        pred = self.data.predictions[params.prediction_id]
        assert pred.status == sp.nat(STATUS_OPEN), "Prediction non ouverte"
        assert pred.deadline > sp.now, "Deadline depassee"
        assert params.choice < sp.len(pred.options), "Choix invalide"

        # Frais plateforme 2 %
        fee    = sp.split_tokens(sp.amount, sp.nat(PLATFORM_FEE_NUM), sp.nat(PLATFORM_FEE_DEN))
        net    = sp.amount - fee
        self.data.bonus_pool += fee

        bet_index = pred.bet_count
        self.data.predictions[params.prediction_id].bets[bet_index] = sp.record(
            bettor     = sp.sender,
            choice     = params.choice,
            amount     = net,
            confidence = params.confidence,
            claimed    = False,
        )
        self.data.predictions[params.prediction_id].bet_count  += 1
        self.data.predictions[params.prediction_id].total_pool += net

    # ------------------------------------------------------------------
    # Entrypoint : resolve_prediction
    # ------------------------------------------------------------------

    @sp.entrypoint
    def resolve_prediction(self, params):
        """Résout une prédiction (oracle uniquement).
        params : { prediction_id: nat, winning_option: nat }
        """
        sp.cast(params, sp.TRecord(
            prediction_id  = sp.TNat,
            winning_option = sp.TNat,
        ))
        assert sp.sender == self.data.oracle_address, "Acces non autorise"

        pred = self.data.predictions[params.prediction_id]
        assert (
            (pred.status == sp.nat(STATUS_OPEN)) |
            (pred.status == sp.nat(STATUS_CLOSED))
        ), "Prediction deja resolue"
        assert params.winning_option < sp.len(pred.options), "Option gagnante invalide"

        self.data.predictions[params.prediction_id].status         = sp.nat(STATUS_RESOLVED)
        self.data.predictions[params.prediction_id].winning_option = sp.some(params.winning_option)

        # Mise à jour ELO pour chaque parieur
        with sp.for_("bet_idx", sp.range(0, pred.bet_count)) as bet_idx:
            bet = pred.bets[bet_idx]
            won = bet.choice == params.winning_option
            self._update_elo(bet.bettor, won, bet.confidence)

    # ------------------------------------------------------------------
    # Entrypoint : claim_reward
    # ------------------------------------------------------------------

    @sp.entrypoint
    def claim_reward(self, params):
        """Réclame les gains d'un pari gagnant.
        params : { prediction_id: nat, bet_index: nat }
        """
        sp.cast(params, sp.TRecord(
            prediction_id = sp.TNat,
            bet_index     = sp.TNat,
        ))
        pred = self.data.predictions[params.prediction_id]
        assert pred.status == sp.nat(STATUS_RESOLVED), "Prediction non resolue"

        bet = pred.bets[params.bet_index]
        assert bet.bettor == sp.sender,  "Ce pari ne vous appartient pas"
        assert ~bet.claimed,             "Gains deja reclames"

        winning_option = pred.winning_option.open_some("Pas de gagnant")
        assert bet.choice == winning_option, "Pari perdant"

        # Somme des mises gagnantes
        winning_pool = sp.local("winning_pool", sp.mutez(0))
        with sp.for_("b_idx", sp.range(0, pred.bet_count)) as b_idx:
            b = pred.bets[b_idx]
            if b.choice == winning_option:
                winning_pool.value += b.amount

        # Reward de base = total_pool × (mise / winning_pool)
        base_reward = sp.split_tokens(
            pred.total_pool,
            sp.utils.mutez_to_nat(bet.amount),
            sp.utils.mutez_to_nat(winning_pool.value),
        )

        # Bonus confiance depuis le bonus_pool
        # conf_mult : 50→0, 75→1, 95→2  (numérateur du bonus)
        conf_num = sp.local("conf_num", sp.nat(0))
        if bet.confidence == sp.nat(75):
            conf_num.value = sp.nat(1)
        if bet.confidence == sp.nat(95):
            conf_num.value = sp.nat(2)

        extra_bonus  = sp.split_tokens(base_reward, conf_num.value, sp.nat(2))
        actual_bonus = sp.local("actual_bonus", sp.mutez(0))
        if self.data.bonus_pool >= extra_bonus:
            actual_bonus.value   = extra_bonus
            self.data.bonus_pool -= extra_bonus

        total_reward = base_reward + actual_bonus.value

        self.data.predictions[params.prediction_id].bets[params.bet_index].claimed = True
        sp.send(sp.sender, total_reward)

    # ------------------------------------------------------------------
    # Entrypoint : close_prediction
    # ------------------------------------------------------------------

    @sp.entrypoint
    def close_prediction(self, prediction_id):
        """Ferme une prédiction après la deadline (oracle uniquement)."""
        sp.cast(prediction_id, sp.TNat)
        assert sp.sender == self.data.oracle_address, "Acces non autorise"
        pred = self.data.predictions[prediction_id]
        assert pred.status == sp.nat(STATUS_OPEN), "Prediction non ouverte"
        assert pred.deadline <= sp.now,             "Deadline pas encore depassee"
        self.data.predictions[prediction_id].status = sp.nat(STATUS_CLOSED)

    # ------------------------------------------------------------------
    # Entrypoint : update_oracle
    # ------------------------------------------------------------------

    @sp.entrypoint
    def update_oracle(self, new_oracle):
        """Met à jour l'adresse de l'oracle résolveur (admin uniquement)."""
        sp.cast(new_oracle, sp.TAddress)
        assert sp.sender == self.data.admin, "Admin uniquement"
        self.data.oracle_address = new_oracle

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    @sp.onchain_view()
    def get_elo(self, addr):
        sp.cast(addr, sp.TAddress)
        if self.data.elo_scores.contains(addr):
            sp.result(self.data.elo_scores[addr])
        else:
            sp.result(sp.int(ELO_INITIAL_VAL))

    @sp.onchain_view()
    def get_prediction(self, prediction_id):
        sp.cast(prediction_id, sp.TNat)
        sp.result(self.data.predictions[prediction_id])

    @sp.onchain_view()
    def get_prediction_count(self):
        sp.result(self.data.prediction_count)

    @sp.onchain_view()
    def get_bonus_pool(self):
        sp.result(self.data.bonus_pool)


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------

if "templates" not in __name__:
    admin_address = sp.address("tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb")
    sp.add_compilation_target(
        "oracle_protocol",
        OracleProtocol(admin=admin_address),
    )
