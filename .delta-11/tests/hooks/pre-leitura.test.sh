#!/usr/bin/env bash
# Teste do vigia pre-leitura.py (v6.3 — D6, C-035, C-130)
source "$(dirname "$0")/_ajudante-hooks-python.sh" pre-leitura
checagens_basicas

novo_projeto
A="$TEST_DIR/.delta-11/ativacoes"
PC="$TEST_DIR/.delta-11/memoria/project-core.md"
vinculos() { # vinculos "agente:ag1=BACK" "principal:sessao-teste=ATLAS" ...
    python3 - "$A/agentes-sessao.json" "$@" <<'PY'
import json, sys
chaves = {}
for par in sys.argv[2:]:
    chave, nome = par.split("=")
    chaves[chave] = {"agente": nome, "visto_em": "2026-10-14T10:00:00Z", "encerrado_em": None}
json.dump({"versao": 1, "chaves": chaves}, open(sys.argv[1], "w"))
PY
}
le() { evento tool_name=Read "tool_input.file_path=$1" "${@:2}"; }

vinculos "agente:ag-back=BACK" "agente:ag-shield=SHIELD" "principal:sessao-teste=ATLAS"
echo ok > "$A/ack-BACK.txt"
espera 2 "BACK (vinculo do agent_id) le o project-core inteiro: bloqueia" "$(le "$PC" agent_id=ag-back agent_type=general-purpose)"
stderr_contem "FATIAS"
espera 0 "BACK le a fatia project-core/contratos.md: passa" "$(le "$TEST_DIR/.delta-11/memoria/project-core/contratos.md" agent_id=ag-back agent_type=general-purpose)"
espera 0 "BACK le outro arquivo: passa" "$(le "$TEST_DIR/src/a.ts" agent_id=ag-back)"
espera 0 "SHIELD pode ler o project-core inteiro (D6)" "$(le "$PC" agent_id=ag-shield agent_type=general-purpose)"
espera 0 "ATLAS na sessao principal: passa mesmo com o ACK do BACK sendo o mais recente (C-035)" "$(le "$PC")"
espera 2 "caminho relativo tambem e vigiado" "$(le ".delta-11/memoria/project-core.md" agent_id=ag-back)"
espera 0 "sub-agente pelo agent_type (qa-ui-tandem): passa" "$(le "$PC" agent_id=ag-x agent_type=qa-ui-tandem)"
espera 2 "agent_type ja com nome Delta-11 (VAULT): bloqueia" "$(le "$PC" agent_id=ag-v agent_type=VAULT)"

# Sem vinculo: o ACK mais recente, ignorando agentes vinculados a outra sessao (D28)
novo_projeto
A="$TEST_DIR/.delta-11/ativacoes"
PC="$TEST_DIR/.delta-11/memoria/project-core.md"
echo ok > "$A/ack-FORM.txt"
espera 2 "sem vinculo: ACK mais recente (FORM) e usado" "$(le "$PC" agent_id=ag-novo)"
vinculos "agente:ag-form=FORM"
espera 0 "FORM vinculado a outro sub-agente: o ACK dele nao identifica este (sem identificacao = libera)" "$(le "$PC" agent_id=ag-novo)"
log_contem "sem agente identificado"
fim
