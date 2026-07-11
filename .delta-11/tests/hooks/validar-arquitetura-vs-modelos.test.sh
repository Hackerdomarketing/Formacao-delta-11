#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do hook validar-arquitetura-vs-modelos.py (Etapa 4 do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que:
#   1. Hook existe em .delta-11/hooks/
#   2. Hook é executavel
#   3. Hook detecta edicao em kanban.md
#   4. Hook detecta transicao "PARA CONCLUIDO" em tarefa da Fase 3
#   5. Hook verifica que existe tarefa "Validação Retroativa Dia 2 ← Dia 3"
#      no kanban ANTES de permitir conclusao da Fase 3
#   6. Hook detecta valores SUSTENTA / REFAZER na retrovalidacao
#   7. Hook é cross-platform (Python 3)
#   8. Hook registrado em settings-hooks.json
#   9. Hook tem exit codes 0/2
#  10. Teste funcional:
#      - Edit em kanban movendo tarefa Fase 3 para CONCLUIDO SEM retrovalidacao
#        → exit 2 (bloqueia)
#      - Edit em kanban com retrovalidacao SUSTENTA → exit 0 (passa)
#      - Edit em kanban com retrovalidacao REFAZER → exit 2 ou 0 conforme politica
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/validar-arquitetura-vs-modelos.py"
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
    echo "Este teste é guarda de regressão do achado #3 da auditoria."
    echo "Se o hook sumir, o sistema inteiro perde a validacao retroativa"
    echo "do Dia 2 (Container) pelo Dia 3 (Superficies). Ate que hook seja"
    echo "criado, o teste falhara."
    exit 1
fi

# 2. Hook executavel
if [ -x "$HOOK" ]; then
    ok "hook é executavel"
else
    err "hook NAO é executavel (chmod +x $HOOK)"
fi

# 3. Hook detecta edicao em kanban.md
if grep -qE "kanban\.md|\.delta-11/kanban" "$HOOK"; then
    ok "hook detecta edicao em kanban.md"
else
    err "hook NAO detecta edicao em kanban.md — alvo incorreto"
fi

# 4. Hook detecta transicao PARA CONCLUIDO / CONCLUÍDO
if grep -qE "CONCLUIDO|CONCLU[IÍ]DO|✅" "$HOOK"; then
    ok "hook detecta marcadores de conclusao (CONCLUIDO / ✅)"
else
    err "hook NAO detecta marcadores de conclusao"
fi

# 5. Hook verifica tarefa de validacao retroativa
if grep -qiE "Valida[cç][ãa]o Retroativa|retroativa|retrovalid" "$HOOK"; then
    ok "hook verifica tarefa de validacao retroativa"
else
    err "hook NAO verifica tarefa de validacao retroativa do Dia 2 pelo Dia 3"
fi

# 6. Hook tem valores SUSTENTA / REFAZER reconhecidos
if grep -qE "SUSTENTA|REFAZER|REFACER" "$HOOK"; then
    ok "hook reconhece respostas SUSTENTA / REFAZER"
else
    err "hook NAO reconhece SUSTENTA / REFAZER — sem isso nao consegue diferenciar"
fi

# 7. Hook Python (cross-platform)
if head -1 "$HOOK" | grep -q "python"; then
    ok "hook é Python (cross-platform)"
else
    err "hook NAO é Python — quebra compatibilidade"
fi

# 8. Hook registrado em settings-hooks.json
if [ -f "$SETTINGS" ] && grep -q "validar-arquitetura-vs-modelos" "$SETTINGS"; then
    ok "hook registrado em settings-hooks.json"
else
    err "hook NAO registrado em settings-hooks.json — nao sera invocado"
fi

# 9. Hook tem exit codes 0 e 2
if grep -qE "sys\.exit\(0\)|return 0" "$HOOK" && grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "hook implementa exit codes 0 (passa) e 2 (bloqueia)"
else
    err "hook NAO implementa exit codes PreToolUse"
fi

# 10. Hook tem docstring
if head -5 "$HOOK" | grep -qE '"""'; then
    ok "hook tem docstring explicativa"
else
    err "hook NAO tem docstring"
fi

# Teste funcional: simular event PreToolUse
# Cenario A — Edit em kanban marcacao CONCLUIDO SEM retrovalidacao → BLOQUEIA (exit 2)
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/memoria"
TEST_KB="$TEST_DIR/.delta-11/kanban.md"
cat > "$TEST_KB" <<'EOF'
# Kanban
## FAZENDO
- [ ] T-VAULT-001 [CRÍTICO] Criar banco de dados
EOF

# Evento de Edit que move T-VAULT-001 para CONCLUÍDO
RESULT=$(python3 -c "
import json
event = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## FAZENDO\n- [ ] T-VAULT-001 [CRÍTICO] Criar banco de dados',
        'new_string': '## FAZENDO\n\n## CONCLUIDO\n- [x] T-VAULT-001 [CRÍTICO] Criar banco de dados\n\n## A FAZER\n- [ ] T-RETRO-001 Validacao Retroativa Dia 2 ← Dia 3'
    }
}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "2" ]; then
    ok "hook BLOQUEIA (exit 2) conclusao de tarefa Fase 3 SEM retrovalidacao registrada"
elif [ "$EXIT_CODE" = "0" ]; then
    err "hook NAO bloqueia conclusao sem retrovalidacao (deveria dar exit 2)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE)"
fi

# Cenario B — Edit em kanban com retrovalidacao SUSTENTA em CONCLUIDO → PASSA (exit 0)
RESULT=$(python3 -c "
import json
event = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_KB',
        'old_string': '## A FAZER\n- [ ] T-RETRO-001 Validacao Retroativa Dia 2 ← Dia 3',
        'new_string': '## A FAZER\n\n## CONCLUIDO\n- [x] T-RETRO-001 Validacao Retroativa Dia 2 ← Dia 3 — **SUSTENTA** (arquitetura do Dia 2 aguenta os modelos do Dia 3)'
    }
}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "0" ]; then
    ok "hook PASSA (exit 0) quando retrovalidacao SUSTENTA registrada"
elif [ "$EXIT_CODE" = "2" ]; then
    err "hook BLOQUEIA mesmo com retrovalidacao SUSTENTA (deveria dar exit 0)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE) para SUSTENTA"
fi

# Limpa
rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — hook validar-arquitetura-vs-modelos.py implementado corretamente${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi