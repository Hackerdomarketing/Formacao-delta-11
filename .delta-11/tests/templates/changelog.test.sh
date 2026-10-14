#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do CHANGELOG.md (documentação das versões do sistema)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   1. Existe em .delta-11/CHANGELOG.md.
#   2. Tem a entrada da versão atual v6.3 (D29), com "Por que existe" e
#      "Como testar".
#   3. Mantém as entradas antigas (imutáveis): v6.2, v6.1, v6.0, v5.4, v5.3,
#      v5.2, v5.1, v5.0, v4.0.4, v4.0 — e os marcos que cada uma registrou.
#   4. Tem a seção "ADIÇÕES POSTERIORES" (regra de imutabilidade).
#   5. Tem pelo menos um bloco bash de "Como testar".
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CHANGELOG="$DELTA_DIR/CHANGELOG.md"
require_file "$CHANGELOG" ".delta-11/CHANGELOG.md" || finish_test "CHANGELOG.md"
pass "existe em .delta-11/CHANGELOG.md"

# Seção de uma versão: do "## vX" até o próximo "## ".
version_section() {
    awk -v version="$1" '
        index($0, "## " version) == 1 { found = 1; print; next }
        found && /^## / { exit }
        found { print }
    ' "$CHANGELOG"
}

for versao in "v6.3" "v6.2" "v6.1" "v6.0" "v5.4" "v5.3" "v5.2" "v5.1" "v5.0" "v4.0.4" "v4.0"; do
    if [ -n "$(version_section "$versao ")$(version_section "$versao(")" ]; then
        pass "entrada $versao presente"
    else
        fail "entrada $versao ausente"
    fi
done

secao_v63=$(version_section "v6.3")
if grep -qiE "por que (essa|esta) (vers(ã|a)o|mudan(ç|c)a) existe|por que existe" <<< "$secao_v63"; then
    pass "v6.3 tem 'Por que existe'"
else
    fail "v6.3 sem 'Por que existe'"
fi
if grep -qiE "como testar" <<< "$secao_v63"; then
    pass "v6.3 tem 'Como testar'"
else
    fail "v6.3 sem 'Como testar'"
fi

expect_match "$CHANGELOG" "Est(á|a)gio 0" "v5.4 registra os Estágios do plano"
expect_match "$CHANGELOG" "Onda 4" "v5.3 registra a Onda 4"
expect_match "$CHANGELOG" "Bloco A" "v5.3 registra o Bloco A"
expect_match "$CHANGELOG" "Zoneamento Documental" "v5.2 registra o Zoneamento Documental"
expect_match "$CHANGELOG" "^## ADI(ÇÕ|CO)ES POSTERIORES" "seção 'ADIÇÕES POSTERIORES' (imutabilidade)"
expect_match "$CHANGELOG" '^[[:space:]]*```bash' "pelo menos um bloco bash de 'Como testar'"

finish_test "CHANGELOG.md"
