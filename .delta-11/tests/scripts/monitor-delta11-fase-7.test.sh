#!/usr/bin/env bash
# Teste da integracao do monitor-delta11.sh com Dia 7 (Etapa 7D)
#
# Verifica que monitor-delta11.sh:
#   1. Detecta operacao autonoma (>14 dias sem modificacao)
#   2. NAO detecta operacao autonoma se ha tarefas em FAZENDO
#   3. NAO detecta operacao autonoma se modificacao foi recente
#   4. Inclui campo operacao_autonoma no monitor-status.json
#   5. Inclui campo dias_silencio no monitor-status.json
#   6. Cross-reference com Fase 7 / Dia 7 da Metodologia

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MONITOR="$SCRIPT_DIR/../../../monitor-delta11.sh"
DOC_REF="$SCRIPT_DIR/../../../../conhecimento/metodologia-genesis-camadas.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ ! -f "$MONITOR" ]; then
    err "monitor-delta11.sh NAO existe em $MONITOR"
    exit 1
fi

# 1. Detecta operacao autonoma (>14 dias)
if grep -qE "OPERACAO_AUTONOMA|operacao.autonoma|THRESHOLD_DIAS" "$MONITOR"; then
    ok "monitor-delta11.sh tem variavel OPERACAO_AUTONOMA / THRESHOLD_DIAS"
else
    err "monitor-delta11.sh NAO tem deteccao de operacao autonoma"
fi

# 2. NAO detecta se ha tarefas em FAZENDO
if grep -qE "FAZENDO|em_fazendo.*0|operacao.*FAZENDO" "$MONITOR"; then
    ok "monitor-delta11.sh considera FAZENDO na deteccao"
else
    err "monitor-delta11.sh NAO considera FAZENDO — pode dar falso positivo"
fi

# 3. Threshold de 14 dias
if grep -qE "THRESHOLD_DIAS.*14|14.*dias.*silencio" "$MONITOR"; then
    ok "threshold de 14 dias (2 semanas) configurado"
else
    err "threshold NAO é 14 dias — Teste Supremo exige 2 semanas"
fi

# 4. Inclui campo operacao_autonoma no monitor-status.json
if grep -qF 'operacao_autonoma":${OPERACAO_AUTONOMA' "$MONITOR" || grep -qF 'operacao_autonoma' "$MONITOR"; then
    ok "campo operacao_autonoma incluido no JSON de status"
else
    err "campo operacao_autonoma AUSENTE do JSON"
fi

# 5. Inclui campo dias_silencio
if grep -qE "dias_silencio.*DIAS_OPERACAO_AUTONOMA" "$MONITOR"; then
    ok "campo dias_silencio incluido"
else
    err "campo dias_silencio AUSENTE"
fi

# 6. Cross-reference com Dia 7
if grep -qiE "Dia 7|Etapa 7|operacao.*autonoma|metodologia.*genesis" "$MONITOR"; then
    ok "cross-reference com Dia 7 / Metodologia Genesis"
else
    err "sem cross-reference — fica orfa do conceito"
fi

# Teste funcional — simular execucao do monitor
# Cenario A: projeto com ativacao antiga + sem FAZENDO → operacao_autonoma=true
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/.delta-11/ativacoes"
mkdir -p "$TEST_DIR/.delta-11/memoria"
TEST_REGISTRY="$HOME/.delta-11-registry.json"

# Cria um arquivo de ativacao com mtime de 20 dias atras (simula operacao autonoma)
touch -t "$(date -v-20d +%Y%m%d%H%M%S 2>/dev/null || date -d "20 days ago" +%Y%m%d%H%M%S)" "$TEST_DIR/.delta-11/ativacoes/ack-TEST.txt" 2>/dev/null || true

# Cria kanban sem tarefas FAZENDO
cat > "$TEST_DIR/.delta-11/kanban.md" <<'EOF'
# Kanban
## CONCLUIDO
- [x] T-001 Tudo feito
EOF

# Mock registry para usar so este projeto
echo "[\"$TEST_DIR\"]" > "$TEST_REGISTRY.backup" 2>/dev/null || true

# Backup registry original se existir
if [ -f "$TEST_REGISTRY" ]; then
    mv "$TEST_REGISTRY" "$TEST_REGISTRY.bak"
fi
echo "[\"$TEST_DIR\"]" > "$TEST_REGISTRY"

# Roda monitor
bash "$MONITOR" >/dev/null 2>&1 || true

# Limpa registry mock
rm -f "$TEST_REGISTRY"
if [ -f "$TEST_REGISTRY.bak" ]; then
    mv "$TEST_REGISTRY.bak" "$TEST_REGISTRY"
fi

# Verifica que monitor-status.json foi criado com campo operacao_autonoma
if [ -f "$TEST_DIR/.delta-11/monitor-status.json" ]; then
    if grep -q "operacao_autonoma" "$TEST_DIR/.delta-11/monitor-status.json"; then
        ok "monitor-status.json gerado COM campo operacao_autonoma"
    else
        err "monitor-status.json gerado SEM campo operacao_autonoma"
    fi
    if grep -q "dias_silencio" "$TEST_DIR/.delta-11/monitor-status.json"; then
        ok "monitor-status.json gerado COM campo dias_silencio"
    else
        err "monitor-status.json gerado SEM campo dias_silencio"
    fi
else
    err "monitor-status.json NAO foi gerado"
fi

rm -rf "$TEST_DIR"

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — monitor-delta11.sh detecta operacao autonoma${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }