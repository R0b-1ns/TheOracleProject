// ---------------------------------------------------------------------------
// Utilitaires Tezos
// ---------------------------------------------------------------------------

/** Formate une adresse tz1... en version courte : tz1ABC...XYZ */
export function shortAddress(addr: string): string {
  if (!addr || addr.length < 10) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

/** Convertit des mutez en tez (string avec 6 décimales max) */
export function mutezToTez(mutez: number): string {
  return (mutez / 1_000_000).toLocaleString("fr-FR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 6,
  });
}

/** Convertit des tez en mutez */
export function tezToMutez(tez: number): number {
  return Math.floor(tez * 1_000_000);
}

/** Formate un timestamp ISO en date lisible française */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Retourne "dans X jours" ou "terminé" */
export function timeRemaining(deadline: string): string {
  const now  = Date.now();
  const end  = new Date(deadline).getTime();
  const diff = end - now;

  if (diff <= 0) return "Terminé";

  const hours   = Math.floor(diff / (1000 * 60 * 60));
  const days    = Math.floor(hours / 24);
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (days > 0)  return `${days}j ${hours % 24}h restantes`;
  if (hours > 0) return `${hours}h ${minutes}min restantes`;
  return `${minutes} min restantes`;
}

/** Calcule le taux de victoire */
export function winRate(wins: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((wins / total) * 100);
}

/** Couleur d'un badge ELO */
export function eloBadgeColor(elo: number): string {
  if (elo >= 1600) return "from-yellow-400 to-amber-600";
  if (elo >= 1300) return "from-violet-500 to-purple-700";
  if (elo >= 1100) return "from-teal-400 to-cyan-600";
  return "from-gray-500 to-gray-700";
}
