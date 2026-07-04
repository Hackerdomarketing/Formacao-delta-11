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

# ─── v5.2 (M-17): migração interativa de memórias legadas ───
# Projetos que existiam ANTES do Δ-11 podem ter arquivos .memoria-* na raiz
# (sistema antigo). Perguntar antes de mover — nunca mover silenciosamente.
LEGADOS=""
for f in "$TARGET_DIR/.memoria-do-dia.md" "$TARGET_DIR/.memoria-projeto.md" "$TARGET_DIR/.memoria-ultimas-tarefas.md"; do
    [ -f "$f" ] && LEGADOS="$LEGADOS $(basename "$f")"
done
if [ -n "$LEGADOS" ]; then
    echo -e "${YELLOW}  ⚠ Encontrei arquivos de memória de um sistema antigo na raiz:${NC}"
    echo "   $LEGADOS"
    read -p "  Mover para .delta-11/memoria/legado/ ? (s/n): " MIGRAR
    if [[ "$MIGRAR" == "s" || "$MIGRAR" == "S" ]]; then
        mkdir -p "$TARGET_DIR/.delta-11-legado-temp"
        for f in "$TARGET_DIR/.memoria-do-dia.md" "$TARGET_DIR/.memoria-projeto.md" "$TARGET_DIR/.memoria-ultimas-tarefas.md"; do
            [ -f "$f" ] && mv "$f" "$TARGET_DIR/.delta-11-legado-temp/"
        done
        echo -e "  ${GREEN}✓${NC} Memórias legadas separadas (serão movidas para .delta-11/memoria/legado/)"
    fi
fi

# Copiar arquivos do sistema
echo "  Copiando arquivos da Formação Δ-11..."

cp -r "$SCRIPT_DIR/.delta-11" "$TARGET_DIR/.delta-11"
cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"

# ─── v5.2 (M-17): finalizar migração das memórias legadas ───
if [ -d "$TARGET_DIR/.delta-11-legado-temp" ]; then
    mkdir -p "$TARGET_DIR/.delta-11/memoria/legado"
    mv "$TARGET_DIR/.delta-11-legado-temp/"* "$TARGET_DIR/.delta-11/memoria/legado/" 2>/dev/null || true
    rmdir "$TARGET_DIR/.delta-11-legado-temp" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Memórias legadas em .delta-11/memoria/legado/"
fi

# ─── v5.2 (M-18): shells de operação vão para .delta-11/scripts/ ───
# Endereço canônico a partir da v5.2 — a raiz do projeto fica só com código + configs.
mkdir -p "$TARGET_DIR/.delta-11/scripts"
for script in task-done.sh disparar.sh monitor-delta11.sh vigilante.sh com.delta11.monitor.plist; do
    [ -f "$SCRIPT_DIR/$script" ] && cp "$SCRIPT_DIR/$script" "$TARGET_DIR/.delta-11/scripts/"
done
chmod +x "$TARGET_DIR/.delta-11/scripts/"*.sh 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Scripts de operação em .delta-11/scripts/ (raiz do projeto fica limpa)"

# ─── v5.2 (M-19): pasta canônica de docs do comandante ───
mkdir -p "$TARGET_DIR/docs/comandante"

# ─── v5.2: hooks ativos desde o primeiro dia (gap fechado) ───
# Antes, projetos novos nasciam SEM .claude/settings.json — hooks só chegavam
# no primeiro sincronizar.sh. Agora nascem com todos os hooks ligados.
mkdir -p "$TARGET_DIR/.claude"
if [ ! -f "$TARGET_DIR/.claude/settings.json" ]; then
    cp "$SCRIPT_DIR/.delta-11/templates/settings-hooks.json" "$TARGET_DIR/.claude/settings.json"
    echo -e "  ${GREEN}✓${NC} Hooks ativados (.claude/settings.json criado do template)"
fi

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
