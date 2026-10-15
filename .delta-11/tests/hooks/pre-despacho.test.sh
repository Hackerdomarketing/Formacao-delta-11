#!/usr/bin/env bash
# Teste do vigia pre-despacho.py (v6.3 — C-130, C-184, D36)
source "$(dirname "$0")/_ajudante-hooks-python.sh" pre-despacho
checagens_basicas

novo_projeto
GRANDE="$TEST_DIR/brief-grande.txt"; python3 -c "print('Agente: BACK\n' + 'detalhe da tarefa ' * 1200)" > "$GRANDE"
PEQUENO="$TEST_DIR/brief-pequeno.txt"; python3 -c "print('Agente: BACK\nfaca a rota X')" > "$PEQUENO"
dispara() { evento tool_name="${3:-Agent}" "tool_input.name=$1" tool_input.description=onda "tool_input.prompt=@$2"; }

espera 0 "BACK com brief pequeno: passa" "$(dispara back-onda-1 "$PEQUENO")"
espera 2 "BACK com brief de ~5.400 tokens (> 4.000): bloqueia" "$(dispara back-onda-1 "$GRANDE")"
stderr_contem "SUB-TAREFAS IRMÃS PARALELAS"
stderr_contem "6 seções"
log_contem "\[pre-despacho\] \[MAIN\] BLOQUEIO: despacho de BACK"
espera 2 "nome antigo da ferramenta (Task) tambem e vigiado" "$(dispara engine-onda-2 "$GRANDE" Task)"
espera 0 "CRONOS e isento" "$(dispara cronos "$GRANDE")"
espera 0 "ATLAS e isento" "$(dispara atlas-replanejar "$GRANDE")"
SUB_GRANDE="$TEST_DIR/sub.txt"; python3 -c "print('Leia .delta-11/sub-agentes/build-validator.md. ' + 'contexto ' * 1200)" > "$SUB_GRANDE"
espera 0 "sub-agente build-validator com brief grande: isento" "$(evento tool_name=Agent tool_input.description=build-validator "tool_input.prompt=@$SUB_GRANDE")"
espera 0 "sub-agente qa-ui-tandem e isento" "$(evento tool_name=Agent tool_input.description=qa-ui-tandem 'tool_input.prompt=x')"
espera 0 "ferramenta que nao e Agent: ignora" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/a tool_input.content=x)"

echo '{"brief_max_tokens": 9000}' > .delta-11/.config-limites.json
espera 0 "brief_max_tokens=9000 no .config-limites.json: o mesmo brief passa (D36)" "$(dispara back-onda-1 "$GRANDE")"
echo 'quebrado' > .delta-11/.config-limites.json
espera 2 "config quebrado: volta ao padrao de 4.000" "$(dispara back-onda-1 "$GRANDE")"
fim
