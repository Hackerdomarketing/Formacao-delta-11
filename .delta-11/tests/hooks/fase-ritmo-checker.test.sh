#!/usr/bin/env bash
# Teste do vigia fase-ritmo-checker.py (v6.3 — C-015, C-028). Fase 3.5 = Dia 4.
source "$(dirname "$0")/_ajudante-hooks-python.sh" fase-ritmo-checker
checagens_basicas

novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
kanban $'# Kanban\n## FAZENDO\n- [ ] T-RIT-01 [3.5] sistema de eventos | Agente: ENGINE'
SELO=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**Fase 3.5 selada** — SUSTENTA (ATLAS)')

espera 0 "concluir uma tarefa da Fase 3.5 (sem selo): passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-RIT-01' 'tool_input.new_string=- [x] T-RIT-01')"
espera 0 "criar tarefa pendente 'Selar Fase 3.5': passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=## FAZENDO' $'tool_input.new_string=## FAZENDO\n- [ ] T-RIT-11 Selar Fase 3.5 | Agente: ATLAS')"
espera 0 "texto com 'ritmo temporal' sem selo: passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nnotas sobre ritmo temporal')"
espera 2 "declarar 'Fase 3.5 selada' sem nenhum artefato: bloqueia" "$SELO"
stderr_contem "Faltam 10"

for n in 01 02 03 04 05 06 07; do echo "conteudo" > "$DEC/2026-10-14-ritmo-temporal-$n-item.md"; done
espera 2 "com 7 de 10 artefatos: bloqueia" "$SELO"
stderr_contem "Faltam 3"
stderr_contem "08. ci-cd-staging"
if printf '%s' "$SAIDA_ERRO" | grep -q "01. sistema-eventos  ->"; then err "lista um artefato que JA existe como faltante (C-028)"; else ok "nao lista como faltante o que ja existe (C-028)"; fi

: > "$DEC/2026-10-14-ritmo-temporal-08-ci-cd-staging.md"
echo x > "$DEC/2026-10-14-ritmo-temporal-07-copia.md"
espera 2 "arquivo vazio e numero repetido nao contam" "$SELO"
stderr_contem "Faltam 3"

for n in 08 09 10; do echo "conteudo" > "$DEC/2026-10-14-ritmo-temporal-$n-item.md"; done
espera 0 "com os 10 artefatos (01 a 10): selo liberado" "$SELO"
espera 0 "[SELO 3.5] tambem e reconhecido e passa com os 10" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n- [x] [SELO 3.5] ritmo')"
rm -f "$DEC"/*-ritmo-temporal-10-*
espera 2 "[SELO 3.5] com 9 artefatos: bloqueia" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n- [x] [SELO 3.5] ritmo')"
espera 0 "selo de OUTRA fase (Fase 3) nao e assunto deste vigia" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nFase 3 selada')"
fim
