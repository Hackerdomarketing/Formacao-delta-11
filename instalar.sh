#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Script de Instalação para macOS
# ═══════════════════════════════════════════════════════════════
#
# O que este script faz:
# 1. Verifica se você tem tudo que precisa instalado (git, gh)
# 2. Cria o repositório privado no seu GitHub
# 3. Faz o primeiro commit e push
# 4. Instala a extensão Live Server no VS Code (para o painel)
# 5. Abre o VS Code com o projeto
# 6. Abre o painel visual no navegador
#
# Como usar:
#   1. Abra o Terminal do macOS
#   2. Navegue até a pasta onde estão os arquivos da Formação Δ-11
#   3. Execute: chmod +x instalar.sh && ./instalar.sh
#
# ═══════════════════════════════════════════════════════════════

set -e

# Cores para o terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}        FORMAÇÃO Δ-11 — Instalação${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── PASSO 1: Verificar pré-requisitos ───────────────────────

echo -e "${YELLOW}[1/6]${NC} Verificando pré-requisitos..."

# Verificar Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git não encontrado.${NC}"
    echo "  Instale com: xcode-select --install"
    echo "  Ou baixe de: https://git-scm.com/download/mac"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git encontrado: $(git --version)"

# Verificar GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI (gh) não encontrado.${NC}"
    echo ""
    echo "  Instale com Homebrew:"
    echo "    brew install gh"
    echo ""
    echo "  Se você não tem o Homebrew, instale primeiro:"
    echo "    /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "  Depois rode este script novamente."
    exit 1
fi
echo -e "  ${GREEN}✓${NC} GitHub CLI encontrado: $(gh --version | head -1)"

# Verificar se gh está autenticado
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}  ⚠ GitHub CLI não está autenticado.${NC}"
    echo "  Vou iniciar o processo de autenticação agora..."
    echo ""
    gh auth login
    echo ""
fi
echo -e "  ${GREEN}✓${NC} GitHub CLI autenticado"

# Verificar VS Code CLI
if ! command -v code &> /dev/null; then
    echo -e "${YELLOW}  ⚠ Comando 'code' do VS Code não encontrado.${NC}"
    echo "  Para instalar:"
    echo "    1. Abra o VS Code"
    echo "    2. Pressione Cmd+Shift+P"
    echo "    3. Digite 'Shell Command: Install code command in PATH'"
    echo "    4. Selecione e confirme"
    echo ""
    VSCODE_AVAILABLE=false
else
    echo -e "  ${GREEN}✓${NC} VS Code CLI encontrado"
    VSCODE_AVAILABLE=true
fi

echo ""

# ─── PASSO 2: Configurar nome do repositório ─────────────────

echo -e "${YELLOW}[2/6]${NC} Configuração do repositório..."
echo ""

# Pegar nome do usuário no GitHub
GH_USER=$(gh api user --jq '.login')
echo -e "  Conta GitHub: ${CYAN}${GH_USER}${NC}"
echo ""

# Perguntar nome do repositório
DEFAULT_REPO="formacao-delta-11"
read -p "  Nome do repositório [$DEFAULT_REPO]: " REPO_NAME
REPO_NAME=${REPO_NAME:-$DEFAULT_REPO}

echo ""

# Verificar se o repositório já existe
if gh repo view "${GH_USER}/${REPO_NAME}" &> /dev/null; then
    echo -e "${YELLOW}  ⚠ O repositório '${REPO_NAME}' já existe.${NC}"
    read -p "  Deseja usar o existente? (s/n): " USE_EXISTING
    if [[ "$USE_EXISTING" != "s" && "$USE_EXISTING" != "S" ]]; then
        echo "  Abortado. Rode o script novamente com outro nome."
        exit 1
    fi
    REPO_EXISTS=true
else
    REPO_EXISTS=false
fi

echo ""

# ─── PASSO 3: Verificar se os arquivos estão aqui ────────────

echo -e "${YELLOW}[3/6]${NC} Verificando arquivos da Formação Δ-11..."

if [ ! -f "CLAUDE.md" ]; then
    echo -e "${RED}✗ Arquivo CLAUDE.md não encontrado nesta pasta.${NC}"
    echo "  Certifique-se de que você está na pasta que contém os arquivos da Formação Δ-11."
    echo "  A estrutura deve ser:"
    echo "    CLAUDE.md"
    echo "    GUIA-DO-COMANDANTE.md"
    echo "    .delta-11/"
    echo "    instalar.sh (este script)"
    exit 1
fi

if [ ! -d ".delta-11" ]; then
    echo -e "${RED}✗ Pasta .delta-11 não encontrada.${NC}"
    echo "  Certifique-se de que a pasta .delta-11 está aqui (ela é oculta)."
    echo "  Use 'ls -la' para verificar."
    exit 1
fi

FILE_COUNT=$(find . -type f -not -path './.git/*' -not -name 'instalar.sh' -not -name '.DS_Store' | wc -l | xargs)
echo -e "  ${GREEN}✓${NC} ${FILE_COUNT} arquivos encontrados"
echo ""

# ─── PASSO 4: Inicializar Git e criar repositório ────────────

echo -e "${YELLOW}[4/6]${NC} Configurando repositório Git..."

# Criar .gitignore
cat > .gitignore << 'EOF'
.DS_Store
*.swp
*.swo
*~
.vscode/settings.json
node_modules/
EOF

# Inicializar git se necessário
if [ ! -d ".git" ]; then
    git init -b main
    echo -e "  ${GREEN}✓${NC} Git inicializado"
fi

# Criar repositório no GitHub se não existe
if [ "$REPO_EXISTS" = false ]; then
    echo "  Criando repositório privado no GitHub..."
    gh repo create "$REPO_NAME" --private --source=. --remote=origin
    echo -e "  ${GREEN}✓${NC} Repositório privado criado: ${CYAN}https://github.com/${GH_USER}/${REPO_NAME}${NC}"
else
    # Verificar se o remote já existe
    if ! git remote get-url origin &> /dev/null; then
        git remote add origin "https://github.com/${GH_USER}/${REPO_NAME}.git"
    fi
    echo -e "  ${GREEN}✓${NC} Usando repositório existente"
fi

echo ""

# ─── PASSO 5: Commit e Push ──────────────────────────────────

echo -e "${YELLOW}[5/6]${NC} Fazendo commit e push..."

git add -A
git commit -m "Formação Δ-11 — Sistema operacional de desenvolvimento por inteligência artificial

Sistema completo com 10 agentes especializados:
- ATLAS (arquiteto), CRONOS (gerente), FRONT, BACK (líderes técnicos)
- PIXEL, FORM, ENGINE, VAULT (executores)
- SHIELD (qualidade), SCOUT (correção de erros)

Inclui: protocolos, kanban, painel visual, templates de memória.
" 2>/dev/null || echo "  (nenhuma mudança para commitar)"

git push -u origin main 2>/dev/null || git push origin main
echo -e "  ${GREEN}✓${NC} Código enviado para o GitHub"
echo ""

# ─── PASSO 5.5: Registrar no registry global ──────────────────

REGISTRY="$HOME/.delta-11-registry.json"
PROJECT_PATH="$(pwd)"

if command -v jq &> /dev/null; then
    if [ -f "$REGISTRY" ]; then
        # Verificar se o projeto ja esta registrado
        ALREADY=$(jq --arg p "$PROJECT_PATH" '.projects | index($p)' "$REGISTRY")
        if [ "$ALREADY" = "null" ]; then
            echo -e "  Registrando projeto no registry global..."
            TMP_REG=$(mktemp)
            jq --arg p "$PROJECT_PATH" '.projects += [$p]' "$REGISTRY" > "$TMP_REG" && mv "$TMP_REG" "$REGISTRY"
            echo -e "  ${GREEN}✓${NC} Projeto registrado em $REGISTRY"
        else
            echo -e "  ${GREEN}✓${NC} Projeto ja registrado no registry"
        fi
    else
        # Criar registry novo
        echo -e "  Criando registry global..."
        cat > "$REGISTRY" << REGEOF
{
  "version": "3.2",
  "source": "/Users/alfa/projetos/Formacao-delta-11",
  "github": "https://github.com/Hackerdomarketing/Formacao-delta-11.git",
  "projects": ["$PROJECT_PATH"],
  "backup": null,
  "historical": null,
  "last_sync": null
}
REGEOF
        echo -e "  ${GREEN}✓${NC} Registry criado em $REGISTRY"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} jq nao encontrado — registro no registry ignorado"
    echo "    Instale jq (brew install jq) e rode sincronizar.sh depois"
fi

echo ""

# ─── PASSO 6: Abrir tudo ─────────────────────────────────────

echo -e "${YELLOW}[6/6]${NC} Abrindo ambiente de trabalho..."

# Instalar extensão Live Server no VS Code (se VS Code disponível)
if [ "$VSCODE_AVAILABLE" = true ]; then
    echo "  Instalando extensão Live Server..."
    code --install-extension ritwickdey.LiveServer 2>/dev/null && \
        echo -e "  ${GREEN}✓${NC} Live Server instalado" || \
        echo -e "  ${YELLOW}⚠${NC} Live Server já instalado ou erro (pode ignorar)"

    echo "  Abrindo VS Code..."
    code .
    echo -e "  ${GREEN}✓${NC} VS Code aberto com o projeto"
fi

# Abrir o painel no navegador
echo "  Abrindo painel visual no navegador..."
open .delta-11/painel.html 2>/dev/null || \
    echo -e "  ${YELLOW}⚠${NC} Não foi possível abrir automaticamente. Abra manualmente: .delta-11/painel.html"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✓ INSTALAÇÃO COMPLETA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Repositório:${NC} https://github.com/${GH_USER}/${REPO_NAME}"
echo -e "  ${BOLD}Painel:${NC}      .delta-11/painel.html"
echo ""
echo -e "  ${BOLD}Para começar um projeto:${NC}"
echo -e "  1. Abra uma janela do Claude Code no VS Code"
echo -e "  2. Digite: ${CYAN}d11${NC}"
echo -e "  3. Descreva o que quer construir"
echo -e "  4. Siga as instruções — o sistema te guia"
echo ""
echo -e "  ${BOLD}Para acompanhar:${NC}"
echo -e "  • Kanban no VS Code: abra ${CYAN}.delta-11/kanban.md${NC} e pressione Ctrl+Shift+V"
echo -e "  • Painel visual: clique direito em ${CYAN}.delta-11/painel.html${NC} → Open with Live Server"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
