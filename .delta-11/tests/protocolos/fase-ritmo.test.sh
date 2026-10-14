#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo fase-ritmo.md (Fase 3.5 = Dia 4)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O protocolo existe e liga com o fluxo (Fase 3.5) e com a Metodologia.
#   2. Os 10 artefatos do Dia 4 (cada um conferido).
#   3. D19: se o protocolo der números de tempo-limite, eles são os
#      padrões únicos: banco 5 s, API externa 10 s, chamada interna 3 s,
#      circuit breaker abre com 5 falhas e fecha em 60 s.
#   4. Quem sela; texto hebraico; exceções; endereço dos entregáveis.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fase-ritmo.md"
if ! require_file "$DOC" ".delta-11/protocolos/fase-ritmo.md"; then
    echo "  Este teste guarda o protocolo formal da Fase 3.5 (Dia 4)."
    finish_test "protocolo fase-ritmo.md"
fi

expect_match "$DOC" "FASE 3\.5|fluxo-zero-ao-lancamento" "liga com o fluxo (Fase 3.5)"
expect_match "$DOC" "metodologia-genesis-camadas|Dia 4|Astros" "liga com a Metodologia Gênesis (Dia 4)"

ARTEFATOS=("eventos" "filas" "jobs" "cache" "timeout" "retr(y|ies|i)" "circuit breaker" "CI/CD" "observabilidade" "sub-contraposi")
for artefato in "${ARTEFATOS[@]}"; do
    expect_match "$DOC" "$artefato" "artefato do Dia 4: '$artefato'"
done

# D19 — só confere os números que o texto citar (não obriga a citar).
D19_ERRADO='(banco|database|db)[^.|]{0,30}timeout[^.|]{0,10}\b([0-46-9]|[1-9][0-9]+) ?s\b|API externa[^.|]{0,30}\b([0-9]|1[1-9]|[2-9][0-9]) ?s\b|circuit breaker[^.|]{0,40}abre[^.|]{0,20}\b([0-46-9]|[1-9][0-9]+) falhas'
expect_no_match "$DOC" "$D19_ERRADO" "D19: tempos-limite citados seguem o padrão (banco 5 s, API externa 10 s, 5 falhas)"

expect_match "$DOC" "quem sel+a|sel+ad[oa] (por|pelo)|(Comandante|l(í|i)der t(é|e)cnico)[^.]{0,40}sel(o|a)" "declara quem sela"
expect_match "$DOC" "yehi meorot|bi-rekia|memshelet" "texto hebraico chave do Dia 4"
expect_match "$DOC" "quando (não|nao|NÃO|NAO) aplicar|exce(ção|cao|ções|coes)|isent" "declara quando NÃO aplicar"
expect_match "$DOC" "memoria/decisoes" "endereço dos entregáveis (memoria/decisoes/)"

finish_test "protocolo fase-ritmo.md (Fase 3.5)"
