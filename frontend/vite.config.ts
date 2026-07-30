import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Techwave Delivery Intelligence -- frontend build config.
// See ARCHITECTURE.md §5.6 for the backend HTTP contract this dev proxy
// forwards to. The frontend never talks to the backend origin directly in
// dev -- it calls same-origin `/api/*`, and Vite proxies to the FastAPI
// server, stripping the `/api` prefix (backend routes are unprefixed, e.g.
// `GET /projects/{id}/risks`). This keeps `api/client.ts` origin-agnostic
// and avoids CORS entirely in dev.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_ORIGIN || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/api/, ""),
      },
    },
  },
});
