#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Iniciar Projeto Novo
# ═══════════════════════════════════════════════════════════════
#
# Use este script para copiar os arquivos da Formação Δ-11
# para uma nova pasta de projeto.
#
# Como usar:
#   ./novo-projeto.sh /caminho/para/meu-projeto
#   ./novo-projeto.sh ~/projetos/meu-app
#
# ═══════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Diretório de origem (onde este script está)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verificar argumento
if [ -z "$1" ]; then
    echo ""
    echo -e "${BOLD}Uso:${NC} ./novo-projeto.sh /caminho/para/meu-projeto"
    echo ""
    echo "Exemplo:"
    echo "  ./novo-projeto.sh ~/projetos/meu-app"
    echo "  ./novo-projeto.sh ./meu-novo-site"
    echo ""
    exit 1
fi

TARGET_DIR="$1"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FORMAÇÃO Δ-11 — Novo Projeto${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# Criar pasta do projeto se não existir
if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
    echo -e "  ${GREEN}✓${NC} Pasta criada: $TARGET_DIR"
else
    # Verificar se já tem .delta-11
    if [ -d "$TARGET_DIR/.delta-11" ]; then
        echo -e "${YELLOW}  ⚠ Este projeto já tem a Formação Δ-11 instalada.${NC}"
        read -p "  Deseja sobrescrever? (s/n): " OVERWRITE
        if [[ "$OVERWRITE" != "s" && "$OVERWRITE" != "S" ]]; then
            echo "  Abortado."
            exit 1
        fi
        rm -rf "$TARGET_DIR/.delta-11"
        rm -f "$TARGET_DIR/CLAUDE.md"
    fi
fi

# Copiar arquivos do sistema
echo "  Copiando arquivos da Formação Δ-11..."

cp -r "$SCRIPT_DIR/.delta-11" "$TARGET_DIR/.delta-11"
cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"

# Limpar os dados do kanban (começar do zero)
cat > "$TARGET_DIR/.delta-11/kanban-data.js" << 'EOF'
window.KANBAN_DATA = {
  projeto: "",
  complexidade: "",
  fase_atual: "",
  ultima_atualizacao: "",
  agente_atualizador: "",
  a_fazer: {
    ATLAS: [], CRONOS: [], FRONT: [], PIXEL: [],
    FORM: [], BACK: [], ENGINE: [], VAULT: [],
    SHIELD: [], SCOUT: []
  },
  fazendo: [],
  revisao: [],
  concluido: [],
  bloqueado: []
};
EOF

# Limpar o kanban.md (template limpo)
# Manter o template mas sem dados preenchidos

# Limpar memórias individuais (não deve ter nenhuma)
find "$TARGET_DIR/.delta-11/memoria" -name "*-estado.md" -delete 2>/dev/null || true

# Resetar project-core.md para template limpo
# (o ATLAS preencherá na Fase 2)

FILE_COUNT=$(find "$TARGET_DIR" -path "$TARGET_DIR/.git" -prune -o -type f -print | wc -l | xargs)

echo -e "  ${GREEN}✓${NC} ${FILE_COUNT} arquivos copiados"
echo ""

# Abrir no VS Code se disponível
if command -v code &> /dev/null; then
    read -p "  Abrir no VS Code? (s/n): " OPEN_VSCODE
    if [[ "$OPEN_VSCODE" == "s" || "$OPEN_VSCODE" == "S" ]]; then
        code "$TARGET_DIR"
        echo -e "  ${GREEN}✓${NC} VS Code aberto"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}  ✓ Projeto pronto!${NC}"
echo ""
echo -e "  ${BOLD}Próximo passo:${NC}"
echo -e "  1. Abra uma janela do Claude Code"
echo -e "  2. Digite: ${CYAN}d11${NC}"
echo -e "  3. Descreva o que quer construir"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
