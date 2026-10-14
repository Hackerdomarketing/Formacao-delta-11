#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#7 — SCOUT não entrega bloco de retomada ao humano
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (D3, D23):
#   1. SCOUT.md não manda entregar ao comandante bloco para copiar e colar.
#   2. SCOUT.md avisa o CRONOS por SendMessage.
#   3. D23: após 3 tentativas o SCOUT para e avisa o CRONOS; quem dispara
#      um NOVO SCOUT é o CRONOS ("SCOUT nunca dispara SCOUT").
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

SCOUT="$DELTA_DIR/operativos/SCOUT.md"
require_file "$SCOUT" ".delta-11/operativos/SCOUT.md" || finish_test "AP#7"

expect_no_instruction "SCOUT.md não entrega bloco de retomada para o comandante colar" \
    "entregue ao comandante[^.]{0,60}(bloco|prompt)|bloco de retomada[^.]{0,40}(copiar|colar)" "$SCOUT"

if grep -qF "SendMessage" "$SCOUT" && grep -qE "CRONOS" "$SCOUT"; then
    pass "SCOUT.md avisa o CRONOS por SendMessage"
else
    fail "SCOUT.md não avisa o CRONOS por SendMessage"
fi

expect_match "$SCOUT" "3 tentativas|tr(ê|e)s tentativas|3 falhas" "D23: SCOUT para após 3 tentativas"
expect_match "$SCOUT" "CRONOS[^.]{0,60}(novo SCOUT|dispara[^.]{0,20}SCOUT)|novo SCOUT[^.]{0,60}CRONOS|SCOUT nunca dispara SCOUT" \
    "D23: quem dispara um novo SCOUT é o CRONOS"

finish_test "AP#7 — SCOUT avisa o CRONOS (sem copiar-e-colar)"
