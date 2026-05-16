# Station One API

Backend unificado para o Station One — operações, missões, wishlist e Financial Core.

**Stack:** FastAPI · SQLAlchemy (async) · Supabase (PostgreSQL + Auth)

## Requisitos

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)
- Projeto criado no [Supabase](https://supabase.com)

## Setup

```bash
# 1. Clone e entre na pasta
cd station-one-api

# 2. Instale as dependências com Poetry
poetry install

# 3. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com seus dados do Supabase

# 4. Rode o schema no Supabase
# Abra supabase.com → seu projeto → SQL Editor
# Cole e execute o conteúdo de migrations/init.sql

# 5. Inicie o servidor
poetry run uvicorn main:app --reload --port 8000
```

## Documentação

Com o servidor rodando, acesse: http://localhost:8000/docs

## Estrutura

```
routers/
├── items.py         — GET/POST/PATCH/DELETE /items
├── goals.py         — GET/POST/DELETE /goals + /milestones
├── wishlist.py      — GET/POST/DELETE /wishlist
└── finance/
    ├── wallets.py   — GET/POST /finance/wallets + sugestor
    ├── transactions.py  — GET/POST /finance/transactions + overview
    ├── debts.py     — GET/POST/PATCH /finance/debts + projeção
    ├── simulator.py — POST /finance/simulator
    └── health_logs.py — GET/POST /finance/health-logs + ROI
```

## Auth

Todas as rotas requerem o header:
```
Authorization: Bearer <supabase_jwt>
```

O JWT é obtido pelo frontend (SvelteKit) após login via `@supabase/supabase-js`.
