#!/usr/bin/env bash
# Teste do vigia regenerar-contratos.py (v6.3 — D31, C-037, C-038, C-130)
source "$(dirname "$0")/_ajudante-hooks-python.sh" regenerar-contratos
checagens_basicas
if grep -qE '"--print"|claude_bin|Popen' "$HOOK"; then err "ainda dispara 'claude --print' escondido (C-037)"; else ok "nao dispara nenhum 'claude --print' (D31)"; fi
if grep -q "impacto-" "$HOOK"; then err "usa o nome antigo impacto-AGENTE (C-038)"; else ok "nome unico do aviso: contrato-alterado-AGENTE (C-038)"; fi

novo_projeto
D="$TEST_DIR/.delta-11"
post() { evento hook_event_name=PostToolUse tool_name="$1" "tool_input.file_path=$2"; }
echo "# PC v1" > "$D/memoria/project-core.md"
echo ok > "$D/ativacoes/ack-BACK.txt"; echo ok > "$D/ativacoes/ack-CRONOS.txt"

espera 0 "project-core alterado: exit 0 (so avisa)" "$(post Edit "$D/memoria/project-core.md")"
[ -f "$D/ativacoes/contratos-desatualizados.txt" ] && ok "grava ativacoes/contratos-desatualizados.txt" || err "sem contratos-desatualizados.txt"
grep -q "hash_novo: [0-9a-f]\{64\}" "$D/ativacoes/contratos-desatualizados.txt" 2>/dev/null && ok "aviso traz o hash novo" || err "aviso sem hash"
grep -q "alterado_em: 20" "$D/ativacoes/contratos-desatualizados.txt" 2>/dev/null && ok "aviso traz a hora" || err "aviso sem hora"
[ -f "$D/ativacoes/contrato-alterado-BACK.txt" ] && ok "avisa o executor ativo (contrato-alterado-BACK.txt)" || err "nao avisou BACK"
[ ! -f "$D/ativacoes/contrato-alterado-CRONOS.txt" ] && ok "CRONOS nao recebe aviso individual (usa o geral)" || err "avisou CRONOS individualmente"
[ -f "$D/.contract-hash" ] && ok "grava .contract-hash" || err "sem .contract-hash"
[ ! -d "$D/.contract-backup" ] && ok "nao faz backup/copia de testes (D31: so avisa)" || err "ainda faz backup"
log_contem "\[regenerar-contratos\] \[MAIN\] contrato alterado"

rm -f "$D/ativacoes/contratos-desatualizados.txt"
espera 0 "mesmo conteudo de novo: nada a fazer" "$(post Write "$D/memoria/project-core.md")"
[ ! -f "$D/ativacoes/contratos-desatualizados.txt" ] && ok "hash igual: nao recria o aviso" || err "recriou aviso com hash igual"

echo "GET /api/users" > "$D/memoria/project-core/contratos.md"
espera 0 "fatia memoria/project-core/contratos.md alterada" "$(post Write "$D/memoria/project-core/contratos.md")"
[ -f "$D/ativacoes/contratos-desatualizados.txt" ] && ok "fatia alterada tambem gera o aviso" || err "fatia ignorada"

rm -f "$D/ativacoes/contratos-desatualizados.txt"
espera 0 "outro arquivo da memoria: ignora" "$(post Write "$D/memoria/BACK-produto.md")"
[ ! -f "$D/ativacoes/contratos-desatualizados.txt" ] && ok "arquivo que nao e contrato nao gera aviso" || err "aviso falso"

# Usa a .delta-11 do ARQUIVO EDITADO, mesmo com o cwd em outro lugar (C-037)
OUTRO="$(mktemp -d "${TMPDIR:-/tmp}/delta11-teste-XXXXXX")"
mkdir -p "$OUTRO/.delta-11/memoria" "$OUTRO/.delta-11/ativacoes"
echo "# outro" > "$OUTRO/.delta-11/memoria/project-core.md"
espera 0 "project-core de outra pasta (caminho absoluto)" "$(post Edit "$OUTRO/.delta-11/memoria/project-core.md")"
[ -f "$OUTRO/.delta-11/ativacoes/contratos-desatualizados.txt" ] && ok "aviso gravado na .delta-11 do arquivo editado" || err "aviso no lugar errado"
case "$OUTRO" in */delta11-teste-*) rm -rf "$OUTRO" ;; esac
fim
