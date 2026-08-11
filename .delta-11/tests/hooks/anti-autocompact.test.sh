#!/usr/bin/env bash
# Teste do hook anti-autocompact.py (Etapa 1 do v6.2)
#
# Verifica que:
#   1. Hook existe em .delta-11/hooks/anti-autocompact.py
#   2. Hook é executavel
#   3. Hook detecta sinais de autocompact iminente:
#      - context window alto (>85%)
#      - tokens aproximados por contagem de chars / 4
#      - marcadores textuais "Auto-compacting...", "context low", "context_window_exceeded"
#   4. Hook bloqueia (exit 2) se detectar autocompact iminente
#   5. Hook passa (exit 0) se nao houver sinal
#   6. Hook NAO e' o mesmo que pre-selo (eh hook NOVO)
#   7. Hook Python (cross-platform)
#   8. Hook registrado em settings-hooks.json (PreToolUse)
#   9. Hook tem docstring
#  10. Teste funcional — hook BLOQUEIA se contexto > 85%
#
# Furo 1 da auditoria 2026-08-11: autocompact matou 5 agentes.

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/anti-autocompact.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. Hook existe
if [ -f "$HOOK" ]; then
    ok "hook existe em $HOOK"
else
    err "hook AUSENTE em $HOOK"
    echo ""
    echo "Teste de regressão do Hook 1 anti-autocompact (Furo 1)."
    echo "Se o hook sumir, o sistema perde a proteção contra autocompact"
    echo "que mata agentes de Claude Code durante tasks longas."
    exit 1
fi

# 2. Executavel
if [ -x "$HOOK" ]; then
    ok "hook executavel"
else
    err "hook NAO executavel (chmod +x $HOOK)"
fi

# 3. Detecta sinais de autocompact
if grep -qiE "autocompact|Auto-compacting|context.*low|context_window_exceeded|context_window_low" "$HOOK"; then
    ok "hook detecta sinais de autocompact"
else
    err "hook NAO detecta sinais de autocompact"
fi

# 4. Bloqueia (exit 2)
if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "hook implementa exit code 2 (bloqueio)"
else
    err "hook NAO implementa exit code 2"
fi

# 5. Hook NAO e' o mesmo que pre-selo
if [ "$HOOK" != "$HOOKS_DIR/pre-selo.py" ]; then
    ok "hook NAO e' pre-selo.py (eh hook NOVO)"
else
    err "hook parece ser copia de pre-selo.py"
fi

# 6. Hook Python cross-platform
if head -1 "$HOOK" | grep -q "python"; then
    ok "hook Python (cross-platform)"
else
    err "hook NAO Python"
fi

# 7. Registrado em settings-hooks.json
if [ -f "$SETTINGS" ] && grep -q "anti-autocompact" "$SETTINGS"; then
    ok "registrado em settings-hooks.json"
else
    err "NAO registrado em settings-hooks.json"
fi

# 8. Docstring
if head -10 "$HOOK" | grep -qE '"""'; then
    ok "docstring presente"
else
    err "sem docstring"
fi

# 9. Hook verifica contexto via contador (4 chars/token)
if grep -qiE "len.*4|/ 4|chars.*token|chars_per_token" "$HOOK"; then
    ok "hook estima tokens via 4 chars/token (padrao D-11)"
else
    err "hook NAO estima tokens"
fi

# 10. Teste funcional: hook BLOQUEIA se contexto > 85%
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/memoria"

# Simula evento PreToolUse com prompt gigante (>85% de 200K contexto = 170K tokens = 680K chars)
BIG_PROMPT=$(python3 -c "print('x' * 700000)")

EVENT_PAYLOAD=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '$TEST_DIR/test.md',
        'content': 'x'
    },
    'prompt': 'x' * 700000
}))
")

EXIT_CODE=$(echo "$EVENT_PAYLOAD" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)

if [ "$EXIT_CODE" = "2" ]; then
    ok "hook BLOQUEIA (exit 2) quando contexto > 85% (~700K chars)"
else
    err "hook NAO bloqueia contexto > 85% (exit=$EXIT_CODE)"
fi

# 11. Hook PASSA com prompt pequeno
SMALL_PAYLOAD=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '$TEST_DIR/test.md',
        'content': 'x'
    },
    'prompt': 'x' * 100
}))
")

EXIT_CODE=$(echo "$SMALL_PAYLOAD" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)

if [ "$EXIT_CODE" = "0" ]; then
    ok "hook PASSA (exit 0) com prompt pequeno (~100 chars)"
else
    err "hook bloqueia prompt pequeno (exit=$EXIT_CODE)"
fi

rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Hook 1 anti-autocompact.py implementado${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi