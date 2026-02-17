#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Golden Path de Finalização de Tarefa
# ═══════════════════════════════════════════════════════════════
#
# Chame este script TODA VEZ que concluir uma tarefa na Fase 4.
# Ele automaticamente gera o prompt do SHIELD e exibe o checklist
# obrigatório do protocolo de finalização.
#
# USO:
#   ./task-done.sh AGENTE TASK_ID "Descrição" "arquivos modificados"
#
# EXEMPLOS:
#   ./task-done.sh ENGINE T-027 "Criar drive-api.js" "src/background/drive-api.js"
#   ./task-done.sh FRONT T-018 "Criar manifest.json" "src/manifest.json src/background/service-worker.js"
#   ./task-done.sh VAULT T-015 "Criar tabelas Supabase" "supabase/migrations/001_initial.sql"
#
# ═══════════════════════════════════════════════════════════════

set -e

# ─── Cores ──────────────────────────────────────────────────────

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ─── Argumentos ─────────────────────────────────────────────────

AGENTE=$1
TASK_ID=$2
DESCRICAO=$3
ARQUIVOS=${4:-"(não especificados)"}
DATA=$(date '+%Y-%m-%d %H:%M')

# ─── Validar argumentos ──────────────────────────────────────────

if [ -z "$AGENTE" ] || [ -z "$TASK_ID" ] || [ -z "$DESCRICAO" ]; then
    echo ""
    echo -e "${RED}ERRO: Argumentos obrigatórios faltando.${NC}"
    echo ""
    echo "  USO: ./task-done.sh AGENTE TASK_ID 'Descrição' 'arquivos'"
    echo ""
    echo "  EXEMPLOS:"
    echo "    ./task-done.sh ENGINE T-027 'Criar drive-api.js' 'src/background/drive-api.js'"
    echo "    ./task-done.sh FRONT T-018 'Criar manifest.json' 'src/manifest.json'"
    echo ""
    exit 1
fi

# ─── Verificar localização ───────────────────────────────────────

if [ ! -f ".delta-11/kanban.md" ]; then
    echo -e "${RED}ERRO: Execute da raiz do projeto (onde .delta-11/ está).${NC}"
    exit 1
fi

# ─── Setup ──────────────────────────────────────────────────────

mkdir -p .delta-11/ativacoes
mkdir -p .delta-11/logs
PROJETO=$(pwd)

# ─── Header ─────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  TASK-DONE — Golden Path Δ-11${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Agente:  ${BOLD}$AGENTE${NC}"
echo -e "  Tarefa:  ${BOLD}$TASK_ID${NC} — $DESCRICAO"
echo -e "  Data:    $DATA"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Verificar tarefa no kanban ─────────────────────────────────

if grep -q "$TASK_ID" .delta-11/kanban.md; then
    echo -e "  ${GREEN}✓${NC} $TASK_ID encontrada no kanban"
else
    echo -e "  ${YELLOW}⚠${NC} $TASK_ID não encontrada no kanban — verifique o ID"
fi
echo ""

# ─── Gerar prompt do SHIELD ─────────────────────────────────────

SHIELD_FILE=".delta-11/ativacoes/janela-SHIELD-revisao.txt"

cat > "$SHIELD_FILE" << SHIELD_PROMPT
Formação Δ-11. Ativação de agente.
Agente: SHIELD
Fase: 4 — Desenvolvimento
Missão: Revisar tarefa $TASK_ID entregue pelo $AGENTE

TAREFA PARA REVISÃO:
- ID: $TASK_ID
- Agente: $AGENTE
- Data: $DATA
- Descrição: $DESCRICAO
- Arquivos modificados: $ARQUIVOS

INSTRUÇÕES:
1. Leia .delta-11/operativos/SHIELD.md (sua identidade e procedimentos)
2. Leia .delta-11/memoria/project-core.md para contexto do projeto
3. Leia .delta-11/memoria/${AGENTE}-estado.md para contexto do agente
4. Revise cada arquivo listado em "Arquivos modificados" acima
5. Verifique: segurança, qualidade do código, conformidade com o contrato
6. Se APROVADO: mova $TASK_ID de REVISÃO para CONCLUÍDO no kanban.md e kanban-data.js
7. Se REPROVADO: crie tarefa de correção no kanban com os problemas encontrados
8. Atualize .delta-11/memoria/SHIELD-estado.md com sua decisão
SHIELD_PROMPT

echo -e "  ${GREEN}✓${NC} Prompt do SHIELD gerado em: $SHIELD_FILE"

# ─── Log do Golden Path ─────────────────────────────────────────

echo "$DATA | $AGENTE | $TASK_ID | $DESCRICAO" >> .delta-11/logs/golden-path.log
echo -e "  ${GREEN}✓${NC} Registrado em .delta-11/logs/golden-path.log"
echo ""

# ─── Checklist obrigatório ──────────────────────────────────────

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  CHECKLIST OBRIGATÓRIO — Faça TUDO isso antes de continuar${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}1.${NC} [ ] Atualizou ${BOLD}.delta-11/memoria/${AGENTE}-estado.md${NC}?"
echo -e "       → O que fez, arquivos criados, próxima tarefa, notas"
echo ""
echo -e "  ${BOLD}2.${NC} [ ] Atualizou ${BOLD}.delta-11/kanban.md${NC}?"
echo -e "       → Tarefa movida de FAZENDO para REVISÃO (NÃO para CONCLUÍDO)"
echo ""
echo -e "  ${BOLD}3.${NC} [ ] Atualizou ${BOLD}.delta-11/kanban-data.js${NC}?"
echo -e "       → Array 'revisao' com: { id: \"$TASK_ID\", desc: \"$DESCRICAO\", por: \"$AGENTE\", revisor: \"SHIELD\" }"
echo ""
echo -e "  ${BOLD}3.5${NC} [ ] ${RED}BUILD VALIDATOR EXECUTADO?${NC}"
echo -e "       → USE Task tool com subagent_type: \"general-purpose\""
echo -e "       → PROMPT: conteúdo de .delta-11/sub-agentes/build-validator.md"
echo -e "       → Adicione no início: \"Projeto em: $PROJETO. Rode os checks agora.\""
echo -e "       → ${RED}FAIL com blockers = PARE AQUI. Corrija antes de continuar.${NC}"
echo -e "       → PASS ou warnings = registre o resultado no estado e continue"
echo ""
echo -e "  ${BOLD}3.7${NC} [ ] ${YELLOW}REVISÃO DO SHIELD:${NC}"
echo -e "       → Prompt pronto em: ${BOLD}$SHIELD_FILE${NC}"
echo -e "       → Dispare o SHIELD via auto-dispatch (protocolo no CLAUDE.md)"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${DIM}Quando tudo acima estiver feito: puxe a próxima tarefa do kanban.${NC}"
echo ""
