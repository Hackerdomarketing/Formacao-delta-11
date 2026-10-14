#!/usr/bin/env bash
# Teste do vigia fase-descanso-checker.py (v6.3 — C-015, C-027). Fase 7 = Dia 7.
source "$(dirname "$0")/_ajudante-hooks-python.sh" fase-descanso-checker
checagens_basicas
if grep -q "CONAGRAC" "$HOOK"; then err "erro de digitacao CONAGRAC ainda existe (C-027)"; else ok "sem o erro de digitacao CONAGRAC (C-027)"; fi

novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
kanban $'# Kanban\n## FAZENDO\n- [ ] T-DES-01 docs [FRONT]'
SELO=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**Fase 7 consagrada**')
SELO_COM_TESTE=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**TESTE SUPREMO PASSOU** — 2 semanas sem intervencao\n**Fase 7 consagrada**')

espera 0 "um '[7]' solto no texto nao dispara (C-027)" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=docs [FRONT]' 'tool_input.new_string=docs [FRONT] ver nota [7] ✅')"
espera 2 "selo da Fase 7 sem entregaveis: bloqueia" "$SELO"
stderr_contem "Faltam"
for n in 01 02 03 04 05 06 07 08 09 10; do echo x > "$DEC/2026-10-14-descanso-$n-item.md"; done
espera 2 "10 entregaveis, mas sem TESTE SUPREMO: bloqueia" "$SELO"
stderr_contem "TESTE SUPREMO"
espera 0 "10 entregaveis + TESTE SUPREMO: selo liberado" "$SELO_COM_TESTE"
espera 0 "[CONSAGRAÇÃO] com SELO e a grafia certa reconhecida" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**TESTE SUPREMO OK** 2 semanas\n[CONSAGRAÇÃO] SELO final')"
rm -f "$DEC"/*-descanso-09-*
espera 2 "[CONSAGRAÇÃO] SELO com 9 entregaveis: bloqueia" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**TESTE SUPREMO OK** 2 semanas\n[CONSAGRAÇÃO] SELO final')"
stderr_contem "09. dr-testado"
espera 0 "'Fase 7.5' ou 'Fase 70' nao sao Fase 7" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nFase 7.5 selada')"
fim
