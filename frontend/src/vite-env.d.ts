/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Public URL of the API in production, e.g. https://stocklens-api.onrender.com. Empty in dev (Vite proxy). */
  readonly VITE_API_BASE_URL?: string;
}
