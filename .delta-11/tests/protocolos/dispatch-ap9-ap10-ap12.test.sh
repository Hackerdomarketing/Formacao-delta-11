#!/usr/bin/env bash
# Teste de regressão: AP#9 + AP#10 + AP#12 — defaults invertidos + auto-abertura
# - AP#9: modo `automatico` e' default v6.1+ (nao `manual`)
# - AP#10: painel.html auto-aberto (nao instrui humano a abrir)
# - AP#12: instalar.sh tenta multiplas plataformas antes de pedir humano

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$SCRIPT_DIR/../../../"
CRONOS="$RAIZ/.delta-11/operativos/CRONOS.md"
CLAUDE="$RAIZ/CLAUDE.md"
INSTALAR="$RAIZ/instalar.sh"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# AP#9 — `manual` NAO pode ser PADRÃO
if grep -qE "manual.*PADR[AÃ]O|manual.*padr[aã]o.*mais seguro" "$CRONOS"; then
    err "CRONOS.md ainda trata 'manual' como PADRÃO (AP#9)"
else
    ok "CRONOS.md NAO trata 'manual' como PADRÃO (AP#9)"
fi

# AP#9 — `automatico` DEVE ser PADRÃO v6.1+
if grep -qE "automatico.*PADRÃO.*v6\.1|automático.*PADRÃO.*v6\.1" "$CRONOS"; then
    ok "CRONOS.md documenta 'automatico' como PADRÃO v6.1+ (AP#9)"
else
    err "CRONOS.md NAO documenta 'automatico' como PADRÃO v6.1+"
fi

# AP#10 — CLAUDE.md NAO deve dizer "abrir no navegador"
if grep -qF "painel.html          ← Painel visual para o comandante (abrir no navegador)" "$CLAUDE"; then
    err "CLAUDE.md ainda diz painel 'abrir no navegador' (AP#10)"
else
    ok "CLAUDE.md NAO diz 'abrir no navegador' (AP#10)"
fi

# AP#12 — instalar.sh deve tentar multiplas plataformas
if grep -qF "xdg-open" "$INSTALAR" 2>/dev/null; then
    ok "instalar.sh tenta xdg-open (Linux) alem de open (Mac) (AP#12)"
else
    err "instalar.sh NAO tenta multiplas plataformas (AP#12)"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#9+AP#10+AP#12 corrigidos (defaults invertidos + auto-abertura)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi