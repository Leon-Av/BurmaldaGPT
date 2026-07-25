import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Прокси запросов API на бэкенд (избегает проблем с CORS при локальной разработке).
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
