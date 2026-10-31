#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# TESTE DA DOCUMENTAÇÃO POR MOTOR — v7 (motor multiempresa)
# ════════════════════════════════════════════════════════════════
#
# O que este teste garante:
#   1. As 12 secoes do motor estao MARCADAS no CLAUDE.md (e os marcadores
#      estao equilibrados).
#   2. O CLAUDE.md do motor Claude Code mantem o texto original INTEIRO
#      (as 12 secoes + a metodologia).
#   3. O CLAUDE.md/AGENTS.md dos outros motores SUBSTITUEM as secoes do
#      motor pelas instrucoes daquele motor — e a METODOLOGIA fica intacta.
#   4. O texto original esta guardado em .delta-11/motor/CLAUDE-original.md
#      (nada se perde).
#   5. O hooks.json do Codex MESCLA com o do usuario (nao sobrescreve) e
#      e idempotente.
#
# Uso: bash .delta-11/tests/motores/documentacao.test.sh
set -uo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd -P)"
DELTA="$AQUI/../.."
MOTOR="$DELTA/motor"
VERDE='\033[0;32m'; VERMELHO='\033[0;31m'; NC='\033[0m'
falhou=0
ok()   { echo -e "  ${VERDE}[OK]${NC}   $1"; }
err()  { echo -e "  ${VERMELHO}[FALHA]${NC} $1"; falhou=$((falhou + 1)); }
checar() { if [ "$1" = "0" ]; then ok "$2"; else err "$2"; fi; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/d11-doc-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

CLAUDE="$DELTA/../CLAUDE.md"
ORIGINAL="$MOTOR/CLAUDE-original.md"

echo "Documentacao por motor — teste"
echo ""

# ── (1) Os marcadores existem e estao equilibrados ─────────────────────────
[ -f "$CLAUDE" ]; checar $? "o CLAUDE.md da Formacao existe"
n_ini=$(grep -c "MOTOR:CODIGO-INICIO" "$CLAUDE")
n_fim=$(grep -c "MOTOR:CODIGO-FIM" "$CLAUDE")
[ "$n_ini" = "12" ]; checar $? "as 12 secoes do motor estao marcadas ($n_ini)"
[ "$n_ini" = "$n_fim" ]; checar $? "os marcadores estao equilibrados ($n_ini / $n_fim)"

# ── (2) O original esta guardado ───────────────────────────────────────────
[ -f "$ORIGINAL" ]; checar $? "o CLAUDE.md original esta guardado em motor/CLAUDE-original.md"
orig_linhas=$(wc -l < "$ORIGINAL" | tr -d ' ')
[ "$orig_linhas" -gt 1000 ]; checar $? "o original tem conteudo substancial ($orig_linhas linhas)"

# O original contem as 12 secoes do motor
faltando=0
for s in "⚡ ATIVAÇÃO DELTA-11" "🚧 VOCÊ NÃO É UM AGENTE" "🤖 DISPATCH AUTÔNOMO" \
         "🛡️ VIGIAS AUTOMÁTICOS" "PROTOCOLO DE ATIVAÇÃO" "PROTOCOLO DE INÍCIO DE TAREFA" \
         "PROTOCOLO DE FINALIZAÇÃO DE TAREFA" "PROTOCOLO DE CONTEXTO ESGOTADO" \
         "PROTOCOLO DE DISPATCH DE AGENTES" "ESTRUTURA OBRIGATÓRIA DO PROMPT DE ATIVAÇÃO"; do
    grep -q "$s" "$ORIGINAL" || faltando=$((faltando + 1))
done
[ "$faltando" = "0" ]; checar $? "o original tem as 10 secoes-chave do motor"

# ── (3) O CLAUDE.md por motor ──────────────────────────────────────────────
python3 "$MOTOR/gerar-claude-por-motor.py" claude-code --fonte "$CLAUDE" --saida "$TMP/cc.md" >/dev/null 2>&1
python3 "$MOTOR/gerar-claude-por-motor.py" codex        --fonte "$CLAUDE" --saida "$TMP/cx.md" >/dev/null 2>&1
python3 "$MOTOR/gerar-claude-por-motor.py" kilo         --fonte "$CLAUDE" --saida "$TMP/kc.md" >/dev/null 2>&1
for f in cc cx kc; do
    [ -s "$TMP/$f.md" ]; checar $? "o motor gerou o CLAUDE.md ($f.md)"
done

# A METODOLOGIA sobrevive nos tres
METODOLOGIA="REGRAS INVIOLÁVEIS (as 17 oficiais)|PAINEL DE COMANDO|METODOLOGIA GÊNESIS|COMANDOS OPERACIONAIS|CORREÇÕES E REGRAS APRENDIDAS|PROTOCOLO DE ATUALIZAÇÃO DO SISTEMA"
for f in cc cx kc; do
    r=$(python3 -c "
import sys
t = open('$TMP/$f.md', encoding='utf-8').read()
faltando = [s for s in '$METODOLOGIA'.split('|') if s not in t]
print('OK' if not faltando else 'FALTA: ' + ', '.join(faltando))
")
    [ "$r" = "OK" ]; checar $? "a metodologia esta intacta em $f.md"
done

# O Claude Code mantem as secoes ORIGINAIS do motor
r=$(python3 -c "
t = open('$TMP/cc.md', encoding='utf-8').read()
secoes = ['## 🤖 DISPATCH AUTÔNOMO', '## 🛡️ VIGIAS AUTOMÁTICOS',
          '### ESTRUTURA OBRIGATÓRIA DO PROMPT DE ATIVAÇÃO',
          '## PROTOCOLO DE CONTEXTO ESGOTADO', '## PROTOCOLO DE INÍCIO DE TAREFA']
print('OK' if all(s in t for s in secoes) else 'FALTA')
")
[ "$r" = "OK" ]; checar $? "o Claude Code mantem as secoes originais do motor"

# Os outros motores SUBSTITUEM as secoes do motor
for f in cx kc; do
    r=$(python3 -c "
t = open('$TMP/$f.md', encoding='utf-8').read()
tem_dispatch = '## 🤖 DISPATCH AUTÔNOMO' in t
tem_hooks = '## 🛡️ VIGIAS AUTOMÁTICOS' in t
print('OK' if (not tem_dispatch and not tem_hooks) else 'AINDA TEM')
")
    [ "$r" = "OK" ]; checar $? "as secoes do motor Claude Code foram substituidas em $f.md"
done

# Cada motor tem o seu bloco de orientacao
for par in "cc:Claude Code" "cx:Codex CLI" "kc:Kilo"; do
    arq="${par%%:*}"; nome="${par##*:}"
    grep -q "MOTOR ATIVO: $nome" "$TMP/$arq.md"; checar $? "o bloco do topo diz '$nome' em $arq.md"
done

# ── (4) O AGENTS.md do Codex ───────────────────────────────────────────────
python3 "$MOTOR/codex/gerar-agents-md.py" "$TMP/AGENTS.md" --motor codex >/dev/null 2>&1
[ -s "$TMP/AGENTS.md" ]; checar $? "o AGENTS.md do Codex foi gerado"
grep -q "MOTOR ATIVO: Codex CLI" "$TMP/AGENTS.md"; checar $? "o AGENTS.md tem o bloco do Codex"
grep -q "REGRAS INVIOLÁVEIS (as 17 oficiais)" "$TMP/AGENTS.md"; checar $? "o AGENTS.md tem a metodologia"
[ "$(grep -c 'MOTOR:CODIGO' "$TMP/AGENTS.md")" = "0" ]; checar $? "o AGENTS.md nao tem os marcadores internos"

# ── (5) O hooks.json do Codex MESCLA (nao sobrescreve) ──────────────────────
cat > "$TMP/hooks-usuario.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      { "hooks": [ { "command": "'/caminho/do/usuario/hook.sh' pre-tool-use", "timeout": 10, "type": "command" } ] }
    ]
  }
}
JSON
python3 "$MOTOR/codex/gerar-hooks.py" --mesclar "$TMP/hooks-usuario.json" --saida "$TMP/hooks-1.json" >/dev/null 2>&1
r=$(python3 -c "
import json
d = json.load(open('$TMP/hooks-1.json'))
usuario = delta = 0
for ev, gs in d.get('hooks', {}).items():
    for g in gs:
        for h in g.get('hooks', []):
            c = h.get('command', '')
            if 'do/usuario' in c: usuario += 1
            elif '.delta-11/hooks/' in c: delta += 1
print('OK' if usuario == 1 and delta > 30 else f'usuario={usuario} delta={delta}')
")
[ "$r" = "OK" ]; checar $? "o hooks.json MESCLA: o hook do usuario foi preservado e os do Δ-11 entraram"

# Idempotente: rodar de novo nao duplica
python3 "$MOTOR/codex/gerar-hooks.py" --mesclar "$TMP/hooks-1.json" --saida "$TMP/hooks-2.json" >/dev/null 2>&1
r=$(python3 -c "
import json
def conta(p):
    d = json.load(open(p)); u = x = 0
    for ev, gs in d.get('hooks', {}).items():
        for g in gs:
            for h in g.get('hooks', []):
                c = h.get('command', '')
                if 'do/usuario' in c: u += 1
                elif '.delta-11/hooks/' in c: x += 1
    return u, x
a, b = conta('$TMP/hooks-1.json'), conta('$TMP/hooks-2.json')
print('OK' if a == b else f'{a} != {b}')
")
[ "$r" = "OK" ]; checar $? "o merge do hooks.json e idempotente (nao duplica)"

# JSON invalido: NAO pode ser alterado
echo '{ nao e json' > "$TMP/hooks-ruim.json"
cp "$TMP/hooks-ruim.json" "$TMP/hooks-ruim-antes.json"
python3 "$MOTOR/codex/gerar-hooks.py" --mesclar "$TMP/hooks-ruim.json" --saida "$TMP/hooks-ruim-saida.json" >/dev/null 2>&1
r=$(cmp -s "$TMP/hooks-ruim.json" "$TMP/hooks-ruim-antes.json" && [ ! -f "$TMP/hooks-ruim-saida.json" ] && echo "OK" || echo "ALTEROU")
[ "$r" = "OK" ]; checar $? "um hooks.json invalido NAO e alterado"

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${VERDE}OK — documentacao por motor${NC}"
    exit 0
else
    echo -e "${VERMELHO}FALHA $falhou item(ns) — documentacao por motor${NC}"
    exit 1
fi
