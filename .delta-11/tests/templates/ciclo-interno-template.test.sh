#!/usr/bin/env bash
# Teste do template ciclo-interno-template.md (Etapa 8B do v6.0)

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../../templates/ciclo-interno-template.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

if [ -f "$TEMPLATE" ]; then
    ok "template existe em .delta-11/templates/ciclo-interno-template.md"
else
    err "template AUSENTE"; exit 1
fi

# 7 secoes com nomes das sub-etapas
secoes=(
    "Planejamento"
    "Delegação"
    "Execução"
    "Comunicação"
    "Revisão"
    "Teste adversarial"
    "Selagem"
)
cobertos=0
for sec in "${secoes[@]}"; do
    if grep -qi "$sec" "$TEMPLATE"; then
        cobertos=$((cobertos + 1))
    fi
done
if [ "$cobertos" -ge 7 ]; then
    ok "7 secoes presentes (encontradas $cobertos)"
else
    err "apenas $cobertos secoes (minimo 7)"
fi

# Cross-reference com protocolo
if grep -qi "ciclo-interno-7d" "$TEMPLATE"; then
    ok "cross-reference com protocolo"; else err "sem cross-reference com protocolo"
fi

# Metodologia
if grep -qi "metodologia-genesis\|Genesis" "$TEMPLATE"; then
    ok "cross-reference com Metodologia Genesis"; else err "sem cross-ref Metodologia"
fi

# Placeholders
if grep -qE "\{\{[A-Z_]+\}\}|\[A-Z_+\]" "$TEMPLATE"; then
    ok "placeholders editaveis"; else err "sem placeholders"
fi

# Pergunta por secao (formato "?" na secao)
PERGUNTAS=$(grep -cE "\?" "$TEMPLATE" || true)
if [ "$PERGUNTAS" -ge 7 ]; then
    ok "pelo menos 7 perguntas concretas (uma por sub-etapa)"
else
    err "apenas $PERGUNTAS perguntas — sub-etapas sem perguntas concretas"
fi

# Entregavel esperado (formato checkbox ou explicit)
if grep -qE "checkbox|\[ \]|ENTREG|Resultad|Evidência" "$TEMPLATE"; then
    ok "template tem entregavel/resultado esperado"
else
    err "sem entregavel esperado — sub-etapa sem saida clara"
fi

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — template ciclo-interno-template.md${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }