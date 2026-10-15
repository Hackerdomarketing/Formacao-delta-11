#!/usr/bin/env bash
# Teste do vigia validar-arquitetura-vs-modelos.py (v6.3 — C-042)
source "$(dirname "$0")/_ajudante-hooks-python.sh" validar-arquitetura-vs-modelos
checagens_basicas

novo_projeto
BASE=$'# Kanban\n## FAZENDO\n- [ ] T-VAULT-01 schema do banco e RLS | Agente: VAULT'
kanban "$BASE"
SELO3=$'\n**Fase 3 selada** — fundacao pronta'

espera 0 "concluir tarefa com 'banco', 'schema', 'RLS' (sem selo): passa (C-042)" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-VAULT-01' 'tool_input.new_string=- [x] T-VAULT-01')"
espera 2 "selo da Fase 3 sem a tarefa de retrovalidacao: bloqueia (AUSENTE)" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE$SELO3")"
stderr_contem "Nao existe a tarefa"
espera 2 "retrovalidacao pendente: bloqueia" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n- [ ] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3'"$SELO3")"
stderr_contem "ainda nao foi concluida"
espera 2 "retrovalidacao concluida sem resposta: bloqueia" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n- [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3'"$SELO3")"
stderr_contem "sem **SUSTENTA**"
espera 2 "retrovalidacao REFAZER: bloqueia" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n- [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3 — **REFAZER**'"$SELO3")"
stderr_contem "REFEITA"
espera 0 "retrovalidacao SUSTENTA: selo da Fase 3 liberado" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n- [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3 — **SUSTENTA** | Por: ATLAS'"$SELO3")"
espera 0 "SUSTENTA em OUTRA linha (nao na da tarefa) nao conta... mas sem selo nao ha checagem" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\nSUSTENTA')"
espera 2 "SUSTENTA solto numa linha e retrovalidacao sem resposta: bloqueia" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n- [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3\nnota: SUSTENTA'"$SELO3")"
espera 0 "selo da Fase 3.5 nao e selo da Fase 3" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\nFase 3.5 selada')"
espera 0 "resumo 'Fase 3 — 2 tarefas concluídas' nao e selo" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n**Fase atual:** Fase 3 — 2 tarefas concluídas')"
fim
