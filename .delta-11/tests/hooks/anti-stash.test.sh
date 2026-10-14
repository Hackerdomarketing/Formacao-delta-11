#!/usr/bin/env bash
# Teste do vigia anti-stash.py (v6.3 — C-020, C-036)
source "$(dirname "$0")/_ajudante-hooks-python.sh" anti-stash
checagens_basicas

novo_projeto
git init -q . && git config user.email t@t.t && git config user.name T
echo x > a.txt && git add a.txt && git commit -qm init
KB="$TEST_DIR/.delta-11/kanban.md"
kanban $'# Kanban\n## FAZENDO\n**T-1** — tarefa | Agente: BACK\n## ✅ CONCLUÍDO\n**T-0** — antiga | Por: BACK'
CONCLUI=$(evento tool_name=Write tool_input.file_path=$KB $'tool_input.content=# Kanban\n## FAZENDO\n## ✅ CONCLUÍDO\n**T-0** — antiga | Por: BACK\n**T-1** — tarefa | Por: BACK | Aprovado: SHIELD')

espera 0 "sem stash: concluir passa" "$CONCLUI"

echo y > a.txt && git stash push -qm "escondendo teste vermelho" a.txt
espera 2 "stash RECENTE: concluir bloqueia" "$CONCLUI"
stderr_contem "git stash pop"

REESCRITA=$(evento tool_name=Write tool_input.file_path=$KB $'tool_input.content=# Kanban (reescrito)\n## FAZENDO\n**T-1** — tarefa | Agente: BACK\n## ✅ CONCLUÍDO\n**T-0** — antiga | Por: BACK')
espera 0 "reescrever o kanban sem conclusao NOVA: passa mesmo com stash (C-036)" "$REESCRITA"
espera 0 "edicao fora do kanban: ignora" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/notas.md 'tool_input.content=- [x] feito')"

# Stash antigo (fora da janela de 4 h) nao bloqueia (C-020)
novo_projeto
git init -q . && git config user.email t@t.t && git config user.name T
echo x > a.txt && git add a.txt && git commit -qm init
echo y > a.txt
VELHO=$(python3 -c "import time; print(int(time.time()) - 6*3600)")
GIT_COMMITTER_DATE="@$VELHO +0000" GIT_AUTHOR_DATE="@$VELHO +0000" git stash push -qm "stash de semanas atras" a.txt
KB="$TEST_DIR/.delta-11/kanban.md"
kanban $'# Kanban\n## FAZENDO\n- [ ] T-5 coisa [FRONT]'
espera 0 "stash de 6 h atras: nao bloqueia" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-5' 'tool_input.new_string=- [x] T-5')"

# caminho relativo do kanban e reconhecido
echo z > a.txt && git stash push -qm "recente" a.txt
espera 2 "caminho relativo .delta-11/kanban.md tambem e vigiado" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-5' 'tool_input.new_string=- [x] T-5')"
fim
