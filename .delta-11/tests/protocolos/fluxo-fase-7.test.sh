#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do fluxo-zero-ao-lancamento.md — Fase 7 (Descanso = Dia 7)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (seção = do título "FASE 7" ao próximo título de fase):
#   1. Título da Fase 7 com termo do Dia 7.
#   2. Quem faz, janela e resultado.
#   3. Os 10 entregáveis do Dia 7.
#   4. D16: teste supremo de 2 semanas.
#   5. Ordem: Fase 6 < Fase 7.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fluxo-zero-ao-lancamento.md"
require_file "$DOC" ".delta-11/protocolos/fluxo-zero-ao-lancamento.md" || finish_test "Fase 7 no fluxo"

TITULO='^#{2,4} FASE 7([^.0-9]|$)'
SECAO=$(markdown_section "$DOC" "$TITULO")
if [ -z "$SECAO" ]; then
    fail "título 'FASE 7' ausente — o Dia 7 não existe no fluxo"
    finish_test "Fase 7 no fluxo"
fi
pass "título 'FASE 7' presente"

section_has() {
    if grep -qiE -- "$1" <<< "$SECAO"; then pass "$2"; else fail "$2"; fi
}
section_has "^#{2,4} FASE 7.*(descanso|consagra(ção|cao)|aut(ô|o)noma)" "Fase 7 nomeada com termo do Dia 7"
section_has "quem" "Fase 7 diz quem faz"
section_has "janela" "Fase 7 diz a janela"
section_has "resultado" "Fase 7 diz o resultado"
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
    section_has "$entregavel" "Fase 7 cita o entregável '$entregavel'"
done
section_has "teste supremo" "Fase 7 cita o teste supremo"
section_has "(2|duas) semanas" "D16: teste supremo de 2 semanas"

pos_6=$(first_line_number "$DOC" '^#{2,4} FASE 6([^.0-9]|$)')
pos_7=$(first_line_number "$DOC" "$TITULO")
if [ -z "$pos_6" ]; then
    fail "título da Fase 6 ausente — não deu para conferir a ordem"
elif [ "$pos_6" -lt "$pos_7" ]; then
    pass "ordem certa: Fase 6 (linha $pos_6) < Fase 7 (linha $pos_7)"
else
    fail "ORDEM ERRADA: Fase 6 (linha $pos_6) / Fase 7 (linha $pos_7)"
fi

finish_test "Fase 7 (Descanso) integra o fluxo"
