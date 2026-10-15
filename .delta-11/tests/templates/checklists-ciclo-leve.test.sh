#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste dos modelos de checklist do ciclo leve (v6.4 — V9)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. Os dois modelos existem, dizem onde salvar e apontam o protocolo.
#   2. Têm os 10 (ritmo) e os 5 (consciência) itens numerados, com o slug
#      que os vigias usam.
#   3. Dizem que o SHIELD confere o que o vigia não julga.
#   4. Cabem em 1 página: o bloco para copiar tem no máximo 25 linhas.
#   5. O exemplo preenchido PASSA no vigia e o modelo em branco NÃO passa
#      (roda o cycle_checklist de verdade, num projeto temporário).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

RITMO="$DELTA_DIR/templates/ritmo-temporal-checklist-template.md"
CONSC="$DELTA_DIR/templates/consciencia-checklist-template.md"

expect_match "$RITMO" "ritmo-temporal-checklist-ciclo-N\.md" "ritmo: diz onde salvar"
expect_match "$RITMO" "protocolos/fase-ritmo\.md" "ritmo: aponta o protocolo"
expect_match "$RITMO" "SHIELD que confere|SHIELD[^.]*confere" "ritmo: o SHIELD confere o que o vigia não julga"
for item in "01 | sistema-eventos" "02 | filas" "03 | jobs-agendados" "04 | cache-ttl" "05 | timeouts" \
            "06 | retries" "07 | circuit-breakers" "08 | ci-cd-staging" "09 | observabilidade" "10 | sub-contraposicao"; do
    expect_match "$RITMO" "\| ${item} \|" "ritmo: item $item"
done
expect_match "$CONSC" "consciencia-checklist-ciclo-N\.md" "consciência: diz onde salvar"
expect_match "$CONSC" "protocolos/fase-consciencia\.md" "consciência: aponta o protocolo"
expect_match "$CONSC" "SHIELD que confere|SHIELD[^.]*confere" "consciência: o SHIELD confere o que o vigia não julga"
for item in "01 | auditoria-imutavel" "02 | rate-limiting" "03 | motor-regras" "04 | lgpd" "05 | fluxos-aprovacao"; do
    expect_match "$CONSC" "\| ${item} \|" "consciência: item $item"
done

PROJETO="$(mktemp -d "${TMPDIR:-/tmp}/delta11-teste-XXXXXX")"
trap '[ -n "$PROJETO" ] && rm -rf "$PROJETO"' EXIT
mkdir -p "$PROJETO/.delta-11/memoria/decisoes"
RESULTADO="$(cd "$PROJETO" && CLAUDE_PROJECT_DIR="$PROJETO" python3 -B - "$DELTA_DIR/hooks" "$RITMO" "$CONSC" "$PROJETO" <<'PY'
import os, re, sys
hooks, ritmo, consc, projeto = sys.argv[1:5]
sys.path.insert(0, hooks)
import _comum

def blocos(caminho):
    return re.findall(r"```markdown\n(.*?)```", open(caminho, encoding="utf-8").read(), re.S)

dec = os.path.join(projeto, ".delta-11", "memoria", "decisoes")
R = {1: "sistema-eventos", 2: "filas", 3: "jobs-agendados", 4: "cache-ttl", 5: "timeouts",
     6: "retries", 7: "circuit-breakers", 8: "ci-cd-staging", 9: "observabilidade", 10: "sub-contraposicao"}
C = {1: "auditoria-imutavel", 2: "rate-limiting", 3: "motor-regras", 4: "lgpd", 5: "fluxos-aprovacao"}
r, c = blocos(ritmo), blocos(consc)
print("linhas-ritmo", len(r[0].strip().splitlines()))
print("linhas-consc", len(c[0].strip().splitlines()))
open(os.path.join(dec, "2026-11-20-ritmo-temporal-02-filas-devolucoes.md"), "w").write("x")
casos = [("ritmo-temporal", 3, r[1], R, "exemplo-ritmo"), ("ritmo-temporal", 4, r[0], R, "branco-ritmo"),
         ("consciencia", 2, c[1], C, "exemplo-consc"), ("consciencia", 5, c[0], C, "branco-consc")]
for prefixo, ciclo, texto, itens, rotulo in casos:
    open(os.path.join(dec, f"2026-11-20-{prefixo}-checklist-ciclo-{ciclo}.md"), "w").write(texto)
    nome, pendencias = _comum.cycle_checklist(prefixo, ciclo, itens)
    print(rotulo, "achado" if nome else "ausente", len(pendencias))
PY
)"
confere() { if grep -qx -- "$1" <<< "$RESULTADO"; then pass "$2"; else fail "$2 — saída: $(tr '\n' ';' <<< "$RESULTADO")"; fi; }
confere "exemplo-ritmo achado 0" "o exemplo do checklist de ritmo PASSA no vigia"
confere "branco-ritmo achado 10" "o modelo de ritmo em branco NÃO passa (10 itens sem resposta)"
confere "exemplo-consc achado 0" "o exemplo do checklist de consciência PASSA no vigia"
confere "branco-consc achado 5" "o modelo de consciência em branco NÃO passa (5 itens sem resposta)"
for rotulo in linhas-ritmo linhas-consc; do
    linhas="$(grep "^$rotulo " <<< "$RESULTADO" | cut -d' ' -f2)"
    if [ -n "$linhas" ] && [ "$linhas" -le 25 ]; then pass "$rotulo: cabe em 1 página ($linhas linhas)"; else fail "$rotulo: passa de 25 linhas ($linhas)"; fi
done

finish_test "modelos de checklist do ciclo leve (V9)"
