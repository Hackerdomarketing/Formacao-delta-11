#!/usr/bin/env bash
# Teste do vigia brief-preservado.py (v6.3 — C-003, C-021). Registrado em PostToolUse.
source "$(dirname "$0")/_ajudante-hooks-python.sh" brief-preservado
checagens_basicas
if grep -q "PostToolUse" "$HOOK"; then ok "documenta PostToolUse"; else err "nao documenta PostToolUse"; fi

novo_projeto
BRIEF="$TEST_DIR/.delta-11/ativacoes/BACK-onda-2.txt"
python3 -c "print('Brief do BACK: implementar a rota de pedidos. ' * 40)" > "$BRIEF"
post() { evento hook_event_name=PostToolUse "$@"; }

espera 0 "brief novo: registra INFO, exit 0" "$(post tool_name=Write tool_input.file_path=$BRIEF tool_input.content=x)"
log_contem "\[brief-preservado\] \[MAIN\] INFO: brief registrado"

# Edit pequeno (trecho curto) com o arquivo final grande: NAO e alerta (C-021)
echo " mais uma linha" >> "$BRIEF"
espera 0 "Edit de um trecho curto: compara o arquivo salvo inteiro" "$(post tool_name=Edit tool_input.file_path=$BRIEF tool_input.old_string=a tool_input.new_string=b)"
if grep -q "ALERTA" .delta-11/activity-log.md; then err "ALERTA falso num Edit pequeno"; else ok "sem ALERTA falso num Edit pequeno"; fi

# Sobrescrita destrutiva: o arquivo salvo encolheu mais de 50 %
echo "curto" > "$BRIEF"
espera 0 "brief encolheu >50%: exit 0 (so informa)" "$(post tool_name=Write tool_input.file_path=$BRIEF tool_input.content=curto)"
log_contem "ALERTA: brief encolheu"

# Exclusao por Bash (rm) e detectada
rm -f "$BRIEF"
espera 0 "rm do brief via Bash: exit 0" "$(post tool_name=Bash 'tool_input.command=rm .delta-11/ativacoes/BACK-onda-2.txt')"
log_contem "ALERTA: brief APAGADO"

# Arquivos de sinal nao sao briefs
espera 0 "ack-*.txt nao e brief" "$(post tool_name=Write tool_input.file_path=$TEST_DIR/.delta-11/ativacoes/ack-BACK.txt tool_input.content=ok)"
if grep -q "ack-BACK" .delta-11/activity-log.md; then err "ack tratado como brief"; else ok "ack ignorado"; fi
espera 0 "arquivo fora de ativacoes: ignora" "$(post tool_name=Write tool_input.file_path=$TEST_DIR/src/a.txt tool_input.content=x)"
fim
