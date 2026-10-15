#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do task-done.sh e do vigilante.sh (v6.3 — C-053, C-066, C-067, D9, D10, D25)
# ════════════════════════════════════════════════════════════════
#
# Monta um projeto git temporário com uma worktree (como a de um executor)
# e confere:
#   task-done.sh (chamado de .delta-11/scripts/ DENTRO da worktree):
#     1. grava golden-path.log e activity-log na pasta PRINCIPAL (D25)
#     2. NÃO cria arquivo .txt de revisão em ativacoes/ (D9, C-067)
#     3. NÃO mexe no kanban (D10)
#     4. mostra o checklist 1a → 3.9 com o SendMessage ao CRONOS
#     5. usa -produto.md (nunca -estado.md)
#   vigilante.sh --once (chamado de .delta-11/scripts/):
#     6. não chama disparar.sh (C-066)
#     7. tarefa em FAZENDO sem ACK → aviso para o CRONOS + linha no activity-log
#     8. nada em /tmp (PID na pasta scratch — D21)
# ════════════════════════════════════════════════════════════════

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$SCRIPT_DIR/../../.." && pwd)"
achar() { [ -f "$RAIZ/$1" ] && echo "$RAIZ/$1" || echo "$RAIZ/.delta-11/scripts/$1"; }
TASK_DONE="$(achar task-done.sh)"
VIGILANTE="$(achar vigilante.sh)"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

for s in "$TASK_DONE" "$VIGILANTE"; do
    [ -f "$s" ] || { echo -e "${RED}[FALTA]${NC} script não encontrado: $s"; exit 1; }
done

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/delta11-taskdone-test-XXXXXX")"
SANDBOX="$(cd "$SANDBOX" && pwd -P)"
cleanup() { [ -n "$SANDBOX" ] && [ -d "$SANDBOX" ] && rm -rf "$SANDBOX"; }
trap cleanup EXIT
export HOME="$SANDBOX/home"; mkdir -p "$HOME"
unset CLAUDE_PROJECT_DIR || true

P="$SANDBOX/projeto"
mkdir -p "$P/.delta-11/scripts" "$P/.delta-11/memoria" "$P/.delta-11/ativacoes" "$P/.delta-11/logs/autocritica" "$P/.delta-11/locks"
cp "$TASK_DONE" "$VIGILANTE" "$P/.delta-11/scripts/"
cat > "$P/.delta-11/kanban.md" <<'EOF'
# KANBAN
## ⚡ FAZENDO
<!-- Formato: **[ID]** — [Descrição] | Agente: [NOME] | Início: [hora] -->
**T-027** — Rota de pedidos | Agente: ENGINE | Início: 2026-10-14T10:00:00-03:00

## 🚫 BLOQUEADO
<!-- Formato -->
EOF
printf 'o que existe\nautocritica: .delta-11/logs/autocritica/2026-10-14-T-027-ENGINE.md\n' > "$P/.delta-11/memoria/ENGINE-produto.md"
echo "T-027 feito" > "$P/.delta-11/memoria/ENGINE-historia.md"
echo "parada 1 e 2" > "$P/.delta-11/logs/autocritica/2026-10-14-T-027-ENGINE.md"
(cd "$P" && git init -q -b main && git add -A && git -c user.email=t@t -c user.name=t commit -q -m inicial \
    && git worktree add -q "$P/.claude/worktrees/agent-engine" -b agent-engine)
W="$P/.claude/worktrees/agent-engine"
KANBAN_ANTES="$(shasum "$P/.delta-11/kanban.md")"

# ─── task-done a partir da worktree ───────────────────────────
SAIDA="$(cd "$W" && bash .delta-11/scripts/task-done.sh ENGINE T-027 "Rota de pedidos" "src/app/api/orders/route.ts" 2>&1)" \
    || { err "task-done terminou com erro"; echo "$SAIDA" | tail -15; }

grep -q "T-027" "$P/.delta-11/logs/golden-path.log" 2>/dev/null && ok "1: golden-path.log gravado na pasta principal" || err "1: golden-path.log não está na pasta principal"
grep -qE '^- \[[0-9T:-]+Z\] \[task-done\] \[ENGINE\] T-027' "$P/.delta-11/activity-log.md" 2>/dev/null \
    && ok "1: linha no activity-log no formato único (D25)" || err "1: linha do activity-log ausente ou fora do formato"
[ -e "$W/.delta-11/logs/golden-path.log" ] && err "1: gravou na cópia da worktree (invisível para o CRONOS)" || true
[ -z "$(ls "$P/.delta-11/ativacoes" "$W/.delta-11/ativacoes" 2>/dev/null | grep -i '\.txt')" ] \
    && ok "2: nenhum .txt de revisão criado (aviso vai por SendMessage)" || err "2: criou arquivo .txt em ativacoes/"
[ "$KANBAN_ANTES" = "$(shasum "$P/.delta-11/kanban.md")" ] && ok "3: kanban intacto (só o CRONOS escreve)" || err "3: task-done mexeu no kanban"
for passo in "1a" "1b" "3.4" "3.5" "3.7" "3.8" "3.9" "SendMessage"; do
    grep -q "$passo" <<< "$SAIDA" || err "4: checklist sem o passo $passo"
done
ok "4: checklist 1a → 3.9 com SendMessage ao CRONOS"
grep -q "estado.md" "$TASK_DONE" && err "5: task-done ainda usa -estado.md" || ok "5: usa -produto.md/-historia.md"
grep -q "Conferências OK" <<< "$SAIDA" && ok "conferências de produto/história/autocrítica passaram" || err "conferências falharam: $(grep '⚠' <<< "$SAIDA" | head -3)"

# ─── vigilante --once ─────────────────────────────────────────
grep -qE '(\./|bash |sh )disparar\.sh' "$VIGILANTE" && err "6: vigilante ainda chama disparar.sh" || ok "6: vigilante não chama disparar.sh (C-066)"
SAIDA_V="$(cd "$P" && bash .delta-11/scripts/vigilante.sh --once 2>&1)" || err "vigilante --once terminou com erro"
[ -f "$P/.delta-11/ativacoes/aviso-vigilante.txt" ] && grep -q "ENGINE" "$P/.delta-11/ativacoes/aviso-vigilante.txt" \
    && ok "7: aviso para o CRONOS gravado em ativacoes/aviso-vigilante.txt" || err "7: aviso para o CRONOS não foi gravado"
grep -q "\[vigilante\] \[CRONOS\]" "$P/.delta-11/activity-log.md" && ok "7: problema registrado no activity-log" || err "7: activity-log sem a linha do vigilante"
grep -q "/tmp/" "$VIGILANTE" && err "8: vigilante ainda usa /tmp" || ok "8: vigilante não usa /tmp (D21)"

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — task-done.sh e vigilante.sh${NC}"; exit 0; } || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }
