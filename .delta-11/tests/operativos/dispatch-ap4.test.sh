#!/usr/bin/env bash
# Teste de regressão: AP#4 — CHECKPOINTS DE APROVAÇÃO manuais foram
# reduzidos de 3 para 0 (decisão de produto ja capturada no PLAN;
# Selo Experiencial e' o unico gate humano de fase). CRONOS
# auto-dispatcha sem pausar para perguntar.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRONOS="$SCRIPT_DIR/../../operativos/CRONOS.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

# 1. CRONOS.md NAO pode ter "CHECKPOINTS DE APROVAÇÃO COM O COMANDANTE"
if grep -qF "CHECKPOINTS DE APROVAÇÃO COM O COMANDANTE" "$CRONOS"; then
    err "CRONOS.md ainda tem secao 'CHECKPOINTS DE APROVAÇÃO COM O COMANDANTE'"
else
    ok "CRONOS.md NAO tem 'CHECKPOINTS DE APROVAÇÃO COM O COMANDANTE'"
fi

# 2. CRONOS.md NAO pode conter "Posso prosseguir" como pergunta bloqueante
if grep -qE 'Diga:.*"[^"]*Posso prosseguir' "$CRONOS"; then
    err "CRONOS.md ainda tem perguntas bloqueantes 'Posso prosseguir'"
else
    ok "CRONOS.md NAO tem perguntas 'Posso prosseguir' bloqueantes"
fi

# 3. CRONOS.md DEVE ter a frase positiva sobre auto-dispatch sem pausar
if grep -qE "Selo.*[Ee]xperiencial.*unico gate|gate humano|autodispatch.*sem pausar|dispatch.*sem pausar" "$CRONOS"; then
    ok "CRONOS.md documenta que auto-dispatch nao pausa para comandante"
else
    err "CRONOS.md NAO documenta auto-dispatch sem pausar"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#4 corrigido (zero CHECKPOINTS bloqueantes)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi