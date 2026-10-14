#!/usr/bin/env bash
# Teste do vigia release-locks.js (SubagentStop + SessionEnd) — Delta-11 v6.3
# Cobre C-007 (não libera no Stop), C-008 (libera travas de sub-agente),
# C-009 (registro único), C-032 (formato D25) e C-130.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro SubagentStop release-locks.js) || { err "release-locks.js NAO registrado em SubagentStop"; resultado_final "release-locks.js"; }
ok "registrado em SubagentStop: $CMD"
comando_do_registro SessionEnd release-locks.js >/dev/null && ok "registrado em SessionEnd" || err "NAO registrado em SessionEnd"
comando_do_registro Stop release-locks.js >/dev/null && err "ainda registrado em Stop (soltaria travas a cada resposta)" || ok "nao registrado em Stop"
N=$(grep -c 'release-locks.js' "$SETTINGS"); [ "$N" = "2" ] && ok "exatamente 2 registros (SubagentStop, SessionEnd)" || err "$N registros"
node --check "$HOOKS_DIR/release-locks.js" 2>/dev/null && ok "node --check" || err "node --check falhou"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
L="$P/.delta-11/locks"
trava() { mkdir -p "$L/$1"; printf "AGENTE: %s\nTAREFA: T-1\n%s" "$2" "${3:-}" > "$L/$1/meta"; }
trava a.lock BACK; trava b.lock FRONT; trava c.lock ATLAS; trava d.lock VAULT "SESSION: AG9
"; trava e.lock PIXEL
cat > "$P/.delta-11/ativacoes/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{
"agente:AG1":{"agente":"BACK","session_id":"S1","agent_id":"AG1","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null},
"principal:S1":{"agente":"ATLAS","session_id":"S1","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null},
"agente:AG5":{"agente":"PIXEL","session_id":"S2","agent_id":"AG5","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null}}}
JSON

rodar "$P" "$P" "$CMD" '{"hook_event_name":"Stop","session_id":"S1","cwd":"'"$P"'"}'
[ "$CODIGO" = "0" ] && [ -d "$L/a.lock" ] && [ -d "$L/c.lock" ] && ok "evento Stop: nenhuma trava liberada" || err "Stop liberou travas (C-007)"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"AG1","agent_type":"general-purpose","cwd":"'"$P"'","stop_hook_active":false}'
[ "$CODIGO" = "0" ] && ok "SubagentStop: exit 0 (codigo 2 impediria o sub-agente de terminar)" || err "exit=$CODIGO"
[ ! -e "$L/a.lock" ] && ok "trava do BACK (sub-agente que terminou) liberada" || err "trava do BACK ficou"
[ -d "$L/b.lock" ] && [ -d "$L/c.lock" ] && ok "travas de FRONT e ATLAS intactas" || err "liberou trava de outro agente"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"AG9","agent_type":"general-purpose","cwd":"'"$P"'"}'
[ ! -e "$L/d.lock" ] && ok "trava com SESSION = agent_id liberada" || err "SESSION nao reconhecido"

rodar "$P" "$P" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"DESCONHECIDO","agent_type":"general-purpose","cwd":"'"$P"'"}'
[ -d "$L/b.lock" ] && [ -d "$L/c.lock" ] && ok "sub-agente nao identificado: nao chuta dono (nada liberado)" || err "liberou sem identificar"

mkdir -p "$L/velha.lock" "$L/nova.lock"; envelhecer "$L/velha.lock" 3
rodar "$P" "$P" "$(comando_do_registro SessionEnd release-locks.js)" '{"hook_event_name":"SessionEnd","session_id":"S1","cwd":"'"$P"'","reason":"other"}'
[ ! -e "$L/c.lock" ] && ok "SessionEnd: trava do ATLAS (sessao S1) liberada" || err "SessionEnd nao liberou a trava da sessao"
[ -d "$L/b.lock" ] && [ -d "$L/e.lock" ] && ok "SessionEnd: travas sem vinculo a S1 (FRONT, PIXEL de S2) intactas" || err "SessionEnd liberou trava de outra sessao"
[ ! -e "$L/velha.lock" ] && [ -d "$L/nova.lock" ] && ok "trava ilegivel: so a mais velha que lock_horas (2 h) sai" || err "regra das travas ilegiveis falhou"

LOG="$P/.delta-11/activity-log.md"
grep -Eq '^- \[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\] \[release-locks\] \[BACK\] 1 trava' "$LOG" && ok "linha no activity-log no formato D25" || err "log: $(cat "$LOG" 2>/dev/null)"
grep -q '^| ' "$LOG" && err "ainda escreve linha de tabela" || ok "sem linha de tabela"

resultado_final "release-locks.js"
