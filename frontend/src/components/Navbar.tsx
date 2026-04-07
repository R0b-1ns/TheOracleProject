import { Link, useLocation } from "react-router-dom";
import { useWallet } from "../context/WalletContext";
import { shortAddress } from "../utils/tezos";
import { RANK_ICONS } from "../types";

export default function Navbar() {
  const { address, elo, rank, connecting, connect, disconnect } = useWallet();
  const { pathname } = useLocation();

  const navLinks = [
    { to: "/",             label: "Prédictions" },
    { to: "/leaderboard",  label: "Leaderboard" },
    { to: "/profile",      label: "Mon Profil" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-oracle-border bg-oracle-dark/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🔮</span>
            <span
              className="font-oracle text-lg font-bold tracking-wider"
              style={{ background: "linear-gradient(135deg, #a78bfa, #f59e0b)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}
            >
              The Oracle Protocol
            </span>
          </Link>

          {/* Navigation links */}
          <div className="hidden items-center gap-1 md:flex">
            {navLinks.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={[
                  "rounded-md px-4 py-2 text-sm font-medium transition-all duration-200",
                  pathname === to
                    ? "bg-oracle-purple/20 text-oracle-glow"
                    : "text-gray-400 hover:bg-oracle-surface hover:text-white",
                ].join(" ")}
              >
                {label}
              </Link>
            ))}
          </div>

          {/* Wallet */}
          <div className="flex items-center gap-3">
            {address ? (
              <div className="flex items-center gap-3">
                {/* ELO badge */}
                <div className="hidden items-center gap-2 rounded-full border border-oracle-border bg-oracle-card px-3 py-1 sm:flex">
                  <span className="text-sm">{RANK_ICONS[rank]}</span>
                  <span className="font-oracle text-xs text-oracle-glow">{elo}</span>
                  <span className="text-xs text-gray-500">ELO</span>
                </div>

                {/* Address + disconnect */}
                <div className="group relative">
                  <button className="rounded-full border border-oracle-purple/40 bg-oracle-purple/10 px-4 py-1.5 text-sm font-medium text-oracle-violet transition-all hover:border-oracle-purple hover:bg-oracle-purple/20">
                    {shortAddress(address)}
                  </button>
                  <div className="absolute right-0 top-full mt-2 hidden min-w-max rounded-lg border border-oracle-border bg-oracle-card p-2 group-hover:block">
                    <button
                      onClick={disconnect}
                      className="w-full rounded px-4 py-2 text-left text-sm text-red-400 hover:bg-red-900/20"
                    >
                      Déconnecter
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <button
                onClick={connect}
                disabled={connecting}
                className="relative overflow-hidden rounded-full border border-oracle-purple bg-oracle-purple/20 px-5 py-2 text-sm font-semibold text-oracle-violet shadow-oracle-glow transition-all duration-300 hover:bg-oracle-purple/40 hover:shadow-lg disabled:opacity-50"
              >
                {connecting ? "Connexion…" : "Connecter Wallet"}
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
