#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo fase-descanso.md (Fase 7 = Dia 7)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O protocolo existe e liga com o fluxo (Fase 7) e com a Metodologia.
#   2. Os 10 entregáveis do Dia 7 — CADA UM precisa estar lá. Antes a lista
#      tinha "documentação técnica" duas vezes e aceitava 9 de 12 (passava
#      faltando entregável).
#   3. D16: o TESTE SUPREMO é de 2 semanas — e nenhum trecho fala em
#      "1 semana" / "uma semana" como teste supremo.
#   4. Quem sela; texto hebraico; ligação com o monitor; endereço dos
#      entregáveis; diferença entre selo provisório (Fase 6) e definitivo (Fase 7).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fase-descanso.md"
require_file "$DOC" ".delta-11/protocolos/fase-descanso.md" || finish_test "protocolo fase-descanso.md"

expect_match "$DOC" "FASE 7|fluxo-zero-ao-lancamento" "liga com o fluxo (Fase 7)"
expect_match "$DOC" "metodologia-genesis-camadas|Dia 7|Descanso Consagrado" "liga com a Metodologia Gênesis (Dia 7)"

ENTREGAVEIS=(
    "documenta(ção|cao) t(é|e)cnica"
    "documenta(ção|cao) de dom(í|i)nio"
    "testes? de aceita(ção|cao)|E2E"
    "deploy automatizado"
    "runbook"
    "alerta"
    "tag de release"
    "backup testado"
    "DR testado|disaster recovery"
    "onboarding"
)
for entregavel in "${ENTREGAVEIS[@]}"; do
    expect_match "$DOC" "$entregavel" "entregável do Dia 7: '$entregavel'"
done

expect_match "$DOC" "teste supremo" "menciona o TESTE SUPREMO"
expect_match "$DOC" "(2|duas) semanas" "D16: teste supremo de 2 semanas"
expect_no_match "$DOC" "(1|uma) semana[^s]" "D16: nada de teste supremo de 1 semana"
expect_match "$DOC" "quem sel+a|sel+ad[oa] (por|pelo)|Comandante[^.]{0,40}sel(o|a)" "declara quem sela"
expect_match "$DOC" "vayechulu|vayishbot|vayvarech|kadash" "texto hebraico chave do Dia 7"
expect_match "$DOC" "monitor-delta11|opera(ção|cao) aut(ô|o)noma" "liga com o monitor / operação autônoma"
expect_match "$DOC" "memoria/decisoes|memoria/runbooks" "endereço dos entregáveis"
expect_match "$DOC" "provis(ó|o)rio" "fala do selo provisório (Fase 6)"
expect_match "$DOC" "definitivo" "fala do selo definitivo (Fase 7)"

finish_test "protocolo fase-descanso.md (Fase 7)"
