#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do fluxo-zero-ao-lancamento.md — Fase 4.5 (Consciência = Dia 6)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (seção = do título "FASE 4.5" ao próximo título de fase):
#   1. Título da Fase 4.5 com termo do Dia 6.
#   2. Quem faz, quem sela e resultado. (As "janelas" foram abolidas na
#      v6.3 — D3: ninguém abre janela; o CRONOS conduz.)
#   3. Os 5 entregáveis do Dia 6. Desde a v6.3 o fluxo diz "limite de
#      requisições" (rate limit). O teste aceita os dois nomes.
#   4. Liga com as skills globais (owasp-top10 / supabase-rls).
#   5. Ordem: Fase 4 < Fase 4.5 < Fase 5.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fluxo-zero-ao-lancamento.md"
require_file "$DOC" ".delta-11/protocolos/fluxo-zero-ao-lancamento.md" || finish_test "Fase 4.5 no fluxo"

TITULO='^#{2,4} FASE 4\.5([^0-9]|$)'
SECAO=$(markdown_section "$DOC" "$TITULO")
if [ -z "$SECAO" ]; then
    fail "título 'FASE 4.5' ausente"
    finish_test "Fase 4.5 no fluxo"
fi
pass "título 'FASE 4.5' presente"

section_has() {
    if grep -qiE -- "$1" <<< "$SECAO"; then pass "$2"; else fail "$2"; fi
}
section_has "^#{2,4} FASE 4\.5.*(consci(ê|e)ncia|autentica(ção|cao)|autoriza(ção|cao))" "Fase 4.5 nomeada com termo do Dia 6"
section_has "quem" "Fase 4.5 diz quem faz"
section_has "quem sela|quem conduz|orquestrad[oa]s? pelo CRONOS" "Fase 4.5 diz quem conduz / quem sela"
section_has "resultado" "Fase 4.5 diz o resultado"
for entregavel in "auditoria imut(á|a)vel" "rate limit|limite de requisi(ç|c)(õ|o)es" "motor de regras" "LGPD" "fluxos? de aprova(ção|cao|ções|coes)"; do
    section_has "$entregavel" "Fase 4.5 cita o entregável '$entregavel'"
done
section_has "owasp-top10|supabase-rls|skills-globais" "Fase 4.5 liga com as skills globais"

pos_4=$(first_line_number "$DOC" '^#{2,4} FASE 4([^.0-9]|$)')
pos_45=$(first_line_number "$DOC" "$TITULO")
pos_5=$(first_line_number "$DOC" '^#{2,4} FASE 5([^.0-9]|$)')
if [ -z "$pos_4" ] || [ -z "$pos_5" ]; then
    fail "não deu para conferir a ordem — falta o título da Fase 4 ou da Fase 5"
elif [ "$pos_4" -lt "$pos_45" ] && [ "$pos_45" -lt "$pos_5" ]; then
    pass "ordem certa: Fase 4 (linha $pos_4) < Fase 4.5 (linha $pos_45) < Fase 5 (linha $pos_5)"
else
    fail "ORDEM ERRADA: Fase 4 (linha $pos_4) / 4.5 (linha $pos_45) / 5 (linha $pos_5)"
fi

finish_test "Fase 4.5 (Consciência) integra o fluxo"
