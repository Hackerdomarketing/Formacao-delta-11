#!/usr/bin/env bash
# Teste de regressão: AP#2 — Fallback SDK agora tenta 3x antes de
# escalar humano. Humano nao e' mais primeira opcao.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE="$SCRIPT_DIR/../../../CLAUDE.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. CLAUDE.md NAO pode ter "Fallback 1 — Mensagem ao comandante" como primeira opcao
if grep -qF "Fallback 1 — Mensagem ao comandante" "$CLAUDE"; then
    err "CLAUDE.md ainda tem 'Fallback 1 - Mensagem ao comandante' como primeira opcao"
else
    ok "CLAUDE.md NAO tem 'Fallback 1 - Mensagem ao comandante' como primeira opcao"
fi

# 2. CLAUDE.md NAO pode dizer "Fluxo manual mas sempre funciona" como caminho primario
# (pode aparecer em frase de alerta, mas NAO como instrucao principal)
if grep -E '^[0-9]+\.|^\*\*|^- |^> ' "$CLAUDE" | grep -qF "Fluxo manual mas sempre funciona"; then
    err "CLAUDE.md ainda tem 'Fluxo manual mas sempre funciona' como instrucao principal"
else
    ok "CLAUDE.md NAO tem 'Fluxo manual' como instrucao principal (so' como alerta)"
fi

# 3. CLAUDE.md DEVE documentar tentativa de retry antes de escalar humano
if grep -qiE "retry.*3|tentar.*3 vezes|Retry 1|Retry 2|Retry 3|cadeia de retry" "$CLAUDE"; then
    ok "CLAUDE.md documenta retry antes de escalar humano"
else
    err "CLAUDE.md NAO documenta retry antes de escalar humano"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#2 corrigido (retry antes de humano)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi