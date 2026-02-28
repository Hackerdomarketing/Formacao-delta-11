#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMACAO D-11 — Disparar Agentes (Universal)
# ═══════════════════════════════════════════════════════════════
#
# Este script le os prompts de ativacao gerados pelos agentes
# e abre uma nova instancia do Claude Code para cada agente,
# com o prompt ja colado e enviado automaticamente.
#
# MODOS DE DISPATCH (detectado automaticamente):
#   terminal-app  — Abre aba no Terminal.app com claude CLI (recomendado)
#   vscode-tab    — Abre tab no VS Code via extensao Claude Code (legado)
#   manual        — Mostra instrucoes para o comandante colar manualmente
#
# Como usar:
#   ./disparar.sh                      # Dispara TODOS os agentes pendentes
#   ./disparar.sh VAULT                # Dispara apenas o agente VAULT
#   ./disparar.sh --list               # Lista agentes disponiveis sem disparar
#   ./disparar.sh --mode=terminal-app  # Forca modo terminal
#   ./disparar.sh --mode=vscode-tab    # Forca modo extensao VS Code
#   ./disparar.sh --mode=manual        # Forca modo manual
#   ./disparar.sh --detect             # Re-detecta o modo automaticamente
#
# Os prompts ficam em .delta-11/ativacoes/*.txt
#
# REQUER: macOS com Permissao de Acessibilidade em:
#   System Settings > Privacy & Security > Accessibility
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

ATIVACOES_DIR=".delta-11/ativacoes"
DISPATCH_MODE_FILE=".delta-11/.dispatch-mode"
PROJECT_PATH=$(pwd)

# ═══════════════════════════════════════════════════════════════
# DETECCAO DE MODO
# ═══════════════════════════════════════════════════════════════

detectar_modo() {
    # 1. Preferencia salva
    if [ -f "$DISPATCH_MODE_FILE" ]; then
        local modo_salvo
        modo_salvo=$(cat "$DISPATCH_MODE_FILE" | tr -d '[:space:]')
        if [[ "$modo_salvo" == "terminal-app" || "$modo_salvo" == "vscode-tab" || "$modo_salvo" == "manual" ]]; then
            echo "$modo_salvo"
            return 0
        fi
    fi

    # 2. CLI disponivel? (mais confiavel, zero conflito de lock)
    if command -v claude &>/dev/null; then
        echo "terminal-app" > "$DISPATCH_MODE_FILE"
        echo "terminal-app"
        return 0
    fi

    # 3. Extensao do VS Code instalada?
    if command -v code &>/dev/null && code --list-extensions 2>/dev/null | grep -q "anthropic.claude-code"; then
        echo "vscode-tab" > "$DISPATCH_MODE_FILE"
        echo "vscode-tab"
        return 0
    fi

    # 4. Nada encontrado
    echo "manual" > "$DISPATCH_MODE_FILE"
    echo "manual"
}

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

verificar_saude() {
    local modo="$1"

    if [ "$modo" = "terminal-app" ]; then
        # Verificar se Terminal.app consegue ser ativado
        if ! osascript -e 'tell application "Terminal" to activate' &>/dev/null; then
            echo -e "${RED}x Nao foi possivel ativar o Terminal.app.${NC}"
            echo "  Verifique as permissoes de Acessibilidade em:"
            echo "  System Settings > Privacy & Security > Accessibility"
            return 1
        fi
        # Verificar se claude CLI esta disponivel
        if ! command -v claude &>/dev/null; then
            echo -e "${RED}x Comando 'claude' nao encontrado no PATH.${NC}"
            echo "  Instale o Claude Code CLI: npm install -g @anthropic-ai/claude-code"
            return 1
        fi

    elif [ "$modo" = "vscode-tab" ]; then
        # Verificar se VS Code esta rodando
        if ! pgrep -x "Code" > /dev/null; then
            echo -e "${RED}x VS Code nao esta rodando.${NC}"
            echo "  Abra o VS Code antes de disparar agentes."
            return 1
        fi
        # Verificar se consegue ativar
        if ! osascript -e 'tell application "Visual Studio Code" to activate' &>/dev/null; then
            echo -e "${RED}x Nao foi possivel ativar o VS Code.${NC}"
            echo "  Verifique as permissoes de Acessibilidade em:"
            echo "  System Settings > Privacy & Security > Accessibility"
            return 1
        fi

    elif [ "$modo" = "manual" ]; then
        # Manual sempre funciona
        return 0
    fi

    return 0
}

# ═══════════════════════════════════════════════════════════════
# AVISO ANTI-COLISAO
# ═══════════════════════════════════════════════════════════════

aviso_anti_colisao() {
    local nome="$1"
    local modo="$2"
    local destino="Terminal.app"
    if [ "$modo" = "vscode-tab" ]; then
        destino="VS Code"
    fi

    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║${NC}  ${BOLD}ABRINDO NOVA JANELA${NC}                                        ${RED}║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║${NC}  Disparando: ${BOLD}${CYAN}${nome}${NC}                                       ${RED}║${NC}"
    echo -e "${RED}║${NC}  Destino:    ${DIM}${destino}${NC}                                       ${RED}║${NC}"
    echo -e "${RED}║${NC}  Projeto:    ${DIM}${PROJECT_PATH}${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║${NC}  ${YELLOW}NAO MOVA O MOUSE. NAO DIGITE NADA.${NC}                          ${RED}║${NC}"
    echo -e "${RED}║${NC}  ${YELLOW}Aguarde 5 segundos...${NC}                                       ${RED}║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    sleep 5
}

# ═══════════════════════════════════════════════════════════════
# ESTRATEGIA 1: TERMINAL.APP COM CLAUDE CLI (recomendado)
# ═══════════════════════════════════════════════════════════════
#
# Cada agente roda como processo claude CLI independente em
# uma aba separada do Terminal.app. Zero conflito de lock file.
#
# ═══════════════════════════════════════════════════════════════

disparar_terminal_app() {
    local projeto="$PROJECT_PATH"

    osascript << APPLESCRIPT
tell application "Terminal"
    activate
    delay 0.5

    -- Abrir nova aba
    tell application "System Events"
        tell process "Terminal"
            keystroke "t" using {command down}
        end tell
    end tell
    delay 1

    -- CD para o projeto e iniciar claude CLI
    do script "cd '$projeto' && claude" in front window
    delay 6

    -- Colar o prompt do clipboard
    tell application "System Events"
        tell process "Terminal"
            keystroke "v" using {command down}
            delay 0.5
            keystroke return
        end tell
    end tell
end tell
APPLESCRIPT
}

# ═══════════════════════════════════════════════════════════════
# ESTRATEGIA 2: VS CODE TAB (legado)
# ═══════════════════════════════════════════════════════════════
#
# Abre nova aba do Claude Code dentro do VS Code via extensao.
# ATENCAO: Multiplas instancias podem causar conflito de lock
# file (bug #13287/#13499). Use terminal-app quando possivel.
#
# ═══════════════════════════════════════════════════════════════

disparar_vscode_tab() {
    local projeto="$PROJECT_PATH"

    # Foca a janela do projeto correto via CLI (sem activate global).
    # Isso garante que o Claude Code vai abrir no projeto certo,
    # nao em outra janela do VS Code de outro projeto.
    # NOTA: nao usa "activate" do AppleScript pois isso causa window jumping
    # entre monitores e Spaces no macOS com multiplas janelas abertas.
    if command -v code &>/dev/null && [ -n "$projeto" ]; then
        code --reuse-window "$projeto" 2>/dev/null || true
        sleep 1.5
    fi

    # Envia keystrokes direto ao processo Code (sem activate)
    osascript << 'APPLESCRIPT'
tell application "System Events"
    tell process "Code"
        -- Abrir Command Palette: Cmd+Shift+P
        -- NAO usar "tell application VS Code to activate" aqui --
        -- isso causa window jumping entre monitores e Spaces no macOS
        keystroke "p" using {command down, shift down}
        delay 0.5

        -- Digitar o comando
        keystroke "Claude Code: Open in New Tab"
        delay 1

        -- Pressionar Enter para executar
        keystroke return
        delay 3

        -- Colar o prompt do clipboard (Cmd+V)
        keystroke "v" using {command down}
        delay 0.5

        -- Pressionar Enter para enviar
        keystroke return
    end tell
end tell
APPLESCRIPT
}

# ═══════════════════════════════════════════════════════════════
# ESTRATEGIA 3: MANUAL (fallback)
# ═══════════════════════════════════════════════════════════════

disparar_manual() {
    local arquivo="$1"
    local nome="$2"

    echo ""
    echo -e "  ${YELLOW}[MANUAL]${NC} Auto-dispatch indisponivel para ${BOLD}${nome}${NC}."
    echo -e "  O prompt esta salvo em: ${CYAN}${arquivo}${NC}"
    echo ""
    echo -e "  Para ativar este agente manualmente:"
    echo -e "  1. Abra um terminal"
    echo -e "  2. cd $PROJECT_PATH"
    echo -e "  3. claude"
    echo -e "  4. Cole o conteudo do arquivo acima"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# FUNCAO PRINCIPAL: Disparar um agente
# ═══════════════════════════════════════════════════════════════

disparar_agente() {
    local arquivo="$1"
    local nome="$2"
    local modo="$3"

    if [ "$modo" = "manual" ]; then
        disparar_manual "$arquivo" "$nome"
        return 0
    fi

    # Aviso visual anti-colisao
    aviso_anti_colisao "$nome" "$modo"

    # Copiar prompt para clipboard
    cat "$arquivo" | pbcopy

    # Disparar conforme o modo
    local resultado=0

    if [ "$modo" = "terminal-app" ]; then
        disparar_terminal_app || resultado=$?
    elif [ "$modo" = "vscode-tab" ]; then
        disparar_vscode_tab || resultado=$?
    fi

    # Se falhou, cair para manual
    if [ $resultado -ne 0 ]; then
        echo -e "  ${RED}x Dispatch falhou. Caindo para modo manual.${NC}"
        disparar_manual "$arquivo" "$nome"
    fi

    return 0
}

# ═══════════════════════════════════════════════════════════════
# PARSE DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════

FILTRO=""
MODO_LISTA=false
FORCE_MODE=""
FORCE_DETECT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            MODO_LISTA=true
            shift
            ;;
        --mode=*)
            FORCE_MODE="${1#*=}"
            shift
            ;;
        --detect)
            FORCE_DETECT=true
            shift
            ;;
        --help|-h)
            echo ""
            echo -e "${BOLD}FORMACAO D-11 — Disparar Agentes${NC}"
            echo ""
            echo "  Uso: ./disparar.sh [OPCOES] [AGENTE]"
            echo ""
            echo "  Opcoes:"
            echo "    --list               Lista agentes disponiveis sem disparar"
            echo "    --mode=MODO          Forca um modo: terminal-app, vscode-tab, manual"
            echo "    --detect             Re-detecta o modo automaticamente"
            echo "    --help               Mostra esta ajuda"
            echo ""
            echo "  Exemplos:"
            echo "    ./disparar.sh                      Dispara todos os agentes"
            echo "    ./disparar.sh VAULT                Dispara apenas o VAULT"
            echo "    ./disparar.sh --mode=terminal-app  Forca modo Terminal.app"
            echo "    ./disparar.sh --detect             Re-detecta e mostra o modo"
            echo ""
            echo "  Modos de dispatch:"
            echo "    terminal-app   Abre aba no Terminal.app com claude CLI (recomendado)"
            echo "    vscode-tab     Abre tab no VS Code via extensao (pode travar com muitos agentes)"
            echo "    manual         Mostra instrucoes para colar manualmente"
            echo ""
            exit 0
            ;;
        *)
            FILTRO="$1"
            shift
            ;;
    esac
done

# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FORMACAO D-11 — Disparando Agentes${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# DETECCAO DE MODO
# ═══════════════════════════════════════════════════════════════

if [ "$FORCE_DETECT" = true ]; then
    rm -f "$DISPATCH_MODE_FILE"
    DISPATCH_MODE=$(detectar_modo)
    echo -e "  Modo re-detectado: ${BOLD}${GREEN}${DISPATCH_MODE}${NC}"
    echo -e "  Salvo em: ${DIM}${DISPATCH_MODE_FILE}${NC}"
    echo ""
    if [ "$MODO_LISTA" = false ] && [ -z "$FILTRO" ]; then
        exit 0
    fi
elif [ -n "$FORCE_MODE" ]; then
    if [[ "$FORCE_MODE" != "terminal-app" && "$FORCE_MODE" != "vscode-tab" && "$FORCE_MODE" != "manual" ]]; then
        echo -e "${RED}x Modo invalido: $FORCE_MODE${NC}"
        echo "  Modos validos: terminal-app, vscode-tab, manual"
        exit 1
    fi
    DISPATCH_MODE="$FORCE_MODE"
    echo -e "  Modo forcado: ${BOLD}${YELLOW}${DISPATCH_MODE}${NC}"
else
    DISPATCH_MODE=$(detectar_modo)
    echo -e "  Modo de dispatch: ${BOLD}${GREEN}${DISPATCH_MODE}${NC}"
fi

# Explicacao do modo para o comandante
case $DISPATCH_MODE in
    terminal-app)
        echo -e "  ${DIM}Cada agente vai abrir em uma aba do Terminal.app${NC}"
        ;;
    vscode-tab)
        echo -e "  ${DIM}Cada agente vai abrir em uma aba do Claude Code no VS Code${NC}"
        echo -e "  ${YELLOW}Aviso: muitos agentes no mesmo VS Code podem causar lentidao${NC}"
        ;;
    manual)
        echo -e "  ${DIM}Os prompts serao exibidos para voce colar manualmente${NC}"
        ;;
esac
echo ""

# ═══════════════════════════════════════════════════════════════
# VERIFICAR PASTA DE ATIVACOES
# ═══════════════════════════════════════════════════════════════

if [ ! -d "$ATIVACOES_DIR" ]; then
    echo -e "${RED}x Pasta $ATIVACOES_DIR nao encontrada.${NC}"
    echo ""
    echo "  O ATLAS ainda nao gerou os prompts de ativacao."
    echo "  Primeiro, abra o Claude Code e inicie com: d11"
    echo "  Quando o ATLAS terminar o planejamento,"
    echo "  ele vai criar os arquivos de ativacao automaticamente."
    echo "  Depois, rode este script."
    echo ""
    exit 1
fi

# ═══════════════════════════════════════════════════════════════
# LISTAR ARQUIVOS DE ATIVACAO
# ═══════════════════════════════════════════════════════════════

if [ -n "$FILTRO" ]; then
    ARQUIVOS=($(ls "$ATIVACOES_DIR"/*"$FILTRO"*.txt 2>/dev/null || true))
else
    ARQUIVOS=($(ls "$ATIVACOES_DIR"/*.txt 2>/dev/null || true))
fi

if [ ${#ARQUIVOS[@]} -eq 0 ]; then
    echo -e "${RED}x Nenhum arquivo de ativacao encontrado${NC}"
    if [ -n "$FILTRO" ]; then
        echo "  Filtro usado: $FILTRO"
        echo "  Arquivos disponiveis:"
        ls "$ATIVACOES_DIR"/*.txt 2>/dev/null | while read f; do
            echo "    - $(basename "$f" .txt)"
        done
    fi
    echo ""
    exit 1
fi

echo -e "  Encontrados ${BOLD}${#ARQUIVOS[@]} agente(s)${NC} para ativar:"
echo ""

for arquivo in "${ARQUIVOS[@]}"; do
    nome=$(basename "$arquivo" .txt)
    tamanho=$(wc -c < "$arquivo" | tr -d ' ')
    echo -e "    > ${CYAN}${nome}${NC} (${tamanho} bytes)"
done

echo ""

# Modo lista: so mostra e sai
if [ "$MODO_LISTA" = true ]; then
    echo "  Use ./disparar.sh para disparar todos."
    echo "  Use ./disparar.sh NOME para disparar um especifico."
    echo ""
    exit 0
fi

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

if ! verificar_saude "$DISPATCH_MODE"; then
    echo ""
    echo -e "  ${YELLOW}Dica: tente outro modo com --mode=terminal-app ou --mode=manual${NC}"
    echo ""
    exit 1
fi

# ═══════════════════════════════════════════════════════════════
# CONFIRMACAO
# ═══════════════════════════════════════════════════════════════

read -p "  Disparar agora? (s/n): " CONFIRMA

if [[ "$CONFIRMA" != "s" && "$CONFIRMA" != "S" ]]; then
    echo "  Abortado."
    exit 0
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# LOOP DE DISPATCH
# ═══════════════════════════════════════════════════════════════

CONTADOR=0
DELAY_ENTRE_AGENTES=8

if [ "$DISPATCH_MODE" = "vscode-tab" ]; then
    DELAY_ENTRE_AGENTES=5
elif [ "$DISPATCH_MODE" = "manual" ]; then
    DELAY_ENTRE_AGENTES=0
fi

for arquivo in "${ARQUIVOS[@]}"; do
    nome=$(basename "$arquivo" .txt)
    CONTADOR=$((CONTADOR + 1))

    echo -e "  ${YELLOW}[$CONTADOR/${#ARQUIVOS[@]}]${NC} Ativando ${BOLD}${nome}${NC}..."

    disparar_agente "$arquivo" "$nome" "$DISPATCH_MODE"

    if [ $CONTADOR -lt ${#ARQUIVOS[@]} ] && [ $DELAY_ENTRE_AGENTES -gt 0 ]; then
        echo -e "  ${CYAN}Aguardando ${DELAY_ENTRE_AGENTES}s antes do proximo agente...${NC}"
        sleep "$DELAY_ENTRE_AGENTES"
    fi
done

# ═══════════════════════════════════════════════════════════════
# CONCLUSAO
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  OK ${CONTADOR} agente(s) disparado(s) com sucesso${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

case $DISPATCH_MODE in
    terminal-app)
        echo -e "  Cada agente esta rodando em uma aba do Terminal.app."
        echo -e "  Alterne entre as abas com ${BOLD}Cmd+Shift+[${NC} e ${BOLD}Cmd+Shift+]${NC}"
        ;;
    vscode-tab)
        echo -e "  Cada agente esta rodando em uma aba do Claude Code no VS Code."
        echo -e "  Alterne entre as abas dentro do VS Code."
        ;;
    manual)
        echo -e "  Os prompts foram exibidos acima."
        echo -e "  Abra um terminal para cada agente, cd para o projeto, rode 'claude', e cole."
        ;;
esac

echo ""
echo -e "  Para acompanhar o progresso:"
echo -e "  > Abra o painel visual: .delta-11/painel.html"
echo ""
