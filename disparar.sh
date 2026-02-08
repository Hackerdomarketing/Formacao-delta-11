#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMACAO D-11 — Disparar Agentes
# ═══════════════════════════════════════════════════════════════
#
# Este script le os prompts de ativacao gerados pelos agentes
# e abre uma nova aba do Claude Code no VS Code para cada agente,
# com o prompt ja colado e enviado automaticamente.
#
# Como usar:
#   ./disparar.sh              # Dispara TODOS os agentes pendentes
#   ./disparar.sh VAULT        # Dispara apenas o agente VAULT
#   ./disparar.sh --list       # Lista agentes disponiveis sem disparar
#
# Os prompts ficam em .delta-11/ativacoes/*.txt
# Cada arquivo e lido, copiado para o clipboard, e colado
# em uma nova aba do Claude Code via AppleScript + VS Code.
#
# REQUER: macOS com VS Code e extensao Claude Code instalada.
# REQUER: Permissao de Acessibilidade para Terminal em:
#   System Settings > Privacy & Security > Accessibility
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
echo -e "${BOLD}  FORMACAO D-11 — Disparando Agentes${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# Verificar se a pasta de ativacoes existe
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

# Filtro por agente especifico
FILTRO=""
if [ "$1" == "--list" ]; then
    MODO_LISTA=true
elif [ -n "$1" ]; then
    FILTRO="$1"
fi

# Contar arquivos de ativacao
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

read -p "  Disparar agora? (s/n): " CONFIRMA

if [[ "$CONFIRMA" != "s" && "$CONFIRMA" != "S" ]]; then
    echo "  Abortado."
    exit 0
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# FUNCAO PRINCIPAL: Disparar um agente no VS Code
# ═══════════════════════════════════════════════════════════════
#
# Tecnica: AppleScript controla o VS Code via System Events
# 1. Copia o prompt para o clipboard (pbcopy)
# 2. Ativa o VS Code
# 3. Abre Command Palette (Cmd+Shift+P)
# 4. Digita "Claude Code: Open in New Tab"
# 5. Pressiona Enter
# 6. Aguarda a aba abrir
# 7. Cola o prompt (Cmd+V)
# 8. Pressiona Enter para enviar
#
# ═══════════════════════════════════════════════════════════════

disparar_agente() {
    local arquivo="$1"
    local nome="$2"

    # Copiar prompt para clipboard
    cat "$arquivo" | pbcopy

    # Executar sequencia AppleScript
    osascript << 'APPLESCRIPT'
tell application "Visual Studio Code"
    activate
end tell

delay 1

tell application "System Events"
    tell process "Code"
        -- Abrir Command Palette: Cmd+Shift+P
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

CONTADOR=0

for arquivo in "${ARQUIVOS[@]}"; do
    nome=$(basename "$arquivo" .txt)
    CONTADOR=$((CONTADOR + 1))

    echo -e "  ${YELLOW}[$CONTADOR/${#ARQUIVOS[@]}]${NC} Ativando ${BOLD}${nome}${NC}..."

    disparar_agente "$arquivo" "$nome"

    if [ $CONTADOR -lt ${#ARQUIVOS[@]} ]; then
        echo -e "  ${CYAN}Aguardando 5s antes do proximo agente...${NC}"
        sleep 5
    fi
done

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  OK ${CONTADOR} agente(s) disparado(s) com sucesso${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Cada agente esta rodando em uma aba do Claude Code no VS Code."
echo -e "  Eles ja estao lendo seus arquivos e comecando a trabalhar."
echo ""
echo -e "  Para acompanhar:"
echo -e "  > Alterne entre as abas do Claude Code no VS Code"
echo -e "  > Abra o painel visual: .delta-11/painel.html"
echo ""
