#!/usr/bin/env bash
# Teste do vigia worktree-prune.py (v6.3 — C-045, C-002)
source "$(dirname "$0")/_ajudante-hooks-python.sh" worktree-prune
checagens_basicas
if grep -q "depoor" "$HOOK"; then err "erro de digitacao 'depoor' ainda existe (C-045)"; else ok "sem 'depoor' (C-045)"; fi

novo_projeto
espera 0 "fora de repositorio git: exit 0" "$(evento hook_event_name=SessionStart)"

git init -q . && git config user.email t@t.t && git config user.name T
echo x > a.txt && git add a.txt && git commit -qm init
WT="${TEST_DIR}-wt-orfa"
git worktree add -q "$WT" -b orfa 2>/dev/null
[ -n "$WT" ] && [ -d "$WT" ] && rm -rf "$WT"
espera 0 "SessionStart com worktree orfa: exit 0" "$(evento hook_event_name=SessionStart)"
if [ -z "$SAIDA_PADRAO" ]; then ok "nada no stdout (SessionStart)"; else err "stdout inesperado: $SAIDA_PADRAO"; fi
if [ -z "$SAIDA_ERRO" ]; then ok "sem erro no stderr (o NameError sumiu)"; else err "stderr: $SAIDA_ERRO"; fi
log_contem "\[worktree-prune\] \[SISTEMA\] 1 registro\(s\) de worktree orfa removido"
if git worktree list --porcelain | grep -q "wt-orfa"; then err "registro da worktree orfa continua"; else ok "registro da worktree orfa removido"; fi
if grep -q "ERRO-INTERNO" .delta-11/activity-log.md; then err "caiu em ERRO-INTERNO"; else ok "sem ERRO-INTERNO"; fi
fim
