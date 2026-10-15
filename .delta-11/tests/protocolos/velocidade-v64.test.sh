#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da v6.4 (Velocidade) nos protocolos e modelos — V1 a V8 e V11
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   V1/V2  nenhum protocolo ou modelo manda disparar "no máximo 3" / "até 3"
#          agentes; a onda inteira sai de uma vez (paralelo_max, padrão 5),
#          com fila por vaga.
#   V3/V4  tarefa grande vira sub-tarefas PARALELAS; brief padrão 4000 (não 2000).
#   V5     só fica em sequência: mesmo arquivo ou dependência declarada.
#   V6     build-validator e contract-tester juntos; SHIELD por onda,
#          veredito por tarefa.
#   V7     pipeline de ondas; merge só das tarefas APROVADAS.
#   V8     revisores de fase juntos, em segundo plano (nenhum em primeiro plano).
#   V11    o SHIELD não reprova por redação de documento.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

P="$DELTA_DIR/protocolos"
T="$DELTA_DIR/templates"
COMUNICACAO="$P/comunicacao.md"
SUB="$P/sub-agentes.md"
MERGE="$P/merge-guiado-contratos.md"
CICLO="$P/ciclo-interno-7d.md"
FLUXO="$P/fluxo-zero-ao-lancamento.md"

TODOS=()
for arquivo in "$P/"*.md "$T/"*.md; do TODOS+=("$arquivo"); done

# V1/V2 — nada de conta-gotas de 3
expect_no_instruction "V2: nenhum texto limita a 3 agentes/sub-agentes/executores ao mesmo tempo" \
    "(m(á|a)ximo|at(é|e)) 3 (agentes|sub-agentes|executores|em paralelo|simult(â|a)neos|por vez)|no m(á|a)ximo 3 agentes" "${TODOS[@]}"
expect_no_instruction "V4: nenhum texto fixa o brief em 2.000 tokens" "2[.]?000 tokens" "${TODOS[@]}"
expect_no_instruction "V8: nenhum disparo de sub-agente/revisor em primeiro plano" "run_in_background: false" "${TODOS[@]}"
expect_no_instruction "V8: nenhuma cadeia em série de revisores (fresh → cold-start → qa-ui)" \
    "fresh.reviewer[^|]{0,6}(→|->)[^|]{0,6}cold.start" "${TODOS[@]}"

expect_match "$COMUNICACAO" "onda inteira" "V1: comunicacao.md — a onda inteira sai de uma vez"
expect_match "$COMUNICACAO" "MESMA mensagem" "V1: comunicacao.md — várias chamadas Agent na mesma mensagem"
expect_match "$COMUNICACAO" "fila (anda )?por vaga|fila por vaga" "V1: comunicacao.md — fila por vaga"
expect_match "$COMUNICACAO" "paralelo_max.{0,20}padr(ã|a)o 5" "V2: comunicacao.md — paralelo_max padrão 5"
expect_match "$COMUNICACAO" "retorno curto|payload" "V1: CRONOS lê só o retorno curto"
expect_match "$COMUNICACAO" "MESMO arquivo" "V5: só fica em sequência quem edita o mesmo arquivo"
expect_match "$COMUNICACAO" "depend(ê|e)ncia declarada" "V5: ou dependência declarada"
expect_match "$COMUNICACAO" "UM SHIELD que revisa a onda inteira|SHIELD (revisa|para) a onda" "V6: um SHIELD por onda"
expect_match "$COMUNICACAO" "POR TAREFA|por tarefa" "V6: veredito por tarefa (D33)"
expect_match "$COMUNICACAO" "[Pp]ipeline" "V7: pipeline de ondas"
expect_match "$COMUNICACAO" "reda(ç|c)(ã|a)o" "V11: comunicacao.md — redação não reprova"

expect_match "$SUB" "JUNTOS" "V8: sub-agentes.md — revisores de fase juntos"
expect_match "$SUB" "run_in_background: true" "V8: sub-agentes.md — disparo em segundo plano"
expect_match "$SUB" "junto com o build-validator" "V6: contract-tester junto com o build-validator"
expect_no_instruction "V6: contract-tester não espera mais o build-validator passar" \
    "(ap(ó|o)s|depois que) o build-validator( passar| passou)?" "$SUB" "$P/regras-inviolaveis.md"

expect_match "$MERGE" "merge por ONDA|uma vez por onda" "V7: merge-guiado — merge por onda"
expect_match "$MERGE" "APROVADA" "V7: merge-guiado — só tarefas APROVADAS"
expect_match "$MERGE" "REPROVADA[^.]*FORA|fica FORA" "V7: branch reprovada fica fora sem travar as outras"

expect_match "$CICLO" "paralela REAL|execu(ç|c)(ã|a)o paralela real" "V1: ciclo-interno-7d — sub-etapa 3 = execução paralela real"
expect_match "$CICLO" "paralelo_max.{0,20}padr(ã|a)o 5" "V2: ciclo-interno-7d — paralelo_max padrão 5"
expect_match "$CICLO" "conta-gotas" "V1: ciclo-interno-7d — conta-gotas é erro comum"

expect_match "$FLUXO" "[Pp]ipeline de ondas" "V7: fluxo — pipeline de ondas na Fase 4"
expect_match "$FLUXO" "sub-tarefas[^.]*AO MESMO TEMPO" "V3: fluxo — tarefa grande vira sub-tarefas paralelas"
expect_match "$FLUXO" "padr(ã|a)o 4000" "V4: fluxo — brief_max_tokens padrão 4000"
expect_match "$FLUXO" "reda(ç|c)(ã|a)o em documento[^.]*NUNCA reprova|nunca reprova" "V11: fluxo — redação nunca reprova"
expect_match "$P/correcao-de-erros.md" "NUNCA reprova" "V11: correcao-de-erros — redação nunca reprova"
expect_match "$P/regras-inviolaveis.md" "nunca a reda(ç|c)(ã|a)o" "V11: regras-inviolaveis (Regra 5)"

expect_match "$T/mini-plano-agente-template.md" "Sub-tarefa irm(ã|a) de" "V3: mini-plano tem o campo de sub-tarefa irmã"
expect_match "$T/cronos-sequenciamento-template.md" "pipeline" "V7: sequenciamento mostra a onda em pipeline"

finish_test "v6.4 Velocidade nos protocolos e modelos (V1–V8, V11)"
