#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SHIELD — Varredura de Seguranca Completa (v6.3 — 2026-10-14)
# ═══════════════════════════════════════════════════════════════
#
# Roda 3 verificacoes de seguranca e retorna relatorio unificado:
#   1. Semgrep (SAST — analise estatica de codigo; precisa de internet
#      para baixar as regras do "--config auto")
#   2. npm audit (vulnerabilidades altas/criticas em dependencias)
#   3. Deteccao de secrets (chaves, tokens, senhas no codigo) — inclusive
#      senha entre aspas simples: password='...' (C-137)
#
# Uso: bash .delta-11/ferramentas/shield-scan.sh [diretorio]
#   Se nao passar diretorio, usa o diretorio atual.
#
# Saida (convencao das ferramentas v6.3):
#   0 = PASS
#   1 = FAIL (problema de seguranca encontrado)
#   2 = INCOMPLETO — alguma checagem obrigatoria NAO rodou (semgrep ausente
#       ou sem internet, npm ausente/sem lockfile num projeto com
#       package.json). Antes isso saia como "SKIP" e o resultado era PASS.
#   Se houver FAIL e INCOMPLETO ao mesmo tempo, vale FAIL (1).
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

ALVO="${1:-.}"
RESULTADO_FINAL="PASS"
INCOMPLETO=false
RELATORIO=""

if [ ! -d "$ALVO" ]; then
    echo "ERRO: '$ALVO' nao e uma pasta."
    echo "Uso: shield-scan.sh [diretorio]"
    exit 1
fi

marcar_incompleto() {
    INCOMPLETO=true
    RELATORIO="$RELATORIO\n[INCOMPLETO] $1"
    echo "  INCOMPLETO — $1"
}

echo "═══════════════════════════════════════════════════"
echo "  SHIELD SCAN — Varredura de Seguranca"
echo "  Alvo: $ALVO"
echo "═══════════════════════════════════════════════════"
echo ""

# ───────────────────────────────────────────────────────
# 1. SEMGREP (SAST)
# ───────────────────────────────────────────────────────

echo "[1/3] Semgrep (analise estatica de codigo)..."

if ! command -v semgrep &>/dev/null; then
    marcar_incompleto "semgrep nao instalado — a analise estatica NAO rodou (pip install semgrep)"
elif ! command -v python3 &>/dev/null; then
    marcar_incompleto "python3 ausente — nao da para ler o resultado do semgrep"
else
    SEMGREP_OUTPUT=$(semgrep --config auto --json --quiet "$ALVO" 2>/dev/null || true)
    SEMGREP_COUNT=$(printf '%s' "$SEMGREP_OUTPUT" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('results',[])))" 2>/dev/null || true)

    if [ -z "$SEMGREP_COUNT" ]; then
        # Saida vazia ou que nao e JSON: normalmente falta de internet para baixar as regras.
        marcar_incompleto "semgrep nao devolveu resultado legivel (sem internet para o --config auto?)"
    elif [ "$SEMGREP_COUNT" -gt 0 ]; then
        RESULTADO_FINAL="FAIL"
        RELATORIO="$RELATORIO\n[SEMGREP] $SEMGREP_COUNT vulnerabilidade(s) encontrada(s):"
        RELATORIO="$RELATORIO\n$(printf '%s' "$SEMGREP_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"  - {r.get('check_id','?')}: {r.get('path','?')}:{r.get('start',{}).get('line','?')} — {r.get('extra',{}).get('message','sem descricao')}\")
" 2>/dev/null || echo "  (erro ao ler os resultados)")"
        echo "  FAIL — $SEMGREP_COUNT problema(s)"
    else
        echo "  PASS — nenhuma vulnerabilidade"
    fi
fi

# ───────────────────────────────────────────────────────
# 2. NPM AUDIT (dependencias)
# ───────────────────────────────────────────────────────

echo "[2/3] npm audit (vulnerabilidades em dependencias)..."

if [ ! -f "$ALVO/package.json" ]; then
    echo "  NAO SE APLICA — sem package.json"
elif ! command -v npm &>/dev/null || ! command -v python3 &>/dev/null; then
    marcar_incompleto "npm (ou python3) ausente num projeto com package.json — dependencias NAO verificadas"
else
    AUDIT_OUTPUT=$(cd "$ALVO" && npm audit --json 2>/dev/null || true)
    AUDIT_VULNS=$(printf '%s' "$AUDIT_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'metadata' not in data:
    raise SystemExit(1)
meta = data['metadata'].get('vulnerabilities', {})
print(meta.get('high', 0) + meta.get('critical', 0))
" 2>/dev/null || true)

    if [ -z "$AUDIT_VULNS" ]; then
        marcar_incompleto "npm audit nao devolveu resultado legivel (sem package-lock.json ou sem internet?)"
    elif [ "$AUDIT_VULNS" -gt 0 ]; then
        RESULTADO_FINAL="FAIL"
        RELATORIO="$RELATORIO\n[NPM AUDIT] $AUDIT_VULNS vulnerabilidade(s) critica(s)/alta(s)"
        echo "  FAIL — $AUDIT_VULNS vulnerabilidade(s) critica/alta"
    else
        echo "  PASS — nenhuma vulnerabilidade critica/alta"
    fi
fi

# ───────────────────────────────────────────────────────
# 3. DETECCAO DE SECRETS
# ───────────────────────────────────────────────────────

echo "[3/3] Deteccao de secrets (chaves, tokens, senhas)..."

GREP_ALVOS=(
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"
    --include="*.py" --include="*.env" --include="*.json"
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next
    --exclude="package-lock.json" --exclude="*.lock"
)
# Prefixos de token conhecidos (diferencia maiusculas: AKIA, ghp_, sk-).
PADRAO_TOKENS='(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})'
# Senha/segredo atribuido a texto entre aspas DUPLAS ou SIMPLES. A classe
# ["'] e escrita com a aspa simples de verdade: o antigo \x27 nao vira aspa
# dentro do grep -E, e password='...' passava sem ser visto (C-137).
PADRAO_SENHAS="(password|passwd|senha|secret_key|api_key)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}[\"']"

SECRETS_FOUND=$( {
    grep -rnE "${GREP_ALVOS[@]}" -- "$PADRAO_TOKENS" "$ALVO" 2>/dev/null || true
    grep -rniE "${GREP_ALVOS[@]}" -- "$PADRAO_SENHAS" "$ALVO" 2>/dev/null || true
} | sort -u)

if [ -n "$SECRETS_FOUND" ]; then
    SECRET_COUNT=$(printf '%s\n' "$SECRETS_FOUND" | wc -l | tr -d ' ')
    RESULTADO_FINAL="FAIL"
    RELATORIO="$RELATORIO\n[SECRETS] $SECRET_COUNT possivel(is) secret(s) exposto(s):"
    RELATORIO="$RELATORIO\n$(printf '%s\n' "$SECRETS_FOUND" | head -10 | sed 's/^/  - /')"
    echo "  FAIL — $SECRET_COUNT possivel(is) secret(s)"
else
    echo "  PASS — nenhum secret detectado"
fi

# ───────────────────────────────────────────────────────
# RELATORIO FINAL
# ───────────────────────────────────────────────────────

if [ "$RESULTADO_FINAL" = "PASS" ] && [ "$INCOMPLETO" = true ]; then
    RESULTADO_FINAL="INCOMPLETO"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  RESULTADO: $RESULTADO_FINAL"
if [ "$INCOMPLETO" = true ]; then
    echo "  ATENCAO: pelo menos uma checagem NAO rodou — o resultado nao garante seguranca."
fi
echo "═══════════════════════════════════════════════════"

if [ -n "$RELATORIO" ]; then
    echo -e "$RELATORIO"
fi

echo ""
case "$RESULTADO_FINAL" in
    PASS) exit 0 ;;
    INCOMPLETO) exit 2 ;;
    *) exit 1 ;;
esac
