#!/usr/bin/env bash
# Teste do vigia pre-compact.sh (PreCompact + SessionStart "compact") — Delta-11 v6.3
# Cobre C-033 (o alerta chega ao modelo por additionalContext no SessionStart
# "compact"; o pulso mantém os campos) e C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro PreCompact pre-compact.sh) || { err "pre-compact.sh NAO registrado em PreCompact"; resultado_final "pre-compact.sh"; }
ok "registrado em PreCompact: $CMD"
CMD_SS=$(comando_do_registro SessionStart pre-compact.sh) && ok "registrado em SessionStart" || err "pre-compact.sh NAO registrado em SessionStart"
[ "$(matchers_do_registro SessionStart pre-compact.sh)" = "compact" ] && ok "SessionStart com matcher \"compact\"" || err "matcher do SessionStart deveria ser compact"
bash -n "$HOOKS_DIR/pre-compact.sh" && ok "bash -n" || err "bash -n falhou"
grep -q "systemMessage" "$HOOKS_DIR/heartbeat.sh" && err "ainda usa systemMessage (descartado no PreCompact)" || ok "nao depende de systemMessage"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
A="$P/.delta-11/ativacoes"
echo '{}' > "$A/ack-ENGINE.txt"
cat > "$A/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{"agente:E1":{"agente":"ENGINE","session_id":"S1","agent_id":"E1","visto_em":"2099-01-01T00:00:00Z"}}}
JSON
echo '{"agente":"ENGINE","status":"ativo","ultima_tool":"Bash","session_id":"S1","worktree":null}' > "$A/pulso-ENGINE.json"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"PreCompact","session_id":"S1","agent_id":"E1","cwd":"'"$P"'","trigger":"auto","custom_instructions":null}'
[ "$CODIGO" = "0" ] && ok "PreCompact: exit 0 (codigo 2 cancelaria a compactacao)" || err "PreCompact exit=$CODIGO"
[ -z "$SAIDA" ] && ok "PreCompact: nada no stdout (seria descartado)" || err "stdout inesperado"
[ "$(campo_json "$A/pulso-ENGINE.json" status)" = "contexto_critico" ] && ok "pulso marcado contexto_critico" || err "status do pulso nao mudou"
[ "$(campo_json "$A/pulso-ENGINE.json" ultima_tool)" = "Bash" ] && [ "$(campo_json "$A/pulso-ENGINE.json" session_id)" = "S1" ] \
    && ok "pulso mantem ultima_tool e session_id" || err "pulso perdeu campos (C-033)"

rodar "$P" "$P" "$CMD_SS" '{"hook_event_name":"SessionStart","session_id":"S1","agent_id":"E1","cwd":"'"$P"'","source":"compact"}'
[ "$CODIGO" = "0" ] && ok "SessionStart compact: exit 0" || err "exit=$CODIGO"
printf '%s' "$SAIDA" | python3 -c 'import json,sys
d = json.load(sys.stdin)["hookSpecificOutput"]
assert d["hookEventName"] == "SessionStart"
assert "ENGINE-produto.md" in d["additionalContext"] and "ENGINE-historia.md" in d["additionalContext"]' \
    && ok "additionalContext com o alerta para o ENGINE (produto/historia, D8)" || err "saida sem additionalContext valido: $SAIDA"
printf '%s' "$SAIDA" | grep -q "estado.md\|kanban" && err "alerta ainda manda mexer em estado.md/kanban" || ok "alerta sem estado.md (legado) nem kanban (so o CRONOS escreve)"

rodar "$P" "$P" "$CMD_SS" '{"hook_event_name":"SessionStart","session_id":"S1","cwd":"'"$P"'","source":"startup"}'
[ "$CODIGO" = "0" ] && [ -z "$SAIDA" ] && ok "SessionStart startup: silencio" || err "SessionStart startup imprimiu: $SAIDA"

resultado_final "pre-compact.sh"
