import path from "node:path"

import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// The API is same-origin in production: FastAPI mounts the built bundle at "/".
// In dev, proxy the API paths to the server on :8000 so no CORS is needed.
const apiPaths = ["/health", "/files", "/scrape", "/jobs"]

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: Object.fromEntries(
      apiPaths.map((route) => [route, { target: "http://localhost:8000", changeOrigin: true }]),
    ),
  },
})
