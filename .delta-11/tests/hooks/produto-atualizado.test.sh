#!/usr/bin/env bash
# Teste do hook produto-atualizado.py (Etapa 3 do v6.2)
#
# Furo 3 da auditoria 2026-08-11: FRONT/PIXEL/VAULT/ATLAS-produto.md
# desatualizados. pre-selo.py so' conta tokens. Hook NAO existia.
#
# Verifica:
#   1-12. Checks de existencia/execucao/Python/settings/docstring/exit
#  13. Teste funcional - BACK sem produto.md BLOQUEIA
#  14. Teste funcional - BACK com produto.md antigo BLOQUEIA
#  15. Teste funcional - BACK com produto.md recente PASSA
#  16. Teste funcional - agente NAO-executor (ATLAS) PASSA sem produto.md

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/produto-atualizado.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1-2. Hook existe e executavel
if [ -f "$HOOK" ]; then
    ok "hook existe em $HOOK"
else
    err "hook AUSENTE em $HOOK"
    echo "Teste de regressão do Hook 3 produto-atualizado (Furo 3)."
    echo "Se hook sumir, sistema perde proteção contra agente marcar"
    echo "CONCLUIDO sem ter atualizado [AGENTE]-produto.md."
    exit 1
fi

if [ -x "$HOOK" ]; then
    ok "hook executavel"
else
    err "hook NAO executavel"
fi

# 3-4. Detecta kanban + conclusao
if grep -qE "kanban\.md|\.delta-11/kanban" "$HOOK"; then
    ok "hook detecta edicao em kanban.md"
else
    err "hook NAO detecta kanban.md"
fi

if grep -qE "CONCLU[IÍ]DO|✅|CONCLUIDA" "$HOOK"; then
    ok "hook detecta transicao CONCLUIDO"
else
    err "hook NAO detecta CONCLUIDO"
fi

# 5-6. Verifica mtime + JANELA
if grep -qE "mtime|stat\(\.st_mtime\)|produto_mtime" "$HOOK"; then
    ok "hook verifica mtime do [AGENTE]-produto.md"
else
    err "hook NAO verifica mtime"
fi

if grep -qE "4 \* 60 \* 60|JANELA_SEGUNDOS.*4 \* 60 \* 60" "$HOOK"; then
    ok "janela de 4 horas configurada"
else
    err "janela NAO configurada como 4h"
fi

# 7-8. Identifica agente + exit code
if grep -qE "AGENTES_EXECUTORES|extract_agente" "$HOOK"; then
    ok "hook identifica agente"
else
    err "hook NAO identifica agente"
fi

if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "hook implementa exit 2"
else
    err "hook NAO implementa exit 2"
fi

# 9-10. Python + settings
if head -1 "$HOOK" | grep -q "python"; then
    ok "hook Python (cross-platform)"
else
    err "hook NAO Python"
fi

if [ -f "$SETTINGS" ] && grep -q "produto-atualizado" "$SETTINGS"; then
    ok "registrado em settings-hooks.json"
else
    err "NAO registrado em settings-hooks.json"
fi

# 11-12. Docstring + exit 0
if head -10 "$HOOK" | grep -qE '"""'; then
    ok "docstring presente"
else
    err "sem docstring"
fi

if grep -qE "sys\.exit\(0\)" "$HOOK"; then
    ok "exit 0 implementado"
else
    err "sem exit 0"
fi

# 13-16. Testes funcionais
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/memoria"
TEST_KB="$TEST_DIR/.delta-11/kanban.md"
ORIG_CWD=$(pwd)

cd "$TEST_DIR"

# Cenario 13: BACK sem produto.md - DEVE BLOQUEAR
cat > "$TEST_KB" <<'EOF'
# Kanban
## CONCLUIDO
EOF

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## CONCLUIDO',
        'new_string': '## CONCLUIDO\n- [x] T-200 [BACK] Sem produto'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then
    ok "BLOQUEIA BACK sem produto.md"
else
    err "NAO bloqueia BACK sem produto.md (exit=$EXIT)"
fi

# Cenario 14: BACK com produto.md ANTIGO (mais de 4h) - DEVE BLOQUEAR
PRODUTO="$TEST_DIR/.delta-11/memoria/BACK-produto.md"
cat > "$PRODUTO" <<'EOF'
# BACK produto
Estado antigo.
EOF
# Define mtime para 5 horas atras (cross-platform: tenta macOS e Linux)
if touch -t "$(date -v-5H +%Y%m%d%H%M%S 2>/dev/null)" "$PRODUTO" 2>/dev/null; then
    : # macOS BSD touch funcionou
elif date -d "5 hours ago" +%Y%m%d%H%M%S >/dev/null 2>&1; then
    # Linux: usa touch -d
    touch -d "5 hours ago" "$PRODUTO" 2>/dev/null
else
    # Fallback: usa Python para setar mtime
    python3 -c "
import os, time
os.utime('$PRODUTO', (time.time() - 5*3600, time.time() - 5*3600))
" 2>/dev/null
fi

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## CONCLUIDO\n- [x] T-200',
        'new_string': '## CONCLUIDO\n- [x] T-200 [BACK] Antigo\n- [x] T-201 [BACK] Outro'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then
    ok "BLOQUEIA BACK com produto.md antigo (5h)"
else
    err "NAO bloqueia BACK com produto.md antigo (exit=$EXIT)"
fi

# Cenario 15: BACK com produto.md RECENTE - DEVE passar
touch "$PRODUTO"  # atualiza mtime para agora

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '- [x] T-201',
        'new_string': '- [x] T-201 [BACK] Recente\n- [x] T-202 [BACK] Mais um'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then
    ok "PASSA BACK com produto.md recente"
else
    err "NAO passa BACK com produto.md recente (exit=$EXIT)"
fi

# Cenario 16: ATLAS (isento) sem produto.md - DEVE passar
cat > "$TEST_KB" <<'EOF'
# Kanban
## CONCLUIDO
EOF

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## CONCLUIDO',
        'new_string': '## CONCLUIDO\n- [x] T-300 [ATLAS] Sem produto'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then
    ok "PASSA ATLAS (isento) sem produto.md"
else
    err "NAO passa ATLAS isento (exit=$EXIT)"
fi

cd "$ORIG_CWD"
rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Hook 3 produto-atualizado.py implementado${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi