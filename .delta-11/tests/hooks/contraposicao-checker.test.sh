#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do hook contraposicao-checker.py (Etapa 3 do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que:
#   1. O hook contraposicao-checker.py existe em .delta-11/hooks/
#   2. É executável (chmod +x)
#   3. Detecta arquivo project-core.md (case A — alvo do hook)
#   4. Detecta arquivos NAO-project-core (case B — nao é alvo)
#   5. É registrado em templates/settings-hooks.json (PreToolUse Edit|Write)
#   6. Implementa exit codes corretos (0=passa, 2=bloqueia)
#   7. Verifica presença da seção "Contraposição" ou "contraposicao" no
#      project-core.md (criterio minimo do Principio 3)
#   8. É cross-platform (Python 3, não depende de bash externo)
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"
HOOK="$HOOKS_DIR/contraposicao-checker.py"
SETTINGS="$SCRIPT_DIR/../../templates/settings-hooks.json"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. Hook existe
if [ -f "$HOOK" ]; then
    ok "hook existe em $HOOK"
else
    err "hook AUSENTE em $HOOK"
    echo ""
    echo "Este teste é guarda de regressão do Principio 3 da Metodologia Genesis."
    echo "Se o hook sumir, o sistema inteiro perde a verificação automatica de"
    echo "contraposicao lateral. O teste falhará até que o hook seja criado."
    exit 1
fi

# 2. Hook é executavel
if [ -x "$HOOK" ]; then
    ok "hook é executavel"
else
    err "hook NAO é executavel (chmod +x $HOOK)"
fi

# 3. Hook detecta arquivo project-core.md
if grep -q "project-core\|project_core\|projectcore" "$HOOK"; then
    ok "hook detecta arquivo project-core.md"
else
    err "hook NAO detecta arquivo project-core.md — alvo incorreto"
fi

# 4. Hook é registrado no settings-hooks.json (PreToolUse Edit|Write)
if [ -f "$SETTINGS" ]; then
    if grep -q "contraposicao-checker" "$SETTINGS"; then
        ok "hook registrado em settings-hooks.json"
    else
        err "hook NAO registrado em settings-hooks.json — nao sera invocado"
    fi
else
    err "settings-hooks.json AUSENTE"
fi

# 5. Hook implementa exit codes 0 e 2 (PreToolUse convention)
if grep -qE "sys\.exit\(0\)|return 0" "$HOOK" && grep -qE "sys\.exit\(2\)|return 2" "$HOOK"; then
    ok "hook implementa exit codes 0 (passa) e 2 (bloqueia)"
else
    err "hook NAO implementa exit codes PreToolUse (0 e 2)"
fi

# 6. Hook busca a string "contraposicao" ou "contraposição" no conteudo
if grep -qiE "contraposi[cç][ãa]o" "$HOOK"; then
    ok "hook verifica presença de 'contraposição' no conteudo"
else
    err "hook NAO verifica palavra 'contraposição' — sem isso não tem como detectar"
fi

# 7. Hook é Python (cross-platform — mesmo padrao de pre-selo.py)
if head -1 "$HOOK" | grep -q "python3\|python"; then
    ok "hook é Python (cross-platform)"
else
    err "hook NAO é Python — quebra compatibilidade Windows/Linux/Mac"
fi

# 8. Hook tem docstring explicando o que faz
if head -5 "$HOOK" | grep -qE '"""'; then
    ok "hook tem docstring explicativa"
else
    err "hook NAO tem docstring — falta contexto para o proximo mantenedor"
fi

# Teste funcional leve: rodar o hook com input de project-core SEM contraposicao
# deve dar exit code 2 (bloqueia)
# CRIA arquivo temporario (o hook faz append se o arquivo existe)
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/memoria"
TEST_PC="$TEST_DIR/.delta-11/memoria/project-core.md"
cat > "$TEST_PC" <<'EOF'
# Project Core
## Dia 1 — Luz
(algum conteudo)
EOF

# Simula um evento PreToolUse (formato JSON via stdin)
# Write com conteudo SEM contraposicao — deve bloquear
RESULT=$(echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$TEST_PC\",\"content\":\"# Project Core\\n## Dia 1 — Luz\\n(sem contraposicao)\"}}" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "2" ]; then
    ok "hook BLOQUEIA (exit 2) project-core.md sem contraposicao"
elif [ "$EXIT_CODE" = "0" ]; then
    err "hook NAO bloqueia project-core sem contraposicao (deveria dar exit 2)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE) — esperado 2 para bloqueio"
fi

# Teste funcional inverso: project-core COM contraposicao deve passar (exit 0)
RESULT=$(echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$TEST_PC\",\"content\":\"# Project Core\\n## Dia 1\\n**Contraposição:** existencial-identitaria\"}}" | python3 "$HOOK" 2>/dev/null; echo "EXIT=$?")
EXIT_CODE=$(echo "$RESULT" | grep "EXIT=" | cut -d= -f2)

if [ "$EXIT_CODE" = "0" ]; then
    ok "hook PASSA (exit 0) project-core.md COM contraposicao"
elif [ "$EXIT_CODE" = "2" ]; then
    err "hook BLOQUEIA project-core COM contraposicao (deveria dar exit 0)"
else
    err "hook retornou exit code inesperado ($EXIT_CODE) para project-core valido"
fi

# Limpa
rm -rf "$TEST_DIR"

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — hook contraposicao-checker.py implementado corretamente${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) — corrigir antes de prosseguir${NC}"
    exit 1
fi