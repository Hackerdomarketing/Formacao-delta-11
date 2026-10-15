#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Instalação (v6.3) — macOS, com apoio a Linux
# ═══════════════════════════════════════════════════════════════
#
# Rode este script UMA vez, dentro da pasta da Formação Δ-11 (a fonte
# oficial: onde ficam CLAUDE.md, .delta-11/ e este arquivo).
#
# O que ele faz, nesta ordem:
# 1. Confere se você tem o que precisa (git, python3, node, jq; gh e VS Code são opcionais)
# 2. Confere se os arquivos da Formação Δ-11 estão nesta pasta
# 3. Protege o .gitignore (acrescenta — NUNCA apaga o que você já tem):
#    senhas (.env), chaves (*.pem, *.key), credentials.json e o estado de execução
# 4. Anota esta pasta como FONTE no registro central (~/.delta-11-registry.json)
#    e cria a memória entre projetos (~/.delta-11/aprendizados-entre-projetos.md)
# 5. (macOS) Liga o monitor automático: gera o LaunchAgent com o caminho REAL
#    desta pasta e recarrega com launchctl — com sua confirmação
# 6. (Opcional) Guarda esta pasta num repositório PRIVADO do GitHub:
#    mostra o "git status" antes de adicionar, recusa se achar segredo e pede
#    confirmação antes de criar o repositório e de enviar (push)
# 7. Abre o VS Code e o painel visual
#
# Como usar:
#   1. Abra o Terminal
#   2. Entre na pasta da Formação Δ-11
#   3. Execute: bash instalar.sh
#
# Variável opcional (usada pelos testes):
#   DELTA11_REGISTRY   caminho do registro (padrão ~/.delta-11-registry.json)
#
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

FONTE="$(cd "$(dirname "$0")" && pwd -P)"
cd "$FONTE"
REGISTRY="${DELTA11_REGISTRY:-$HOME/.delta-11-registry.json}"
PASTA_D11_USUARIO="$HOME/.delta-11"
APRENDIZADOS="$PASTA_D11_USUARIO/aprendizados-entre-projetos.md"

perguntar() {
    # perguntar "texto" → 0 se a pessoa respondeu s/S
    local resposta=""
    read -r -p "  $1 (s/n): " resposta || resposta=""
    [[ "$resposta" == "s" || "$resposta" == "S" ]]
}

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}        FORMAÇÃO Δ-11 — Instalação (v6.3)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── PASSO 1: Pré-requisitos ──────────────────────────────────

echo -e "${YELLOW}[1/7]${NC} Verificando pré-requisitos..."

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git não encontrado.${NC}"
    echo "  Instale com: xcode-select --install"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git: $(git --version)"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ python3 não encontrado (os vigias e o monitor precisam dele).${NC}"
    echo "  Instale com: xcode-select --install   (ou: brew install python)"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} $(python3 --version)"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ node não encontrado (os vigias de trava e de diário são em JavaScript).${NC}"
    echo "  Instale com: brew install node   (ou baixe em https://nodejs.org)"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} node: $(node --version)"

if command -v jq &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} jq: $(jq --version)"
else
    echo -e "  ${YELLOW}⚠${NC} jq não encontrado — o sincronizar.sh precisa dele. Instale com: brew install jq"
fi

VSCODE_AVAILABLE=false
if command -v code &> /dev/null; then
    VSCODE_AVAILABLE=true
    echo -e "  ${GREEN}✓${NC} VS Code (comando 'code')"
else
    echo -e "  ${DIM}  VS Code (comando 'code') não encontrado — opcional${NC}"
fi
echo ""

# ─── PASSO 2: Arquivos da Formação Δ-11 ───────────────────────

echo -e "${YELLOW}[2/7]${NC} Verificando arquivos da Formação Δ-11..."

if [ ! -f "CLAUDE.md" ] || [ ! -d ".delta-11" ]; then
    echo -e "${RED}✗ Não achei CLAUDE.md e a pasta .delta-11 aqui ($FONTE).${NC}"
    echo "  Rode este script dentro da pasta da Formação Δ-11."
    exit 1
fi
FILE_COUNT=$(find . -type f -not -path './.git/*' -not -name '.DS_Store' | wc -l | xargs)
echo -e "  ${GREEN}✓${NC} ${FILE_COUNT} arquivos encontrados em $FONTE"
echo ""

# ─── PASSO 3: .gitignore protegido (C-147) ────────────────────

echo -e "${YELLOW}[3/7]${NC} Protegendo senhas e chaves no .gitignore..."

LINHAS_GITIGNORE=(
    ".env" ".env.*" "!.env.example" "*.pem" "*.key" "credentials.json"
    ".claude/settings.local.json" ".DS_Store" ".vscode/settings.json" "node_modules/"
    ".delta-11/activity-log.md" ".delta-11/monitor-status.json" ".delta-11/monitor-data.js"
    ".delta-11/pulsos-data.js" ".delta-11/ativacoes/" ".delta-11/locks/*" "!.delta-11/locks/.gitkeep"
    ".delta-11/scratch/*" "!.delta-11/scratch/README.md" ".delta-11/logs/sub-agentes/*.log"
    ".claude/worktrees/" "__pycache__/" "*.pyc"
)
FALTANDO=()
for linha in "${LINHAS_GITIGNORE[@]}"; do
    if [ ! -f .gitignore ] || ! grep -Fxq -- "$linha" .gitignore; then
        FALTANDO+=("$linha")
    fi
done
if [ ${#FALTANDO[@]} -gt 0 ]; then
    {
        [ -s .gitignore ] && echo ""
        echo "# ─── Formação Δ-11 (v6.3): segredos e estado de execução nunca vão ao GitHub ───"
        printf '%s\n' "${FALTANDO[@]}"
    } >> .gitignore
    echo -e "  ${GREEN}✓${NC} ${#FALTANDO[@]} linha(s) de proteção acrescentadas (nada do que já existia foi apagado)"
else
    echo -e "  ${GREEN}✓${NC} .gitignore já protegia tudo"
fi
echo ""

# ─── PASSO 4: Registro central + memória entre projetos ───────

echo -e "${YELLOW}[4/7]${NC} Registro central e memória entre projetos..."

python3 - "$REGISTRY" "$FONTE" << 'PY'
import json, os, sys, tempfile
registro, fonte = sys.argv[1], sys.argv[2]
dados = {}
if os.path.exists(registro):
    try:
        with open(registro, encoding="utf-8") as f:
            dados = json.load(f)
    except Exception:
        print("  ✗ O registro %s não é um JSON válido — não mexi nele." % registro)
        sys.exit(0)
antiga = dados.get("source")
if antiga and os.path.realpath(os.path.expanduser(antiga)) != fonte:
    print("  ⚠ O registro apontava a fonte para: %s" % antiga)
    print("    Agora aponta para esta pasta: %s" % fonte)
    dados["source_anterior"] = antiga
dados["source"] = fonte
dados["version"] = "6.3"
dados.setdefault("projects", [])
pasta = os.path.dirname(os.path.abspath(registro))
os.makedirs(pasta, exist_ok=True)
fd, tmp = tempfile.mkstemp(dir=pasta)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
    f.write("\n")
os.replace(tmp, registro)
print("  ✓ Registro central: %s (fonte = %s)" % (registro, fonte))
PY

if [ ! -f "$APRENDIZADOS" ]; then
    mkdir -p "$PASTA_D11_USUARIO"
    cat > "$APRENDIZADOS" << 'EOF'
# Aprendizados entre projetos — Formação Δ-11

> Lições que valem para QUALQUER projeto. O ATLAS lê este arquivo na Fase 0 e na Fase 2.
> O CRONOS acrescenta de 3 a 5 lições ao fim de cada ciclo e na Fase 7.
> Formato de cada lição: `- [AAAA-MM-DD] [projeto] lição em uma frase — por quê`.

## Lições
EOF
    echo -e "  ${GREEN}✓${NC} Memória entre projetos criada: $APRENDIZADOS"
else
    echo -e "  ${GREEN}✓${NC} Memória entre projetos já existe: $APRENDIZADOS"
fi
echo ""

# ─── PASSO 5: Monitor automático (C-062) ──────────────────────

echo -e "${YELLOW}[5/7]${NC} Monitor automático (avisa quando um agente trava)..."

MODELO_PLIST="$FONTE/com.delta11.monitor.plist"
if [ "$(uname -s)" = "Darwin" ] && command -v launchctl &> /dev/null && [ -f "$MODELO_PLIST" ]; then
    DESTINO_PLIST="$HOME/Library/LaunchAgents/com.delta11.monitor.plist"
    PASTA_LOGS="$PASTA_D11_USUARIO/logs"
    if [ -f "$DESTINO_PLIST" ]; then
        echo "  Já existe um monitor instalado. Hoje ele roda:"
        grep -A2 "<key>ProgramArguments</key>" "$DESTINO_PLIST" | grep "<string>" | sed 's/^[[:space:]]*/    /'
    fi
    if perguntar "Ligar o monitor usando o script DESTA pasta ($FONTE/monitor-delta11.sh)?"; then
        mkdir -p "$PASTA_LOGS" "$(dirname "$DESTINO_PLIST")"
        python3 - "$MODELO_PLIST" "$DESTINO_PLIST" "$FONTE" "$PASTA_LOGS" << 'PY'
import sys
from xml.sax.saxutils import escape
modelo, destino, fonte, logs = sys.argv[1:5]
texto = open(modelo, encoding="utf-8").read()
texto = texto.replace("__CAMINHO_DA_FONTE__", escape(fonte)).replace("__PASTA_DE_LOGS__", escape(logs))
open(destino, "w", encoding="utf-8").write(texto)
PY
        if command -v plutil &> /dev/null && ! plutil -lint "$DESTINO_PLIST" > /dev/null; then
            echo -e "  ${RED}✗ O arquivo gerado ficou inválido; o monitor não foi ligado.${NC}"
        else
            DOMINIO="gui/$(id -u)"
            launchctl bootout "$DOMINIO" "$DESTINO_PLIST" 2>/dev/null || launchctl unload "$DESTINO_PLIST" 2>/dev/null || true
            if launchctl bootstrap "$DOMINIO" "$DESTINO_PLIST" 2>/dev/null || launchctl load "$DESTINO_PLIST" 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} Monitor ligado (a cada 5 min). Registro em $PASTA_LOGS/monitor.log"
            else
                echo -e "  ${YELLOW}⚠${NC} Não consegui recarregar o monitor agora. Ele liga no próximo login."
            fi
            echo -e "  ${DIM}Se os projetos ficam em Documentos ou Downloads, o macOS pode bloquear o monitor.${NC}"
            echo -e "  ${DIM}Para liberar: Ajustes do Sistema > Privacidade e Segurança > Acesso Total ao Disco > ative o /bin/bash.${NC}"
        fi
    else
        echo -e "  ${DIM}Monitor não alterado.${NC}"
    fi
else
    echo -e "  ${DIM}Fora do macOS o monitor automático não é instalado.${NC}"
    echo -e "  ${DIM}Use .delta-11/scripts/vigilante.sh num terminal, ou agende o monitor (a cada 5 min):${NC}"
    echo -e "  ${DIM}  */5 * * * * /bin/bash \"$FONTE/monitor-delta11.sh\" >> \"$PASTA_D11_USUARIO/logs/monitor.log\" 2>&1${NC}"
fi
echo ""

# ─── PASSO 6: Git e GitHub (opcional, sempre com confirmação) ──

echo -e "${YELLOW}[6/7]${NC} Repositório (opcional)..."

GH_USER=""
REPO_NAME=""
if perguntar "Quer guardar esta pasta num repositório PRIVADO do seu GitHub?"; then
    if ! command -v gh &> /dev/null; then
        echo -e "  ${YELLOW}⚠${NC} GitHub CLI (gh) não encontrado. Instale com: brew install gh — e rode o instalar.sh de novo."
    else
        if ! gh auth status &> /dev/null; then
            echo -e "  ${YELLOW}⚠${NC} O gh precisa da sua conta do GitHub. Vou abrir o login agora (passo seu)."
            gh auth login
        fi
        GH_USER=$(gh api user --jq '.login')
        echo -e "  Conta GitHub: ${CYAN}${GH_USER}${NC}"

        [ -d ".git" ] || { git init -b main > /dev/null; echo -e "  ${GREEN}✓${NC} Git inicializado"; }

        # Segredo nunca vai: se algum arquivo sensível seria enviado, PARA tudo.
        SENSIVEIS=$(git ls-files --cached --others --exclude-standard | \
            grep -E '(^|/)(\.env(\..+)?|credentials\.json|[^/]*\.pem|[^/]*\.key|settings\.local\.json)$' | \
            grep -vE '(^|/)\.env\.example$' || true)
        if [ -n "$SENSIVEIS" ]; then
            echo -e "  ${RED}✗ Achei arquivos que parecem senha ou chave e iriam para o GitHub:${NC}"
            echo "$SENSIVEIS" | sed 's/^/      /'
            echo "  Nada foi enviado. Tire esses arquivos do git (git rm --cached <arquivo>) e rode de novo."
            exit 1
        fi

        echo "  Isto é o que o git vai guardar (git status):"
        git status --short | head -40 | sed 's/^/    /'
        TOTAL_STATUS=$(git status --short | wc -l | xargs)
        [ "$TOTAL_STATUS" -gt 40 ] && echo "    ... e mais $((TOTAL_STATUS - 40)) arquivo(s)"

        if [ "$TOTAL_STATUS" -gt 0 ] && perguntar "Adicionar estes arquivos e fazer o commit?"; then
            git add -A
            git commit -q -m "Formação Δ-11 — sistema de desenvolvimento com 10 agentes (v6.3)" \
                && echo -e "  ${GREEN}✓${NC} Commit feito"
        fi

        DEFAULT_REPO="formacao-delta-11"
        read -r -p "  Nome do repositório [$DEFAULT_REPO]: " REPO_NAME || REPO_NAME=""
        REPO_NAME=${REPO_NAME:-$DEFAULT_REPO}

        if gh repo view "${GH_USER}/${REPO_NAME}" &> /dev/null; then
            echo -e "  ${YELLOW}⚠${NC} O repositório ${REPO_NAME} já existe na sua conta."
            if perguntar "Enviar (push) para o repositório existente ${GH_USER}/${REPO_NAME}?"; then
                git remote get-url origin &> /dev/null || git remote add origin "https://github.com/${GH_USER}/${REPO_NAME}.git"
                git push -u origin main && echo -e "  ${GREEN}✓${NC} Enviado para o GitHub"
            else
                echo -e "  ${DIM}Nada foi enviado.${NC}"
            fi
        elif perguntar "Criar o repositório PRIVADO ${GH_USER}/${REPO_NAME} e enviar (push)?"; then
            gh repo create "$REPO_NAME" --private --source=. --remote=origin --push \
                && echo -e "  ${GREEN}✓${NC} Repositório privado criado: ${CYAN}https://github.com/${GH_USER}/${REPO_NAME}${NC}"
        else
            echo -e "  ${DIM}Nada foi enviado.${NC}"
        fi
    fi
else
    echo -e "  ${DIM}Pulado — nada foi enviado para a internet.${NC}"
fi
echo ""

# ─── PASSO 7: Abrir o ambiente ────────────────────────────────

echo -e "${YELLOW}[7/7]${NC} Abrindo o ambiente de trabalho..."

if [ "$VSCODE_AVAILABLE" = true ]; then
    code . && echo -e "  ${GREEN}✓${NC} VS Code aberto"
fi

# Painel: tenta várias plataformas antes de pedir ao humano (AP#12)
( open .delta-11/painel.html 2>/dev/null || \
  xdg-open .delta-11/painel.html 2>/dev/null || \
  start .delta-11/painel.html 2>/dev/null || \
  (which sensible-browser >/dev/null 2>&1 && sensible-browser .delta-11/painel.html) || \
  echo -e "  ${YELLOW}⚠${NC} Não consegui abrir sozinho. Abra o arquivo .delta-11/painel.html no navegador." )

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✓ INSTALAÇÃO COMPLETA${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
[ -n "$REPO_NAME" ] && [ -n "$GH_USER" ] && echo -e "  ${BOLD}Repositório:${NC} https://github.com/${GH_USER}/${REPO_NAME}"
echo -e "  ${BOLD}Fonte oficial:${NC} $FONTE"
echo ""
echo -e "  ${BOLD}Para começar um projeto:${NC}"
echo -e "  1. Crie a pasta do projeto: ${CYAN}bash $FONTE/novo-projeto.sh ~/projetos/meu-app${NC}"
echo -e "  2. Abra o Claude Code nessa pasta e digite: ${CYAN}d11${NC}"
echo -e "  3. O painel visual abre sozinho; descreva o que quer construir"
echo ""
echo -e "  ${BOLD}Para levar melhorias do sistema aos projetos:${NC} ${CYAN}bash $FONTE/sincronizar.sh${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
