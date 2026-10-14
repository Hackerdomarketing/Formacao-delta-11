#!/usr/bin/env bash
# Teste do vigia fase-consciencia-checker.py (v6.3 — C-015, C-026). Fase 4.5 = Dia 6.
source "$(dirname "$0")/_ajudante-hooks-python.sh" fase-consciencia-checker
checagens_basicas

novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
kanban $'# Kanban\n## FAZENDO\n- [ ] T-CON-01 [4.5] auditoria | Agente: VAULT'
SELO_REL=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nFase 4.5 selada pelo SHIELD')
SELO_ABS=$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n- [x] Dia 6 selado')

espera 0 "concluir tarefa [4.5] individual: passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-CON-01' 'tool_input.new_string=- [x] T-CON-01')"
espera 2 "selo com caminho RELATIVO e sem entregaveis: bloqueia (C-026)" "$SELO_REL"
espera 2 "selo 'Dia 6 selado' com caminho absoluto: bloqueia" "$SELO_ABS"

# 5 arquivos quaisquer com 'consciencia' no nome NAO bastam (C-026)
for s in a b c d e; do echo x > "$DEC/2026-10-14-consciencia-01-$s.md"; done
espera 2 "5 arquivos todos com numero 01: bloqueia (faltam 02 a 05)" "$SELO_REL"
stderr_contem "05. fluxos-aprovacao"

for n in 02 03 04 05; do echo x > "$DEC/2026-10-14-consciencia-$n-item.md"; done
espera 0 "um entregavel de cada numero (01 a 05): selo liberado" "$SELO_REL"
espera 0 "edicao sem selo: passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md tool_input.old_string=auditoria tool_input.new_string=auditoria-imutavel)"
fim
