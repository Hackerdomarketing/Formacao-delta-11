#!/usr/bin/env bash
# Teste do hook shield-aprovado.py (Etapa 5 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/shield-aprovado.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "kanban\.md" "$HOOK"; then ok "hook detecta kanban.md"; else err "hook NAO detecta kanban.md"; fi
if grep -qE "BACK.*ENGINE.*VAULT|AGENTES_QUE_EXIGEM_SHIELD" "$HOOK"; then ok "hook tem lista BACK/ENGINE/VAULT"; else err "sem lista"; fi
if grep -qE "activity.log\.md" "$HOOK"; then ok "hook verifica activity-log.md"; else err "sem activity-log"; fi
if grep -qE "sys\.exit|return 2" "$HOOK"; then ok "exit 2 (sys.exit ou return 2)"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "shield-aprovado" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Testes funcionais
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
mkdir -p .delta-11
echo "# Kanban" > .delta-11/kanban.md

# Cenario: BACK sem SHIELD log = BLOQUEIA
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '.delta-11/kanban.md',
        'old_string': '# Kanban',
        'new_string': '# Kanban\n## CONCLUIDO\n- [x] T-1 [BACK] ok'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA BACK sem SHIELD"; else err "NAO bloqueia BACK (exit=$EXIT)"; fi

# Cenario: BACK COM SHIELD log recente = PASSA
echo "- [2026-08-11T04:00:00Z] [SHIELD] [BACK] aprovado" >> .delta-11/activity-log.md
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA BACK com SHIELD log"; else err "NAO passa BACK com SHIELD (exit=$EXIT)"; fi

# Cenario: FRONT (isento) sem SHIELD = PASSA
rm .delta-11/activity-log.md
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '.delta-11/kanban.md',
        'old_string': '# Kanban',
        'new_string': '# Kanban\n## CONCLUIDO\n- [x] T-1 [FRONT] ok'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA FRONT (isento) sem SHIELD"; else err "NAO passa FRONT (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 5 shield-aprovado.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi