#!/usr/bin/env bash
# Teste do vigia validar-deploy.py (v6.3 — C-044, C-130, D30)
source "$(dirname "$0")/_ajudante-hooks-python.sh" validar-deploy
checagens_basicas

novo_projeto
mkdir -p "$TEST_DIR/tests/contracts" "$TEST_DIR/bin"
touch "$TEST_DIR/pyproject.toml"
printf '#!/bin/sh\n[ -f "%s/.passar" ] && exit 0\necho "FAILED contrato"; exit 1\n' "$TEST_DIR" > "$TEST_DIR/bin/pytest"
chmod +x "$TEST_DIR/bin/pytest"
export PATH="$TEST_DIR/bin:$PATH"
pede() { evento hook_event_name=UserPromptSubmit "prompt=$1"; }

for frase in "faça o deploy" "pode fazer o deploy?" "publique em produção" "sobe pra produção agora" "coloca no ar" "deploy" "/deploy" "ship it" "bora fazer o deploy do painel"; do
    espera 2 "pedido claro: '$frase' com testes falhando bloqueia" "$(pede "$frase")"
done
stderr_contem "testes de contrato falharam"
for frase in "não faça deploy" "nao suba pra produção ainda" "sem deploy hoje" "don't deploy" "como funciona o deploy?" "quando vamos fazer o deploy?" "o deploy de ontem falhou" "[CRONOS] relatorio: deploy feito no staging" "<task-notification>faça o deploy</task-notification>" "revise o texto da pagina"; do
    espera 0 "nao e pedido: '$frase'" "$(pede "$frase")"
done
touch "$TEST_DIR/.passar"
espera 0 "pedido claro com testes passando: libera" "$(pede "faça o deploy")"

novo_projeto
espera 0 "sem framework de testes: libera com AVISO" "$(pede "faça o deploy")"
log_contem "AVISO: nenhum framework"
fim
