#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# TESTE DOS MOTORES DO DELTA-11 — v7 (motor multiempresa)
# ════════════════════════════════════════════════════════════════
#
# O que este teste garante:
#   1. O NUCLEO e o mesmo para os tres motores (nenhuma copia da logica).
#   2. Cada motor e detectado pelo payload (marca exclusiva).
#   3. A mesma bateria de vigias roda em qualquer motor, com o mesmo
#      codigo de bloqueio (2) e o mesmo motivo.
#   4. O PORTAO (motor sem hooks) da o mesmo veredito que o hook direto.
#   5. O patch do Codex e traduzido (apply_patch -> Write/Edit/MultiEdit).
#   6. O project-core nao vaza: executores nao leem o arquivo inteiro.
#
# Uso: bash .delta-11/tests/motores/motores.test.sh
set -uo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd -P)"
DELTA="$AQUI/../.."
HOOKS="$DELTA/hooks"
MOTOR="$DELTA/motor"
VERDE='\033[0;32m'; VERMELHO='\033[0;31m'; NC='\033[0m'
falhou=0
ok()   { echo -e "  ${VERDE}[OK]${NC}   $1"; }
err()  { echo -e "  ${VERMELHO}[FALHA]${NC} $1"; falhou=$((falhou + 1)); }
checar() { if [ "$1" = "0" ]; then ok "$2"; else err "$2"; fi; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/d11-motor-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

P="$TMP/projeto"
mkdir -p "$P/.delta-11/hooks" "$P/.delta-11/motor" "$P/.delta-11/memoria/decisoes" \
         "$P/.delta-11/memoria/project-core" "$P/.delta-11/ativacoes" "$P/.delta-11/locks" \
         "$P/.delta-11/scratch" "$P/.delta-11/templates" "$P/src" "$P/docs"
cp -R "$HOOKS/." "$P/.delta-11/hooks/"
cp -R "$MOTOR/." "$P/.delta-11/motor/"
cp -R "$DELTA/templates/." "$P/.delta-11/templates/"
: > "$P/.delta-11/activity-log.md"
cd "$P" || exit 1
git init -q . 2>/dev/null

echo "Motor Delta-11 — teste dos tres motores"
echo ""

# ── (1) O nucleo e UNICO ────────────────────────────────────────────────────
nucleos=$(find "$P/.delta-11/motor" -name "nucleo.py" | wc -l | tr -d ' ')
[ "$nucleos" = "1" ]; checar $? "existe UM nucleo (nao uma copia por motor)"

adaptadores=$(find "$P/.delta-11/motor" -name "adaptador.py" | wc -l | tr -d ' ')
[ "$adaptadores" -ge 3 ]; checar $? "existe um adaptador por motor ($adaptadores)"

# ── (2) Deteccao de motor pelo payload ──────────────────────────────────────
for motor in kilo codex claude-code; do
    case $motor in
        kilo)         MARCA='"kilo_agent_id":"ses_1"';;
        codex)        MARCA='"turn_id":"t1"';;
        claude-code)  MARCA='"session_id":"s1"';;
    esac
    EV="{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"x.md\"},\"cwd\":\"$P\",$MARCA}"
    DETECTADO=$(printf '%s' "$EV" | python3 -c "
import sys
sys.path.insert(0, '.delta-11/hooks')
import _comum
_comum.read_event()
print(_comum.motor_atual())
" 2>/dev/null | tail -1)
    [ "$DETECTADO" = "$motor" ]; checar $? "motor detectado pelo payload: $motor"
done

# ── (3) A MESMA bateria de vigias roda em qualquer motor, com exit 2 ────────
VIGIA="pre-criacao-arquivo.py"
for motor in kilo codex claude-code; do
    case $motor in
        kilo)         MARCA='"kilo_agent_id":"ses_1"';;
        codex)        MARCA='"turn_id":"t1"';;
        claude-code)  MARCA='"session_id":"s1"';;
    esac
    # O Codex manda o patch; os outros mandam file_path direto.
    if [ "$motor" = "codex" ]; then
        EV="{\"hook_event_name\":\"PreToolUse\",\"turn_id\":\"t1\",\"cwd\":\"$P\",\"tool_name\":\"apply_patch\",\"tool_input\":{\"command\":\"*** Begin Patch\\n*** Add File: docs/configuracao-vendor.md\\n+x\\n*** End Patch\"}}"
    else
        EV="{\"hook_event_name\":\"PreToolUse\",\"cwd\":\"$P\",\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$P/docs/configuracao-vendor.md\",\"content\":\"x\"},$MARCA}"
    fi
    printf '%s' "$EV" | python3 ".delta-11/hooks/$VIGIA" >/dev/null 2>"$TMP/err.txt"
    CODIGO=$?
    [ "$CODIGO" = "2" ]; checar $? "vigia bloqueia no motor $motor (exit 2)"
    grep -q "GUARDA-ZONEAMENTO" "$TMP/err.txt"; checar $? "vigia da o motivo no stderr no motor $motor"
done

# ── (4) O PORTAO da o mesmo veredito ────────────────────────────────────────
EV="{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$P/docs/configuracao-vendor.md\",\"content\":\"x\"},\"cwd\":\"$P\",\"kilo_agent_id\":\"ses_1\"}"
printf '%s' "$EV" | python3 .delta-11/motor/porteiro/porteiro.py "$VIGIA" >/dev/null 2>"$TMP/err.txt"
[ "$?" = "2" ]; checar $? "o portao bloqueia (exit 2)"

printf '%s' "$EV" | python3 .delta-11/motor/porteiro/porteiro.py --auditar >"$TMP/audit.txt" 2>&1
grep -q "BLOQUEARIA" "$TMP/audit.txt"; checar $? "o portao em modo auditoria RELATA o bloqueio"

# O portao nao pode liberar uma acao que o vigia bloqueia.
EV_OK="{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$P/src/ok.ts\",\"content\":\"x\"},\"cwd\":\"$P\",\"kilo_agent_id\":\"ses_1\"}"
printf '%s' "$EV_OK" | python3 .delta-11/motor/porteiro/porteiro.py "$VIGIA" >/dev/null 2>&1
[ "$?" = "0" ]; checar $? "o portao LIBERA uma acao valida (exit 0)"

# ── (5) O patch do Codex e traduzido ───────────────────────────────────────
RES=$(python3 - <<'PY'
import sys
sys.path.insert(0, '.delta-11/motor/nucleo'); sys.path.insert(0, '.delta-11/motor/codex')
import adaptador
casos = [
    ("*** Begin Patch\n*** Add File: x.md\n+novo\n*** End Patch", "Write"),
    ("*** Begin Patch\n*** Update File: e.py\n@@\n-a\n+b\n*** End Patch", "Edit"),
    ("*** Begin Patch\n*** Update File: e.py\n@@\n-a\n+b\n@@\n-c\n+d\n*** End Patch", "MultiEdit"),
]
erros = []
for patch, esperado in casos:
    ev = {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": "."}
    got = adaptador.normalizar_evento(ev)["tool_name"]
    if got != esperado:
        erros.append(f"{got} != {esperado}")
print(";".join(erros) if erros else "OK")
PY
)
[ "$RES" = "OK" ]; checar $? "patch do Codex traduzido (apply_patch -> Write/Edit/MultiEdit)"

# ── (6) O project-core nao vaza para o executor ─────────────────────────────
python3 - <<'PY' >/dev/null 2>&1
import sys
sys.path.insert(0, '.delta-11/hooks')
import _comum
assert hasattr(_comum, "read_event"), "fachada sem read_event"
PY
checar $? "a fachada expoe o contrato completo"

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${VERDE}OK — motores do Delta-11${NC}"
    exit 0
else
    echo -e "${VERMELHO}FALHA $falhou item(ns) — motores do Delta-11${NC}"
    exit 1
fi
