#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#5 — executores pedem a revisão do SHIELD ao CRONOS
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos nos 7 executores (VAULT, BACK, ENGINE, FRONT, PIXEL,
# FORM, SCOUT — D11):
#   1. Não mandam gerar prompt do SHIELD nem criar arquivo .txt de pedido de
#      revisão (D9 3.8: "NÃO criar .txt").
#   2. Avisam o CRONOS por SendMessage (D5, D9 3.8).
#   3. Nenhum executor dispara outro agente (D5) — não há bloco Agent(...).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

EXECUTORES=("VAULT" "BACK" "ENGINE" "FRONT" "PIXEL" "FORM" "SCOUT")

for agente in "${EXECUTORES[@]}"; do
    arquivo="$DELTA_DIR/operativos/$agente.md"
    require_file "$arquivo" ".delta-11/operativos/$agente.md" || continue

    expect_no_instruction "$agente: não gera prompt/arquivo .txt para o SHIELD" \
        "gere (o )?prompt do SHIELD|janela-SHIELD|(revisao|revis(ã|a)o|pedido)[a-z-]*SHIELD[a-z-]*\.txt|SHIELD[a-z-]*(revisao|pedido)[a-z-]*\.txt" "$arquivo"

    if grep -qF "SendMessage" "$arquivo" && grep -qE "CRONOS" "$arquivo"; then
        pass "$agente: avisa o CRONOS por SendMessage"
    else
        fail "$agente: não avisa o CRONOS por SendMessage"
    fi

    if grep -qE "^[[:space:]]*Agent\(" "$arquivo"; then
        fail "$agente: tem bloco Agent(...) — executor não dispara agente (D5)"
    else
        pass "$agente: não dispara outro agente"
    fi
done

finish_test "AP#5 — revisão do SHIELD pedida ao CRONOS por SendMessage"
