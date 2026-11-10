import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  // Reads VITE_API_TARGET from the environment (set in docker-compose) or a .env file.
  const env = loadEnv(mode, ".", "");
  const apiTarget = env.VITE_API_TARGET || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/health": apiTarget,
        "/api": apiTarget,
      },
    },
  };
});
