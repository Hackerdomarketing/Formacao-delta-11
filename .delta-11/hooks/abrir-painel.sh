#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DELTA-11 v6.3 — Hook SessionStart: abrir o painel sozinho (N-001, D27)
# ═══════════════════════════════════════════════════════════════
# Registro (templates/settings-hooks.json):
#   SessionStart  matcher ""  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/abrir-painel.sh"
#
# O que faz:
#   1. Descobre a PASTA PRINCIPAL do projeto (D25): pai do
#      `git rev-parse --git-common-dir`; senão $CLAUDE_PROJECT_DIR;
#      senão o cwd. Abre SEMPRE o painel da pasta principal, nunca o de
#      uma worktree.
#   2. Se `.delta-11/painel.html` existe e a marca
#      `.delta-11/ativacoes/.painel-aberto` tem menos de 8 horas, não
#      abre de novo (uma vez por sessão de trabalho, não a cada agente).
#   3. Senão grava a marca (com a hora UTC) e abre o painel:
#      macOS `open`, Linux `xdg-open`, Windows `start`.
#
# Para desligar (ex.: servidor sem tela): crie `.delta-11/.nao-abrir-painel`.
#
# Nunca falha a sessão: não imprime nada no stdout (no SessionStart o
# stdout entra no contexto do modelo) e sai sempre com 0.
# ═══════════════════════════════════════════════════════════════

HORAS_ENTRE_ABERTURAS=8

ENTRADA=$(cat 2>/dev/null)

# cwd do evento (JSON lido com python3; se faltar, o diretório atual)
CWD=""
if command -v python3 >/dev/null 2>&1; then
    CWD=$(printf '%s' "$ENTRADA" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("cwd") or "")
except Exception:
    print("")' 2>/dev/null)
fi
[ -n "$CWD" ] || CWD=$(pwd)

raiz_principal() {
    local pasta="$1" comum candidato
    comum=$(git -C "$pasta" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
    for candidato in "${comum:+$(dirname "$comum")}" "${CLAUDE_PROJECT_DIR:-}" "$pasta"; do
        if [ -n "$candidato" ] && [ -d "$candidato/.delta-11" ]; then
            echo "$candidato"
            return 0
        fi
    done
    return 1
}

RAIZ=$(raiz_principal "$CWD") || exit 0
PAINEL="$RAIZ/.delta-11/painel.html"
MARCA="$RAIZ/.delta-11/ativacoes/.painel-aberto"

[ -f "$PAINEL" ] || exit 0
[ -f "$RAIZ/.delta-11/.nao-abrir-painel" ] && exit 0

# Já abriu nas últimas 8 horas? (find -mmin funciona em macOS e Linux)
if [ -f "$MARCA" ] && [ -z "$(find "$MARCA" -mmin +$((HORAS_ENTRE_ABERTURAS * 60)) 2>/dev/null)" ]; then
    exit 0
fi

mkdir -p "$RAIZ/.delta-11/ativacoes" 2>/dev/null
date -u +%Y-%m-%dT%H:%M:%SZ > "$MARCA" 2>/dev/null

case "$(uname -s 2>/dev/null)" in
    Darwin)
        { command -v open && open "$PAINEL"; } >/dev/null 2>&1 &
        ;;
    MINGW*|MSYS*|CYGWIN*)
        { cmd.exe /c start "" "$(cygpath -w "$PAINEL" 2>/dev/null || echo "$PAINEL")"; } >/dev/null 2>&1 &
        ;;
    *)
        { command -v xdg-open && xdg-open "$PAINEL"; } >/dev/null 2>&1 &
        ;;
esac

LOG="$RAIZ/.delta-11/activity-log.md"
[ -f "$LOG" ] && printf -- '- [%s] [abrir-painel] [SISTEMA] painel aberto: %s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" ".delta-11/painel.html" >> "$LOG" 2>/dev/null

exit 0
