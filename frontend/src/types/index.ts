// ---------------------------------------------------------------------------
// Types partagés — The Oracle Protocol
// ---------------------------------------------------------------------------

export type ConfidenceLevel = 50 | 75 | 95;

export type PredictionStatus = "open" | "closed" | "resolved";

export interface Bet {
  bettor: string;
  choice: number;
  amount: number;       // en mutez
  confidence: ConfidenceLevel;
  claimed: boolean;
}

export interface Prediction {
  id: number;
  creator: string;
  description: string;
  deadline: string;     // ISO string
  options: string[];
  status: PredictionStatus;
  winningOption: number | null;
  totalPool: number;    // en mutez
  bets: Bet[];
}

export type OracleRank =
  | "Apprenti Oracle"
  | "Voyant"
  | "Prophète"
  | "Architecte du Futur";

export interface OracleProfile {
  address: string;
  elo: number;
  rank: OracleRank;
  predictions: number;
  wins: number;
  totalWagered: number; // en mutez
}

export interface LeaderboardEntry {
  rank: number;
  address: string;
  elo: number;
  oracleRank: OracleRank;
  wins: number;
  predictions: number;
  winRate: number;
}

// Maps the raw on-chain status nat to a typed string
export const STATUS_MAP: Record<number, PredictionStatus> = {
  0: "open",
  1: "closed",
  2: "resolved",
};

// ELO → rang
export function getOracleRank(elo: number): OracleRank {
  if (elo < 1100) return "Apprenti Oracle";
  if (elo < 1300) return "Voyant";
  if (elo < 1600) return "Prophète";
  return "Architecte du Futur";
}

export const RANK_COLORS: Record<OracleRank, string> = {
  "Apprenti Oracle":       "text-gray-400",
  "Voyant":                "text-oracle-teal",
  "Prophète":              "text-oracle-violet",
  "Architecte du Futur":   "text-oracle-gold",
};

export const RANK_ICONS: Record<OracleRank, string> = {
  "Apprenti Oracle":       "🌙",
  "Voyant":                "👁️",
  "Prophète":              "🔮",
  "Architecte du Futur":   "⚡",
};

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  50: "Prudent",
  75: "Confiant",
  95: "Certain",
};

export const CONFIDENCE_MULTIPLIERS: Record<ConfidenceLevel, string> = {
  50: "×1",
  75: "×1.5",
  95: "×2",
};

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
  50: "text-oracle-teal border-oracle-teal",
  75: "text-oracle-violet border-oracle-violet",
  95: "text-oracle-gold border-oracle-gold",
};
