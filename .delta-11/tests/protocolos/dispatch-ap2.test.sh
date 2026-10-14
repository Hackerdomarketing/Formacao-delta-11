#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#2 — falha do Agent tool: tentar de novo antes do humano
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (D3, D4):
#   1. O primeiro recurso, quando o disparo falha, NÃO é mandar mensagem ao
#      comandante.
#   2. "Fluxo manual" não aparece como caminho principal (só como alerta).
#   3. O CLAUDE.md documenta novas tentativas automáticas (3) antes de
#      envolver o comandante.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CLAUDE="$REPO_ROOT/CLAUDE.md"

expect_no_match "$CLAUDE" "Fallback 1[^|]{0,5}(Mensagem|Avis[ae]r?|Pedir)[^|]{0,10}(ao )?comandante" \
    "o primeiro recurso de falha NÃO é falar com o comandante"

expect_no_instruction "\"fluxo manual\" não é o caminho principal" \
    "fluxo manual[^.]{0,30}(sempre funciona|caminho (principal|padr))" "$CLAUDE"

expect_match "$CLAUDE" "retry[^.]{0,40}3|3 (novas )?tentativas|tentar[^.]{0,20}3 vezes|Retry [123]|cadeia de retry" \
    "CLAUDE.md documenta novas tentativas automáticas antes de envolver o comandante"

finish_test "AP#2 — novas tentativas antes de envolver o comandante"
