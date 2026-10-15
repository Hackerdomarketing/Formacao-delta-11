#!/usr/bin/env bash
# Teste do vigia sistema-no-historico.py (v6.4.1): despacho em worktree com regras do sistema fora do historico do git.
source "$(dirname "$0")/_ajudante-hooks-python.sh" sistema-no-historico
checagens_basicas

novo_projeto
mkdir -p .delta-11/operativos src
echo "# CRONOS v6.2" > .delta-11/operativos/CRONOS.md
echo "codigo" > src/app.ts
DESPACHO=$(evento tool_name=Agent tool_input.isolation=worktree tool_input.name=back-onda-1 'tool_input.prompt=Agente: BACK')
SEM_WORKTREE=$(evento tool_name=Agent tool_input.name=back-onda-1 'tool_input.prompt=Agente: BACK')

espera 0 "fora de repositorio git: libera" "$DESPACHO"

git init -q && git config user.email t@t && git config user.name t && git add -A && git commit -qm inicio
espera 0 "tudo commitado: libera" "$DESPACHO"

echo "# CRONOS v6.4.1" > .delta-11/operativos/CRONOS.md
espera 2 "operativo atualizado e NAO commitado + despacho em worktree: bloqueia" "$DESPACHO"
stderr_contem ".delta-11/operativos/CRONOS.md"
stderr_contem "git commit -m"
log_contem "sistema-no-historico"
espera 0 "mesmo caso, mas despacho SEM worktree: libera" "$SEM_WORKTREE"
espera 0 "ferramenta que nao e Agent/Task: libera" "$(evento tool_name=Edit tool_input.file_path=src/app.ts)"

echo "outra coisa" > src/app.ts
rodar_hook "$DESPACHO"
COMANDO=$(printf '%s\n' "$SAIDA_ERRO" | grep -E '^  (git add|git commit)')
if (eval "$(printf '%s\n' "$COMANDO" | sed 's/^  //')") >/dev/null 2>&1; then ok "o comando sugerido pelo vigia roda sem erro"; else err "o comando sugerido pelo vigia FALHOU: $COMANDO"; fi
espera 0 "depois do comando sugerido: libera (codigo do projeto alterado nao importa)" "$DESPACHO"
if git status --porcelain -- src/app.ts | grep -q "app.ts"; then ok "o comando sugerido NAO commitou o codigo do projeto"; else err "o comando sugerido commitou codigo do projeto"; fi

mkdir -p .delta-11/perfis && echo '{"model":"sonnet"}' > .delta-11/perfis/SHIELD.json
espera 2 "perfil novo (arquivo nao rastreado) tambem conta: bloqueia" "$DESPACHO"
fim
