#!/usr/bin/env bash
# Teste do hook worktree-prune.py (Hook 10 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/worktree-prune.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "git worktree prune" "$HOOK"; then ok "hook executa git worktree prune"; else err "sem git worktree prune"; fi
if grep -qE "SessionStart|session.?start" "$HOOK"; then ok "hook documenta SessionStart"; else err "sem SessionStart"; fi
if grep -qE "sys\.exit\(0\)|sys\.exit\(main" "$HOOK"; then ok "exit 0 ou main()"; else err "sem exit 0"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "worktree-prune" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "list.*worktree|list_worktrees" "$HOOK"; then ok "hook lista worktrees antes/depois"; else err "sem listagem"; fi

# Teste funcional
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
git init -q
git config user.email "t@t.t"
git config user.name "T"
echo "x" > a.txt && git add a.txt && git commit -qm "init"

# Cenario: nao ha worktrees orfas, hook deve exit 0
EXIT=$(python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA (exit 0) sem worktrees orfas"; else err "NAO passa sem worktrees (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 10 worktree-prune.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi