import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, Trash2 } from "lucide-react";
import { txCreatePrediction } from "../utils/contract";
import { useWallet } from "../context/WalletContext";
import toast from "react-hot-toast";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function CreatePredictionModal({ onClose, onCreated }: Props) {
  const { address } = useWallet();
  const [description, setDescription] = useState("");
  const [deadline, setDeadline]       = useState("");
  const [options, setOptions]         = useState<string[]>(["", ""]);
  const [loading, setLoading]         = useState(false);

  function addOption() {
    if (options.length < 6) setOptions([...options, ""]);
  }

  function removeOption(i: number) {
    if (options.length > 2) setOptions(options.filter((_, idx) => idx !== i));
  }

  function updateOption(i: number, value: string) {
    const next = [...options];
    next[i] = value;
    setOptions(next);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!address) return toast.error("Connectez votre wallet");
    if (!description.trim()) return toast.error("Description requise");
    if (!deadline) return toast.error("Deadline requise");
    const cleanOpts = options.filter((o) => o.trim());
    if (cleanOpts.length < 2) return toast.error("Au moins 2 options");

    setLoading(true);
    try {
      const op = await txCreatePrediction(description.trim(), deadline, cleanOpts);
      await op.confirmation(1);
      toast.success("Prédiction créée !");
      onCreated();
      onClose();
    } catch (err: any) {
      toast.error(err?.message ?? "Erreur lors de la création");
    } finally {
      setLoading(false);
    }
  }

  // Min datetime = maintenant + 1 heure
  const minDate = new Date(Date.now() + 3_600_000).toISOString().slice(0, 16);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-oracle-border bg-oracle-card shadow-oracle-purple"
        >
          {/* Header */}
          <div className="border-b border-oracle-border px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="font-oracle text-lg font-bold text-white">
                🔮 Nouvelle Prédiction
              </h2>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-oracle-surface hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Description */}
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">
                Votre prédiction
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                maxLength={280}
                placeholder="Bitcoin atteindra 200 000$ avant fin 2025 ?"
                className="w-full resize-none rounded-xl border border-oracle-border bg-oracle-surface px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-oracle-violet focus:outline-none"
              />
              <div className="mt-1 text-right text-xs text-gray-600">
                {description.length}/280
              </div>
            </div>

            {/* Deadline */}
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">
                Deadline
              </label>
              <input
                type="datetime-local"
                value={deadline}
                min={minDate}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full rounded-xl border border-oracle-border bg-oracle-surface px-4 py-3 text-sm text-white focus:border-oracle-violet focus:outline-none"
              />
            </div>

            {/* Options */}
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Options ({options.length}/6)
                </label>
                <button
                  type="button"
                  onClick={addOption}
                  disabled={options.length >= 6}
                  className="flex items-center gap-1 rounded-lg border border-oracle-border px-2 py-1 text-xs text-gray-400 hover:border-oracle-violet hover:text-oracle-violet disabled:opacity-40"
                >
                  <Plus className="h-3 w-3" /> Ajouter
                </button>
              </div>
              <div className="space-y-2">
                {options.map((opt, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={opt}
                      onChange={(e) => updateOption(i, e.target.value)}
                      placeholder={`Option ${i + 1}`}
                      maxLength={80}
                      className="flex-1 rounded-xl border border-oracle-border bg-oracle-surface px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-oracle-violet focus:outline-none"
                    />
                    {options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => removeOption(i)}
                        className="rounded-lg p-2 text-gray-500 hover:bg-red-900/20 hover:text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gradient-to-r from-oracle-purple to-oracle-violet py-3 font-bold text-white shadow-oracle-glow transition-all hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Envoi en cours…" : "Créer la prédiction"}
            </button>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
