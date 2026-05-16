.PHONY: dev api frontend install

dev: ## Sobe frontend + API em paralelo
	@npx concurrently --names "API,WEB" --prefix-colors "cyan,magenta" \
		"cd api && poetry run uvicorn main:app --reload" \
		"cd frontend && pnpm dev"

api: ## Sobe só a API
	cd api && poetry run uvicorn main:app --reload

frontend: ## Sobe só o frontend
	cd frontend && pnpm dev

install: ## Instala dependências dos dois projetos
	cd frontend && pnpm install && node_modules/.bin/svelte-kit sync
	cd api && poetry install
