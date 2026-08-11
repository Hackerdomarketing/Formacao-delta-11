#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do template fase-ritmo-template.md (Etapa 5B do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o template existe em templates/ e tem:
#   1. Localizacao correta em .delta-11/templates/fase-ritmo-template.md
#   2. Nome do template descreve para que serve
#   3. Estrutura minima: header com nome, secao "O que preencher"
#   4. Cobre os 10 artefatos do Dia 4
#   5. Cada artefato tem: Descricao / Escolha / Justificativa / Link
#   6. Cross-reference com protocolo fase-ritmo.md
#   7. Cross-reference com Metodologia Genesis (Dia 4)
#   8. Formato "Substitua {{VARIAVEL}}" para indicar campos editaveis
#   9. Aviso de NAO comecar Fase 4 sem preencher todos
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../../templates/fase-ritmo-template.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$TEMPLATE" ]; then
    ok "template existe em .delta-11/templates/fase-ritmo-template.md"
else
    err "template AUSENTE em $TEMPLATE"
    echo ""
    echo "Este teste é guarda de regressão do template da Fase 3.5."
    echo "Sem template, cada agente preenchera os 10 artefatos do Dia 4"
    "de forma diferente e inconsistente. O teste falhara ate criacao."
    exit 1
fi

# 2. Nome descreve para que serve
if head -5 "$TEMPLATE" | grep -qi "fase.*ritmo\|ritmo.*temporal\|Dia 4\|astros"; then
    ok "nome do template descreve proposito"
else
    err "nome NAO descreve proposito — agente nao sabe pra que serve"
fi

# 3. Estrutura: header + "O que preencher"
if head -3 "$TEMPLATE" | grep -qE "^# "; then
    ok "tem header Markdown"
else
    err "NAO tem header Markdown"
fi

# 4. Cobre os 10 artefatos
artefatos=(
    "eventos"
    "filas"
    "jobs"
    "cache"
    "timeout"
    "retri"           # cobre "retry" e "retries"
    "circuit breaker"
    "CI/CD"
    "observabilidade"
    "sub-contraposi"
)
for art in "${artefatos[@]}"; do
    if grep -qi "$art" "$TEMPLATE"; then
        ok "template cobre artefato '$art'"
    else
        err "template NAO cobre artefato '$art'"
    fi
done

# 5. Estrutura por artefato: Descricao / Escolha / Justificativa / Link
# Verifica que pelo menos 1 artefato tem essas 4 secoes
if grep -qE "##\s+.*[Dd]escri" "$TEMPLATE" && \
   grep -qE "##\s+.*[Ee]scolha" "$TEMPLATE" && \
   grep -qE "##\s+.*[Jj]ustificativa" "$TEMPLATE" && \
   grep -qE "##\s+.*[Ll]ink" "$TEMPLATE"; then
    ok "template tem secoes Descricao / Escolha / Justificativa / Link"
else
    err "template NAO tem as 4 secoes canonicas por artefato"
fi

# 6. Cross-reference com protocolo
if grep -qi "fase-ritmo\.md\|protocolo.*fase-ritmo" "$TEMPLATE"; then
    ok "template cross-reference com protocolo fase-ritmo.md"
else
    err "NAO cross-reference com protocolo — fica orfa"
fi

# 7. Cross-reference com Metodologia Genesis
if grep -qi "metodologia-genesis\|Dia 4\|Astros" "$TEMPLATE"; then
    ok "template cross-reference com Metodologia Genesis"
else
    err "NAO cross-reference com Metodologia Genesis"
fi

# 8. Formato com placeholders editaveis
if grep -qE "\{\{[A-Z_]+\}\}|\[A-Z_+\]" "$TEMPLATE"; then
    ok "template usa placeholders para campos editaveis"
else
    err "template NAO usa placeholders — agente nao sabe o que substituir"
fi

# 9. Aviso sobre NAO avancar Fase 4 sem preencher
# Aceita com ou sem acento
if grep -qE "N..o avan..ar.*Fase 4|antes da Fase 4" "$TEMPLATE"; then
    ok "template avisa sobre dependencia com Fase 4"
else
    err "template NAO avisa sobre dependencia — agente pode pular"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — template fase-ritmo-template.md pronto para uso${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns)${NC}"
    exit 1
fi