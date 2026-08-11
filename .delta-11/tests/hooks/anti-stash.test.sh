#!/usr/bin/env bash
# Teste do hook anti-stash.py (Etapa 4 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/anti-stash.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "kanban\.md" "$HOOK"; then ok "hook detecta kanban.md"; else err "hook NAO detecta kanban.md"; fi
if grep -qE "CONCLU[IÍ]DO|✅" "$HOOK"; then ok "hook detecta CONCLUIDO"; else err "hook NAO detecta CONCLUIDO"; fi
if grep -qE "git stash list" "$HOOK"; then ok "hook executa git stash list"; else err "hook NAO executa git stash list"; fi
if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then ok "exit 2 (bloqueio)"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python cross-platform"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "anti-stash" "$SETTINGS"; then ok "registrado em settings"; else err "NAO registrado em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Teste funcional: stash vazio = passa
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
git init -q
git config user.email "t@t.t"
git config user.name "T"
echo "x" > a.txt && git add a.txt && git commit -qm "init"
mkdir -p .delta-11
echo "# Kanban" > .delta-11/kanban.md

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
if [ "$EXIT" = "0" ]; then ok "PASSA com stash vazio"; else err "NAO passa com stash vazio (exit=$EXIT)"; fi

# Teste funcional: stash com entrada = BLOQUEIA
echo "y" > a.txt && git stash push -qm "teste stash" a.txt
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA com stash ativo"; else err "NAO bloqueia com stash (exit=$EXIT)"; fi

# Limpa
rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 4 anti-stash.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi