#!/usr/bin/env bash
# Teste do vigia gc-locks.py (v6.3 — C-030, C-130, D36)
source "$(dirname "$0")/_ajudante-hooks-python.sh" gc-locks
checagens_basicas

novo_projeto
L="$TEST_DIR/.delta-11/locks"
A="$TEST_DIR/.delta-11/ativacoes"
trava() { mkdir -p "$L/$1"; printf 'AGENTE: %s\nTAREFA: T-1\n' "$2" > "$L/$1/meta"; envelhecer "$L/$1" "$3"; }
trava src--a.ts.lock BACK 3        # velha, dono SEM pulso      -> remove
trava src--b.ts.lock FRONT 3       # velha, dono COM pulso      -> fica (C-030)
trava src--c.ts.lock VAULT 1       # nova                        -> fica
trava src--d.ts.lock ENGINE 3      # velha, pulso velho          -> remove
printf '{"agente":"FRONT","epoch":%s}\n' "$(date +%s)" > "$A/pulso-FRONT.json"
printf '{"agente":"ENGINE","epoch":%s}\n' "$(( $(date +%s) - 4*3600 ))" > "$A/pulso-ENGINE.json"
mkdir -p "$L/activity-log.mutex"; envelhecer "$L/activity-log.mutex" 3
echo "x" > "$L/README.md"; envelhecer "$L/README.md" 100
echo x > "$TEST_DIR/.delta-11/scratch/velho.txt"; envelhecer "$TEST_DIR/.delta-11/scratch/velho.txt" $((8*24))
echo x > "$TEST_DIR/.delta-11/scratch/novo.txt"
echo x > "$TEST_DIR/.delta-11/logs/sub-agentes/antigo.log"; envelhecer "$TEST_DIR/.delta-11/logs/sub-agentes/antigo.log" $((31*24))
echo "nao tocar" > "$TEST_DIR/.delta-11/kanban.md"; envelhecer "$TEST_DIR/.delta-11/kanban.md" 1000

espera 0 "SessionStart: limpeza nunca bloqueia" "$(evento hook_event_name=SessionStart source=startup)"
if [ -z "$SAIDA_PADRAO" ]; then ok "nada no stdout"; else err "stdout: $SAIDA_PADRAO"; fi
[ ! -e "$L/src--a.ts.lock" ] && ok "trava velha de dono sem pulso: removida" || err "trava sem pulso ficou"
[ -d "$L/src--b.ts.lock" ] && ok "trava velha de dono COM pulso recente: mantida (C-030)" || err "apagou trava de agente vivo"
[ -d "$L/src--c.ts.lock" ] && ok "trava nova: mantida" || err "apagou trava nova"
[ ! -e "$L/src--d.ts.lock" ] && ok "trava velha de dono com pulso velho: removida" || err "trava com pulso velho ficou"
[ ! -e "$L/activity-log.mutex" ] && ok "mutex abandonado: removido" || err "mutex abandonado ficou"
[ -f "$L/README.md" ] && ok "README.md protegido" || err "apagou README.md"
[ ! -e "$TEST_DIR/.delta-11/scratch/velho.txt" ] && [ -f "$TEST_DIR/.delta-11/scratch/novo.txt" ] && ok "scratch: so o de 8 dias saiu" || err "scratch errado"
[ ! -e "$TEST_DIR/.delta-11/logs/sub-agentes/antigo.log" ] && ok "log de 31 dias: removido" || err "log antigo ficou"
[ -f "$TEST_DIR/.delta-11/kanban.md" ] && ok "kanban nunca e tocado" || err "apagou o kanban"
log_contem "\[gc-locks\] \[SISTEMA\] trava mantida \(dono FRONT com pulso"

# lock_horas configuravel (D36)
novo_projeto
L="$TEST_DIR/.delta-11/locks"
trava src--e.ts.lock PIXEL 3
echo '{"lock_horas": 5}' > .delta-11/.config-limites.json
espera 0 "com lock_horas=5" "$(evento hook_event_name=SessionStart)"
[ -d "$L/src--e.ts.lock" ] && ok "lock_horas=5: trava de 3 h mantida" || err "ignorou lock_horas"
fim
