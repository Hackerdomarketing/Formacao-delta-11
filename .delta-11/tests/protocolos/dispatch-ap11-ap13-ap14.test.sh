#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#11 + AP#13 + AP#14 — vigilante, selo e "rode manualmente"
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (D3, D4):
#   AP#11  vigilante.sh não manda ninguém rodar ./disparar.sh.
#   AP#13  O selo experiencial não manda o comandante operar o produto: é o
#          sub-agente com o Tandem Browser que opera; o humano só lê.
#   AP#14  ATLAS e SHIELD não dizem "rode manualmente" (o agente roda com a
#          ferramenta Bash).
# Todo arquivo conferido precisa existir (checagem negativa sem arquivo = FALHA).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

VIGILANTE="$REPO_ROOT/vigilante.sh"
SELO="$DELTA_DIR/templates/selo-experiencial-template.md"
SHIELD="$DELTA_DIR/operativos/SHIELD.md"
ATLAS="$DELTA_DIR/operativos/ATLAS.md"

expect_no_match "$VIGILANTE" "rode \./disparar\.sh" "AP#11: vigilante.sh não manda rodar ./disparar.sh"

expect_no_instruction "AP#13: o selo não manda o comandante operar o produto" \
    "comandante (opera|operar|testa|navega)[^.]{0,30}produto" "$SELO"
expect_match "$SELO" "Tandem" "AP#13: o selo usa o Tandem Browser (sub-agente opera, humano lê)"

expect_no_instruction "AP#14: SHIELD.md e ATLAS.md não dizem \"rode manualmente\"" \
    "rode manualmente|rodar manualmente" "$SHIELD" "$ATLAS"

finish_test "AP#11 + AP#13 + AP#14"
