#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do fluxo-zero-ao-lancamento.md — Fase 3.5 (Ritmo Temporal = Dia 4)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (a seção vai do título "FASE 3.5" até o próximo
# título de fase — não depende de "N linhas depois"):
#   1. Existe o título da Fase 3.5, com termo do Dia 4 (ritmo/astros/temporal).
#   2. A seção diz quem faz, quem sela e o resultado esperado. (As "janelas"
#      foram abolidas na v6.3 — D3: ninguém abre janela; o CRONOS conduz.)
#   3. A seção cita os 10 artefatos do Dia 4. Desde a v6.3 o fluxo usa os
#      nomes em português: "tempos-limite" (timeout) e "novas tentativas"
#      (retry). O teste aceita os dois nomes.
#   4. Ordem: Fase 3 < Fase 3.5 < Fase 4.
#   5. Liga com a Metodologia Gênesis.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/protocolos/fluxo-zero-ao-lancamento.md"
require_file "$DOC" ".delta-11/protocolos/fluxo-zero-ao-lancamento.md" || finish_test "Fase 3.5 no fluxo"

TITULO='^#{2,4} FASE 3\.5([^0-9]|$)'
SECAO=$(markdown_section "$DOC" "$TITULO")

if [ -z "$SECAO" ]; then
    fail "título 'FASE 3.5' ausente — sem ele o Dia 4 não existe no fluxo"
    finish_test "Fase 3.5 no fluxo"
fi
pass "título 'FASE 3.5' presente"

section_has() {
    if grep -qiE -- "$1" <<< "$SECAO"; then pass "$2"; else fail "$2"; fi
}
section_has "^#{2,4} FASE 3\.5.*(ritmo|astros|temporal)" "Fase 3.5 nomeada com termo do Dia 4"
section_has "CRONOS|DevOps|SRE|l(í|i)der t(é|e)cnico|quem faz" "Fase 3.5 diz quem faz"
section_has "quem sela|quem conduz|orquestrad[oa]s? pelo CRONOS" "Fase 3.5 diz quem conduz / quem sela"
section_has "resultado" "Fase 3.5 diz o resultado esperado"
for artefato in "eventos" "filas" "jobs" "cache" "timeout|tempos?-limite" "retr(y|ies|i)|novas tentativas" "circuit breaker" "CI/CD" "observabilidade" "sub-contraposi"; do
    section_has "$artefato" "Fase 3.5 cita o artefato '$artefato'"
done

pos_3=$(first_line_number "$DOC" '^#{2,4} FASE 3([^.0-9]|$)')
pos_35=$(first_line_number "$DOC" "$TITULO")
pos_4=$(first_line_number "$DOC" '^#{2,4} FASE 4([^.0-9]|$)')
if [ -z "$pos_3" ] || [ -z "$pos_4" ]; then
    fail "não deu para conferir a ordem — falta o título da Fase 3 ou da Fase 4"
elif [ "$pos_3" -lt "$pos_35" ] && [ "$pos_35" -lt "$pos_4" ]; then
    pass "ordem certa: Fase 3 (linha $pos_3) < Fase 3.5 (linha $pos_35) < Fase 4 (linha $pos_4)"
else
    fail "ORDEM ERRADA: Fase 3 (linha $pos_3) / 3.5 (linha $pos_35) / 4 (linha $pos_4) — 'peixes antes das águas'"
fi

expect_match "$DOC" "metodologia-genesis-camadas|Dia 4" "o fluxo liga com a Metodologia Gênesis (Dia 4)"

finish_test "Fase 3.5 (Ritmo Temporal) integra o fluxo"
