#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de _comum.dispatch_target (v6.4): quem é o alvo de um disparo
# ════════════════════════════════════════════════════════════════
# Antes da v6.4 a busca olhava o prompt inteiro em ordem alfabética: um
# contract-tester (cujo texto cita o build-validator) virava "build-validator".
# Ordem certa: name → subagent_type → sub-agente na description → linha
# "Sub-agente: .../<nome>.md" do prompt → "Agente: NOME" → primeiro sub-agente
# citado no resto do prompt. Também confere que a isenção de limite do
# pre-despacho continua valendo para o contract-tester com brief grande.
# ════════════════════════════════════════════════════════════════
source "$(dirname "$0")/_ajudante-hooks-python.sh" pre-despacho

alvo() {  # alvo JSON-do-tool_input → imprime o alvo
    python3 -B -c '
import json, sys
sys.path.insert(0, sys.argv[1])
import _comum
print(_comum.dispatch_target({"tool_input": json.loads(sys.argv[2])}))' "$HOOKS_DIR" "$1"
}
confere() {  # confere ESPERADO "descricao" JSON
    local veio
    veio="$(alvo "$3")"
    if [ "$veio" = "$1" ]; then ok "$2 → $veio"; else err "$2 — esperado '$1', veio '$veio'"; fi
}

confere contract-tester "description com contract-tester e prompt que cita o build-validator" \
    '{"description":"contract-tester — T-042","prompt":"Rode depois de ler o relatório do build-validator."}'
confere contract-tester "linha Sub-agente: .../contract-tester.md no prompt" \
    '{"description":"Validação T-042","prompt":"Sub-agente: .delta-11/sub-agentes/contract-tester.md\nO build-validator roda junto."}'
confere contract-tester "linha **Sub-agente:** em negrito" \
    '{"description":"Validação","prompt":"**Sub-agente:** `contract-tester`\nbuild-validator em paralelo"}'
confere contract-tester "sem pista melhor: o PRIMEIRO citado no prompt, não o primeiro do alfabeto" \
    '{"description":"Validação","prompt":"Você é o contract-tester. Não repita o build-validator."}'
confere build-validator "description do sub-agente vence a linha Agente: do prompt" \
    '{"description":"build-validator — T-1","prompt":"Agente: ENGINE"}'
confere ENGINE "name do executor vence tudo" \
    '{"name":"engine-onda-2","description":"Ativação ENGINE — onda 2","prompt":"rode o build-validator"}'
confere CRONOS "Agente: CRONOS no prompt sem sub-agente na description" \
    '{"description":"Retomada","prompt":"Agente: CRONOS\nretomar"}'
confere "" "sem pista nenhuma: vazio" '{"description":"x","prompt":"nada"}'

novo_projeto
GRANDE="$TEST_DIR/sub.txt"
python3 -c "print('Sub-agente: .delta-11/sub-agentes/contract-tester.md\nLeia o build-validator. ' + 'contexto ' * 5000)" > "$GRANDE"
espera 0 "pre-despacho: contract-tester com brief grande continua isento" \
    "$(evento tool_name=Agent tool_input.description=Validação "tool_input.prompt=@$GRANDE")"
fim
