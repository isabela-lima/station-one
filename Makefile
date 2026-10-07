.PHONY: dev api frontend install deploy service-stop service-restart service-status logs tailscale-on tailscale-off

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
	cd api && poetry env use /opt/homebrew/bin/python3.13 && poetry install

# ─── Rodar no Mac (serviço) + acesso pelo Tailscale ──────────────────────────
# Jeito simples: ./start.sh (no terminal, Ctrl+C desliga). Os alvos abaixo
# instalam como serviço que liga sozinho no login — opcional.
# Portas 4100 (app) e 8100 (API), ambas só em 127.0.0.1;
# convivem com `make dev` (5173/8000).

deploy: ## Compila e (re)instala os serviços — rode de novo após cada atualização
	./deploy/install.sh

service-stop: ## Para e remove os serviços
	./deploy/uninstall.sh

service-restart: ## Reinicia os serviços sem recompilar
	launchctl kickstart -k gui/$$(id -u)/com.station-one.api
	launchctl kickstart -k gui/$$(id -u)/com.station-one.web

service-status: ## Mostra se os serviços estão de pé
	@launchctl list | grep station-one || echo "serviços não instalados"
	@curl -s -o /dev/null -w "app: HTTP %{http_code}\n" http://127.0.0.1:4100/login || true
	@curl -s -o /dev/null -w "api: HTTP %{http_code}\n" http://127.0.0.1:4100/api/health || true

logs: ## Acompanha os logs dos serviços
	tail -f ~/Library/Logs/station-one/api.log ~/Library/Logs/station-one/web.log

tailscale-on: ## Publica o app na sua rede Tailscale (https://<mac>.<rede>.ts.net e http://<mac>:4100)
	tailscale serve --bg --https=443 http://127.0.0.1:4100
	tailscale serve --bg --http=4100 http://127.0.0.1:4100

tailscale-off: ## Tira o app do Tailscale
	tailscale serve --https=443 off
	tailscale serve --http=4100 off
