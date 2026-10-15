#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da v6.4 — ciclo leve (V9) e Fase 7 sem travar ciclos (V10)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   V9   fluxo, fase-ritmo e fase-consciencia explicam o Ciclo 1 completo e os
#        Ciclos 2+ leves (checklist de 1 página com o nome certo), o documento
#        completo para a área que o ciclo MEXE, de onde vem o número do ciclo, e
#        que o SHIELD confere o que o vigia não julga. Fases 2.3 e 2.4 só para
#        o que é novo.
#   V10  fluxo e fase-descanso: as 2 semanas correm em paralelo com o ciclo
#        seguinte; o vigia só cobra o teste supremo no selo final.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

P="$DELTA_DIR/protocolos"
FLUXO="$P/fluxo-zero-ao-lancamento.md"
RITMO="$P/fase-ritmo.md"
CONSC="$P/fase-consciencia.md"
DESCANSO="$P/fase-descanso.md"
METODO="$DELTA_DIR/conhecimento/metodologia-genesis-camadas.md"

for doc in "$FLUXO" "$RITMO" "$CONSC" "$METODO"; do
    nome="$(basename "$doc")"
    expect_match "$doc" "Ciclo 1" "V9: $nome fala do Ciclo 1 (completo)"
    expect_match "$doc" "Ciclo 2 em diante|Ciclos 2 a 7" "V9: $nome fala dos Ciclos 2+ (leves)"
    expect_match "$doc" "MEXE" "V9: $nome — área que o ciclo MEXE ganha documento completo"
done
expect_match "$FLUXO" "ritmo-temporal-checklist-ciclo-N\.md" "V9: fluxo — nome do checklist da Fase 3.5"
expect_match "$FLUXO" "consciencia-checklist-ciclo-N\.md" "V9: fluxo — nome do checklist da Fase 4.5"
expect_match "$FLUXO" "sem tecnologia nova" "V9: fluxo — Fase 2.3 só para tecnologia nova"
expect_match "$FLUXO" "sem ferramenta nova" "V9: fluxo — Fase 2.4 só para ferramenta nova"
expect_match "$FLUXO" "\*\*Ciclo atual:\*\*" "V9: fluxo — número do ciclo no kanban"
expect_match "$RITMO" "ritmo-temporal-checklist-ciclo-N\.md" "V9: fase-ritmo — nome do checklist"
expect_match "$RITMO" "ritmo-temporal-checklist-template\.md" "V9: fase-ritmo — aponta o modelo do checklist"
expect_match "$RITMO" "NÃO consegue conferir[^.]*" "V9: fase-ritmo — limite do vigia declarado"
expect_match "$RITMO" "Quem confere isso é o \*\*SHIELD\*\*" "V9: fase-ritmo — o SHIELD confere o que o vigia não julga"
expect_match "$CONSC" "consciencia-checklist-ciclo-N\.md" "V9: fase-consciencia — nome do checklist"
expect_match "$CONSC" "consciencia-checklist-template\.md" "V9: fase-consciencia — aponta o modelo do checklist"
expect_match "$CONSC" "Quem confere é o \*\*SHIELD\*\*" "V9: fase-consciencia — o SHIELD confere o que o vigia não julga"

expect_match "$FLUXO" "EM PARALELO com o ciclo seguinte|correm EM PARALELO" "V10: fluxo — 2 semanas em paralelo com o ciclo seguinte"
expect_match "$FLUXO" "Fase 7 entregue" "V10: fluxo — marco 'Fase 7 entregue' abre o ciclo seguinte"
expect_match "$DESCANSO" "n(ã|a)o trava o ciclo seguinte" "V10: fase-descanso — Fase 7 não trava o ciclo seguinte"
expect_match "$DESCANSO" "em paralelo" "V10: fase-descanso — observação em paralelo"
expect_match "$DESCANSO" "SÓ no selo final" "V10: fase-descanso — vigia só cobra o teste supremo no selo final"
expect_no_match "$DESCANSO" "(1|uma) semana[^s]" "D16 continua: nada de 1 semana"

finish_test "v6.4 — ciclo leve (V9) e Fase 7 em paralelo (V10)"
