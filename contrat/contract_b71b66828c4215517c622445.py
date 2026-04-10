import smartpy as sp

@sp.module
def main():
    # Constantes
    STATUS_OPEN = sp.nat(0)
    STATUS_CLOSED = sp.nat(1)
    STATUS_RESOLVED = sp.nat(2)
    ELO_INITIAL = sp.int(1000)

    class OracleProtocol(sp.Contract):
        def __init__(self, admin):
            self.data.admin = admin
            self.data.oracle_address = admin
            self.data.prediction_count = sp.nat(0)
            self.data.bonus_pool = sp.mutez(0)
            
            self.data.elo_scores = sp.cast(
                {}, sp.map[sp.address, sp.int]
            )
            self.data.predictions = sp.cast(
                {}, 
                sp.map[sp.nat, sp.record(
                    creator = sp.address,
                    description = sp.string,
                    deadline = sp.timestamp,
                    options = sp.list[sp.string],
                    status = sp.nat,
                    winning_option = sp.option[sp.nat],
                    total_pool = sp.mutez,
                    total_winning_weight = sp.nat,
                    bets = sp.map[sp.nat, sp.record(
                        bettor = sp.address,
                        choice = sp.nat,
                        amount = sp.mutez,
                        confidence = sp.nat,
                        weight = sp.nat,
                        claimed = sp.bool,
                    )],
                    bet_count = sp.nat,
                )]
            )

        @sp.entrypoint
        def create_prediction(self, description, deadline, options):
            new_pred = sp.record(
                creator = sp.sender,
                description = description,
                deadline = deadline,
                options = options,
                status = STATUS_OPEN,
                winning_option = sp.cast(None, sp.option[sp.nat]),
                total_pool = sp.mutez(0),
                total_winning_weight = sp.nat(0),
                bets = sp.cast({}, sp.map[sp.nat, sp.record(
                    bettor = sp.address,
                    choice = sp.nat,
                    amount = sp.mutez,
                    confidence = sp.nat,
                    weight = sp.nat,
                    claimed = sp.bool,
                )]),
                bet_count = sp.nat(0)
            )
            self.data.predictions[self.data.prediction_count] = new_pred
            self.data.prediction_count += 1

        @sp.entrypoint
        def place_bet(self, prediction_id, choice, confidence):
            # Validation stricte de la confiance
            is_valid = False
            if confidence == sp.nat(50):
                is_valid = True
            if confidence == sp.nat(75):
                is_valid = True
            if confidence == sp.nat(95):
                is_valid = True
            assert is_valid, "INVALID_CONFIDENCE"
            
            assert prediction_id < self.data.prediction_count, "INVALID_ID"
            prediction = self.data.predictions[prediction_id]
            assert sp.now < prediction.deadline, "DEADLINE_PASSED"
            assert prediction.status == STATUS_OPEN, "NOT_OPEN"
            
            fee = sp.split_tokens(sp.amount, 2, 100)
            net_bet = sp.amount - fee
            
            self.data.bonus_pool += fee
            
            new_bet = sp.record(
                bettor = sp.sender,
                choice = choice,
                amount = net_bet,
                confidence = confidence,
                weight = sp.nat(0),
                claimed = False
            )
            
            prediction.bets[prediction.bet_count] = new_bet
            prediction.bet_count += 1
            prediction.total_pool += net_bet
            
            self.data.predictions[prediction_id] = prediction

        @sp.entrypoint
        def resolve_prediction(self, prediction_id, winning_option):
            assert sp.sender == self.data.oracle_address, "NOT_AUTHORIZED"
            prediction = self.data.predictions[prediction_id]
            assert prediction.status == STATUS_OPEN, "ALREADY_RESOLVED"
            
            prediction.winning_option = sp.Some(winning_option)
            prediction.status = STATUS_RESOLVED
            
            for i in sp.range(0, prediction.bet_count):
                bet = prediction.bets[i]
                is_winner = (bet.choice == winning_option)
                
                if not self.data.elo_scores.contains(bet.bettor):
                    self.data.elo_scores[bet.bettor] = ELO_INITIAL
                
                current_elo = self.data.elo_scores[bet.bettor]
                
                if is_winner:
                    res_amount = sp.ediv(bet.amount, sp.mutez(1)).unwrap_some()
                    amt_nat = sp.fst(res_amount)
                    bet.weight = amt_nat * bet.confidence * sp.as_nat(current_elo)
                    prediction.total_winning_weight += bet.weight
                
                # --- CALCUL ELO (Paliers Fixes) ---
                delta = sp.int(0)
                if bet.confidence == sp.nat(50):
                    delta = sp.int(15)
                if bet.confidence == sp.nat(75):
                    delta = sp.int(30)
                if bet.confidence == sp.nat(95):
                    delta = sp.int(60)
                
                if is_winner:
                    self.data.elo_scores[bet.bettor] = current_elo + delta
                else:
                    self.data.elo_scores[bet.bettor] = current_elo - delta
                # ------------------------------------------
                
                prediction.bets[i] = bet
                
            self.data.predictions[prediction_id] = prediction

        @sp.entrypoint
        def claim_reward(self, prediction_id, bet_id):
            prediction = self.data.predictions[prediction_id]
            assert prediction.status == STATUS_RESOLVED, "NOT_RESOLVED"
            
            bet = prediction.bets[bet_id]
            assert bet.bettor == sp.sender, "NOT_YOUR_BET"
            assert not bet.claimed, "ALREADY_CLAIMED"
            
            winning_opt = prediction.winning_option.unwrap_some()
            assert bet.choice == winning_opt, "LOST_BET"
            
            reward = sp.split_tokens(prediction.total_pool, bet.weight, prediction.total_winning_weight)
            
            bet.claimed = True
            prediction.bets[bet_id] = bet
            self.data.predictions[prediction_id] = prediction
            
            sp.send(sp.sender, reward)


# ---------------------------------------------------------------------------
# Scénario de Tests
# ---------------------------------------------------------------------------

@sp.add_test()
def test():
    scenario = sp.test_scenario("Oracle_Protocol_Audit", main)
    
    # 1. Initialisation des acteurs
    admin = sp.test_account("admin")
    alice = sp.test_account("alice_50")     # Joueuse prudente
    bob = sp.test_account("bob_75")         # Joueur initié
    charlie = sp.test_account("charlie_95") # Joueur visionnaire
    eve = sp.test_account("eve_hacker")     # L'attaquante
    
    # Déploiement
    c1 = main.OracleProtocol(admin.address)
    scenario += c1
    
    scenario.h1("1. Tests d'Initialisation")
    scenario.verify(c1.data.prediction_count == 0)
    scenario.verify(c1.data.bonus_pool == sp.mutez(0))
    scenario.verify(c1.data.oracle_address == admin.address)
    
    scenario.h1("2. Création des Prédictions")
    future_date = sp.timestamp(1800000000) # Dans le futur
    past_date = sp.timestamp(0)            # Dans le passé (1970)
    
    # Pred 0 : Normale
    c1.create_prediction(description="Pred 1", deadline=future_date, options=["Oui", "Non"], _sender=admin)
    # Pred 1 : Normale (Ne sera pas résolue pour les tests de sécurité)
    c1.create_prediction(description="Pred 2", deadline=future_date, options=["A", "B"], _sender=admin)
    # Pred 2 : Expirée
    c1.create_prediction(description="Pred 3 (Expirée)", deadline=past_date, options=["1", "2"], _sender=admin)
    
    scenario.verify(c1.data.prediction_count == 3)

    scenario.h1("3. Prise de Paris (Happy Path & Comptabilité)")
    # Alice mise 10 XTZ (2% = 0.2 XTZ, Net = 9.8 XTZ)
    c1.place_bet(prediction_id=0, choice=0, confidence=50, _sender=alice, _amount=sp.tez(10))
    # Bob mise 20 XTZ (2% = 0.4 XTZ, Net = 19.6 XTZ)
    c1.place_bet(prediction_id=0, choice=0, confidence=75, _sender=bob, _amount=sp.tez(20))
    # Charlie mise 30 XTZ (2% = 0.6 XTZ, Net = 29.4 XTZ) sur la mauvaise réponse
    c1.place_bet(prediction_id=0, choice=1, confidence=95, _sender=charlie, _amount=sp.tez(30))
    
    # VERIFICATION MATHÉMATIQUE DE LA POOL :
    # Total misé = 60 XTZ. Frais = 1.2 XTZ. Net dans la pool = 58.8 XTZ
    scenario.verify(c1.data.bonus_pool == sp.mutez(1_200_000)) # 1.2 XTZ
    scenario.verify(c1.data.predictions[0].total_pool == sp.mutez(58_800_000)) # 58.8 XTZ

    scenario.h1("4. Sécurité des Paris (Les attaques d'Eve)")
    # Fausse confiance (80%)
    c1.place_bet(prediction_id=0, choice=0, confidence=80, _sender=eve, _amount=sp.tez(1), _valid=False, _exception="INVALID_CONFIDENCE")
    # ID Invalide
    c1.place_bet(prediction_id=99, choice=0, confidence=50, _sender=eve, _amount=sp.tez(1), _valid=False, _exception="INVALID_ID")
    # Deadline dépassée (Pari sur Pred 2)
    c1.place_bet(prediction_id=2, choice=0, confidence=50, _sender=eve, _amount=sp.tez(1), _valid=False, _exception="DEADLINE_PASSED")

    scenario.h1("5. Résolution & Vérification des ELOs")
    # L'usurpateur tente de résoudre
    c1.resolve_prediction(prediction_id=0, winning_option=0, _sender=eve, _valid=False, _exception="NOT_AUTHORIZED")
    
    # L'Admin résout (Le choix '0' gagne)
    c1.resolve_prediction(prediction_id=0, winning_option=0, _sender=admin)
    
    # Double résolution
    c1.resolve_prediction(prediction_id=0, winning_option=0, _sender=admin, _valid=False, _exception="ALREADY_RESOLVED")
    # Parier sur une partie finie
    c1.place_bet(prediction_id=0, choice=0, confidence=50, _sender=eve, _amount=sp.tez(1), _valid=False, _exception="NOT_OPEN")

    # VERIFICATIONS MATHEMATIQUES ELO (Paliers Fixes)
    # Alice (Gagnante 50%) : 1000 + 15 = 1015
    scenario.verify(c1.data.elo_scores[alice.address] == 1015)
    # Bob (Gagnant 75%) : 1000 + 30 = 1030
    scenario.verify(c1.data.elo_scores[bob.address] == 1030)
    # Charlie (Perdant 95%) : 1000 - 60 = 940
    scenario.verify(c1.data.elo_scores[charlie.address] == 940)

    scenario.h1("6. Réclamations des gains (Sécurité & Double-Claim)")
    # Trop pressé : Alice tente de réclamer sur Pred 1 (Non résolue)
    c1.claim_reward(prediction_id=1, bet_id=0, _sender=alice, _valid=False, _exception="NOT_RESOLVED")
    
    # Mauvais perdant : Charlie tente de réclamer
    c1.claim_reward(prediction_id=0, bet_id=2, _sender=charlie, _valid=False, _exception="LOST_BET")
    
    # Voleur : Eve tente de réclamer le gain de Bob (bet_id = 1)
    c1.claim_reward(prediction_id=0, bet_id=1, _sender=eve, _valid=False, _exception="NOT_YOUR_BET")
    
    # SUCCESS CLAIMS
    c1.claim_reward(prediction_id=0, bet_id=0, _sender=alice)
    c1.claim_reward(prediction_id=0, bet_id=1, _sender=bob)
    
    # Vérification d'état (Le booléen est-il passé à True ?)
    scenario.verify(c1.data.predictions[0].bets[0].claimed == True)
    
    # CRITIQUE : Double-Claim (Alice tente de vider le contrat)
    c1.claim_reward(prediction_id=0, bet_id=0, _sender=alice, _valid=False, _exception="ALREADY_CLAIMED")
    