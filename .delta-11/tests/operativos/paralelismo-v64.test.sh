#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do paralelismo da v6.4 — Velocidade (V1 a V8)
# ════════════════════════════════════════════════════════════════
# Motivo: no salvahacks (14/10) 38% do tempo ativo ficou sem nenhum
# executor trabalhando, com média de 0,99 agente por vez. As causas
# estavam no texto do CRONOS. Este teste impede que elas voltem.
#
# Conceitos conferidos no CRONOS.md e no CLAUDE.md:
#   V1  Nenhum conta-gotas: nada de "AGUARDE" entre lançamentos, nada de
#       "máximo 3"; a onda inteira sai na MESMA mensagem e a fila anda
#       por vaga.
#   V2  `paralelo_max` padrão 5 (texto e .config-limites.json).
#   V3  Brief grande NÃO vira "ondas em série": vira tarefas paralelas.
#   V4  `brief_max_tokens` = 4.000 (texto e .config-limites.json).
#   V6  SHIELD revisa por ONDA (um por onda ou um por zona), não por tarefa.
#   V7  Pipeline de ondas: a onda N+1 roda enquanto o SHIELD revisa a N.
#   V8  Revisores (fresh-reviewer, cold-start-tester, qa-ui-tandem) com
#       `run_in_background: true`; nenhum `run_in_background: false`.
#   V12 O CRONOS roda o medir-paralelismo.py ao fechar cada fase.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CRONOS="$DELTA_DIR/operativos/CRONOS.md"
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"
LIMITES="$DELTA_DIR/.config-limites.json"

require_file "$CRONOS" ".delta-11/operativos/CRONOS.md" || finish_test "paralelismo v6.4"
require_file "$CLAUDE_MD" "CLAUDE.md" || finish_test "paralelismo v6.4"

echo "[V1] nenhum conta-gotas"
# "AGUARDE" em maiúsculas era o passo do conta-gotas ("lance 3, AGUARDE 1").
expect_no_match "$CRONOS" "AGUARDE" "CRONOS.md: nenhum 'AGUARDE' entre lançamentos"
# grep -i não serve aqui: "aguarde liberação" (trava) é legítimo no CLAUDE.md.
if grep -nE "AGUARDE" "$CLAUDE_MD" >/dev/null; then
    fail "CLAUDE.md: ainda tem 'AGUARDE' entre lançamentos"
else
    pass "CLAUDE.md: nenhum 'AGUARDE' entre lançamentos"
fi
expect_no_instruction "nenhum limite fixo de 3 agentes paralelos" \
    "(m(á|a)ximo|at(é|e)|limite de) 3 (agentes|paralel|simult|em paralelo|por vez)|3 simult(â|a)neos|m(á|a)x 3 agentes|lance os (3|tr(ê|e)s) primeiros" \
    "$CRONOS" "$CLAUDE_MD"
expect_match "$CRONOS" "MESMA mensagem" "CRONOS.md: a onda inteira sai na MESMA mensagem"
expect_match "$CLAUDE_MD" "MESMA mensagem" "CLAUDE.md: a onda inteira sai na MESMA mensagem"
expect_match "$CRONOS" "fila por vaga|fila anda por vaga" "CRONOS.md: fila por vaga (vaga livre = próximo da fila)"
expect_match "$CRONOS" "Nunca espere uma rodada inteira" "CRONOS.md: nunca espera a rodada inteira terminar"

echo "[V2/V4] limites"
if python3 - "$LIMITES" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
sys.exit(0 if d.get("paralelo_max") == 5 and d.get("brief_max_tokens") == 4000 else 1)
PY
then pass ".config-limites.json: paralelo_max 5 e brief_max_tokens 4000"
else fail ".config-limites.json: paralelo_max deveria ser 5 e brief_max_tokens 4000"; fi

for arquivo in "$CRONOS" "$CLAUDE_MD"; do
    nome="$(basename "$arquivo")"
    expect_match "$arquivo" "paralelo_max[^.]{0,40}(padr(ã|a)o|vale) 5" "$nome: paralelo_max padrão 5"
    expect_no_match "$arquivo" "paralelo_max[^.]{0,40}(padr(ã|a)o|vale) 3|padr(ã|a)o 3[^.]{0,20}(agentes|simult)" \
        "$nome: nenhum paralelo_max padrão 3"
    expect_no_match "$arquivo" "LIMITE DURO DE 2|brief[^.]{0,60}2\.?000|2\.?000 tokens[^.]{0,40}(brief|executor|despacho)" \
        "$nome: nenhum limite de brief de 2.000 tokens"
done
expect_match "$CRONOS" "4\.?000" "CRONOS.md: brief_max_tokens 4.000"
if python3 - "$CLAUDE_MD" "$LIMITES" <<'PY'
import json, re, sys
texto = open(sys.argv[1], encoding="utf-8").read()
config = json.load(open(sys.argv[2], encoding="utf-8"))
achado = re.search(r'`(\{"brief_max_tokens"[^`]*\})`', texto)
sys.exit(0 if achado and json.loads(achado.group(1)) == config else 1)
PY
then pass "CLAUDE.md documenta o mesmo .config-limites.json do disco"
else fail "CLAUDE.md documenta um .config-limites.json diferente do disco"; fi

echo "[V3] brief grande vira tarefas paralelas"
expect_no_instruction "nenhuma 'onda em série' por tamanho de brief" \
    "ondas? em s(é|e)rie|quebre a onda em mais ondas|vira 2-3 ondas" "$CRONOS" "$CLAUDE_MD"
granularizacao=$(awk '/PRINC(Í|I)PIO DA GRANULARIZA/{achou=1} achou{print} /^\*\*Isentos do limite/{if(achou) exit}' "$CRONOS")
if grep -qiE "PARALELAS|AO MESMO TEMPO" <<< "$granularizacao" && grep -qiE "irm(ã|a)o|irm(ã|a)s" <<< "$granularizacao"; then
    pass "CRONOS.md: granularização divide em sub-tarefas irmãs que rodam ao mesmo tempo"
else
    fail "CRONOS.md: a granularização não diz que a divisão é em tarefas paralelas (irmãs)"
fi

echo "[V6] SHIELD revisa por onda"
expect_match "$CRONOS" "shield-onda-" "CRONOS.md: SHIELD nomeado por onda (shield-onda-[N])"
expect_match "$CRONOS" "UM SHIELD[^.]{0,80}onda" "CRONOS.md: um SHIELD por onda"
expect_match "$CRONOS" "um por zona" "CRONOS.md: onda grande = um SHIELD por zona, em paralelo"
expect_match "$CLAUDE_MD" "UM SHIELD[^.]{0,80}onda" "CLAUDE.md: um SHIELD por onda"
expect_no_match "$CRONOS" "Mova para REVIS(Ã|A)O e dispare o SHIELD|shield-\[T-XXX\]" \
    "CRONOS.md: o Passo 3.8 não dispara um SHIELD por tarefa"
expect_no_match "$CLAUDE_MD" "move a tarefa para REVIS(Ã|A)O e dispara o SHIELD \(sem worktree\)\. Voc|shield-revisao-t-xxx" \
    "CLAUDE.md: o Passo 3.8 não dispara um SHIELD por tarefa"

echo "[V7] pipeline de ondas"
expect_match "$CRONOS" "\\*\\*Pipeline:\\*\\*|pipeline[^.]{0,6}(—|-|\\()[^.]{0,6}V7" "CRONOS.md: regra do pipeline de ondas (V7)"
expect_match "$CRONOS" "onda N\+1[^.]{0,80}(n(ã|a)o dependem|NÃO dependem)" \
    "CRONOS.md: a onda N+1 roda nas tarefas que não dependem da onda N"
expect_match "$CLAUDE_MD" "onda seguinte[^.]{0,60}(n(ã|a)o dependem|j(á|a) trabalha)|(n(ã|a)o dependem|j(á|a) trabalha)[^.]{0,60}onda seguinte" \
    "CLAUDE.md: a onda seguinte trabalha enquanto o SHIELD revisa"

echo "[V8] revisores em segundo plano"
relatorio=$(python3 - "$CRONOS" "$CLAUDE_MD" <<'PY'
import re, sys
revisores = ("fresh", "cold", "qa-ui-tandem", "selo experiencial")
achados = {nome: 0 for nome in revisores}
for caminho in sys.argv[1:]:
    texto = open(caminho, encoding="utf-8").read()
    nome_arquivo = caminho.rsplit("/", 1)[-1]
    for bloco in re.finditer(r"Agent\((.*?)\n\s*\)", texto, re.S):
        corpo = bloco.group(1)
        linha = texto.count("\n", 0, bloco.start()) + 1
        if re.search(r"run_in_background:\s*false", corpo):
            print(f"FORA: {nome_arquivo}:{linha}: Agent(...) com run_in_background: false")
        rotulo = corpo.lower()
        for revisor in revisores:
            if revisor in rotulo:
                achados[revisor] += 1
                if not re.search(r"run_in_background:\s*true", corpo):
                    print(f"FORA: {nome_arquivo}:{linha}: revisor '{revisor}' sem run_in_background: true")
for revisor in ("fresh", "cold", "qa-ui-tandem"):
    if achados[revisor] == 0 and not (revisor == "qa-ui-tandem" and achados["selo experiencial"]):
        print(f"FORA: nenhum bloco Agent(...) do revisor '{revisor}'")
PY
)
if [ -z "$relatorio" ]; then
    pass "revisores (fresh-reviewer, cold-start-tester, qa-ui-tandem) com run_in_background: true; nenhum em primeiro plano"
else
    fail "revisor em primeiro plano ou sem bloco de disparo:"
    echo "$relatorio" | sed 's/^/            /'
fi
expect_match "$CRONOS" "revisores de fase JUNTOS" "CRONOS.md: revisores de fase disparados juntos"

echo "[V12] medição ao fechar a fase"
expect_match "$CRONOS" "medir-paralelismo\\.py" "CRONOS.md: mede o paralelismo ao fechar cada fase"

finish_test "paralelismo v6.4 — onda inteira, fila por vaga, SHIELD por onda e pipeline"
