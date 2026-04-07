# 🔮 The Oracle Protocol

Marché de prédictions décentralisé sur **Tezos Ghostnet**, avec système de réputation ELO et niveaux de confiance.

---

## Architecture

```
TheOracleProject/
├── contracts/
│   └── oracle_protocol.py     # Smart contract SmartPy
├── tests/
│   └── test_oracle_protocol.py # Tests SmartPy complets
└── frontend/
    ├── src/
    │   ├── components/        # Navbar, PredictionCard, EloRing, Modals
    │   ├── pages/             # Home, Profile, Leaderboard
    │   ├── context/           # WalletContext (Beacon)
    │   ├── utils/             # Taquito helpers, formatters
    │   └── types/             # TypeScript types
    ├── package.json
    └── tailwind.config.js
```

---

## Smart Contract

### Storage
| Champ | Type | Description |
|-------|------|-------------|
| `elo_scores` | `map(address, int)` | Score ELO par joueur (initial : 1000) |
| `predictions` | `map(nat, Prediction)` | Toutes les prédictions |
| `prediction_count` | `nat` | Compteur de prédictions |
| `bonus_pool` | `mutez` | Cagnotte alimentée par les frais (2%) |
| `oracle_address` | `address` | Résolveur de prédictions |

### Entrypoints
| Entrypoint | Accès | Description |
|-----------|-------|-------------|
| `create_prediction` | Public | Crée une prédiction avec deadline et options |
| `place_bet` | Public | Place une mise avec niveau de confiance |
| `resolve_prediction` | Oracle | Résout en désignant l'option gagnante |
| `claim_reward` | Gagnant | Réclame les gains d'un pari gagnant |
| `close_prediction` | Oracle | Ferme une prédiction après la deadline |
| `update_oracle` | Admin | Met à jour l'adresse de l'oracle |

### Logique ELO
```
delta = K(32) × (confidence/50) × (résultat - 0.5)
résultat = 1 si gagné, 0 si perdu
```

| Confiance | Multiplicateur ELO | Multiplicateur gains |
|-----------|-------------------|---------------------|
| 50%       | ×1                | ×1                  |
| 75%       | ×1.5              | ×1.5                |
| 95%       | ×1.9              | ×2                  |

### Rangs
| ELO | Rang |
|-----|------|
| < 1100 | 🌙 Apprenti Oracle |
| 1100–1299 | 👁️ Voyant |
| 1300–1599 | 🔮 Prophète |
| ≥ 1600 | ⚡ Architecte du Futur |

---

## Développement

### Prérequis
- Python 3.10+ avec SmartPy CLI
- Node.js 18+

### Smart Contract

```bash
# Compiler
smartpy compile contracts/oracle_protocol.py smartpy-out/

# Lancer les tests
smartpy test tests/test_oracle_protocol.py
```

### Déploiement sur Ghostnet
```bash
# Via octez-client
octez-client -E https://rpc.ghostnet.teztnets.com originate contract oracle_protocol \
  transferring 0 from <VOTRE_ADRESSE> \
  running smartpy-out/oracle_protocol.tz \
  --init '<STORAGE_INITIAL>' \
  --burn-cap 5
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Éditer .env avec l'adresse du contrat déployé

npm run dev      # Développement (http://localhost:5173)
npm run build    # Production
```

---

## Stack technique

| Couche | Technologie |
|--------|------------|
| Smart contract | SmartPy |
| Blockchain | Tezos Ghostnet |
| Interaction chain | Taquito v20 |
| Wallet | Beacon SDK + Temple Wallet |
| Frontend | React 18 + TypeScript + Vite |
| UI | Tailwind CSS + Framer Motion |
| Icônes | Lucide React |

---

## Frais de plateforme

- **2%** de chaque mise alimentent le `bonus_pool`
- Le bonus pool finance les multiplicateurs de gains pour les paris à haute confiance
- Les frais ne sont jamais prélevés sur les gains, uniquement à l'entrée

---

*The Oracle Protocol — Predict. Prove. Ascend.*
