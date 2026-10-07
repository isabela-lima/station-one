#!/usr/bin/env bash
# Para e remove os serviços do Station One (não mexe no código nem nos dados).
set -euo pipefail
DOMAIN="gui/$(id -u)"
for svc in api web; do
	label="com.station-one.$svc"
	launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
	rm -f "$HOME/Library/LaunchAgents/$label.plist"
	echo "→ $label removido"
done
