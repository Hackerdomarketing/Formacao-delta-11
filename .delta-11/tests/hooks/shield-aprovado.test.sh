#!/usr/bin/env bash
# Teste do vigia shield-aprovado.py (v6.3 — C-039, D11, D33)
source "$(dirname "$0")/_ajudante-hooks-python.sh" shield-aprovado
checagens_basicas

novo_projeto
LOG="$TEST_DIR/.delta-11/activity-log.md"
BASE=$'# Kanban\n## FAZENDO\n**T-012** — rota | Agente: BACK\n**T-020** — tela | Agente: PIXEL\n**T-030** — teste | Agente: SHIELD'
kanban "$BASE"
conclui() { evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md "tool_input.old_string=**$1** — $2 | Agente: $3" "tool_input.new_string=**$1** — $2 | Por: $3 | CONCLUÍDO"; }
AGORA=$(agora_iso)

espera 2 "BACK sem aprovacao do SHIELD: bloqueia" "$(conclui T-012 rota BACK)"
echo "- [$AGORA] [SHIELD] REPROVADO T-012 [BACK] faltou validar entrada" >> "$LOG"
espera 2 "REPROVADO nao vale como aprovacao (C-039)" "$(conclui T-012 rota BACK)"
stderr_contem "REPROVOU"
echo "- [$AGORA] [SHIELD] APROVADO T-012 [BACK]" >> "$LOG"
espera 0 "APROVADO T-012 [BACK]: passa" "$(conclui T-012 rota BACK)"
echo "- [$AGORA] [SHIELD] REPROVADO T-012 [BACK] regressao" >> "$LOG"
espera 2 "reprovacao DEPOIS da aprovacao: vale a ultima decisao" "$(conclui T-012 rota BACK)"

espera 2 "PIXEL tambem exige SHIELD (D11)" "$(conclui T-020 tela PIXEL)"
echo "- [$AGORA] [SHIELD] APROVADO T-999 [PIXEL]" >> "$LOG"
espera 2 "aprovacao de OUTRA tarefa nao vale" "$(conclui T-020 tela PIXEL)"
echo "- [$(horas_atras 5)] [SHIELD] APROVADO T-020 [PIXEL]" >> "$LOG"
espera 2 "aprovacao de 5 h atras (pelo horario da linha): fora da janela" "$(conclui T-020 tela PIXEL)"
echo "[SHIELD] APROVADO T-020 [PIXEL]" >> "$LOG"
espera 2 "aprovacao sem horario nao conta" "$(conclui T-020 tela PIXEL)"
echo "- [$AGORA] [SHIELD] APROVADO T-020 [PIXEL]" >> "$LOG"
espera 0 "aprovacao recente de T-020 [PIXEL]: passa" "$(conclui T-020 tela PIXEL)"
espera 0 "tarefa do proprio SHIELD: isenta" "$(conclui T-030 teste SHIELD)"
fim
