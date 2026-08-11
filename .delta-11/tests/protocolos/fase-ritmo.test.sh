#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do protocolo fase-ritmo.md (Etapa 5A do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o protocolo formal da Fase 3.5 existe e cobre:
#   1. Arquivo existe em .delta-11/protocolos/fase-ritmo.md
#   2. Cross-reference com fluxo-zero-ao-lancamento.md (Fase 3.5)
#   3. Cross-reference com a base canonica Metodologia Genesis
#   4. Os 10 artefatos do Dia 4 declarados
#   5. Quem sella (lider tecnico + Comandante)
#   6. Texto hebraico chave do Dia 4 mencionado
#   7. Secao "Quando NAO aplicar esta fase" (saber quando pular)
#   8. Cross-reference com entregaveis salvos em .delta-11/memoria/decisoes/
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/fase-ritmo.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$DOC" ]; then
    ok "protocolo existe em .delta-11/protocolos/fase-ritmo.md"
else
    err "protocolo AUSENTE em $DOC"
    echo ""
    echo "Este teste é guarda de regressão do protocolo formal da Fase 3.5."
    echo "A Fase 3.5 foi adicionada ao fluxo na Etapa 2A mas precisa de"
    echo "protocolo detalhado para que os agentes saibam EXATAMENTE o que fazer."
    echo "Sem protocolo, o template e o hook vao flutuar sem norte."
    exit 1
fi

# 2. Cross-reference com fluxo
if grep -qi "FASE 3\.5\|fluxo-zero-ao-lancamento" "$DOC"; then
    ok "cross-reference com fluxo-zero-ao-lancamento.md (Fase 3.5)"
else
    err "NAO cross-reference com fluxo — fica orfa"
fi

# 3. Cross-reference com Metodologia Genesis
if grep -qi "metodologia-genesis-camadas\|Dia 4\|Astros" "$DOC"; then
    ok "cross-reference com Metodologia Genesis (Dia 4)"
else
    err "NAO cross-reference com Metodologia Genesis"
fi

# 4. Os 10 artefatos do Dia 4 declarados
artefatos=(
    "eventos"
    "filas"
    "jobs"
    "cache"
    "timeout"
    "retry"
    "circuit breaker"
    "CI/CD"
    "observabilidade"
    "sub-contraposi"
)
for art in "${artefatos[@]}"; do
    if grep -qi "$art" "$DOC"; then
        ok "protocolo menciona artefato '$art'"
    else
        err "protocolo NAO menciona artefato '$art'"
    fi
done

# 5. Quem sella
if grep -qiE "quem sella|sella:|Comandante.*[sS]elo|lider tecnico.*selo" "$DOC"; then
    ok "protocolo declara quem sella"
else
    err "protocolo NAO declara quem sella"
fi

# 6. Texto hebraico chave do Dia 4
if grep -qE "yehi meorot|bi-rekia|memshelet" "$DOC"; then
    ok "texto hebraico chave do Dia 4 presente"
else
    err "NAO inclui texto hebraico do Dia 4 — perde fidelidade a fonte"
fi

# 7. Quando NAO aplicar esta fase (honestidade intelectual)
if grep -qiE "quando n..o|nao aplicar|exce|isento" "$DOC"; then
    ok "protocolo declara quando NAO aplicar (excecoes)"
else
    err "protocolo NAO declara quando NAO aplicar — sem saida para excessoes legitimas"
fi

# 8. Endereco dos entregaveis (memoria/decisoes/)
if grep -qi "memoria/decisoes" "$DOC"; then
    ok "endereco canonico dos entregaveis (.delta-11/memoria/decisoes/)"
else
    err "NAO declara endereco canonico dos entregaveis"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — protocolo fase-ritmo.md cobre a Fase 3.5${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi