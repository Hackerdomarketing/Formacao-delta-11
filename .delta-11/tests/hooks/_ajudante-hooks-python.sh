#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Ajudante comum dos testes dos vigias Python — Delta-11 v6.3
# ════════════════════════════════════════════════════════════════
# NAO e um teste (nao termina em .test.sh): os testes fazem
#   source "$(dirname "$0")/_ajudante-hooks-python.sh" nome-do-hook
#
# Garantias:
#   - Todo cenario roda num PROJETO TEMPORARIO (mktemp -d), com
#     CLAUDE_PROJECT_DIR apontando para ele. Nada e gravado no
#     repositorio real nem no $HOME.
#   - Cada cenario tem UM resultado esperado (0, 1 ou 2). Nada de
#     "aceita 0 ou 2" (C-126).
#   - O codigo de saida e o do proprio python3, sem "|| python".
# ════════════════════════════════════════════════════════════════

AJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(cd "$AJ_DIR/../../hooks" && pwd)"
HOOK_NOME="${1:?informe o nome do hook}"
HOOK="$HOOKS_DIR/$HOOK_NOME.py"

VERDE='\033[0;32m'; VERMELHO='\033[0;31m'; SEM_COR='\033[0m'
falhou=0
TEST_DIR=""
SAIDA_CODIGO=""
SAIDA_ERRO=""
SAIDA_PADRAO=""

ok()  { echo -e "  ${VERDE}[OK]${SEM_COR}   $1"; }
err() { echo -e "  ${VERMELHO}[FALHA]${SEM_COR} $1"; falhou=$((falhou + 1)); }

limpar_projeto() {
    if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
        case "$TEST_DIR" in
            */tmp.*|*/delta11-teste-*) rm -rf "$TEST_DIR" ;;
        esac
    fi
    TEST_DIR=""
}
trap limpar_projeto EXIT

# Cria um projeto Delta-11 temporario vazio e entra nele.
novo_projeto() {
    limpar_projeto
    TEST_DIR="$(cd "$(mktemp -d "${TMPDIR:-/tmp}/delta11-teste-XXXXXX")" && pwd -P)"
    mkdir -p "$TEST_DIR/.delta-11/memoria/decisoes" "$TEST_DIR/.delta-11/memoria/project-core" \
             "$TEST_DIR/.delta-11/ativacoes" "$TEST_DIR/.delta-11/logs/sub-agentes" \
             "$TEST_DIR/.delta-11/locks" "$TEST_DIR/.delta-11/scratch"
    : > "$TEST_DIR/.delta-11/activity-log.md"
    export CLAUDE_PROJECT_DIR="$TEST_DIR"
    cd "$TEST_DIR" || exit 1
}

# Monta o JSON do evento. Uso: evento chave=valor ...
#   chaves com ponto viram objetos: tool_input.file_path=...
#   valor "@arquivo" le o conteudo do arquivo; "json:..." e JSON cru.
#   cwd vira o projeto temporario se nao for informado.
evento() {
    python3 - "$TEST_DIR" "$@" <<'PY'
import json, sys
projeto, pares = sys.argv[1], sys.argv[2:]
dados = {"cwd": projeto, "session_id": "sessao-teste", "hook_event_name": "PreToolUse"}
for par in pares:
    chave, _, valor = par.partition("=")
    if valor.startswith("@"):
        valor = open(valor[1:], encoding="utf-8").read()
    elif valor.startswith("json:"):
        valor = json.loads(valor[5:])
    alvo = dados
    partes = chave.split(".")
    for p in partes[:-1]:
        alvo = alvo.setdefault(p, {})
    alvo[partes[-1]] = valor
print(json.dumps(dados, ensure_ascii=False))
PY
}

# Roda o hook com o JSON dado (no stdin). Preenche SAIDA_CODIGO/ERRO/PADRAO.
rodar_hook() {
    local json="$1"
    local arq_erro arq_saida
    arq_erro="$(mktemp "${TMPDIR:-/tmp}/delta11-teste-erro-XXXXXX")"
    arq_saida="$(mktemp "${TMPDIR:-/tmp}/delta11-teste-saida-XXXXXX")"
    (cd "$TEST_DIR" && printf '%s' "$json" | python3 "$HOOK" >"$arq_saida" 2>"$arq_erro")
    SAIDA_CODIGO=$?
    SAIDA_ERRO="$(cat "$arq_erro")"
    SAIDA_PADRAO="$(cat "$arq_saida")"
    rm -f "$arq_erro" "$arq_saida"
}

# espera CODIGO "descricao" JSON
espera() {
    local esperado="$1" descricao="$2" json="$3"
    rodar_hook "$json"
    if [ "$SAIDA_CODIGO" = "$esperado" ]; then
        ok "$descricao (exit $SAIDA_CODIGO)"
    else
        err "$descricao — esperado exit $esperado, veio $SAIDA_CODIGO. stderr: $(echo "$SAIDA_ERRO" | head -3 | tr '\n' ' ')"
    fi
}

# confere que o stderr da ultima execucao contem um trecho
stderr_contem() {
    if printf '%s' "$SAIDA_ERRO" | grep -qF -- "$1"; then ok "mensagem cita: $1"; else err "mensagem NAO cita: $1"; fi
}

# confere que o activity-log do projeto temporario tem uma linha no formato D25
log_contem() {
    local arquivo="$TEST_DIR/.delta-11/activity-log.md"
    if [ ! -f "$arquivo" ]; then err "activity-log nao existe"; return; fi
    if grep -qE -- "$1" "$arquivo"; then ok "activity-log tem: $1"; else err "activity-log NAO tem: $1"; fi
}

# arquivo com mtime N horas atras
envelhecer() {
    python3 -c "import os,sys,time; t=time.time()-float(sys.argv[2])*3600; os.utime(sys.argv[1],(t,t))" "$1" "$2"
}

agora_iso()   { date -u +%Y-%m-%dT%H:%M:%SZ; }
horas_atras() { python3 -c "import datetime,sys; print((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=float(sys.argv[1]))).strftime('%Y-%m-%dT%H:%M:%SZ'))" "$1"; }

# Checagens estaticas comuns a todo vigia Python (C-006, C-016, C-017)
checagens_basicas() {
    if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE: $HOOK"; fim; fi
    if head -1 "$HOOK" | grep -q "python3"; then ok "Python 3"; else err "sem shebang python3"; fi
    if head -5 "$HOOK" | grep -q '"""'; then ok "docstring no topo"; else err "sem docstring"; fi
    if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$HOOK"; then ok "sintaxe valida"; else err "sintaxe invalida"; fi
    if grep -q "import _comum" "$HOOK"; then ok "usa o utilitario comum (_comum.py)"; else err "nao usa _comum.py"; fi
    if grep -q "utcnow" "$HOOK"; then err "ainda usa datetime.utcnow (C-017)"; else ok "sem datetime.utcnow (C-017)"; fi
    if grep -qE 'Path\("\.delta-11' "$HOOK"; then err "caminho relativo .delta-11 fixo no codigo (C-006)"; else ok "sem caminho relativo fixo (C-006)"; fi
    if grep -q "comum.run(main" "$HOOK"; then ok "erro interno tratado por _comum.run (C-016)"; else err "sem _comum.run (C-016)"; fi
}

# Escreve o kanban do projeto temporario
kanban() { printf '%s\n' "$1" > "$TEST_DIR/.delta-11/kanban.md"; }

fim() {
    limpar_projeto
    echo ""
    if [ "$falhou" -eq 0 ]; then
        echo -e "${VERDE}OK — $HOOK_NOME${SEM_COR}"
        exit 0
    fi
    echo -e "${VERMELHO}FALHA — $HOOK_NOME: $falhou item(ns)${SEM_COR}"
    exit 1
}
