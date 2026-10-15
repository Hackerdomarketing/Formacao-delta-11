#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# ENGINE — Testes de API via curl (v6.3 — 2026-10-14)
# ═══════════════════════════════════════════════════════════════
#
# Testa rotas da API com curl e verifica:
#   1. Status code esperado
#   2. Tempo de resposta (limite de 5 s por chamada)
#   3. D13: erro de validacao = 400 com { "error": { "code": "VALIDATION_ERROR", ... } }
#
# Uso:
#   bash .delta-11/ferramentas/engine-test-api.sh [base_url] [--incluir-escrita]
#   bash .delta-11/ferramentas/engine-test-api.sh http://localhost:3000
#
# Se nao passar URL, usa http://localhost:3000
#
# De onde vem as rotas: memoria/project-core/contratos.md (fatia — D6) ou,
# se ela nao existir, memoria/project-core.md — sempre na PASTA PRINCIPAL do
# projeto (D25). Cada rota passa por um filtro estrito: so letras, numeros e
# / _ . - : { } [ ]. Rota com qualquer outro caractere (; $ ` espaco...) e
# IGNORADA com aviso. O curl e montado como lista de argumentos — sem eval
# (C-135): nada que vem do arquivo vira comando.
#
# Seguranca dos dados:
#   - GET: espera 200; 401/403 tambem passam (rota protegida por login).
#     Rota com parametro (:id, [id], {id}) aceita tambem 400 e 404.
#   - POST/PUT/PATCH so rodam com --incluir-escrita, com corpo vazio {}:
#     esperam 400 (D13) ou 401/403. Sem a opcao: PULADOS (nada e gravado).
#   - DELETE nunca e chamado por esta ferramenta.
#
# Saida (convencao das ferramentas v6.3): 0 = PASS; 1 = FAIL (ou servidor fora do ar).
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

BASE_URL="http://localhost:3000"
INCLUIR_ESCRITA=false
for arg in "$@"; do
    case "$arg" in
        --incluir-escrita) INCLUIR_ESCRITA=true ;;
        http://*|https://*) BASE_URL="${arg%/}" ;;
        *)
            echo "ERRO: argumento desconhecido '$arg'."
            echo "Uso: engine-test-api.sh [http://host:porta] [--incluir-escrita]"
            exit 1
            ;;
    esac
done

RESULTADO_FINAL="PASS"
RELATORIO=""
TESTES_TOTAL=0
TESTES_OK=0
TESTES_FAIL=0
TESTES_PULADOS=0
LIMITE_SEGUNDOS=5

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

# Arquivo temporario em .delta-11/scratch/ (D21 — nada em /tmp). Fora de um
# projeto Delta-11 (sem .delta-11/) usa a pasta temporaria do sistema.
if [ -d "$(find_main_folder)/.delta-11" ]; then
    SCRATCH_DIR="$(find_main_folder)/.delta-11/scratch"
    mkdir -p "$SCRATCH_DIR"
    RESPOSTA_TEMP=$(mktemp "$SCRATCH_DIR/engine-test-api-XXXXXX")
else
    RESPOSTA_TEMP=$(mktemp)
fi
trap 'rm -f "$RESPOSTA_TEMP"' EXIT

echo "═══════════════════════════════════════════════════"
echo "  ENGINE TEST API"
echo "  Base URL: $BASE_URL"
echo "═══════════════════════════════════════════════════"
echo ""

# ───────────────────────────────────────────────────────
# FUNCOES
# ───────────────────────────────────────────────────────

registrar_falha() {
    TESTES_FAIL=$((TESTES_FAIL + 1))
    RESULTADO_FINAL="FAIL"
    RELATORIO="$RELATORIO\n  $1"
    echo "  FAIL  $1"
}

# testar_rota <metodo> <rota> <status aceitos separados por espaco> [corpo]
testar_rota() {
    local metodo="$1"
    local rota="$2"
    local status_aceitos="$3"
    local corpo="${4:-}"

    TESTES_TOTAL=$((TESTES_TOTAL + 1))

    local curl_args=(-s -o "$RESPOSTA_TEMP" -w '%{http_code}|%{time_total}' --max-time "$LIMITE_SEGUNDOS" -X "$metodo")
    if [ -n "$corpo" ]; then
        curl_args+=(-H 'Content-Type: application/json' --data "$corpo")
    fi

    local resultado
    resultado=$(curl "${curl_args[@]}" "${BASE_URL}${rota}" 2>/dev/null || true)
    local status_code="${resultado%%|*}"
    local tempo="${resultado#*|}"
    [ -n "$status_code" ] || status_code="000"

    if [ "$status_code" = "000" ]; then
        registrar_falha "$metodo $rota → sem resposta em ${LIMITE_SEGUNDOS}s"
        return
    fi

    case " $status_aceitos " in
        *" $status_code "*)
            TESTES_OK=$((TESTES_OK + 1))
            echo "  PASS  $metodo $rota → $status_code (${tempo}s)"
            ;;
        *)
            registrar_falha "$metodo $rota → $status_code (esperado: $status_aceitos)"
            return
            ;;
    esac

    # D13: um 400 de validacao precisa vir no formato unico.
    if [ "$status_code" = "400" ] && ! grep -q '"VALIDATION_ERROR"' "$RESPOSTA_TEMP" 2>/dev/null; then
        registrar_falha "$metodo $rota → 400 fora do formato D13 (esperado { \"error\": { \"code\": \"VALIDATION_ERROR\", \"message\", \"details\" } })"
    fi
}

pular_rota() {
    TESTES_PULADOS=$((TESTES_PULADOS + 1))
    echo "  PULADO $1"
}

# ───────────────────────────────────────────────────────
# VERIFICAR SE SERVIDOR ESTA RODANDO
# ───────────────────────────────────────────────────────

echo "[0] Verificando se o servidor esta acessivel..."

HEALTH_CHECK=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$BASE_URL" 2>/dev/null || true)
[ -n "$HEALTH_CHECK" ] || HEALTH_CHECK="000"

if [ "$HEALTH_CHECK" = "000" ]; then
    echo ""
    echo "  FAIL — Servidor nao esta acessivel em $BASE_URL"
    echo "  Verifique se o servidor esta rodando (npm run dev, etc.)"
    echo ""
    exit 1
fi

echo "  OK — Servidor acessivel (status $HEALTH_CHECK)"
echo ""

# ───────────────────────────────────────────────────────
# TESTES BASICOS (sempre rodam)
# ───────────────────────────────────────────────────────

echo "[1] Testes basicos..."

# Pagina principal deve responder (redirecionamento para login tambem vale)
testar_rota "GET" "/" "200 301 302 307 308"

# Rotas de API que nao existem devem retornar 404
testar_rota "GET" "/api/rota-que-nao-existe-$(date +%s)" "404"

# ───────────────────────────────────────────────────────
# TESTES DINAMICOS (contratos do project-core)
# ───────────────────────────────────────────────────────

echo ""
echo "[2] Testes de rotas do projeto..."

MEMORIA_DIR="$(find_main_folder)/.delta-11/memoria"
FONTE_CONTRATOS=""
for candidato in "$MEMORIA_DIR/project-core/contratos.md" "$MEMORIA_DIR/project-core.md"; do
    if [ -f "$candidato" ]; then
        FONTE_CONTRATOS="$candidato"
        break
    fi
done

ROTA_VALIDA='^/api(/[][A-Za-z0-9_.:{}-]*)*$'

if [ -n "$FONTE_CONTRATOS" ]; then
    echo "  Fonte: ${FONTE_CONTRATOS#"$MEMORIA_DIR"/}"
    ROTAS=$(grep -oE '(GET|POST|PUT|DELETE|PATCH)[[:space:]]+/api/[^[:space:]`|)]+' "$FONTE_CONTRATOS" 2>/dev/null | sort -u || true)

    if [ -n "$ROTAS" ]; then
        while read -r metodo rota; do
            [ -n "$metodo" ] || continue
            if ! [[ "$rota" =~ $ROTA_VALIDA ]]; then
                pular_rota "$metodo $rota — IGNORADA: caractere fora do padrao de rota (possivel texto malicioso)"
                continue
            fi
            tem_parametro=false
            if [[ "$rota" == *":"* || "$rota" == *"{"* || "$rota" == *"["* ]]; then
                tem_parametro=true
            fi

            case "$metodo" in
                GET)
                    if [ "$tem_parametro" = true ]; then
                        testar_rota "GET" "$rota" "200 400 401 403 404"
                    else
                        testar_rota "GET" "$rota" "200 401 403"
                    fi
                    ;;
                POST|PUT|PATCH)
                    if [ "$INCLUIR_ESCRITA" = true ]; then
                        testar_rota "$metodo" "$rota" "400 401 403" "{}"
                    else
                        pular_rota "$metodo $rota — escrita so com --incluir-escrita (nada foi gravado)"
                    fi
                    ;;
                DELETE)
                    pular_rota "DELETE $rota — DELETE nunca e chamado automaticamente"
                    ;;
            esac
        done <<< "$ROTAS"
    else
        echo "  Nenhuma rota encontrada em ${FONTE_CONTRATOS#"$MEMORIA_DIR"/}"
    fi
else
    echo "  AVISO — contratos nao encontrados (memoria/project-core/contratos.md ou memoria/project-core.md)"
fi

# ───────────────────────────────────────────────────────
# RELATORIO FINAL
# ───────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════"
echo "  RESULTADO: $RESULTADO_FINAL"
echo "  Total: $TESTES_TOTAL | OK: $TESTES_OK | FAIL: $TESTES_FAIL | Pulados: $TESTES_PULADOS"
echo "═══════════════════════════════════════════════════"

if [ -n "$RELATORIO" ]; then
    echo -e "$RELATORIO"
fi

echo ""
if [ "$RESULTADO_FINAL" = "PASS" ]; then
    exit 0
fi
exit 1
