#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Suíte de Testes Automatizada do Sistema
# ════════════════════════════════════════════════════════════════
#
# Filosofia (v5.4 — Estágio 0): a infra de teste CRESCE a cada
# estágio do plano de execução. Todo estágio adiciona pelo menos 1
# teste e fecha com 100% verde antes de avançar.
#
# Uso:
#   bash .delta-11/tests/rodar-todos.sh           # roda tudo
#   bash .delta-11/tests/rodar-todos.sh --rapido  # só os hooks
#   bash .delta-11/tests/rodar-todos.sh --hook pre-criacao-arquivo
#
# Saída: linha por teste [OK] / [FAIL] + total X/Y no fim.
# Exit code: 0 se todos passaram, 1 se algum falhou.
# ════════════════════════════════════════════════════════════════

set -u

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Caminhos
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$TESTS_DIR/../hooks" && pwd)"
TEMPLATES_DIR="$(cd "$TESTS_DIR/../templates" && pwd)"
PROJECTS_DIR="$(cd "$TESTS_DIR/../.." && pwd)"

# Contadores
TOTAL=0
PASSOU=0
FALHOU=0

# Lista dos testes que falharam (para resumo)
FALHAS=()

log_ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
log_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; log_erro "$1"; }
log_info() { echo -e "  ${CYAN}[..]${NC}  $1"; }
log_erro() { FALHAS+=("$1"); }

rodar_teste() {
    local script="$1"
    local desc="$2"
    TOTAL=$((TOTAL + 1))

    if [ ! -f "$script" ]; then
        log_fail "$desc — script nao encontrado: $script"
        FALHOU=$((FALHOU + 1))
        return
    fi

    # Detectar interpretador pela extensão
    local cmd
    case "$script" in
        *.test.py) cmd=(python3 "$script") ;;
        *.test.sh) cmd=(bash "$script") ;;
        *)         cmd=(bash "$script") ;;
    esac

    if "${cmd[@]}" >/tmp/delta11-test-$$.out 2>&1; then
        log_ok "$desc"
        PASSOU=$((PASSOU + 1))
    else
        log_fail "$desc — ver /tmp/delta11-test-$$.out"
        echo -e "      ${YELLOW}saida:${NC}"
        sed 's/^/        /' /tmp/delta11-test-$$.out | head -20
        FALHOU=$((FALHOU + 1))
    fi
    rm -f /tmp/delta11-test-$$.out
}

banner() {
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  Formação Δ-11 — Suíte de Testes v5.4${NC}"
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

resumo() {
    local cor
    if [ "$FALHOU" -eq 0 ]; then
        cor="$GREEN"
    else
        cor="$RED"
    fi
    echo ""
    echo -e "${cor}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${cor}${BOLD}  Resultado: ${PASSOU}/${TOTAL} OK${NC}"
    if [ "$FALHOU" -gt 0 ]; then
        echo -e "${RED}  ${FALHOU} teste(s) falharam:${NC}"
        for f in "${FALHAS[@]}"; do
            echo -e "${RED}    - $f${NC}"
        done
    fi
    echo -e "${cor}${BOLD}════════════════════════════════════════════════════════════${NC}"
}

# ─── Filtros CLI ────────────────────────────────────────────────
MODO="${1:-todos}"
HOOK_FILTRO="${2:-}"

case "$MODO" in
    --rapido|--hooks)
        banner
        echo -e "${BOLD}Modo: somente hooks${NC}"
        echo ""
        if [ -n "$HOOK_FILTRO" ]; then
            for f in "$TESTS_DIR/hooks/"$HOOK_FILTRO".test.py" "$TESTS_DIR/hooks/"$HOOK_FILTRO".test.sh"; do
                [ -f "$f" ] && rodar_teste "$f" "hook $HOOK_FILTRO"
            done
        else
            for f in "$TESTS_DIR/hooks/"*.test.*; do
                [ -f "$f" ] || continue
                rodar_teste "$f" "$(basename "$f" | sed -E 's/\.(test\.(py|sh))$//')"
            done
        fi
        resumo
        [ "$FALHOU" -eq 0 ]
        exit $?
        ;;
    todos|--all|"")
        banner
        echo -e "${BOLD}Modo: suite completa${NC}"
        echo ""
        echo -e "${BOLD}[hooks]${NC}"
        for f in "$TESTS_DIR/hooks/"*.test.*; do
            [ -f "$f" ] || continue
            rodar_teste "$f" "$(basename "$f" | sed -E 's/\.(test\.(py|sh))$//')"
        done
        echo ""
        echo -e "${BOLD}[templates]${NC}"
        for f in "$TESTS_DIR/templates/"*.test.*; do
            [ -f "$f" ] || continue
            rodar_teste "$f" "$(basename "$f" | sed -E 's/\.(test\.(py|sh))$//')"
        done
        echo ""
        echo -e "${BOLD}[scripts]${NC}"
        for f in "$TESTS_DIR/scripts/"*.test.*; do
            [ -f "$f" ] || continue
            rodar_teste "$f" "$(basename "$f" | sed -E 's/\.(test\.(py|sh))$//')"
        done
        resumo
        [ "$FALHOU" -eq 0 ]
        exit $?
        ;;
    *)
        echo "Uso: bash $0 [todos|--rapido|--hooks [hook-nome]]"
        exit 2
        ;;
esac