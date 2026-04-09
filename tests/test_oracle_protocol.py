"""
Tests SmartPy - The Oracle Protocol
Compatible SmartPy >= 0.18 (nouvelle API)

Points clés nouvelle API :
  - sp.test_scenario("nom", main)   → passer le module, pas la classe
  - main.OracleProtocol(args)       → préfixer avec le nom du module
  - sp.record(...)                  → pour passer les params des entrypoints
  - sp.timestamp(int)               → pour les timestamps
"""

import smartpy as sp
from contracts.oracle_protocol import main


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@sp.add_test()
def test_oracle_protocol():
    scenario = sp.test_scenario("Oracle Protocol - Tests Complets", main)

    # Comptes de test
    admin   = sp.test_account("Admin")
    oracle  = sp.test_account("Oracle")
    alice   = sp.test_account("Alice")
    bob     = sp.test_account("Bob")
    charlie = sp.test_account("Charlie")

    NOW         = sp.timestamp(1_800_000_000)
    FUTURE      = sp.timestamp(1_800_010_000)   # +10 000 s (deadline valide)
    FUTURE_LONG = sp.timestamp(1_800_020_000)
    PAST        = sp.timestamp(1_000_000_000)
    AFTER       = sp.timestamp(1_900_000_000)   # après toutes les deadlines

    # ------------------------------------------------------------------
    # 1. Déploiement
    # ------------------------------------------------------------------
    scenario.h1("1. Deploiement")
    c = main.OracleProtocol(admin=admin.address)
    scenario += c

    scenario.verify(c.data.prediction_count == sp.nat(0))
    scenario.verify(c.data.bonus_pool       == sp.mutez(0))
    scenario.verify(c.data.admin            == admin.address)

    # ------------------------------------------------------------------
    # 2. Configuration oracle
    # ------------------------------------------------------------------
    scenario.h1("2. Configuration oracle")
    c.update_oracle(oracle.address, _sender=admin)
    scenario.verify(c.data.oracle_address == oracle.address)

    # Non-admin → rejeté
    c.update_oracle(alice.address, _sender=alice, _valid=False)

    # ------------------------------------------------------------------
    # 3. Création de prédictions
    # ------------------------------------------------------------------
    scenario.h1("3. Creation de predictions")

    c.create_prediction(
        sp.record(
            description = "Tezos depassera 5$ avant fin 2025 ?",
            deadline    = FUTURE,
            options     = ["Oui", "Non"],
        ),
        _sender = alice,
        _now    = NOW,
    )
    scenario.verify(c.data.prediction_count    == sp.nat(1))
    scenario.verify(c.data.predictions[0].status == sp.nat(0))  # STATUS_OPEN
    scenario.verify(c.data.predictions[0].bet_count == sp.nat(0))

    # Deadline passée → rejeté
    c.create_prediction(
        sp.record(
            description = "Passe",
            deadline    = PAST,
            options     = ["Oui", "Non"],
        ),
        _sender = alice,
        _now    = NOW,
        _valid  = False,
    )

    # Moins de 2 options → rejeté
    c.create_prediction(
        sp.record(
            description = "Une seule option",
            deadline    = FUTURE,
            options     = ["Seul"],
        ),
        _sender = alice,
        _now    = NOW,
        _valid  = False,
    )

    # Deuxième prédiction
    c.create_prediction(
        sp.record(
            description = "BTC > 100k USD en 2025 ?",
            deadline    = FUTURE_LONG,
            options     = ["Oui", "Non", "Impossible a dire"],
        ),
        _sender = bob,
        _now    = NOW,
    )
    scenario.verify(c.data.prediction_count == sp.nat(2))

    # ------------------------------------------------------------------
    # 4. Paris — 3 niveaux de confiance
    # ------------------------------------------------------------------
    scenario.h1("4. Paris — 3 niveaux de confiance")

    scenario.h2("4a. Alice — confiance 50 (Prudent)")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(50)),
        _sender = alice,
        _amount = sp.tez(10),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == sp.nat(1))
    # 2% de 10 tez = 0.2 tez de frais → net = 9.8 tez = 9_800_000 mutez
    scenario.verify(c.data.predictions[0].total_pool == sp.mutez(9_800_000))
    scenario.verify(c.data.bonus_pool                == sp.mutez(200_000))

    scenario.h2("4b. Bob — confiance 75 (Confiant)")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(75)),
        _sender = bob,
        _amount = sp.tez(10),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == sp.nat(2))

    scenario.h2("4c. Charlie — confiance 95 (Certain) — vote Non")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(1), confidence=sp.nat(95)),
        _sender = charlie,
        _amount = sp.tez(5),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == sp.nat(3))

    # Confiance invalide → rejeté
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(60)),
        _sender = alice,
        _amount = sp.tez(1),
        _now    = NOW,
        _valid  = False,
    )

    # Montant nul → rejeté
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(50)),
        _sender = alice,
        _amount = sp.mutez(0),
        _now    = NOW,
        _valid  = False,
    )

    # ------------------------------------------------------------------
    # 5. Résolution
    # ------------------------------------------------------------------
    scenario.h1("5. Resolution")

    # Non-oracle → rejeté
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(0), winning_option=sp.nat(0)),
        _sender = alice,
        _valid  = False,
    )

    # Oracle résout : option 0 ("Oui") gagne
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(0), winning_option=sp.nat(0)),
        _sender = oracle,
        _now    = AFTER,
    )
    scenario.verify(c.data.predictions[0].status         == sp.nat(2))  # STATUS_RESOLVED
    scenario.verify(c.data.predictions[0].winning_option == sp.Some(sp.nat(0)))

    # Vérification des scores ELO :
    #   Alice   conf=50, gagne : delta = 32×100×(100-50)÷10000 = +16  → 1016
    #   Bob     conf=75, gagne : delta = 32×150×(100-50)÷10000 = +24  → 1024
    #   Charlie conf=95, perd  : delta = 32×190×(  0-50)÷10000 = -30  → 970
    scenario.verify(c.get_elo(alice.address)   == sp.int(1016))
    scenario.verify(c.get_elo(bob.address)     == sp.int(1024))
    scenario.verify(c.get_elo(charlie.address) == sp.int(970))

    # Résoudre deux fois → rejeté
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(0), winning_option=sp.nat(1)),
        _sender = oracle,
        _valid  = False,
    )

    # ------------------------------------------------------------------
    # 6. Claim rewards
    # ------------------------------------------------------------------
    scenario.h1("6. Claim rewards")

    # Alice réclame son pari gagnant (index 0)
    c.claim_reward(
        sp.record(prediction_id=sp.nat(0), bet_index=sp.nat(0)),
        _sender = alice,
    )
    scenario.verify(c.data.predictions[0].bets[0].claimed == True)

    # Double claim → rejeté
    c.claim_reward(
        sp.record(prediction_id=sp.nat(0), bet_index=sp.nat(0)),
        _sender = alice,
        _valid  = False,
    )

    # Bob réclame son pari gagnant (index 1)
    c.claim_reward(
        sp.record(prediction_id=sp.nat(0), bet_index=sp.nat(1)),
        _sender = bob,
    )
    scenario.verify(c.data.predictions[0].bets[1].claimed == True)

    # Charlie tente de réclamer un pari perdant → rejeté
    c.claim_reward(
        sp.record(prediction_id=sp.nat(0), bet_index=sp.nat(2)),
        _sender = charlie,
        _valid  = False,
    )

    # Mauvais sender → rejeté
    c.claim_reward(
        sp.record(prediction_id=sp.nat(0), bet_index=sp.nat(1)),
        _sender = charlie,
        _valid  = False,
    )

    # ------------------------------------------------------------------
    # 7. Progression ELO — second round
    # ------------------------------------------------------------------
    scenario.h1("7. Progression ELO — second round")

    c.create_prediction(
        sp.record(
            description = "BTC > 100k USD en mars 2025 ?",
            deadline    = FUTURE_LONG,
            options     = ["Oui", "Non"],
        ),
        _sender = admin,
        _now    = NOW,
    )
    scenario.verify(c.data.prediction_count == sp.nat(3))

    # Alice conf=95 vote Oui
    c.place_bet(
        sp.record(prediction_id=sp.nat(2), choice=sp.nat(0), confidence=sp.nat(95)),
        _sender = alice,
        _amount = sp.tez(20),
        _now    = NOW,
    )

    # Charlie conf=50 vote Non
    c.place_bet(
        sp.record(prediction_id=sp.nat(2), choice=sp.nat(1), confidence=sp.nat(50)),
        _sender = charlie,
        _amount = sp.tez(10),
        _now    = NOW,
    )

    # Oracle : Oui gagne
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(2), winning_option=sp.nat(0)),
        _sender = oracle,
        _now    = AFTER,
    )

    # Alice  : 1016 + 32×190×50÷10000 = 1016 + 30 = 1046
    # Charlie: 970  + 32×100×(−50)÷10000 = 970 − 16 = 954
    scenario.verify(c.get_elo(alice.address)   == sp.int(1046))
    scenario.verify(c.get_elo(charlie.address) == sp.int(954))

    # ------------------------------------------------------------------
    # 8. Views
    # ------------------------------------------------------------------
    scenario.h1("8. Views")
    scenario.verify(c.get_prediction_count() == sp.nat(3))
    scenario.verify(c.get_bonus_pool()        >= sp.mutez(0))
    # Nouvel oracle non encore enregistré → ELO initial
    scenario.verify(c.get_elo(oracle.address) == sp.int(1000))

    scenario.h1("Tous les tests passes avec succes")
