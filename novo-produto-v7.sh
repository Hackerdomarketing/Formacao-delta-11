#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Começar um produto no Delta-11 v7
# ═══════════════════════════════════════════════════════════════
#
# Atalho para o instalador do v7 (v7/03-motor/ferramentas/instalar.py).
# Passa todos os argumentos para ele, do jeito que vieram.
#
# O v7 é outro sistema, separado da v6.4.1 (novo-projeto.sh, d11, sincronizar.sh):
# só para Mac e Claude Code (outras IAs pela porta compatível, com --ia), e começa
# o produto por uma conversa com o ATLAS. O sincronizar.sh NÃO atualiza produtos
# do v7: para atualizar, use --atualizar.
#
# Como usar:
#   bash novo-produto-v7.sh ~/projetos/meu-produto
#   bash novo-produto-v7.sh ~/projetos/meu-produto --motor claude-code
#   bash novo-produto-v7.sh ~/projetos/meu-produto --ia deepseek
#   bash novo-produto-v7.sh --atualizar ~/projetos/meu-produto
#   bash novo-produto-v7.sh --passar-do-v6 ~/projetos/projeto-antigo --ensaio
#
# --ia aceita: claude (padrão), deepseek, minimax, kimi, glm ou gateway
# (o gateway pede também --endereco, --modelo-forte, --modelo-medio e --modelo-leve).
# --passar-do-v6 passa um projeto que já usa o Delta-11 v6 para o v7, com cópia
# de segurança e volta atrás; --ensaio só mostra o que faria, sem mudar nada.
# Todas as opções: v7/03-motor/ferramentas/instalar.py (o começo do arquivo explica cada uma).
#
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
INSTALADOR="$SCRIPT_DIR/v7/03-motor/ferramentas/instalar.py"

if [ ! -f "$INSTALADOR" ]; then
    echo -e "${RED}x Não achei o instalador do v7 em $INSTALADOR${NC}"
    echo "  Esta pasta é a Formação Δ-11 completa? Rode: git pull"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}x O v7 precisa do python3 e ele não está instalado.${NC}"
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo -e "${RED}x O v7 precisa do python3 na versão 3.9 ou mais nova (aqui: $(python3 -V 2>&1)).${NC}"
    exit 1
fi

if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "--ajuda" ]; then
    sed -n '/^# Como usar:/,/^# Todas as opções/p' "$0" | sed 's/^# \{0,1\}//' | sed '$d'
    echo ""
    echo "Dê o caminho de uma pasta só para o produto (ela pode ainda não existir)."
    [ $# -eq 0 ] && exit 1
    exit 0
fi

# Sem criar __pycache__ dentro da pasta da Formação (ela é um repositório git que você atualiza com git pull)
export PYTHONDONTWRITEBYTECODE=1

exec python3 -B "$INSTALADOR" "$@"
