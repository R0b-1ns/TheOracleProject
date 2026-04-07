import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Target, Trophy, Coins, Clock } from "lucide-react";
import { useWallet } from "../context/WalletContext";
import { fetchElo, fetchPredictions } from "../utils/contract";
import { getOracleRank, RANK_ICONS, RANK_COLORS } from "../types";
import { shortAddress, mutezToTez, timeRemaining } from "../utils/tezos";
import EloRing from "../components/EloRing";
import type { Prediction } from "../types";

interface Stats {
  elo: number;
  predictions: number;
  wins: number;
  totalWagered: number;
  pendingClaims: number;
}

const RANK_THRESHOLDS = [
  { rank: "Apprenti Oracle",     min: 0,    max: 1099, color: "bg-gray-500" },
  { rank: "Voyant",              min: 1100, max: 1299, color: "bg-teal-500" },
  { rank: "Prophète",            min: 1300, max: 1599, color: "bg-violet-500" },
  { rank: "Architecte du Futur", min: 1600, max: 9999, color: "bg-amber-500" },
];

export default function Profile() {
  const { address, elo, rank } = useWallet();
  const [stats,       setStats]       = useState<Stats>({ elo: 1000, predictions: 0, wins: 0, totalWagered: 0, pendingClaims: 0 });
  const [myBets,      setMyBets]      = useState<{ pred: Prediction; betIdx: number }[]>([]);
  const [loading,     setLoading]     = useState(false);

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    Promise.all([fetchElo(address), fetchPredictions()])
      .then(([eloScore, preds]) => {
        let wins = 0;
        let wagered = 0;
        let pending = 0;
        const bets: typeof myBets = [];

        for (const pred of preds) {
          pred.bets.forEach((b, idx) => {
            if (b.bettor === address) {
              wagered += b.amount;
              bets.push({ pred, betIdx: idx });
              if (pred.status === "resolved" && pred.winningOption === b.choice) {
                wins++;
                if (!b.claimed) pending++;
              }
            }
          });
        }

        setStats({ elo: eloScore, predictions: bets.length, wins, totalWagered: wagered, pendingClaims: pending });
        setMyBets(bets);
      })
      .catch(() => {
        // Mode démo
        setStats({ elo, predictions: 7, wins: 5, totalWagered: 45_000_000, pendingClaims: 1 });
      })
      .finally(() => setLoading(false));
  }, [address, elo]);

  if (!address) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-oracle-void pt-16">
        <span className="text-6xl">🔮</span>
        <h2 className="mt-4 font-oracle text-2xl font-bold text-white">
          Connectez votre wallet
        </h2>
        <p className="mt-2 text-gray-500">
          Pour accéder à votre profil Oracle.
        </p>
      </div>
    );
  }

  const nextRankIdx = RANK_THRESHOLDS.findIndex((r) => stats.elo < r.max);
  const currentTier = RANK_THRESHOLDS[Math.max(0, nextRankIdx - 1)] ?? RANK_THRESHOLDS[RANK_THRESHOLDS.length - 1];
  const nextTier    = RANK_THRESHOLDS[nextRankIdx];
  const progress    = nextTier
    ? ((stats.elo - currentTier.min) / (nextTier.min - currentTier.min)) * 100
    : 100;

  return (
    <div className="min-h-screen bg-oracle-void pb-16 pt-24">
      <div className="mx-auto max-w-4xl px-4">
        {/* Profile header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 overflow-hidden rounded-2xl border border-oracle-border bg-oracle-card"
        >
          {/* Banner */}
          <div
            className="h-28"
            style={{
              background: "linear-gradient(135deg, rgba(124,58,237,0.3) 0%, rgba(245,158,11,0.2) 100%)",
            }}
          />

          <div className="relative px-6 pb-6">
            {/* Avatar + ELO ring */}
            <div className="absolute -top-12 left-6">
              <EloRing elo={stats.elo} size={96} />
            </div>

            <div className="ml-28 pt-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h1 className="font-oracle text-2xl font-bold text-white">
                    {shortAddress(address)}
                  </h1>
                  <div className={`mt-1 flex items-center gap-2 text-sm ${RANK_COLORS[rank]}`}>
                    <span>{RANK_ICONS[rank]}</span>
                    <span className="font-semibold">{rank}</span>
                  </div>
                </div>

                {stats.pendingClaims > 0 && (
                  <div className="rounded-full border border-oracle-gold bg-oracle-gold/10 px-4 py-1.5 text-sm font-semibold text-oracle-gold">
                    ✨ {stats.pendingClaims} gain{stats.pendingClaims > 1 ? "s" : ""} à réclamer
                  </div>
                )}
              </div>

              {/* ELO progress bar */}
              <div className="mt-4">
                <div className="mb-1.5 flex items-center justify-between text-xs text-gray-500">
                  <span>{rank}</span>
                  {nextTier ? (
                    <span>Prochain rang : {nextTier.rank} ({nextTier.min} ELO)</span>
                  ) : (
                    <span>Rang maximum atteint !</span>
                  )}
                </div>
                <div className="h-2 rounded-full bg-oracle-surface">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full rounded-full bg-gradient-to-r from-oracle-purple to-oracle-violet"
                  />
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Stats grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4"
        >
          {[
            { icon: TrendingUp, label: "Score ELO",  value: stats.elo,                   color: "text-oracle-violet" },
            { icon: Target,     label: "Paris",       value: stats.predictions,            color: "text-oracle-teal" },
            { icon: Trophy,     label: "Victoires",   value: stats.wins,                  color: "text-oracle-gold" },
            { icon: Coins,      label: "Misé (ꜩ)",   value: mutezToTez(stats.totalWagered), color: "text-emerald-400" },
          ].map(({ icon: Icon, label, value, color }) => (
            <div
              key={label}
              className="rounded-2xl border border-oracle-border bg-oracle-card p-5 text-center"
            >
              <Icon className={`mx-auto mb-2 h-5 w-5 ${color}`} />
              <div className={`font-oracle text-2xl font-bold ${color}`}>{value}</div>
              <div className="mt-1 text-xs text-gray-500">{label}</div>
            </div>
          ))}
        </motion.div>

        {/* Rank progression */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mb-8 rounded-2xl border border-oracle-border bg-oracle-card p-6"
        >
          <h2 className="mb-4 font-oracle text-lg font-bold text-white">
            Progression des rangs
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {RANK_THRESHOLDS.map((tier) => {
              const active = rank === tier.rank;
              return (
                <div
                  key={tier.rank}
                  className={[
                    "rounded-xl border p-3 text-center transition-all",
                    active
                      ? "border-oracle-violet bg-oracle-violet/10"
                      : "border-oracle-border bg-oracle-surface opacity-60",
                  ].join(" ")}
                >
                  <div className="text-2xl mb-1">
                    {RANK_ICONS[tier.rank as keyof typeof RANK_ICONS]}
                  </div>
                  <div className={`text-xs font-semibold ${active ? RANK_COLORS[rank] : "text-gray-500"}`}>
                    {tier.rank}
                  </div>
                  <div className="mt-1 text-xs text-gray-600">{tier.min}+ ELO</div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* My bets history */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="rounded-2xl border border-oracle-border bg-oracle-card p-6"
        >
          <h2 className="mb-4 font-oracle text-lg font-bold text-white">
            Historique des paris
          </h2>
          {loading ? (
            <div className="flex h-20 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-oracle-purple border-t-transparent" />
            </div>
          ) : myBets.length === 0 ? (
            <p className="text-center text-gray-500">Aucun pari pour l'instant.</p>
          ) : (
            <div className="space-y-3">
              {myBets.map(({ pred, betIdx }) => {
                const bet = pred.bets[betIdx];
                const isWin = pred.status === "resolved" && pred.winningOption === bet.choice;
                const isLoss = pred.status === "resolved" && pred.winningOption !== bet.choice;
                return (
                  <div
                    key={`${pred.id}-${betIdx}`}
                    className={[
                      "flex items-center justify-between gap-4 rounded-xl border p-4",
                      isWin  ? "border-emerald-500/30 bg-emerald-500/5"  : "",
                      isLoss ? "border-red-500/30 bg-red-500/5"           : "",
                      !isWin && !isLoss ? "border-oracle-border bg-oracle-surface" : "",
                    ].join(" ")}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-sm font-medium text-white">{pred.description}</p>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
                        <span>Option : {pred.options[bet.choice]}</span>
                        <span>·</span>
                        <span>Confiance : {bet.confidence}%</span>
                        <span>·</span>
                        <span className="flex items-center gap-0.5">
                          <Clock className="h-3 w-3" />
                          {timeRemaining(pred.deadline)}
                        </span>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-bold text-white">
                        {mutezToTez(bet.amount)} ꜩ
                      </div>
                      <div className={`text-xs font-semibold ${
                        isWin ? "text-emerald-400" : isLoss ? "text-red-400" : "text-gray-500"
                      }`}>
                        {isWin ? (bet.claimed ? "✓ Réclamé" : "✨ Gagné") : isLoss ? "✗ Perdu" : "En attente"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
