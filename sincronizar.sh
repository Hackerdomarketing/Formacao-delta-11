#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMACAO D-11 — Sincronizar Sistema em Todos os Projetos
# ═══════════════════════════════════════════════════════════════
#
# Este script sincroniza os arquivos ESTRUTURAIS do sistema D-11
# (operativos, protocolos, sub-agentes, templates, CLAUDE.md, painel)
# em TODOS os projetos registrados no registry.
#
# O que ELE SINCRONIZA (arquivos do sistema):
#   - CLAUDE.md
#   - .delta-11/operativos/*.md
#   - .delta-11/protocolos/*.md
#   - .delta-11/sub-agentes/*.md
#   - .delta-11/templates/*.md
#   - .delta-11/painel.html
#
# O que ELE NUNCA TOCA (dados do projeto):
#   - .delta-11/kanban.md
#   - .delta-11/kanban-data.js
#   - .delta-11/memoria/**
#   - .delta-11/ativacoes/**
#   - .delta-11/.dispatch-mode  (modo de dispatch é específico de cada projeto/máquina)
#
# Como usar:
#   ./sincronizar.sh                    # Sincroniza tudo
#   ./sincronizar.sh --pull             # git pull antes de sincronizar
#   ./sincronizar.sh --dry-run          # Mostra o que faria sem fazer
#   ./sincronizar.sh --diff             # Mostra diff entre repo e projetos
#   ./sincronizar.sh --nota "mensagem"  # Adiciona nota de atualizacao
#
# REQUER: jq (brew install jq)
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

REGISTRY="$HOME/.delta-11-registry.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DRY_RUN=false
DO_PULL=false
DO_DIFF=false
NOTA=""

# ─── Parse argumentos ──────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --pull) DO_PULL=true; shift ;;
        --diff) DO_DIFF=true; shift ;;
        --nota) NOTA="$2"; shift 2 ;;
        *) echo -e "${RED}Argumento desconhecido: $1${NC}"; exit 1 ;;
    esac
done

# ─── Header ────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${BOLD}  FORMACAO D-11 — Sincronizacao (DRY RUN)${NC}"
else
    echo -e "${BOLD}  FORMACAO D-11 — Sincronizando Sistema${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── Verificar pre-requisitos ──────────────────────────────────

if ! command -v jq &> /dev/null; then
    echo -e "${RED}x jq nao encontrado. Instale com: brew install jq${NC}"
    exit 1
fi

if [ ! -f "$REGISTRY" ]; then
    echo -e "${RED}x Registry nao encontrado em $REGISTRY${NC}"
    echo "  Rode instalar.sh em um projeto para criar o registry."
    exit 1
fi

# ─── Ler registry ──────────────────────────────────────────────

SOURCE=$(jq -r '.source' "$REGISTRY")
BACKUP=$(jq -r '.backup' "$REGISTRY")
HISTORICAL=$(jq -r '.historical' "$REGISTRY")
PROJECTS=($(jq -r '.projects[]' "$REGISTRY"))

echo -e "  ${BOLD}Fonte:${NC}    $SOURCE"
echo -e "  ${BOLD}Projetos:${NC} ${#PROJECTS[@]} registrados"
echo -e "  ${BOLD}Backup:${NC}   $BACKUP"
echo ""

# ─── Verificar que estamos no repo fonte ───────────────────────

if [ "$SCRIPT_DIR" != "$SOURCE" ]; then
    echo -e "${YELLOW}! Script esta rodando de $SCRIPT_DIR${NC}"
    echo -e "  ${DIM}Esperado: $SOURCE${NC}"
    echo -e "  Usando $SOURCE como fonte de verdade."
    echo ""
fi

# ─── Git pull (opcional) ───────────────────────────────────────

if [ "$DO_PULL" = true ]; then
    echo -e "  ${YELLOW}[PULL]${NC} Atualizando repo de distribuicao..."
    cd "$SOURCE"
    git pull 2>&1 | while read line; do echo "    $line"; done
    echo -e "  ${GREEN}OK${NC} Pull concluido"
    echo ""
fi

# ─── Definir arquivos a sincronizar ────────────────────────────

# Coleta os arquivos do sistema no repo fonte
SYNC_FILES=()

# CLAUDE.md
if [ -f "$SOURCE/CLAUDE.md" ]; then
    SYNC_FILES+=("CLAUDE.md")
fi

# Operativos
for f in "$SOURCE/.delta-11/operativos/"*.md; do
    [ -f "$f" ] && SYNC_FILES+=(".delta-11/operativos/$(basename "$f")")
done

# Protocolos
for f in "$SOURCE/.delta-11/protocolos/"*.md; do
    [ -f "$f" ] && SYNC_FILES+=(".delta-11/protocolos/$(basename "$f")")
done

# Sub-agentes
for f in "$SOURCE/.delta-11/sub-agentes/"*.md; do
    [ -f "$f" ] && SYNC_FILES+=(".delta-11/sub-agentes/$(basename "$f")")
done

# Templates
for f in "$SOURCE/.delta-11/templates/"*.md; do
    [ -f "$f" ] && SYNC_FILES+=(".delta-11/templates/$(basename "$f")")
done

# Painel
if [ -f "$SOURCE/.delta-11/painel.html" ]; then
    SYNC_FILES+=(".delta-11/painel.html")
fi

echo -e "  ${BOLD}Arquivos de sistema:${NC} ${#SYNC_FILES[@]}"
echo ""

# ─── Modo diff ─────────────────────────────────────────────────

if [ "$DO_DIFF" = true ]; then
    echo -e "  ${BOLD}Comparando repo com projetos...${NC}"
    echo ""

    for proj in "${PROJECTS[@]}"; do
        proj_name=$(basename "$proj")
        echo -e "  ${CYAN}[$proj_name]${NC}"

        if [ ! -d "$proj" ]; then
            echo -e "    ${RED}x Pasta nao encontrada${NC}"
            continue
        fi

        DIFF_COUNT=0
        for rel_path in "${SYNC_FILES[@]}"; do
            src="$SOURCE/$rel_path"
            dst="$proj/$rel_path"

            if [ ! -f "$dst" ]; then
                echo -e "    ${YELLOW}+ $rel_path${NC} (nao existe no projeto)"
                DIFF_COUNT=$((DIFF_COUNT + 1))
            elif ! diff -q "$src" "$dst" &> /dev/null; then
                echo -e "    ${YELLOW}~ $rel_path${NC} (diferente)"
                DIFF_COUNT=$((DIFF_COUNT + 1))
            fi
        done

        if [ $DIFF_COUNT -eq 0 ]; then
            echo -e "    ${GREEN}OK Todos iguais${NC}"
        else
            echo -e "    ${YELLOW}$DIFF_COUNT arquivo(s) diferente(s)${NC}"
        fi
        echo ""
    done

    exit 0
fi

# ─── Funcao: sincronizar um destino ───────────────────────────

sincronizar_destino() {
    local destino="$1"
    local nome="$2"
    local copiados=0
    local ignorados=0
    local criados=0

    if [ ! -d "$destino" ]; then
        echo -e "    ${RED}x Pasta nao encontrada: $destino${NC}"
        return 1
    fi

    for rel_path in "${SYNC_FILES[@]}"; do
        local src="$SOURCE/$rel_path"
        local dst="$destino/$rel_path"

        # Criar diretorio pai se nao existir
        local dst_dir=$(dirname "$dst")
        if [ ! -d "$dst_dir" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "    ${DIM}mkdir -p $dst_dir${NC}"
            else
                mkdir -p "$dst_dir"
            fi
            criados=$((criados + 1))
        fi

        # Verificar se precisa copiar
        if [ -f "$dst" ] && diff -q "$src" "$dst" &> /dev/null; then
            ignorados=$((ignorados + 1))
            continue
        fi

        # Copiar
        if [ "$DRY_RUN" = true ]; then
            if [ ! -f "$dst" ]; then
                echo -e "    ${GREEN}+ $(basename "$rel_path")${NC} (novo)"
            else
                echo -e "    ${YELLOW}~ $(basename "$rel_path")${NC} (atualizado)"
            fi
        else
            cp "$src" "$dst"
        fi
        copiados=$((copiados + 1))
    done

    if [ $copiados -eq 0 ]; then
        echo -e "    ${GREEN}OK Ja estava atualizado${NC}"
    else
        echo -e "    ${GREEN}OK ${copiados} arquivo(s) sincronizado(s)${NC}, ${ignorados} ja iguais"
    fi
}

# ─── Sincronizar projetos ativos ──────────────────────────────

echo -e "  ${BOLD}Sincronizando projetos ativos...${NC}"
echo ""

PROJ_OK=0
PROJ_FAIL=0

for proj in "${PROJECTS[@]}"; do
    proj_name=$(basename "$proj")
    echo -e "  ${CYAN}[$proj_name]${NC}"

    if sincronizar_destino "$proj" "$proj_name"; then
        PROJ_OK=$((PROJ_OK + 1))
    else
        PROJ_FAIL=$((PROJ_FAIL + 1))
    fi
    echo ""
done

# ─── Sincronizar backup ───────────────────────────────────────

echo -e "  ${BOLD}Sincronizando backup...${NC}"
echo ""

backup_name=$(basename "$BACKUP")
echo -e "  ${CYAN}[$backup_name]${NC}"
if [ -d "$BACKUP" ]; then
    sincronizar_destino "$BACKUP" "$backup_name"

    # Backup tambem recebe os scripts de distribuicao
    for script in instalar.sh novo-projeto.sh disparar.sh sincronizar.sh GUIA-DO-COMANDANTE.md README.md; do
        if [ -f "$SOURCE/$script" ]; then
            if [ "$DRY_RUN" = true ]; then
                if [ ! -f "$BACKUP/$script" ] || ! diff -q "$SOURCE/$script" "$BACKUP/$script" &> /dev/null; then
                    echo -e "    ${YELLOW}~ $script${NC} (script de distribuicao)"
                fi
            else
                cp "$SOURCE/$script" "$BACKUP/$script"
            fi
        fi
    done
else
    echo -e "    ${YELLOW}! Pasta de backup nao encontrada${NC}"
fi

echo ""

# ─── Criar .last-update em cada projeto ────────────────────────

if [ "$DRY_RUN" = false ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")

    # Montar lista de arquivos alterados
    ALTERADOS=""
    for rel_path in "${SYNC_FILES[@]}"; do
        ALTERADOS="$ALTERADOS, $(basename "$rel_path")"
    done
    ALTERADOS="${ALTERADOS:2}" # remover ", " inicial

    UPDATE_NOTE="${NOTA:-Sincronizacao automatica}"

    for proj in "${PROJECTS[@]}"; do
        if [ -d "$proj/.delta-11" ]; then
            cat > "$proj/.delta-11/.last-update" << UPDATEEOF
$TIMESTAMP
Atualizacao: $UPDATE_NOTE
Arquivos sincronizados: $ALTERADOS
UPDATEEOF
        fi
    done

    # Atualizar timestamp no registry
    TMP_REG=$(mktemp)
    jq --arg ts "$TIMESTAMP" '.last_sync = $ts' "$REGISTRY" > "$TMP_REG" && mv "$TMP_REG" "$REGISTRY"
fi

# ─── Relatorio final ──────────────────────────────────────────

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}${BOLD}  DRY RUN — Nenhum arquivo foi alterado${NC}"
else
    echo -e "${GREEN}${BOLD}  OK Sincronizacao concluida${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Projetos: ${GREEN}$PROJ_OK OK${NC}"
if [ $PROJ_FAIL -gt 0 ]; then
    echo -e "  Falhas:   ${RED}$PROJ_FAIL${NC}"
fi
echo -e "  Backup:   ${GREEN}Atualizado${NC}"
echo -e "  Historico: ${DIM}Nao tocado (construcao-delta-11)${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "  ${DIM}Para verificar: ./sincronizar.sh --diff${NC}"
    echo -e "  ${DIM}Registry: $REGISTRY${NC}"
    echo ""
fi
