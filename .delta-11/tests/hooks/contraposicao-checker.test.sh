#!/usr/bin/env bash
# Teste do vigia contraposicao-checker.py (v6.3 — C-023)
source "$(dirname "$0")/_ajudante-hooks-python.sh" contraposicao-checker
checagens_basicas

novo_projeto
PC="$TEST_DIR/.delta-11/memoria/project-core.md"
MODELO=$'# MEMORIA CENTRAL\n## PROJETO\nNome: [preencher]\n## CONTRAPOSIÇÃO LATERAL (por dia)\n- **Dia 1 — Tipo 1 (existencial-identitaria):** [preencher]\n- **Dia 2 — Tipo 2 (estrutural tripla):** [preencher]\n## CONTRATOS\n(vazio)'
printf '%s\n' "$MODELO" > "$PC"

espera 0 "editar CONTRATOS (fora da secao) com o modelo vazio: passa" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=(vazio)' 'tool_input.new_string=GET /api/users -> 200')"
espera 0 "preencher o Dia 1 com os dois lados: passa" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=(existencial-identitaria):** [preencher]' 'tool_input.new_string=(existencial-identitaria):** identidade assumida × identidade fugida')"
espera 2 "preencher o Dia 1 com um lado so: bloqueia" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=(existencial-identitaria):** [preencher]' 'tool_input.new_string=(existencial-identitaria):** identidade assumida')"
stderr_contem "dominante × testemunha"
espera 2 "apagar a secao de contraposicao: bloqueia" "$(evento tool_name=Write tool_input.file_path=$PC $'tool_input.content=# MEMORIA CENTRAL\n## PROJETO\nNome: X')"
espera 0 "aceita 'vs' como separador" "$(evento tool_name=Edit tool_input.file_path=$PC 'tool_input.old_string=(estrutural tripla):** [preencher]' 'tool_input.new_string=(estrutural tripla):** arquitetura vs mundo externo')"
espera 2 "secao so com texto solto, sem linha de Dia: bloqueia" "$(evento tool_name=Write tool_input.file_path=$PC $'tool_input.content=# MC\n## CONTRAPOSIÇÃO LATERAL\nAinda vamos pensar nisso com calma.')"

# project-core antigo, sem a secao: nao bloqueia (so AVISO)
printf '# MC\n## PROJETO\nx\n' > "$PC"
espera 0 "project-core sem secao (antigo): nao bloqueia" "$(evento tool_name=Edit tool_input.file_path=$PC tool_input.old_string=x tool_input.new_string=y)"
log_contem "AVISO: project-core sem secao"
espera 0 "fatia memoria/project-core/contratos.md nao e alvo" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/.delta-11/memoria/project-core/contratos.md tool_input.content=x)"
espera 0 "caminho relativo e reconhecido (e liberado quando ok)" "$(evento tool_name=Write tool_input.file_path=.delta-11/memoria/project-core.md $'tool_input.content=## Contraposição lateral\n- Dia 3 — Tipo 3: schema × contratos')"
espera 2 "caminho relativo com Dia sem os dois lados: bloqueia" "$(evento tool_name=Write tool_input.file_path=.delta-11/memoria/project-core.md $'tool_input.content=## Contraposição lateral\n- Dia 3 — Tipo 3: schema')"
fim
