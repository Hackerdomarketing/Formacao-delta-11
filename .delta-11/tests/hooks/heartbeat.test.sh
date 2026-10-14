#!/usr/bin/env bash
# Teste do vigia heartbeat.sh (PostToolUse "*") — Delta-11 v6.3
# Cobre N-002/D28 (pulso na pasta principal, pulsos-data.js, identificação
# por agent_id/agent_type/ACK mais recente), C-031 (JSON seguro), C-006, C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro PostToolUse heartbeat.sh) || { err "heartbeat.sh NAO registrado em PostToolUse"; resultado_final "heartbeat.sh"; }
ok "registrado em PostToolUse: $CMD"
[ "$(matchers_do_registro PostToolUse heartbeat.sh)" = "*" ] && ok "matcher \"*\" (toda ferramenta)" || err "matcher deveria ser *"
bash -n "$HOOKS_DIR/heartbeat.sh" && ok "bash -n" || err "bash -n falhou"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
com_git_e_worktree "$P"
W="$P/.claude/worktrees/w1"
A="$P/.delta-11/ativacoes"

# 1. Sub-agente na worktree escreve o próprio ACK (Passo 0)
touch "$A/ack-BACK.txt"
rodar "$P" "$W" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S1","agent_id":"AG1","agent_type":"general-purpose","cwd":"'"$W"'","tool_name":"Bash","tool_input":{"command":"echo {} > .delta-11/ativacoes/ack-BACK.txt"}}'
[ "$CODIGO" = "0" ] && ok "sai com 0" || err "exit=$CODIGO"
[ -z "$SAIDA" ] && ok "nao imprime nada no stdout" || err "stdout inesperado: $SAIDA"
[ -f "$A/pulso-BACK.json" ] && ok "pulso gravado na PASTA PRINCIPAL" || err "pulso-BACK.json ausente na principal"
[ ! -e "$W/.delta-11/ativacoes/pulso-BACK.json" ] && ok "nada gravado dentro da worktree" || err "pulso gravado na worktree (C-006)"
json_valido "$A/pulso-BACK.json" && ok "pulso e JSON valido" || err "pulso invalido"
case "$(campo_json "$A/pulso-BACK.json" worktree)" in *"/.claude/worktrees/w1") ok "pulso registra a worktree" ;; *) err "campo worktree errado" ;; esac
grep -q '"agente":"BACK"' "$A/pulso-BACK.json" && grep -q '"epoch":[0-9]' "$A/pulso-BACK.json" \
    && ok "campos no formato compacto que o monitor le (\"agente\":\"...\", \"epoch\":N)" || err "formato incompativel com o monitor"
grep -q '"agente:AG1"' "$A/agentes-sessao.json" && ok "vinculo agent_id AG1 -> BACK gravado" || err "vinculo nao gravado"

PD="$P/.delta-11/pulsos-data.js"
if [ -f "$PD" ] && grep -q '^window.D11_PULSOS = ' "$PD"; then ok "pulsos-data.js regenerado"; else err "pulsos-data.js ausente"; fi
python3 - "$PD" <<'PY' && ok "pulsos-data.js: atualizado_em + agentes.BACK{ultimo_sinal,ferramenta,worktree}" || err "conteudo do pulsos-data.js fora do formato D28"
import json, re, sys
texto = open(sys.argv[1], encoding="utf-8").read()
dados = json.loads(re.search(r"window\.D11_PULSOS = (\{.*\});", texto, re.S).group(1))
b = dados["agentes"]["BACK"]
assert dados["atualizado_em"].endswith("Z")
assert b["ultimo_sinal"].endswith("Z") and b["ferramenta"] == "Bash" and b["worktree"].endswith("w1")
PY

# 2. Ação seguinte do mesmo sub-agente: identificado pelo vínculo, mesmo com ACK de outro mais novo
sleep 1; touch "$A/ack-FRONT.txt"
rodar "$P" "$W" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S1","agent_id":"AG1","cwd":"'"$W"'","tool_name":"Edit","tool_input":{"file_path":"'"$W"'/src/a.ts"}}'
[ "$(campo_json "$A/pulso-BACK.json" ultima_tool)" = "Edit" ] && ok "agent_id ja vinculado: pulso do BACK renovado" || err "vinculo do agent_id nao usado"
[ ! -f "$A/pulso-FRONT.json" ] && ok "ACK mais novo de outro agente nao rouba o pulso" || err "pulso atribuido ao agente errado"

# 3. agent_type com nome Delta-11
rodar "$P" "$P" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S2","agent_id":"AG2","agent_type":"shield","cwd":"'"$P"'","tool_name":"Read","tool_input":{}}'
[ -f "$A/pulso-SHIELD.json" ] && ok "agent_type \"shield\" identifica SHIELD" || err "agent_type nao usado"

# 4. Sem vínculo nem agent_type: ACK MAIS RECENTE (não o primeiro em ordem alfabética)
rodar "$P" "$P" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S3","cwd":"'"$P"'","tool_name":"Grep","tool_input":{}}'
[ -f "$A/pulso-FRONT.json" ] && ok "sem vinculo: usa o ACK mais recente (FRONT), nao o primeiro alfabetico" || err "fallback do ACK mais recente falhou"

# 5. Caracteres especiais não quebram o JSON (C-031)
rodar "$P" "$P" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S\"3\\x","cwd":"'"$P"'","tool_name":"Gr\"ep","tool_input":{}}'
json_valido "$A/pulso-FRONT.json" && ok "aspas no session_id/tool_name: JSON continua valido" || err "JSON quebrado por aspas"

# 6. JSON de entrada com espaços (o grep antigo falhava)
rodar "$P" "$P" "$CMD" '{ "hook_event_name" : "PostToolUse", "session_id" : "S4", "agent_id" : "AG1", "cwd" : "'"$W"'", "tool_name" : "Write", "tool_input" : {} }'
[ "$(campo_json "$A/pulso-BACK.json" ultima_tool)" = "Write" ] && ok "entrada com espacos apos os dois-pontos e lida" || err "entrada com espacos nao lida"

# 7. Agente removeu o próprio ACK: pulso some
rodar "$P" "$W" "$CMD" '{"hook_event_name":"PostToolUse","session_id":"S1","agent_id":"AG1","cwd":"'"$W"'","tool_name":"Bash","tool_input":{"command":"rm -f .delta-11/ativacoes/ack-BACK.txt"}}'
[ ! -f "$A/pulso-BACK.json" ] && ok "rm do proprio ACK apaga o pulso" || err "pulso ficou depois do rm do ACK"
grep -q '"BACK"' "$PD" && err "BACK continua no pulsos-data.js" || ok "pulsos-data.js sem o BACK"

# 8. Pasta que não é projeto Delta-11: não cria nada
Q=$(mktemp -d "${TMPDIR:-/tmp}/d11-teste.XXXXXX"); PASTAS_TEMP+=("$Q")
rodar "$Q" "$Q" "bash \"$HOOKS_DIR/heartbeat.sh\"" '{"hook_event_name":"PostToolUse","cwd":"'"$Q"'","tool_name":"Bash","tool_input":{}}'
[ "$CODIGO" = "0" ] && [ -z "$(ls -A "$Q")" ] && ok "fora de projeto Delta-11: exit 0 e nada criado" || err "criou arquivos fora de projeto Delta-11"

# 9. Entrada malformada nunca derruba
rodar "$P" "$P" "$CMD" 'isto nao e json'
[ "$CODIGO" = "0" ] && ok "entrada malformada: exit 0" || err "entrada malformada exit=$CODIGO"

resultado_final "heartbeat.sh"
