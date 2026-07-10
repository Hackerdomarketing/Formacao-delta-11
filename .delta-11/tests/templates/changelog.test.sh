#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do CHANGELOG.md (E3 — documentação do sistema)
# ════════════════════════════════════════════════════════════════
#
# Verifica que o CHANGELOG:
#   1. Existe em .delta-11/CHANGELOG.md (caminho canonico)
#   2. Tem seção v5.4 (versao atual) com Estagios 0-3 mencionados
#   3. Tem secao v5.3 (Onda 4 + Bloco A)
#   4. Tem secao v5.2 (Ciclo de Zoneamento Documental)
#   5. Tem secao de versões anteriores (v5.1, v5, v4.0.4, v4.0)
#   6. Tem secao ADICOES POSTERIORES para correções imutáveis
#   7. Tem bloco "Como testar" executavel (comando bash)
#   8. Tem seção "Por que existe" para cada versão principal
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHANGELOG="$SCRIPT_DIR/../../CHANGELOG.md"

if [ ! -f "$CHANGELOG" ]; then
    echo -e "${RED}[FAIL]${NC} CHANGELOG.md nao encontrado em $CHANGELOG"
    exit 1
fi

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. Caminho canonico
ok "existe em .delta-11/CHANGELOG.md"

# 2. v5.4 com Estagios 0-3
if grep -q "^## v5\.4" "$CHANGELOG"; then
    ok "secao v5.4 presente"
    for est in "Estágio 0" "Estágio 1" "Estágio 2" "Estágio 3"; do
        if grep -q "$est" "$CHANGELOG"; then
            ok "v5.4 menciona $est"
        else
            err "v5.4 NAO menciona $est"
        fi
    done
else
    err "secao v5.4 AUSENTE"
fi

# 3. v5.3
if grep -q "^## v5\.3" "$CHANGELOG"; then
    ok "secao v5.3 presente"
    grep -q "Onda 4" "$CHANGELOG" && ok "v5.3 menciona Onda 4" || err "v5.3 sem Onda 4"
    grep -q "Bloco A da auditoria" "$CHANGELOG" && ok "v5.3 menciona Bloco A" || err "v5.3 sem Bloco A"
else
    err "secao v5.3 AUSENTE"
fi

# 4. v5.2
if grep -q "^## v5\.2" "$CHANGELOG"; then
    ok "secao v5.2 presente"
    grep -q "Zoneamento Documental" "$CHANGELOG" && ok "v5.2 menciona Zoneamento Documental" || err "v5.2 sem Zoneamento Documental"
else
    err "secao v5.2 AUSENTE"
fi

# 5. Versoes anteriores
for ver in "v5\.1" "v5\.0" "v4\.0\.4" "v4\.0"; do
    if grep -qE "^##[[:space:]]+${ver}" "$CHANGELOG"; then
        ok "secao $ver presente (resumo)"
    else
        err "secao $ver AUSENTE"
    fi
done

# 6. ADICOES POSTERIORES
if grep -q "^## ADIÇÕES POSTERIORES\|^## ADICOES POSTERIORES" "$CHANGELOG"; then
    ok "secao 'ADICOES POSTERIORES' presente (regra de imutabilidade)"
else
    err "secao 'ADICOES POSTERIORES' AUSENTE (regra de imutabilidade quebrada)"
fi

# 7. Bloco Como testar (deve ter pelo menos um bloco bash)
if grep -qE '^[[:space:]]*\`\`\`bash' "$CHANGELOG"; then
    ok "pelo menos um bloco de codigo bash (Como testar)"
else
    err "nenhum bloco bash presente (Como testar inexecutavel)"
fi

# 8. Secao Por que existe em v5.4 e v5.2 (mudancas principais)
for ver in "v5\.4" "v5\.2"; do
    # Pegar do heading ate o proximo ## ou fim
    if awk -v v="$ver" 'BEGIN{p=0} $0 ~ "^## "v{p=1; next} p && /^## /{p=0} p' "$CHANGELOG" | grep -qi "por que essa versão existe\|por que essa mudança existe"; then
        ok "v$ver tem secao 'Por que existe'"
    else
        err "v$ver sem secao 'Por que existe'"
    fi
done

# Bonus: cada secao principal tem "Como testar"
for ver in "v5\.4" "v5\.3" "v5\.2"; do
    if awk -v v="$ver" 'BEGIN{p=0} $0 ~ "^## "v{p=1; next} p && /^## /{p=0} p' "$CHANGELOG" | grep -qi "como testar"; then
        ok "v$ver tem bloco 'Como testar'"
    else
        err "v$ver sem bloco 'Como testar'"
    fi
done

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} CHANGELOG.md: v5.4 + v5.3 + v5.2 + anteriores + imutabilidade + Como testar"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi