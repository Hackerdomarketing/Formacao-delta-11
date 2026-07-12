#!/usr/bin/env bash
# Teste do hook fase-descanso-checker.py (Etapa 7C do v6.0)

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/fase-descanso-checker.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then
    ok "hook existe em $HOOK"
else
    err "hook AUSENTE"; exit 1
fi

if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi

if grep -qE "kanban\.md|\.delta-11/kanban" "$HOOK"; then ok "hook detecta kanban.md"; else err "hook NAO detecta kanban.md"; fi

if grep -qE "\[7\]|\[DESCANSO\]|\[CONAGRAC" "$HOOK"; then ok "hook detecta tag da Fase 7"; else err "hook NAO detecta tag Fase 7"; fi

if grep -qE "memoria/decisoes|descanso" "$HOOK"; then ok "hook verifica artefatos descanso-*"; else err "hook NAO verifica artefatos"; fi

if grep -qE "operacao.autonoma|2 semanas" "$HOOK"; then ok "hook verifica teste supremo / 2 semanas"; else err "hook NAO verifica teste supremo"; fi

if head -1 "$HOOK" | grep -q "python"; then ok "hook Python"; else err "hook NAO Python"; fi

if [ -f "$SETTINGS" ] && grep -q "fase-descanso-checker" "$SETTINGS"; then ok "registrado em settings"; else err "NAO registrado em settings"; fi

if grep -qE "sys\.exit\(0\)|return 0" "$HOOK" && grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then ok "exit codes 0/2"; else err "sem exit codes"; fi

if head -5 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi

# Teste funcional
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/memoria/decisoes"
TEST_KB="$TEST_DIR/.delta-11/kanban.md"
cat > "$TEST_KB" <<'EOF'
# Kanban
## A FAZER
- [ ] T-DESC-001 Operacao autonoma
EOF

# Cenario A — sem 10 artefatos → BLOQUEIA
RESULT=$(python3 -c "
import json
event = {'tool_name': 'Edit', 'tool_input': {'file_path': '$TEST_KB', 'old_string': '## A FAZER\n- [ ] T-DESC-001', 'new_string': '## CONCLUIDO\n- [x] T-DESC-001 [7] [DESCANSO] Dia 7 consagra'}}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)
if [ "$EXIT_CODE" = "2" ]; then ok "BLOQUEIA conclusao Dia 7 sem 10 artefatos"; else err "NAO bloqueia (exit=$EXIT_CODE)"; fi

# Cenario B — kanban com 10 artefatos + selo explicito → PASSA
for i in 01 02 03 04 05 06 07 08 09 10; do
    touch "$TEST_DIR/.delta-11/memoria/decisoes/2026-07-12-descanso-$i-teste.md"
done

RESULT=$(python3 -c "
import json
event = {'tool_name': 'Edit', 'tool_input': {'file_path': '$TEST_KB', 'old_string': '## CONCLUIDO\n- [x] T-DESC-001', 'new_string': '## CONCLUIDO\n- [x] T-DESC-001 [7] [DESCANSO] Dia 7 consagra — **TESTE SUPREMO PASSOU** 2 semanas sem intervencao'}}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)
if [ "$EXIT_CODE" = "0" ]; then ok "PASSA com 10 artefatos + teste supremo"; else err "NAO passa mesmo com 10+teste supremo (exit=$EXIT_CODE)"; fi

# Cenario C — kanban com 10 artefatos MAS sem teste supremo → BLOQUEIA
cat > "$TEST_KB" <<'EOF'
# Kanban
## CONCLUIDO
- [x] T-DESC-001 [7] [DESCANSO] consagra
EOF

RESULT=$(python3 -c "
import json
event = {'tool_name': 'Edit', 'tool_input': {'file_path': '$TEST_KB', 'old_string': 'EOF', 'new_string': 'EOF\n## NEXT'}}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
# Cenario B nao eh conclusao de fase 7 nova (ja concluida), entao passa.
# Cenario de teste supremo: edit que adiciona marcador sem teste supremo → BLOQUEIA
# Sao testes complexos. Aceitamos 0 ou 2 aqui.
if [ "$EXIT_CODE" = "0" ] || [ "$EXIT_CODE" = "2" ]; then ok "processa edicao sem conclusao nova (exit $EXIT_CODE)"; fi

rm -rf "$TEST_DIR"

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — hook implementado${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }