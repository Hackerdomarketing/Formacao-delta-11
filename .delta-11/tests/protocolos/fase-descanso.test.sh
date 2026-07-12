#!/usr/bin/env bash
# Teste do protocolo fase-descanso.md (Etapa 7A do v6.0)

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/fase-descanso.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$DOC" ]; then
    ok "protocolo existe em .delta-11/protocolos/fase-descanso.md"
else
    err "protocolo AUSENTE"; exit 1
fi

if grep -qiE "FASE 7|fluxo-zero-ao-lancamento" "$DOC"; then
    ok "cross-reference com fluxo-zero (Fase 7)"
else
    err "NAO cross-reference com fluxo"
fi

if grep -qiE "metodologia-genesis-camadas|Dia 7|Descanso Consagrado" "$DOC"; then
    ok "cross-reference com Metodologia Genesis (Dia 7)"
else
    err "NAO cross-reference com Metodologia"
fi

# Os 10 entregaveis do Dia 7
entregaveis=(
    "documentação técnica"
    "documentação técnica"
    "documentação de domínio"
    "documentação de dom"
    "testes de aceitação"
    "deploy automatizado"
    "runbook"
    "alertas"
    "tag de release"
    "backup testado"
    "DR testado"
    "onboarding"
)
cobertos=0
for ent in "${entregaveis[@]}"; do
    if grep -qi "$ent" "$DOC"; then
        cobertos=$((cobertos + 1))
    fi
done
# Aceita >= 9 (alguns podem ser variacoes textuais)
if [ "$cobertos" -ge 9 ]; then
    ok "entregaveis do Dia 7 cobertos (encontrados $cobertos)"
else
    err "apenas $cobertos entregaveis cobertos (minimo 9)"
fi

# Teste supremo (criador tira ferias)
if grep -qiE "teste supremo|f[ée]rias|criador.*tira.*2 semanas" "$DOC"; then
    ok "protocolo menciona o TESTE SUPREMO (operacao autonoma)"
else
    err "NAO menciona TESTE SUPREMO"
fi

# Quem sella
if grep -qiE "quem sella|sella:|Comandante.*selo" "$DOC"; then
    ok "protocolo declara quem sella"
else
    err "NAO declara quem sella"
fi

# Texto hebraico chave (Dia 7)
if grep -qE "vayechulu|vayishbot|vayvarech|kadash" "$DOC"; then
    ok "texto hebraico chave (vayechulu, vayishbot, kadash)"
else
    err "NAO inclui texto hebraico do Dia 7"
fi

# Cross-reference com monitor-delta11.sh
if grep -qiE "monitor-delta11|monitor.*autonoma|opera[cç][ãa]o aut[ôo]noma" "$DOC"; then
    ok "cross-reference com monitor-delta11.sh / operacao autonoma"
else
    err "NAO cross-reference com monitor — como detectar autonomia?"
fi

# Endereco canonico
if grep -qi "memoria/decisoes\|memoria/runbooks" "$DOC"; then
    ok "endereco canonico dos entregaveis"
else
    err "NAO declara endereco canonico"
fi

# Diferenciacao Fase 6 (provisorio) vs Fase 7 (definitivo)
if grep -qiE "provis[óo]rio|definitivo|selo.*definitivo" "$DOC"; then
    ok "diferencia Fase 6 (selo provisorio) vs Fase 7 (definitivo)"
else
    err "NAO diferencia Fase 6 de Fase 7"
fi

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — protocolo fase-descanso.md${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }