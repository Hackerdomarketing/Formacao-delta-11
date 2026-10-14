#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Funções comuns da suíte de testes (v6.3 — 2026-10-14)
# ════════════════════════════════════════════════════════════════
#
# Para que serve esta pasta (C-070): até a v6.2 a pasta tests/framework/
# existia vazia. Na v6.3 ela guarda as funções que os testes de documento
# (protocolos, templates, conhecimento, operativos) usam em comum, para que
# todos sigam as mesmas regras de qualidade:
#
#   1. Checagem negativa ("o documento NÃO pode dizer X") FALHA quando o
#      arquivo não existe. Antes ela passava por engano (C-128).
#   2. Acentos: use alternância — (não|nao) — e nunca "n..o". O ponto do
#      grep conta bytes ou letras conforme o idioma do terminal, e o teste
#      mudava de resultado de uma máquina para outra.
#   3. Teste confere o CONCEITO exigido pelas decisões da v6.3, não uma
#      frase exata que pode ser reescrita.
#   4. Uma linha com negação ("nunca", "não", "sem", "ninguém pede",
#      "proibido"...) não conta como instrução. Assim "NUNCA peça para copiar e colar" não é
#      confundido com "copie e cole este bloco".
#
# Uso dentro de um teste (em tests/<pasta>/):
#   source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"
#   ...
#   finish_test "nome do teste"
#
# Variáveis prontas: DELTA_DIR (pasta .delta-11) e REPO_ROOT (raiz do
# projeto ou da fonte oficial).
# ════════════════════════════════════════════════════════════════

# Idioma do terminal: com UTF-8, "grep -i" iguala Ç/ç, Ã/ã... e o ponto do
# grep conta letras (não bytes). Sem isso o mesmo teste dava resultados
# diferentes conforme o terminal. Usa o primeiro UTF-8 disponível.
# (A lista vai para uma variável antes: com "set -o pipefail", um
# "locale -a | grep -q" falha quando o grep para de ler cedo.)
available_locales="$(locale -a 2>/dev/null || true)"
for test_locale in pt_BR.UTF-8 en_US.UTF-8 pt_BR.utf8 en_US.utf8 C.UTF-8 C.utf8; do
    if grep -qx "$test_locale" <<< "$available_locales"; then
        export LC_ALL="$test_locale"
        break
    fi
done
unset test_locale available_locales

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEST_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DELTA_DIR="$(cd "$TEST_HELPERS_DIR/../.." && pwd)"
REPO_ROOT="$(cd "$DELTA_DIR/.." && pwd)"

TEST_FAILURES=0

# Linha com qualquer uma destas expressões é tratada como proibição ou
# registro histórico, não como instrução ativa. O "não" sozinho NÃO basta
# (ex.: "o agente não executou e peça que ele ative manualmente" continua
# sendo instrução); vale só "não peça", "não precisa", "não deve",
# "não leia", "não escreva", "não atualize"...
NEGATION_PATTERN='(nunca|jamais|hip(ó|o)tese alguma|proib|❌|removid|legad|deixou de|em vez de|ao invés|ao inves|desatualizad|antes da v6|opt-in|nada mais|zero |(não|nao|NÃO|NAO) (peça|peca|PEÇA|precisa|deve|pode|use|usar|é mais|existe mais|pedir|pede|instrua|mande|há|leia|lê|ler|escreva|escreve|escrever|crie|criar|edite|editar|atualize|atualizar|grave|gravar|mexa|toque|mova|mover)|sem (você|voce|precisar|o humano|humano|intervenção|intervencao)|ningu(é|e)m (pede|pedir|precisa|deve|abre|cola|copia|ativa))'

pass() { echo -e "  ${GREEN}[OK]${NC}    $1"; }
fail() { echo -e "  ${RED}[FALTA]${NC} $1"; TEST_FAILURES=$((TEST_FAILURES + 1)); }
skip() { echo -e "  ${YELLOW}[PULADO]${NC} $1"; }

# A fonte oficial tem os instaladores na raiz. Num projeto do usuário eles
# não existem — os testes de arquivos que só existem na fonte são pulados
# (de forma visível) quando a suíte roda dentro de um projeto.
is_official_source() {
    [ -f "$REPO_ROOT/instalar.sh" ] && [ -f "$REPO_ROOT/sincronizar.sh" ]
}

# require_file <caminho> [rótulo] — falha (e devolve 1) se o arquivo não existe.
require_file() {
    local path="$1"
    local label="${2:-$1}"
    if [ -f "$path" ]; then
        return 0
    fi
    fail "arquivo ausente: $label ($path)"
    return 1
}

# expect_match <arquivo> <regex ERE> <o que deveria existir>
# Sem diferenciar maiúsculas de minúsculas.
expect_match() {
    local path="$1" pattern="$2" label="$3"
    require_file "$path" || return 0
    if grep -qiE -- "$pattern" "$path"; then
        pass "$label"
    else
        fail "$label — não encontrado em $(basename "$path")"
    fi
}

# expect_no_match <arquivo> <regex ERE> <o que NÃO pode existir>
# Exige que o arquivo exista ANTES (C-128). Mostra até 5 linhas culpadas.
expect_no_match() {
    local path="$1" pattern="$2" label="$3"
    require_file "$path" || return 0
    local found
    found=$(grep -niE -- "$pattern" "$path" | head -5 || true)
    if [ -z "$found" ]; then
        pass "$label"
    else
        fail "$label — encontrado em $(basename "$path"):"
        echo "$found" | cut -c1-200 | sed 's/^/            /'
    fi
}

# instruction_lines <regex ERE> <arquivo>... — imprime "arquivo:linha:texto"
# das linhas que casam com a regex e NÃO têm negação (ver NEGATION_PATTERN).
instruction_lines() {
    local pattern="$1"
    shift
    local path line text
    for path in "$@"; do
        [ -f "$path" ] || continue
        while IFS= read -r line; do
            text="${line#*:}"
            if ! grep -qiE -- "$NEGATION_PATTERN" <<< "$text"; then
                echo "${path#"$REPO_ROOT"/}:$line"
            fi
        done < <(grep -niE -- "$pattern" "$path" || true)
    done
}

# expect_no_instruction <rótulo> <regex ERE> <arquivo>...
# Todo arquivo da lista precisa existir. Falha se alguma linha SEM negação
# casar com a regex. Mostra até 8 linhas culpadas.
expect_no_instruction() {
    local label="$1" pattern="$2"
    shift 2
    local path missing=0
    for path in "$@"; do
        require_file "$path" "${path#"$REPO_ROOT"/}" || missing=1
    done
    [ "$missing" -eq 0 ] || return 0
    local found
    found=$(instruction_lines "$pattern" "$@" | head -8)
    if [ -z "$found" ]; then
        pass "$label"
    else
        fail "$label — ainda aparece como instrução:"
        echo "$found" | cut -c1-220 | sed 's/^/            /'
    fi
}

# markdown_section <arquivo> <regex ERE do título>
# Imprime a seção que começa no primeiro título que casa com a regex e
# termina no próximo título de nível igual ou maior (ex.: de "### FASE 3.5"
# até o próximo "### " ou "## "). Sem diferenciar maiúsculas de minúsculas,
# como o expect_match ("recorte" acha "## 2. Recorte").
markdown_section() {
    local path="$1" pattern="$2"
    [ -f "$path" ] || return 0
    awk -v pattern="$pattern" '
        function header_level(text,   count) {
            count = 0
            while (substr(text, count + 1, 1) == "#") count++
            return count
        }
        started == 0 && /^#+ / && tolower($0) ~ tolower(pattern) { started = 1; level = header_level($0); print; next }
        started == 1 && /^#+ / && header_level($0) <= level { exit }
        started == 1 { print }
    ' "$path"
}

# first_line_number <arquivo> <regex ERE> — número da primeira linha que casa (ou vazio).
first_line_number() {
    grep -nE -- "$2" "$1" 2>/dev/null | head -1 | cut -d: -f1 || true
}

# finish_test <nome> — imprime o resumo e sai com 0 (tudo certo) ou 1.
finish_test() {
    echo ""
    if [ "$TEST_FAILURES" -eq 0 ]; then
        echo -e "${GREEN}OK — $1${NC}"
        exit 0
    fi
    echo -e "${RED}FALTA $TEST_FAILURES item(ns) — $1${NC}"
    exit 1
}
