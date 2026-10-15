#!/usr/bin/env bash
# Teste do vigia fase-ritmo-checker.py (v6.3 — C-015, C-028; v6.4 — V9 ciclo leve). Fase 3.5 = Dia 4.
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

# ── v6.4 — V9: ciclo leve (checklist de 1 página do Ciclo 2 em diante) ──
novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
selo_no_ciclo() {  # $1 = linha do ciclo no kanban ("" = sem informação)
    kanban "# Kanban"$'\n'"$1"
    evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n**Fase 3.5 selada** — SUSTENTA (BACK)'
}
checklist_ritmo() {  # $1 = arquivo; $2 = resposta do item 04 (vazio = não responde)
    {
        echo "# Checklist de Ritmo Temporal — Ciclo 2"
        echo "| Nº | Item | Neste ciclo | Documento completo |"
        echo "|---|---|---|---|"
        for item in "01 sistema-eventos" "02 filas" "03 jobs-agendados" "04 cache-ttl" "05 timeouts" \
                    "06 retries" "07 circuit-breakers" "08 ci-cd-staging" "09 observabilidade" "10 sub-contraposicao"; do
            n="${item%% *}"; slug="${item#* }"
            if [ "$n" = "04" ]; then resposta="$2"; else resposta="sem mudança"; fi
            echo "| $n | $slug | $resposta | — |"
        done
    } > "$1"
}

espera 2 "Ciclo 1 (sem informação de ciclo) sem os 10 documentos: bloqueia" "$(selo_no_ciclo "")"
stderr_contem "Faltam 10"
checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-1.md" "sem mudança"
espera 2 "Ciclo 1 explícito: o checklist NÃO substitui os 10 documentos" "$(selo_no_ciclo "**Ciclo atual:** 1")"
rm -f "$DEC"/*-checklist-ciclo-1.md

espera 2 "Ciclo 2 sem checklist e sem documentos: bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
stderr_contem "ritmo-temporal-checklist-ciclo-2.md"
stderr_contem "ritmo-temporal-checklist-template.md"

checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md" "sem mudança"
espera 0 "Ciclo 2 com o checklist completo: selo liberado" "$(selo_no_ciclo "**Ciclo atual:** 2")"
log_contem "fase-ritmo-checker.*Ciclo 2.*checklist"
espera 2 "checklist do Ciclo 2 NÃO vale para o Ciclo 3" "$(selo_no_ciclo "**Ciclo atual:** 3")"
espera 0 "ciclo lido do fase_atual do kanban-data.js (\"Ciclo 2 · Fase 3.5\")" "$(
    printf 'window.KANBAN_DATA = {\n  fase_atual: "Ciclo 2 · Fase 3.5 · onda 1 de 2",\n};\n' > "$TEST_DIR/.delta-11/kanban-data.js"
    selo_no_ciclo "")"
rm -f "$TEST_DIR/.delta-11/kanban-data.js"
espera 0 "ciclo lido da linha **Fase atual:** (\"Ciclo 2 — Fase 3.5\")" "$(selo_no_ciclo "**Fase atual:** Ciclo 2 — Fase 3.5")"
espera 0 "ciclo lido da própria linha do selo (\"[SELO 3.5] Ciclo 2\")" "$(kanban "# Kanban"; evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n[SELO 3.5] Ciclo 2 — SUSTENTA')"

checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md" "[sem mudança — ou \"mudou: ...\"]"
espera 2 "Ciclo 2 com checklist sem resposta no item 04 (marcador do modelo): bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
stderr_contem "04. cache-ttl"
checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md" "mudou: TTL do catálogo caiu para 5 min (novo campo de estoque)"
espera 0 "item 04 com a mudança em 1 linha: passa" "$(selo_no_ciclo "**Ciclo atual:** 2")"
checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md" "mudou: cache novo — documento completo: 2026-10-15-ritmo-temporal-04-cache-ttl.md"
espera 2 "item 04 cita documento completo que NÃO existe: bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
stderr_contem "documento completo"
echo "cache novo do catalogo" > "$DEC/2026-10-15-ritmo-temporal-04-cache-ttl.md"
espera 0 "item 04 cita documento completo que existe: passa" "$(selo_no_ciclo "**Ciclo atual:** 2")"

: > "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md"
rm -f "$DEC"/*-ritmo-temporal-04-*
for n in 01 02 03 04 05 06 07 08 09 10; do echo "conteudo" > "$DEC/2026-10-14-ritmo-temporal-$n-item.md"; done
espera 2 "Ciclo 2 só com os 10 documentos do Ciclo 1, sem checklist do ciclo atual: bloqueia (v6.4)" "$(selo_no_ciclo "**Ciclo atual:** 2")"
checklist_ritmo "$DEC/2026-10-15-ritmo-temporal-checklist-ciclo-2.md" ""
espera 2 "Ciclo 2: checklist COMEÇADO e incompleto bloqueia mesmo com documentos antigos" "$(selo_no_ciclo "**Ciclo atual:** 2")"
# Documentos COMPLETOS feitos no ciclo atual (citam "Ciclo N") também liberam o selo (caso real: salvahacks, Ciclo 5)
rm -f "$DEC"/*-checklist-ciclo-2.md
for n in 01 02 03 04 05 06 07 08 09 10; do echo "Recorte do Ciclo 2: conteudo" > "$DEC/2026-10-15-ritmo-temporal-$n-item.md"; done
espera 0 "Ciclo 2 sem checklist, mas com os 10 documentos completos do Ciclo 2: passa" "$(selo_no_ciclo "**Ciclo atual:** 2")"
log_contem "fase-ritmo-checker.*documentos completos do ciclo"
echo "conteudo sem ciclo" > "$DEC/2026-10-15-ritmo-temporal-07-item.md"
espera 2 "Ciclo 2: 9 documentos do ciclo + 1 sem citar o ciclo: bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
fim
