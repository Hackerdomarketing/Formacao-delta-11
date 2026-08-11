#!/usr/bin/env bash
# Teste do hook forca-despacho.py (Etapa 2 do v6.2)
#
# Verifica:
#   1. Hook existe em .delta-11/hooks/forca-despacho.py
#   2. Hook executavel
#   3. Hook detecta edit em kanban.md
#   4. Hook detecta transicao "CONCLUIDO" no novo conteudo
#   5. Hook identifica agente (BACK, FRONT, etc.) na tarefa
#   6. Hook BLOQUEIA se BACK tentar CONCLUIDO sem log de sub-agente
#   7. Hook PASSA se BACK tiver log de build-validator recente
#   8. Hook PASSA se agente for ATLAS/CRONOS (isentos)
#   9. Hook Python cross-platform
#  10. Hook registrado em settings-hooks.json
#  11. Hook tem docstring
#  12. Hook tem exit codes 0/2
#  13. Teste funcional - agente NAO executor passa
#  14. Teste funcional - agente executor com log passa
#  15. Teste funcional - agente executor sem log BLOQUEIA

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/forca-despacho.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1-2. Hook existe e executavel
if [ -f "$HOOK" ]; then
    ok "hook existe em $HOOK"
else
    err "hook AUSENTE em $HOOK"
    echo "Teste de regressão do Hook 2 forca-despacho (Furo 2)."
    echo "Se hook sumir, sistema perde proteção contra agente marcar"
    echo "CONCLUIDO sem disparar sub-agente de validação."
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

# 5-6. Identifica agente + BLOQUEIA sem log
if grep -qE "AGENTES_EXECUTORES|\[BACK\]|\[FRONT\]|extract_agente" "$HOOK"; then
    ok "hook identifica agente da tarefa"
else
    err "hook NAO identifica agente"
fi

if grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "hook implementa exit 2 (bloqueio)"
else
    err "hook NAO implementa exit 2"
fi

# 7-8. Isencao de agentes arquiteto
if grep -qiE "ATLAS.*isent|isent.*ATLAS|isento.*CRONOS" "$HOOK"; then
    ok "hook isenta ATLAS/CRONOS (agentes arquitetos)"
else
    err "hook NAO isenta agentes arquitetos"
fi

# 9-10. Python + settings
if head -1 "$HOOK" | grep -q "python"; then
    ok "hook Python (cross-platform)"
else
    err "hook NAO Python"
fi

if [ -f "$SETTINGS" ] && grep -q "forca-despacho" "$SETTINGS"; then
    ok "registrado em settings-hooks.json"
else
    err "NAO registrado em settings-hooks.json"
fi

# 11-12. Docstring + exit codes
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

# 13-15. Testes funcionais
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/logs/sub-agentes"
TEST_KB="$TEST_DIR/.delta-11/kanban.md"

# Salva cwd original para restaurar no fim
ORIG_CWD=$(pwd)

# Cenario A: agente NAO executor (ATLAS) marcando CONCLUIDO - DEVE passar
cd "$TEST_DIR"
cat > "$TEST_KB" <<'EOF'
# Kanban
## CONCLUIDO
- [x] T-001 [ATLAS] Teste
EOF

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '# Kanban\n## CONCLUIDO',
        'new_string': '# Kanban\n## CONCLUIDO\n- [x] T-002 [ATLAS] Outro'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then
    ok "PASSA quando agente NAO-executor (ATLAS) marca CONCLUIDO"
else
    err "NAO passa para agente NAO-executor (exit=$EXIT)"
fi

# Cenario B: agente executor (BACK) SEM log de sub-agente - DEVE BLOQUEAR
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
        'new_string': '## CONCLUIDO\n- [x] T-100 [BACK] Implementar feature X'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "2" ]; then
    ok "BLOQUEIA quando BACK marca CONCLUIDO sem log de sub-agente"
else
    err "NAO bloqueia BACK sem sub-agente (exit=$EXIT)"
fi

# Cenario C: agente executor (BACK) COM log de sub-agente - DEVE passar
cat > "$TEST_KB" <<'EOF'
# Kanban
## CONCLUIDO
EOF

# Cria log de sub-agente recente
LOG_FILE="$TEST_DIR/.delta-11/logs/sub-agentes/2026-08-11-build-validator-BACK.log"
touch "$LOG_FILE"

EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## CONCLUIDO',
        'new_string': '## CONCLUIDO\n- [x] T-101 [BACK] Implementar feature Y'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then
    ok "PASSA quando BACK tem log de build-validator recente"
else
    err "NAO passa BACK com sub-agente recente (exit=$EXIT)"
fi

cd "$ORIG_CWD"
rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Hook 2 forca-despacho.py implementado${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi