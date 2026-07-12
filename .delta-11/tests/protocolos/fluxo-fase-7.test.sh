#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da Etapa 2C do v6.0 — Fluxo com Fase 7 (Descanso/Consagracao)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o protocolo de fluxo-zero-ao-lancamento.md declara:
#   1. Cabecalho 'FASE 7' existe APOS a Fase 6
#   2. Nomeada com termo do Dia 7 (descanso/consagracao/autonoma)
#   3. Quem faz
#   4. Janela estimada
#   5. Resultado esperado
#   6. 10 entregaveis: docs tecnica+dominio, testes E2E, deploy
#      automatizado, runbooks, monitoramento+alertas, tag de release,
#      backup testado, DR testado, onboarding testado, teste supremo
#   7. O TESTE SUPREMO (criador tira ferias e sistema continua) e
#      obrigatorio como criterio de selo
#   8. ORDEM: 7 vem APOS a Fase 6
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/fluxo-zero-ao-lancamento.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ ! -f "$DOC" ]; then
    echo "fluxo-zero-ao-lancamento.md AUSENTE em $DOC"
    exit 1
fi

# 1. Cabecalho
if grep -qE "^### FASE 7 " "$DOC"; then
    ok "cabecalho 'FASE 7' presente"
else
    err "cabecalho 'FASE 7' AUSENTE — Dia 7 nao existe no fluxo"
fi

# 2. Nomeada com termo do Dia 7
if grep -E "^### FASE 7 " "$DOC" | grep -qi "descanso\|consagração\|autônoma\|autonoma"; then
    ok "Fase 7 nomeada com termo do Dia 7 (descanso/consagracao)"
else
    err "Fase 7 NAO nomeada com termo do Dia 7 — confusao conceitual"
fi

# 3. Quem faz
if grep -A40 "^### FASE 7 " "$DOC" | grep -qiF "Quem"; then
    ok "Fase 7 declara quem faz"
else
    err "Fase 7 NAO declara quem faz"
fi

# 4. Janela
if grep -A40 "^### FASE 7 " "$DOC" | grep -qiF "Janela"; then
    ok "Fase 7 declara janela"
else
    err "Fase 7 NAO declara janela"
fi

# 5. Resultado
if grep -A60 "^### FASE 7 " "$DOC" | grep -qF "**Resultado:**"; then
    ok "Fase 7 declara Resultado"
else
    err "Fase 7 NAO declara Resultado"
fi

# 6. Os 10 entregaveis do Dia 7
entregaveis=(
    "documentação técnica"
    "documentação de domínio"
    "testes de aceitação"
    "deploy automatizado"
    "runbook"
    "alertas"
    "tag de release"
    "backup testado"
    "DR testado"
    "onboarding"
)
for ent in "${entregaveis[@]}"; do
    if grep -A60 "^### FASE 7 " "$DOC" | grep -qiF "$ent"; then
        ok "Fase 7 menciona entregavel '$ent'"
    else
        err "Fase 7 NAO menciona entregavel '$ent'"
    fi
done

# 7. TESTE SUPREMO (criador tira ferias, sistema continua)
if grep -A60 "^### FASE 7 " "$DOC" | grep -qiE "teste supremo|férias|2 semanas"; then
    ok "Fase 7 menciona o teste supremo (operacao autonoma)"
else
    err "Fase 7 NAO menciona teste supremo — selo fica incompleto"
fi

# 8. ORDEM — Fase 7 APOS Fase 6
pos_7=$(grep -nE "^### FASE 7 " "$DOC" | head -1 | cut -d: -f1 || echo "0")
pos_6=$(grep -nE "^### FASE 6 " "$DOC" | head -1 | cut -d: -f1 || echo "999")

if [ "$pos_7" = "0" ]; then
    err "Fase 7 AUSENTE"
elif [ "$pos_6" = "999" ]; then
    err "Fase 6 AUSENTE — impossivel verificar ordem"
elif [ "$pos_6" -lt "$pos_7" ]; then
    ok "Fase 7 (linha $pos_7) vem APOS Fase 6 (linha $pos_6) — ordem correta"
else
    err "ORDEM ERRADA — Fase 6 (linha $pos_6) / Fase 7 (linha $pos_7). Esperado: 6 < 7"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Fase 7 (Descanso/Consagracao) integra o fluxo corretamente${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) — corrigir antes de prosseguir${NC}"
    exit 1
fi