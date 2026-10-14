#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do monitor-delta11.sh — Dia 7 / Fase 7 e status por projeto (v6.3)
# ════════════════════════════════════════════════════════════════
#
# C-129: este teste NUNCA toca no ~/.delta-11-registry.json real. Ele roda
# o monitor com HOME, registro (DELTA11_REGISTRY) e pastas de varredura
# (DELTA11_SEARCH_PATHS) temporários, e sem notificações.
#
# Cenários (Teste Supremo do Dia 7 = 2 semanas, THRESHOLD_DIAS=14):
#   A. Fase 7, 20 dias parado, sem FAZENDO      → operacao_autonoma = true
#   B. 20 dias parado mas com tarefa em FAZENDO → false + alerta de órfã (abandono, C-065)
#   C. 20 dias parado fora da Fase 7            → false (abandono)
#   D. atividade recente                        → false
#   E. morte-*.json é avisada e arquivada (não repete a cada 5 min — C-064)
#   F. cada projeto recebe SÓ o próprio status, também em monitor-data.js (C-149, D28)
#   H. com alerta pendente (morte/órfã/travado) nunca é operação autônoma
#   G. pasta inexistente no registro e cópia do sistema são ignoradas (C-065, C-057)
# ════════════════════════════════════════════════════════════════

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MONITOR="$RAIZ/monitor-delta11.sh"
[ -f "$MONITOR" ] || MONITOR="$RAIZ/.delta-11/scripts/monitor-delta11.sh"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

if [ ! -f "$MONITOR" ]; then
    echo -e "${RED}[FALTA]${NC} monitor-delta11.sh não encontrado"
    exit 1
fi

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/delta11-monitor-test-XXXXXX")"
cleanup() { [ -n "$SANDBOX" ] && [ -d "$SANDBOX" ] && rm -rf "$SANDBOX"; }
trap cleanup EXIT

export HOME="$SANDBOX/home"
export DELTA11_REGISTRY="$SANDBOX/registro.json"
export DELTA11_SEARCH_PATHS="$SANDBOX/busca"
export DELTA11_SEM_NOTIFICACAO=1
mkdir -p "$HOME" "$DELTA11_SEARCH_PATHS"

VINTE_DIAS="$(date -v-20d +%Y%m%d%H%M.%S 2>/dev/null || date -d '20 days ago' +%Y%m%d%H%M.%S)"

criar_projeto() {
    # criar_projeto <nome> <fase> <linha-em-FAZENDO-ou-vazio> <antigo:1|0>
    local p="$DELTA11_SEARCH_PATHS/$1"
    mkdir -p "$p/.delta-11/ativacoes" "$p/.delta-11/memoria"
    cat > "$p/.delta-11/kanban.md" <<EOF
# KANBAN
**Fase atual:** $2

## ⚡ FAZENDO

<!-- Formato: **[ID]** — [Descrição] | Agente: [NOME] | Início: [hora] -->
$3

---

## ✅ CONCLUÍDO
**T-001** — Tudo feito | Por: ENGINE
EOF
    echo "ok" > "$p/.delta-11/ativacoes/registro.txt"
    if [ "$4" = "1" ]; then
        find "$p/.delta-11" -type f -exec touch -t "$VINTE_DIAS" {} +
    fi
}

criar_projeto proj-a "Fase 7 — Dia 7 (operação)" "" 1
criar_projeto proj-b "Fase 7 — Dia 7 (operação)" "**T-009** — Tela X | Agente: PIXEL | Início: 2026-09-01T10:00:00-03:00" 1
criar_projeto proj-c "Fase 4 — Desenvolvimento" "" 1
criar_projeto proj-d "Fase 7 — Dia 7 (operação)" "" 0
criar_projeto proj-e "Fase 7 — Dia 7 (operação)" "" 1

# E. morte no projeto D
echo '{"agente":"ENGINE","morreu_em":"2026-10-14T10:00:00Z","motivo":"teste"}' > "$DELTA11_SEARCH_PATHS/proj-d/.delta-11/ativacoes/morte-ENGINE.json"

# H. Fase 7, 20 dias parado, sem FAZENDO, mas com morte registrada (alerta pendente)
echo '{"agente":"SHIELD","morreu_em":"2026-09-20T10:00:00Z","motivo":"teste"}' > "$DELTA11_SEARCH_PATHS/proj-e/.delta-11/ativacoes/morte-SHIELD.json"
touch -t "$VINTE_DIAS" "$DELTA11_SEARCH_PATHS/proj-e/.delta-11/ativacoes/morte-SHIELD.json"

# G. cópia do sistema na varredura + pasta inexistente no registro
mkdir -p "$DELTA11_SEARCH_PATHS/clone-do-sistema/.delta-11/ativacoes" "$DELTA11_SEARCH_PATHS/clone-do-sistema/boilerplate-delta-11-nextjs"
echo "{\"source\":\"$SANDBOX/fonte-inexistente\",\"projects\":[\"$SANDBOX/nao-existe\",\"$DELTA11_SEARCH_PATHS/proj-a\"]}" > "$DELTA11_REGISTRY"

SAIDA="$(bash "$MONITOR" 2>&1 || true)"

campo() { python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$1" "$2" 2>/dev/null || echo "ERRO"; }
ST() { echo "$DELTA11_SEARCH_PATHS/$1/.delta-11/monitor-status.json"; }

[ "$(campo "$(ST proj-a)" operacao_autonoma)" = "True" ] && ok "A: Fase 7 parada há 20 dias sem FAZENDO = operação autônoma" || err "A: deveria ser operação autônoma"
[ "$(campo "$(ST proj-a)" sinal)" = "OPERACAO_AUTONOMA_DETECTADA" ] && ok "A: sinal OPERACAO_AUTONOMA_DETECTADA presente" || err "A: sinal ausente"
[ "$(campo "$(ST proj-e)" operacao_autonoma)" = "False" ] && ok "H: com morte registrada (alerta pendente) NÃO é operação autônoma" || err "H: alerta pendente foi chamado de operação autônoma"
[ "$(campo "$(ST proj-e)" sinal)" = "None" ] && ok "H: sem sinal OPERACAO_AUTONOMA_DETECTADA" || err "H: sinal indevido"
[ "$(campo "$(ST proj-a)" dias_silencio)" -ge 14 ] 2>/dev/null && ok "A: dias_silencio ≥ 14" || err "A: dias_silencio errado"
[ "$(campo "$(ST proj-b)" operacao_autonoma)" = "False" ] && ok "B: com tarefa em FAZENDO NÃO é operação autônoma (abandono)" || err "B: tarefa aberta foi chamada de operação autônoma"
grep -q '"orfa"' "$(ST proj-b)" && ok "B: tarefa sem agente vira alerta de órfã" || err "B: faltou o alerta de órfã"
[ "$(campo "$(ST proj-b)" tarefas_fazendo)" = "1" ] && ok "B: tarefas_fazendo soma o quadro inteiro" || err "B: contagem de FAZENDO errada"
[ "$(campo "$(ST proj-c)" operacao_autonoma)" = "False" ] && ok "C: parado fora da Fase 7 NÃO é operação autônoma" || err "C: abandono fora da Fase 7 foi consagrado"
[ "$(campo "$(ST proj-d)" operacao_autonoma)" = "False" ] && ok "D: atividade recente NÃO é operação autônoma" || err "D: atividade recente marcada como autônoma"

# E. morte arquivada
if [ ! -f "$DELTA11_SEARCH_PATHS/proj-d/.delta-11/ativacoes/morte-ENGINE.json" ] && [ -f "$DELTA11_SEARCH_PATHS/proj-d/.delta-11/logs/mortes/morte-ENGINE.json" ]; then
    ok "E: morte avisada e arquivada em logs/mortes/"
else
    err "E: morte-ENGINE.json não foi arquivada (o aviso se repetiria para sempre)"
fi
grep -q "MORTE: ENGINE" <<< "$SAIDA" && ok "E: morte registrada no log do monitor" || err "E: morte não apareceu no log"
SAIDA2="$(bash "$MONITOR" 2>&1 || true)"
grep -q "MORTE:" <<< "$SAIDA2" && err "E: a mesma morte foi avisada de novo" || ok "E: a segunda rodada não repete o aviso"

# F. só o próprio projeto + monitor-data.js
if grep -q "proj-b" "$(ST proj-a)" || grep -q "$SANDBOX" "$(ST proj-a)"; then
    err "F: o status do proj-a contém dados/caminhos de outros projetos"
else
    ok "F: cada projeto recebe só o próprio status"
fi
DADOS_JS="$DELTA11_SEARCH_PATHS/proj-a/.delta-11/monitor-data.js"
if [ -f "$DADOS_JS" ] && grep -q "^window.D11_MONITOR = {" "$DADOS_JS"; then
    node -e "global.window={}; require('$DADOS_JS'); if(window.D11_MONITOR.projeto!=='proj-a') process.exit(1)" 2>/dev/null \
        && ok "F: monitor-data.js válido com window.D11_MONITOR do próprio projeto" \
        || { command -v node >/dev/null 2>&1 && err "F: monitor-data.js inválido" || ok "F: monitor-data.js gerado (node ausente: só formato conferido)"; }
else
    err "F: monitor-data.js não foi gerado"
fi

# G. ignorados
[ -e "$DELTA11_SEARCH_PATHS/clone-do-sistema/.delta-11/monitor-status.json" ] && err "G: a cópia do sistema foi tratada como projeto" || ok "G: cópia do sistema ignorada"
grep -q "Verificados 5 projetos" <<< "$SAIDA" && ok "G: pasta inexistente do registro ignorada (5 projetos reais)" || err "G: contagem de projetos errada: $(head -1 <<< "$SAIDA")"

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — monitor-delta11.sh: Dia 7, status por projeto e mortes sem repetição${NC}"; exit 0; } \
  || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }
