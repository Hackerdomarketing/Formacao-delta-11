#!/usr/bin/env bash
# Teste do hook brief-preservado.py (Hook 8 do v6.2)
set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/brief-preservado.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ -f "$HOOK" ]; then ok "hook existe"; else err "hook AUSENTE"; exit 1; fi
if [ -x "$HOOK" ]; then ok "hook executavel"; else err "hook NAO executavel"; fi
if grep -qE "ativacoes" "$HOOK"; then ok "hook detecta .delta-11/ativacoes/"; else err "sem ativacoes"; fi
if grep -qE "ALERTA|severidade" "$HOOK"; then ok "hook tem nivel de severidade"; else err "sem severidade"; fi
if grep -qE "PostToolUse" "$HOOK"; then ok "hook documenta PostToolUse"; else err "sem PostToolUse"; fi
if head -1 "$HOOK" | grep -q "python"; then ok "Python"; else err "NAO Python"; fi
if [ -f "$SETTINGS" ] && grep -q "brief-preservado" "$SETTINGS"; then ok "registrado em settings"; else err "NAO em settings"; fi
if head -10 "$HOOK" | grep -qE '"""'; then ok "docstring"; else err "sem docstring"; fi
if grep -qE "sys\.exit\(0\)|sys\.exit\(main" "$HOOK"; then ok "exit 0 ou main()"; else err "sem exit 0"; fi

# Teste funcional
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
mkdir -p .delta-11/memoria .delta-11/ativacoes
echo "x" > .delta-11/ativacoes/primeiro.txt

# Cenario A: novo arquivo = INFO, exit 0
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '.delta-11/ativacoes/teste-brief.txt',
        'content': 'Conteudo inicial do brief do agente BACK. Tarefa T-1234: implementar feature X. Resumo: o agente deve fazer A, B, C. Contexto: o sistema esta em producao desde 2026-04-20. Estado: o banco tem 12 tabelas. Restricoes: nao quebrar compatibilidade.'
    }
}))
")
EXIT=$(echo "$EVENT" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?" | grep -oE '[0-9]+' | tail -1)
if [ "$EXIT" = "0" ]; then ok "PASSA (INFO) com arquivo novo"; else err "NAO passa novo (exit=$EXIT)"; fi

# Cenario B: reducao > 50% = ALERTA no log, exit 0 (PostToolUse)
EVENT=$(python3 -c "
import json
print(json.dumps({
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '.delta-11/ativacoes/teste-brief.txt',
        'content': 'curto'
    }
}))
")
echo "$EVENT" | python3 "$HOOK" 2>/dev/null >/dev/null
# Verifica se log tem ALERTA
if grep -q "ALERTA" .delta-11/activity-log.md 2>/dev/null; then
    ok "LOGA ALERTA quando tamanho cai > 50%"
else
    err "NAO loga ALERTA quando tamanho cai > 50%"
fi

cd / && rm -rf "$TEST_DIR"

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${GREEN}OK — Hook 8 brief-preservado.py${NC}"; exit 0; else echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; fi