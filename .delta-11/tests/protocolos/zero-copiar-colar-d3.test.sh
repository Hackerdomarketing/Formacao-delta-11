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
# nada") são permitidas — o teste ignora linhas com negação.
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

expect_no_instruction "nenhum texto pede para copiar e colar" "$COPIAR_COLAR" "${ARQUIVOS[@]}"
expect_no_instruction "nenhum texto pede para colar um bloco ou prompt" "$COLAR_BLOCO" "${ARQUIVOS[@]}"
expect_no_instruction "nenhum texto pede para abrir nova janela, sessão ou aba" "$NOVA_JANELA" "${ARQUIVOS[@]}"
expect_no_instruction "nenhum texto pede para ativar um agente manualmente" "$ATIVAR_MANUAL" "${ARQUIVOS[@]}"
expect_no_instruction "nenhum texto manda pedir ao comandante que abra, cole, ative, rode ou dispare algo" \
    "$PEDIR_AO_COMANDANTE" "${ARQUIVOS[@]}"

# Lado positivo: o CLAUDE.md diz que o disparo é feito pelo Agent tool.
expect_match "$REPO_ROOT/CLAUDE.md" "Agent tool" "CLAUDE.md documenta o disparo via Agent tool"

finish_test "D3 — zero copiar-e-colar"
