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

# Trilho leve (v6.4.1): [AJUSTE] aprovado pelo COMANDANTE + VISUAL-OK do vigia trilho-leve, sem SHIELD
kanban $'# Kanban\n## FAZENDO\n**T-271** — [AJUSTE] colunas | Agente: FRONT'
conclui_ajuste() { evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md "tool_input.old_string=**T-271** — [AJUSTE] colunas | Agente: FRONT" "tool_input.new_string=**T-271** — [AJUSTE] colunas | Por: FRONT | CONCLUÍDO"; }
espera 2 "[AJUSTE] sem nenhuma prova: bloqueia" "$(conclui_ajuste)"
stderr_contem "COMANDANTE"
echo "- [$AGORA] [trilho-leve] [CRONOS] VISUAL-OK T-271 branch x (1 arquivo(s), so visuais)" >> "$LOG"
espera 2 "[AJUSTE] com VISUAL-OK mas sem o comandante: bloqueia" "$(conclui_ajuste)"
echo "- [$AGORA] [COMANDANTE] APROVADO T-271" >> "$LOG"
espera 0 "[AJUSTE] com VISUAL-OK + comandante APROVADO: passa sem SHIELD" "$(conclui_ajuste)"
log_contem "shield-aprovado.*trilho leve"
echo "- [$AGORA] [COMANDANTE] REPROVADO T-271 ainda largo" >> "$LOG"
espera 2 "comandante REPROVOU depois: vale a ultima decisao" "$(conclui_ajuste)"
kanban $'# Kanban\n## FAZENDO\n**T-280** — colunas | Agente: FRONT'
echo "- [$AGORA] [COMANDANTE] APROVADO T-280" >> "$LOG"
espera 2 "SEM a marca [AJUSTE] a aprovacao do comandante nao substitui o SHIELD" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md "tool_input.old_string=**T-280** — colunas | Agente: FRONT" "tool_input.new_string=**T-280** — colunas | Por: FRONT | CONCLUÍDO")"
fim
