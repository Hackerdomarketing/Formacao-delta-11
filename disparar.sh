#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Disparar Agentes
# ═══════════════════════════════════════════════════════════════
#
# Este script lê os prompts de ativação que o ATLAS gerou
# e abre uma janela do Claude Code para cada agente,
# direto no VS Code, com o prompt já colado e rodando.
#
# Como usar:
#   ./disparar.sh
#
# O ATLAS salva os prompts em .delta-11/ativacoes/
# Este script lê cada arquivo e dispara um Claude Code por agente.
#
# ═══════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

ATIVACOES_DIR=".delta-11/ativacoes"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FORMAÇÃO Δ-11 — Disparando Agentes${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# Verificar se a pasta de ativações existe
if [ ! -d "$ATIVACOES_DIR" ]; then
    echo -e "${RED}✗ Pasta $ATIVACOES_DIR não encontrada.${NC}"
    echo ""
    echo "  O ATLAS ainda não gerou os prompts de ativação."
    echo "  Primeiro, abra o Claude Code e inicie com: d11"
    echo "  Quando o ATLAS terminar o planejamento (Fase 2),"
    echo "  ele vai criar os arquivos de ativação automaticamente."
    echo "  Depois, rode este script."
    echo ""
    exit 1
fi

# Contar arquivos de ativação
ARQUIVOS=($(ls "$ATIVACOES_DIR"/*.txt 2>/dev/null))

if [ ${#ARQUIVOS[@]} -eq 0 ]; then
    echo -e "${RED}✗ Nenhum arquivo de ativação encontrado em $ATIVACOES_DIR${NC}"
    echo ""
    echo "  O ATLAS precisa gerar os prompts primeiro."
    echo "  Os arquivos devem estar em: $ATIVACOES_DIR/*.txt"
    echo ""
    exit 1
fi

echo -e "  Encontrados ${BOLD}${#ARQUIVOS[@]} agentes${NC} para ativar:"
echo ""

for arquivo in "${ARQUIVOS[@]}"; do
    nome=$(basename "$arquivo" .txt)
    echo -e "    • ${CYAN}${nome}${NC}"
done

echo ""
read -p "  Disparar todos agora? (s/n): " CONFIRMA

if [[ "$CONFIRMA" != "s" && "$CONFIRMA" != "S" ]]; then
    echo "  Abortado."
    exit 0
fi

echo ""

PROJECT_DIR="$(pwd)"
CONTADOR=0

for arquivo in "${ARQUIVOS[@]}"; do
    nome=$(basename "$arquivo" .txt)
    PROMPT=$(cat "$arquivo")
    CONTADOR=$((CONTADOR + 1))

    echo -e "  ${YELLOW}[$CONTADOR/${#ARQUIVOS[@]}]${NC} Ativando ${BOLD}${nome}${NC}..."

    # Abre uma nova aba do Terminal do macOS e roda o Claude Code
    # com o prompt do agente, dentro da pasta do projeto
    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd \"$PROJECT_DIR\" && claude \"$PROMPT\""
end tell
EOF

    # Pequena pausa entre ativações para não sobrecarregar
    sleep 2
done

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✓ ${CONTADOR} agentes disparados${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Cada agente está rodando em uma aba do Terminal."
echo -e "  Eles já estão lendo seus arquivos e começando a trabalhar."
echo ""
echo -e "  Para acompanhar:"
echo -e "  • Alterne entre as abas do Terminal para ver cada agente"
echo -e "  • Abra o painel visual: .delta-11/painel.html"
echo ""
