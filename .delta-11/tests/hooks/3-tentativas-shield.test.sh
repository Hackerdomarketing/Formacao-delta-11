#!/usr/bin/env bash
# Teste do hook 3-tentativas-shield.py (Hook 11 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/3-tentativas-shield.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "shield-falhas\.log" "$HOOK"; then ok "hook le shield-falhas.log"; else err "sem log"; fi
if grep -qE "SessionStart|session.?start" "$HOOK"; then ok "hook documenta SessionStart"; else err "sem SessionStart"; fi
if grep -qE "3|LIMITE_FALHAS" "$HOOK"; then ok "hook tem limite de 3 falhas"; else err "sem limite"; fi
if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then ok "exit 2"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "3-tentativas-shield" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Testes funcionais
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
mkdir -p .delta-11/logs/sub-agentes

# Cenario A: sem falhas = PASSA
EXIT=$(python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA sem falhas"; else err "NAO passa sem falhas (exit=$EXIT)"; fi

# Cenario B: 2 falhas BACK = PASSA
HOJE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > .delta-11/logs/sub-agentes/shield-falhas.log <<EOF
- [$HOJE] [BACK] FAIL tentativa 1
- [$HOJE] [BACK] FAIL tentativa 2
EOF
EXIT=$(python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA com 2 falhas (< 3)"; else err "NAO passa com 2 (exit=$EXIT)"; fi

# Cenario C: 3 falhas BACK = BLOQUEIA
echo "- [$HOJE] [BACK] FAIL tentativa 3" >> .delta-11/logs/sub-agentes/shield-falhas.log
EXIT=$(python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA com 3 falhas BACK"; else err "NAO bloqueia com 3 (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 11 3-tentativas-shield.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi