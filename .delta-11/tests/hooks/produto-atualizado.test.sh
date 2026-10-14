#!/usr/bin/env bash
# Teste do vigia produto-atualizado.py (v6.3 — C-006, C-036)
source "$(dirname "$0")/_ajudante-hooks-python.sh" produto-atualizado
checagens_basicas

novo_projeto
MEM="$TEST_DIR/.delta-11/memoria"
BASE=$'# Kanban\n## FAZENDO\n- [ ] T-20 tela | Agente: FRONT\n## CONCLUÍDO\n- [x] T-10 antiga | Por: VAULT'
kanban "$BASE"
CONCLUI=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-20' 'tool_input.new_string=- [x] T-20')

espera 2 "FRONT conclui sem FRONT-produto.md: bloqueia" "$CONCLUI"
stderr_contem "NAO EXISTE"
echo "estado" > "$MEM/FRONT-produto.md"; envelhecer "$MEM/FRONT-produto.md" 5
espera 2 "FRONT-produto.md de 5 h atras: bloqueia" "$CONCLUI"
touch "$MEM/FRONT-produto.md"
espera 0 "FRONT-produto.md recente: passa" "$CONCLUI"
espera 0 "reescrever o kanban com a tarefa antiga de VAULT (sem VAULT-produto): passa (C-036)" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/.delta-11/kanban.md "tool_input.content=$BASE"$'\n(reorganizado)')"
espera 0 "ATLAS isento" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=## CONCLUÍDO' $'tool_input.new_string=## CONCLUÍDO\n- [x] T-30 plano | Por: ATLAS')"

# O produto.md e lido da PASTA PRINCIPAL mesmo com o cwd numa subpasta (C-006)
mkdir -p "$TEST_DIR/src/sub"
rm -f "$MEM/FRONT-produto.md"
espera 2 "cwd numa subpasta e sem produto: bloqueia" "$(evento cwd=$TEST_DIR/src/sub tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=- [ ] T-20' 'tool_input.new_string=- [x] T-20')"
echo x > "$MEM/FRONT-produto.md"
espera 0 "cwd numa subpasta e produto na pasta principal: passa" "$(evento cwd=$TEST_DIR/src/sub tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=- [ ] T-20' 'tool_input.new_string=- [x] T-20')"
fim
