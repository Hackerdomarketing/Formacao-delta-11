#!/usr/bin/env bash
# Teste do vigia log-activity.js (PostToolUse Write|Edit|Bash) — Delta-11 v6.3
# Cobre C-032/D25 (formato único de linha, hora UTC), C-006 (log na pasta
# principal mesmo de dentro da worktree) e C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro PostToolUse log-activity.js) || { err "log-activity.js NAO registrado em PostToolUse"; resultado_final "log-activity.js"; }
ok "registrado em PostToolUse: $CMD"
M=$(matchers_do_registro PostToolUse log-activity.js)
for f in Write Edit Bash; do echo "$M" | grep -q "$f" && ok "matcher inclui $f" || err "matcher sem $f"; done
node --check "$HOOKS_DIR/log-activity.js" 2>/dev/null && ok "node --check" || err "node --check falhou"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
com_git_e_worktree "$P"
W="$P/.claude/worktrees/w1"
LOG="$P/.delta-11/activity-log.md"
cat > "$P/.delta-11/ativacoes/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{"agente:AG1":{"agente":"BACK","session_id":"S1","agent_id":"AG1","visto_em":"2099-01-01T00:00:00Z"}}}
JSON
mkdir -p "$P/.delta-11/locks/src--a.ts.lock"; printf 'AGENTE: BACK\nTAREFA: T-012\n' > "$P/.delta-11/locks/src--a.ts.lock/meta"

rodar "$P" "$W" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S1","agent_id":"AG1","cwd":"'"$W"'","tool_name":"Edit","tool_input":{"file_path":"'"$W"'/src/a.ts","old_string":"linha | com pipe","new_string":"y"}}'
[ "$CODIGO" = "0" ] && ok "sai com 0" || err "exit=$CODIGO"
[ -f "$LOG" ] && ok "activity-log criado na PASTA PRINCIPAL" || err "activity-log ausente na principal"
[ ! -e "$W/.delta-11/activity-log.md" ] && ok "nada gravado dentro da worktree" || err "log gravado na worktree"
FORMATO='^- \[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\] \[log-activity\] \[[A-Za-z0-9_-]+\] '
tail -1 "$LOG" | grep -Eq "$FORMATO" && ok "linha no formato unico D25 (hora UTC com Z)" || err "formato errado: $(tail -1 "$LOG")"
tail -1 "$LOG" | grep -q '\[BACK\] Edit src/a.ts (T-012)' && ok "agente pelo vinculo do agent_id + tarefa da trava + caminho relativo" || err "conteudo: $(tail -1 "$LOG")"
grep -q '^| Hora' "$LOG" && err "ainda escreve tabela markdown" || ok "sem tabela markdown (C-032)"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S9","cwd":"'"$P"'","tool_name":"Bash","tool_input":{"command":"echo um\necho dois"}}'
tail -1 "$LOG" | grep -q '\[PRINCIPAL\] Bash: echo um echo dois' && ok "Bash de varias linhas vira uma linha; sessao sem agente = PRINCIPAL" || err "Bash: $(tail -1 "$LOG")"

LINHAS=$(wc -l < "$LOG")
rodar "$P" "$P" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S9","cwd":"'"$P"'","tool_name":"Read","tool_input":{"file_path":"x"}}'
[ "$(wc -l < "$LOG")" = "$LINHAS" ] && ok "Read nao gera linha" || err "Read gerou linha"

rodar "$P" "$P" "$CMD" 'quebrado'
[ "$CODIGO" = "0" ] && ok "entrada malformada: exit 0 (nunca bloqueia)" || err "exit=$CODIGO"

COUNT=$(grep -Evc "$FORMATO|^#|^>|^$" "$LOG")
[ "$COUNT" = "0" ] && ok "todas as linhas de registro seguem o formato" || err "$COUNT linha(s) fora do formato"

resultado_final "log-activity.js"
