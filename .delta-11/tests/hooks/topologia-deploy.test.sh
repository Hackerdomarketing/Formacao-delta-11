#!/usr/bin/env bash
# Teste do hook topologia-deploy.py (Hook 9 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/topologia-deploy.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "deploy|wrangler|subir.*producao" "$HOOK"; then ok "hook detecta keywords deploy"; else err "sem keywords"; fi
if grep -qE "topologia\.json" "$HOOK"; then ok "hook verifica topologia.json"; else err "sem topologia.json"; fi
if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then ok "exit 2"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "topologia-deploy" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Testes funcionais
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
mkdir -p .delta-11/memoria

# Cenario A: sem topologia.json = BLOQUEIA
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'wrangler deploy'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA sem topologia.json"; else err "NAO bloqueia sem topologia (exit=$EXIT)"; fi

# Cenario B: com topologia.json completa = PASSA
echo '{"worker_url": "https://api.x.com", "pages_url": "https://admin.x.com"}' > .delta-11/memoria/topologia.json
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA com topologia valida"; else err "NAO passa com topologia (exit=$EXIT)"; fi

# Cenario C: sem keyword deploy = PASSA sempre
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'apenas atualizando documentacao'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA sem keyword deploy"; else err "NAO passa sem keyword (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 9 topologia-deploy.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi