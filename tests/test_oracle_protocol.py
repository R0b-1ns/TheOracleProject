"""
Tests SmartPy - The Oracle Protocol
Scénario complet : création → mise → résolution → claim
"""

import smartpy as sp
from contracts.oracle_protocol import OracleProtocol, STATUS_OPEN, STATUS_RESOLVED


def future(offset=7200):
    return sp.timestamp(1_800_000_000 + offset)   # timestamp fixe + offset


def past():
    return sp.timestamp(1_000_000_000)


@sp.add_test()
def test_oracle_protocol():
    scenario = sp.test_scenario("Oracle Protocol - Tests Complets", [OracleProtocol])

    # ------------------------------------------------------------------
    # Comptes
    # ------------------------------------------------------------------
    admin   = sp.test_account("Admin")
    oracle  = sp.test_account("Oracle")
    alice   = sp.test_account("Alice")
    bob     = sp.test_account("Bob")
    charlie = sp.test_account("Charlie")

    # ------------------------------------------------------------------
    # 1. Déploiement
    # ------------------------------------------------------------------
    scenario.h1("1. Déploiement")
    c = OracleProtocol(admin=admin.address)
    scenario += c

    scenario.verify(c.data.prediction_count == 0)
    scenario.verify(c.data.bonus_pool == sp.mutez(0))

    # ------------------------------------------------------------------
    # 2. Configuration oracle
    # ------------------------------------------------------------------
    scenario.h1("2. Configuration oracle")
    c.update_oracle(oracle.address, _sender=admin)
    scenario.verify(c.data.oracle_address == oracle.address)

    # Non-admin refusé
    c.update_oracle(alice.address, _sender=alice, _valid=False)

    # ------------------------------------------------------------------
    # 3. Création de prédictions
    # ------------------------------------------------------------------
    scenario.h1("3. Création de prédictions")

    NOW = sp.timestamp(1_800_000_000)

    c.create_prediction(
        sp.record(
            description = "Tezos depassera 5$ avant fin 2025 ?",
            deadline    = future(7200),
            options     = ["Oui", "Non"],
        ),
        _sender = alice,
        _now    = NOW,
    )
    scenario.verify(c.data.prediction_count == 1)
    scenario.verify(c.data.predictions[0].status == sp.nat(STATUS_OPEN))

    # Deadline passée → rejeté
    c.create_prediction(
        sp.record(
            description = "Passé",
            deadline    = past(),
            options     = ["Oui", "Non"],
        ),
        _sender = alice,
        _now    = NOW,
        _valid  = False,
    )

    # Moins de 2 options → rejeté
    c.create_prediction(
        sp.record(
            description = "Une option",
            deadline    = future(7200),
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
            deadline    = future(14400),
            options     = ["Oui", "Non", "Impossible a dire"],
        ),
        _sender = bob,
        _now    = NOW,
    )
    scenario.verify(c.data.prediction_count == 2)

    # ------------------------------------------------------------------
    # 4. Paris — 3 niveaux de confiance
    # ------------------------------------------------------------------
    scenario.h1("4. Paris avec 3 niveaux de confiance")

    scenario.h2("4a. Alice — confiance 50%")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(50)),
        _sender = alice,
        _amount = sp.tez(10),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == 1)
    # frais 2% sur 10 tez = 0.2 tez → net = 9.8 tez
    scenario.verify(c.data.predictions[0].total_pool == sp.mutez(9_800_000))
    scenario.verify(c.data.bonus_pool == sp.mutez(200_000))

    scenario.h2("4b. Bob — confiance 75%")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(0), confidence=sp.nat(75)),
        _sender = bob,
        _amount = sp.tez(10),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == 2)

    scenario.h2("4c. Charlie — confiance 95%")
    c.place_bet(
        sp.record(prediction_id=sp.nat(0), choice=sp.nat(1), confidence=sp.nat(95)),
        _sender = charlie,
        _amount = sp.tez(5),
        _now    = NOW,
    )
    scenario.verify(c.data.predictions[0].bet_count == 3)

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
    scenario.h1("5. Résolution")

    # Non-oracle → rejeté
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(0), winning_option=sp.nat(0)),
        _sender = alice,
        _valid  = False,
    )

    # Oracle résout : "Oui" (index 0) gagne
    RESOLVE_NOW = sp.timestamp(1_800_010_000)
    c.resolve_prediction(
        sp.record(prediction_id=sp.nat(0), winning_option=sp.nat(0)),
        _sender = oracle,
        _now    = RESOLVE_NOW,
    )
    scenario.verify(c.data.predictions[0].status         == sp.nat(STATUS_RESOLVED))
    scenario.verify(c.data.predictions[0].winning_option == sp.some(sp.nat(0)))

    # Vérification ELO
    # Alice  confiance 50 gagne : delta = 32×100×50/10000 = +16  → 1016
    # Bob    confiance 75 gagne : delta = 32×150×50/10000 = +24  → 1024
    # Charlie confiance 95 perd : delta = 32×190×(−50)/10000 = −30 → 970
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

    # Alice réclame (bet_index 0, gagnant)
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

    # Bob réclame (bet_index 1, gagnant)
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
    # 7. Progression ELO sur un second round
    # ------------------------------------------------------------------
    scenario.h1("7. Progression ELO — second round")

    c.create_prediction(
        sp.record(
            description = "BTC > 100k USD en mars 2025 ?",
            deadline    = future(28800),
            options     = ["Oui", "Non"],
        ),
        _sender = admin,
        _now    = NOW,
    )

    # Alice confiance 95 vote Oui
    c.place_bet(
        sp.record(prediction_id=sp.nat(2), choice=sp.nat(0), confidence=sp.nat(95)),
        _sender = alice,
        _amount = sp.tez(20),
        _now    = NOW,
    )

    # Charlie confiance 50 vote Non
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
        _now    = RESOLVE_NOW,
    )

    # Alice  : 1016 + 32×190×50/10000 = 1016 + 30 = 1046
    # Charlie: 970  + 32×100×(−50)/10000 = 970 − 16 = 954
    scenario.verify(c.get_elo(alice.address)   == sp.int(1046))
    scenario.verify(c.get_elo(charlie.address) == sp.int(954))

    # ------------------------------------------------------------------
    # 8. Views
    # ------------------------------------------------------------------
    scenario.h1("8. Views")
    scenario.verify(c.get_prediction_count() == sp.nat(3))
    scenario.verify(c.get_bonus_pool()        >= sp.mutez(0))

    scenario.h1("Tous les tests passes avec succes ✓")
