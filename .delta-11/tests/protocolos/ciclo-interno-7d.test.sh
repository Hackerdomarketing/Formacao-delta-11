#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo ciclo-interno-7d.md (Etapa 8A do v6.0, revisto na v6.3)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O protocolo existe.
#   2. As 7 sub-etapas do ciclo interno estão todas lá (cada uma conta uma
#      vez, com ou sem acento).
#   3. Liga com a Metodologia Gênesis, com o critério de selo e com o
#      template ciclo-interno-template.md.
#   4. Declara que se repete em cada fase.
#   5. D17: o checklist do ciclo vive no mini-plano planos/[AGENTE]-plan.md.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/ciclo-interno-7d.md"
require_file "$DOC" ".delta-11/protocolos/ciclo-interno-7d.md" || finish_test "protocolo ciclo-interno-7d.md"
pass "protocolo existe"

SUB_ETAPAS=(
    "planejamento"
    "delega(ção|cao)"
    "execu(ção|cao) paralela"
    "comunica(ção|cao)"
    "revis(ão|ao) cruzada"
    "teste adversarial"
    "selagem"
)
for sub in "${SUB_ETAPAS[@]}"; do
    expect_match "$DOC" "$sub" "sub-etapa '$sub'"
done

expect_match "$DOC" "metodologia-genesis|Metodologia G(ê|e)nesis|7 sub-etapas" "liga com a Metodologia Gênesis"
expect_match "$DOC" "selo|crit(é|e)rio" "fala do critério de selo"
expect_match "$DOC" "replic(á|a)vel|cada fase|por fase" "declara que se repete em cada fase"
expect_match "$DOC" "ciclo-interno-template" "aponta para o template ciclo-interno-template.md"
expect_match "$DOC" "mini-plano|-plan\.md" "D17: o checklist do ciclo vai no mini-plano (planos/[AGENTE]-plan.md)"

finish_test "protocolo ciclo-interno-7d.md"
