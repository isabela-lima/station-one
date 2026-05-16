# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

**Station One** é um dashboard pessoal PWA estilo "space station" — relógio, clima, operações (tarefas/notas/links), missões (metas + marcos), protocolos (hábitos com streak), log diário, wishlist e finanças. Tema escuro com glassmorphism, acentos ciano/roxo.

- **Notion (planejamento):** https://www.notion.so/361ba7a32d94810baa54f3fd05f70dcf
- **Kanban de tarefas:** https://www.notion.so/e52fa9959a554f9ab97a47b855de5635

## Comandos

```bash
pnpm dev          # servidor de desenvolvimento (localhost:5173)
pnpm build        # build de produção
pnpm preview      # preview do build
pnpm check        # type-check com svelte-check
pnpm check:watch  # type-check em modo watch
pnpm lint         # verificar formatação (Prettier)
pnpm format       # formatar código

./bin/pocketbase serve  # NÃO USADO — backend é FastAPI + Supabase
```

O backend FastAPI deve estar rodando em `http://localhost:8000` (variável `PUBLIC_API_URL`).

## Arquitetura

### Duas camadas de backend

| Responsabilidade | Onde |
|---|---|
| Auth, realtime, DB direto | Supabase (`src/lib/supabase.ts`) |
| Lógica de negócio (finanças, hábitos, etc.) | FastAPI (`src/lib/api.ts`) |

Toda chamada ao FastAPI passa o JWT do Supabase no header `Authorization: Bearer <token>` via `getAuthToken()` de `supabase.ts`.

### Fluxo de dados no dashboard (`src/routes/+page.svelte`)

1. `onMount` → busca todos os dados via `api.*` em paralelo com `Promise.all`
2. Supabase realtime via `postgres_changes` mantém sincronização ao vivo para `items`, `goals`, `milestones`, `wishlist`, `habits`
3. Todo estado é Svelte 5 `$state` — sem stores externos exceto `toasts` (writable store em `toast.ts`)
4. `onDestroy` limpa todas as subscriptions do Supabase

### Formulário unificado

`AddForm.svelte` é o único ponto de criação de qualquer entidade. O tipo é controlado pelo union discriminado `FormPayload` (`src/lib/components/dashboard/types.ts`). O dashboard recebe o payload via prop `onSubmit` e roteila para a API correta.

```ts
// FormPayload — sempre use o campo `kind` para discriminar
type FormPayload =
  | { kind: 'item'; type: 'note' | 'task' | 'link'; ... }
  | { kind: 'goal'; title: string }
  | { kind: 'milestone'; title: string; goal_id: string }
  | { kind: 'wishlist'; ... }
  | { kind: 'transaction'; ... }
  | { kind: 'wallet'; ... }
  | { kind: 'habit'; name: string; emoji: string }
```

### Navegação/layout

- **Desktop:** `AppSidebar` (fixo à direita) com nav entre seções + formulário dinâmico
- **Mobile:** `MobileNav` (bottom bar) + `MobileSheet` (bottom sheet com formulário)
- Seção ativa controlada pelo tipo `Section = 'operations' | 'missions' | 'wishlist' | 'finance' | 'protocols'`

## Design System

**Tema DaisyUI customizado `station`** definido em `src/routes/layout.css`:
- `base-100: #0a0a12` (fundo principal)
- `primary: #06b6d4` (ciano)
- `secondary: #8b5cf6` (roxo)

**Classes utilitárias locais:**
- `.glass-card` — card glassmorphism base (use em todo card novo)
- `.glass-sidebar` — variante para sidebar
- `.card-enter` — animação de entrada com delay via `style="animation-delay: {index * 50}ms"`
- `.skeleton-pulse` — loading skeleton

**Ícones:** sempre use `lucide-svelte`. Nunca adicione outra biblioteca de ícones.

## Svelte 5 — Padrões do Projeto

O projeto usa **runes mode** habilitado para todo código fora de `node_modules` (ver `svelte.config.js`).

```svelte
<!-- Estado reativo -->
let items = $state<Item[]>([]);

<!-- Derivados -->
const completedTasks = $derived(items.filter(i => i.completed));

<!-- Props de componente -->
let { item, onToggle, pending = false, index = 0 } = $props();

<!-- Callbacks em vez de createEventDispatcher -->
<ItemCard {item} onToggle={handleToggle} onDelete={handleDelete} />
```

Não use `export let`, `createEventDispatcher`, nem `on:event` — são Svelte 4.

## Importações

```ts
// Tipos e utilitários — via $lib
import type { Item, Goal, FormPayload, Section } from '$lib';
import { showToast, supabase } from '$lib';
import * as api from '$lib/api';

// Componentes — direto, não via barrel
import ItemCard from '$lib/components/ItemCard.svelte';
import AppSidebar from '$lib/components/dashboard/AppSidebar.svelte';
```

Componentes Svelte não são re-exportados pelo barrel `$lib` (causaria problemas de bundling) — importe sempre pelo caminho direto.
