#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#3 — o ATLAS não pede ao humano para colar prompt
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (D3, D5):
#   1. ATLAS.md não manda o comandante copiar/colar prompt nem abrir janela.
#   2. ATLAS.md dispara o CRONOS automaticamente pelo Agent tool.
#   3. D5: o ATLAS dispara SOMENTE o CRONOS — todo bloco Agent(...) do
#      ATLAS.md é do CRONOS (o SHIELD, por exemplo, é pedido ao CRONOS).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

ATLAS="$DELTA_DIR/operativos/ATLAS.md"
require_file "$ATLAS" ".delta-11/operativos/ATLAS.md" || finish_test "AP#3"

expect_no_instruction "ATLAS.md não manda o comandante copiar/colar prompt" \
    "cop(i|ia|iar|ie)[a-z]*[[:space:]]+(e|ou)[[:space:]]+col|comandante col(a|aria|e)|(^|[^a-z])col(e|ar)[[:space:]]+(o[[:space:]]+)?(texto|bloco|prompt)" "$ATLAS"
expect_match "$ATLAS" "Agent tool|Agent\(" "ATLAS.md usa o Agent tool para disparar"
expect_match "$ATLAS" "dispar(e|a|ar)[^.]{0,30}CRONOS[^.]{0,40}automaticamente|CRONOS[^.]{0,40}automaticamente via Agent|disparo[^.]{0,20}aut(ô|o)nomo" \
    "ATLAS.md dispara o CRONOS automaticamente"

agent_report=$(python3 - "$ATLAS" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
blocks = 0
for match in re.finditer(r"Agent\((.*?)\n\s*\)", text, re.S):
    body = match.group(1)
    blocks += 1
    name = re.search(r'name:\s*"([^"]+)"', body)
    description = re.search(r'description:\s*"([^"]+)"', body)
    label = (name.group(1) if name else "") + " " + (description.group(1) if description else "")
    if "cronos" not in label.lower():
        line = text.count("\n", 0, match.start()) + 1
        print(f"ATLAS.md:{line}: Agent(...) que não é do CRONOS: {label.strip()}")
print(f"BLOCOS:{blocks}")
PY
)
fora_da_regra=$(echo "$agent_report" | grep -v '^BLOCOS:' || true)
if [ -z "$fora_da_regra" ]; then
    pass "D5: o ATLAS só dispara o CRONOS ($(echo "$agent_report" | grep '^BLOCOS:'))"
else
    fail "D5: o ATLAS dispara outro agente além do CRONOS:"
    echo "$fora_da_regra" | sed 's/^/            /'
fi

finish_test "AP#3 — ATLAS dispara só o CRONOS, sem copiar-e-colar"
