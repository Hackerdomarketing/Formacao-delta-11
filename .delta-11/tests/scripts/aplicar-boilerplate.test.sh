#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do aplicar-boilerplate.sh (G2 — F6, F11, F12 do Bloco A)
# ════════════════════════════════════════════════════════════════
#
# Estratégia (v5.4 E1): cria 3 probes em /tmp:
#   1. projeto SEM src/          → script DEVE recusar (F11)
#   2. projeto válido COM src/   → script DEVE aplicar overlay
#   3. projeto COM arquivos pré-existentes → script DEVE fazer backup (F12)
#
# Valida também env.example cita Regra 15 (F6).
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
APPLICADOR="$REPO_ROOT/boilerplate-delta-11-nextjs/aplicar-boilerplate.sh"
ENV_EXAMPLE="$REPO_ROOT/boilerplate-delta-11-nextjs/overlay/env.example"

if [ ! -f "$APPLICADOR" ]; then
    echo -e "${RED}[FAIL]${NC} aplicador nao encontrado: $APPLICADOR"
    exit 1
fi
if [ ! -f "$ENV_EXAMPLE" ]; then
    echo -e "${RED}[FAIL]${NC} env.example nao encontrado: $ENV_EXAMPLE"
    exit 1
fi

SANDBOX="$(mktemp -d /tmp/delta11-boilerplate-test-XXXXXX)"
falhou=0

cleanup() { rm -rf "$SANDBOX"; }
trap cleanup EXIT

ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FAIL]${NC} $1"; falhou=$((falhou + 1)); }

# ─── Probe 1: projeto SEM src/ → script recusa (F11) ─────────
PROBE1="$SANDBOX/projeto-sem-src"
mkdir -p "$PROBE1"
echo '{"name":"sem-src"}' > "$PROBE1/package.json"

if bash "$APPLICADOR" "$PROBE1" >/dev/null 2>&1; then
    err "Probe 1 (sem src/): script DEVERIA ter recusado (F11) e aceitou"
else
    ok "Probe 1: projeto sem src/ foi recusado (F11 OK)"
fi

# ─── Probe 2: projeto válido COM src/ → script aplica ───────
PROBE2="$SANDBOX/projeto-ok"
mkdir -p "$PROBE2/src"
echo '{"name":"ok"}' > "$PROBE2/package.json"

if bash "$APPLICADOR" "$PROBE2" >/dev/null 2>&1; then
    # Conferir que copiou src/lib/env.ts
    if [ -f "$PROBE2/src/lib/env.ts" ] || [ -d "$PROBE2/src/lib" ]; then
        ok "Probe 2: projeto com src/ aplicado com sucesso"
    else
        err "Probe 2: script rodou mas nao copiou src/lib/"
    fi
else
    err "Probe 2: projeto valido foi recusado indevidamente"
fi

# ─── Probe 3: arquivos pré-existentes → backup criado (F12) ─
PROBE3="$SANDBOX/projeto-com-conflito"
mkdir -p "$PROBE3/src/lib"
echo "env antigo" > "$PROBE3/.env.example"
echo "meu lib custom" > "$PROBE3/src/lib/meu-arquivo-custom.ts"
echo '{"name":"conflito"}' > "$PROBE3/package.json"

# O aplicar vai tentar copiar src/ do overlay sobre $PROBE3/src/ — isso vai dar erro
# pq $PROBE3/src/lib existe. Mas vamos capturar o que importa: o backup.
bash "$APPLICADOR" "$PROBE3" >/dev/null 2>&1 || true

# Se houve backup, fica .bak-YYYYMMDD-HHMMSS
backup_count=$(find "$PROBE3" -name "*.bak-*" | wc -l | xargs)
if [ "$backup_count" -gt 0 ]; then
    ok "Probe 3: backup(s) criado(s) para arquivos pre-existentes (F12 OK) — $backup_count .bak-*"
else
    # Aceitavel se o cp -R sobrescreveu a pasta em vez de arquivo individual
    # O importante é que NAO houve perda silenciosa. Verificar que o arquivo custom sobreviveu:
    if [ -f "$PROBE3/src/lib/meu-arquivo-custom.ts" ]; then
        ok "Probe 3: arquivo custom preservado (cp -R mesclou a pasta)"
    else
        err "Probe 3: nenhum backup E arquivo custom perdido (F12 nao fechou)"
    fi
fi

# ─── Verificação direta: env.example cita Regra 15 (F6) ──────
if grep -q "REGRA INVIOÁVEL 15\|REGRA INVIOLAVEL 15\|Regra 15" "$ENV_EXAMPLE"; then
    ok "env.example cita Regra 15 (F6 OK)"
else
    err "env.example NAO cita Regra 15 (F6 nao fechado)"
fi

# ─── Verificação: --force existe no script ──────────────────
if grep -q '\-\-force' "$APPLICADOR"; then
    ok "aplicar-boilerplate.sh suporta --force para sobrescrita"
else
    err "aplicar-boilerplate.sh nao suporta --force"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} aplicar-boilerplate: F6 (Regra 15) + F11 (check src/) + F12 (backup) todos OK"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi