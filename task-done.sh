#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Golden Path de Finalização de Tarefa (v6.3)
# ═══════════════════════════════════════════════════════════════
#
# O executor chama este script TODA VEZ que termina uma tarefa.
# Ele confere o que já foi feito, registra a entrega e mostra o
# checklist da finalização na ordem única (D9):
#   1a produto.md (com a linha "autocritica: <caminho>")
#   1b historia.md
#   3.4 autocrítica em 2 paradas (logs/autocritica/)
#   3.5 build-validator
#   3.7 contract-tester (gera E roda os testes de contrato)
#   3.8 avisar o CRONOS por SendMessage pedindo a revisão do SHIELD
#   3.9 liberar as travas
#
# O que ele NÃO faz (de propósito):
#   - não escreve no kanban (só o CRONOS escreve — D10);
#   - não cria arquivo de "janela"/prompt para o SHIELD (D9, C-067):
#     o pedido de revisão vai ao CRONOS por SendMessage, e o registro é o
#     próprio -produto.md. Assim duas tarefas ao mesmo tempo nunca se apagam.
#
# USO (de qualquer pasta do projeto ou da worktree do agente):
#   .delta-11/scripts/task-done.sh AGENTE TASK_ID "Descrição" "arquivos modificados"
#
# EXEMPLOS:
#   .delta-11/scripts/task-done.sh ENGINE T-027 "Criar rota de pedidos" "src/app/api/orders/route.ts"
#   .delta-11/scripts/task-done.sh VAULT T-015 "Criar tabelas" "supabase/migrations/001_initial.sql"
#
# ═══════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

AGENTE=$(echo "${1:-}" | tr '[:lower:]' '[:upper:]')
TASK_ID="${2:-}"
DESCRICAO="${3:-}"
ARQUIVOS="${4:-(não especificados)}"
DATA=$(date '+%Y-%m-%d %H:%M')
AGORA_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [ -z "$AGENTE" ] || [ -z "$TASK_ID" ] || [ -z "$DESCRICAO" ]; then
    echo ""
    echo -e "${RED}ERRO: argumentos obrigatórios faltando.${NC}"
    echo ""
    echo "  USO: .delta-11/scripts/task-done.sh AGENTE TASK_ID 'Descrição' 'arquivos'"
    echo ""
    echo "  EXEMPLO:"
    echo "    .delta-11/scripts/task-done.sh ENGINE T-027 'Criar rota de pedidos' 'src/app/api/orders/route.ts'"
    echo ""
    exit 1
fi

case "$AGENTE" in
    ATLAS|CRONOS|FRONT|PIXEL|FORM|BACK|ENGINE|VAULT|SHIELD|SCOUT) ;;
    *) echo -e "${RED}ERRO: agente desconhecido: $AGENTE${NC}"; exit 1 ;;
esac

# ─── Pastas: a da tarefa (pode ser worktree) e a PRINCIPAL (D25) ─
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"

descobrir_pasta_principal() {
    local base="$1" comum prefixo principal
    comum=$(git -C "$base" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || \
        comum=$(cd "$base" 2>/dev/null && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd -P) || comum=""
    if [ -n "$comum" ]; then
        prefixo=$(git -C "$base" rev-parse --show-prefix 2>/dev/null)
        principal="$(dirname "$comum")"
        [ -n "$prefixo" ] && principal="$principal/${prefixo%/}"
        if [ -d "$principal/.delta-11" ]; then
            echo "$principal"; return
        fi
    fi
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.delta-11" ]; then
        echo "$CLAUDE_PROJECT_DIR"; return
    fi
    echo "$base"
}

if [ -d "$(pwd)/.delta-11" ]; then
    PASTA_DA_TAREFA="$(pwd -P)"
else
    case "$SCRIPT_DIR" in
        */.delta-11/scripts) PASTA_DA_TAREFA="${SCRIPT_DIR%/.delta-11/scripts}" ;;
        *) PASTA_DA_TAREFA="$(pwd -P)" ;;
    esac
fi
PROJETO="$(descobrir_pasta_principal "$PASTA_DA_TAREFA")"
D11="$PROJETO/.delta-11"

if [ ! -f "$D11/kanban.md" ]; then
    echo -e "${RED}ERRO: não achei .delta-11/kanban.md em $PROJETO. Rode de dentro do projeto.${NC}"
    exit 1
fi

mkdir -p "$D11/logs/autocritica"

# ─── Cabeçalho ──────────────────────────────────────────────────

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  TASK-DONE — Golden Path Δ-11 (v6.3)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Agente:   ${BOLD}$AGENTE${NC}"
echo -e "  Tarefa:   ${BOLD}$TASK_ID${NC} — $DESCRICAO"
echo -e "  Data:     $DATA"
echo -e "  Projeto:  $PROJETO"
[ "$PASTA_DA_TAREFA" != "$PROJETO" ] && echo -e "  Worktree: $PASTA_DA_TAREFA"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Conferências (só leitura) ──────────────────────────────────

PENDENCIAS=0
conferir() {
    # conferir <ok:0|1> <texto ok> <texto pendente>
    if [ "$1" -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $2"
    else
        echo -e "  ${YELLOW}⚠${NC} $3"
        PENDENCIAS=$((PENDENCIAS + 1))
    fi
}

set +e   # as conferências podem "falhar" sem derrubar o script
grep -qF -- "$TASK_ID" "$D11/kanban.md"
conferir $? "$TASK_ID está no kanban" "$TASK_ID não está no kanban — confira o ID com o CRONOS"

PRODUTO="$D11/memoria/${AGENTE}-produto.md"
HISTORIA="$D11/memoria/${AGENTE}-historia.md"
[ -f "$PRODUTO" ]
conferir $? "memoria/${AGENTE}-produto.md existe" "memoria/${AGENTE}-produto.md não existe (passo 1a)"
grep -qiE '^[-* ]*autocritica:' "$PRODUTO" 2>/dev/null
conferir $? "-produto.md tem a linha 'autocritica: <caminho>'" "-produto.md sem a linha 'autocritica: <caminho>' (passo 1a)"
grep -qF -- "$TASK_ID" "$HISTORIA" 2>/dev/null
conferir $? "memoria/${AGENTE}-historia.md cita $TASK_ID" "memoria/${AGENTE}-historia.md não cita $TASK_ID (passo 1b)"

AUTOCRITICA=""
for f in "$D11/logs/autocritica/"*"$TASK_ID"*.md; do
    [ -f "$f" ] && AUTOCRITICA="$f" && break
done
[ -n "$AUTOCRITICA" ]
conferir $? "autocrítica registrada: ${AUTOCRITICA#"$PROJETO/"}" "autocrítica ausente em .delta-11/logs/autocritica/ (passo 3.4)"

# Travas do agente ainda abertas (pastas *.lock com "AGENTE: NOME" no meta)
TRAVAS=0
for trava in "$D11/locks/"*.lock; do
    [ -d "$trava" ] || continue
    grep -qE "^AGENTE:[[:space:]]*\[?$AGENTE\]?[[:space:]]*$" "$trava/meta" 2>/dev/null && TRAVAS=$((TRAVAS + 1))
done
[ "$TRAVAS" -eq 0 ]
conferir $? "nenhuma trava aberta em nome de $AGENTE" "$TRAVAS trava(s) de $AGENTE ainda abertas em .delta-11/locks/ (passo 3.9)"
set -e
echo ""

# ─── Registro da entrega (append-only, uma linha por tarefa) ───

mkdir -p "$D11/logs"
echo "$DATA | $AGENTE | $TASK_ID | $DESCRICAO | $ARQUIVOS" >> "$D11/logs/golden-path.log"
echo "- [$AGORA_ISO] [task-done] [$AGENTE] $TASK_ID entregue para revisão do SHIELD ($PENDENCIAS pendência(s) no checklist)" >> "$D11/activity-log.md"
echo -e "  ${GREEN}✓${NC} Registrado em .delta-11/logs/golden-path.log e no activity-log"
echo ""

# ─── Checklist (ordem única D9) ─────────────────────────────────

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  CHECKLIST DA FINALIZAÇÃO — faça tudo, nesta ordem${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}1a${NC}  [ ] ${BOLD}.delta-11/memoria/${AGENTE}-produto.md${NC} atualizado (≤500 tokens)"
echo -e "        → o que existe agora + a linha ${BOLD}autocritica: .delta-11/logs/autocritica/<arquivo>.md${NC}"
echo -e "        → algo para o project-core? escreva em PROPOSTAS PARA O PROJECT-CORE (só o ATLAS edita o project-core)"
echo -e "  ${BOLD}1b${NC}  [ ] ${BOLD}.delta-11/memoria/${AGENTE}-historia.md${NC}: o que foi feito e por quê (diário, sem limite)"
echo -e "  ${BOLD}3.4${NC} [ ] Autocrítica em 2 paradas salva em"
echo -e "        ${BOLD}.delta-11/logs/autocritica/$(date +%Y-%m-%d)-$TASK_ID-$AGENTE.md${NC}"
echo -e "        → Parada 1 (antes de validar): ≥3 bugs prováveis concretos + ≥3 casos extremos"
echo -e "        → Parada 2 (depois dos testes): os casos extremos viraram teste? valor fixo no código? console.log?"
echo -e "  ${BOLD}3.5 + 3.7${NC} [ ] JUNTOS, na mesma mensagem, os dois em segundo plano (v6.4): espere os dois"
echo -e "  ${BOLD}3.5${NC} [ ] build-validator rodado (Agent tool, prompt de .delta-11/sub-agentes/build-validator.md)"
echo -e "        → ${RED}FAIL com bloqueio = pare e corrija antes de seguir${NC}"
echo -e "  ${BOLD}3.7${NC} [ ] contract-tester: GERA e RODA os testes de contrato do que mudou"
echo -e "        (Agent tool, prompt de .delta-11/sub-agentes/contract-tester.md) — desvio de contrato = corrigir antes"
echo -e "  ${BOLD}3.8${NC} [ ] Avise o CRONOS por ${BOLD}SendMessage${NC} (não crie arquivo .txt). Texto sugerido:"
echo -e "        ${CYAN}\"$AGENTE: $TASK_ID pronta para revisão do SHIELD. Resumo: $DESCRICAO. Arquivos: $ARQUIVOS."
echo -e "        Produto: .delta-11/memoria/${AGENTE}-produto.md\"${NC}"
echo -e "        → o CRONOS dispara o SHIELD e é quem move a tarefa no kanban (você não edita o kanban)"
echo -e "  ${BOLD}3.9${NC} [ ] Libere as suas travas em .delta-11/locks/ (as pastas *.lock que você criou no Passo 0.3)"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
if [ "$PENDENCIAS" -gt 0 ]; then
    echo -e "  ${YELLOW}${PENDENCIAS} item(ns) ainda pendente(s) acima — resolva antes do passo 3.8.${NC}"
else
    echo -e "  ${GREEN}Conferências OK. Siga para o passo 3.8.${NC}"
fi
echo -e "  ${DIM}Depois do aviso ao CRONOS, aguarde a próxima tarefa que ele atribuir.${NC}"
echo ""
