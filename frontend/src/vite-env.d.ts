/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de la API (vacía = mismo origen) */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
