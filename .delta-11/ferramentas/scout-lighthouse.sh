#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SCOUT — Auditoria Lighthouse de Performance (v6.3 — 2026-10-14)
# ═══════════════════════════════════════════════════════════════
#
# Roda Google Lighthouse e retorna scores de:
#   1. Performance
#   2. Acessibilidade
#   3. Melhores Praticas
#   4. SEO
#
# Uso:
#   bash .delta-11/ferramentas/scout-lighthouse.sh [url]
#   bash .delta-11/ferramentas/scout-lighthouse.sh http://localhost:3000
#
# Requer: lighthouse (npm i -g lighthouse), Chrome/Chromium e python3.
#
# Saida (convencao das ferramentas v6.3):
#   0 = PASS
#   1 = FAIL (score ruim, URL fora do ar ou Lighthouse quebrou)
#   2 = INCOMPLETO — o Lighthouse (ou o python3) nao esta instalado: a
#       checagem de desempenho NAO rodou. Antes respondia "SKIP" com saida 0
#       e a checagem sumia sem aviso (C-136).
#
# Relatorio temporario em .delta-11/scratch/ (D21 — nada em /tmp), com nome
# unico de verdade (o mktemp do macOS nao troca os X quando ha extensao
# depois deles) e apagado na saida, mesmo se a execucao for interrompida.
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

URL="${1:-http://localhost:3000}"
RESULTADO_FINAL="PASS"

find_main_folder() {
    local common_dir
    if common_dir=$(git rev-parse --git-common-dir 2>/dev/null) && [ -n "$common_dir" ]; then
        (cd "$common_dir/.." && pwd)
    elif [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
        echo "$CLAUDE_PROJECT_DIR"
    else
        pwd
    fi
}

echo "═══════════════════════════════════════════════════"
echo "  SCOUT LIGHTHOUSE — Auditoria de Performance"
echo "  URL: $URL"
echo "═══════════════════════════════════════════════════"
echo ""

# Programas obrigatorios: ausencia = INCOMPLETO bem visivel (nao "passou").
for programa in lighthouse python3; do
    if ! command -v "$programa" &>/dev/null; then
        echo "  ┌─────────────────────────────────────────────────────────┐"
        echo "  │ INCOMPLETO — '$programa' nao esta instalado.            "
        echo "  │ A auditoria de desempenho NAO rodou. Nao trate como OK. "
        echo "  └─────────────────────────────────────────────────────────┘"
        if [ "$programa" = "lighthouse" ]; then
            echo "  Instale com: npm install -g lighthouse"
        fi
        echo ""
        echo "═══════════════════════════════════════════════════"
        echo "  RESULTADO: INCOMPLETO"
        echo "═══════════════════════════════════════════════════"
        exit 2
    fi
done

# Verificar se URL esta acessivel
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL" 2>/dev/null || true)
if [ -z "$HEALTH" ] || [ "$HEALTH" = "000" ]; then
    echo "  FAIL — URL nao acessivel: $URL"
    exit 1
fi

echo "[1/2] Rodando Lighthouse (pode demorar 30-60 segundos)..."

if [ -d "$(find_main_folder)/.delta-11" ]; then
    SCRATCH_DIR="$(find_main_folder)/.delta-11/scratch"
    mkdir -p "$SCRATCH_DIR"
    TEMP_REPORT=$(mktemp "$SCRATCH_DIR/lighthouse-XXXXXX")
else
    TEMP_REPORT=$(mktemp)
fi
trap 'rm -f "$TEMP_REPORT"' EXIT

if ! lighthouse "$URL" \
    --output=json \
    --output-path="$TEMP_REPORT" \
    --chrome-flags="--headless --no-sandbox" \
    --only-categories=performance,accessibility,best-practices,seo \
    --quiet \
    2>/dev/null; then
    echo "  FAIL — Lighthouse falhou ao rodar"
    echo "  Verifique se Chrome/Chromium esta instalado"
    exit 1
fi

echo "[2/2] Analisando resultados..."
echo ""

# Extrair scores (o caminho vai como argumento — nao dentro do codigo python)
SCORES=$(python3 - "$TEMP_REPORT" <<'PY' 2>/dev/null || true
import json, sys
with open(sys.argv[1]) as report_file:
    data = json.load(report_file)
categories = data.get("categories", {})
for key in ["performance", "accessibility", "best-practices", "seo"]:
    category = categories.get(key, {})
    score = int((category.get("score", 0) or 0) * 100)
    print(f"{key}|{score}")
PY
)

if [ -z "$SCORES" ]; then
    echo "  FAIL — nao foi possivel ler o relatorio do Lighthouse"
    exit 1
fi

echo "  Categoria          Score"
echo "  ─────────────────  ─────"

while IFS='|' read -r categoria score; do
    if [ "$score" -ge 90 ]; then
        indicador="OTIMO"
    elif [ "$score" -ge 50 ]; then
        indicador="MEDIO"
    else
        indicador="RUIM"
        RESULTADO_FINAL="FAIL"
    fi
    printf "  %-19s %3s  [%s]\n" "$categoria" "$score" "$indicador"
done <<< "$SCORES"

# ───────────────────────────────────────────────────────
# RELATORIO FINAL
# ───────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════"
echo "  RESULTADO: $RESULTADO_FINAL"
echo "═══════════════════════════════════════════════════"
echo ""

if [ "$RESULTADO_FINAL" = "PASS" ]; then
    exit 0
fi
exit 1
