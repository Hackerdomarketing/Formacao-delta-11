#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da Metodologia Gênesis como base canônica (Etapa 1 do v6.0)
# ════════════════════════════════════════════════════════════════
#
# Verifica que a base da Metodologia Gênesis existe em
# .delta-11/conhecimento/metodologia-genesis-camadas.md e tem:
#   1. Caminho canônico (pasta conhecimento/, nome correto)
#   2. 3 Princípios Fundamentais (Ordem, Selagem, Contraposição)
#   3. 7 Dias (Luz, Container, Superfícies, Astros, Habitantes, Consciência, Descanso)
#   4. 7 Tipos de Contraposição Lateral (um por dia)
#   5. Critérios objetivos de selo (mencionados por dia)
#   6. As 7 sub-etapas do Ciclo Interno
#   7. Os 4 Sinais de "Fazendo Certo"
#   8. Texto hebraico chave de pelo menos 1 dia (referência)
#   9. Cross-reference com a skills-globais-v5-4.md
#  10. Cross-reference com o relatório de auditoria 2026-07-10
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/conhecimento/ → sobe 3 níveis: tests/ → .delta-11/ → raiz do repo
DOC="$SCRIPT_DIR/../../conhecimento/metodologia-genesis-camadas.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

# 1. Caminho canônico
if [ -f "$DOC" ]; then
    ok "existe em .delta-11/conhecimento/metodologia-genesis-camadas.md"
else
    err "ARQUIVO AUSENTE em $DOC"
    echo ""
    echo "Este teste é o guarda de regressão da Etapa 1 do v6.0."
    echo "Se a base da Metodologia Gênesis sumir, o sistema inteiro perde"
    echo "sua referência canônica. O teste falhará até que o arquivo seja criado."
    exit 1
fi

# 2. 3 Princípios Fundamentais
for principio in "Ordem" "Selagem" "Contraposição"; do
    if grep -qi "$principio" "$DOC"; then
        ok "menciona princípio $principio"
    else
        err "NAO menciona princípio $principio"
    fi
done

# 3. 7 Dias (nomes canônicos)
for dia in "Luz" "Container" "Superfícies" "Astros" "Habitantes" "Consciência" "Descanso"; do
    if grep -q "$dia" "$DOC"; then
        ok "menciona Dia $dia"
    else
        err "NAO menciona Dia $dia"
    fi
done

# 4. Os 7 tipos de contraposição lateral
# Tipo 1: existencial-identitária (Dia 1)
# Tipo 2: estrutural tripla (Dia 2)
# Tipo 3: substância + estrutural-reprodutiva (Dia 3)
# Tipo 4: funcional-temporal + hierárquica (Dia 4)
# Tipo 5: territorial + escalar (Dia 5)
# Tipo 6: complementar + hierárquica (Dia 6)
# Tipo 7: estado (Dia 7)
for tipo in \
    "existencial" \
    "estrutural tripla" \
    "substância" \
    "funcional-temporal" \
    "territorial" \
    "complementar" \
    "estado"; do
    if grep -qi "$tipo" "$DOC"; then
        ok "menciona tipo de contraposição '$tipo'"
    else
        err "NAO menciona tipo de contraposição '$tipo'"
    fi
done

# 5. Critérios objetivos de selo (palavra-chave por dia)
# Pelo menos UMA menção por dia a "selo" ou "critério"
# Range de 25 linhas após o cabeçalho do Dia cobre seções inteiras
for dia in "Dia 1" "Dia 2" "Dia 3" "Dia 4" "Dia 5" "Dia 6" "Dia 7"; do
    if grep -q "$dia" "$DOC"; then
        # busca selos perto do dia (mesma linha ou 25 linhas depois — cobre seções inteiras)
        if grep -A25 "^### $dia " "$DOC" | grep -qi "selo\|critério"; then
            ok "$dia menciona critério/selo"
        else
            err "$dia NAO menciona critério/selo (verificar se seção de critérios objetivos de selo está dentro do Dia)"
        fi
    else
        err "$dia AUSENTE do documento"
    fi
done

# 6. As 7 sub-etapas do Ciclo Interno
for sub in "planejamento" "delegação" "execução paralela" "comunicação" "revisão cruzada" "teste adversarial" "selagem"; do
    if grep -qi "$sub" "$DOC"; then
        ok "menciona sub-etapa '$sub'"
    else
        err "NAO menciona sub-etapa '$sub'"
    fi
done

# 7. Os 4 Sinais de "Fazendo Certo"
# Sinal 1: energia para consagrar diminui
# Sinal 2: novos membros entendem sem o criador
# Sinal 3: bug no dia N é resolvido no dia N
# Sinal 4: tirar 2 semanas de férias e o sistema continua
if grep -qi "sinal\|sinais de" "$DOC"; then
    ok "menciona Sinais de 'Fazendo Certo'"
else
    err "NAO menciona Sinais de 'Fazendo Certo'"
fi

# 8. Texto hebraico chave (mínimo 1 dia, preferencialmente Dia 1 = yehi or)
if grep -q "yehi\|vayavdel\|badal\|shabat\|kalá\|yom\|shamayim" "$DOC"; then
    ok "inclui texto hebraico chave (referência Massorética)"
else
    err "NAO inclui texto hebraico chave — perde fidelidade à fonte"
fi

# 9. Cross-reference com skills-globais-v5-4.md (o sistema ja reconhece skills globais)
if grep -q "skills-globais-v5-4\|skill global\|owasp-top10\|supabase-rls\|react-next" "$DOC"; then
    ok "cross-reference com skills globais v5.4"
else
    err "NAO cross-reference com skills globais — fica órfão do v5.4"
fi

# 10. Cross-reference com o relatório de auditoria
if grep -q "auditoria-delta-11-vs-metodologia-genesis\|2026-07-10-auditoria" "$DOC"; then
    ok "cross-reference com relatório de auditoria 2026-07-10"
else
    err "NAO cross-reference com auditoria — perde rastreabilidade"
fi

# Resumo
echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — base da Metodologia Gênesis conforme esperado${NC}"
    exit 0
else
    echo -e "${RED}FALTA $falhou item(ns) — corrigir antes de prosseguir para Etapa 2${NC}"
    exit 1
fi