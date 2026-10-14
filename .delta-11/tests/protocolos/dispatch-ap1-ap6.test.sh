#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#1 + AP#6 — CRONOS se auto-retoma (v6.3)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos (decisões canônicas D2, D3, D5):
#   1. Nenhum texto diz que só o comandante dispara o CRONOS.
#   2. Nenhum texto pede ao comandante para abrir sessão / colar prompt
#      de retomada do CRONOS.
#   3. CLAUDE.md e CRONOS.md documentam que o CRONOS se auto-retoma pelo
#      Agent tool.
#   4. D2: todo bloco Agent(...) que dispara o CRONOS usa name "cronos"
#      e NÃO usa isolation "worktree" (o CRONOS roda na pasta principal).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CLAUDE="$REPO_ROOT/CLAUDE.md"
CRONOS="$DELTA_DIR/operativos/CRONOS.md"
ATLAS="$DELTA_DIR/operativos/ATLAS.md"

# 1. Ninguém além do comandante? Errado: o CRONOS pode ser disparado pelo ATLAS e por ele mesmo.
expect_no_instruction "nenhum texto diz que só o comandante dispara o CRONOS" \
    "(só|so) o comandante (pode )?(disparar|dispara|ativa|ativar)" "$CLAUDE" "$CRONOS" "$ATLAS"

# 2. Nada de pedir ao humano para abrir sessão / colar a retomada.
expect_no_instruction "nenhum texto pede ao comandante para abrir sessão ou colar a retomada" \
    "comandante (abre|abra|abrir) (uma )?nova sess|comandante[^.]{0,40}(dispara|dispare) (o )?CRONOS|comandante[^.]{0,40}cola[^.]{0,30}(prompt|bloco)[^.]{0,30}retomada" \
    "$CLAUDE" "$CRONOS"

# 3. Auto-retomada documentada (conceito: CRONOS + disparar a si mesmo / auto-retoma).
AUTO_RETOMADA='auto-?retom|auto-?dispens|disparar (a )?si mesmo|disparar ele mesmo|dispara a si mesmo'
expect_match "$CLAUDE" "$AUTO_RETOMADA" "CLAUDE.md documenta a auto-retomada do CRONOS"
expect_match "$CRONOS" "$AUTO_RETOMADA" "CRONOS.md documenta a auto-retomada"

# 4. D2 — blocos Agent(...) do CRONOS: name "cronos" e sem worktree.
check_cronos_blocks() {
    python3 - "$@" <<'PY'
import re, sys
problems, blocks = [], 0
for path in sys.argv[1:]:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        continue
    for match in re.finditer(r"Agent\((.*?)\n\s*\)", text, re.S):
        body = match.group(1)
        name = re.search(r'name:\s*"([^"]+)"', body)
        if not name or not name.group(1).lower().startswith("cronos"):
            continue
        blocks += 1
        line = text.count("\n", 0, match.start()) + 1
        short = path.split("/")[-1]
        if name.group(1) != "cronos":
            problems.append(f'{short}:{line}: name "{name.group(1)}" (D2 exige name: "cronos")')
        if re.search(r'isolation:\s*"?worktree', body):
            problems.append(f'{short}:{line}: CRONOS disparado com isolation "worktree" (D2: sem worktree)')
print(f"BLOCOS:{blocks}")
for item in problems:
    print(item)
PY
}
cronos_report=$(check_cronos_blocks "$CLAUDE" "$CRONOS" "$ATLAS")
cronos_problems=$(echo "$cronos_report" | grep -v '^BLOCOS:' || true)
if [ -z "$cronos_problems" ]; then
    pass "D2: blocos Agent(...) do CRONOS usam name \"cronos\" e rodam sem worktree ($(echo "$cronos_report" | head -1))"
else
    fail "D2: bloco de disparo do CRONOS fora da regra:"
    echo "$cronos_problems" | sed 's/^/            /'
fi

finish_test "AP#1 + AP#6 — CRONOS autônomo (auto-retomada sem worktree)"
