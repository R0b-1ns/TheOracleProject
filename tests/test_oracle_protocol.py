"""
Tests SmartPy - The Oracle Protocol
Scénarios complets : création → mise → résolution → claim
"""

import smartpy as sp
from contracts.oracle_protocol import OracleProtocol, STATUS_OPEN, STATUS_RESOLVED


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_contract(admin):
    return OracleProtocol(admin=admin.address)


def future_timestamp(offset_seconds=3600):
    """Retourne un timestamp dans le futur (now + offset)."""
    return sp.timestamp_from_utc(2025, 1, 1, 12, 0, 0).add_seconds(offset_seconds)


def past_timestamp():
    return sp.timestamp_from_utc(2020, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------------------
# Suite de tests
# ---------------------------------------------------------------------------

@sp.add_test()
def test_oracle_protocol():
    scenario = sp.test_scenario("Oracle Protocol - Tests Complets", [OracleProtocol])

    # Comptes de test
    admin   = sp.test_account("Admin")
    oracle  = sp.test_account("Oracle")
    alice   = sp.test_account("Alice")
    bob     = sp.test_account("Bob")
    charlie = sp.test_account("Charlie")

    # -----------------------------------------------------------------------
    # Déploiement
    # -----------------------------------------------------------------------
    scenario.h1("1. Déploiement du contrat")
    c = get_contract(admin)
    scenario += c

    scenario.verify(c.data.prediction_count == 0)
    scenario.verify(c.data.bonus_pool == sp.mutez(0))
    scenario.verify(c.data.admin == admin.address)

    # -----------------------------------------------------------------------
    # Mise à jour de l'oracle
    # -----------------------------------------------------------------------
    scenario.h1("2. Configuration de l'oracle résolveur")
    c.update_oracle(oracle.address, _sender=admin)
    scenario.verify(c.data.oracle_address == oracle.address)

    # Accès refusé si non-admin
    c.update_oracle(alice.address, _sender=alice, _valid=False)

    # -----------------------------------------------------------------------
    # Création de prédiction
    # -----------------------------------------------------------------------
    scenario.h1("3. Création de prédictions")

    deadline = future_timestamp(7200)  # +2h

    c.create_prediction(
        description = "Tezos dépassera 5$ avant fin 2025 ?",
        deadline    = deadline,
        options     = ["Oui", "Non"],
        _sender     = alice,
        _now        = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
    )
    scenario.verify(c.data.prediction_count == 1)
    scenario.verify(c.data.predictions[0].description == "Tezos dépassera 5$ avant fin 2025 ?")
    scenario.verify(c.data.predictions[0].status == STATUS_OPEN)
    scenario.verify(c.data.predictions[0].bet_count == 0)

    # Deadline dans le passé → rejeté
    c.create_prediction(
        description = "Test passé",
        deadline    = past_timestamp(),
        options     = ["Oui", "Non"],
        _sender     = alice,
        _now        = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
        _valid      = False,
    )

    # Moins de 2 options → rejeté
    c.create_prediction(
        description = "Une seule option",
        deadline    = deadline,
        options     = ["Seul"],
        _sender     = alice,
        _now        = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
        _valid      = False,
    )

    scenario.h2("Création d'une deuxième prédiction")
    c.create_prediction(
        description = "ETH flippe BTC en market cap en 2025 ?",
        deadline    = deadline,
        options     = ["Oui", "Non", "Impossible à dire"],
        _sender     = bob,
        _now        = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
    )
    scenario.verify(c.data.prediction_count == 2)

    # -----------------------------------------------------------------------
    # Place_bet — 3 niveaux de confiance
    # -----------------------------------------------------------------------
    scenario.h1("4. Mise avec 3 niveaux de confiance")

    scenario.h2("4a. Alice mise avec confiance 50% (conservateur)")
    c.place_bet(
        prediction_id = sp.nat(0),
        choice        = sp.nat(0),  # "Oui"
        confidence    = sp.nat(50),
        _sender       = alice,
        _amount       = sp.tez(10),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
    )
    scenario.verify(c.data.predictions[0].bet_count == 1)
    # 2% de frais sur 10 tez = 0.2 tez → bet_amount = 9.8 tez
    scenario.verify(c.data.predictions[0].total_pool == sp.mutez(9_800_000))
    scenario.verify(c.data.bonus_pool == sp.mutez(200_000))

    scenario.h2("4b. Bob mise avec confiance 75% (modéré)")
    c.place_bet(
        prediction_id = sp.nat(0),
        choice        = sp.nat(0),  # "Oui"
        confidence    = sp.nat(75),
        _sender       = bob,
        _amount       = sp.tez(10),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
    )
    scenario.verify(c.data.predictions[0].bet_count == 2)

    scenario.h2("4c. Charlie mise avec confiance 95% (audacieux)")
    c.place_bet(
        prediction_id = sp.nat(0),
        choice        = sp.nat(1),  # "Non"
        confidence    = sp.nat(95),
        _sender       = charlie,
        _amount       = sp.tez(5),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
    )
    scenario.verify(c.data.predictions[0].bet_count == 3)

    # Confiance invalide → rejeté
    c.place_bet(
        prediction_id = sp.nat(0),
        choice        = sp.nat(0),
        confidence    = sp.nat(60),  # invalide
        _sender       = alice,
        _amount       = sp.tez(1),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
        _valid        = False,
    )

    # Mise à 0 → rejeté
    c.place_bet(
        prediction_id = sp.nat(0),
        choice        = sp.nat(0),
        confidence    = sp.nat(50),
        _sender       = alice,
        _amount       = sp.mutez(0),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 10, 0, 0),
        _valid        = False,
    )

    # -----------------------------------------------------------------------
    # Résolution
    # -----------------------------------------------------------------------
    scenario.h1("5. Résolution de la prédiction")

    # Non-oracle → refusé
    c.resolve_prediction(
        prediction_id  = sp.nat(0),
        winning_option = sp.nat(0),
        _sender        = alice,
        _valid         = False,
    )

    # Oracle résout : "Oui" (option 0) gagne
    c.resolve_prediction(
        prediction_id  = sp.nat(0),
        winning_option = sp.nat(0),
        _sender        = oracle,
        _now           = sp.timestamp_from_utc(2025, 1, 1, 14, 0, 0),
    )
    scenario.verify(c.data.predictions[0].status == STATUS_RESOLVED)
    scenario.verify(c.data.predictions[0].winning_option == sp.Some(sp.nat(0)))

    # Vérification ELO : Alice et Bob ont gagné (confiance 50 et 75)
    # Charlie a perdu (confiance 95)
    alice_elo   = c.get_elo(alice.address)
    bob_elo     = c.get_elo(bob.address)
    charlie_elo = c.get_elo(charlie.address)

    # Alice confiance 50 : delta = 32 * 100 * (100-50) / 10000 = 16 → ELO 1016
    scenario.verify(alice_elo == 1016)
    # Bob confiance 75 : delta = 32 * 150 * (100-50) / 10000 = 24 → ELO 1024
    scenario.verify(bob_elo == 1024)
    # Charlie confiance 95 : delta = 32 * 190 * (0-50) / 10000 = -30 (arrondi) → ELO 970
    scenario.verify(charlie_elo == 970)

    # Résoudre deux fois → rejeté
    c.resolve_prediction(
        prediction_id  = sp.nat(0),
        winning_option = sp.nat(1),
        _sender        = oracle,
        _valid         = False,
    )

    # -----------------------------------------------------------------------
    # Claim reward
    # -----------------------------------------------------------------------
    scenario.h1("6. Réclamation des gains")

    # Alice réclame son pari gagnant (bet_index 0)
    initial_balance = scenario.compute(sp.balance_of(alice.address))
    c.claim_reward(
        prediction_id = sp.nat(0),
        bet_index     = sp.nat(0),
        _sender       = alice,
    )
    scenario.verify(
        c.data.predictions[0].bets[0].claimed == True
    )

    # Réclamer deux fois → rejeté
    c.claim_reward(
        prediction_id = sp.nat(0),
        bet_index     = sp.nat(0),
        _sender       = alice,
        _valid        = False,
    )

    # Bob réclame son pari gagnant (bet_index 1)
    c.claim_reward(
        prediction_id = sp.nat(0),
        bet_index     = sp.nat(1),
        _sender       = bob,
    )
    scenario.verify(c.data.predictions[0].bets[1].claimed == True)

    # Charlie tente de réclamer un pari perdant → rejeté
    c.claim_reward(
        prediction_id = sp.nat(0),
        bet_index     = sp.nat(2),
        _sender       = charlie,
        _valid        = False,
    )

    # Mauvais sender → rejeté
    c.claim_reward(
        prediction_id = sp.nat(0),
        bet_index     = sp.nat(0),
        _sender       = charlie,
        _valid        = False,
    )

    # -----------------------------------------------------------------------
    # Test progression ELO sur plusieurs rounds
    # -----------------------------------------------------------------------
    scenario.h1("7. Progression ELO sur plusieurs rounds")

    c.create_prediction(
        description = "BTC > 100k USD en mars 2025 ?",
        deadline    = future_timestamp(14400),
        options     = ["Oui", "Non"],
        _sender     = admin,
        _now        = sp.timestamp_from_utc(2025, 1, 1, 12, 0, 0),
    )

    # Alice joue confiance 95 et gagne → gros boost ELO
    c.place_bet(
        prediction_id = sp.nat(2),
        choice        = sp.nat(0),
        confidence    = sp.nat(95),
        _sender       = alice,
        _amount       = sp.tez(20),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 12, 0, 0),
    )

    # Charlie joue confiance 50 et perd → petite perte ELO
    c.place_bet(
        prediction_id = sp.nat(2),
        choice        = sp.nat(1),
        confidence    = sp.nat(50),
        _sender       = charlie,
        _amount       = sp.tez(10),
        _now          = sp.timestamp_from_utc(2025, 1, 1, 12, 0, 0),
    )

    c.resolve_prediction(
        prediction_id  = sp.nat(2),
        winning_option = sp.nat(0),  # "Oui" gagne
        _sender        = oracle,
        _now           = sp.timestamp_from_utc(2025, 1, 1, 16, 0, 0),
    )

    # Alice : 1016 + 60 (confiance 95 gagnée) = 1076
    # delta = 32 * 190 * 50 / 10000 = 30 → 1016 + 30 = 1046
    scenario.verify(c.get_elo(alice.address) == 1046)

    # Charlie : 970 - 16 (confiance 50 perdue) = 954
    # delta = 32 * 100 * -50 / 10000 = -16 → 970 - 16 = 954
    scenario.verify(c.get_elo(charlie.address) == 954)

    # -----------------------------------------------------------------------
    # Views
    # -----------------------------------------------------------------------
    scenario.h1("8. Vérification des views")
    scenario.verify(c.get_prediction_count() == sp.nat(3))
    scenario.verify(c.get_bonus_pool() >= sp.mutez(0))
    scenario.verify(c.get_prediction(sp.nat(0)).status == STATUS_RESOLVED)

    scenario.h1("Tests terminés avec succès ✓")
