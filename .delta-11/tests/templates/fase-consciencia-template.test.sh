#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do template fase-consciencia-template.md (Etapa 6B do v6.0)
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../../templates/fase-consciencia-template.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$TEMPLATE" ]; then
    ok "template existe em .delta-11/templates/fase-consciencia-template.md"
else
    err "template AUSENTE em $TEMPLATE"
    exit 1
fi

# 2. Cobre os 5 entregaveis
entregaveis=(
    "auditoria imutavel"
    "auditoria imutável"
    "rate limiting"
    "motor de regras"
    "LGPD"
    "fluxos de aprovação"
    "fluxos de aprovacao"
)
cobertos=0
for ent in "${entregaveis[@]}"; do
    if grep -qi "$ent" "$TEMPLATE"; then
        cobertos=$((cobertos + 1))
    fi
done
if [ "$cobertos" -ge 5 ]; then
    ok "5 entregaveis cobertos (encontrados $cobertos)"
else
    err "apenas $cobertos entregaveis cobertos"
fi

# 3. Estrutura canonica por entregavel
if grep -qE "##\s+.*[Dd]escri[cç][ãa]o" "$TEMPLATE" && \
   grep -qE "##\s+.*[Ee]scolha" "$TEMPLATE" && \
   grep -qE "##\s+.*[Jj]ustificativa" "$TEMPLATE"; then
    ok "template tem secoes Descricao / Escolha / Justificativa"
else
    err "template NAO tem secoes canonicas"
fi

# 4. Cross-reference com protocolo
if grep -qi "fase-consciencia\.md\|protocolo" "$TEMPLATE"; then
    ok "cross-reference com protocolo"
else
    err "NAO cross-reference com protocolo"
fi

# 5. Cross-reference com Metodologia
if grep -qi "metodologia-genesis\|Dia 6" "$TEMPLATE"; then
    ok "cross-reference com Metodologia Genesis"
else
    err "NAO cross-reference com Metodologia Genesis"
fi

# 6. Placeholders editaveis
if grep -qE "\{\{[A-Z_]+\}\}|\[A-Z_+\]" "$TEMPLATE"; then
    ok "template usa placeholders"
else
    err "template NAO usa placeholders"
fi

# 7. Aviso NAO avancar Fase 5
if grep -qiE "n[ãa]o (avan[cç]ar|come[cç]ar).*Fase 5|antes da Fase 5" "$TEMPLATE"; then
    ok "template avisa sobre dependencia com Fase 5"
else
    err "template NAO avisa sobre dependencia"
fi

# 8. Cross-ref com skills globais
if grep -qiE "owasp-top10|supabase-rls|skills-globais" "$TEMPLATE"; then
    ok "template cross-reference skills globais"
else
    err "NAO cross-reference skills globais"
fi

# 9. Testes de verificacao por entregavel
if grep -qiE "teste|verifica[cç][ãa]o|como testar" "$TEMPLATE"; then
    ok "template menciona como testar/verificar"
else
    err "NAO menciona como testar — entrega fica sem validacao objetiva"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — template fase-consciencia-template.md pronto${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi