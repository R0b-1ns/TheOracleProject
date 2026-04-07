import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Plus, Search, Filter, Zap } from "lucide-react";
import PredictionCard from "../components/PredictionCard";
import CreatePredictionModal from "../components/CreatePredictionModal";
import { fetchPredictions } from "../utils/contract";
import { useWallet } from "../context/WalletContext";
import type { Prediction, PredictionStatus } from "../types";

const FILTERS: { label: string; value: PredictionStatus | "all" }[] = [
  { label: "Toutes",   value: "all" },
  { label: "En cours", value: "open" },
  { label: "Résolues", value: "resolved" },
  { label: "Fermées",  value: "closed" },
];

// Données de démo (utilisées si le contrat n'est pas déployé)
const DEMO_PREDICTIONS: Prediction[] = [
  {
    id: 0,
    creator: "tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb",
    description: "Tezos dépassera 5$ avant fin 2025 ?",
    deadline: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
    options: ["Oui", "Non"],
    status: "open",
    winningOption: null,
    totalPool: 45_000_000,
    bets: [
      { bettor: "tz1Alice", choice: 0, amount: 9_800_000, confidence: 75, claimed: false },
      { bettor: "tz1Bob",   choice: 1, amount: 9_800_000, confidence: 50, claimed: false },
      { bettor: "tz1Carol", choice: 0, amount: 4_900_000, confidence: 95, claimed: false },
    ],
  },
  {
    id: 1,
    creator: "tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb",
    description: "ETH flippe BTC en market cap avant 2026 ?",
    deadline: new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
    options: ["Oui", "Non", "Trop tôt pour le dire"],
    status: "open",
    winningOption: null,
    totalPool: 120_000_000,
    bets: [
      { bettor: "tz1Dave", choice: 2, amount: 49_000_000, confidence: 50, claimed: false },
    ],
  },
  {
    id: 2,
    creator: "tz1Alice",
    description: "Quel protocole DeFi dominera Tezos en Q2 2025 ?",
    deadline: new Date(Date.now() - 3600 * 1000).toISOString(),
    options: ["Plenty", "Quipuswap", "Youves"],
    status: "resolved",
    winningOption: 1,
    totalPool: 200_000_000,
    bets: [],
  },
];

export default function Home() {
  const { address } = useWallet();
  const [predictions, setPredictions] = useState<Prediction[]>(DEMO_PREDICTIONS);
  const [filter,      setFilter]      = useState<PredictionStatus | "all">("all");
  const [search,      setSearch]      = useState("");
  const [showCreate,  setShowCreate]  = useState(false);
  const [loading,     setLoading]     = useState(false);

  const loadPredictions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPredictions();
      if (data.length > 0) setPredictions(data);
    } catch {
      // Contrat non déployé → démo
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPredictions(); }, [loadPredictions]);

  const filtered = predictions.filter((p) => {
    const matchFilter = filter === "all" || p.status === filter;
    const matchSearch = p.description.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  return (
    <div className="min-h-screen bg-oracle-void pt-24 pb-12">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-oracle-border bg-oracle-dark py-16">
        <div className="absolute inset-0 opacity-30"
          style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.4) 0%, transparent 70%)" }}
        />
        <div className="relative mx-auto max-w-7xl px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-oracle-purple/30 bg-oracle-purple/10 px-4 py-1.5 text-sm text-oracle-violet">
              <Zap className="h-3.5 w-3.5" />
              Marché de prédictions décentralisé — Ghostnet
            </div>
            <h1 className="font-oracle text-4xl font-black tracking-wider text-white md:text-6xl"
              style={{ textShadow: "0 0 40px rgba(167,139,250,0.4)" }}
            >
              THE ORACLE PROTOCOL
            </h1>
            <p className="mt-4 text-lg text-gray-400">
              Prédisez. Pariez. Prouvez votre prescience.
            </p>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-8 flex flex-wrap justify-center gap-8 text-center"
          >
            {[
              { label: "Prédictions actives", value: predictions.filter(p => p.status === "open").length },
              { label: "Volume total (ꜩ)",     value: (predictions.reduce((s, p) => s + p.totalPool, 0) / 1e6).toFixed(0) },
              { label: "Oracles actifs",       value: new Set(predictions.flatMap(p => p.bets.map(b => b.bettor))).size },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="font-oracle text-3xl font-bold text-oracle-glow">{value}</div>
                <div className="text-sm text-gray-500">{label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 pt-8">
        {/* Toolbar */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Rechercher une prédiction…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border border-oracle-border bg-oracle-card pl-9 pr-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-oracle-violet focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-3">
            {/* Filters */}
            <div className="flex items-center gap-1 rounded-xl border border-oracle-border bg-oracle-card p-1">
              <Filter className="ml-2 h-3.5 w-3.5 text-gray-500" />
              {FILTERS.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setFilter(value)}
                  className={[
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
                    filter === value
                      ? "bg-oracle-purple text-white"
                      : "text-gray-400 hover:text-white",
                  ].join(" ")}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Create button */}
            {address && (
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-oracle-purple to-oracle-violet px-4 py-2.5 text-sm font-bold text-white shadow-oracle-glow transition-all hover:opacity-90"
              >
                <Plus className="h-4 w-4" />
                Créer
              </button>
            )}
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-oracle-purple border-t-transparent" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-500">
            <span className="text-5xl">🔮</span>
            <p className="mt-4 text-lg">Aucune prédiction trouvée</p>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((pred) => (
              <PredictionCard
                key={pred.id}
                prediction={pred}
                onRefresh={loadPredictions}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {showCreate && (
        <CreatePredictionModal
          onClose={() => setShowCreate(false)}
          onCreated={loadPredictions}
        />
      )}
    </div>
  );
}
