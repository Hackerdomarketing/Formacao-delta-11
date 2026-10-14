#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da rotina única dos executores (v6.3 — D6, D8, D9, D10, D16)
# ════════════════════════════════════════════════════════════════
# Executores: VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT.
# Conceitos conferidos em cada operativo:
#   D9  Início: ACK (ativacoes/ack-[NOME].txt) e Passo 0.3 (travas com mkdir
#       em .delta-11/locks/). Fim: autocrítica em logs/autocritica/,
#       build-validator e contract-tester.
#   D6  (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM) leem as FATIAS em
#       memoria/project-core/ (banco, contratos, visual, decisoes-tecnicas)
#       e NÃO mandam ler o project-core.md inteiro.
#   D8  Estado = [NOME]-produto.md + [NOME]-historia.md. Nenhuma instrução
#       manda escrever [NOME]-estado.md (legado: só leitura, se existir).
#   D10 Só o CRONOS escreve kanban.md e kanban-data.js: nenhum executor
#       manda atualizar/escrever/mover nada no kanban.
#   D16 O executor sabe que as Fases 3.5, 4.5 e 7 existem.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

EXECUTORES=("VAULT" "BACK" "ENGINE" "FRONT" "PIXEL" "FORM" "SCOUT")
LEEM_FATIAS=" VAULT BACK ENGINE FRONT PIXEL FORM "

for agente in "${EXECUTORES[@]}"; do
    arquivo="$DELTA_DIR/operativos/$agente.md"
    echo "[$agente]"
    require_file "$arquivo" ".delta-11/operativos/$agente.md" || continue

    # D9 — início e fim da tarefa
    expect_match "$arquivo" "ack-($agente|\[NOME\]|\[SEU-NOME\])\.txt" "$agente D9: Passo 0 grava o ACK"
    if { grep -qE "locks/" "$arquivo" && grep -qE "mkdir" "$arquivo"; } || grep -qiE "passo 0\.3" "$arquivo"; then
        pass "$agente D9: Passo 0.3 — travas com mkdir em .delta-11/locks/"
    else
        fail "$agente D9: não mostra o Passo 0.3 (travas mkdir .delta-11/locks/...lock)"
    fi
    expect_match "$arquivo" "logs/autocritica" "$agente D9: autocrítica em logs/autocritica/"
    expect_match "$arquivo" "build-validator" "$agente D9: roda o build-validator"
    expect_match "$arquivo" "contract-tester" "$agente D9: roda o contract-tester"

    # D6 — fatias do project-core
    if [[ "$LEEM_FATIAS" == *" $agente "* ]]; then
        expect_match "$arquivo" "project-core/(banco|contratos|visual|decisoes-tecnicas)\.md" \
            "$agente D6: lê as fatias em memoria/project-core/"
        expect_no_instruction "$agente D6: não manda ler o project-core.md inteiro" \
            "(leia|ler|consult(e|ar)|abra|abrir)[^.]{0,40}project-core\.md" "$arquivo"
    fi

    # D8 — produto × história
    expect_match "$arquivo" "($agente|\[NOME\]|\[AGENTE\])-produto\.md" "$agente D8: escreve o -produto.md"
    expect_match "$arquivo" "($agente|\[NOME\]|\[AGENTE\])-historia\.md" "$agente D8: escreve o -historia.md"
    expect_no_instruction "$agente D8: nenhuma instrução usa o [NOME]-estado.md (legado)" \
        "($agente|\[NOME\]|\[AGENTE\])-estado\.md" "$arquivo"

    # D10 — kanban é só do CRONOS
    expect_no_instruction "$agente D10: não escreve no kanban (só o CRONOS escreve)" \
        "(atualiz|escrev|grav|mov|adicion|marqu|edit|registr)[a-z]*[^.]{0,50}kanban" "$arquivo"

    # D16 — fases que o executor precisa conhecer
    for fase in "3\.5" "4\.5" "7([^.0-9]|$)"; do
        if grep -qE "(Fase|FASE|F) ?$fase" "$arquivo"; then
            pass "$agente D16: conhece a Fase ${fase%%(*}"
        else
            fail "$agente D16: não menciona a Fase ${fase%%(*}"
        fi
    done
done

finish_test "rotina única dos executores (v6.3)"
