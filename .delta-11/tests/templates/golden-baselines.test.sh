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
# Runner — a execução mais recente tem prompts com conteúdo real
#          (não mais uma pasta datada fixa — C-128)
# Os golden baselines só existem na FONTE OFICIAL: dentro de um projeto
# o teste é pulado de forma visível.
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
if [ ! -d "$REPO_ROOT/golden-baselines" ] && [ ! -f "$REPO_ROOT/sincronizar.sh" ]; then
    echo -e "  \033[1;33m[PULADO]\033[0m golden-baselines/ so existe na fonte oficial (rodando dentro de um projeto)"
    exit 0
fi
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FAIL]${NC} $1"; falhou=$((falhou + 1)); }

# ─── F9: campo Última atualização em cada tarefa ───────────
echo "[F9] campo 'Ultima atualizacao':"
if [ ! -d "$TAREFAS_DIR" ]; then
    err "pasta de tarefas nao encontrada: $TAREFAS_DIR"
else
    sem_updated=0
    total_tarefas=0
    for f in "$TAREFAS_DIR"/*.md; do
        [ -f "$f" ] || continue
        total_tarefas=$((total_tarefas + 1))
        if ! grep -q "Última atualização\|Ultima atualizacao" "$f"; then
            err "$(basename "$f"): sem campo 'Última atualização'"
            sem_updated=$((sem_updated + 1))
        fi
    done
    if [ "$total_tarefas" -eq 0 ]; then
        err "nenhuma tarefa canonica em $TAREFAS_DIR (o teste nao conferiu nada)"
    elif [ "$sem_updated" -eq 0 ]; then
        ok "todas as $total_tarefas tarefas tem campo de atualizacao"
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
    [ -f "$f" ] || continue
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
# ─── Regressão do runner (v5.4 E2, revisto na v6.3) ─────────────
# Antes o teste olhava só a pasta fixa "2026-07-10-v5.4-baseline" (C-128):
# uma execução nova nunca era conferida. Agora confere a execução MAIS
# RECENTE de execucoes/ (as pastas começam com a data AAAA-MM-DD, então a
# última em ordem alfabética é a mais nova). Execuções antigas são
# histórico: a v5.3 foi gerada pelo runner com defeito que a v5.4 corrigiu.
echo "[runner] extracao de prompts (execucao mais recente):"
execucao_recente=""
for pasta_execucao in "$EXECUCOES_DIR"/*/; do
    [ -d "$pasta_execucao" ] && execucao_recente="$pasta_execucao"
done
if [ -z "$execucao_recente" ]; then
    err "nenhuma execucao em $EXECUCOES_DIR — rode 'bash golden-baselines/rodar-comparacao.sh <rotulo>'"
else
    prompts_conferidos=0
    prompts_vazios=0
    for f in "$execucao_recente"*/prompt-de-ativacao.txt; do
        [ -f "$f" ] || continue
        prompts_conferidos=$((prompts_conferidos + 1))
        linhas=$(wc -l < "$f" | xargs)
        if [ "$linhas" -lt 5 ]; then
            err "$(basename "$(dirname "$f")"): prompt-de-ativacao tem so $linhas linhas (esperado >=5)"
            prompts_vazios=$((prompts_vazios + 1))
        fi
    done
    if [ "$prompts_conferidos" -eq 0 ]; then
        err "$(basename "$execucao_recente"): nenhum prompt-de-ativacao.txt (runner nao extraiu nada)"
    elif [ "$prompts_vazios" -eq 0 ]; then
        ok "$(basename "$execucao_recente"): $prompts_conferidos prompts com conteudo real"
    fi
fi

if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} golden baselines: F9 + F10 + F14 + runner verificados"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi
