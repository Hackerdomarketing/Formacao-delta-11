#!/usr/bin/env bash
# Teste de regressão: AP#3 — ATLAS NAO pode instruir humano a copiar/colar
# prompt de ativacao de agentes. Disparo deve ser via Agent tool.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ATLAS="$SCRIPT_DIR/../../operativos/ATLAS.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ ! -f "$ATLAS" ]; then
    err "ATLAS.md nao encontrado em $ATLAS"; exit 1
fi

# 1. ATLAS NAO pode conter "comandante só precisa copiar e colar"
if grep -qF "O comandante só precisa copiar e colar" "$ATLAS"; then
    err "ATLAS.md ainda contem 'O comandante só precisa copiar e colar. Nada mais.' (anti-padrao AP#3)"
else
    ok "ATLAS.md NAO contem 'O comandante só precisa copiar e colar'"
fi

# 2. ATLAS NAO pode conter frase que proibe auto-dispatch
if grep -qF "comandante colaria manualmente" "$ATLAS"; then
    err "ATLAS.md ainda fala em 'comandante colaria manualmente'"
else
    ok "ATLAS.md NAO fala em 'comandante colaria manualmente'"
fi

# 3. ATLAS DEVE mencionar Agent tool como caminho de disparo do CRONOS
if grep -qE "Agent tool|Agent\(.*subagent_type" "$ATLAS"; then
    ok "ATLAS.md mantem mencao a Agent tool para disparo"
else
    err "ATLAS.md NAO menciona Agent tool — caminho de auto-dispatch ausente"
fi

# 4. ATLAS DEVE ter a frase positiva sobre disparo autonomo
if grep -qiE "dispar[ae].*automaticamente|disparo.*aut[oô]nomo|Dispare o CRONOS.*automaticamente" "$ATLAS"; then
    ok "ATLAS.md menciona disparo autonomo do CRONOS via Agent tool"
else
    err "ATLAS.md NAO menciona disparo autonomo do CRONOS"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#3 corrigido (ATLAS nao pede humano para colar prompt)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi