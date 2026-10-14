#!/usr/bin/env bash
# Teste do vigia abrir-painel.sh (SessionStart) — Delta-11 v6.3
# Cobre N-001/D27: abre o painel da pasta principal, no máximo uma vez a
# cada 8 h, nunca falha a sessão, funciona com entrada vazia (Passo 0).
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"

CMD=$(comando_do_registro SessionStart abrir-painel.sh) || { err "abrir-painel.sh NAO registrado em SessionStart"; resultado_final "abrir-painel.sh"; }
ok "registrado em SessionStart: $CMD"
[ "$(matchers_do_registro SessionStart abrir-painel.sh)" = "" ] && ok "matcher vazio (toda sessao)" || err "matcher inesperado"
bash -n "$HOOKS_DIR/abrir-painel.sh" && ok "bash -n" || err "bash -n falhou"
[ -x "$HOOKS_DIR/abrir-painel.sh" ] && ok "executavel" || err "sem permissao de execucao"

P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
com_git_e_worktree "$P"
W="$P/.claude/worktrees/w1"
echo "<html></html>" > "$P/.delta-11/painel.html"
# Falsos "open"/"xdg-open": só anotam o que seria aberto (não abre navegador no teste)
mkdir -p "$P/bin-falso"
for prog in open xdg-open; do printf '#!/bin/sh\necho "$@" >> "%s/aberturas.txt"\n' "$P" > "$P/bin-falso/$prog"; chmod +x "$P/bin-falso/$prog"; done
CMD_FALSO="PATH=\"$P/bin-falso:\$PATH\"; $CMD"
esperar_abertura() { local i; for i in 1 2 3 4 5 6 7 8 9 10; do [ -f "$P/aberturas.txt" ] && return 0; sleep 0.2; done; return 1; }

rodar "$P" "$W" "$CMD_FALSO" '{"hook_event_name":"SessionStart","session_id":"S1","cwd":"'"$W"'","source":"startup"}'
[ "$CODIGO" = "0" ] && ok "exit 0" || err "exit=$CODIGO"
[ -z "$SAIDA" ] && ok "nada no stdout (no SessionStart iria para o modelo)" || err "stdout: $SAIDA"
esperar_abertura && grep -qx "$P/.delta-11/painel.html" "$P/aberturas.txt" && ok "abriu o painel da PASTA PRINCIPAL (chamado de dentro da worktree)" || err "nao abriu o painel da principal"
[ -f "$P/.delta-11/ativacoes/.painel-aberto" ] && ok "marca .painel-aberto gravada na principal" || err "marca ausente"

rodar "$P" "$P" "$CMD_FALSO" '{"hook_event_name":"SessionStart","session_id":"S2","cwd":"'"$P"'","source":"resume"}'
sleep 0.5
[ "$(wc -l < "$P/aberturas.txt" | tr -d ' ')" = "1" ] && ok "segunda sessao em menos de 8 h: nao abre de novo" || err "abriu de novo antes de 8 h"

envelhecer "$P/.delta-11/ativacoes/.painel-aberto" 9
rm -f "$P/aberturas.txt"
(cd "$W" && PATH="$P/bin-falso:$PATH" CLAUDE_PROJECT_DIR="$P" bash "$P/.delta-11/hooks/abrir-painel.sh" </dev/null); CODIGO=$?
[ "$CODIGO" = "0" ] && esperar_abertura && ok "entrada vazia (Passo 0, </dev/null) e marca com 9 h: abre de novo" || err "nao reabriu apos 8 h com entrada vazia (exit=$CODIGO)"

envelhecer "$P/.delta-11/ativacoes/.painel-aberto" 9; rm -f "$P/aberturas.txt"
touch "$P/.delta-11/.nao-abrir-painel"
rodar "$P" "$P" "$CMD_FALSO" '{"hook_event_name":"SessionStart","cwd":"'"$P"'"}'
sleep 0.5
[ "$CODIGO" = "0" ] && [ ! -f "$P/aberturas.txt" ] && ok ".nao-abrir-painel desliga a abertura" || err "abriu mesmo com .nao-abrir-painel"

Q=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$Q")
rodar "$Q" "$Q" "PATH=\"$P/bin-falso:\$PATH\"; bash \"$Q/.delta-11/hooks/abrir-painel.sh\"" 'nao e json'
[ "$CODIGO" = "0" ] && ok "sem painel.html e entrada malformada: exit 0" || err "exit=$CODIGO"

resultado_final "abrir-painel.sh"
