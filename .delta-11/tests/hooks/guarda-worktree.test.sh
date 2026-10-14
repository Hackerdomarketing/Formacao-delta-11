#!/usr/bin/env bash
# Teste do vigia guarda-worktree.py (v6.3 — C-130, C-006, D25)
source "$(dirname "$0")/_ajudante-hooks-python.sh" guarda-worktree
checagens_basicas

novo_projeto
espera 0 "fora de repositorio git: nao se aplica" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/src/a.ts tool_input.old_string=a tool_input.new_string=b)"

git init -q . && git config user.email t@t.t && git config user.name T
mkdir -p src && echo a > src/a.ts && echo k > .delta-11/kanban.md && git add -A && git commit -qm init
PRINCIPAL="$TEST_DIR"
edita() { evento "cwd=$1" tool_name=Edit "tool_input.file_path=$2" tool_input.old_string=a tool_input.new_string=b; }

espera 0 "principal sem worktrees: editar codigo passa" "$(edita "$PRINCIPAL" "$PRINCIPAL/src/a.ts")"

WT="${TEST_DIR}-wt-back"
git worktree add -q "$WT" -b back-onda-1
espera 2 "CASO A: codigo na main com worktree ativa: bloqueia" "$(edita "$PRINCIPAL" "$PRINCIPAL/src/a.ts")"
stderr_contem "CASO A"
log_contem "\[guarda-worktree\] \[MAIN\] BLOQUEIO: CASO A"
espera 0 "na main, editar .delta-11 (coordenacao): passa" "$(edita "$PRINCIPAL" "$PRINCIPAL/.delta-11/kanban.md")"
espera 0 "na main, editar CLAUDE.md: passa" "$(edita "$PRINCIPAL" "$PRINCIPAL/CLAUDE.md")"
touch "$PRINCIPAL/.delta-11/.permitir-edicao-main"
espera 0 "escape .permitir-edicao-main: passa" "$(edita "$PRINCIPAL" "$PRINCIPAL/src/a.ts")"
rm -f "$PRINCIPAL/.delta-11/.permitir-edicao-main"

espera 0 "na worktree, editar o proprio codigo: passa" "$(edita "$WT" "src/a.ts")"
espera 2 "CASO B: na worktree, kanban pela copia local: bloqueia" "$(edita "$WT" ".delta-11/kanban.md")"
stderr_contem "$PRINCIPAL/.delta-11/kanban.md"
espera 2 "CASO B: logs/ tambem e compartilhado" "$(edita "$WT" "$WT/.delta-11/logs/sub-agentes/x.log")"
espera 0 "na worktree, editar o kanban da PRINCIPAL por caminho absoluto: passa" "$(edita "$WT" "$PRINCIPAL/.delta-11/kanban.md")"
espera 2 "CASO C: na worktree, codigo da main por caminho absoluto: bloqueia" "$(edita "$WT" "$PRINCIPAL/src/a.ts")"
log_contem "\[guarda-worktree\] \[MAIN\] BLOQUEIO: CASO C"
if [ -f "$WT/.delta-11/activity-log.md" ] && grep -q "guarda-worktree" "$WT/.delta-11/activity-log.md"; then err "log foi para a copia da worktree (C-006)"; else ok "log vai para a pasta principal, nao para a worktree (C-006)"; fi

# Caso real do Claude Code: a worktree fica DENTRO do repo principal (.claude/worktrees/agent-x/).
# Achado no teste ao vivo da v6.3: o vigia tratava o arquivo da propria copia como "codigo da main".
WT_DENTRO="$PRINCIPAL/.claude/worktrees/agent-teste"
git worktree add -q "$WT_DENTRO" -b agent-teste
espera 0 "worktree dentro de .claude/worktrees: editar o proprio codigo por caminho ABSOLUTO passa" "$(edita "$WT_DENTRO" "$WT_DENTRO/src/a.ts")"
espera 2 "worktree dentro de .claude/worktrees: codigo da main por caminho absoluto continua bloqueado" "$(edita "$WT_DENTRO" "$PRINCIPAL/src/a.ts")"

git worktree remove --force "$WT_DENTRO" 2>/dev/null
git worktree remove --force "$WT" 2>/dev/null
[ -n "$WT" ] && [ -d "$WT" ] && rm -rf "$WT"
fim
