#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do bootstrap do gotchas.md (novo-projeto.sh — F5 da auditoria)
# ════════════════════════════════════════════════════════════════
#
# Estratégia (v5.4 E0): valida que novo-projeto.sh cria o arquivo
# .delta-11/memoria/gotchas.md dentro do projeto novo, copiando do
# template gotchas-inicial.md.
#
# Verificações:
#   1. Executa novo-projeto.sh em diretório-temporário descartável
#   2. Confirma que .delta-11/memoria/gotchas.md existe no destino
#   3. Confirma que tem pelo menos 1 gotcha (formato ## G-001:)
#   4. Confirma que tem o cabeçalho esperado
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/scripts/ → tests/ → .delta-11/ → raiz
REPO_ROOT="$SCRIPT_DIR/../../.."
NOVO_PROJETO="$REPO_ROOT/novo-projeto.sh"

if [ ! -f "$NOVO_PROJETO" ]; then
    echo -e "${RED}[FAIL]${NC} novo-projeto.sh nao encontrado: $NOVO_PROJETO"
    exit 1
fi

# Sandbox
TARGET="$(mktemp -d /tmp/delta11-f5-test-XXXXXX)"
cleanup() { rm -rf "$TARGET"; }
trap cleanup EXIT

# Responder "n" para VS Code
export PATH_BACKUP="$PATH"
# Simular 'n' para o read -p (echo n via stdin)
echo "n" | bash "$NOVO_PROJETO" "$TARGET" >/dev/null 2>&1

GOTCHAS="$TARGET/.delta-11/memoria/gotchas.md"
falhou=0

# 1. Arquivo existe
if [ ! -f "$GOTCHAS" ]; then
    echo -e "${RED}[FAIL]${NC} gotchas.md nao foi criado em $GOTCHAS"
    exit 1
fi

# 2. Tem pelo menos 1 gotcha formatado
if ! grep -q "^## G-001:" "$GOTCHAS"; then
    echo -e "${RED}[FAIL]${NC} gotchas.md sem entrada G-001 (formato esperado ## G-NNN:)"
    falhou=$((falhou + 1))
fi

# 3. Tem o cabeçalho orientativo
if ! grep -q "^# Gotchas do Projeto" "$GOTCHAS"; then
    echo -e "${RED}[FAIL]${NC} gotchas.md sem cabeçalho '# Gotchas do Projeto'"
    falhou=$((falhou + 1))
fi

# 4. Tem zona
if ! grep -q "Zona:" "$GOTCHAS"; then
    echo -e "${RED}[FAIL]${NC} gotchas.md sem campo Zona: (esperado pelo template)"
    falhou=$((falhou + 1))
fi

if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} bootstrap gotchas.md (F5): arquivo criado com formato correto"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi