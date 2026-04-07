// Anneau ELO animé — composant de profil

interface Props {
  elo: number;
  size?: number;
}

export default function EloRing({ elo, size = 120 }: Props) {
  // Normalise l'ELO entre 0 et 1 (plage de référence 800–2000)
  const normalised = Math.min(1, Math.max(0, (elo - 800) / 1200));
  const circumference = 2 * Math.PI * 45; // r=45
  const dashOffset = circumference * (1 - normalised);

  let color = "#6b7280"; // gray
  if (elo >= 1600) color = "#f59e0b"; // gold
  else if (elo >= 1300) color = "#8b5cf6"; // violet
  else if (elo >= 1100) color = "#14b8a6"; // teal

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg
        viewBox="0 0 100 100"
        width={size}
        height={size}
        className="-rotate-90"
      >
        {/* Track */}
        <circle
          cx="50" cy="50" r="45"
          fill="none"
          stroke="#1a1a2e"
          strokeWidth="8"
        />
        {/* Progress */}
        <circle
          cx="50" cy="50" r="45"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 1s ease-in-out", filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-oracle text-xl font-bold text-white">{elo}</span>
        <span className="text-xs text-gray-500">ELO</span>
      </div>
    </div>
  );
}
