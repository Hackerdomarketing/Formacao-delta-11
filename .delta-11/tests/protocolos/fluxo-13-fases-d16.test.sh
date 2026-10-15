#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da decisão D16 (v6.3) — as 13 fases do fluxo
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. O fluxo-zero-ao-lancamento.md tem um título para cada uma das
#      13 fases, nesta ordem: 0, 1, 2, 2.3, 2.4, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7.
#      (O "2.7" das decisões é o Passo 2.7 do SHIELD — testes de contrato —
#      e não tem título próprio no fluxo; se ganhar, precisa vir entre 2.5 e 3.)
#   2. O fluxo diz "13 fases".
#   3. Nenhum título ou resumo de CLAUDE.md, fluxo, metodologia ou
#      operativos conta outro número de fases ("7 fases", "7 FASES"...).
#   4. O mapa de Dias da metodologia (Dia 1=F0, 2=F2, 3=F3, 4=F3.5, 5=F4,
#      6=F4.5, 7=F7) e o teste supremo de 2 semanas.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

FLUXO="$DELTA_DIR/protocolos/fluxo-zero-ao-lancamento.md"
METODOLOGIA="$DELTA_DIR/conhecimento/metodologia-genesis-camadas.md"
CLAUDE="$REPO_ROOT/CLAUDE.md"

if require_file "$FLUXO" ".delta-11/protocolos/fluxo-zero-ao-lancamento.md"; then
    FASES=(0 1 2 2.3 2.4 2.5 3 3.5 4 4.5 5 6 7)
    anterior=0
    for fase in "${FASES[@]}"; do
        fase_regex="${fase//./\\.}"
        linha=$(first_line_number "$FLUXO" "^#{2,4} FASE ${fase_regex}([^.0-9]|$)")
        if [ -z "$linha" ]; then
            fail "fluxo sem título da Fase $fase"
        elif [ "$linha" -le "$anterior" ]; then
            fail "Fase $fase (linha $linha) fora de ordem"
        else
            pass "Fase $fase (linha $linha)"
            anterior="$linha"
        fi
    done
    linha_27=$(first_line_number "$FLUXO" '^#{2,4} FASE 2\.7([^0-9]|$)')
    if [ -n "$linha_27" ]; then
        pos_25=$(first_line_number "$FLUXO" '^#{2,4} FASE 2\.5([^0-9]|$)')
        pos_3=$(first_line_number "$FLUXO" '^#{2,4} FASE 3([^.0-9]|$)')
        if [ -n "$pos_25" ] && [ -n "$pos_3" ] && [ "$pos_25" -lt "$linha_27" ] && [ "$linha_27" -lt "$pos_3" ]; then
            pass "Fase 2.7 entre 2.5 e 3"
        else
            fail "Fase 2.7 fora de ordem (precisa ficar entre 2.5 e 3)"
        fi
    fi
    expect_match "$FLUXO" "13 fases" "o fluxo diz \"13 fases\""
fi

# Qualquer "N fases" com N diferente de 13 em título/resumo.
OUTRO_NUMERO='(^|[^0-9.])([02-9]|1[0-24-9]|[2-9][0-9]) fases'
ARQUIVOS=("$CLAUDE" "$FLUXO" "$METODOLOGIA")
for arquivo in "$DELTA_DIR/operativos/"*.md; do ARQUIVOS+=("$arquivo"); done
expect_no_instruction "nenhum texto conta outro número de fases (a contagem oficial é 13)" \
    "$OUTRO_NUMERO" "${ARQUIVOS[@]}"

if require_file "$METODOLOGIA" ".delta-11/conhecimento/metodologia-genesis-camadas.md"; then
    # Mapa de Dias (D16): Dia 1=F0, 2=F2, 3=F3, 4=F3.5, 5=F4, 6=F4.5, 7=F7.
    MAPA=("1:0" "2:2" "3:3" "4:3.5" "5:4" "6:4.5" "7:7")
    for par in "${MAPA[@]}"; do
        dia="${par%%:*}"
        fase="${par#*:}"
        fase_regex="${fase//./\\.}"
        if grep -qE "^\|[[:space:]]*(Dia )?${dia}[^0-9|][^|]*\|[^|]*Fase ${fase_regex}([^.0-9]|$)" "$METODOLOGIA"; then
            pass "metodologia: Dia $dia = Fase $fase"
        else
            fail "metodologia: a tabela de mapeamento não liga o Dia $dia à Fase $fase"
        fi
    done
    expect_match "$METODOLOGIA" "(2|duas) semanas" "metodologia: teste supremo de 2 semanas"
fi

finish_test "D16 — 13 fases do fluxo"
