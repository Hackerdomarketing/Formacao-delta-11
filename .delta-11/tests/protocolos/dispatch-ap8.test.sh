#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#8 — disparar.sh (AppleScript) não volta
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (D3: zero copiar-e-colar, zero script manual de disparo):
#   1. disparar.sh não existe na raiz. Se existir, não pode ter AppleScript
#      (osascript / tell application "Terminal").            [C-125]
#   2. Nenhum documento recomenda rodar ./disparar.sh.
# Caminho certo: a RAIZ é a pasta que contém .delta-11/ (C-124).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DISPARAR="$REPO_ROOT/disparar.sh"
CLAUDE="$REPO_ROOT/CLAUDE.md"

if [ ! -f "$DISPARAR" ]; then
    pass "disparar.sh não existe em $(basename "$REPO_ROOT")/ (AppleScript legado removido)"
elif grep -qE 'osascript|tell application "Terminal"' "$DISPARAR"; then
    fail "disparar.sh existe e ainda tem AppleScript ativo"
else
    pass "disparar.sh existe mas não tem AppleScript"
fi

expect_no_instruction "nenhum documento manda rodar ./disparar.sh" \
    '(rode|rodar|execute|executar|bash|sh)[[:space:]]+(o script )?`?(\./)?disparar\.sh' "$CLAUDE" "$DELTA_DIR/operativos/CRONOS.md" "$DELTA_DIR/operativos/ATLAS.md"

finish_test "AP#8 — AppleScript legado removido"
