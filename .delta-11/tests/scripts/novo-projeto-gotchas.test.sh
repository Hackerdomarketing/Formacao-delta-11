#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do novo-projeto.sh (v5.4 F5 + v6.3 C-048, C-049, C-053, C-147, D1, D38)
# ════════════════════════════════════════════════════════════════
#
# Roda o novo-projeto.sh com HOME e registro TEMPORÁRIOS (nunca toca no
# ~/.delta-11-registry.json real — C-129) e confere que o projeto novo:
#   1. tem memoria/gotchas.md no formato do modelo (F5)
#   2. NÃO herda lixo de execução da fonte (activity-log, monitor-status,
#      ativacoes, locks, logs, scratch, memórias de agente, planos) — C-048
#   3. tem kanban e project-core iguais aos modelos (zerados) — C-048
#   4. tem .claude/settings.json igual ao modelo
#   5. tem os scripts de operação em .delta-11/scripts/ e nada na raiz — C-053
#   6. tem .gitignore protegendo .env, chaves e o estado de execução — C-147
#   7. está no registro central (temporário) — C-049
#   8. criou a memória entre projetos (D38) e o .modo-selo "automatico" (D1)
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
NOVO_PROJETO="$REPO_ROOT/novo-projeto.sh"

if [ ! -f "$NOVO_PROJETO" ]; then
    if [ ! -f "$REPO_ROOT/sincronizar.sh" ]; then
        echo -e "${GREEN}[SKIP]${NC} novo-projeto.sh só existe na distribuição oficial (isto é um projeto)"
        exit 0
    fi
    echo -e "${RED}[FAIL]${NC} novo-projeto.sh nao encontrado: $NOVO_PROJETO"
    exit 1
fi

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/delta11-novo-projeto-test-XXXXXX")"
cleanup() { [ -n "$SANDBOX" ] && [ -d "$SANDBOX" ] && rm -rf "$SANDBOX"; }
trap cleanup EXIT

# Fonte falsa = cópia da distribuição + "lixo" de execução plantado
FONTE="$SANDBOX/fonte"
mkdir -p "$FONTE"
(cd "$REPO_ROOT" && tar --exclude='./.git' --exclude='./.delta-11/bg-delta11.png' -cf - .) | (cd "$FONTE" && tar -xf -)
mkdir -p "$FONTE/.delta-11/ativacoes" "$FONTE/.delta-11/locks/src--x.ts.lock" "$FONTE/.delta-11/planos" "$FONTE/.delta-11/logs/sub-agentes"
echo "- [2026-01-01T00:00:00Z] [x] [ATLAS] lixo" > "$FONTE/.delta-11/activity-log.md"
MARCA_VAZAMENTO="cliente-secreto-$$-$RANDOM"
echo "{\"projetos\":[\"/Users/outra-pessoa/$MARCA_VAZAMENTO\"]}" > "$FONTE/.delta-11/monitor-status.json"
echo "ack" > "$FONTE/.delta-11/ativacoes/ack-ENGINE.txt"
echo "produto de outro projeto" > "$FONTE/.delta-11/memoria/ENGINE-produto.md"
echo "historia de outro projeto" > "$FONTE/.delta-11/memoria/ENGINE-historia.md"
echo "estado antigo" > "$FONTE/.delta-11/memoria/ENGINE-estado.md"
echo "plano velho" > "$FONTE/.delta-11/planos/ENGINE-plan.md"
echo "log" > "$FONTE/.delta-11/logs/sub-agentes/20260101T000000Z-x.log"
echo "rascunho" > "$FONTE/.delta-11/scratch/rascunho.txt"

export HOME="$SANDBOX/home"
mkdir -p "$HOME"
export DELTA11_REGISTRY="$HOME/registro-teste.json"
TARGET="$SANDBOX/meu-projeto"

# Responder "n" para o VS Code
echo "n" | bash "$FONTE/novo-projeto.sh" "$TARGET" >/dev/null 2>&1

D="$TARGET/.delta-11"
falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FAIL]${NC} $1"; falhou=$((falhou + 1)); }

# 1. gotchas.md
GOTCHAS="$D/memoria/gotchas.md"
if [ -f "$GOTCHAS" ] && grep -q "^## G-001:" "$GOTCHAS" && grep -q "^# Gotchas do Projeto" "$GOTCHAS" && grep -q "Zona:" "$GOTCHAS"; then
    ok "gotchas.md criado com o formato do modelo (F5)"
else
    err "gotchas.md ausente ou fora do formato"
fi

# 2. Nenhum lixo de execução
for lixo in activity-log.md monitor-status.json ativacoes/ack-ENGINE.txt locks/src--x.ts.lock \
            memoria/ENGINE-produto.md memoria/ENGINE-historia.md memoria/ENGINE-estado.md \
            planos logs/sub-agentes/20260101T000000Z-x.log scratch/rascunho.txt; do
    if [ -e "$D/$lixo" ]; then
        err "herdou lixo de execução da fonte: .delta-11/$lixo"
    fi
done
grep -rq "$MARCA_VAZAMENTO" "$D" 2>/dev/null && err "dados de outro projeto vazaram para o projeto novo"
[ "$falhou" -eq 0 ] && ok "nenhum lixo de execução herdado (C-048)"

# 3. Modelos zerados
cmp -s "$D/kanban.md" "$REPO_ROOT/.delta-11/kanban.md" && ok "kanban.md = modelo" || err "kanban.md diferente do modelo"
cmp -s "$D/memoria/project-core.md" "$REPO_ROOT/.delta-11/memoria/project-core.md" && ok "project-core.md = modelo" || err "project-core.md diferente do modelo"
[ -f "$D/kanban-data.js" ] && ok "kanban-data.js presente" || err "kanban-data.js ausente"

# 4. settings.json
cmp -s "$TARGET/.claude/settings.json" "$REPO_ROOT/.delta-11/templates/settings-hooks.json" \
    && ok ".claude/settings.json criado do modelo" || err ".claude/settings.json ausente ou diferente do modelo"

# 5. Scripts em .delta-11/scripts/
for s in task-done.sh monitor-delta11.sh vigilante.sh; do
    [ -x "$D/scripts/$s" ] || err "$s ausente (ou sem permissão de execução) em .delta-11/scripts/"
    [ -e "$TARGET/$s" ] && err "$s apareceu na raiz do projeto"
done
[ -e "$D/scripts/disparar.sh" ] && err "disparar.sh foi copiado (removido na v6.1)"
[ -e "$D/scripts/com.delta11.monitor.plist" ] && err "plist foi copiado para o projeto"
ok "scripts de operação conferidos em .delta-11/scripts/ (C-053)"

# 6. .gitignore
for linha in ".env" ".env.*" "!.env.example" "*.pem" "*.key" "credentials.json" ".claude/settings.local.json" ".delta-11/ativacoes/" ".delta-11/activity-log.md"; do
    grep -Fxq -- "$linha" "$TARGET/.gitignore" 2>/dev/null || err ".gitignore não protege: $linha"
done
ok ".gitignore conferido (C-147)"

# 7. Registro (temporário)
if command -v jq >/dev/null 2>&1; then
    REAL_TARGET="$(cd "$TARGET" && pwd -P)"
    jq -e --arg p "$REAL_TARGET" '.projects | index($p)' "$DELTA11_REGISTRY" >/dev/null 2>&1 \
        && ok "projeto anotado no registro central (C-049)" || err "projeto NÃO entrou no registro central"
else
    grep -q "meu-projeto" "$DELTA11_REGISTRY" && ok "projeto anotado no registro central (C-049)" || err "projeto NÃO entrou no registro central"
fi

# 8. D38 + D1
[ -f "$HOME/.delta-11/aprendizados-entre-projetos.md" ] && ok "memória entre projetos criada (D38)" || err "aprendizados-entre-projetos.md não foi criado"
[ "$(cat "$D/.modo-selo" 2>/dev/null)" = "automatico" ] && ok ".modo-selo = automatico (D1)" || err ".modo-selo não é 'automatico'"

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} novo-projeto.sh: projeto limpo, protegido e registrado"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi
