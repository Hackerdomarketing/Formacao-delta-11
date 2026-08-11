#!/usr/bin/env bash
# Teste do hook contratos-minimos.py (Etapa 7 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/contratos-minimos.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "kanban\.md" "$HOOK"; then ok "hook detecta kanban.md"; else err "sem kanban"; fi
if grep -qE "NOVO.CICLO|CICLO.\d+|\[1-9]..\s*CICLO" "$HOOK"; then ok "hook detecta novo ciclo"; else err "sem novo ciclo"; fi
if grep -qE "project-core\.md" "$HOOK"; then ok "hook verifica project-core.md"; else err "sem project-core"; fi
if grep -qE "sys\.exit|return 2" "$HOOK"; then ok "exit 2 (sys.exit ou return 2)"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "contratos-minimos" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Testes funcionais
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
mkdir -p .delta-11/memoria
echo "# Kanban" > .delta-11/kanban.md
echo "# Project Core" > .delta-11/memoria/project-core.md

# Cenario A: kanban SEM novo ciclo = passa
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
if [ "$EXIT" = "0" ]; then ok "PASSA sem novo ciclo"; else err "NAO passa sem novo ciclo (exit=$EXIT)"; fi

# Cenario B: novo ciclo + project-core.md recente = passa
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '.delta-11/kanban.md',
        'old_string': '# Kanban',
        'new_string': '# Kanban\n## FAZENDO\n- [ ] T-2 [CICLO 5] novo'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA novo ciclo com project-core.md recente"; else err "NAO passa project-core recente (exit=$EXIT)"; fi

# Cenario C: novo ciclo + project-core.md antigo = BLOQUEIA
# Define mtime para 5h atras
python3 -c "
import os, time
path = '.delta-11/memoria/project-core.md'
os.utime(path, (time.time() - 5*3600, time.time() - 5*3600))
"
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA novo ciclo com project-core.md antigo (5h)"; else err "NAO bloqueia project-core antigo (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 7 contratos-minimos.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi