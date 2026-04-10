import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: "class", // 👈 required for next-themes + Tailwind dark support
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#111827",
        secondary: "#6B7280",
        accent: "#6366F1",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
