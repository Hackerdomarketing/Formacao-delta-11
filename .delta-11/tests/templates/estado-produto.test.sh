#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do template estado-produto-template.md (G1 — F4 do Bloco A)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o template:
#   1. Tem seção AUTOCRÍTICA com formato de path esperado
#   2. Tem seção PORQUÊS-CHAVE (v5)
#   3. Tem seção DESVIOS DO PLANO (v5)
#   4. Tem seção RELATÓRIOS DE SUB-AGENTES (v5)
#   5. Tem seção O QUE FOI DECIDIDO NÃO FAZER
#   6. Tem EXEMPLO COMPLETO PREENCHIDO com o bloco markdown de exemplo
#   7. Limite de 500 tokens visível no topo
#
# Saída: exit 0 se tudo OK, exit 1 com lista de faltantes se falhar.
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/templates/ → tests/ → .delta-11/ → templates/
TEMPLATE="$SCRIPT_DIR/../../templates/estado-produto-template.md"

if [ ! -f "$TEMPLATE" ]; then
    echo -e "${RED}[FAIL]${NC} template nao encontrado: $TEMPLATE"
    exit 1
fi

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. AUTOCRÍTICA com formato correto
grep -q "## AUTOCRÍTICA" "$TEMPLATE" && \
    grep -q "\.delta-11/logs/autocritica/" "$TEMPLATE" \
    && ok "secao AUTOCRITICA com formato de path esperado" \
    || err "secao AUTOCRITICA com formato .delta-11/logs/autocritica/AAAA-MM-DD-T-XXX-NOME.md"

# 2. PORQUÊS-CHAVE
grep -q "## PORQUÊS-CHAVE" "$TEMPLATE" \
    && ok "secao PORQUEIS-CHAVE presente" \
    || err "secao PORQUEIS-CHAVE ausente"

# 3. DESVIOS DO PLANO
grep -q "## DESVIOS DO PLANO" "$TEMPLATE" \
    && ok "secao DESVIOS DO PLANO presente" \
    || err "secao DESVIOS DO PLANO ausente"

# 4. RELATÓRIOS DE SUB-AGENTES
grep -q "## RELATÓRIOS DE SUB-AGENTES" "$TEMPLATE" \
    && ok "secao RELATORIOS DE SUB-AGENTES presente" \
    || err "secao RELATORIOS DE SUB-AGENTES ausente"

# 5. DECIDIDO NÃO FAZER
grep -q "## O QUE FOI DECIDIDO NÃO FAZER" "$TEMPLATE" \
    && ok "secao O QUE FOI DECIDIDO NAO FAZER presente" \
    || err "secao DECIDIDO NAO FAZER ausente"

# 6. EXEMPLO COMPLETO PREENCHIDO (v5.4 — F4)
grep -q "EXEMPLO COMPLETO PREENCHIDO" "$TEMPLATE" && \
    grep -q "^> Para agentes novos" "$TEMPLATE" && \
    grep -q '```markdown' "$TEMPLATE" \
    && ok "EXEMPLO COMPLETO PREENCHIDO presente (F4)" \
    || err "EXEMPLO COMPLETO PREENCHIDO ausente (F4 nao fechado)"

# 7. Limite 500 tokens visível
grep -q "LIMITE DURO: 500 tokens" "$TEMPLATE" \
    && ok "LIMITE 500 TOKENS visivel no topo" \
    || err "LIMITE 500 TOKENS ausente"

if [ "$falhou" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}[OK]${NC} estado-produto-template: todas as secoes obrigatorias + exemplo (F4)"
    exit 0
else
    echo ""
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) faltando"
    exit 1
fi