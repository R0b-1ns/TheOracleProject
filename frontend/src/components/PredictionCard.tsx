import { useState } from "react";
import { motion } from "framer-motion";
import { Clock, Users, Coins } from "lucide-react";
import type { Prediction, ConfidenceLevel } from "../types";
import {
  CONFIDENCE_LABELS,
  CONFIDENCE_MULTIPLIERS,
  CONFIDENCE_COLORS,
} from "../types";
import { mutezToTez, timeRemaining } from "../utils/tezos";
import { useWallet } from "../context/WalletContext";
import { txPlaceBet } from "../utils/contract";
import toast from "react-hot-toast";

interface Props {
  prediction: Prediction;
  onRefresh?: () => void;
}

const STATUS_STYLE: Record<string, string> = {
  open:     "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
  closed:   "text-gray-400 bg-gray-400/10 border-gray-400/30",
  resolved: "text-oracle-gold bg-oracle-gold/10 border-oracle-gold/30",
};

const STATUS_LABEL: Record<string, string> = {
  open:     "En cours",
  closed:   "Fermée",
  resolved: "Résolue",
};

const CONFIDENCE_LEVELS: ConfidenceLevel[] = [50, 75, 95];

export default function PredictionCard({ prediction, onRefresh }: Props) {
  const { address } = useWallet();
  const [expanded,   setExpanded]   = useState(false);
  const [chosenOpt,  setChosenOpt]  = useState<number | null>(null);
  const [confidence, setConfidence] = useState<ConfidenceLevel>(50);
  const [amount,     setAmount]     = useState<string>("1");
  const [loading,    setLoading]    = useState(false);

  const isOpen   = prediction.status === "open";
  const timeLeft = timeRemaining(prediction.deadline);

  async function handleBet() {
    if (!address)         return toast.error("Connectez votre wallet");
    if (chosenOpt === null) return toast.error("Choisissez une option");
    const tez = parseFloat(amount);
    if (isNaN(tez) || tez <= 0) return toast.error("Montant invalide");

    setLoading(true);
    try {
      const op = await txPlaceBet(prediction.id, chosenOpt, confidence, tez);
      await op.confirmation(1);
      toast.success("Pari placé avec succès !");
      onRefresh?.();
      setExpanded(false);
    } catch (err: any) {
      toast.error(err?.message ?? "Erreur lors du pari");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative overflow-hidden rounded-2xl border border-oracle-border bg-oracle-card transition-all duration-300 hover:border-oracle-purple/50 hover:shadow-oracle-purple"
    >
      {/* Top glow accent */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-oracle-purple/60 to-transparent" />

      <div className="p-5">
        {/* Header */}
        <div className="mb-3 flex items-start justify-between gap-3">
          <h3 className="font-oracle text-base font-semibold leading-snug text-white">
            {prediction.description}
          </h3>
          <span
            className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[prediction.status]}`}
          >
            {STATUS_LABEL[prediction.status]}
          </span>
        </div>

        {/* Stats */}
        <div className="mb-4 flex flex-wrap gap-4 text-sm text-gray-400">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-oracle-purple" />
            <span>{timeLeft}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5 text-oracle-teal" />
            <span>{prediction.bets.length} paris</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Coins className="h-3.5 w-3.5 text-oracle-gold" />
            <span>{mutezToTez(prediction.totalPool)} ꜩ</span>
          </div>
        </div>

        {/* Options */}
        <div className="mb-4 grid grid-cols-2 gap-2">
          {prediction.options.map((opt, idx) => {
            const totalVotes = prediction.bets.filter((b) => b.choice === idx).length;
            const pct =
              prediction.bets.length === 0
                ? 50
                : Math.round((totalVotes / prediction.bets.length) * 100);
            const isWinner = prediction.status === "resolved" && prediction.winningOption === idx;

            return (
              <button
                key={idx}
                onClick={() => isOpen && setChosenOpt(idx)}
                disabled={!isOpen}
                className={[
                  "relative overflow-hidden rounded-xl border p-3 text-left text-sm transition-all",
                  isOpen && chosenOpt === idx
                    ? "border-oracle-violet bg-oracle-violet/20 text-white"
                    : isWinner
                    ? "border-oracle-gold bg-oracle-gold/10 text-oracle-gold"
                    : "border-oracle-border bg-oracle-surface text-gray-300 hover:border-oracle-border/80",
                ].join(" ")}
              >
                <div className="relative z-10">
                  <div className="font-medium">{opt}</div>
                  <div className="mt-1 text-xs opacity-70">{pct}% des paris</div>
                </div>
                {/* Progress bar */}
                <div
                  className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-oracle-purple to-oracle-violet opacity-40"
                  style={{ width: `${pct}%` }}
                />
              </button>
            );
          })}
        </div>

        {/* Bet panel (open only) */}
        {isOpen && (
          <div>
            <button
              onClick={() => setExpanded((v) => !v)}
              className="w-full rounded-xl border border-oracle-purple/30 bg-oracle-purple/10 py-2 text-sm font-semibold text-oracle-violet transition-all hover:bg-oracle-purple/20"
            >
              {expanded ? "Annuler" : "Placer un pari"}
            </button>

            {expanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mt-4 space-y-4"
              >
                {/* Confidence */}
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Niveau de confiance
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {CONFIDENCE_LEVELS.map((lvl) => (
                      <button
                        key={lvl}
                        onClick={() => setConfidence(lvl)}
                        className={[
                          "rounded-lg border py-2 text-center text-sm transition-all",
                          confidence === lvl
                            ? `border ${CONFIDENCE_COLORS[lvl]} bg-current/10 font-bold`
                            : "border-oracle-border text-gray-400 hover:border-gray-500",
                        ].join(" ")}
                      >
                        <div className={confidence === lvl ? CONFIDENCE_COLORS[lvl].split(" ")[0] : ""}>
                          {lvl}%
                        </div>
                        <div className="text-xs opacity-70">
                          {CONFIDENCE_LABELS[lvl]}
                        </div>
                        <div className="text-xs font-bold opacity-80">
                          {CONFIDENCE_MULTIPLIERS[lvl]}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Amount */}
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Montant (ꜩ)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="flex-1 rounded-lg border border-oracle-border bg-oracle-surface px-3 py-2 text-sm text-white focus:border-oracle-violet focus:outline-none"
                      placeholder="1.0"
                    />
                    {[1, 5, 10].map((v) => (
                      <button
                        key={v}
                        onClick={() => setAmount(String(v))}
                        className="rounded-lg border border-oracle-border bg-oracle-surface px-3 py-2 text-xs text-gray-400 hover:border-oracle-violet hover:text-white"
                      >
                        {v}ꜩ
                      </button>
                    ))}
                  </div>
                </div>

                {/* Submit */}
                <button
                  onClick={handleBet}
                  disabled={loading || chosenOpt === null}
                  className="w-full rounded-xl bg-gradient-to-r from-oracle-purple to-oracle-violet py-3 text-sm font-bold text-white shadow-oracle-glow transition-all hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading
                    ? "Transaction en cours…"
                    : chosenOpt === null
                    ? "Choisissez une option"
                    : `Miser ${amount} ꜩ sur "${prediction.options[chosenOpt]}" (${confidence}%)`}
                </button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
