#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da Metodologia Gênesis como base canônica (Etapa 1 do v6.0, revisto na v6.3)
# ════════════════════════════════════════════════════════════════
# Conceitos conferidos em .delta-11/conhecimento/metodologia-genesis-camadas.md:
#   1. O arquivo existe.
#   2. Os 3 Princípios (Ordem, Selagem, Contraposição).
#   3. Os 7 Dias (Luz, Container, Superfícies, Astros, Habitantes,
#      Consciência, Descanso) — cada um com seção própria "Dia N" que fala
#      de critério/selo (a seção inteira, até o próximo título).
#   4. Os 7 tipos de contraposição lateral.
#   5. As 7 sub-etapas do Ciclo Interno.
#   6. Os 4 Sinais de "Fazendo Certo".
#   7. Texto hebraico; skills globais; relatório de auditoria.
# (O mapa Dia → Fase e as "13 fases" ficam em protocolos/fluxo-13-fases-d16.test.sh.)
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

DOC="$DELTA_DIR/conhecimento/metodologia-genesis-camadas.md"
if ! require_file "$DOC" ".delta-11/conhecimento/metodologia-genesis-camadas.md"; then
    echo "  Sem esta base o sistema perde sua referência canônica."
    finish_test "base da Metodologia Gênesis"
fi
pass "existe em .delta-11/conhecimento/metodologia-genesis-camadas.md"

for principio in "Ordem" "Selagem" "Contraposi(ção|cao)"; do
    expect_match "$DOC" "$principio" "princípio '$principio'"
done

DIAS=("Luz" "Container" "Superf(í|i)cies" "Astros" "Habitantes" "Consci(ê|e)ncia" "Descanso")
for numero in 1 2 3 4 5 6 7; do
    nome="${DIAS[$((numero - 1))]}"
    secao=$(markdown_section "$DOC" "^#{2,4} Dia $numero([^0-9]|$)")
    if [ -z "$secao" ]; then
        fail "Dia $numero ($nome) sem seção própria"
        continue
    fi
    if grep -qiE "$nome" <<< "$secao"; then
        pass "Dia $numero = $nome"
    else
        fail "Dia $numero não fala de '$nome'"
    fi
    if grep -qiE "selo|crit(é|e)rio" <<< "$secao"; then
        pass "Dia $numero tem critério de selo"
    else
        fail "Dia $numero sem critério de selo na própria seção"
    fi
done

for tipo in "existencial" "estrutural tripla" "subst(â|a)ncia" "funcional-temporal" "territorial" "complementar" "estado"; do
    expect_match "$DOC" "$tipo" "tipo de contraposição '$tipo'"
done

for sub in "planejamento" "delega(ção|cao)" "execu(ção|cao) paralela" "comunica(ção|cao)" "revis(ão|ao) cruzada" "teste adversarial" "selagem"; do
    expect_match "$DOC" "$sub" "sub-etapa '$sub'"
done

expect_match "$DOC" "sinais? de" "os Sinais de 'Fazendo Certo'"
expect_match "$DOC" "yehi|vayavdel|badal|shabat|kal(á|a)|yom|shamayim" "texto hebraico chave"
expect_match "$DOC" "skills-globais-v5-4|skill global|owasp-top10|supabase-rls|react-next" "liga com as skills globais"
expect_match "$DOC" "auditoria-delta-11-vs-metodologia-genesis|2026-07-10-auditoria" "liga com o relatório de auditoria 2026-07-10"

finish_test "base da Metodologia Gênesis"
