import type { Config } from "tailwindcss";

// Design tokens transcribed from docs/ux/ux-spec.md §3 "Cross-cutting design
// system & tokens" (Figma variable collection `tokens`, 23 variables).
// Status colors use the UX-spec's *corrected* contrast values directly
// (§9 consolidated accessibility pass) rather than the originally-designed
// values, since the fixes are non-negotiable per the spec:
//   - status-green text is #166534 (not #15803D -- the on-#DCFCE7 subtitle
//     fix, ~5.2:1) so a single token is safe on both heading and subtitle use.
//   - text-muted is #64748B (not #94A3B8, which is reserved for on-dark
//     surfaces only per the spec).
export default {
  darkMode: "media",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#EEF2F6",
        surface: "#FFFFFF",
        subtle: "#F8FAFC",
        sidebar: "#0F172A",
        "text-primary": "#0F172A",
        "text-secondary": "#475569",
        "text-muted": "#64748B",
        status: {
          green: "#166534",
          "green-bg": "#DCFCE7",
          "green-border": "#86EFAC",
          red: "#B91C1C",
          "red-bg": "#FEE2E2",
          "red-border": "#FCA5A5",
          amber: "#B45309",
          "amber-bg": "#FEF3C7",
          "amber-border": "#FDE68A",
          info: "#1D4ED8",
          "info-bg": "#DBEAFE",
          "info-border": "#BFDBFE",
        },
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
