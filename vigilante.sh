#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Vigilante (Monitor de Atividade)
# ═══════════════════════════════════════════════════════════════
#
# Funciona em: macOS (Terminal e VS Code) + Windows (Git Bash e VS Code)
#
# O que este script faz:
# Fica rodando no fundo verificando se os agentes Delta-11
# estão trabalhando. Se ninguém se mexe por 15 minutos,
# manda uma notificação no sistema e tenta redespachar
# agentes que ficaram pendentes.
#
# Como usar:
#   ./vigilante.sh              # Inicia o vigilante (roda até você fechar)
#   ./vigilante.sh --once       # Verifica uma vez e sai
#   ./vigilante.sh --stop       # Para o vigilante rodando em background
#
# O vigilante verifica a cada 5 minutos.
# Para parar: Ctrl+C ou feche a janela do terminal.
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

# Configuração
INTERVALO=300          # Verificar a cada 5 minutos (em segundos)
LIMITE_SILENCIO=900    # Alertar após 15 minutos sem atividade (em segundos)
PID_FILE="/tmp/delta11-vigilante-$$.pid"
PROJECT_PATH="$(pwd)"

# ─── Detecção de sistema operacional ────────────────────────

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

# ─── Funções adaptadas por sistema operacional ──────────────

obter_mtime() {
    # Retorna a data de modificação de um arquivo em epoch (segundos desde 1970)
    local arquivo="$1"
    case "$OS_TYPE" in
        macos)
            stat -f "%m" "$arquivo" 2>/dev/null || echo "0"
            ;;
        windows|wsl|linux)
            stat -c "%Y" "$arquivo" 2>/dev/null || echo "0"
            ;;
        *)
            stat -f "%m" "$arquivo" 2>/dev/null || stat -c "%Y" "$arquivo" 2>/dev/null || echo "0"
            ;;
    esac
}

notificar() {
    local titulo="$1"
    local mensagem="$2"

    case "$OS_TYPE" in
        macos)
            osascript -e "display notification \"$mensagem\" with title \"$titulo\" sound name \"Sosumi\"" 2>/dev/null
            ;;
        windows|wsl)
            # Notificação via PowerShell (funciona no Git Bash e WSL)
            powershell.exe -Command "
                Add-Type -AssemblyName System.Windows.Forms
                \$balloon = New-Object System.Windows.Forms.NotifyIcon
                \$balloon.Icon = [System.Drawing.SystemIcons]::Warning
                \$balloon.BalloonTipTitle = '$titulo'
                \$balloon.BalloonTipText = '$mensagem'
                \$balloon.Visible = \$true
                \$balloon.ShowBalloonTip(10000)
                Start-Sleep -Seconds 3
                \$balloon.Dispose()
            " 2>/dev/null
            if [ $? -ne 0 ]; then
                echo -e "\a"
            fi
            ;;
        linux)
            if command -v notify-send &>/dev/null; then
                notify-send "$titulo" "$mensagem" 2>/dev/null
            else
                echo -e "\a"
            fi
            ;;
    esac
}

processo_rodando() {
    # Verifica se um processo com determinado PID existe
    local pid="$1"
    case "$OS_TYPE" in
        windows)
            # pgrep não existe no Git Bash — usar ps
            ps -p "$pid" > /dev/null 2>&1
            ;;
        wsl|macos|linux)
            kill -0 "$pid" 2>/dev/null
            ;;
        *)
            kill -0 "$pid" 2>/dev/null
            ;;
    esac
}

# ─── Funções do Heartbeat (checklist inteligente) ───────────

verificar_delta11() {
    if [ ! -d ".delta-11" ]; then
        echo -e "${RED}Erro: pasta .delta-11 não encontrada.${NC}"
        echo "Execute este script na pasta raiz de um projeto com Delta-11 instalado."
        exit 1
    fi
}

ultimo_toque() {
    # Encontra o arquivo mais recentemente modificado no .delta-11/
    local mais_recente=0

    for arquivo in \
        .delta-11/kanban-data.js \
        .delta-11/kanban.md \
        .delta-11/activity-log.md \
        .delta-11/memoria/*-estado.md \
        .delta-11/ativacoes/ack-*.txt
    do
        if [ -f "$arquivo" ]; then
            local mtime
            mtime=$(obter_mtime "$arquivo")
            if [ "$mtime" -gt "$mais_recente" ] 2>/dev/null; then
                mais_recente=$mtime
            fi
        fi
    done

    echo "$mais_recente"
}

agentes_ativos() {
    # Conta quantos agentes têm ACK (estão ativos)
    local count=0
    for ack in .delta-11/ativacoes/ack-*.txt; do
        [ -f "$ack" ] && count=$((count + 1))
    done
    echo "$count"
}

prompts_pendentes() {
    # Conta prompts de ativação que existem MAS não têm ACK correspondente
    local pendentes=0
    local lista=""

    for prompt in .delta-11/ativacoes/janela-*.txt .delta-11/ativacoes/retomada-*.txt; do
        [ -f "$prompt" ] || continue

        # Extrair nome do agente do arquivo
        local agente=""
        agente=$(grep -m1 "^Agente:" "$prompt" 2>/dev/null | sed 's/Agente: *//' | tr -d '[:space:]')

        if [ -n "$agente" ]; then
            local ack=".delta-11/ativacoes/ack-${agente}.txt"
            if [ ! -f "$ack" ]; then
                pendentes=$((pendentes + 1))
                lista="$lista $agente"
            fi
        fi
    done

    echo "$pendentes|$lista"
}

# ─── Checklist Heartbeat (inspirado no OpenClaw) ────────────

tarefas_orfas() {
    # Verifica se há tarefas em FAZENDO no kanban sem agente ativo correspondente
    local orfas=0
    local lista=""

    if [ ! -f ".delta-11/kanban.md" ]; then
        echo "0|"
        return
    fi

    # Procura linhas com "FAZENDO" e extrai o agente
    while IFS= read -r linha; do
        for agente_nome in ATLAS CRONOS FRONT PIXEL FORM BACK ENGINE VAULT SHIELD SCOUT; do
            if echo "$linha" | grep -qi "$agente_nome" 2>/dev/null; then
                local ack=".delta-11/ativacoes/ack-${agente_nome}.txt"
                if [ ! -f "$ack" ]; then
                    orfas=$((orfas + 1))
                    # Evitar duplicados na lista
                    if ! echo "$lista" | grep -q "$agente_nome"; then
                        lista="$lista $agente_nome"
                    fi
                fi
            fi
        done
    done < <(grep -A5 "FAZENDO\|fazendo\|Em andamento" .delta-11/kanban.md 2>/dev/null | grep -i "agente\|ATLAS\|CRONOS\|FRONT\|PIXEL\|FORM\|BACK\|ENGINE\|VAULT\|SHIELD\|SCOUT")

    echo "$orfas|$lista"
}

bloqueios_antigos() {
    # Verifica se há bloqueios registrados há mais de 30 minutos
    local agora
    agora=$(date +%s)
    local count=0

    if [ -f ".delta-11/kanban.md" ]; then
        # Se existem linhas com BLOQUEIO no kanban, conta
        count=$(grep -c "BLOQUEIO\|bloqueado\|BLOQUEADO" .delta-11/kanban.md 2>/dev/null || echo "0")
    fi

    echo "$count"
}

tentar_redespacho() {
    local agente="$1"

    if [ -x "./disparar.sh" ]; then
        echo -e "  ${YELLOW}→ Tentando redespachar ${agente}...${NC}"
        ./disparar.sh "$agente" 2>/dev/null
        return $?
    else
        echo -e "  ${RED}→ disparar.sh não encontrado ou não executável${NC}"
        return 1
    fi
}

# ─── Exibição de status ────────────────────────────────────

exibir_status() {
    local agora
    agora=$(date +%s)
    local ultimo
    ultimo=$(ultimo_toque)
    local silencio=0

    if [ "$ultimo" -gt 0 ] 2>/dev/null; then
        silencio=$((agora - ultimo))
    fi

    local ativos
    ativos=$(agentes_ativos)

    local resultado_pendentes
    resultado_pendentes=$(prompts_pendentes)
    local num_pendentes
    num_pendentes=$(echo "$resultado_pendentes" | cut -d'|' -f1)
    local lista_pendentes
    lista_pendentes=$(echo "$resultado_pendentes" | cut -d'|' -f2)

    local resultado_orfas
    resultado_orfas=$(tarefas_orfas)
    local num_orfas
    num_orfas=$(echo "$resultado_orfas" | cut -d'|' -f1)
    local lista_orfas
    lista_orfas=$(echo "$resultado_orfas" | cut -d'|' -f2)

    local num_bloqueios
    num_bloqueios=$(bloqueios_antigos)

    # Formatar tempo de silêncio
    local min=$((silencio / 60))
    local seg=$((silencio % 60))

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Δ-11 VIGILANTE — $(date '+%H:%M:%S') [${OS_TYPE}]${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "  Projeto:             ${DIM}$(basename "$PROJECT_PATH")${NC}"
    echo -e "  Agentes ativos:      ${GREEN}${ativos}${NC}"
    echo -e "  Último movimento:    ${min}m${seg}s atrás"
    echo ""
    echo -e "  ${BOLD}HEARTBEAT:${NC}"
    echo -e "  Prompts sem ACK:     ${num_pendentes}"
    echo -e "  Tarefas sem agente:  ${num_orfas}"
    echo -e "  Bloqueios no kanban: ${num_bloqueios}"

    # Determinar se o sistema está travado
    local travado=0

    if [ "$silencio" -gt "$LIMITE_SILENCIO" ]; then
        travado=1
        echo ""
        echo -e "  ${RED}${BOLD}⚠ SISTEMA PARADO HÁ ${min} MINUTOS${NC}"
    fi

    if [ "$num_pendentes" -gt 0 ]; then
        travado=1
        echo -e "  ${YELLOW}⚠ Agentes não despachados:${lista_pendentes}${NC}"
    fi

    if [ "$num_orfas" -gt 0 ]; then
        travado=1
        echo -e "  ${YELLOW}⚠ Tarefas em FAZENDO sem agente ativo:${lista_orfas}${NC}"
    fi

    if [ "$num_bloqueios" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠ ${num_bloqueios} bloqueio(s) registrado(s) no kanban${NC}"
    fi

    if [ "$travado" -eq 0 ]; then
        echo ""
        echo -e "  ${GREEN}✓ Sistema ativo — tudo fluindo${NC}"
    fi

    return $travado
}

ciclo_verificacao() {
    exibir_status
    local parado=$?

    if [ "$parado" -eq 1 ]; then
        local resultado_pendentes
        resultado_pendentes=$(prompts_pendentes)
        local num_pendentes
        num_pendentes=$(echo "$resultado_pendentes" | cut -d'|' -f1)
        local lista_pendentes
        lista_pendentes=$(echo "$resultado_pendentes" | cut -d'|' -f2)

        local resultado_orfas
        resultado_orfas=$(tarefas_orfas)
        local num_orfas
        num_orfas=$(echo "$resultado_orfas" | cut -d'|' -f1)
        local lista_orfas
        lista_orfas=$(echo "$resultado_orfas" | cut -d'|' -f2)

        # Montar mensagem de notificação
        local msg=""
        [ "$num_pendentes" -gt 0 ] && msg="${msg}${num_pendentes} agente(s) sem ACK. "
        [ "$num_orfas" -gt 0 ] && msg="${msg}${num_orfas} tarefa(s) sem agente ativo. "
        [ -z "$msg" ] && msg="Nenhum arquivo foi atualizado nos últimos 15 minutos."

        notificar "Δ-11 TRAVADO" "$msg"

        # Tentar redespachar agentes pendentes (prompts sem ACK)
        if [ "$num_pendentes" -gt 0 ]; then
            echo ""
            echo -e "  ${BOLD}Tentando redespachar agentes pendentes...${NC}"
            for agente in $lista_pendentes; do
                tentar_redespacho "$agente"
                sleep 8  # Esperar entre dispatches (regra do Delta-11)
            done
        fi

        # Alertar sobre tarefas órfãs (não pode redespachar automaticamente — precisa do prompt)
        if [ "$num_orfas" -gt 0 ]; then
            echo ""
            echo -e "  ${YELLOW}Tarefas órfãs detectadas (agente morreu no meio do trabalho):${NC}"
            echo -e "  ${YELLOW}Agentes afetados:${lista_orfas}${NC}"
            echo -e "  ${DIM}v6.1+: CRONOS auto-retoma via Agent tool — nenhuma acao manual necessaria. Tarefas orfas serao retomadas automaticamente.${NC}"
        fi
    fi
}

# ─── Tratamento de argumentos ────────────────────────────────

case "${1:-}" in
    --once)
        verificar_delta11
        ciclo_verificacao
        exit 0
        ;;
    --stop)
        # Parar todos os vigilantes deste projeto
        for pid_file in /tmp/delta11-vigilante-*.pid; do
            [ -f "$pid_file" ] || continue
            local_path=$(head -1 "$pid_file" 2>/dev/null)
            if [ "$local_path" = "$(pwd)" ]; then
                pid=$(basename "$pid_file" | sed 's/delta11-vigilante-//' | sed 's/.pid//')
                if processo_rodando "$pid"; then
                    kill "$pid" 2>/dev/null && echo "Vigilante $pid parado."
                else
                    echo "Vigilante $pid já não existia."
                fi
                rm -f "$pid_file"
            fi
        done
        exit 0
        ;;
    --help|-h)
        echo "Uso: ./vigilante.sh [--once|--stop|--help]"
        echo ""
        echo "  (sem argumentos)  Inicia monitoramento contínuo"
        echo "  --once            Verifica uma vez e sai"
        echo "  --stop            Para o vigilante rodando em background"
        echo "  --help            Mostra esta ajuda"
        echo ""
        echo "  Sistema detectado: $OS_TYPE"
        exit 0
        ;;
esac

# ─── Loop principal ──────────────────────────────────────────

verificar_delta11

# Salvar PID para --stop
echo "$(pwd)" > "$PID_FILE"

# Limpar PID ao sair
trap "rm -f '$PID_FILE'; echo ''; echo 'Vigilante encerrado.'; exit 0" INT TERM

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Δ-11 VIGILANTE — Iniciando monitoramento${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Sistema:           ${BOLD}${OS_TYPE}${NC}"
echo -e "  Verificando a cada: ${BOLD}$((INTERVALO / 60)) minutos${NC}"
echo -e "  Alerta após:       ${BOLD}$((LIMITE_SILENCIO / 60)) minutos${NC} sem atividade"
echo -e "  Para parar:        ${DIM}Ctrl+C${NC}"

while true; do
    ciclo_verificacao
    echo ""
    echo -e "  ${DIM}Próxima verificação em $((INTERVALO / 60)) minutos...${NC}"
    sleep "$INTERVALO"
done
