#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo fase-consciencia.md (Etapa 6A do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o protocolo formal da Fase 4.5 existe e cobre:
#   1. Arquivo existe em .delta-11/protocolos/fase-consciencia.md
#   2. Cross-reference com fluxo-zero-ao-lancamento.md (Fase 4.5)
#   3. Cross-reference com Metodologia Genesis (Dia 6)
#   4. Os 5 entregaveis do Dia 6: auditoria imutavel, rate limiting,
#      motor de regras central, LGPD, fluxos de aprovacao
#   5. Quem sella
#   6. Texto hebraico chave do Dia 6 (naaseh adam, tov meod)
#   7. Cross-reference com skills globais v5.4 (owasp-top10, supabase-rls)
#   8. Quando NAO aplicar
#   9. Endereco canonico dos entregaveis
#  10. Relacao com Dia 5 (governa os habitantes do Dia 5)
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/fase-consciencia.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$DOC" ]; then
    ok "protocolo existe em .delta-11/protocolos/fase-consciencia.md"
else
    err "protocolo AUSENTE em $DOC"
    echo ""
    echo "Teste de regressão do protocolo formal da Fase 4.5."
    echo "A Fase 4.5 foi adicionada ao fluxo na Etapa 2B mas precisa de"
    "protocolo detalhado para os agentes de consciencia."
    exit 1
fi

# 2. Cross-reference fluxo
if grep -qiE "FASE 4\.5|fluxo-zero-ao-lancamento" "$DOC"; then
    ok "cross-reference com fluxo-zero (Fase 4.5)"
else
    err "NAO cross-reference com fluxo"
fi

# 3. Cross-reference Metodologia
if grep -qiE "metodologia-genesis-camadas|Dia 6|Consciência Dominante" "$DOC"; then
    ok "cross-reference com Metodologia Genesis (Dia 6)"
else
    err "NAO cross-reference com Metodologia Genesis"
fi

# 4. Os 5 entregaveis
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
    if grep -qi "$ent" "$DOC"; then
        cobertos=$((cobertos + 1))
    fi
done
if [ "$cobertos" -ge 5 ]; then
    ok "5 entregaveis do Dia 6 presentes (encontrados $cobertos)"
else
    err "apenas $cobertos entregaveis cobertos (minimo 5)"
fi

# 5. Quem sella
if grep -qiE "quem sella|sella:|SHIELD.*selo|Comandante.*selo" "$DOC"; then
    ok "protocolo declara quem sella"
else
    err "protocolo NAO declara quem sella"
fi

# 6. Texto hebraico chave (Dia 6)
if grep -qE "naaseh adam|tov meod|be-tzalmenu|zachar u-nekev" "$DOC"; then
    ok "texto hebraico chave do Dia 6 presente"
else
    err "NAO inclui texto hebraico do Dia 6"
fi

# 7. Cross-ref skills globais v5.4
if grep -qiE "owasp-top10|supabase-rls|skills-globais" "$DOC"; then
    ok "cross-reference com skills globais v5.4 (obrigatorio)"
else
    err "NAO cross-reference com skills globais v5.4 — fica orfa"
fi

# 8. Quando NAO aplicar
if grep -qiE "quando n[ãa]o|isento|exce[cç][ãa]o" "$DOC"; then
    ok "protocolo declara excecoes"
else
    err "protocolo NAO declara quando NAO aplicar"
fi

# 9. Endereco canonico
if grep -qi "memoria/decisoes" "$DOC"; then
    ok "endereco canonico dos entregaveis"
else
    err "NAO declara endereco canonico"
fi

# 10. Relacao com Dia 5 (governa os habitantes)
if grep -qiE "Dia 5|governa.*habitante|acima.*servi[cç]os" "$DOC"; then
    ok "declara relacao com Dia 5 (governa os habitantes)"
else
    err "NAO declara relacao hierarquica com Dia 5"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — protocolo fase-consciencia.md cobre a Fase 4.5${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi