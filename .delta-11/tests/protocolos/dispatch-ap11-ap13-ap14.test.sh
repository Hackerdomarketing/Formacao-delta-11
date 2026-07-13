#!/usr/bin/env bash
# Teste de regressão: AP#11 + AP#13 + AP#14 — vigilante, selo, linguagem
# "rode manualmente" removidos/corrigidos.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$SCRIPT_DIR/../../../"
VIGILANTE="$RAIZ/vigilante.sh"
SELO="$RAIZ/.delta-11/templates/selo-experiencial-template.md"
SHIELD="$RAIZ/.delta-11/operativos/SHIELD.md"
ATLAS="$RAIZ/.delta-11/operativos/ATLAS.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

# AP#11 - vigilante NAO instrui humano a rodar disparar.sh
if grep -qF "rode ./disparar.sh" "$VIGILANTE" 2>/dev/null; then
    err "vigilante.sh ainda diz 'rode ./disparar.sh'"
else
    ok "vigilante.sh NAO diz 'rode ./disparar.sh' (AP#11)"
fi

# AP#13 - selo NAO instrui humano a operar o produto
# (pode aparecer como "removido:" em diff, mas NAO como instrucao ativa)
if grep -E '^[^#-]' "$SELO" | grep -qF "comandante OPERA o produto, não lê relatório"; then
    err "selo-experiencial-template.md ainda instrui humano a operar (fora de comentario de remocao)"
else
    ok "selo-experiencial NAO instrui humano a operar como instrucao ativa (AP#13)"
fi

# AP#13 - selo DEVE mencionar Tandem Browser
if grep -qiF "Tandem" "$SELO"; then
    ok "selo menciona Tandem Browser MCP (AP#13)"
else
    err "selo NAO menciona Tandem Browser"
fi

# AP#14 - "rode manualmente" NAO deve aparecer em SHIELD/ATLAS (linguagem ambigua)
if grep -qF "Rode manualmente:" "$SHIELD"; then
    err "SHIELD.md ainda tem 'Rode manualmente:'"
else
    ok "SHIELD.md NAO tem 'Rode manualmente:' (AP#14)"
fi
if grep -qF "rode manualmente:" "$ATLAS"; then
    err "ATLAS.md ainda tem 'rode manualmente:'"
else
    ok "ATLAS.md NAO tem 'rode manualmente:' (AP#14)"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#11+AP#13+AP#14 corrigidos${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi