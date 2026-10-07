#!/usr/bin/env bash
# Instala/atualiza o Station One como serviço do macOS (launchd):
# compila o frontend, instala as dependências da API e (re)inicia os dois
# processos. Os dois escutam só em 127.0.0.1; quem publica o app para os
# seus aparelhos é o Tailscale (`make tailscale-on`). Mesmo esquema do ./start.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_PORT="${API_PORT:-8100}"
WEB_PORT="${WEB_PORT:-4100}"
LOG_DIR="$HOME/Library/Logs/station-one"
AGENTS="$HOME/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"

NODE="$(command -v node || true)"
[ -n "$NODE" ] || { echo "node não encontrado no PATH" >&2; exit 1; }

TS_HOST="$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null || true)"

echo "→ API: dependências"
(cd "$ROOT/api" && poetry install --no-interaction --no-root --only main -q)

echo "→ Frontend: build"
(cd "$ROOT/frontend" && pnpm install --frozen-lockfile --silent && pnpm build >/dev/null)

mkdir -p "$LOG_DIR" "$AGENTS"
for svc in api web; do
	label="com.station-one.$svc"
	sed -e "s#__ROOT__#$ROOT#g" -e "s#__NODE__#$NODE#g" -e "s#__LOG_DIR__#$LOG_DIR#g" \
		-e "s#__API_PORT__#$API_PORT#g" -e "s#__WEB_PORT__#$WEB_PORT#g" \
		"$ROOT/deploy/launchd/$label.plist" > "$AGENTS/$label.plist"
	launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
	launchctl bootstrap "$DOMAIN" "$AGENTS/$label.plist"
	echo "→ $label iniciado"
done

echo
echo "Station One rodando em http://127.0.0.1:$WEB_PORT (logs em $LOG_DIR)"
[ -n "$TS_HOST" ] && echo "Nos seus aparelhos (depois de 'make tailscale-on'): https://$TS_HOST"
