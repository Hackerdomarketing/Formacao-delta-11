#!/usr/bin/env bash
# Teste do template fase-descanso-template.md (Etapa 7B do v6.0)

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../../templates/fase-descanso-template.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$TEMPLATE" ]; then
    ok "template existe em .delta-11/templates/fase-descanso-template.md"
else
    err "template AUSENTE"; exit 1
fi

# Cobre os 10 entregaveis
entregaveis=(
    "doc.*t[ée]cnica"
    "doc.*dom"
    "(E2E|aceita)"
    "deploy automatizado"
    "runbook"
    "alerta"
    "tag de release"
    "backup testado"
    "DR testado"
    "onboarding"
)
cobertos=0
for ent in "${entregaveis[@]}"; do
    if grep -qiE "$ent" "$TEMPLATE"; then cobertos=$((cobertos + 1)); fi
done
if [ "$cobertos" -ge 10 ]; then
    ok "10 entregaveis cobertos (encontrados $cobertos)"
else
    err "apenas $cobertos entregaveis cobertos (minimo 10)"
fi

# Estrutura canonica
if grep -qE "##\s+.*[Dd]escri[cç][ãa]o" "$TEMPLATE" && \
   grep -qE "##\s+.*[Ee]vid[eê]ncia" "$TEMPLATE"; then
    ok "template tem Descricao + Evidencia (essencial para Dia 7)"
else
    err "template NAO tem Evidencia"
fi

# Cross-reference com protocolo
if grep -qi "fase-descanso\.md\|protocolo" "$TEMPLATE"; then
    ok "cross-reference com protocolo"; else err "sem cross-reference com protocolo"
fi

# Cross-reference com Metodologia
if grep -qi "metodologia-genesis\|Dia 7" "$TEMPLATE"; then
    ok "cross-reference com Metodologia Genesis"; else err "sem cross-reference Metodologia"
fi

# Placeholders editaveis
if grep -qE "\{\{[A-Z_]+\}\}|\[A-Z_+\]" "$TEMPLATE"; then
    ok "placeholders editaveis presentes"; else err "sem placeholders"
fi

# Aviso: NAO avancar sem teste supremo
if grep -qiE "teste supremo|opera[cç][ãa]o aut[ôo]noma" "$TEMPLATE"; then
    ok "template menciona teste supremo"; else err "sem menção a teste supremo"
fi

# Cross-ref com skills globais (runbooks)
if grep -qiE "owasp-top10|07-incident-response" "$TEMPLATE"; then
    ok "cross-reference com skill owasp-top10 (runbooks)"; else err "sem cross-ref runbooks"
fi

# Endereco canonico dos runbooks
if grep -qi "memoria/runbooks" "$TEMPLATE"; then
    ok "endereco canonico dos runbooks"; else err "sem endereco para runbooks"
fi

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — template fase-descanso-template.md${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }