#!/usr/bin/env bash
# Teste de regressão: AP#7 — SCOUT NAO pode instruir humano a copiar prompt
# de retomada. SCOUT envia SendMessage ao CRONOS que dispara Agent tool.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCOUT="$SCRIPT_DIR/../../operativos/SCOUT.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

# 1. SCOUT NAO pode dizer "Entregue ao comandante o bloco de retomada pronto para copiar e colar"
if grep -qF "Entregue ao comandante o bloco de retomada pronto para copiar e colar" "$SCOUT"; then
    err "SCOUT.md ainda instrui 'Entregue ao comandante o bloco...copiar e colar'"
else
    ok "SCOUT.md NAO instrui humano a copiar prompt de retomada"
fi

# 2. SCOUT DEVE ter SendMessage ao CRONOS como caminho para retomada
if grep -qiF "SendMessage" "$SCOUT" && grep -qiF "CRONOS" "$SCOUT"; then
    ok "SCOUT.md usa SendMessage ao CRONOS para retomada"
else
    err "SCOUT.md NAO usa SendMessage ao CRONOS para retomada"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#7 corrigido (SCOUT usa SendMessage)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi