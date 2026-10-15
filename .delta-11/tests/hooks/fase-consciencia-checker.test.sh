#!/usr/bin/env bash
# Teste do vigia fase-consciencia-checker.py (v6.3 — C-015, C-026; v6.4 — V9 ciclo leve). Fase 4.5 = Dia 6.
source "$(dirname "$0")/_ajudante-hooks-python.sh" fase-consciencia-checker
checagens_basicas

novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
kanban $'# Kanban\n## FAZENDO\n- [ ] T-CON-01 [4.5] auditoria | Agente: VAULT'
SELO_REL=$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nFase 4.5 selada pelo SHIELD')
SELO_ABS=$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\n- [x] Dia 6 selado')

espera 0 "concluir tarefa [4.5] individual: passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-CON-01' 'tool_input.new_string=- [x] T-CON-01')"
espera 2 "selo com caminho RELATIVO e sem entregaveis: bloqueia (C-026)" "$SELO_REL"
espera 2 "selo 'Dia 6 selado' com caminho absoluto: bloqueia" "$SELO_ABS"

# 5 arquivos quaisquer com 'consciencia' no nome NAO bastam (C-026)
for s in a b c d e; do echo x > "$DEC/2026-10-14-consciencia-01-$s.md"; done
espera 2 "5 arquivos todos com numero 01: bloqueia (faltam 02 a 05)" "$SELO_REL"
stderr_contem "05. fluxos-aprovacao"

for n in 02 03 04 05; do echo x > "$DEC/2026-10-14-consciencia-$n-item.md"; done
espera 0 "um entregavel de cada numero (01 a 05): selo liberado" "$SELO_REL"
espera 0 "edicao sem selo: passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md tool_input.old_string=auditoria tool_input.new_string=auditoria-imutavel)"

# ── v6.4 — V9: ciclo leve (checklist de 1 página do Ciclo 2 em diante) ──
novo_projeto
DEC="$TEST_DIR/.delta-11/memoria/decisoes"
selo_no_ciclo() {  # $1 = linha do ciclo no kanban ("" = sem informação)
    kanban "# Kanban"$'\n'"$1"
    evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=# Kanban' $'tool_input.new_string=# Kanban\nFase 4.5 selada pelo SHIELD'
}
checklist_consciencia() {  # $1 = arquivo; $2 = resposta do item 03 (vazio = não responde)
    {
        echo "# Checklist de Consciência — Ciclo 2"
        echo "| Nº | Item | Neste ciclo | Documento completo |"
        echo "|---|---|---|---|"
        for item in "01 auditoria-imutavel" "02 rate-limiting" "03 motor-regras" "04 lgpd" "05 fluxos-aprovacao"; do
            n="${item%% *}"; slug="${item#* }"
            if [ "$n" = "03" ]; then resposta="$2"; else resposta="sem mudança"; fi
            echo "| $n | $slug | $resposta | — |"
        done
    } > "$1"
}

espera 2 "Ciclo 1 (sem informação) sem os 5 documentos: bloqueia" "$(selo_no_ciclo "")"
checklist_consciencia "$DEC/2026-10-15-consciencia-checklist-ciclo-1.md" "sem mudança"
espera 2 "Ciclo 1: o checklist NÃO substitui os 5 documentos" "$(selo_no_ciclo "**Ciclo atual:** 1")"
rm -f "$DEC"/*-checklist-ciclo-1.md
espera 2 "Ciclo 2 sem checklist e sem documentos: bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
stderr_contem "consciencia-checklist-ciclo-2.md"
stderr_contem "consciencia-checklist-template.md"
checklist_consciencia "$DEC/2026-10-15-consciencia-checklist-ciclo-2.md" "sem mudança"
espera 0 "Ciclo 2 com o checklist completo: selo liberado" "$(selo_no_ciclo "**Ciclo atual:** 2")"
espera 0 "ciclo lido do fase_atual do kanban-data.js" "$(
    printf 'window.KANBAN_DATA = {\n  fase_atual: "Ciclo 2 · Fase 4.5",\n};\n' > "$TEST_DIR/.delta-11/kanban-data.js"
    selo_no_ciclo "")"
rm -f "$TEST_DIR/.delta-11/kanban-data.js"
checklist_consciencia "$DEC/2026-10-15-consciencia-checklist-ciclo-2.md" ""
espera 2 "Ciclo 2 com checklist sem resposta no item 03: bloqueia" "$(selo_no_ciclo "**Ciclo atual:** 2")"
stderr_contem "03. motor-regras"
checklist_consciencia "$DEC/2026-10-15-consciencia-checklist-ciclo-2.md" "mudou: regra nova de desconto em business-rules/can-apply-discount.ts"
espera 0 "item 03 com a mudança descrita: passa" "$(selo_no_ciclo "**Ciclo atual:** 2")"
fim
