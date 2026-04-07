import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Trophy, TrendingUp, Zap } from "lucide-react";
import { fetchLeaderboard } from "../utils/contract";
import { useWallet } from "../context/WalletContext";
import { getOracleRank, RANK_ICONS, RANK_COLORS } from "../types";
import { shortAddress, eloBadgeColor, winRate } from "../utils/tezos";
import type { LeaderboardEntry } from "../types";

// Démo data
const DEMO_LEADERBOARD: LeaderboardEntry[] = [
  { rank: 1, address: "tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb", elo: 1842, oracleRank: "Architecte du Futur", wins: 34, predictions: 40, winRate: 85 },
  { rank: 2, address: "tz1aSkwEot3L2kmUenu8Ann6Transformers", elo: 1654, oracleRank: "Architecte du Futur", wins: 28, predictions: 35, winRate: 80 },
  { rank: 3, address: "tz1bLiquidityProvider9x8mNaBcDefGhi", elo: 1521, oracleRank: "Prophète",            wins: 22, predictions: 30, winRate: 73 },
  { rank: 4, address: "tz1cGhostnetTester7y6nMlOpQrStUvWx",   elo: 1388, oracleRank: "Prophète",            wins: 18, predictions: 27, winRate: 67 },
  { rank: 5, address: "tz1dDecentralizedOracle5z4kJkLmNoPq",  elo: 1247, oracleRank: "Voyant",              wins: 15, predictions: 24, winRate: 63 },
  { rank: 6, address: "tz1eSmartContractDev3w2iHiJkKlMnOp",   elo: 1180, oracleRank: "Voyant",              wins: 12, predictions: 20, winRate: 60 },
  { rank: 7, address: "tz1fTezosMaximalist1u0gFfGhHiIjJkKl",  elo: 1092, oracleRank: "Apprenti Oracle",    wins: 8,  predictions: 15, winRate: 53 },
  { rank: 8, address: "tz1gNewcomer0tx9eEdEeFfGgHhIiJjKkLl",  elo: 1021, oracleRank: "Apprenti Oracle",    wins: 4,  predictions: 10, winRate: 40 },
];

const MEDAL: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

export default function Leaderboard() {
  const { address } = useWallet();
  const [entries,  setEntries]  = useState<LeaderboardEntry[]>(DEMO_LEADERBOARD);
  const [loading,  setLoading]  = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchLeaderboard()
      .then((data) => { if (data.length > 0) setEntries(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const myEntry = address ? entries.find((e) => e.address === address) : null;

  return (
    <div className="min-h-screen bg-oracle-void pb-16 pt-24">
      <div className="mx-auto max-w-4xl px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 text-center"
        >
          <div className="mb-3 text-5xl">🏆</div>
          <h1 className="font-oracle text-4xl font-black tracking-wider text-white">
            HALL DES ORACLES
          </h1>
          <p className="mt-3 text-gray-500">
            Les prophètes les plus précis du protocole
          </p>
        </motion.div>

        {/* My rank highlight */}
        {myEntry && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 rounded-2xl border border-oracle-violet bg-oracle-violet/10 p-4"
          >
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-oracle-violet bg-oracle-violet/20 text-sm font-bold text-oracle-violet">
                #{myEntry.rank}
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold text-white">
                  Votre position {RANK_ICONS[myEntry.oracleRank]}
                </div>
                <div className="text-xs text-gray-500">{shortAddress(myEntry.address)}</div>
              </div>
              <div className="text-right">
                <div className="font-oracle text-xl font-bold text-oracle-glow">{myEntry.elo}</div>
                <div className="text-xs text-gray-500">ELO</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Top 3 podium */}
        {entries.length >= 3 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8 grid grid-cols-3 gap-4"
          >
            {/* 2nd place */}
            <div className="mt-6 flex flex-col items-center rounded-2xl border border-gray-500/30 bg-gray-500/5 p-4">
              <div className="text-3xl mb-1">{MEDAL[2]}</div>
              <div className={`text-sm font-semibold ${RANK_COLORS[entries[1].oracleRank]}`}>
                {RANK_ICONS[entries[1].oracleRank]}
              </div>
              <div className="mt-2 text-xs text-gray-400">{shortAddress(entries[1].address)}</div>
              <div className="mt-1 font-oracle text-xl font-bold text-white">{entries[1].elo}</div>
              <div className="text-xs text-gray-600">ELO</div>
            </div>

            {/* 1st place */}
            <div
              className="flex flex-col items-center rounded-2xl border p-5"
              style={{
                borderColor: "rgba(245,158,11,0.5)",
                background: "radial-gradient(ellipse at top, rgba(245,158,11,0.1), transparent 70%)",
                boxShadow: "0 0 30px rgba(245,158,11,0.15)",
              }}
            >
              <div className="text-4xl mb-1">{MEDAL[1]}</div>
              <div className={`text-sm font-semibold ${RANK_COLORS[entries[0].oracleRank]}`}>
                {RANK_ICONS[entries[0].oracleRank]} {entries[0].oracleRank}
              </div>
              <div className="mt-2 text-xs text-gray-300">{shortAddress(entries[0].address)}</div>
              <div className="mt-1 font-oracle text-3xl font-bold text-oracle-gold">{entries[0].elo}</div>
              <div className="text-xs text-gray-500">ELO</div>
            </div>

            {/* 3rd place */}
            <div className="mt-6 flex flex-col items-center rounded-2xl border border-orange-700/30 bg-orange-900/5 p-4">
              <div className="text-3xl mb-1">{MEDAL[3]}</div>
              <div className={`text-sm font-semibold ${RANK_COLORS[entries[2].oracleRank]}`}>
                {RANK_ICONS[entries[2].oracleRank]}
              </div>
              <div className="mt-2 text-xs text-gray-400">{shortAddress(entries[2].address)}</div>
              <div className="mt-1 font-oracle text-xl font-bold text-white">{entries[2].elo}</div>
              <div className="text-xs text-gray-600">ELO</div>
            </div>
          </motion.div>
        )}

        {/* Full table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="overflow-hidden rounded-2xl border border-oracle-border bg-oracle-card"
        >
          {/* Table header */}
          <div className="grid grid-cols-[3rem_1fr_auto_auto_auto] gap-4 border-b border-oracle-border px-6 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
            <span>#</span>
            <span>Oracle</span>
            <span className="hidden text-center sm:block">ELO</span>
            <span className="hidden text-center sm:block">Victoires</span>
            <span className="text-center">Win%</span>
          </div>

          {loading ? (
            <div className="flex h-40 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-oracle-purple border-t-transparent" />
            </div>
          ) : (
            <div>
              {entries.map((entry, i) => {
                const isMe = entry.address === address;
                return (
                  <motion.div
                    key={entry.address}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className={[
                      "grid grid-cols-[3rem_1fr_auto_auto_auto] items-center gap-4 border-b border-oracle-border/40 px-6 py-4 transition-colors",
                      isMe
                        ? "bg-oracle-violet/10"
                        : "hover:bg-oracle-surface/50",
                      i === entries.length - 1 ? "border-b-0" : "",
                    ].join(" ")}
                  >
                    {/* Rank */}
                    <div className="font-oracle text-lg font-bold">
                      {MEDAL[entry.rank] ?? (
                        <span className="text-gray-500">#{entry.rank}</span>
                      )}
                    </div>

                    {/* Oracle info */}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">
                          {shortAddress(entry.address)}
                          {isMe && (
                            <span className="ml-2 rounded-full bg-oracle-violet/20 px-2 py-0.5 text-xs text-oracle-violet">
                              Vous
                            </span>
                          )}
                        </span>
                      </div>
                      <div className={`text-xs ${RANK_COLORS[entry.oracleRank]}`}>
                        {RANK_ICONS[entry.oracleRank]} {entry.oracleRank}
                      </div>
                    </div>

                    {/* ELO */}
                    <div className="hidden text-center sm:block">
                      <span
                        className={`inline-block rounded-full bg-gradient-to-r ${eloBadgeColor(entry.elo)} px-3 py-0.5 font-oracle text-sm font-bold text-white`}
                      >
                        {entry.elo}
                      </span>
                    </div>

                    {/* Wins */}
                    <div className="hidden text-center text-sm text-gray-300 sm:block">
                      <Trophy className="mx-auto mb-0.5 h-3.5 w-3.5 text-oracle-gold" />
                      {entry.wins}/{entry.predictions}
                    </div>

                    {/* Win rate */}
                    <div className="text-center">
                      <div className="text-sm font-bold text-white">{entry.winRate}%</div>
                      <div className="mx-auto mt-1 h-1 w-12 rounded-full bg-oracle-surface">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-oracle-teal to-oracle-violet"
                          style={{ width: `${entry.winRate}%` }}
                        />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Legend */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 rounded-xl border border-oracle-border bg-oracle-card p-4"
        >
          <div className="flex flex-wrap gap-4 text-sm">
            {(["Apprenti Oracle", "Voyant", "Prophète", "Architecte du Futur"] as const).map((r) => (
              <div key={r} className="flex items-center gap-2">
                <span>{RANK_ICONS[r]}</span>
                <span className={RANK_COLORS[r]}>{r}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
