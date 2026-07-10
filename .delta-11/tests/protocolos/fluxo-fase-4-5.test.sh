#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da Etapa 2B do v6.0 — Fluxo com Fase 4.5 (Consciencia)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o protocolo de fluxo-zero-ao-lancamento.md declara:
#   1. Cabecalho 'FASE 4.5' existe entre Fase 4 e Fase 5
#   2. Nomeada com termo do Dia 6 (consciencia/autenticacao/autorizacao)
#   3. Quem faz
#   4. Janela estimada
#   5. Resultado esperado
#   6. 5 entregaveis: auditoria imutavel, rate limiting, motor de regras,
#      LGPD, fluxos de aprovacao
#   7. Cross-reference com skills globais v5.4 (owasp-top10, supabase-rls)
#   8. ORDEM: 4.5 vem ANTES da Fase 5
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

# 1. Cabecalho
if grep -qE "^### FASE 4\.5 " "$DOC"; then
    ok "cabecalho 'FASE 4.5' presente"
else
    err "cabecalho 'FASE 4.5' AUSENTE"
fi

# 2. Nomeada com termo do Dia 6
if grep -E "^### FASE 4\.5 " "$DOC" | grep -qi "consciência\|consciencia\|autenticação\|autorização"; then
    ok "Fase 4.5 nomeada com termo do Dia 6"
else
    err "Fase 4.5 NAO nomeada com termo do Dia 6"
fi

# 3. Quem faz
if grep -A40 "^### FASE 4\.5 " "$DOC" | grep -qiF "Quem"; then
    ok "Fase 4.5 declara quem faz"
else
    err "Fase 4.5 NAO declara quem faz"
fi

# 4. Janela
if grep -A40 "^### FASE 4\.5 " "$DOC" | grep -qiF "Janela"; then
    ok "Fase 4.5 declara janela"
else
    err "Fase 4.5 NAO declara janela"
fi

# 5. Resultado
if grep -A40 "^### FASE 4\.5 " "$DOC" | grep -qF "**Resultado:**"; then
    ok "Fase 4.5 declara Resultado"
else
    err "Fase 4.5 NAO declara Resultado"
fi

# 6. Os 5 entregaveis do Dia 6
entregaveis=(
    "auditoria imutável"
    "rate limiting"
    "motor de regras"
    "LGPD"
    "fluxos de aprovação"
)
for ent in "${entregaveis[@]}"; do
    if grep -A50 "^### FASE 4\.5 " "$DOC" | grep -qiF "$ent"; then
        ok "Fase 4.5 menciona entregavel '$ent'"
    else
        err "Fase 4.5 NAO menciona entregavel '$ent'"
    fi
done

# 7. Cross-reference com skills globais v5.4
if grep -A50 "^### FASE 4\.5 " "$DOC" | grep -qiE "owasp-top10|supabase-rls|skills-globais"; then
    ok "Fase 4.5 cross-reference com skills globais v5.4"
else
    err "Fase 4.5 NAO cross-reference com skills globais — fica orfa do v5.4"
fi

# 8. ORDEM — 4.5 entre 4 e 5
pos_45=$(grep -nE "^### FASE 4\.5 " "$DOC" | head -1 | cut -d: -f1 || echo "0")
pos_4=$(grep -nE "^### FASE 4 " "$DOC" | head -1 | cut -d: -f1 || echo "999")
pos_5=$(grep -nE "^### FASE 5 " "$DOC" | head -1 | cut -d: -f1 || echo "9999")

if [ "$pos_45" = "0" ]; then
    err "Fase 4.5 AUSENTE — impossivel verificar ordem"
elif [ "$pos_4" = "999" ] || [ "$pos_5" = "9999" ]; then
    err "Fase 4 ou 5 AUSENTE — impossivel verificar ordem"
elif [ "$pos_4" -lt "$pos_45" ] && [ "$pos_45" -lt "$pos_5" ]; then
    ok "Fase 4.5 (linha $pos_45) entre Fase 4 (linha $pos_4) e Fase 5 (linha $pos_5) — ordem correta"
else
    err "ORDEM ERRADA — Fase 4 (linha $pos_4) / 4.5 (linha $pos_45) / 5 (linha $pos_5). Esperado: 4 < 4.5 < 5"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — Fase 4.5 (Consciencia) integra o fluxo corretamente${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) — corrigir antes de prosseguir para Etapa 2C${NC}"
    exit 1
fi