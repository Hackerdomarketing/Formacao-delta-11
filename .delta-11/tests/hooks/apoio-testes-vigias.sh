#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Apoio comum aos testes dos vigias JS/Shell (Delta-11 v6.3)
# ════════════════════════════════════════════════════════════════
# Não é um teste (o rodar-todos.sh só executa *.test.*): é carregado
# com `source` pelos testes check-lock, heartbeat, log-activity,
# on-stop, pre-compact, release-locks, abrir-painel, fim-subagente e
# registro-vigias.
#
# Segurança: todo projeto de teste é criado com mktemp FORA de qualquer
# repositório git. Isso importa: a fonte do Delta-11 é um repositório
# git e os vigias gravam na pasta principal descoberta pelo
# `git rev-parse --git-common-dir`. Rodar um vigia com cwd dentro da
# fonte gravaria no .delta-11 real.
#
# Os vigias são chamados pelo COMANDO EXATO do registro
# (templates/settings-hooks.json), via `sh -c '<comando>'`, com
# CLAUDE_PROJECT_DIR apontando para o projeto de teste e o evento JSON
# no stdin — igual ao Claude Code.
# ════════════════════════════════════════════════════════════════

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
APOIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(cd "$APOIO_DIR/../../hooks" && pwd)"
SETTINGS="$(cd "$APOIO_DIR/../../templates" && pwd)/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

PASTAS_TEMP=()
limpar_pastas_temp() {
    local d
    for d in "${PASTAS_TEMP[@]:-}"; do
        [ -n "$d" ] || continue
        case "$d" in
            */d11-teste.*) [ -d "$d" ] && rm -rf "$d" ;;   # só apaga o que este apoio criou
        esac
    done
}
trap limpar_pastas_temp EXIT

# Cria um projeto Delta-11 de teste (sem git) e imprime o caminho real.
novo_projeto() {
    local d
    d=$(mktemp -d "${TMPDIR:-/tmp}/d11-teste.XXXXXX") || return 1
    d=$(cd "$d" && pwd -P)
    if git -C "$d" rev-parse --git-dir >/dev/null 2>&1; then
        echo "ERRO: pasta temporaria $d esta dentro de um repositorio git" >&2
        return 1
    fi
    mkdir -p "$d/.delta-11/ativacoes" "$d/.delta-11/locks" "$d/src"
    cp -R "$HOOKS_DIR" "$d/.delta-11/hooks"
    echo "$d"
}

# Transforma o projeto em repositório git com uma worktree em
# .claude/worktrees/w1 (como o isolation: "worktree" do Claude Code).
com_git_e_worktree() {
    local d="$1"
    (
        cd "$d" || exit 1
        git init -q
        git config user.email "teste@delta11.local"
        git config user.name "Teste Delta-11"
        echo "x" > src/a.ts
        printf '.claude/\n' > .gitignore
        git add -A && git commit -qm "inicio"
        git worktree add -q .claude/worktrees/w1 -b w1
    ) >/dev/null 2>&1
}

# comando_do_registro EVENTO ARQUIVO-DO-HOOK → imprime o comando registrado
comando_do_registro() {
    python3 - "$SETTINGS" "$1" "$2" <<'PY'
import json, sys
dados = json.load(open(sys.argv[1], encoding="utf-8"))
for grupo in dados.get("hooks", {}).get(sys.argv[2], []):
    for hook in grupo.get("hooks", []):
        if hook.get("command", "").rstrip('"').endswith("/hooks/" + sys.argv[3]):
            print(hook["command"])
            sys.exit(0)
sys.exit(1)
PY
}

# matchers_do_registro EVENTO ARQUIVO-DO-HOOK → um matcher por linha
matchers_do_registro() {
    python3 - "$SETTINGS" "$1" "$2" <<'PY'
import json, sys
dados = json.load(open(sys.argv[1], encoding="utf-8"))
for grupo in dados.get("hooks", {}).get(sys.argv[2], []):
    for hook in grupo.get("hooks", []):
        if hook.get("command", "").rstrip('"').endswith("/hooks/" + sys.argv[3]):
            print(grupo.get("matcher", ""))
PY
}

# rodar PROJETO CWD COMANDO JSON → define SAIDA, ERRO e CODIGO
rodar() {
    local projeto="$1" cwd="$2" comando="$3" json="$4" arquivo_erro
    arquivo_erro=$(mktemp "${TMPDIR:-/tmp}/d11-teste-erro.XXXXXX")
    SAIDA=$(cd "$cwd" && printf '%s' "$json" | CLAUDE_PROJECT_DIR="$projeto" sh -c "$comando" 2>"$arquivo_erro")
    CODIGO=$?
    ERRO=$(cat "$arquivo_erro")
    rm -f "$arquivo_erro"
}

# json_valido ARQUIVO → 0 se o arquivo é JSON válido
json_valido() { python3 -m json.tool "$1" >/dev/null 2>&1; }

# campo_json ARQUIVO CAMPO → imprime o valor (vazio se faltar)
campo_json() {
    python3 -c 'import json,sys
try:
    v = json.load(open(sys.argv[1], encoding="utf-8")).get(sys.argv[2])
    print("" if v is None else v)
except Exception:
    print("")' "$1" "$2"
}

# Torna um arquivo "velho" (N horas atrás) — funciona em macOS e Linux
envelhecer() {
    local arquivo="$1" horas="$2" carimbo
    carimbo=$(python3 -c 'import sys,time;print(time.strftime("%Y%m%d%H%M.%S", time.localtime(time.time()-float(sys.argv[1])*3600)))' "$horas")
    touch -t "$carimbo" "$arquivo"
}

resultado_final() {
    echo ""
    if [ "$falhou" -eq 0 ]; then
        echo -e "${GREEN}OK — $1${NC}"
        exit 0
    fi
    echo -e "${RED}FALTA $falhou item(ns) — $1${NC}"
    exit 1
}
