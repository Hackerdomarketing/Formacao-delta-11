#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# CRONOS — Painel de Status da Formação D-11 (v6.3 — 2026-10-14)
# ═══════════════════════════════════════════════════════════════
#
# Verifica o estado de todos os agentes e retorna relatorio
# estruturado com: ACKs, travas de arquivo, kanban, travas de fase
# e avisos pendentes em ativacoes/.
#
# Uso:
#   bash .delta-11/ferramentas/cronos-status.sh
#   bash .delta-11/ferramentas/cronos-status.sh --resumo   # so o resultado final
#
# Onde le: sempre na PASTA PRINCIPAL do projeto (D25). Rodando de dentro de
# uma worktree, a pasta principal e o pai de `git rev-parse --git-common-dir`.
# Sem git: CLAUDE_PROJECT_DIR; sem ele, a pasta atual.
#
# Saida (convencao das ferramentas v6.3): 0 = OK ou ALERTA (o relatorio diz
# qual — alerta nao bloqueia); 1 = FALHA/erro ao rodar.
# Nao precisa instalar nada — usa apenas ferramentas do sistema.
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

find_main_folder() {
    local common_dir
    if common_dir=$(git rev-parse --git-common-dir 2>/dev/null) && [ -n "$common_dir" ]; then
        (cd "$common_dir/.." && pwd)
    elif [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
        echo "$CLAUDE_PROJECT_DIR"
    else
        pwd
    fi
}

# Le um numero do .delta-11/.config-limites.json (D36), com valor padrao.
read_limit() {
    local key="$1" default_value="$2" value=""
    if [ -f "$CONFIG_LIMITES" ]; then
        value=$(grep -oE "\"$key\"[[:space:]]*:[[:space:]]*[0-9]+" "$CONFIG_LIMITES" | grep -oE '[0-9]+$' || true)
    fi
    echo "${value:-$default_value}"
}

# Idade em segundos pelo mtime (macOS: stat -f; Linux: stat -c).
age_in_seconds() {
    local modified
    modified=$(stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo "$NOW")
    echo $(( NOW - modified ))
}

# Conta linhas que casam com o padrao. grep -c imprime "0" E sai com 1 quando
# nao acha nada — por isso "|| true", nunca "|| echo 0" (viraria "0\n0", C-134).
count_matches() {
    local count
    count=$(grep -cE "$1" "$2" 2>/dev/null || true)
    echo "${count:-0}"
}

MAIN_FOLDER="$(find_main_folder)"
DELTA_DIR="$MAIN_FOLDER/.delta-11"
ATIVACOES_DIR="$DELTA_DIR/ativacoes"
LOCKS_DIR="$DELTA_DIR/locks"
KANBAN="$DELTA_DIR/kanban.md"
CONFIG_LIMITES="$DELTA_DIR/.config-limites.json"
MODO_RESUMO=false

if [[ "${1:-}" == "--resumo" ]]; then
    MODO_RESUMO=true
fi

# Mesmo limite do gc-locks.py (D36: lock_horas, padrao 2 h).
LOCK_HORAS=$(read_limit "lock_horas" 2)
LOCK_MAX_SEGUNDOS=$(( LOCK_HORAS * 3600 ))
NOW=$(date +%s)

AGENTES="ATLAS CRONOS FRONT PIXEL FORM BACK ENGINE VAULT SHIELD SCOUT"
RESULTADO_FINAL="OK"
ALERTAS=0

# No modo --resumo, os detalhes vao para o lixo e so o resultado final aparece.
if [ "$MODO_RESUMO" = true ]; then
    exec 3>&1 1>/dev/null
fi

echo "═══════════════════════════════════════════════════"
echo "  CRONOS STATUS — Painel da Formacao D-11"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Pasta principal: $MAIN_FOLDER"
echo "═══════════════════════════════════════════════════"
echo ""

if [ ! -d "$DELTA_DIR" ]; then
    echo "  ERRO: pasta .delta-11 nao encontrada em $MAIN_FOLDER"
    if [ "$MODO_RESUMO" = true ]; then
        exec 1>&3
    fi
    echo "  RESULTADO: ERRO — .delta-11 nao encontrada em $MAIN_FOLDER"
    exit 1
fi

# ───────────────────────────────────────────────────────
# 1. AGENTES ATIVOS (ACKs)
# ───────────────────────────────────────────────────────

echo "[1/5] AGENTES ATIVOS"
echo "─────────────────────────────────────────────────"

ATIVOS=0
for agente in $AGENTES; do
    ack_file="$ATIVACOES_DIR/ack-${agente}.txt"
    if [ -f "$ack_file" ]; then
        ts=$(grep -oE '"timestamp":"[^"]*"' "$ack_file" 2>/dev/null | cut -d'"' -f4 || true)
        echo "  ATIVO   $agente (desde ${ts:-?})"
        ATIVOS=$((ATIVOS + 1))
    fi
done

if [ "$ATIVOS" -eq 0 ]; then
    echo "  Nenhum agente ativo no momento."
else
    echo ""
    echo "  Total: $ATIVOS agente(s) ativo(s)"
fi
echo ""

# ───────────────────────────────────────────────────────
# 2. TRAVAS DE ARQUIVO (.delta-11/locks/*.lock — pasta ou arquivo)
# ───────────────────────────────────────────────────────

echo "[2/5] TRAVAS DE ARQUIVO (orfa = mais de ${LOCK_HORAS}h, igual ao gc-locks)"
echo "─────────────────────────────────────────────────"

if [ -d "$LOCKS_DIR" ]; then
    LOCK_COUNT=0
    LOCK_ORFAO=0

    for lock_path in "$LOCKS_DIR"/*.lock; do
        # Sem nenhuma trava o glob volta literal: pula.
        [ -e "$lock_path" ] || continue
        LOCK_COUNT=$((LOCK_COUNT + 1))

        # Formato atual (mkdir atomico): pasta com arquivo "meta" dentro.
        # Formato antigo: arquivo com as linhas AGENTE:/TAREFA:.
        if [ -d "$lock_path" ]; then
            meta_file="$lock_path/meta"
        else
            meta_file="$lock_path"
        fi
        lock_agente=$(grep -m1 "^AGENTE:" "$meta_file" 2>/dev/null | sed 's/AGENTE: *//' || true)
        lock_tarefa=$(grep -m1 "^TAREFA:" "$meta_file" 2>/dev/null | sed 's/TAREFA: *//' || true)
        lock_arquivo=$(basename "$lock_path" .lock | sed 's/--/\//g')

        lock_age_sec=$(age_in_seconds "$lock_path")
        lock_age_min=$(( lock_age_sec / 60 ))

        if [ "$lock_age_sec" -gt "$LOCK_MAX_SEGUNDOS" ]; then
            echo "  ORFA   $lock_arquivo"
            LOCK_ORFAO=$((LOCK_ORFAO + 1))
            ALERTAS=$((ALERTAS + 1))
        else
            echo "  ATIVA  $lock_arquivo"
        fi
        echo "           Agente: ${lock_agente:-?} | Tarefa: ${lock_tarefa:-?} | Idade: ${lock_age_min}min"
    done

    if [ "$LOCK_COUNT" -eq 0 ]; then
        echo "  Nenhuma trava ativa."
    else
        echo ""
        echo "  Total: $LOCK_COUNT trava(s), $LOCK_ORFAO orfa(s)"
        if [ "$LOCK_ORFAO" -gt 0 ]; then
            RESULTADO_FINAL="ALERTA"
            echo "  ALERTA: travas orfas! O agente pode ter morrido sem liberar (o gc-locks limpa na proxima sessao)."
        fi
    fi
else
    echo "  Pasta de travas nao encontrada."
fi
echo ""

# ───────────────────────────────────────────────────────
# 3. TAREFAS NO KANBAN
# ───────────────────────────────────────────────────────

echo "[3/5] TAREFAS NO KANBAN"
echo "─────────────────────────────────────────────────"

if [ -f "$KANBAN" ]; then
    total_tarefas=$(count_matches '^- \[( |x|X)\]' "$KANBAN")
    concluidas=$(count_matches '^- \[(x|X)\]' "$KANBAN")
    pendentes=$((total_tarefas - concluidas))
    bloqueadas=$(grep -ciE "bloqueado|blocked|depende de" "$KANBAN" 2>/dev/null || true)
    bloqueadas="${bloqueadas:-0}"

    echo "  Total: $total_tarefas tarefa(s)"
    echo "  Concluidas: $concluidas"
    echo "  Pendentes: $pendentes"
    if [ "$bloqueadas" -gt 0 ]; then
        echo "  Com bloqueio ou dependencia: ~$bloqueadas linha(s)"
    fi
else
    echo "  Kanban nao encontrado: $KANBAN"
fi
echo ""

# ───────────────────────────────────────────────────────
# 4. TRAVAS DE FASE (ativacoes/.trava-fase-N — todas as 13 fases)
# ───────────────────────────────────────────────────────

echo "[4/5] TRAVAS DE FASE"
echo "─────────────────────────────────────────────────"

TRAVA_ENCONTRADA=false
for trava_dir in "$ATIVACOES_DIR"/.trava-fase-*; do
    [ -d "$trava_dir" ] || continue
    fase="${trava_dir##*/.trava-fase-}"
    owner=$(head -1 "$trava_dir/owner" 2>/dev/null || true)
    echo "  TRAVA  Fase $fase — dono: ${owner:-?}"
    TRAVA_ENCONTRADA=true
done

if [ "$TRAVA_ENCONTRADA" = false ]; then
    echo "  Nenhuma trava de fase ativa."
fi
echo ""

# ───────────────────────────────────────────────────────
# 5. AVISOS PENDENTES EM ativacoes/
# ───────────────────────────────────────────────────────

echo "[5/5] AVISOS PENDENTES"
echo "─────────────────────────────────────────────────"

if [ -d "$ATIVACOES_DIR" ]; then
    AVISO_COUNT=0
    LEGADO_COUNT=0
    # Avisos atuais: pendente-*, retomada-*, erro-*, contratos-desatualizados (D31)
    # e contrato-alterado-[AGENTE] (D31).
    for f in "$ATIVACOES_DIR"/pendente-*.txt "$ATIVACOES_DIR"/retomada-*.txt "$ATIVACOES_DIR"/erro-*.txt \
             "$ATIVACOES_DIR"/contratos-desatualizados.txt "$ATIVACOES_DIR"/contrato-alterado-*.txt; do
        [ -f "$f" ] || continue
        AVISO_COUNT=$((AVISO_COUNT + 1))
        tamanho=$(wc -c < "$f" | tr -d ' ')
        echo "  PENDENTE  $(basename "$f" .txt) ($tamanho bytes)"
    done
    # janela-*.txt e legado (v6.1+: ninguem cola prompt em janela — D3).
    for f in "$ATIVACOES_DIR"/janela-*.txt; do
        [ -f "$f" ] || continue
        LEGADO_COUNT=$((LEGADO_COUNT + 1))
        echo "  LEGADO    $(basename "$f" .txt) (registro antigo de janela; o disparo hoje e pelo Agent tool)"
    done

    if [ "$AVISO_COUNT" -eq 0 ]; then
        echo "  Nenhum aviso pendente."
    else
        echo ""
        echo "  Total: $AVISO_COUNT aviso(s) para o CRONOS tratar"
        RESULTADO_FINAL="ALERTA"
        ALERTAS=$((ALERTAS + AVISO_COUNT))
    fi
    if [ "$LEGADO_COUNT" -gt 0 ]; then
        echo "  ($LEGADO_COUNT arquivo(s) legado(s) janela-*.txt)"
    fi
else
    echo "  Pasta de ativacoes nao encontrada."
fi
echo ""

# ───────────────────────────────────────────────────────
# RELATORIO FINAL
# ───────────────────────────────────────────────────────

if [ "$MODO_RESUMO" = true ]; then
    exec 1>&3
fi

echo "═══════════════════════════════════════════════════"
if [ "$RESULTADO_FINAL" = "OK" ]; then
    echo "  RESULTADO: OK — Nenhum problema detectado"
else
    echo "  RESULTADO: ALERTA — $ALERTAS ponto(s) de atencao"
fi
echo "═══════════════════════════════════════════════════"
echo ""

exit 0
