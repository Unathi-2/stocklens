// In development the Vite proxy forwards /api and /health, so the base is empty.
// In production the frontend and API live on different domains, so the build
// reads the API address from VITE_API_BASE_URL.
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
