#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da Etapa 2 do v6.0 — Fluxo com Fase 3.5 (Ritmo Temporal)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o protocolo de fluxo-zero-ao-lancamento.md declara:
#   1. Fase 3.5 — RITMO TEMPORAL existe entre Fase 3 e Fase 4
#   2. Quem faz (CRONOS + DevOps/SRE)
#   3. Janelas estimadas
#   4. Resultado esperado
#   5. Critério de selo com os 10 artefatos do Dia 4
#   6. Cross-reference com a base canonica da Metodologia Genesis
#   7. A Fase 3.5 vem ANTES da Fase 4 (ordem inegociavel)
#
# Guard de regressao: se a Fase 3.5 for removida ou renomeada,
# este teste falha. Se ela for colocada DEPOIS da Fase 4 (inversao
# heretica), este teste tambem falha.
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/fluxo-zero-ao-lancamento.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ ! -f "$DOC" ]; then
    echo "fluxo-zero-ao-lancamento.md AUSENTE em $DOC"
    exit 1
fi

# 1. Cabecalho da Fase 3.5 existe
if grep -qE "^### FASE 3\.5 " "$DOC"; then
    ok "cabecalho 'FASE 3.5' presente"
else
    err "cabecalho 'FASE 3.5' AUSENTE — sem isso, Dia 4 nao existe no fluxo"
fi

# 2. Nome da Fase 3.5 menciona RITMO (palavra-chave do Dia 4)
# Procura na mesma linha do cabecalho
if grep -E "^### FASE 3\.5 " "$DOC" | grep -qi "ritmo\|astros\|temporal"; then
    ok "Fase 3.5 nomeada com termo do Dia 4 (ritmo/astros/temporal)"
else
    err "Fase 3.5 NAO nomeada com termo do Dia 4 — confusao conceitual"
fi

# 3. Quem faz — CRONOS + DevOps/SRE/lider tecnico presentes
# Range de 25 linhas apos o cabecalho cobre a secao inteira
if grep -A25 "^### FASE 3\.5 " "$DOC" | grep -qi "CRONOS\|DevOps\|SRE\|l[íi]der t[ée]cnico"; then
    ok "Fase 3.5 declara quem faz"
else
    err "Fase 3.5 NAO declara quem faz"
fi

# 4. Janela estimada presente (formato: Janela(s): N — busca simples para evitar problemas de regex)
if grep -A25 "^### FASE 3\.5 " "$DOC" | grep -qiF "Janela"; then
    ok "Fase 3.5 declara janela estimada"
else
    err "Fase 3.5 NAO declara janela estimada"
fi

# 5. Resultado esperado presente (palavra-chave: Resultado no padrao das outras fases)
# Range de 40 linhas apos o cabecalho cobre secoes inteiras
if grep -A40 "^### FASE 3\.5 " "$DOC" | grep -qF "**Resultado:**"; then
    ok "Fase 3.5 declara Resultado esperado"
else
    err "Fase 3.5 NAO declara Resultado esperado (padrao das outras fases)"
fi

# 6. Critério de selo com os 10 artefatos do Dia 4
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
    "Sub-contraposição"
)
for art in "${artefatos[@]}"; do
    if grep -A40 "^### FASE 3\.5 " "$DOC" | grep -qiF "$art"; then
        ok "Fase 3.5 menciona artefato '$art'"
    else
        err "Fase 3.5 NAO menciona artefato '$art'"
    fi
done

# 7. ORDEM INEGOCIAVEL — Fase 3.5 vem ANTES da Fase 4
pos_35=$(grep -nE "^### FASE 3\.5 " "$DOC" | head -1 | cut -d: -f1 || echo "0")
pos_4=$(grep -nE "^### FASE 4 " "$DOC" | head -1 | cut -d: -f1 || echo "999")

if [ "$pos_35" = "0" ] || [ "$pos_4" = "999" ]; then
    err "impossivel determinar posicao — falta Fase 3.5 ou Fase 4"
elif [ "$pos_35" -lt "$pos_4" ]; then
    ok "Fase 3.5 (linha $pos_35) vem ANTES da Fase 4 (linha $pos_4) — ordem inegociavel preservada"
else
    err "INVERSAO HERETICA — Fase 3.5 (linha $pos_35) esta DEPOIS da Fase 4 (linha $pos_4). Isso e exatamente o erro que a Metodologia Genesis adverte: 'fazer os peixes antes das aguas'."
fi

# 8. Cross-reference com a base canonica da Metodologia
if grep -q "metodologia-genesis-camadas\|Dia 4\|metodologia.*genesis" "$DOC"; then
    ok "cross-reference com Metodologia Genesis (Dia 4)"
else
    err "NAO cross-reference com Metodologia Genesis — Fase 3.5 fica orfa do conceito"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Fase 3.5 (Ritmo Temporal) integra o fluxo corretamente${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) — corrigir antes de prosseguir para Etapa 2B${NC}"
    exit 1
fi