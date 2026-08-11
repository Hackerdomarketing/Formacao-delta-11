#!/usr/bin/env bash
# Teste CONSOLIDADO de regressão v6.2 — todos os 11 hooks novos.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TESTS_DIR="$SCRIPT_DIR/../.."

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

TESTES_V6_2=(
  "tests/hooks/anti-autocompact.test.sh"
  "tests/hooks/forca-despacho.test.sh"
  "tests/hooks/produto-atualizado.test.sh"
  "tests/hooks/anti-stash.test.sh"
  "tests/hooks/shield-aprovado.test.sh"
  "tests/hooks/urls-validas.test.sh"
  "tests/hooks/contratos-minimos.test.sh"
  "tests/hooks/brief-preservado.test.sh"
  "tests/hooks/topologia-deploy.test.sh"
  "tests/hooks/worktree-prune.test.sh"
  "tests/hooks/3-tentativas-shield.test.sh"
)

total_testes=0
testes_ok=0
testes_fail=0

for t in "${TESTES_V6_2[@]}"; do
    total_testes=$((total_testes + 1))
    path="$TESTS_DIR/$t"
    if [ ! -f "$path" ]; then
        err "teste $t NAO existe"
        testes_fail=$((testes_fail + 1))
        continue
    fi
    if bash "$path" >/dev/null 2>&1; then
        testes_ok=$((testes_ok + 1))
        ok "  $t"
    else
        err "  $t FALHOU"
        testes_fail=$((testes_fail + 1))
    fi
done

# Verifica CHANGELOG, CLAUDE.md, e arquivos
CHANGELOG="$TESTS_DIR/CHANGELOG.md"
if [ -f "$CHANGELOG" ] && grep -qF "## v6.2" "$CHANGELOG"; then
    ok "CHANGELOG.md tem entrada v6.2 (imutavel)"
else
    err "CHANGELOG.md NAO tem entrada v6.2"
fi

CLAUDE="$TESTS_DIR/../CLAUDE.md"
if [ -f "$CLAUDE" ] && grep -qF "BEHAVIORAL HOOKS v6.2" "$CLAUDE"; then
    ok "CLAUDE.md tem secao v6.2 (behavioral hooks)"
else
    err "CLAUDE.md NAO tem secao v6.2"
fi

# Verifica que os 11 hooks existem
HOOKS_DIR="$TESTS_DIR/hooks"
HOOKS_ESPERADOS=(
    "anti-autocompact.py"
    "forca-despacho.py"
    "produto-atualizado.py"
    "anti-stash.py"
    "shield-aprovado.py"
    "urls-validas.py"
    "contratos-minimos.py"
    "brief-preservado.py"
    "topologia-deploy.py"
    "worktree-prune.py"
    "3-tentativas-shield.py"
)
for hook in "${HOOKS_ESPERADOS[@]}"; do
    if [ -f "$HOOKS_DIR/$hook" ]; then
        ok "hook existe: $hook"
    else
        err "hook AUSENTE: $hook"
    fi
done

# Verifica que os 11 testes existem
TESTS_DIR_HOOKS="$TESTS_DIR/tests/hooks"
for t in "${TESTES_V6_2[@]}"; do
    baseline=$(basename "$t")
    if [ -f "$TESTS_DIR_HOOKS/$baseline" ]; then
        ok "teste existe: $baseline"
    else
        err "teste AUSENTE: $baseline"
    fi
done

echo ""
echo "============================================="
echo "  v6.2 Teste Consolidado"
echo "  Testes de regressao: $testes_ok / $total_testes"
echo "============================================="

if [ "$falhou" -eq 0 ] && [ "$testes_fail" -eq 0 ]; then
    echo -e "${GREEN}OK — v6.2 behavioral hooks intactos (11 hooks + 11 testes + 3 checks finais)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) e/ou $testes_fail teste(s) de hook falharam${NC}"
    exit 1
fi