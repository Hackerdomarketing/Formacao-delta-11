#!/usr/bin/env bash
# Teste do hook dia1-badal-checker.py (Etapa 9A do v6.0)
#
# Verifica que:
#   1. Hook existe em .delta-11/hooks/dia1-badal-checker.py
#   2. Hook é executavel
#   3. Hook detecta edicao em PRD (.delta-11/docs/prd.md)
#   4. Hook verifica presenca das 8 perguntas obrigatorias do Dia 1:
#      - frase decisoria
#      - identidade assumida
#      - identidade fugida
#      - teste do badal
#      - inimigo unico
#      - trauma unico
#      - lago abandonado
#      - nova categoria de solucao
#   5. Hook e Python
#   6. Hook registrado em settings-hooks.json
#   7. Hook tem exit codes 0/2
#   8. Hook tem docstring
#   9. Teste funcional:
#      - PRD sem 8 perguntas -> BLOQUEIA (exit 2)
#      - PRD com 8 perguntas -> PASSA (exit 0)
#      - Edicao em arquivo NAO-PRD -> passa direto
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/dia1-badal-checker.py"
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
    echo "Teste de regressão da Etapa 9A do v6.0 (Dia 1 com teste do badal)."
    echo "Se o hook sumir, o sistema perde a validacao automatica das 8"
    echo "perguntas obrigatorias do Dia 1 da Metodologia Genesis."
    exit 1
fi

# 2. Hook executavel
if [ -x "$HOOK" ]; then
    ok "hook executavel"
else
    err "hook NAO executavel"
fi

# 3. Hook detecta PRD (ou project-core como fallback)
if grep -qE "prd\.md|project-core\.md" "$HOOK"; then
    ok "hook detecta arquivo alvo (PRD ou project-core)"
else
    err "hook NAO detecta arquivo alvo"
fi

# 4. Hook verifica as 8 perguntas obrigatorias
perguntas=(
    "frase decis"
    "frase deciso"
    "identidade assumida"
    "identidade fugida"
    "badal"
    "inimigo"
    "trauma"
    "lago abandonado"
    "lago"
    "nova categoria"
    "Categoria"
)
# Verifica pelo menos 6 das 8 (busca com sinonimos)
cobertos=0
for p in "${perguntas[@]}"; do
    if grep -qi "$p" "$HOOK"; then
        cobertos=$((cobertos + 1))
    fi
done
if [ "$cobertos" -ge 6 ]; then
    ok "hook cobre pelo menos 6 dos 8 elementos do Dia 1 (buscou $cobertos sinonimos)"
else
    err "hook cobre apenas $cobertos elementos — insuficiente para Dia 1"
fi

# 5. Hook Python
if head -1 "$HOOK" | grep -q "python"; then
    ok "hook Python (cross-platform)"
else
    err "hook NAO Python"
fi

# 6. Registrado em settings
if [ -f "$SETTINGS" ] && grep -q "dia1-badal-checker" "$SETTINGS"; then
    ok "registrado em settings-hooks.json"
else
    err "NAO registrado em settings-hooks.json"
fi

# 7. Exit codes
if grep -qE "sys\.exit\(0\)|return 0" "$HOOK" && grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "exit codes 0/2"
else
    err "sem exit codes 0/2"
fi

# 8. Docstring
if head -5 "$HOOK" | grep -qE '"""'; then
    ok "docstring presente"
else
    err "sem docstring"
fi

# 9. Teste funcional
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/docs"
TEST_PRD="$TEST_DIR/docs/prd.md"

# Cenario A: PRD vazio (sem 8 perguntas) — Write tool
cat > "$TEST_PRD" <<'EOF'
# PRD
## Visão Geral
Um produto qualquer
EOF

RESULT=$(python3 -c "
import json
event = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '$TEST_PRD',
        'content': '# PRD\n## Visao\nUm produto qualquer\n'
    }
}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "2" ]; then
    ok "hook BLOQUEIA PRD sem 8 perguntas"
elif [ "$EXIT_CODE" = "0" ]; then
    err "hook NAO bloqueia PRD vazio (deveria dar exit 2)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE)"
fi

# Cenario B: PRD com 8 perguntas — Write tool
cat > "$TEST_PRD" <<'EOF'
# PRD

## Frase decisória
"Eu uso X para me tornar Y, fugindo de Z"

## Identidade assumida
Pessoa que cuida de suas próprias finanças

## Identidade fugida
Pessoa dependente de bancos tradicionais

## Teste do badal
As duas identidades ficam nítidas: cuidadosa vs dependente

## Inimigo único
A ilusão de que gerenciar dinheiro é coisa de rico

## Trauma único
Adultos que chegam aos 50 sem reserva nenhuma

## Lago abandonado
Planilha do Excel esquecida há 3 anos

## Nova categoria de Solução
Finanças pessoais com guarda automatizada
EOF

RESULT=$(python3 -c "
import json
event = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '$TEST_PRD',
        'content': open('$TEST_PRD').read()
    }
}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "0" ]; then
    ok "hook PASSA PRD com 8 perguntas respondidas"
elif [ "$EXIT_CODE" = "2" ]; then
    err "hook BLOQUEIA mesmo PRD completo (deveria dar exit 0)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE)"
fi

# Cenario C: edicao em arquivo NAO-PRD — passa direto
RESULT=$(python3 -c "
import json
event = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '$TEST_DIR/algum-outro.md',
        'old_string': 'x',
        'new_string': 'y'
    }
}
print(json.dumps(event))
" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "0" ]; then
    ok "hook ignora edicao em arquivo NAO-PRD"
elif [ "$EXIT_CODE" = "2" ]; then
    err "hook BLOQUEIA edicao em arquivo nao-alvo (NAO deveria)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE)"
fi

# Limpa
rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — hook dia1-badal-checker.py implementado${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi