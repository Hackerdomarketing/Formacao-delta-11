#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da decisão D3 (v6.3) — zero copiar-e-colar
# ════════════════════════════════════════════════════════════════
# Nenhum texto do sistema pede ao comandante para:
#   - copiar e colar um bloco ou prompt;
#   - abrir uma nova janela, sessão ou aba;
#   - "ativar manualmente" um agente;
#   - (qualquer forma de) "peça ao comandante que abra/cole/ative/rode".
# Todo disparo é feito pelo CRONOS via Agent tool (o ATLAS dispara só o CRONOS).
#
# Frases de proibição ("NUNCA peça para copiar e colar", "sem você colar
# nada", "Ninguém pede ao comandante para abrir janela") são permitidas — o
# teste ignora linhas com negação. Também ignora o REGISTRO HISTÓRICO do
# problema, no passado ("textos ainda pediam ao comandante para abrir
# janela"): descreve o que foi corrigido, não manda fazer.
# Arquivos: CLAUDE.md, operativos, protocolos, templates, sub-agentes e, na
# fonte oficial, GUIA-DO-COMANDANTE.md e README.md.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

ARQUIVOS=("$REPO_ROOT/CLAUDE.md")
for pasta in operativos protocolos templates sub-agentes; do
    for arquivo in "$DELTA_DIR/$pasta/"*.md; do
        [ -f "$arquivo" ] && ARQUIVOS+=("$arquivo")
    done
done
if is_official_source; then
    ARQUIVOS+=("$REPO_ROOT/GUIA-DO-COMANDANTE.md" "$REPO_ROOT/README.md")
else
    skip "GUIA-DO-COMANDANTE.md e README.md só existem na fonte oficial"
fi

COPIAR_COLAR='cop(i|ia|iar|ie|iam|iando)[[:space:]]+(e|ou)[[:space:]]+col(a|e|ar|ando|am)'
COLAR_BLOCO='(^|[^a-z])col(e|ar|ando)[[:space:]]+(o[[:space:]]+|este[[:space:]]+|esse[[:space:]]+|cada[[:space:]]+|um[[:space:]]+|o seguinte[[:space:]]+)?(bloco|prompt|texto)'
NOVA_JANELA='(abr(a|e|ir|am)|abre)[[:space:]]+(uma[[:space:]]+|um[[:space:]]+)?nova[[:space:]]+(janela|sess(ã|a)o|aba)'
ATIVAR_MANUAL='ativ(e|ar|a|em)[[:space:]]+manualmente'
PEDIR_AO_COMANDANTE='pe(ç|c)a[[:space:]]+(ao|para o)[[:space:]]+comandante[^.]{0,40}(abr|col|ativ|rod|dispar)'

# Registro histórico (verbo no passado): descreve o problema já corrigido.
HISTORY_PATTERN='(pediam|mandavam|antes (pedia|mandava))[^.]{0,40}comandante'

for arquivo in "${ARQUIVOS[@]}"; do
    require_file "$arquivo" "${arquivo#"$REPO_ROOT"/}" || true
done

# expect_no_active_instruction <rótulo> <regex> — como expect_no_instruction,
# mas também descarta as linhas de registro histórico.
expect_no_active_instruction() {
    local label="$1" pattern="$2" found
    found=$(instruction_lines "$pattern" "${ARQUIVOS[@]}" \
        | { grep -viE -- "$HISTORY_PATTERN" || true; } | head -8)
    if [ -z "$found" ]; then
        pass "$label"
    else
        fail "$label — ainda aparece como instrução:"
        echo "$found" | cut -c1-220 | sed 's/^/            /'
    fi
}

expect_no_active_instruction "nenhum texto pede para copiar e colar" "$COPIAR_COLAR"
expect_no_active_instruction "nenhum texto pede para colar um bloco ou prompt" "$COLAR_BLOCO"
expect_no_active_instruction "nenhum texto pede para abrir nova janela, sessão ou aba" "$NOVA_JANELA"
expect_no_active_instruction "nenhum texto pede para ativar um agente manualmente" "$ATIVAR_MANUAL"
expect_no_active_instruction "nenhum texto manda pedir ao comandante que abra, cole, ative, rode ou dispare algo" \
    "$PEDIR_AO_COMANDANTE"

# Lado positivo: o CLAUDE.md diz que o disparo é feito pelo Agent tool.
expect_match "$REPO_ROOT/CLAUDE.md" "Agent tool" "CLAUDE.md documenta o disparo via Agent tool"

finish_test "D3 — zero copiar-e-colar"
