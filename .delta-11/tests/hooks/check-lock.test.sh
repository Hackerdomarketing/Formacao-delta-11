#!/usr/bin/env bash
# Teste do vigia check-lock.js (PreToolUse Write|Edit) — Delta-11 v6.3
# Cobre C-022 (sessão principal identificada; entrada malformada bloqueia),
# C-006/D25 (travas na pasta principal mesmo de dentro da worktree) e C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro PreToolUse check-lock.js) || { err "check-lock.js NAO registrado em PreToolUse"; resultado_final "check-lock.js"; }
ok "registrado em PreToolUse: $CMD"
case "$CMD" in *'"$CLAUDE_PROJECT_DIR/.delta-11/hooks/check-lock.js"'*) ok "comando usa \"\$CLAUDE_PROJECT_DIR\"" ;; *) err "comando sem \"\$CLAUDE_PROJECT_DIR\"" ;; esac
M=$(matchers_do_registro PreToolUse check-lock.js)
if echo "$M" | grep -q "Edit" && echo "$M" | grep -q "Write"; then ok "matcher cobre Edit e Write ($M)"; else err "matcher errado: $M"; fi
node --check "$HOOKS_DIR/check-lock.js" 2>/dev/null && ok "node --check" || err "node --check falhou"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
com_git_e_worktree "$P"
W="$P/.claude/worktrees/w1"
[ -d "$W" ] && ok "projeto de teste com worktree" || err "worktree de teste nao criada"

# ATLAS na sessão principal (S1) e BACK no sub-agente AG1 (vínculos do heartbeat)
cat > "$P/.delta-11/ativacoes/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{"principal:S1":{"agente":"ATLAS","session_id":"S1","visto_em":"2099-01-01T00:00:00Z"},
"agente:AG1":{"agente":"BACK","session_id":"S1","agent_id":"AG1","visto_em":"2099-01-01T00:00:00Z"}}}
JSON

ev_edit() { # $1 cwd $2 arquivo $3 agent_id(opcional)
    local extra=""; [ -n "${3:-}" ] && extra=",\"agent_id\":\"$3\",\"agent_type\":\"general-purpose\""
    printf '{"hook_event_name":"PreToolUse","session_id":"S1"%s,"cwd":"%s","tool_name":"Edit","tool_input":{"file_path":"%s","old_string":"x","new_string":"y"}}' "$extra" "$1" "$2"
}

rodar "$P" "$P" "$CMD" "$(ev_edit "$P" "$P/src/a.ts")"
[ "$CODIGO" = "0" ] && ok "sem trava: libera (exit 0)" || err "sem trava deveria liberar (exit=$CODIGO)"

mkdir -p "$P/.delta-11/locks/src--a.ts.lock"
printf 'AGENTE: FRONT\nTAREFA: T-001\nFAZENDO: tela de login\nINICIOU: 2026-10-14T10:00:00Z\n' > "$P/.delta-11/locks/src--a.ts.lock/meta"

rodar "$P" "$P" "$CMD" "$(ev_edit "$P" "$P/src/a.ts")"
if [ "$CODIGO" = "2" ] && echo "$ERRO" | grep -q "BLOQUEADO" && echo "$ERRO" | grep -q "FRONT"; then
    ok "trava de FRONT bloqueia ATLAS na sessao principal (exit 2, motivo no stderr)"
else err "deveria bloquear com exit 2 (exit=$CODIGO, stderr=$ERRO)"; fi
echo "$ERRO" | grep -q "Você foi identificado como ATLAS" && ok "mensagem diz quem e o agente atual" || err "mensagem nao identifica o agente"
echo "$ERRO" | grep -q "apague a pasta" && ok "mensagem ensina o comandante a liberar trava esquecida" || err "mensagem sem saida para o comandante"

rodar "$P" "$W" "$CMD" "$(ev_edit "$W" "$W/src/a.ts" AG1)"
[ "$CODIGO" = "2" ] && ok "BACK na worktree e bloqueado pela trava da pasta principal" || err "trava da principal ignorada na worktree (exit=$CODIGO)"

sed -i.bak 's/AGENTE: FRONT/AGENTE: BACK/' "$P/.delta-11/locks/src--a.ts.lock/meta" && rm -f "$P/.delta-11/locks/src--a.ts.lock/meta.bak"
rodar "$P" "$W" "$CMD" "$(ev_edit "$W" "$W/src/a.ts" AG1)"
[ "$CODIGO" = "0" ] && ok "dono da trava (BACK, pelo agent_id) edita livre" || err "dono da trava foi bloqueado (exit=$CODIGO)"

printf 'AGENTE: FRONT\nSESSION: S9\n' > "$P/.delta-11/locks/src--a.ts.lock/meta"
rodar "$P" "$P" "$CMD" "$(ev_edit "$P" "$P/src/a.ts" | sed 's/"session_id":"S1"/"session_id":"S9"/')"
[ "$CODIGO" = "0" ] && ok "trava com SESSION igual ao session_id da sessao principal: libera" || err "SESSION da trava ignorado (exit=$CODIGO)"

rodar "$P" "$P" "$CMD" '{"tool_name": "Edit", quebrado'
if [ "$CODIGO" = "2" ] && echo "$ERRO" | grep -q "JSON"; then ok "entrada malformada: bloqueia com mensagem clara (exit 2)"; else err "entrada malformada deveria bloquear (exit=$CODIGO)"; fi

rodar "$P" "$P" "$CMD" "$(ev_edit "$P" "/etc/hosts")"
[ "$CODIGO" = "0" ] && ok "arquivo fora do projeto: libera" || err "arquivo fora do projeto bloqueado (exit=$CODIGO)"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"PreToolUse","session_id":"S1","cwd":"'"$P"'","tool_name":"Read","tool_input":{"file_path":"'"$P"'/src/a.ts"}}'
[ "$CODIGO" = "0" ] && ok "outra ferramenta (Read): libera" || err "Read bloqueado (exit=$CODIGO)"

resultado_final "check-lock.js"
