#!/usr/bin/env bash
# Teste do vigia dia1-badal-checker.py (v6.3 — C-025)
source "$(dirname "$0")/_ajudante-hooks-python.sh" dia1-badal-checker
checagens_basicas

VISAO_CHEIA=$'## VISÃO DO PRODUTO\n- **Frase decisória:** "Chega de planilha"\n- **Identidade assumida:** gestora que decide com dados\n- **Identidade fugida:** dona que apaga incendio\n- **Teste do badal:** as duas ficam nitidas\n- **Inimigo único:** retrabalho\n- **Trauma único:** perder cliente por atraso\n- **Lago abandonado:** planilhas soltas\n- **Nova categoria:** painel de decisao diaria'
VISAO_MODELO=$'## VISÃO DO PRODUTO\n- **Frase decisória:** [preencher]\n- **Identidade assumida:** [preencher]\n- **Identidade fugida:** [preencher]\n- **Teste do badal:** [preencher]\n- **Inimigo único:** [preencher]\n- **Trauma único:** [preencher]\n- **Lago abandonado:** [preencher]\n- **Nova categoria:** [preencher]'

novo_projeto
PC="$TEST_DIR/.delta-11/memoria/project-core.md"
printf '# PC\n%s\n## CONTRATOS\n(vazio)\n' "$VISAO_MODELO" > "$PC"
espera 0 "VISAO do modelo sem mudanca: passa" "$(evento tool_name=Write tool_input.file_path=$PC "tool_input.content=$(cat "$PC")")"
espera 0 "editar CONTRATOS com a VISAO ainda vazia: passa (nao trava contratos)" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=(vazio)' 'tool_input.new_string=POST /api/orders')"
espera 2 "preencher so 3 elementos da VISAO: bloqueia" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=- **Frase decisória:** [preencher]' $'tool_input.new_string=- **Frase decisória:** chega\n- x')"
stderr_contem "de 8 respostas"
espera 0 "VISAO com os 8 preenchidos: passa" "$(evento tool_name=Write tool_input.file_path=$PC "tool_input.content=# PC"$'\n'"$VISAO_CHEIA"$'\n## CONTRATOS\n')"
printf '# PC\n%s\n## CONTRATOS\n' "$VISAO_CHEIA" > "$PC"
espera 2 "trocar respostas por rotulos com [preencher]: bloqueia (rotulo nao e resposta)" "$(evento tool_name=Write tool_input.file_path=$PC "tool_input.content=# PC"$'\n'"$VISAO_MODELO"$'\n## CONTRATOS\nPOST /x')"
printf '# PC\n## CONTRATOS\n' > "$PC"
espera 0 "project-core sem secao VISAO: nada a conferir" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=## CONTRATOS' $'tool_input.new_string=## CONTRATOS\nGET /x')"

# PRD (docs/prd.md)
mkdir -p "$TEST_DIR/docs"
espera 2 "PRD sem os elementos: bloqueia" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/docs/prd.md $'tool_input.content=# PRD\n## 1. O problema\nalgo')"
espera 0 "PRD com a VISAO completa: passa" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/docs/prd.md "tool_input.content=# PRD"$'\n'"$VISAO_CHEIA")"
espera 0 "outro arquivo .md: ignora" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/docs/outro.md tool_input.content=x)"
fim
