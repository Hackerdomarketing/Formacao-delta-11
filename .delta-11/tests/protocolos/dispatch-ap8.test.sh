#!/usr/bin/env bash
# Teste de regressão: AP#8 — disparar.sh foi deletado ou desativado.
# Sistema NAO depende mais de AppleScript para abrir Terminal humano.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$SCRIPT_DIR/../../../"
DISPARAR="$RAIZ/disparar.sh"
CLAUDE="$RAIZ/CLAUDE.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

# 1. disparar.sh NAO pode existir (foi deletado)
if [ ! -f "$DISPARAR" ]; then
    ok "disparar.sh foi deletado (AppleScript legado removido)"
else
    # Se existir, NAO pode conter AppleScript ativo
    if grep -qE "osascript|tell application "Terminal"" "$DISPARAR" 2>/dev/null; then
        err "disparar.sh existe e ainda tem AppleScript ativo"
    else
        ok "disparar.sh existe mas nao tem AppleScript (refatorado)"
    fi
fi

# 2. CLAUDE.md NAO pode recomendar disparar.sh como caminho de fallback
if grep -qF "Fallback 2 — Script \`./disparar.sh\` legado" "$CLAUDE"; then
    err "CLAUDE.md ainda recomenda disparar.sh como fallback"
else
    ok "CLAUDE.md NAO recomenda disparar.sh"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#8 corrigido (AppleScript legacy removido)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi