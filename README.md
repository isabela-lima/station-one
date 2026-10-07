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
api/supabase/migrations/20261007020000_assistant_settings_usage.sql
```

As migrações em `api/supabase/migrations/` são idempotentes (podem rodar de novo sem efeito).

Em **Authentication → URL Configuration → Redirect URLs**, adicione `http://localhost:5173/login?reset=1` e `https://<nome-do-mac>.<rede>.ts.net/login?reset=1` para o fluxo de "esqueci minha senha".

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

### No dia a dia (no seu Mac, acessando pelo iPhone)

```bash
./start.sh            # Ctrl+C desliga
./start.sh --rebuild  # força recompilar o frontend
```

Sobe a API e o app (compila o frontend se o código mudou) e publica na sua rede [Tailscale](https://tailscale.com):

- `https://<nome-do-mac>.<rede>.ts.net` — com HTTPS: necessário para o clima e para instalar como app
- `http://<nome-do-mac>:4100` — endereço curto, sem HTTPS

Os dois processos escutam só em `127.0.0.1`; quem expõe o app é o `tailscale serve`, então ele aparece **só** para os seus aparelhos no Tailscale, nunca na rede Wi-Fi. Pré-requisitos (uma vez): Tailscale rodando com MagicDNS, e o *Serve* habilitado na rede — na primeira execução, se não estiver, o script mostra o link para habilitar.

No iPhone: abra o endereço HTTPS no Safari → **Compartilhar → Adicionar à Tela de Início**.

Opcional — rodar como serviço que liga sozinho no login (`launchd`):

```bash
make deploy          # compila e instala/atualiza (rode de novo após cada atualização)
make tailscale-on    # publica no Tailscale
make service-status  # está de pé?
make logs            # acompanha os logs
make service-stop    # remove o serviço
```

### Desenvolvendo (hot reload)

```bash
make dev        # frontend + API juntos
make frontend   # só o frontend (http://localhost:5173)
make api        # só a API (http://localhost:8000)
```

O navegador sempre chama `/api/...` no mesmo endereço do app; o servidor do frontend (`src/hooks.server.ts`) repassa para o FastAPI. Docs da API em `http://localhost:8000/docs` (apenas em `ENVIRONMENT=development`).

As portas de dev (5173/8000) e as do `./start.sh` (4100/8100) são diferentes, então dá para rodar os dois ao mesmo tempo.

---

## Seções do Dashboard

| Seção | O que faz |
|-------|-----------|
| **Hoje** | Tela inicial: tarefas pendentes, protocolos, finanças, diário e progresso das missões. |
| **Operações** | Tarefas, cada uma opcionalmente ligada a uma missão. Foco (⭐) e limpeza das concluídas. |
| **Missões** | Projetos que agrupam tarefas, com barra de progresso. |
| **Diário** | Entradas com hora, humor/energia do dia e resumo automático (tarefas, protocolos, gastos), com histórico. |
| **Assistente** (✨ ou ⌘K) | Escreva em português (“pagar a fatura sexta, gastei 45 no mercado”) e ele propõe tarefas, gastos, entradas no diário e check-in; nada é gravado antes de você confirmar. Usa a **sua** chave da Anthropic, configurada em Configurações. |
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
