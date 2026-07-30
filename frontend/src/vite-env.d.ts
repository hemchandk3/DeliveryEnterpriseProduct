/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PROJECT_ID?: string;
  readonly VITE_SPRINT_ID?: string;
  readonly VITE_DATA_PROVENANCE?: string;
  readonly VITE_BACKEND_ORIGIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
