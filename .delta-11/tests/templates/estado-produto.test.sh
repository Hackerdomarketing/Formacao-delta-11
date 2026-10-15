#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste dos templates de estado: produto × história (D7, D8, D9, D38)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   D8  O estado do agente é DOIS arquivos:
#       - [NOME]-produto.md (o que existe agora; limite de 500 tokens para
#         executores; ATLAS e CRONOS isentos);
#       - [NOME]-historia.md (diário, sem limite).
#       O estado-agente-template.md ([NOME]-estado.md) é LEGADO: se ainda
#       existir, precisa se declarar legado.
#   D9  O produto tem a linha "autocritica: <caminho>" apontando para
#       .delta-11/logs/autocritica/.
#   D7  O produto tem a seção PROPOSTAS PARA O PROJECT-CORE (quem não é o
#       ATLAS propõe ali; o CRONOS encaminha).
#   v5  Seções PORQUÊS-CHAVE, DESVIOS DO PLANO, RELATÓRIOS DE SUB-AGENTES,
#       O QUE FOI DECIDIDO NÃO FAZER e um exemplo completo preenchido.
#   D38 A história não aponta mais para a skill "inteligencia-progressiva":
#       as lições vão para ~/.delta-11/aprendizados-entre-projetos.md.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

PRODUTO="$DELTA_DIR/templates/estado-produto-template.md"
HISTORIA="$DELTA_DIR/templates/estado-historia-template.md"
LEGADO="$DELTA_DIR/templates/estado-agente-template.md"

if require_file "$PRODUTO" ".delta-11/templates/estado-produto-template.md"; then
    TOPO_PRODUTO="$(head -12 "$PRODUTO")"
    if grep -qiE "500 tokens" <<< "$TOPO_PRODUTO"; then
        pass "D8: limite de 500 tokens visível no topo do produto"
    else
        fail "D8: limite de 500 tokens não aparece no topo do produto"
    fi
    if grep -qE "ATLAS" <<< "$TOPO_PRODUTO" && grep -qE "CRONOS" <<< "$TOPO_PRODUTO"; then
        pass "D8: o topo diz que ATLAS e CRONOS ficam fora do limite"
    else
        fail "D8: o topo não diz que ATLAS e CRONOS ficam fora do limite"
    fi
    expect_match "$PRODUTO" "autocr(í|i)tica:[[:space:]]*\.?(\.delta-11/)?logs/autocritica/" \
        "D9: linha 'autocritica: <caminho>' apontando para .delta-11/logs/autocritica/"
    expect_match "$PRODUTO" "^#+ .*PROPOSTAS PARA O PROJECT-CORE" "D7: seção PROPOSTAS PARA O PROJECT-CORE"
    expect_match "$PRODUTO" "^#+ .*PORQU(Ê|E)S-CHAVE" "seção PORQUÊS-CHAVE"
    expect_match "$PRODUTO" "^#+ .*DESVIOS DO PLANO" "seção DESVIOS DO PLANO"
    expect_match "$PRODUTO" "^#+ .*RELAT(Ó|O)RIOS DE SUB-AGENTES" "seção RELATÓRIOS DE SUB-AGENTES"
    expect_match "$PRODUTO" "^#+ .*DECIDIDO N(Ã|A)O FAZER" "seção O QUE FOI DECIDIDO NÃO FAZER"
    if grep -qiE "EXEMPLO COMPLETO PREENCHIDO" "$PRODUTO" && grep -qE '^```markdown' "$PRODUTO"; then
        pass "exemplo completo preenchido (bloco markdown)"
    else
        fail "exemplo completo preenchido ausente"
    fi
    expect_no_instruction "D8: o produto não manda escrever [NOME]-estado.md" "-estado\.md" "$PRODUTO"
fi

if require_file "$HISTORIA" ".delta-11/templates/estado-historia-template.md"; then
    expect_match "$HISTORIA" "sem limite" "D8: a história não tem limite de tamanho"
    expect_no_match "$HISTORIA" "intelig(ê|e)ncia[ -]progressiva" \
        "D38: a história não aponta para a skill inteligencia-progressiva"
fi

if [ -f "$LEGADO" ]; then
    TOPO_LEGADO="$(head -10 "$LEGADO")"
    if grep -qiE "legad|LEGAD|n(ã|a)o (use|usar|escreva)" <<< "$TOPO_LEGADO"; then
        pass "D8: estado-agente-template.md se declara LEGADO"
    else
        fail "D8: estado-agente-template.md ([NOME]-estado.md) ainda existe sem se declarar LEGADO"
    fi
else
    pass "D8: estado-agente-template.md (legado) não existe mais"
fi

finish_test "templates de estado produto × história"
