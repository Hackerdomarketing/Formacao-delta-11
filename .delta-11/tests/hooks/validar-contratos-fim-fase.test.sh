#!/usr/bin/env bash
# Teste do vigia validar-contratos-fim-fase.py (v6.3 — C-043, C-130, D30)
source "$(dirname "$0")/_ajudante-hooks-python.sh" validar-contratos-fim-fase
checagens_basicas

novo_projeto
BASE=$'# Kanban\n**Fase atual:** Fase 3\n## FAZENDO\n- [ ] T-1 rota [BACK]\n## CONCLUÍDO\n- [x] T-0 antiga [BACK] CONCLUIDO'
kanban "$BASE"
# projeto Python com testes de contrato falsos (sem pytest real): usa um pyproject e um "pytest" de mentira no PATH
mkdir -p "$TEST_DIR/tests/contracts" "$TEST_DIR/bin"
touch "$TEST_DIR/pyproject.toml"
printf '#!/bin/sh\n[ -f "%s/.passar" ] && { echo "1 passed"; exit 0; }\necho "FAILED tests/contracts/test_users.py::test_get - 500"; exit 1\n' "$TEST_DIR" > "$TEST_DIR/bin/pytest"
chmod +x "$TEST_DIR/bin/pytest"
export PATH="$TEST_DIR/bin:$PATH"

espera 0 "concluir uma tarefa (sem mudar de fase): NAO roda a bateria" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=- [ ] T-1' 'tool_input.new_string=- [x] T-1')"
espera 0 "reescrever o kanban inteiro sem mudar de fase: NAO roda" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n(organizado)')"
espera 0 "'[x]' e CONCLUIDO antigos nao disparam" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE")"
espera 2 "selo de fase com testes de contrato falhando: bloqueia" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=## FAZENDO' $'tool_input.new_string=**Fase 3 selada**\n## FAZENDO')"
stderr_contem "test_users.py"
espera 2 "mudar o 'Fase atual' com testes falhando: bloqueia" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=**Fase atual:** Fase 3' 'tool_input.new_string=**Fase atual:** Fase 3.5')"
touch "$TEST_DIR/.passar"
espera 0 "selo de fase com testes passando: libera" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=## FAZENDO' $'tool_input.new_string=**Fase 3 selada**\n## FAZENDO')"
log_contem "OK: testes de contrato passaram"

# sem framework de testes: libera com AVISO
novo_projeto
kanban "$BASE"
espera 0 "sem framework de testes: transicao liberada" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=**Fase atual:** Fase 3' 'tool_input.new_string=**Fase atual:** Fase 4')"
log_contem "AVISO: nenhum framework"
touch "$TEST_DIR/pyproject.toml"
espera 0 "pyproject sem pasta tests/contracts: nao roda pytest (sem bloqueio falso)" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md 'tool_input.old_string=**Fase atual:** Fase 3' 'tool_input.new_string=**Fase atual:** Fase 4')"
if grep -q "TEMPO_MAXIMO = 110" "$HOOK"; then ok "tempo maximo dos testes 110 s (< 120 s do registro, D30)"; else err "tempo maximo nao e 110 s"; fi
fim
