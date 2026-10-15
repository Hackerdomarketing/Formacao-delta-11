#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Suíte de Testes Automatizada do Sistema (v6.4)
# ════════════════════════════════════════════════════════════════
#
# Filosofia: a infra de teste CRESCE a cada versão. Toda mudança
# adiciona pelo menos 1 teste e fecha com 100% verde.
#
# Uso:
#   bash .delta-11/tests/rodar-todos.sh                      # roda tudo
#   bash .delta-11/tests/rodar-todos.sh --rapido             # só os hooks
#   bash .delta-11/tests/rodar-todos.sh --hook pre-criacao-arquivo
#   bash .delta-11/tests/rodar-todos.sh --pasta protocolos   # uma pasta só
#
# Pastas rodadas (nesta ordem): hooks, templates, conhecimento,
# protocolos, operativos, scripts. Funções comuns: tests/framework/.
#
# Saída de cada teste: .delta-11/scratch/AAAA-MM-DD-testes-delta11/
# (D21 — nada em /tmp). A saída de um teste que passou é apagada; a de
# um teste que falhou fica lá para leitura (o gc-locks limpa em 7 dias).
#
# Isolamento: os testes rodam com HOME, DELTA11_REGISTRY e
# DELTA11_SEARCH_PATHS apontando para uma pasta temporária dentro do
# scratch — nenhum teste toca no $HOME real nem no registro real de
# projetos (~/.delta-11-registry.json).
#
# Todos os testes rodam ANTES do resumo. Se o teste do hook
# pre-criacao-arquivo falhar, o aviso de segurança aparece em destaque
# no fim — mas os outros testes rodam do mesmo jeito (antes a suíte
# parava ali e o relatório ficava incompleto — C-131).
#
# Exit code: 0 se todos passaram, 1 se algum falhou, 2 uso errado.
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
DELTA_DIR="$(cd "$TESTS_DIR/.." && pwd)"
REPO_ROOT="$(cd "$DELTA_DIR/.." && pwd)"
PASTAS_DE_TESTE=(hooks templates conhecimento protocolos operativos scripts)

# Pasta de saída (D21): .delta-11/scratch/AAAA-MM-DD-testes-delta11/
OUTPUT_DIR="$DELTA_DIR/scratch/$(date +%Y-%m-%d)-testes-delta11"
mkdir -p "$OUTPUT_DIR"
ISOLATED_HOME="$(mktemp -d "$OUTPUT_DIR/home-isolado-XXXXXX")"

# Contadores
TOTAL=0
PASSOU=0
FALHOU=0
FALHAS=()
SEGURANCA_REGREDIU=false

log_ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
log_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; }

limpar_home_isolado() {
    # Apaga só a pasta temporária criada acima (nunca uma variável vazia).
    if [ -n "${ISOLATED_HOME:-}" ] && [ -d "$ISOLATED_HOME" ] && [[ "$ISOLATED_HOME" == "$OUTPUT_DIR"/home-isolado-* ]]; then
        rm -rf "$ISOLATED_HOME"
    fi
    rmdir "$OUTPUT_DIR" 2>/dev/null || true
}
trap limpar_home_isolado EXIT

rodar_teste() {
    local script="$1"
    local desc="$2"
    TOTAL=$((TOTAL + 1))

    if [ ! -f "$script" ]; then
        log_fail "$desc — script não encontrado: $script"
        FALHAS+=("$desc")
        FALHOU=$((FALHOU + 1))
        return
    fi

    local cmd
    case "$script" in
        *.test.py) cmd=(python3 "$script") ;;
        *)         cmd=(bash "$script") ;;
    esac

    local saida
    saida="$OUTPUT_DIR/$(basename "$(dirname "$script")")--$(basename "$script").out"

    # Roda a partir da RAIZ do projeto (os testes calculam caminhos a partir dela)
    # e com HOME/registro isolados.
    if (cd "$REPO_ROOT" && \
        HOME="$ISOLATED_HOME" \
        DELTA11_REGISTRY="$ISOLATED_HOME/.delta-11-registry.json" \
        DELTA11_SEARCH_PATHS="$ISOLATED_HOME" \
        "${cmd[@]}") >"$saida" 2>&1; then
        log_ok "$desc"
        PASSOU=$((PASSOU + 1))
        rm -f "$saida"
    else
        log_fail "$desc — saída completa: ${saida#"$REPO_ROOT"/}"
        echo -e "      ${YELLOW}saída:${NC}"
        sed 's/^/        /' "$saida" | head -20
        FALHAS+=("$desc")
        FALHOU=$((FALHOU + 1))
        if [[ "$desc" == *"pre-criacao-arquivo"* ]]; then
            SEGURANCA_REGREDIU=true
        fi
    fi
}

rodar_pasta() {
    local pasta="$1"
    local f
    echo -e "${BOLD}[$pasta]${NC}"
    if [ ! -d "$TESTS_DIR/$pasta" ]; then
        echo -e "  ${YELLOW}(pasta tests/$pasta não existe)${NC}"
        echo ""
        return
    fi
    for f in "$TESTS_DIR/$pasta/"*.test.*; do
        [ -f "$f" ] || continue
        rodar_teste "$f" "$pasta/$(basename "$f" | sed -E 's/\.test\.(py|sh)$//')"
    done
    echo ""
}

banner() {
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  Formação Δ-11 — Suíte de Testes v6.4${NC}"
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

resumo() {
    local cor="$GREEN"
    [ "$FALHOU" -eq 0 ] || cor="$RED"
    echo -e "${cor}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${cor}${BOLD}  Resultado: ${PASSOU}/${TOTAL} OK${NC}"
    if [ "$FALHOU" -gt 0 ]; then
        echo -e "${RED}  ${FALHOU} teste(s) falharam:${NC}"
        for f in "${FALHAS[@]}"; do
            echo -e "${RED}    - $f${NC}"
        done
        echo -e "  Saídas dos que falharam: ${OUTPUT_DIR#"$REPO_ROOT"/}/"
    fi
    echo -e "${cor}${BOLD}════════════════════════════════════════════════════════════${NC}"

    if [ "$SEGURANCA_REGREDIU" = true ]; then
        echo ""
        echo -e "${RED}${BOLD}  ATENÇÃO: o hook de SEGURANÇA pre-criacao-arquivo regrediu.${NC}"
        echo -e "${RED}${BOLD}  Investigue ANTES de confiar no resto do resultado.${NC}"
        echo "  Possíveis causas:"
        echo "    1. sincronizar.sh trouxe versão antiga de outro projeto"
        echo "    2. git pull trouxe versão antiga (raro — checar git log)"
        echo "    3. o hook foi editado e regrediu"
        echo "  Recuperação:"
        echo "    git checkout HEAD -- .delta-11/hooks/pre-criacao-arquivo.py"
        echo "    bash .delta-11/tests/rodar-todos.sh --hook pre-criacao-arquivo"
    fi
}

terminar() {
    resumo
    [ "$FALHOU" -eq 0 ] && exit 0
    exit 1
}

# ─── Filtros CLI ────────────────────────────────────────────────
MODO="${1:-todos}"
FILTRO="${2:-}"

case "$MODO" in
    --rapido|--hooks|--hook)
        banner
        if [ -n "$FILTRO" ]; then
            echo -e "${BOLD}Modo: hook $FILTRO${NC}"
            echo ""
            achou=false
            for f in "$TESTS_DIR/hooks/$FILTRO.test.py" "$TESTS_DIR/hooks/$FILTRO.test.sh"; do
                if [ -f "$f" ]; then
                    rodar_teste "$f" "hooks/$FILTRO"
                    achou=true
                fi
            done
            if [ "$achou" = false ]; then
                echo -e "${RED}Nenhum teste encontrado para o hook '$FILTRO' em tests/hooks/.${NC}"
                exit 2
            fi
            echo ""
        else
            echo -e "${BOLD}Modo: somente hooks${NC}"
            echo ""
            rodar_pasta hooks
        fi
        terminar
        ;;
    --pasta)
        banner
        if [ -z "$FILTRO" ] || [ ! -d "$TESTS_DIR/$FILTRO" ]; then
            echo "Uso: bash $0 --pasta <${PASTAS_DE_TESTE[*]}>"
            exit 2
        fi
        rodar_pasta "$FILTRO"
        terminar
        ;;
    todos|--all|"")
        banner
        echo -e "${BOLD}Modo: suíte completa${NC}"
        echo ""
        for pasta in "${PASTAS_DE_TESTE[@]}"; do
            rodar_pasta "$pasta"
        done
        terminar
        ;;
    *)
        echo "Uso: bash $0 [todos | --rapido | --hook <nome-do-hook> | --pasta <pasta>]"
        exit 2
        ;;
esac
