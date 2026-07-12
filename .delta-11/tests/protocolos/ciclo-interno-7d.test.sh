#!/usr/bin/env bash
# Teste do protocolo ciclo-interno-7d.md (Etapa 8A do v6.0)

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC="$SCRIPT_DIR/../../protocolos/ciclo-interno-7d.md"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC}   $1"; falhou=$((falhou + 1)); }

if [ -f "$DOC" ]; then
    ok "protocolo existe em .delta-11/protocolos/ciclo-interno-7d.md"
else
    err "protocolo AUSENTE em $DOC"
    echo ""
    echo "Teste de regressao do protocolo do Ciclo Interno de 7 sub-etapas."
    echo "A Metodologia Genesis exige que cada fase siga as 7 sub-etapas."
    echo "Sem protocolo, cada agente subverte a ordem."
    exit 1
fi

# As 7 sub-etapas declaradas explicitamente
sub_etapas=(
    "planejamento"
    "delegação|delegacao"
    "execução paralela|execucao paralela"
    "comunicação|comunicacao"
    "revisão cruzada|revisao cruzada"
    "teste adversarial"
    "selagem"
)
for sub in "${sub_etapas[@]}"; do
    if grep -qiE "$sub" "$DOC"; then
        ok "protocolo menciona sub-etapa '$sub'"
    else
        err "protocolo NAO menciona sub-etapa '$sub'"
    fi
done

# Cross-reference com Metodologia
if grep -qiE "metodologia-genesis|Dia 1|7 sub-etapas" "$DOC"; then
    ok "cross-reference com Metodologia Genesis"
else
    err "NAO cross-reference com Metodologia"
fi

# Cita o principio de Selagem
if grep -qiE "selo|criterio|critério" "$DOC"; then
    ok "menciona criterio/selo"
else
    err "NAO menciona criterio/selo"
fi

# Declara que e replicavel por fase
if grep -qiE "replic[aá]vel|cada fase|por fase|replica" "$DOC"; then
    ok "declara que e replicavel por fase"
else
    err "NAO declara replicabilidade"
fi

# Cross-reference com templates
if grep -qiE "ciclo-interno-template|template.md" "$DOC"; then
    ok "cross-reference com template"
else
    err "sem cross-reference com template"
fi

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — protocolo ciclo-interno-7d.md${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }