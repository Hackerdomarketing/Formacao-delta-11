#!/usr/bin/env bash
# Teste do hook urls-validas.py (Etapa 6 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/urls-validas.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "https?://" "$HOOK"; then ok "hook detecta URLs (regex)"; else err "sem regex URL"; fi
if grep -qE "TLD|tld" "$HOOK"; then ok "hook valida TLD"; else err "sem TLD check"; fi
if grep -qE "sys\.exit|return 2" "$HOOK"; then ok "exit 2 (sys.exit ou return 2)"; else err "sem exit 2"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "urls-validas" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)" "$HOOK"; then ok "exit 0"; else err "sem exit 0"; fi

# Testes funcionais
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
touch test.md

# Cenario A: conteudo sem URL = passa
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'sem urls aqui'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA sem URL"; else err "NAO passa sem URL (exit=$EXIT)"; fi

# Cenario B: URL valida = passa
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'Acesse https://example.com/path'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA URL valida"; else err "NAO passa URL valida (exit=$EXIT)"; fi

# Cenario C: URL sem TLD = BLOQUEIA
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'Acesse https://localhost'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA URL sem TLD"; else err "NAO bloqueia URL sem TLD (exit=$EXIT)"; fi

# Cenario D: URL com espaco = BLOQUEIA
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': 'test.md',
        'content': 'Acesse https://foo bar.com'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then ok "BLOQUEIA URL com espaco"; else err "NAO bloqueia URL com espaco (exit=$EXIT)"; fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 6 urls-validas.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi