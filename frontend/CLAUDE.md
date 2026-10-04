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
2. Supabase realtime via `postgres_changes` mantém sincronização ao vivo para `items`, `goals`, `milestones`, `wishlist` (aplicando a linha do evento) e `habits`/`habit_completions` (refetch via API, porque `streak`/`completed_today` são calculados no backend)
3. Toda chamada à API envia `X-Timezone` — o backend usa para saber o "hoje" do usuário (dependência `Today` em `api/deps.py`)
4. Todo estado é Svelte 5 `$state` — sem stores externos exceto `toasts` (writable store em `toast.ts`)
5. `onDestroy` limpa todas as subscriptions do Supabase

### Formulário unificado

`AddForm.svelte` é o único ponto de criação de qualquer entidade; ele é aberto pelo botão **Novo** dentro de `CreateDialog.svelte` (um `<dialog>` nativo, que vira folha inferior no celular). O tipo é controlado pelo union discriminado `FormPayload` (`src/lib/components/dashboard/types.ts`). O dashboard recebe o payload via prop `onSubmit` e roteila para a API correta.

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

- `AppHeader` no topo: chips das seções (rolam na horizontal no celular), botão **Novo** e menu do avatar (tema + sair).
- Seção ativa controlada pelo tipo `Section` (`'today' | 'operations' | ...`); a ordem, rótulo, ícone e cor de cada seção ficam em `SECTIONS` (`dashboard/types.ts`).
- `today` é a tela inicial (`components/today/TodayView.svelte`): três colunas de tiles que empilham de forma independente. As outras seções são uma página com um único `.tile`.

## Design System

**Três temas, um layout** — definidos em `src/routes/layout.css` e trocados pelo menu do avatar (`src/lib/theme.svelte.ts`; salvo no `localStorage` e aplicado antes do primeiro paint por um script em `app.html`):

| Tema | Visual |
|---|---|
| `orbita` (padrão) | escuro, espacial, acento ciano |
| `diario` | escuro, minimalista, acento lavanda |
| `painel` | claro, cada seção com sua cor |

**Nunca use cor fixa em componentes** — use os tokens, para funcionar nos três temas:
- DaisyUI: `--color-base-100` (fundo), `--color-base-200` (tiles), `--color-base-300` (bordas), `--color-base-content`, `--color-primary`, etc.
- Fontes: `--font-display` / `--font-body` / `--font-mono` (classes `.font-display`, `.font-mono-num`)
- Cor por seção: `--c-<seção>`, `--c-<seção>-soft` (fundo), `--c-<seção>-ink` (texto sobre o soft). A classe `.sec-<seção>` (`sec-ops`, `sec-missions`, …) expõe a da seção como `--sec` / `--sec-soft` / `--sec-ink`.
- Forma: `--tile-radius`, `--tile-pad`, `--radius-field`, `--radius-selector`
- Nomes de classe que colidem com componentes do DaisyUI (`stat`, `hero`, `menu`, `card`…) herdam estilos dele — use outro nome.

**Classes utilitárias locais:**
- `.tile` — bloco do layout (use com uma `.sec-*` para ganhar a cor da seção)
- `.glass-card` — card interno de lista (nome legado; não tem mais glassmorphism)
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
