#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste de regressão AP#9 + AP#10 + AP#12 — modo padrão e painel automático
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos:
#   AP#9  (D1)  O modo padrão do selo é "automatico":
#               - o arquivo .delta-11/.modo-selo da distribuição contém automatico;
#               - CLAUDE.md, CRONOS.md e o template do selo não chamam o
#                 "manual" de padrão;
#               - CLAUDE.md e CRONOS.md dizem que o padrão é automático;
#               - o comando "modo manual" continua existindo (opção).
#   AP#10 (D27) O painel abre sozinho: existe o hook hooks/abrir-painel.sh,
#               ele tenta macOS (open), Linux (xdg-open) e Windows (start), e
#               o CLAUDE.md não manda o comandante abrir o painel na mão.
#   AP#12       instalar.sh (só na fonte oficial) tenta várias plataformas.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

CLAUDE="$REPO_ROOT/CLAUDE.md"
CRONOS="$DELTA_DIR/operativos/CRONOS.md"
SELO="$DELTA_DIR/templates/selo-experiencial-template.md"
MODO_SELO="$DELTA_DIR/.modo-selo"
ABRIR_PAINEL="$DELTA_DIR/hooks/abrir-painel.sh"
INSTALAR="$REPO_ROOT/instalar.sh"

# ─── AP#9 / D1 ───────────────────────────────────────────────
if require_file "$MODO_SELO" ".delta-11/.modo-selo"; then
    modo_atual=$(tr -d '[:space:]' < "$MODO_SELO")
    if [ "$modo_atual" = "automatico" ]; then
        pass "D1: .delta-11/.modo-selo da distribuição contém \"automatico\""
    else
        fail "D1: .delta-11/.modo-selo contém \"$modo_atual\" (esperado: automatico)"
    fi
fi

MANUAL_PADRAO='modo manual[^.;]{0,40}(padr(ã|a)o|PADR(Ã|A)O|default)|`manual`[^.;]{0,40}(padr(ã|a)o|PADR(Ã|A)O|default)|manual[^.;]{0,6}\((padr(ã|a)o|PADR(Ã|A)O)'
expect_no_instruction "D1: nenhum texto chama o modo manual de padrão" \
    "$MANUAL_PADRAO" "$CLAUDE" "$CRONOS" "$SELO"

AUTOMATICO_PADRAO='autom(á|a)tico`?[^.;]{0,40}(padr(ã|a)o|PADR(Ã|A)O|default)|(padr(ã|a)o|PADR(Ã|A)O|default)[^.;]{0,30}autom(á|a)tico'
expect_match "$CLAUDE" "$AUTOMATICO_PADRAO" "D1: CLAUDE.md diz que o padrão é automático"
expect_match "$CRONOS" "$AUTOMATICO_PADRAO" "D1: CRONOS.md diz que o padrão é automático"
expect_match "$CRONOS" "modo manual" "D1: o comando \"modo manual\" continua documentado no CRONOS.md"

# ─── AP#10 / D27 ─────────────────────────────────────────────
if require_file "$ABRIR_PAINEL" ".delta-11/hooks/abrir-painel.sh (D27)"; then
    for comando in "open" "xdg-open" "start"; do
        if grep -qE "(^|[^a-z-])$comando([^a-z-]|$)" "$ABRIR_PAINEL"; then
            pass "D27: abrir-painel.sh tenta \"$comando\""
        else
            fail "D27: abrir-painel.sh não tenta \"$comando\""
        fi
    done
fi
expect_no_instruction "AP#10: CLAUDE.md não manda o comandante abrir o painel na mão" \
    "painel[^.]{0,40}(abrir no navegador|abra (no|o) navegador|abra manualmente)|abr(a|ir) (o )?painel[^.]{0,20}manualmente" "$CLAUDE"

# ─── AP#12 (arquivo só da fonte oficial) ─────────────────────
if is_official_source; then
    expect_match "$INSTALAR" "xdg-open" "AP#12: instalar.sh tenta xdg-open (Linux) além de open (Mac)"
else
    skip "AP#12: instalar.sh só existe na fonte oficial (rodando dentro de um projeto)"
fi

finish_test "AP#9 + AP#10 + AP#12 — modo automático e painel que abre sozinho"
