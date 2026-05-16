// ─── Models / Types ───────────────────────────────────────────────────────────
export * from './models';

// ─── Dashboard Types ──────────────────────────────────────────────────────────
export type { Section, FormType, FormPayload } from './components/dashboard/types';

// ─── API ──────────────────────────────────────────────────────────────────────
export * from './api';

// ─── Supabase ─────────────────────────────────────────────────────────────────
export * from './supabase';

// ─── Toast ────────────────────────────────────────────────────────────────────
export * from './toast';

// ─── Components ───────────────────────────────────────────────────────────────
// Svelte components não são re-exportados aqui para evitar problemas de bundling.
// Importe-os diretamente via '$lib/components' ou '$lib/components/dashboard'.
