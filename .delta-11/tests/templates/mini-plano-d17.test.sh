#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da decisão D17 (v6.3) — mini-plano do agente
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos no mini-plano-agente-template.md:
#   1. O arquivo é planos/[AGENTE]-plan.md — UM por agente, sobrescrito a
#      cada onda; o histórico vai para planos/arquivo/.
#      (Não pode mais mandar salvar como [AGENTE]-plan-[ciclo]-onda-[N].md.)
#   2. As 6 seções, na ordem:
#      1 Objetivo da onda; 2 Recorte da fase anterior (cita o -produto.md
#      anterior); 3 Tarefas; 4 Critérios de aceite; 5 Limites de escopo;
#      6 Convenções.
#   3. Traz o checklist do ciclo interno de 7 sub-etapas.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

TEMPLATE="$DELTA_DIR/templates/mini-plano-agente-template.md"
require_file "$TEMPLATE" ".delta-11/templates/mini-plano-agente-template.md" || finish_test "D17 — mini-plano"

expect_match "$TEMPLATE" "planos/\[AGENTE\]-plan\.md" "D17: caminho único planos/[AGENTE]-plan.md"
expect_match "$TEMPLATE" "planos/arquivo" "D17: histórico em planos/arquivo/"
expect_no_instruction "D17: não manda salvar um arquivo por onda ([AGENTE]-plan-[ciclo]-onda-[N].md)" \
    "-plan-\[[^]]*\]-onda" "$TEMPLATE"

SECOES=(
    "1:objetivo"
    "2:recorte"
    "3:tarefa"
    "4:crit(é|e)rios? de aceite"
    "5:limites de escopo"
    "6:conven(ç|c)(õ|o)es"
)
anterior=0
for item in "${SECOES[@]}"; do
    numero="${item%%:*}"
    conceito="${item#*:}"
    linha=$(grep -niE "^#+ +${numero}\.? +(${conceito})" "$TEMPLATE" | head -1 | cut -d: -f1 || true)
    if [ -z "$linha" ]; then
        fail "D17: seção $numero ($conceito) ausente"
    elif [ "$linha" -le "$anterior" ]; then
        fail "D17: seção $numero fora de ordem"
    else
        pass "D17: seção $numero ($conceito) na linha $linha"
        anterior="$linha"
    fi
done

RECORTE=$(markdown_section "$TEMPLATE" "^#+ +2\.? .*recorte")
if grep -qE -- "-produto\.md" <<< "$RECORTE"; then
    pass "D17: o recorte da fase anterior cita o -produto.md anterior"
else
    fail "D17: o recorte da fase anterior não cita o -produto.md anterior"
fi

expect_match "$TEMPLATE" "7 sub-etapas|ciclo interno|ciclo-interno" "D17: checklist do ciclo interno de 7 sub-etapas"

finish_test "D17 — mini-plano do agente"
