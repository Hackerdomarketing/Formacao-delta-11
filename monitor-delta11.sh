#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Monitor Invisível (substitui vigilante.sh)
# ═══════════════════════════════════════════════════════════════
#
# Executado pelo LaunchAgent a cada 5 minutos.
# NUNCA abre janela. NUNCA mexe no cursor. NUNCA usa AppleScript
# de window management. Apenas verifica arquivos e manda
# notificação discreta (popup no canto da tela).
#
# ═══════════════════════════════════════════════════════════════

LIMITE_SILENCIO=900  # 15 minutos sem heartbeat = agente morto
AGORA=$(date +%s)

# ─── Encontrar todos os projetos com Delta-11 ──────────────

PROJETOS=()

# Ler do registry se existir
REGISTRY="$HOME/.delta-11-registry.json"
if [ -f "$REGISTRY" ]; then
    while IFS= read -r linha; do
        # Expandir ~ para $HOME
        dir=$(echo "$linha" | sed "s|~|$HOME|g" | tr -d '",' | xargs)
        if [ -d "$dir/.delta-11" ]; then
            PROJETOS+=("$dir")
        fi
    done < <(grep -o '"[^"]*"' "$REGISTRY" | grep -v "version\|source\|github\|backup\|historical\|last_sync\|projects" | grep '/')
fi

# Busca adicional em diretórios comuns
for base in "$HOME/Documents/VSCODE" "$HOME/projetos" "$HOME/Downloads"; do
    [ -d "$base" ] || continue
    for dir in "$base"/*/; do
        [ -d "${dir}.delta-11" ] || continue
        # Evitar duplicatas
        ja_existe=0
        for p in "${PROJETOS[@]}"; do
            if [ "$p" = "${dir%/}" ]; then
                ja_existe=1
                break
            fi
        done
        if [ "$ja_existe" -eq 0 ]; then
            PROJETOS+=("${dir%/}")
        fi
    done
done

# ─── Verificar cada projeto ────────────────────────────────

ALERTAS=""
MORTES=""
TRAVADOS=""
STATUS_PROJETOS="["

for projeto in "${PROJETOS[@]}"; do
    DELTA_DIR="${projeto}/.delta-11"
    NOME_PROJETO=$(basename "$projeto")
    ATIVACOES="${DELTA_DIR}/ativacoes"

    [ -d "$ATIVACOES" ] || continue

    projeto_alertas=""

    # 1. Verificar arquivos de morte (agente morreu)
    for morte in "${ATIVACOES}/morte-"*.json; do
        [ -f "$morte" ] || continue
        agente=$(grep -o '"agente":"[^"]*"' "$morte" | head -1 | cut -d'"' -f4)
        morreu_em=$(grep -o '"morreu_em":"[^"]*"' "$morte" | head -1 | cut -d'"' -f4)
        motivo=$(grep -o '"motivo":"[^"]*"' "$morte" | head -1 | cut -d'"' -f4)

        MORTES="${MORTES}${agente} morreu em ${NOME_PROJETO} (${motivo})\n"
        projeto_alertas="${projeto_alertas}{\"tipo\":\"morte\",\"agente\":\"${agente}\",\"quando\":\"${morreu_em}\",\"motivo\":\"${motivo}\"},"
    done

    # 2. Verificar pulsos antigos (agente travou sem morrer)
    for pulso in "${ATIVACOES}/pulso-"*.json; do
        [ -f "$pulso" ] || continue
        agente=$(grep -o '"agente":"[^"]*"' "$pulso" | head -1 | cut -d'"' -f4)
        epoch=$(grep -o '"epoch":[0-9]*' "$pulso" | head -1 | cut -d':' -f2)
        status=$(grep -o '"status":"[^"]*"' "$pulso" | head -1 | cut -d'"' -f4)

        if [ -n "$epoch" ]; then
            silencio=$((AGORA - epoch))
            if [ "$silencio" -gt "$LIMITE_SILENCIO" ]; then
                min=$((silencio / 60))
                TRAVADOS="${TRAVADOS}${agente} sem pulso há ${min}min em ${NOME_PROJETO}\n"
                projeto_alertas="${projeto_alertas}{\"tipo\":\"travado\",\"agente\":\"${agente}\",\"silencio_min\":${min}},"
            fi
        fi
    done

    # 3. Verificar tarefas em FAZENDO sem agente ativo
    KANBAN="${DELTA_DIR}/kanban.md"
    if [ -f "$KANBAN" ]; then
        for agente_nome in ATLAS CRONOS FRONT PIXEL FORM BACK ENGINE VAULT SHIELD SCOUT; do
            # Tem tarefa em FAZENDO para esse agente?
            em_fazendo=$(grep -A5 "FAZENDO\|fazendo\|Em andamento" "$KANBAN" 2>/dev/null | grep -ci "$agente_nome" 2>/dev/null | tr -d '[:space:]')
            [ -z "$em_fazendo" ] && em_fazendo=0
            if [ "$em_fazendo" -gt 0 ]; then
                # Tem ack?
                if [ ! -f "${ATIVACOES}/ack-${agente_nome}.txt" ]; then
                    # Tem pulso recente?
                    if [ ! -f "${ATIVACOES}/pulso-${agente_nome}.json" ]; then
                        projeto_alertas="${projeto_alertas}{\"tipo\":\"orfa\",\"agente\":\"${agente_nome}\"},"
                    fi
                fi
            fi
        done
    fi

    # ─────────────────────────────────────────────────────────────────
    # 4. v6.0 (Etapa 7D) — Detectar OPERACAO AUTONOMA (Dia 7)
    # ─────────────────────────────────────────────────────────────────
    # Se o projeto nao tem NENHUM arquivo de ativacao modificado nos
    # ultimos X dias (padrao 14 = 2 semanas do Teste Supremo), e nao ha
    # tarefas em FAZENDO, entao o sistema pode estar em operacao autonoma.
    OPERACAO_AUTONOMA="false"
    DIAS_OPERACAO_AUTONOMA=0
    THRESHOLD_DIAS=14  # 2 semanas

    if [ -d "$ATIVACOES" ]; then
        # Encontra o arquivo de ativacao mais recente
        MAIS_RECENTE=$(find "$ATIVACOES" -type f -name "*.txt" -o -name "*.json" 2>/dev/null | \
            xargs -I {} stat -f "%m {}" 2>/dev/null | \
            sort -rn | head -1 | cut -d' ' -f2-)
        if [ -n "$MAIS_RECENTE" ]; then
            EPOCH_MAIS_RECENTE=$(stat -f "%m" "$MAIS_RECENTE" 2>/dev/null || echo 0)
            if [ "$EPOCH_MAIS_RECENTE" -gt 0 ]; then
                SILENCIO_SEG=$((AGORA - EPOCH_MAIS_RECENTE))
                DIAS_OPERACAO_AUTONOMA=$((SILENCIO_SEG / 86400))
                if [ "$DIAS_OPERACAO_AUTONOMA" -ge "$THRESHOLD_DIAS" ]; then
                    # So considera operacao autonoma se NAO ha tarefas em FAZENDO
                    if [ "$em_fazendo" -eq 0 ] || [ -z "$em_fazendo" ]; then
                        OPERACAO_AUTONOMA="true"
                    fi
                fi
            fi
        fi
    fi

    # Montar status do projeto
    if [ -n "$projeto_alertas" ]; then
        # Remover vírgula final
        projeto_alertas="${projeto_alertas%,}"
        STATUS_PROJETOS="${STATUS_PROJETOS}{\"projeto\":\"${NOME_PROJETO}\",\"path\":\"${projeto}\",\"alertas\":[${projeto_alertas}],\"operacao_autonoma\":${OPERACAO_AUTONOMA},\"dias_silencio\":${DIAS_OPERACAO_AUTONOMA}},"
    else
        STATUS_PROJETOS="${STATUS_PROJETOS}{\"projeto\":\"${NOME_PROJETO}\",\"path\":\"${projeto}\",\"alertas\":[],\"operacao_autonoma\":${OPERACAO_AUTONOMA},\"dias_silencio\":${DIAS_OPERACAO_AUTONOMA}},"
    fi
done

# Fechar JSON
STATUS_PROJETOS="${STATUS_PROJETOS%,}]"

# ─── Gravar status em cada projeto (para o painel ler) ─────

for projeto in "${PROJETOS[@]}"; do
    DELTA_DIR="${projeto}/.delta-11"
    [ -d "$DELTA_DIR" ] || continue

    cat > "${DELTA_DIR}/monitor-status.json" << EOF
{
  "verificado_em": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "epoch": ${AGORA},
  "projetos": ${STATUS_PROJETOS}
}
EOF
done

# ─── Enviar notificações (SEM roubar foco) ─────────────────

if [ -n "$MORTES" ]; then
    MSG=$(echo -e "$MORTES" | head -3)
    osascript -e "display notification \"$MSG\" with title \"Δ-11: Agente Morreu\" sound name \"Sosumi\"" 2>/dev/null
fi

if [ -n "$TRAVADOS" ]; then
    MSG=$(echo -e "$TRAVADOS" | head -3)
    osascript -e "display notification \"$MSG\" with title \"Δ-11: Agente Travado\" sound name \"Purr\"" 2>/dev/null
fi

# ─── Log ───────────────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Verificados ${#PROJETOS[@]} projetos"
[ -n "$MORTES" ] && echo -e "  MORTES: $MORTES"
[ -n "$TRAVADOS" ] && echo -e "  TRAVADOS: $TRAVADOS"
[ -z "$MORTES" ] && [ -z "$TRAVADOS" ] && echo "  OK - Sem alertas"
