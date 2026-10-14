#!/usr/bin/env bash
# Teste do vigia 3-tentativas-shield.py (v6.3 — C-018, C-002, D23, D35)
source "$(dirname "$0")/_ajudante-hooks-python.sh" 3-tentativas-shield
checagens_basicas

FALHAS=".delta-11/logs/sub-agentes/shield-falhas.log"
disparo() { evento hook_event_name=PreToolUse tool_name=Agent "tool_input.name=$1" "tool_input.description=onda" "tool_input.prompt=Agente: ${2:-X}"; }

novo_projeto
espera 0 "sem log de falhas: disparar BACK passa" "$(disparo back-onda-1)"

AGORA=$(agora_iso)
printf '[%s] [BACK] FAIL T-010 teste vermelho\n[%s] [BACK] FAIL T-010 de novo\n' "$AGORA" "$AGORA" > "$FALHAS"
espera 0 "2 falhas de BACK: ainda passa" "$(disparo back-onda-1)"

printf '[%s] [BACK] FAIL T-010 terceira\n' "$AGORA" >> "$FALHAS"
espera 2 "3 falhas de BACK (formato D35): bloqueia redisparo de BACK" "$(disparo back-onda-2)"
stderr_contem "SCOUT NOVO"
log_contem '^- \[[0-9T:Z-]+\] \[3-tentativas-shield\] \[[A-Z]+\] BLOQUEIO'
espera 0 "SCOUT novo pode ser disparado (D23)" "$(disparo scout-onda-1)"
espera 0 "sub-agente nao e bloqueado" "$(evento tool_name=Agent tool_input.description=build-validator tool_input.prompt=roda)"
espera 0 "Edit nao e alvo deste vigia" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/a.ts tool_input.old_string=a tool_input.new_string=b)"

# Formato antigo "[TS] [SHIELD] [AGENTE] FAIL" nao conta como falha "do SHIELD" (C-018)
novo_projeto
printf '%s\n' "[$AGORA] [SHIELD] [FRONT] FAIL T-1 a" "[$AGORA] [SHIELD] [FRONT] FAIL T-1 b" "[$AGORA] [SHIELD] [FRONT] FAIL T-1 c" > "$FALHAS"
espera 2 "formato antigo com [SHIELD]: atribui a FRONT" "$(disparo front-onda-3)"
espera 0 "SHIELD nao fica travado pelas falhas dos outros" "$(disparo shield-revisao)"

# Linhas sem horario e falhas antigas nao contam
novo_projeto
VELHO=$(horas_atras 5)
printf '%s\n' "[BACK] FAIL T-1 sem hora" "[BACK] FAIL T-1 sem hora" "[$VELHO] [BACK] FAIL T-1 antiga" "[$VELHO] [BACK] FAIL T-1 antiga" "[$AGORA] [BACK] FAIL T-1 nova" > "$FALHAS"
espera 0 "sem horario ou fora da janela de 4 h: nao contam" "$(disparo back-onda-1)"

# Aprovacao do SHIELD depois das falhas zera a contagem (D33)
novo_projeto
ANTES=$(horas_atras 1)
printf '%s\n' "[$ANTES] [BACK] FAIL T-1 a" "[$ANTES] [BACK] FAIL T-1 b" "[$ANTES] [BACK] FAIL T-1 c" > "$FALHAS"
echo "- [$AGORA] [SHIELD] APROVADO T-1 [BACK]" >> .delta-11/activity-log.md
espera 0 "APROVADO depois das falhas libera BACK" "$(disparo back-onda-1)"

# SCOUT so trava com 6 falhas no total (D23 -> ATLAS)
novo_projeto
for i in 1 2 3 4 5; do echo "[$AGORA] [SCOUT] FAIL T-2 tentativa $i" >> "$FALHAS"; done
espera 0 "SCOUT com 5 falhas: CRONOS ainda pode disparar SCOUT novo" "$(disparo scout-onda-2)"
echo "[$AGORA] [SCOUT] FAIL T-2 tentativa 6" >> "$FALHAS"
espera 2 "SCOUT com 6 falhas: bloqueia (hora do ATLAS)" "$(disparo scout-onda-3)"
stderr_contem "ATLAS"

# SessionStart: so avisa, exit 0, com additionalContext
novo_projeto
printf '%s\n' "[$AGORA] [VAULT] FAIL T-3 a" "[$AGORA] [VAULT] FAIL T-3 b" "[$AGORA] [VAULT] FAIL T-3 c" > "$FALHAS"
espera 0 "SessionStart nunca bloqueia" "$(evento hook_event_name=SessionStart source=startup)"
if printf '%s' "$SAIDA_PADRAO" | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'VAULT' in d['hookSpecificOutput']['additionalContext']"; then ok "SessionStart devolve additionalContext citando VAULT"; else err "SessionStart sem additionalContext"; fi
novo_projeto
espera 0 "SessionStart sem falhas: silencioso" "$(evento hook_event_name=SessionStart source=startup)"
if [ -z "$SAIDA_PADRAO" ]; then ok "nada no stdout"; else err "stdout inesperado: $SAIDA_PADRAO"; fi

# Erro interno: exit 1 + ERRO-INTERNO no log (C-016)
novo_projeto
espera 1 "JSON quebrado vira erro interno visivel (exit 1)" "{quebrado"
log_contem "ERRO-INTERNO"

fim
