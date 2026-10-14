#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do template ciclo-interno-template.md (Etapa 8B do v6.0)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O template existe.
#   2. Tem um título para CADA uma das 7 sub-etapas, na ordem 1 → 7.
#   3. Cada sub-etapa termina em pergunta concreta (pelo menos 7 "?").
#   4. Liga com o protocolo ciclo-interno-7d.md e com a Metodologia Gênesis.
#   5. Usa campos para preencher ({{CAMPO}}) e tem entregável esperado.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

TEMPLATE="$DELTA_DIR/templates/ciclo-interno-template.md"
require_file "$TEMPLATE" ".delta-11/templates/ciclo-interno-template.md" || finish_test "template ciclo-interno"

NOMES=("planejamento" "delega(ção|cao)" "execu(ção|cao)" "comunica(ção|cao)" "revis(ão|ao)" "teste adversarial" "selagem")
anterior=0
for numero in 1 2 3 4 5 6 7; do
    nome="${NOMES[$((numero - 1))]}"
    linha=$(grep -niE "^#+ .*sub-etapa $numero([^0-9]|$).*($nome)" "$TEMPLATE" | head -1 | cut -d: -f1 || true)
    if [ -z "$linha" ]; then
        fail "sem título para a sub-etapa $numero ($nome)"
    elif [ "$linha" -le "$anterior" ]; then
        fail "sub-etapa $numero fora de ordem"
    else
        pass "sub-etapa $numero ($nome) na linha $linha"
        anterior="$linha"
    fi
done

perguntas=$(grep -c "?" "$TEMPLATE" || true)
if [ "$perguntas" -ge 7 ]; then
    pass "pelo menos 7 perguntas concretas ($perguntas)"
else
    fail "só $perguntas pergunta(s) — sub-etapas sem pergunta concreta"
fi

expect_match "$TEMPLATE" "ciclo-interno-7d" "liga com o protocolo ciclo-interno-7d.md"
expect_match "$TEMPLATE" "metodologia-genesis|G(ê|e)nesis" "liga com a Metodologia Gênesis"
expect_match "$TEMPLATE" '\{\{[A-Z_]+\}\}' "usa campos para preencher ({{CAMPO}})"
expect_match "$TEMPLATE" '\[ \]|entreg|resultad|evid(ê|e)ncia' "tem entregável/resultado esperado"

finish_test "template ciclo-interno-template.md"
