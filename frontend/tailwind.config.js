/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Palette mystique sombre
        oracle: {
          void:    "#0a0a0f",
          dark:    "#0f0f1a",
          surface: "#151520",
          card:    "#1a1a2e",
          border:  "#252540",
          purple:  "#7c3aed",
          violet:  "#8b5cf6",
          indigo:  "#6366f1",
          gold:    "#f59e0b",
          amber:   "#fbbf24",
          teal:    "#14b8a6",
          glow:    "#a78bfa",
        },
      },
      fontFamily: {
        oracle: ["'Cinzel'", "serif"],
        body:   ["'Inter'", "sans-serif"],
      },
      boxShadow: {
        "oracle-glow":   "0 0 20px rgba(124, 58, 237, 0.4)",
        "oracle-gold":   "0 0 20px rgba(245, 158, 11, 0.3)",
        "oracle-purple": "0 0 40px rgba(124, 58, 237, 0.2)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float":      "float 6s ease-in-out infinite",
        "shimmer":    "shimmer 2s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-10px)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
