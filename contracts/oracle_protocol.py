"""
The Oracle Protocol - Smart Contract SmartPy
Marché de prédictions avec système ELO et niveaux de confiance.
Déploiement cible : Ghostnet (testnet Tezos)

Compatible SmartPy >= 0.18 (nouvelle API, syntaxe @sp.module obligatoire)
"""

import smartpy as sp


# ---------------------------------------------------------------------------
# Module SmartPy — tout le code contrat DOIT être ici
# ---------------------------------------------------------------------------

@sp.module
def main():

    # Statuts (Python int, coercés en sp.nat lors des comparaisons)
    STATUS_OPEN     = 0
    STATUS_CLOSED   = 1
    STATUS_RESOLVED = 2

    # Paramètres ELO
    ELO_INITIAL  = 1000
    ELO_K_FACTOR = 32

    class OracleProtocol(sp.Contract):
        def __init__(self, admin):
            # Nouvelle API : self.data.field = value  (plus de self.init())
            self.data.admin            = admin
            self.data.oracle_address   = admin
            self.data.prediction_count = sp.nat(0)
            self.data.bonus_pool       = sp.mutez(0)
            self.data.elo_scores       = sp.cast(
                {},
                sp.map[sp.address, sp.int],
            )
            self.data.predictions      = sp.cast(
                {},
                sp.map[sp.nat, sp.record(
                    creator        = sp.address,
                    description    = sp.string,
                    deadline       = sp.timestamp,
                    options        = sp.list[sp.string],
                    status         = sp.nat,
                    winning_option = sp.option[sp.nat],
                    total_pool     = sp.mutez,
                    bets           = sp.map[sp.nat, sp.record(
                        bettor     = sp.address,
                        choice     = sp.nat,
                        amount     = sp.mutez,
                        confidence = sp.nat,
                        claimed    = sp.bool,
                    )],
                    bet_count      = sp.nat,
                )],
            )

        # ------------------------------------------------------------------
        # Helper privé : mise à jour ELO
        # @sp.private fonctionne uniquement à l'intérieur de @sp.module
        # ------------------------------------------------------------------

        @sp.private(with_storage="read-write")
        def _update_elo(self, addr, won, confidence):
            """
            delta = K(32) × (confidence×2) × (résultat − 50) ÷ 10000
            Base 100 : résultat=100 si gagné, 0 si perdu, expected=50
            """
            if not self.data.elo_scores.contains(addr):
                self.data.elo_scores[addr] = sp.int(ELO_INITIAL)

            current = self.data.elo_scores[addr]
            mult    = sp.to_int(confidence) * sp.int(2)   # 50→100 | 75→150 | 95→190
            k       = sp.int(ELO_K_FACTOR) * mult

            actual = sp.int(0)
            if won:
                actual = sp.int(100)

            delta = k * (actual - sp.int(50)) // sp.int(10000)
            self.data.elo_scores[addr] = current + delta

        # ------------------------------------------------------------------
        # Entrypoint : create_prediction
        # ------------------------------------------------------------------

        @sp.entrypoint
        def create_prediction(self, params):
            """Crée une nouvelle prédiction.
            params : { description: string, deadline: timestamp, options: list[string] }
            """
            sp.cast(params, sp.record(
                description = sp.string,
                deadline    = sp.timestamp,
                options     = sp.list[sp.string],
            ))
            assert sp.len(params.options) >= 2, "Au moins 2 options requises"
            assert params.deadline > sp.now,    "Deadline dans le futur requise"

            pid = self.data.prediction_count
            self.data.predictions[pid] = sp.record(
                creator        = sp.sender,
                description    = params.description,
                deadline       = params.deadline,
                options        = params.options,
                status         = sp.nat(STATUS_OPEN),
                winning_option = None,
                total_pool     = sp.mutez(0),
                bets           = sp.cast(
                    {},
                    sp.map[sp.nat, sp.record(
                        bettor     = sp.address,
                        choice     = sp.nat,
                        amount     = sp.mutez,
                        confidence = sp.nat,
                        claimed    = sp.bool,
                    )],
                ),
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
            sp.cast(params, sp.record(
                prediction_id = sp.nat,
                choice        = sp.nat,
                confidence    = sp.nat,
            ))
            assert (
                (params.confidence == sp.nat(50)) |
                (params.confidence == sp.nat(75)) |
                (params.confidence == sp.nat(95))
            ), "Confiance invalide : 50, 75 ou 95"

            assert sp.amount > sp.mutez(0), "Mise > 0 requise"

            pred = self.data.predictions[params.prediction_id]
            assert pred.status == sp.nat(STATUS_OPEN), "Prediction non ouverte"
            assert pred.deadline > sp.now,             "Deadline depassee"
            assert params.choice < sp.len(pred.options), "Choix invalide"

            # Frais plateforme 2 %
            fee = sp.split_tokens(sp.amount, sp.nat(2), sp.nat(100))
            net = sp.amount - fee
            self.data.bonus_pool += fee

            idx = pred.bet_count
            self.data.predictions[params.prediction_id].bets[idx] = sp.record(
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
            sp.cast(params, sp.record(
                prediction_id  = sp.nat,
                winning_option = sp.nat,
            ))
            assert sp.sender == self.data.oracle_address, "Oracle uniquement"

            pred = self.data.predictions[params.prediction_id]
            assert (
                (pred.status == sp.nat(STATUS_OPEN)) |
                (pred.status == sp.nat(STATUS_CLOSED))
            ), "Prediction deja resolue"
            assert params.winning_option < sp.len(pred.options), "Option invalide"

            self.data.predictions[params.prediction_id].status         = sp.nat(STATUS_RESOLVED)
            self.data.predictions[params.prediction_id].winning_option = sp.Some(params.winning_option)

            # Mise à jour ELO — itération native sur la map (nouvelle API)
            for _, bet in pred.bets.items():
                self._update_elo(
                    bet.bettor,
                    bet.choice == params.winning_option,
                    bet.confidence,
                )

        # ------------------------------------------------------------------
        # Entrypoint : claim_reward
        # ------------------------------------------------------------------

        @sp.entrypoint
        def claim_reward(self, params):
            """Réclame les gains d'un pari gagnant.
            params : { prediction_id: nat, bet_index: nat }
            """
            sp.cast(params, sp.record(
                prediction_id = sp.nat,
                bet_index     = sp.nat,
            ))
            pred = self.data.predictions[params.prediction_id]
            assert pred.status == sp.nat(STATUS_RESOLVED), "Prediction non resolue"

            bet = pred.bets[params.bet_index]
            assert bet.bettor == sp.sender, "Ce pari ne vous appartient pas"
            assert ~bet.claimed,            "Gains deja reclames"

            winning_option = pred.winning_option.unwrap_some("Pas de gagnant")
            assert bet.choice == winning_option, "Pari perdant"

            # Somme des mises gagnantes
            winning_pool = sp.mutez(0)
            for _, b in pred.bets.items():
                if b.choice == winning_option:
                    winning_pool += b.amount

            # Conversion mutez → nat via ediv (1 mutez = 1 unité)
            # sp.ediv(mutez, mutez) → option[(quotient:nat, remainder:mutez)]
            bet_nat   = sp.ediv(bet.amount,      sp.mutez(1)).unwrap_some().fst
            pool_nat  = sp.ediv(winning_pool,    sp.mutez(1)).unwrap_some().fst
            total_nat = sp.ediv(pred.total_pool, sp.mutez(1)).unwrap_some().fst

            # reward de base = total_pool × (bet / winning_pool)
            reward_nat  = total_nat * bet_nat // pool_nat
            base_reward = sp.mutez(reward_nat)

            # Bonus confiance (0 pour 50%, ½×base pour 75%, 1×base pour 95%)
            conf_num = sp.nat(0)
            if bet.confidence == sp.nat(75):
                conf_num = sp.nat(1)
            if bet.confidence == sp.nat(95):
                conf_num = sp.nat(2)

            extra_bonus  = sp.split_tokens(base_reward, conf_num, sp.nat(2))
            actual_bonus = sp.mutez(0)
            if self.data.bonus_pool >= extra_bonus:
                actual_bonus          = extra_bonus
                self.data.bonus_pool -= extra_bonus

            total_reward = base_reward + actual_bonus
            self.data.predictions[params.prediction_id].bets[params.bet_index].claimed = True
            sp.send(sp.sender, total_reward)

        # ------------------------------------------------------------------
        # Entrypoint : close_prediction
        # ------------------------------------------------------------------

        @sp.entrypoint
        def close_prediction(self, prediction_id):
            """Ferme une prédiction après la deadline (oracle uniquement)."""
            sp.cast(prediction_id, sp.nat)
            assert sp.sender == self.data.oracle_address, "Oracle uniquement"
            pred = self.data.predictions[prediction_id]
            assert pred.status == sp.nat(STATUS_OPEN), "Prediction non ouverte"
            assert pred.deadline <= sp.now,            "Deadline non encore atteinte"
            self.data.predictions[prediction_id].status = sp.nat(STATUS_CLOSED)

        # ------------------------------------------------------------------
        # Entrypoint : update_oracle
        # ------------------------------------------------------------------

        @sp.entrypoint
        def update_oracle(self, new_oracle):
            """Met à jour l'oracle résolveur (admin uniquement)."""
            sp.cast(new_oracle, sp.address)
            assert sp.sender == self.data.admin, "Admin uniquement"
            self.data.oracle_address = new_oracle

        # ------------------------------------------------------------------
        # Views — nouvelle API : utiliser return (plus sp.result)
        # ------------------------------------------------------------------

        @sp.onchain_view()
        def get_elo(self, addr):
            sp.cast(addr, sp.address)
            if self.data.elo_scores.contains(addr):
                return self.data.elo_scores[addr]
            return sp.int(ELO_INITIAL)

        @sp.onchain_view()
        def get_prediction_count(self):
            return self.data.prediction_count

        @sp.onchain_view()
        def get_bonus_pool(self):
            return self.data.bonus_pool


# ---------------------------------------------------------------------------
# Compilation — HORS du @sp.module, référencer via main.OracleProtocol
# ---------------------------------------------------------------------------

sp.add_compilation_target(
    "oracle_protocol",
    main.OracleProtocol(admin=sp.address("tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb")),
)
