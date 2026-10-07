#!/usr/bin/env bash
# Sobe o Station One na sua máquina: API (127.0.0.1:8100) + app (127.0.0.1:4100).
# O Tailscale publica o app para os seus aparelhos — e só para eles:
#
#   http://<nome-do-mac>:4100            endereço curto (como o Lumiverse)
#   https://<nome-do-mac>.<rede>.ts.net  com HTTPS (clima e app instalável no iPhone)
#
# Ctrl+C desliga. Requer o "Serve" habilitado na sua rede Tailscale (uma vez).
#
#   ./start.sh            # sobe (recompila o frontend se o código mudou)
#   ./start.sh --rebuild  # força recompilar
#
# Para desenvolver com hot reload, use `make dev` (portas 5173/8000).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API_PORT="${API_PORT:-8100}"
WEB_PORT="${WEB_PORT:-4100}"
cd "$ROOT"

REBUILD=0
for arg in "$@"; do
	case "$arg" in
		--rebuild) REBUILD=1 ;;
		*) echo "opção desconhecida: $arg" >&2; exit 2 ;;
	esac
done

say() { printf '\033[36m→\033[0m %s\n' "$*"; }

# ── Endereço no Tailscale ────────────────────────────────────────────────────
TS_HOST="" TS_NAME=""
if command -v tailscale >/dev/null; then
	TS_HOST="$(tailscale status --json 2>/dev/null |
		python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null || true)"
	TS_NAME="${TS_HOST%%.*}"
fi
# Só localhost: quem expõe é o Tailscale (no macOS ele não consegue repassar para o
# próprio IP 100.x, mas repassa para 127.0.0.1). Assim a rede Wi-Fi nunca enxerga o app.
WEB_HOST=127.0.0.1

# ── Dependências e build (só quando necessário) ──────────────────────────────
if [ ! -x api/.venv/bin/uvicorn ]; then
	say "Instalando dependências da API…"
	(cd api && poetry install --no-interaction --no-root -q)
fi
if [ ! -d frontend/node_modules ]; then
	say "Instalando dependências do frontend…"
	(cd frontend && pnpm install --frozen-lockfile --silent)
fi
stale="$(find frontend/src frontend/static frontend/package.json frontend/svelte.config.js frontend/vite.config.ts \
	-newer frontend/build/index.js 2>/dev/null | head -1 || true)"
if [ "$REBUILD" = 1 ] || [ ! -f frontend/build/index.js ] || [ -n "$stale" ]; then
	say "Compilando o frontend…"
	(cd frontend && pnpm build >/dev/null)
fi

# ── Sobe os dois processos; Ctrl+C derruba ambos ─────────────────────────────
pids=()
cleanup() {
	trap - INT TERM EXIT
	echo
	say "Desligando…"
	# ${pids[@]+...}: o bash 3.2 do macOS reclama de array vazio com `set -u`
	kill ${pids[@]+"${pids[@]}"} 2>/dev/null || true
	wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

(cd api && exec .venv/bin/uvicorn main:app --host 127.0.0.1 --port "$API_PORT" --log-level warning) &
pids+=($!)
# Sem ORIGIN fixo: o app é acessado por mais de um endereço (HTTP e HTTPS)
(cd frontend && HOST="$WEB_HOST" PORT="$WEB_PORT" \
	API_INTERNAL_URL="http://127.0.0.1:$API_PORT" exec node build) &
pids+=($!)

for _ in $(seq 1 60); do
	# -f: um 502 (API ainda subindo) conta como falha e continua esperando
	curl -sf -o /dev/null "http://$WEB_HOST:$WEB_PORT/api/health" && break
	sleep 0.5
done

# ── Publica no Tailscale (só dispositivos da sua rede enxergam) ──────────────
# A configuração do `serve` é persistente: só é criada na primeira vez.
ts_serve() {
	# Se o Serve não estiver habilitado na rede, o Tailscale espera para sempre
	# um clique no painel — então limitamos a 15 s e mostramos a mensagem dele.
	local log pid
	log="$(mktemp)"
	tailscale serve --bg "$@" >"$log" 2>&1 &
	pid=$!
	for _ in $(seq 1 15); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
	if kill -0 "$pid" 2>/dev/null || ! wait "$pid"; then
		kill "$pid" 2>/dev/null || true
		say "Não consegui publicar no Tailscale. Mensagem dele:"
		sed 's/^/    /' "$log"
		rm -f "$log"
		return 1
	fi
	rm -f "$log"
}

if [ -n "$TS_HOST" ]; then
	target="http://127.0.0.1:$WEB_PORT"
	status="$(tailscale serve status 2>/dev/null || true)"
	ok=1
	if ! printf '%s' "$status" | grep -q "https://$TS_HOST (tailnet only)" ||
		! printf '%s' "$status" | grep -A2 "https://$TS_HOST (tailnet only)" | grep -q "$target"; then
		ts_serve --https=443 "$target" || ok=0
	fi
	if [ "$ok" = 1 ] && ! printf '%s' "$status" | grep -q ":$WEB_PORT (tailnet only)"; then
		ts_serve --http="$WEB_PORT" "$target" || ok=0
	fi
	if [ "$ok" = 1 ]; then
		say "No iPhone: https://$TS_HOST"
		say "      ou: http://$TS_NAME:$WEB_PORT"
	fi
else
	say "Tailscale não encontrado — só neste Mac: http://127.0.0.1:$WEB_PORT"
fi
say "Ctrl+C para desligar"
# Fica no ar enquanto os dois estiverem vivos (sem `wait -n`: o bash do macOS é 3.2)
while kill -0 "${pids[0]}" 2>/dev/null && kill -0 "${pids[1]}" 2>/dev/null; do
	sleep 1
done
say "Um dos processos parou — veja o erro acima."
exit 1
