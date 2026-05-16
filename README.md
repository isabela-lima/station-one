# 🛸 Station One

Centro de atenção pessoal — dashboard web com estética *Herta Space Station*. Substitui o caos de apps separados (todoist, notion, planilha de finanças) com uma interface única, coesa e com identidade visual própria.

**Conceito visual:** escuro profundo `#0a0a12`, acentos ciano `#06b6d4` e roxo `#8b5cf6`, glassmorphism.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | SvelteKit 2 + Svelte 5 (runes) |
| Styling | Tailwind CSS v4 + DaisyUI 5 |
| Ícones | Lucide Svelte |
| Auth + Realtime | Supabase |
| Backend | FastAPI (Python) — [`station-one-api`](../station-one-api/) |
| PWA | vite-plugin-pwa |

---

## Pré-requisitos

- Node.js ≥ 20 + pnpm
- Python ≥ 3.11 + Poetry
- Conta no [Supabase](https://supabase.com) com o schema aplicado

---

## Como rodar

### 1. Banco de dados (Supabase)

No painel do Supabase, vá em **SQL Editor** e execute o arquivo:

```
station-one-api/migrations/init.sql
```

Isso cria todas as tabelas com isolamento por `user_id` e RLS configurado.

---

### 2. Backend (FastAPI)

```bash
cd station-one-api

# Instalar dependências
poetry install

# Configurar variáveis de ambiente
cp .env.example .env
# Preencher .env com os valores do Supabase (ver seção Variáveis abaixo)

# Rodar o servidor
poetry run uvicorn main:app --reload
# API disponível em http://localhost:8000
# Docs em http://localhost:8000/docs (apenas em development)
```

**Variáveis do `.env` da API:**

```env
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_SECRET_KEY=<service_role key>
SUPABASE_JWT_SECRET=<JWT secret>
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<db>
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

> Todos os valores ficam em **Supabase → Settings → API** e **Settings → Database**.

---

### 3. Frontend (SvelteKit)

```bash
cd station-one

# Instalar dependências
pnpm install

# Configurar variáveis de ambiente
cp .env.example .env
# Preencher .env

# Rodar em desenvolvimento
pnpm dev
# App disponível em http://localhost:5173
```

**Variáveis do `.env` do frontend:**

```env
PUBLIC_SUPABASE_URL=https://<seu-projeto>.supabase.co
PUBLIC_SUPABASE_ANON_KEY=<anon/public key>
PUBLIC_API_URL=http://localhost:8000
```

> `PUBLIC_SUPABASE_ANON_KEY` fica em **Supabase → Settings → API → Project API keys → anon public**.

---

## Seções do Dashboard

| Seção | O que faz |
|-------|-----------|
| **Operações** | Tarefas, notas e links do dia. Suporte a foco (⚡) e bulk delete de concluídas. |
| **Missões** | Metas de longo prazo com marcos e barra de progresso. |
| **Protocolos** | Hábitos diários com contagem de streak 🔥 |
| **Wishlist** | Lista de desejos com preço atual vs. meta. |
| **Finanças** | Carteiras, transações, orçamentos e dívidas. |

---

## Arquitetura

```
Browser
  │
  ├── Supabase Auth (JWT)
  ├── Supabase Realtime (postgres_changes) ──► itens, metas, marcos, wishlist, hábitos
  └── FastAPI (REST) ──► toda lógica de negócio
        └── PostgreSQL (Supabase)
```

O frontend obtém um JWT do Supabase no login e o envia em cada requisição para o FastAPI via `Authorization: Bearer <token>`. O FastAPI valida o JWT e usa o `user_id` para isolar os dados.

---

## Scripts úteis

```bash
# Frontend
pnpm dev          # desenvolvimento
pnpm build        # build de produção
pnpm check        # type check (svelte-check)
pnpm format       # formatar com prettier

# Backend
poetry run uvicorn main:app --reload   # desenvolvimento
poetry run pytest                      # testes
```

---

## Estrutura de pastas

```
src/
├── routes/
│   ├── +layout.svelte        # auth guard
│   ├── +page.svelte          # dashboard principal
│   └── login/                # página de login/cadastro
└── lib/
    ├── api.ts                # cliente FastAPI
    ├── supabase.ts           # cliente Supabase + getAuthToken()
    ├── toast.ts              # sistema de notificações
    ├── models/types.ts       # tipos TypeScript
    └── components/
        ├── ItemCard.svelte
        ├── GoalCard.svelte
        ├── HabitCard.svelte
        ├── WishlistCard.svelte
        ├── DailyLog.svelte
        ├── dashboard/        # layout (sidebar, nav mobile, form)
        └── finance/          # dashboard financeiro
```
