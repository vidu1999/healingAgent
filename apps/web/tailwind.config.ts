import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sentinel: {
          950: "#070a14",
          900: "#0b1220",
          800: "#11192b",
          700: "#1c273c",
          600: "#2d3a55",
          500: "#3e4f6e",
        },
        primary: "#8cbfff",
        "primary-foreground": "#000000",
        green: { 400: "#4ade80", 500: "#22c55e", 600: "#16a34a" },
        amber: { 400: "#fbbf24", 500: "#f59e0b", 600: "#d97706" },
        red: { 400: "#f87171", 500: "#ef4444", 600: "#dc2626" },
      },
      borderRadius: { xl: "0.75rem" },
    },
  },
  plugins: [],
};

export default config;
