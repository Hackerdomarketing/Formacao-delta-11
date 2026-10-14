#!/usr/bin/env bash
# Teste do vigia fim-subagente.sh (SubagentStop) — Delta-11 v6.3
# Cobre D32 (log em logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log),
# N-002 (limpa ACK/pulso do sub-agente que terminou) e C-008.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro SubagentStop fim-subagente.sh) || { err "fim-subagente.sh NAO registrado em SubagentStop"; resultado_final "fim-subagente.sh"; }
ok "registrado em SubagentStop: $CMD"
bash -n "$HOOKS_DIR/fim-subagente.sh" && ok "bash -n" || err "bash -n falhou"
[ -x "$HOOKS_DIR/fim-subagente.sh" ] && ok "executavel" || err "sem permissao de execucao"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
com_git_e_worktree "$P"
W="$P/.claude/worktrees/w1"
A="$P/.delta-11/ativacoes"
for n in BACK FRONT VAULT; do echo '{}' > "$A/ack-$n.txt"; echo "{\"agente\":\"$n\",\"status\":\"ativo\"}" > "$A/pulso-$n.json"; done
cat > "$A/agentes-sessao.json" <<JSON
{"versao":1,"chaves":{"agente:AG1":{"agente":"BACK","session_id":"S1","agent_id":"AG1","visto_em":"2099-01-01T00:00:00Z","encerrado_em":null}}}
JSON

rodar "$P" "$W" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"AG1","agent_type":"general-purpose","cwd":"'"$W"'","stop_hook_active":false,"agent_transcript_path":"/nao/existe.jsonl","last_assistant_message":"T-007 pronta: 3 rotas e testes"}'
[ "$CODIGO" = "0" ] && ok "exit 0 (codigo 2 impediria o sub-agente de terminar)" || err "exit=$CODIGO"
LOGS="$P/.delta-11/logs/sub-agentes"
ARQ=$(ls "$LOGS" 2>/dev/null | grep -E '^[0-9]{8}T[0-9]{6}Z-general-purpose\.log$' | head -1)
[ -n "$ARQ" ] && ok "log D32 na PASTA PRINCIPAL: $ARQ" || err "log D32 ausente em $LOGS"
[ ! -d "$W/.delta-11/logs" ] && ok "nada gravado dentro da worktree" || err "log gravado na worktree"
if [ -n "$ARQ" ]; then
    grep -q '^agent_id: AG1$' "$LOGS/$ARQ" && grep -q '^agente_delta11: BACK$' "$LOGS/$ARQ" && ok "log tem agent_id e agente Delta-11" || err "log sem agent_id/agente"
    grep -q 'T-007 pronta: 3 rotas e testes' "$LOGS/$ARQ" && ok "log tem a ultima mensagem" || err "log sem a ultima mensagem"
fi
[ ! -f "$A/ack-BACK.txt" ] && [ ! -f "$A/pulso-BACK.json" ] && ok "ACK e pulso do BACK apagados" || err "ACK/pulso do BACK ficaram"
[ -f "$A/ack-FRONT.txt" ] && [ -f "$A/pulso-FRONT.json" ] && ok "sinais de outro agente intactos" || err "apagou sinal de outro agente"
grep -q '"FRONT"' "$P/.delta-11/pulsos-data.js" && ! grep -q '"BACK"' "$P/.delta-11/pulsos-data.js" && ok "pulsos-data.js regenerado sem o BACK" || err "pulsos-data.js desatualizado"
[ ! -f "$A/morte-BACK.json" ] && ok "terminar nao e morrer: sem registro de morte" || err "gravou morte para sub-agente que terminou normalmente"
python3 -c 'import json,sys; v=json.load(open(sys.argv[1]))["chaves"]["agente:AG1"]; assert v["encerrado_por"]=="SubagentStop"' "$A/agentes-sessao.json" \
    && ok "vinculo marcado como encerrado (nao apagado: release-locks roda em paralelo)" || err "vinculo nao marcado"

# Sem vínculo: identificado pelo operativo citado na primeira mensagem da transcrição
printf '{"type":"user","message":{"content":"Voce e o VAULT. Leia .delta-11/operativos/VAULT.md e rode .delta-11/sub-agentes/contract-tester.md"}}\n' > "$P/transcricao.jsonl"
rodar "$P" "$P" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"AG3","agent_type":"general-purpose","cwd":"'"$P"'","agent_transcript_path":"'"$P"'/transcricao.jsonl","last_assistant_message":"ok"}'
[ ! -f "$A/ack-VAULT.txt" ] && ok "sem vinculo: VAULT identificado pela transcricao e limpo" || err "transcricao nao usada"
grep -rq '^subagente_detectado: contract-tester$' "$LOGS" && ok "log anota o sub-agente detectado (contract-tester)" || err "sub-agente nao detectado"

# Sub-agente que não é Delta-11 (ex.: Explore): só registra, não apaga nada
rodar "$P" "$P" "$CMD" '{"hook_event_name":"SubagentStop","session_id":"S1","agent_id":"X1","agent_type":"Explore","cwd":"'"$P"'","last_assistant_message":"achei"}'
ls "$LOGS" | grep -q -- '-Explore\.log$' && ok "sub-agente generico: log gravado" || err "log do Explore ausente"
[ -f "$A/ack-FRONT.txt" ] && ok "sub-agente generico: nao apaga ACK de ninguem" || err "apagou ACK sem identificar"

resultado_final "fim-subagente.sh"
