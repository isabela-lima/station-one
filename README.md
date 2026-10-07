# 🛸 Station One

Centro de atenção pessoal — dashboard web com estética *Herta Space Station*. Substitui o caos de apps separados (todoist, notion, planilha de finanças) com uma interface única, coesa e com identidade visual própria.

**Conceito visual:** escuro profundo `#0a0a12`, acentos ciano `#06b6d4` e roxo `#8b5cf6`, glassmorphism.

---

## Estrutura do monorepo

```
station-one/
├── frontend/   SvelteKit 2 + Svelte 5 + Tailwind + DaisyUI
├── api/        FastAPI + SQLAlchemy + Supabase
└── Makefile    atalhos para rodar tudo
```

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | SvelteKit 2 + Svelte 5 (runes) |
| Styling | Tailwind CSS v4 + DaisyUI 5 |
| Ícones | Lucide Svelte |
| Auth + Realtime | Supabase |
| Backend | FastAPI (Python 3.11+) |
| PWA | vite-plugin-pwa |

---

## Pré-requisitos

- Node.js ≥ 20 + pnpm
- Python ≥ 3.11 + Poetry
- Conta no [Supabase](https://supabase.com) com o schema aplicado

---

## Setup

### 1. Banco de dados (uma vez só)

No painel do Supabase, vá em **SQL Editor** e execute, nesta ordem:

```
api/migrations/init.sql
api/migrations/phase3.sql
api/supabase/migrations/20261004000000_enable_realtime.sql
api/supabase/migrations/20261004010000_tasks_missions_journal.sql
api/supabase/migrations/20261007000000_cleanup_legacy_data.sql
api/supabase/migrations/20261007010000_task_due_date_as_date.sql
```

As migrações em `api/supabase/migrations/` são idempotentes (podem rodar de novo sem efeito).

Em **Authentication → URL Configuration → Redirect URLs**, adicione `http://localhost:5173/login?reset=1` (e o equivalente em produção) para o fluxo de "esqueci minha senha".

### 2. Variáveis de ambiente

```bash
cp frontend/.env.example frontend/.env
cp api/.env.example api/.env
```

Preencha os valores — tudo fica em **Supabase → Settings → API** e **Settings → Database**.

### 3. Instalar dependências

```bash
make install
```

---

## Como rodar

```bash
make dev        # frontend + API juntos
make frontend   # só o frontend (http://localhost:5173)
make api        # só a API (http://localhost:8000)
```

Docs da API disponíveis em `http://localhost:8000/docs` (apenas em `ENVIRONMENT=development`).

---

## Seções do Dashboard

| Seção | O que faz |
|-------|-----------|
| **Hoje** | Tela inicial: tarefas pendentes, protocolos, finanças, diário e progresso das missões. |
| **Operações** | Tarefas, cada uma opcionalmente ligada a uma missão. Foco (⭐) e limpeza das concluídas. |
| **Missões** | Projetos que agrupam tarefas, com barra de progresso. |
| **Diário** | Entradas com hora, humor/energia do dia e resumo automático (tarefas, protocolos, gastos), com histórico. |
| **Protocolos** | Hábitos diários com streak 🔥 |
| **Wishlist** | Lista de desejos com preço atual vs. meta. |
| **Finanças** | Carteiras, transações, orçamentos e dívidas. |

---

## Arquitetura

```
Browser
  │
  ├── Supabase Auth (JWT)
  ├── Supabase Realtime ──► tarefas, missões, wishlist, hábitos, diário
  └── FastAPI ──► lógica de negócio
        └── PostgreSQL (Supabase)
```

O frontend obtém um JWT do Supabase no login e o envia em cada requisição para o FastAPI via `Authorization: Bearer <token>`.
