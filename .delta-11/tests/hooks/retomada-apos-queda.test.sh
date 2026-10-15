#!/usr/bin/env bash
# Teste do vigia retomada-apos-queda.py (v6.4.1): sessao nova avisa o que a sessao anterior deixou "em andamento".
source "$(dirname "$0")/_ajudante-hooks-python.sh" retomada-apos-queda
checagens_basicas

novo_projeto
INICIO=$(evento hook_event_name=SessionStart source=startup)
espera 0 "sem kanban-data nem pulsos: passa calado" "$INICIO"
[ -z "$SAIDA_PADRAO" ] && ok "sem aviso quando nao ha nada pendente" || err "avisou sem motivo"

cat > .delta-11/kanban-data.js <<'JS'
window.KANBAN_DATA = {
  agentes: [
    { agente: "CRONOS", ultima_atividade: "2026-10-15T07:00:00Z", tarefa_atual: "aguardando a revisao conjunta T-258" },
    { agente: "SHIELD", ultima_atividade: "2026-10-15T07:00:00Z", tarefa_atual: "T-258 revisao conjunta" },
    { agente: "FRONT", ultima_atividade: null, tarefa_atual: "" }
  ]
};
JS
printf 'window.D11_PULSOS = {"agentes": {"SHIELD": {"ultimo_sinal": "2026-10-15T07:10:00Z", "status": "ativo"}, "ENGINE": {"ultimo_sinal": null, "status": "descansando"}}};\n' > .delta-11/pulsos-data.js

espera 0 "sessao nova com trabalho marcado como em andamento: nunca bloqueia" "$INICIO"
printf '%s' "$SAIDA_PADRAO" | python3 -c "import json,sys; d=json.load(sys.stdin)['hookSpecificOutput']; assert d['hookEventName']=='SessionStart'" && ok "aviso no formato additionalContext do SessionStart" || err "saida nao e additionalContext valido"
for trecho in "T-258 revisao conjunta" 'SHIELD com status \"ativo\"' "confira o DISCO"; do
    printf '%s' "$SAIDA_PADRAO" | grep -qF -- "$trecho" && ok "aviso cita: $trecho" || err "aviso NAO cita: $trecho"
done
printf '%s' "$SAIDA_PADRAO" | grep -q "FRONT" && err "citou agente sem tarefa" || ok "agente sem tarefa_atual nao aparece"
printf '%s' "$SAIDA_PADRAO" | grep -q "ENGINE" && err "citou agente descansando" || ok "agente descansando nao aparece"
log_contem "retomada-apos-queda.*AVISO SessionStart"

espera 0 "volta da compactacao (source: compact): os agentes continuam vivos, nao avisa" "$(evento hook_event_name=SessionStart source=compact)"
[ -z "$SAIDA_PADRAO" ] && ok "sem aviso na compactacao" || err "avisou na compactacao"
espera 0 "retomar a conversa (source: resume) tambem avisa" "$(evento hook_event_name=SessionStart source=resume)"
[ -n "$SAIDA_PADRAO" ] && ok "avisou no resume" || err "nao avisou no resume"
fim
