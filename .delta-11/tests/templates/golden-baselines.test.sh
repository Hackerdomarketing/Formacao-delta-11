#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do golden baselines (G4 — F9 + F10 + F14)
# ════════════════════════════════════════════════════════════════
#
# F9  — Cada tarefa canônica tem campo "Última atualização:"
# F10 — Nenhuma tarefa tem critério subjetivo solto em "Critérios de sucesso"
#       (itens vagos como "fonte com personalidade" devem virar itens
#       ESPECÍFICOS no gabarito, não ficar na seção de sucesso)
# F14 — Pasta execucoes/ existe com .gitkeep
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
TAREFAS_DIR="$REPO_ROOT/golden-baselines/tarefas"
EXECUCOES_DIR="$REPO_ROOT/golden-baselines/execucoes"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FAIL]${NC} $1"; falhou=$((falhou + 1)); }

# ─── F9: campo Última atualização em cada tarefa ───────────
echo "[F9] campo 'Ultima atualizacao':"
if [ ! -d "$TAREFAS_DIR" ]; then
    err "pasta de tarefas nao encontrada: $TAREFAS_DIR"
else
    sem_updated=0
    for f in "$TAREFAS_DIR"/*.md; do
        if ! grep -q "Última atualização\|Ultima atualizacao" "$f"; then
            err "$(basename "$f"): sem campo 'Última atualização'"
            sem_updated=$((sem_updated + 1))
        fi
    done
    if [ "$sem_updated" -eq 0 ]; then
        ok "todas as tarefas tem campo de atualizacao"
    fi
fi

# ─── F10: nenhum critério subjetivo solto ────────────────────
echo ""
echo "[F10] sem criterios subjetivos soltos:"
# Lista de padroes subjetivos (devem ter saido da secao 'Criterios de sucesso')
padroes=(
    "fonte com personalidade"
    "paleta com intenção"
    "paleta com intencao"
    "completos e bonitos"
    "bonito e funcional"
    "código limpo"
    "codigo limpo"
    "boa prática"
    "boa pratica"
)
achou_subj=0
for f in "$TAREFAS_DIR"/*.md; do
    # Extrair secao "Criterios de sucesso" ate a proxima secao
    secao=$(awk '/^## 3\. Crit/{flag=1; next} /^## /{flag=0} flag' "$f")
    for padrao in "${padroes[@]}"; do
        if echo "$secao" | grep -qi "$padrao"; then
            err "$(basename "$f"): termo subjetivo '$padrao' em 'Criterios de sucesso' (deveria estar especifico no gabarito)"
            achou_subj=$((achou_subj + 1))
        fi
    done
done
if [ "$achou_subj" -eq 0 ]; then
    ok "nenhum termo subjetivo em 'Criterios de sucesso'"
fi

# ─── F14: pasta execucoes/ com .gitkeep ─────────────────────
echo ""
echo "[F14] pasta execucoes/.gitkeep:"
if [ -d "$EXECUCOES_DIR" ]; then
    ok "pasta execucoes/ existe"
    if [ -f "$EXECUCOES_DIR/.gitkeep" ]; then
        ok ".gitkeep presente"
    else
        err ".gitkeep ausente em execucoes/"
    fi
else
    err "pasta execucoes/ nao existe"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} golden baselines: F9 + F10 + F14 verificados"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi