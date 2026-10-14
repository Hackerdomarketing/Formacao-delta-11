#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Vigilante (Monitor de Atividade de UM projeto) — v6.3
# ═══════════════════════════════════════════════════════════════
#
# Funciona em: macOS, Linux, Windows (Git Bash) e WSL.
#
# O que este script faz:
# Fica rodando no fundo e verifica se os agentes Δ-11 do projeto estão
# trabalhando. Se algo parar (15 min sem movimento, tarefa em FAZENDO sem
# agente, bloqueio no quadro), ele:
#   1. mostra uma notificação no sistema;
#   2. REGISTRA o problema no activity-log (linha do vigilante);
#   3. deixa o aviso para o CRONOS em .delta-11/ativacoes/aviso-vigilante.txt.
# Quem retoma agentes é SEMPRE o CRONOS, pelo Agent tool (D3/D5). O vigilante
# não dispara nada e não pede para ninguém abrir janela (C-066).
#
# Diferença para o monitor-delta11.sh: o monitor roda sozinho (LaunchAgent)
# e olha TODOS os projetos; o vigilante é para acompanhar UM projeto num
# terminal aberto (útil fora do macOS, onde não há LaunchAgent).
#
# Como usar (de qualquer pasta do projeto ou de uma worktree):
#   .delta-11/scripts/vigilante.sh           # roda até você fechar
#   .delta-11/scripts/vigilante.sh --once    # verifica uma vez e sai
#   .delta-11/scripts/vigilante.sh --stop    # para o vigilante em segundo plano
#
# ═══════════════════════════════════════════════════════════════

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

INTERVALO=300          # verificar a cada 5 minutos (segundos)
LIMITE_SILENCIO=900    # alertar após 15 minutos sem atividade (segundos)
AGENTES="ATLAS CRONOS FRONT PIXEL FORM BACK ENGINE VAULT SHIELD SCOUT"

# ─── Descobrir a pasta PRINCIPAL do projeto (D25) ─────────────
# Funciona chamado da raiz, de .delta-11/scripts/ ou de dentro de uma worktree.
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
    BASE="$(pwd -P)"
else
    case "$SCRIPT_DIR" in
        */.delta-11/scripts) BASE="${SCRIPT_DIR%/.delta-11/scripts}" ;;
        *) BASE="$(pwd -P)" ;;
    esac
fi
PROJECT_PATH="$(descobrir_pasta_principal "$BASE")"
DELTA_DIR="$PROJECT_PATH/.delta-11"
ATIVACOES="$DELTA_DIR/ativacoes"
AVISO="$ATIVACOES/aviso-vigilante.txt"
PID_DIR="$DELTA_DIR/scratch"          # D21: nada em /tmp
PID_FILE="$PID_DIR/vigilante-$$.pid"

# ─── Sistema operacional ──────────────────────────────────────

OS_TYPE="desconhecido"
case "$(uname -s)" in
    Darwin*)  OS_TYPE="macos" ;;
    MINGW*|MSYS*|CYGWIN*)  OS_TYPE="windows" ;;
    Linux*)
        if [ -n "$WSL_DISTRO_NAME" ] || grep -qi microsoft /proc/version 2>/dev/null; then
            OS_TYPE="wsl"
        else
            OS_TYPE="linux"
        fi
        ;;
esac

obter_mtime() {
    # data de modificação em segundos desde 1970 (funciona em macOS e Linux)
    stat -f "%m" "$1" 2>/dev/null || stat -c "%Y" "$1" 2>/dev/null || echo "0"
}

notificar() {
    local titulo="$1" mensagem="$2"
    case "$OS_TYPE" in
        macos)
            # Texto passado como argumento: aspas na mensagem não quebram o comando
            osascript -e 'on run argv' \
                      -e 'display notification (item 1 of argv) with title (item 2 of argv) sound name "Sosumi"' \
                      -e 'end run' "$mensagem" "$titulo" > /dev/null 2>&1
            ;;
        windows|wsl)
            local t="${titulo//\'/\'\'}" m="${mensagem//\'/\'\'}"
            powershell.exe -NoProfile -Command "
                Add-Type -AssemblyName System.Windows.Forms
                \$balloon = New-Object System.Windows.Forms.NotifyIcon
                \$balloon.Icon = [System.Drawing.SystemIcons]::Warning
                \$balloon.BalloonTipTitle = '$t'
                \$balloon.BalloonTipText = '$m'
                \$balloon.Visible = \$true
                \$balloon.ShowBalloonTip(10000)
                Start-Sleep -Seconds 3
                \$balloon.Dispose()
            " > /dev/null 2>&1 || echo -e "\a"
            ;;
        linux)
            if command -v notify-send > /dev/null 2>&1; then
                notify-send -- "$titulo" "$mensagem" 2>/dev/null
            else
                echo -e "\a"
            fi
            ;;
    esac
}

processo_rodando() {
    case "$OS_TYPE" in
        windows) ps -p "$1" > /dev/null 2>&1 ;;
        *) kill -0 "$1" 2>/dev/null ;;
    esac
}

verificar_delta11() {
    if [ ! -d "$DELTA_DIR" ]; then
        echo -e "${RED}Erro: pasta .delta-11 não encontrada em $PROJECT_PATH.${NC}"
        echo "Rode este script dentro de um projeto com o Δ-11 instalado."
        exit 1
    fi
}

# ─── Leituras ─────────────────────────────────────────────────

ultimo_toque() {
    local mais_recente=0 arquivo mtime
    for arquivo in \
        "$DELTA_DIR/kanban-data.js" \
        "$DELTA_DIR/kanban.md" \
        "$DELTA_DIR/activity-log.md" \
        "$DELTA_DIR"/memoria/*-produto.md \
        "$DELTA_DIR"/memoria/*-historia.md \
        "$ATIVACOES"/ack-*.txt \
        "$ATIVACOES"/pulso-*.json
    do
        [ -f "$arquivo" ] || continue
        mtime=$(obter_mtime "$arquivo")
        if [ "$mtime" -gt "$mais_recente" ] 2>/dev/null; then
            mais_recente=$mtime
        fi
    done
    echo "$mais_recente"
}

agentes_ativos() {
    local count=0 ack
    for ack in "$ATIVACOES"/ack-*.txt; do
        [ -f "$ack" ] && count=$((count + 1))
    done
    echo "$count"
}

linhas_da_secao() {
    # Linhas de conteúdo da seção "## ... NOME ..." do kanban (sem comentários)
    local nome="$1"
    [ -f "$DELTA_DIR/kanban.md" ] || return 0
    awk -v nome="$nome" '
        /^## / { dentro = (index(toupper($0), nome) > 0); next }
        dentro && $0 !~ /^[[:space:]]*$/ && $0 !~ /<!--/ && $0 !~ /^---/ { print }
    ' "$DELTA_DIR/kanban.md"
}

tarefas_orfas() {
    # Agentes com tarefa em FAZENDO e sem ACK
    local lista="" agente fazendo
    fazendo=$(linhas_da_secao "FAZENDO")
    for agente in $AGENTES; do
        if printf '%s\n' "$fazendo" | grep -qw "$agente"; then
            [ -f "$ATIVACOES/ack-${agente}.txt" ] || lista="$lista $agente"
        fi
    done
    echo "$lista"
}

contar_bloqueios() {
    # Tarefas na seção BLOQUEADO (C-134: nada de "0\n0")
    local n
    n=$(linhas_da_secao "BLOQUEADO" | grep -c "T-\|\*\*" || true)
    echo "${n:-0}"
}

# ─── Registro do aviso para o CRONOS ──────────────────────────

registrar_aviso() {
    local resumo="$1" agora_iso
    agora_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    mkdir -p "$ATIVACOES"
    local corpo
    corpo="Aviso do vigilante para o CRONOS (não é ativação; nenhum agente foi disparado).
Projeto: $PROJECT_PATH
Problema: $resumo
O que fazer (CRONOS): conferir o kanban e retomar pelo Agent tool quem estiver parado."
    # Só registra quando o problema muda (sem encher o log a cada 5 min)
    if [ -f "$AVISO" ] && [ "$(sed -n '2,99p' "$AVISO")" = "$corpo" ]; then
        return 0
    fi
    printf '%s\n%s\n' "$agora_iso" "$corpo" > "$AVISO"
    echo "- [$agora_iso] [vigilante] [CRONOS] $resumo" >> "$DELTA_DIR/activity-log.md"
    echo -e "  ${DIM}Registrado no activity-log e em ativacoes/aviso-vigilante.txt${NC}"
}

limpar_aviso() {
    [ -n "$AVISO" ] || return 0
    if [ -f "$AVISO" ]; then
        echo -e "  ${DIM}Situação normalizada — retirando o aviso antigo:${NC}"
        ls -l "$AVISO" | sed 's/^/    /'
        rm -f "$AVISO"
        echo "- [$(date -u +%Y-%m-%dT%H:%M:%SZ)] [vigilante] [CRONOS] situação normalizada" >> "$DELTA_DIR/activity-log.md"
    fi
}

# ─── Verificação ──────────────────────────────────────────────

ciclo_verificacao() {
    local agora ultimo silencio=0 ativos orfas num_orfas bloqueios min seg travado=0 resumo=""
    agora=$(date +%s)
    ultimo=$(ultimo_toque)
    [ "$ultimo" -gt 0 ] 2>/dev/null && silencio=$((agora - ultimo))
    ativos=$(agentes_ativos)
    orfas=$(tarefas_orfas)
    num_orfas=$(echo $orfas | wc -w | xargs)
    bloqueios=$(contar_bloqueios)
    min=$((silencio / 60))
    seg=$((silencio % 60))

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Δ-11 VIGILANTE — $(date '+%H:%M:%S') [${OS_TYPE}]${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "  Projeto:             ${DIM}$(basename "$PROJECT_PATH")${NC}"
    echo -e "  Agentes ativos:      ${GREEN}${ativos}${NC}"
    echo -e "  Último movimento:    ${min}m${seg}s atrás"
    echo -e "  Tarefas sem agente:  ${num_orfas}"
    echo -e "  Bloqueios no quadro: ${bloqueios}"

    # Silêncio só é problema se há alguém trabalhando ou tarefa aberta
    if [ "$silencio" -gt "$LIMITE_SILENCIO" ] && { [ "$ativos" -gt 0 ] || [ "$num_orfas" -gt 0 ]; }; then
        travado=1
        resumo="${resumo}sistema parado há ${min} min. "
        echo -e "  ${RED}${BOLD}⚠ SISTEMA PARADO HÁ ${min} MINUTOS${NC}"
    fi
    if [ "$num_orfas" -gt 0 ]; then
        travado=1
        resumo="${resumo}tarefa(s) em FAZENDO sem agente ativo:${orfas}. "
        echo -e "  ${YELLOW}⚠ Tarefas em FAZENDO sem agente ativo:${orfas}${NC}"
    fi
    if [ "$bloqueios" -gt 0 ]; then
        travado=1
        resumo="${resumo}${bloqueios} bloqueio(s) no quadro. "
        echo -e "  ${YELLOW}⚠ ${bloqueios} bloqueio(s) registrado(s) no quadro${NC}"
    fi

    if [ "$travado" -eq 1 ]; then
        notificar "Δ-11 precisa de atenção" "$resumo"
        registrar_aviso "$resumo"
        echo -e "  ${DIM}Quem retoma é o CRONOS (Agent tool). Você não precisa abrir janela nem colar nada.${NC}"
    else
        limpar_aviso
        echo ""
        echo -e "  ${GREEN}✓ Sistema ativo — tudo fluindo${NC}"
    fi
    return 0
}

# ─── Argumentos ───────────────────────────────────────────────

case "${1:-}" in
    --once)
        verificar_delta11
        ciclo_verificacao
        exit 0
        ;;
    --stop)
        verificar_delta11
        for pid_file in "$PID_DIR"/vigilante-*.pid; do
            [ -f "$pid_file" ] || continue
            pid=$(basename "$pid_file" .pid)
            pid="${pid#vigilante-}"
            [ -n "$pid" ] || continue
            if processo_rodando "$pid"; then
                kill "$pid" 2>/dev/null && echo "Vigilante $pid parado."
            else
                echo "Vigilante $pid já não existia."
            fi
            rm -f "$pid_file"
        done
        exit 0
        ;;
    --help|-h)
        echo "Uso: .delta-11/scripts/vigilante.sh [--once|--stop|--help]"
        echo ""
        echo "  (sem argumentos)  Inicia monitoramento contínuo"
        echo "  --once            Verifica uma vez e sai"
        echo "  --stop            Para o vigilante rodando em segundo plano"
        echo "  --help            Mostra esta ajuda"
        echo ""
        echo "  Sistema detectado: $OS_TYPE"
        echo "  Projeto detectado: $PROJECT_PATH"
        exit 0
        ;;
esac

# ─── Loop principal ───────────────────────────────────────────

verificar_delta11
mkdir -p "$PID_DIR"
echo "$PROJECT_PATH" > "$PID_FILE"
trap "rm -f '$PID_FILE'; echo ''; echo 'Vigilante encerrado.'; exit 0" INT TERM

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Δ-11 VIGILANTE — Iniciando monitoramento${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Projeto:            ${BOLD}${PROJECT_PATH}${NC}"
echo -e "  Sistema:            ${BOLD}${OS_TYPE}${NC}"
echo -e "  Verificando a cada: ${BOLD}$((INTERVALO / 60)) minutos${NC}"
echo -e "  Alerta após:        ${BOLD}$((LIMITE_SILENCIO / 60)) minutos${NC} sem atividade"
echo -e "  Para parar:         ${DIM}Ctrl+C${NC}"

while true; do
    ciclo_verificacao
    echo ""
    echo -e "  ${DIM}Próxima verificação em $((INTERVALO / 60)) minutos...${NC}"
    sleep "$INTERVALO" &
    wait $!
done
