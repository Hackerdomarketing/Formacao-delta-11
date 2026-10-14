#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#4 — CRONOS sem perguntas de aprovação (D4)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. CRONOS.md não tem seção de "checkpoints de aprovação com o comandante".
#   2. D4: CRONOS.md, CLAUDE.md e os protocolos não perguntam "Posso
#      prosseguir?" nem mandam "aguardar aprovação" (frases do tipo
#      "Não há pergunta 'Posso prosseguir?'" são permitidas).
#   3. CRONOS.md documenta que segue sem pausar; a única parada de fase é
#      o Selo (e a fronteira entre fases no modo manual).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CRONOS="$DELTA_DIR/operativos/CRONOS.md"
require_file "$CRONOS" ".delta-11/operativos/CRONOS.md" || finish_test "AP#4"

expect_no_instruction "CRONOS.md não tem 'checkpoints de aprovação com o comandante'" \
    "^#+ .*CHECKPOINTS? DE APROVA(ÇÃO|CAO)" "$CRONOS"

ARQUIVOS=("$CRONOS" "$REPO_ROOT/CLAUDE.md")
for arquivo in "$DELTA_DIR/protocolos/"*.md; do ARQUIVOS+=("$arquivo"); done
expect_no_instruction "D4: ninguém pergunta \"Posso prosseguir?\" nem manda aguardar aprovação" \
    "posso prosseguir|aguarde (a |o )?(aprova|ok do comandante)|aguardar (a )?aprova(ção|cao) do comandante" "${ARQUIVOS[@]}"

expect_match "$CRONOS" "gate humano|sem pausar|sem esperar|(prossegue|segue|avan(ç|c)a) automaticamente|auto-?avan(ç|c)a" \
    "CRONOS.md documenta que segue sem pausar"

finish_test "AP#4 — zero perguntas de aprovação bloqueantes"
