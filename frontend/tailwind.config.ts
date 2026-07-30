import type { Config } from "tailwindcss";

// Design tokens as CSS custom properties (see src/index.css for the light
// and `prefers-color-scheme: dark` value sets), following the shadcn/ui
// convention of `rgb(var(--token) / <alpha-value>)` so every semantic color
// name below picks up the active theme automatically -- no component ever
// hardcodes a hex value or a raw Tailwind gray. This is what makes
// light/dark a token-layer change, not a per-component rewrite.
//
// Palette shape: neutral surfaces + one accent (indigo) + semantic risk
// colors (green/amber/red) + info -- restrained on purpose (coordinator
// scope-change: "modern 2026-era design language ... restrained color").
export default {
  darkMode: "media",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        subtle: "rgb(var(--color-subtle) / <alpha-value>)",
        skeleton: "rgb(var(--color-skeleton) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        sidebar: "#0F172A", // persistent dark nav rail -- constant across themes by design
        "text-primary": "rgb(var(--color-text-primary) / <alpha-value>)",
        "text-secondary": "rgb(var(--color-text-secondary) / <alpha-value>)",
        "text-muted": "rgb(var(--color-text-muted) / <alpha-value>)",
        status: {
          green: "rgb(var(--status-green-text) / <alpha-value>)",
          "green-bg": "rgb(var(--status-green-bg) / <alpha-value>)",
          "green-border": "rgb(var(--status-green-border) / <alpha-value>)",
          red: "rgb(var(--status-red-text) / <alpha-value>)",
          "red-bg": "rgb(var(--status-red-bg) / <alpha-value>)",
          "red-border": "rgb(var(--status-red-border) / <alpha-value>)",
          amber: "rgb(var(--status-amber-text) / <alpha-value>)",
          "amber-bg": "rgb(var(--status-amber-bg) / <alpha-value>)",
          "amber-border": "rgb(var(--status-amber-border) / <alpha-value>)",
          info: "rgb(var(--status-info-text) / <alpha-value>)",
          "info-bg": "rgb(var(--status-info-bg) / <alpha-value>)",
          "info-border": "rgb(var(--status-info-border) / <alpha-value>)",
        },
      },
      borderRadius: {
        DEFAULT: "0.5rem",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 200ms ease-out",
      },
    },
  },
  plugins: [],
} satisfies Config;
