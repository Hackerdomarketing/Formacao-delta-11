#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da decisão D13 (v6.3) — erro de API: 400 e formato único
# ════════════════════════════════════════════════════════════════
# Validação falhou ou campo faltando = HTTP 400, com o formato único:
#   { "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
# Conceitos conferidos:
#   1. Bases, templates, sub-agentes, protocolos e operativos não ensinam
#      422 para validação (linhas com "não use 422" são permitidas).
#   2. As bases de API (nextjs-api-patterns, backend-integracao-patterns),
#      o template de contratos e o sub-agente contract-tester mostram o
#      formato único: "VALIDATION_ERROR" + "details" e o status 400.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

ARQUIVOS=()
for pasta in conhecimento templates sub-agentes protocolos operativos; do
    for arquivo in "$DELTA_DIR/$pasta/"*.md; do
        [ -f "$arquivo" ] && ARQUIVOS+=("$arquivo")
    done
done
expect_no_instruction "nenhum texto ensina 422 para erro de validação (D13: 400)" \
    '(^|[^0-9])422([^0-9]|$)' "${ARQUIVOS[@]}"

FORMATO_UNICO=(
    "$DELTA_DIR/conhecimento/nextjs-api-patterns.md"
    "$DELTA_DIR/conhecimento/backend-integracao-patterns.md"
    "$DELTA_DIR/templates/contratos-api-template.md"
    "$DELTA_DIR/sub-agentes/contract-tester.md"
)
for arquivo in "${FORMATO_UNICO[@]}"; do
    nome="${arquivo#"$DELTA_DIR"/}"
    require_file "$arquivo" "$nome" || continue
    if grep -qE "VALIDATION_ERROR" "$arquivo" && grep -qE '"?details"?' "$arquivo"; then
        pass "$nome usa o formato único (VALIDATION_ERROR + details)"
    else
        fail "$nome não mostra o formato único { error: { code: \"VALIDATION_ERROR\", message, details } }"
    fi
    if grep -qE "(^|[^0-9])400([^0-9]|$)" "$arquivo"; then
        pass "$nome cita o status 400"
    else
        fail "$nome não cita o status 400 para validação"
    fi
done

finish_test "D13 — erro de API 400 com formato único"
