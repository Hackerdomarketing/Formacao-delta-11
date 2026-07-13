#!/usr/bin/env bash
# Teste de regressão: AP#5 — anti-padrão "Gere prompt do SHIELD em arquivo"
# deve ter sido REMOVIDO dos 7 operativos (BACK, ENGINE, FORM, FRONT, PIXEL, SCOUT, VAULT).
#
# Substituído por: SendMessage ao CRONOS que dispara SHIELD via Agent tool.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPERATIVOS_DIR="$SCRIPT_DIR/../../operativos"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

OPERATIVOS_EXECUTORES=("BACK" "ENGINE" "FORM" "FRONT" "PIXEL" "SCOUT" "VAULT")

# 1. Cada operativo NAO pode conter "Gere prompt do SHIELD"
for agente in "${OPERATIVOS_EXECUTORES[@]}"; do
    file="$OPERATIVOS_DIR/$agente.md"
    if [ ! -f "$file" ]; then
        err "$file NAO existe"
        continue
    fi
    if grep -qF "Gere prompt do SHIELD em \`.delta-11/ativacoes/janela-SHIELD" "$file"; then
        err "$agente.md ainda contem 'Gere prompt do SHIELD' (anti-padrao AP#5)"
    else
        ok "$agente.md NAO contem anti-padrao 'Gere prompt do SHIELD'"
    fi
done

# 2. Cada operativo DEVE conter SendMessage ao CRONOS (caminho correto)
for agente in "${OPERATIVOS_EXECUTORES[@]}"; do
    file="$OPERATIVOS_DIR/$agente.md"
    if [ ! -f "$file" ]; then
        continue
    fi
    # Procura tanto SendMessage quanto mencao a CRONOS no contexto de revisao
    if grep -qiF "SendMessage" "$file" && grep -qiF "CRONOS" "$file"; then
        ok "$agente.md mantem SendMessage ao CRONOS (caminho correto)"
    else
        err "$agente.md NAO menciona SendMessage ao CRONOS — caminho correto ausente"
    fi
done

# 3. Verifica que o numero de arquivos "janela-SHIELD-revisao-*.txt" no operativos
# eh ZERO (nenhum operativo deve instruir criacao desse arquivo)
total_ocorrencias=0
for agente in "${OPERATIVOS_EXECUTORES[@]}"; do
    file="$OPERATIVOS_DIR/$agente.md"
    if [ -f "$file" ]; then
        c=$(grep -cF "janela-SHIELD-revisao-" "$file" || true)
        total_ocorrencias=$((total_ocorrencias + c))
    fi
done
if [ "$total_ocorrencias" -eq 0 ]; then
    ok "ZERO ocorrencias de 'janela-SHIELD-revisao-' em todos os 7 operativos"
else
    err "encontradas $total_ocorrencias ocorrencias de 'janela-SHIELD-revisao-' (devia ser 0)"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#5 corrigido (zero anti-padroes 'humano-colar-prompt' nos 7 operativos)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi