#!/usr/bin/env bash
# Teste CONSOLIDADO de regressão v6.1 — todos os anti-padroes de
# dispatch humano corrigidos. Se algum AP voltar (regressão), este
# teste falha. E o guarda de que a v6.1 NAO pode ser revertida
# acidentalmente sem que alguem perceba.

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TESTS_DIR="$SCRIPT_DIR/../.."

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# Lista de TODOS os testes de dispatch da v6.1
TESTES_V6_1=(
  "tests/operativos/dispatch-ap5.test.sh"
  "tests/operativos/dispatch-ap3.test.sh"
  "tests/operativos/dispatch-ap4.test.sh"
  "tests/protocolos/dispatch-ap1-ap6.test.sh"
  "tests/protocolos/dispatch-ap2.test.sh"
  "tests/operativos/dispatch-ap7.test.sh"
  "tests/protocolos/dispatch-ap8.test.sh"
  "tests/protocolos/dispatch-ap11-ap13-ap14.test.sh"
  "tests/protocolos/dispatch-ap9-ap10-ap12.test.sh"
)

total_testes=0
testes_ok=0
testes_fail=0

for t in "${TESTES_V6_1[@]}"; do
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

# Verifica tambem que o CHANGELOG tem entrada v6.1
CHANGELOG="$TESTS_DIR/CHANGELOG.md"
if [ -f "$CHANGELOG" ] && grep -qF "## v6.1" "$CHANGELOG"; then
    ok "CHANGELOG.md tem entrada v6.1 (imutavel)"
else
    err "CHANGELOG.md NAO tem entrada v6.1"
fi

# Verifica que CLAUDE.md tem secao v6.1
CLAUDE="$TESTS_DIR/../CLAUDE.md"
if [ -f "$CLAUDE" ] && grep -qF "DISPATCH AUTÔNOMO v6.1" "$CLAUDE"; then
    ok "CLAUDE.md tem secao v6.1 (dispatch autonomo)"
else
    err "CLAUDE.md NAO tem secao v6.1"
fi

# Verifica que disparar.sh foi deletado
RAIZ="$TESTS_DIR/../.."
if [ ! -f "$RAIZ/disparar.sh" ]; then
    ok "disparar.sh NAO existe (AppleScript legacy removido)"
else
    err "disparar.sh ainda existe"
fi

echo ""
echo "============================================="
echo "  v6.1 Teste Consolidado"
echo "  Total: $total_testes | OK: $testes_ok | FAIL: $testes_fail"
echo "============================================="

if [ "$falhou" -eq 0 ] && [ "$testes_fail" -eq 0 ]; then
    echo -e "${GREEN}OK — v6.1 dispatch autonomo intacto (9 testes de regressao + 3 checks finais)${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) e/ou $testes_fail teste(s) de dispatch falharam${NC}"
    exit 1
fi