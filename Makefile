.PHONY: dev api frontend install

dev: ## Sobe frontend + API em paralelo
	@npx concurrently --names "API,WEB" --prefix-colors "cyan,magenta" \
		"cd api && .venv/bin/uvicorn main:app --reload" \
		"cd frontend && pnpm dev"

api: ## Sobe só a API
	cd api && .venv/bin/uvicorn main:app --reload

frontend: ## Sobe só o frontend
	cd frontend && pnpm dev

install: ## Instala dependências dos dois projetos
	cd frontend && pnpm install && node_modules/.bin/svelte-kit sync
	cd api && /opt/homebrew/bin/python3.13 -m venv .venv && \
		.venv/bin/pip install -q \
		fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg greenlet \
		"pydantic>=2.5.0" pydantic-settings "python-jose[cryptography]" \
		python-multipart httpx supabase
