#!/usr/bin/env bash
# Teste do vigia anti-autocompact.py (v6.3 — C-019, C-181)
# Mede o contexto REAL pelo `usage` da ultima resposta na conversa (transcript_path).
source "$(dirname "$0")/_ajudante-hooks-python.sh" anti-autocompact
checagens_basicas
if grep -q "transcript_path" "$HOOK"; then ok "le o transcript_path do evento (C-019)"; else err "nao le transcript_path"; fi

# conversa(arquivo, tokens): grava uma conversa JSONL cuja ultima resposta usou N tokens
conversa() {
    python3 - "$1" "$2" <<'PY'
import json, sys
caminho, tokens = sys.argv[1], int(sys.argv[2])
with open(caminho, "w") as f:
    f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "oi"}}) + "\n")
    f.write(json.dumps({"type": "assistant", "message": {"usage": {"input_tokens": 10, "cache_read_input_tokens": 5}}}) + "\n")
    f.write(json.dumps({"type": "assistant", "message": {"usage": {"input_tokens": 1000, "cache_read_input_tokens": tokens - 1000, "cache_creation_input_tokens": 0, "output_tokens": 50}}}) + "\n")
PY
}

novo_projeto
SESSAO="$TEST_DIR/conversas/sessao-teste.jsonl"
mkdir -p "$TEST_DIR/conversas/sessao-teste/subagents"
SUB="$TEST_DIR/conversas/sessao-teste/subagents/agent-ag1.jsonl"
CODIGO="$TEST_DIR/src/app.ts"
ev_sub() { evento tool_name="$1" "transcript_path=$SESSAO" agent_id=ag1 agent_type=general-purpose "${@:2}"; }

conversa "$SESSAO" 50000
conversa "$SUB" 50000
espera 0 "sub-agente com 50 mil tokens: passa" "$(ev_sub Edit tool_input.file_path=$CODIGO tool_input.old_string=a tool_input.new_string=b)"

conversa "$SUB" 900000
espera 2 "sub-agente com 900 mil tokens (>85% de 1 milhao): bloqueia Edit de codigo" "$(ev_sub Edit tool_input.file_path=$CODIGO tool_input.old_string=a tool_input.new_string=b)"
stderr_contem "SendMessage"
espera 2 "...e bloqueia Bash" "$(ev_sub Bash tool_input.command=ls)"
espera 0 "...mas deixa gravar o produto.md (salvar o estado)" "$(ev_sub Write tool_input.file_path=$TEST_DIR/.delta-11/memoria/BACK-produto.md tool_input.content=estado)"
espera 0 "...e deixa disparar a retomada (Agent)" "$(ev_sub Agent tool_input.name=cronos tool_input.prompt=retomar)"

# Um texto GIGANTE numa unica acao nao e mais o criterio (C-019)
conversa "$SUB" 20000
GRANDE="$TEST_DIR/grande.txt"; python3 -c "print('x'*800000)" > "$GRANDE"
espera 0 "conteudo de 800 mil caracteres com contexto pequeno: passa" "$(ev_sub Write tool_input.file_path=$CODIGO tool_input.content=@$GRANDE)"

# A medicao e a do PROPRIO sub-agente, nao a da sessao principal
conversa "$SESSAO" 900000
conversa "$SUB" 30000
espera 0 "sessao principal cheia nao trava o sub-agente com contexto pequeno" "$(ev_sub Bash tool_input.command=ls)"

# Sub-agente cuja conversa nao foi achada: nao mede, nao bloqueia
espera 0 "sem conversa do sub-agente: libera" "$(evento tool_name=Bash transcript_path=$SESSAO agent_id=desconhecido tool_input.command=ls)"

# Sessao principal (sem agent_id) so registra AVISO
espera 0 "sessao principal com 900 mil: nao bloqueia o comandante" "$(evento tool_name=Bash transcript_path=$SESSAO tool_input.command=ls)"
log_contem "\[anti-autocompact\] \[MAIN\] AVISO"

# Janela de 1 milhao: uso acima de 200 mil prova janela grande
conversa "$SUB" 400000
espera 0 "400 mil tokens num modelo de 1 milhao: passa" "$(ev_sub Bash tool_input.command=ls)"
conversa "$SUB" 900000
espera 2 "900 mil tokens num modelo de 1 milhao: bloqueia" "$(ev_sub Bash tool_input.command=ls)"

# Limite configuravel (.config-limites.json — D36)
conversa "$SUB" 600000
echo '{"contexto_alerta_pct": 50}' > .delta-11/.config-limites.json
espera 2 "contexto_alerta_pct=50 no .config-limites.json: 600 mil ja bloqueia" "$(ev_sub Bash tool_input.command=ls)"

# v6.4.1 — UMA janela para todos (1 milhao): sem lista de modelos (decisao do comandante)
conversa_modelo() {  # $1 arquivo, $2 tokens, $3 modelo
    python3 - "$1" "$2" "$3" <<'PY'
import json, sys
caminho, tokens, modelo = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(caminho, "w") as f:
    f.write(json.dumps({"type": "assistant", "message": {"model": modelo, "usage": {"input_tokens": 1000, "cache_read_input_tokens": tokens - 1000}}}) + "\n")
PY
}
rm -f .delta-11/.config-limites.json
conversa_modelo "$SUB" 180000 claude-sonnet-5-5
espera 0 "sonnet-5-5 com 180 mil (janela de 1 milhao): passa — fim do laco de retomadas" "$(ev_sub Bash tool_input.command=ls)"
conversa_modelo "$SUB" 180000 claude-opus-5-5
espera 0 "opus-5-5 com 180 mil: passa" "$(ev_sub Bash tool_input.command=ls)"
conversa_modelo "$SUB" 860000 claude-sonnet-5-5
espera 2 "sonnet-5-5 com 860 mil (>85% de 1 milhao): bloqueia" "$(ev_sub Bash tool_input.command=ls)"
stderr_contem "modelo claude-sonnet-5-5"
conversa_modelo "$SUB" 180000 claude-haiku-5-5
espera 0 "qualquer modelo com 180 mil (sem lista de modelos): passa" "$(ev_sub Bash tool_input.command=ls)"
conversa_modelo "$SUB" 180000 modelo-desconhecido-x
espera 0 "modelo NOVO que nao existia quando o vigia foi escrito, 180 mil: passa" "$(ev_sub Bash tool_input.command=ls)"
echo '{"contexto_janela_tokens": 200000}' > .delta-11/.config-limites.json
conversa_modelo "$SUB" 180000 claude-sonnet-5-5
espera 2 "projeto FORCA 200 mil no .config-limites.json: vale o projeto, bloqueia" "$(ev_sub Bash tool_input.command=ls)"
rm -f .delta-11/.config-limites.json

espera 0 "evento vazio: passa" ""
fim
