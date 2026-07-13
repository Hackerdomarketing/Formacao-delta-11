#!/usr/bin/env bash
# Teste de regressão: AP#1 + AP#6 — CRONOS auto-retomada e auto-dispatch.
# CRONOS PODE disparar a si mesmo via Agent tool (mesma ferramenta que
# usa para disparar outros agentes). NAO precisa do humano.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/protocolos/ -> sobe 3 niveis: tests/ -> .delta-11/ -> raiz do repo
CLAUDE="$SCRIPT_DIR/../../../CLAUDE.md"
CRONOS="$SCRIPT_DIR/../../operativos/CRONOS.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. CLAUDE.md NAO pode proibir CRONOS de se auto-dispensar
if grep -qF "Só o comandante pode disparar CRONOS" "$CLAUDE"; then
    err "CLAUDE.md ainda diz 'Só o comandante pode disparar CRONOS' (anti-padrao AP#1)"
else
    ok "CLAUDE.md NAO proibe CRONOS de se auto-dispensar"
fi

# 2. CRONOS.md NAO pode pedir ao humano para abrir nova sessao
if grep -qE "comandante abre nova sess[aã]o|comandante.*dispara CRONOS|comandante.*cola.*prompt.*retomada" "$CRONOS"; then
    err "CRONOS.md ainda instrui humano a abrir nova sessao (anti-padrao AP#6)"
else
    ok "CRONOS.md NAO instrui humano a abrir nova sessao"
fi

# 3. CLAUDE.md DEVE ter a frase positiva sobre CRONOS auto-dispensavel
if grep -qiE "CRONOS.*pode.*se.*auto.*dispensar|CRONOS.*disparar.*ele.*mesmo|CRONOS.*auto.*retomar" "$CLAUDE"; then
    ok "CLAUDE.md diz que CRONOS pode se auto-dispensar / auto-retomar"
else
    err "CLAUDE.md NAO diz que CRONOS pode se auto-dispensar"
fi

# 4. CRONOS.md DEVE ter a frase positiva sobre auto-dispatch
if grep -qiF "auto-retoma" "$CRONOS" || grep -qiF "auto-dispensar" "$CRONOS" || grep -qiF "disparar a si mesmo" "$CRONOS"; then
    ok "CRONOS.md documenta auto-dispatch"
else
    err "CRONOS.md NAO documenta auto-dispatch"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — AP#1+AP#6 corrigidos (CRONOS autonomo)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi