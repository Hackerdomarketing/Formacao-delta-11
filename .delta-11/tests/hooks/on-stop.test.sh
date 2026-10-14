#!/usr/bin/env bash
# Teste do vigia on-stop.sh (Stop + SessionEnd) — Delta-11 v6.3
# Cobre C-007 (Stop não "mata" o agente a cada resposta), C-008 (SessionEnd
# registrado e com a lógica de encerramento) e C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro Stop on-stop.sh) || { err "on-stop.sh NAO registrado em Stop"; resultado_final "on-stop.sh"; }
ok "registrado em Stop: $CMD"
CMD_FIM=$(comando_do_registro SessionEnd on-stop.sh) && ok "registrado em SessionEnd" || err "on-stop.sh NAO registrado em SessionEnd"
bash -n "$HOOKS_DIR/on-stop.sh" && ok "bash -n" || err "bash -n falhou"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
A="$P/.delta-11/ativacoes"
# ATLAS na sessão S1 (principal), CRONOS sub-agente de S1, BACK de OUTRA sessão (S2)
for n in ATLAS CRONOS BACK; do echo '{}' > "$A/ack-$n.txt"; echo "{\"agente\":\"$n\",\"status\":\"ativo\",\"ultima_tool\":\"Edit\"}" > "$A/pulso-$n.json"; done
cat > "$A/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{
"principal:S1":{"agente":"ATLAS","session_id":"S1","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null},
"agente:C1":{"agente":"CRONOS","session_id":"S1","agent_id":"C1","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null},
"principal:S2":{"agente":"BACK","session_id":"S2","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null}}}
JSON

rodar "$P" "$P" "$CMD" '{"hook_event_name":"Stop","session_id":"S1","cwd":"'"$P"'","stop_hook_active":false,"last_assistant_message":"ok"}'
[ "$CODIGO" = "0" ] && ok "Stop: exit 0 (codigo 2 impediria o agente de parar)" || err "Stop exit=$CODIGO"
[ -f "$A/ack-ATLAS.txt" ] && ok "Stop: ACK continua (nao mata o agente a cada resposta)" || err "Stop apagou o ACK (C-007)"
ls "$A"/morte-*.json >/dev/null 2>&1 && err "Stop gravou registro de morte" || ok "Stop: nenhum registro de morte"
[ "$(campo_json "$A/pulso-ATLAS.json" status)" = "aguardando" ] && ok "Stop: pulso renovado com status aguardando" || err "Stop nao renovou o pulso"
[ "$(campo_json "$A/pulso-ATLAS.json" ultima_tool)" = "Edit" ] && ok "Stop: campos do pulso preservados" || err "Stop perdeu ultima_tool"

rodar "$P" "$P" "$CMD_FIM" '{"hook_event_name":"SessionEnd","session_id":"S1","cwd":"'"$P"'","reason":"prompt_input_exit"}'
[ "$CODIGO" = "0" ] && ok "SessionEnd: exit 0" || err "SessionEnd exit=$CODIGO"
[ -f "$A/morte-ATLAS.json" ] && [ -f "$A/morte-CRONOS.json" ] && ok "SessionEnd: registro de morte dos agentes DESTA sessao" || err "morte nao gravada"
[ "$(campo_json "$A/morte-ATLAS.json" motivo)" = "sessao_encerrada:prompt_input_exit" ] && ok "motivo vem do campo reason do SessionEnd" || err "motivo: $(campo_json "$A/morte-ATLAS.json" motivo)"
[ ! -f "$A/ack-ATLAS.txt" ] && [ ! -f "$A/pulso-ATLAS.json" ] && [ ! -f "$A/ack-CRONOS.txt" ] && ok "SessionEnd: ACK e pulso apagados" || err "ACK/pulso ficaram"
[ -f "$A/ack-BACK.txt" ] && [ -f "$A/pulso-BACK.json" ] && [ ! -f "$A/morte-BACK.json" ] && ok "agente de OUTRA sessao nao e tocado" || err "SessionEnd mexeu em agente de outra sessao"
grep -q '"BACK"' "$P/.delta-11/pulsos-data.js" && ! grep -q '"ATLAS"' "$P/.delta-11/pulsos-data.js" && ok "pulsos-data.js regenerado" || err "pulsos-data.js desatualizado"
grep -Eq '^- \[[0-9TZ:-]+\] \[on-stop\] \[ATLAS,CRONOS\] sess' "$P/.delta-11/activity-log.md" && ok "linha no activity-log (formato D25)" || err "sem linha no activity-log"

resultado_final "on-stop.sh"
