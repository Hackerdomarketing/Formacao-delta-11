#!/usr/bin/env bash
# Teste do vigia contratos-minimos.py (v6.3 — C-024)
source "$(dirname "$0")/_ajudante-hooks-python.sh" contratos-minimos
checagens_basicas
if grep -q "CONCLUSAO_RE" "$HOOK"; then err "regra morta CONCLUSAO_RE ainda existe"; else ok "sem regra morta CONCLUSAO_RE"; fi

novo_projeto
KB="$TEST_DIR/.delta-11/kanban.md"
PC="$TEST_DIR/.delta-11/memoria/project-core.md"
kanban $'# Kanban\n## [CICLO 2]\n- [ ] T-1 algo [BACK]'
echo "# PC" > "$PC"; envelhecer "$PC" 5

espera 0 "reescrever o kanban mantendo [CICLO 2]: passa (nao e ciclo novo)" "$(evento tool_name=Write tool_input.file_path=$KB $'tool_input.content=# Kanban\n## [CICLO 2]\n- [x] T-1 algo [BACK]')"
espera 0 "texto livre 'novo ciclo' nao e marcador: passa" "$(evento tool_name=Edit tool_input.file_path=$KB 'tool_input.old_string=algo' 'tool_input.new_string=algo (pensar num novo ciclo depois)')"
ABRE=$(evento tool_name=Edit tool_input.file_path=$KB 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n## [CICLO 3]')
espera 2 "abrir [CICLO 3] com project-core de 5 h: bloqueia" "$ABRE"
stderr_contem "CICLO 3"
touch "$PC"
espera 0 "abrir [CICLO 3] com project-core recente: passa" "$ABRE"
envelhecer "$PC" 5
echo "contratos" > "$TEST_DIR/.delta-11/memoria/project-core/contratos.md"
espera 0 "abrir ciclo com FATIA do project-core recente: passa" "$ABRE"
rm -f "$TEST_DIR/.delta-11/memoria/project-core/contratos.md" "$PC"
espera 2 "abrir ciclo sem project-core: bloqueia" "$ABRE"
espera 2 "[NOVO CICLO] tambem conta" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n- [NOVO CICLO] onda 1')"
fim
