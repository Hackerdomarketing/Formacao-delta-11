#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste CONSOLIDADO do disparo autônomo (v6.1, atualizado na v6.3)
# ════════════════════════════════════════════════════════════════
# Roda todos os testes de disparo e confere:
#   - cada teste de disparo existe e passa;
#   - o CHANGELOG tem as entradas v6.1 e v6.3 (D29);
#   - o CLAUDE.md tem a seção de disparo autônomo (qualquer versão);
#   - disparar.sh não existe na RAIZ certa (a pasta que contém .delta-11/).
#     Antes da v6.3 a raiz subia uma pasta a mais e o teste passava sem
#     olhar o lugar certo (C-124).
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

TESTES_DE_DISPARO=(
  "tests/operativos/dispatch-ap3.test.sh"
  "tests/operativos/dispatch-ap4.test.sh"
  "tests/operativos/dispatch-ap5.test.sh"
  "tests/operativos/dispatch-ap7.test.sh"
  "tests/protocolos/dispatch-ap1-ap6.test.sh"
  "tests/protocolos/dispatch-ap2.test.sh"
  "tests/protocolos/dispatch-ap8.test.sh"
  "tests/protocolos/dispatch-ap9-ap10-ap12.test.sh"
  "tests/protocolos/dispatch-ap11-ap13-ap14.test.sh"
  "tests/protocolos/zero-copiar-colar-d3.test.sh"
)

for teste in "${TESTES_DE_DISPARO[@]}"; do
    caminho="$DELTA_DIR/$teste"
    if [ ! -f "$caminho" ]; then
        fail "teste $teste não existe"
    elif bash "$caminho" >/dev/null 2>&1; then
        pass "$teste"
    else
        fail "$teste FALHOU (rode: bash .delta-11/$teste)"
    fi
done

CHANGELOG="$DELTA_DIR/CHANGELOG.md"
expect_match "$CHANGELOG" "^## v6\.1" "CHANGELOG.md tem a entrada v6.1 (imutável)"
expect_match "$CHANGELOG" "^## v6\.3" "CHANGELOG.md tem a entrada v6.3 (D29)"

expect_match "$REPO_ROOT/CLAUDE.md" "^#+ .*DISPATCH AUT(Ô|O)NOMO|^#+ .*DISPARO AUT(Ô|O)NOMO" \
    "CLAUDE.md tem a seção de disparo autônomo"

if [ -f "$REPO_ROOT/disparar.sh" ]; then
    fail "disparar.sh ainda existe em $REPO_ROOT"
else
    pass "disparar.sh não existe na raiz ($REPO_ROOT)"
fi

finish_test "disparo autônomo intacto (${#TESTES_DE_DISPARO[@]} testes de disparo + 4 conferências)"
