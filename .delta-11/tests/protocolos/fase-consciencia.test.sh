#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo fase-consciencia.md (Fase 4.5 = Dia 6)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O protocolo existe (sem ele o teste FALHA e sai — antes, uma frase
#      solta era executada como comando nessa saída: C-128).
#   2. Liga com o fluxo (Fase 4.5) e com a Metodologia Gênesis (Dia 6).
#   3. Os 5 entregáveis do Dia 6 — CADA UM precisa estar lá (antes, a
#      contagem somava variações com e sem acento e passava faltando
#      entregável): auditoria imutável, rate limiting, motor de regras,
#      LGPD, fluxos de aprovação.
#   4. Quem sela; texto hebraico do Dia 6; skills globais; exceções;
#      endereço dos entregáveis; relação com o Dia 5.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fase-consciencia.md"
if ! require_file "$DOC" ".delta-11/protocolos/fase-consciencia.md"; then
    echo "  Este teste guarda o protocolo formal da Fase 4.5 (Dia 6)."
    finish_test "protocolo fase-consciencia.md"
fi

expect_match "$DOC" "FASE 4\.5|fluxo-zero-ao-lancamento" "liga com o fluxo (Fase 4.5)"
expect_match "$DOC" "metodologia-genesis-camadas|Dia 6|Consci(ê|e)ncia Dominante" "liga com a Metodologia Gênesis (Dia 6)"

ENTREGAVEIS=(
    "auditoria imut(á|a)vel"
    "rate limit"
    "motor de regras"
    "LGPD"
    "fluxos? de aprova(ção|cao|ções|coes)"
)
for entregavel in "${ENTREGAVEIS[@]}"; do
    expect_match "$DOC" "$entregavel" "entregável do Dia 6: '$entregavel'"
done

expect_match "$DOC" "quem sel+a|sel+ad[oa] (por|pelo)|(SHIELD|Comandante)[^.]{0,40}sel(o|a)" "declara quem sela"
expect_match "$DOC" "naaseh adam|tov meod|be-tzalmenu|zachar u-nekev" "texto hebraico chave do Dia 6"
expect_match "$DOC" "owasp-top10|supabase-rls|skills-globais" "liga com as skills globais"
expect_match "$DOC" "quando (não|nao|NÃO|NAO) aplicar|exce(ção|cao|ções|coes)|isent" "declara quando NÃO aplicar"
expect_match "$DOC" "memoria/decisoes" "endereço dos entregáveis (memoria/decisoes/)"
expect_match "$DOC" "Dia 5|governa[^.]{0,20}habitante|acima[^.]{0,20}servi(ç|c)os" "relação com o Dia 5 (governa os habitantes)"

finish_test "protocolo fase-consciencia.md (Fase 4.5)"
