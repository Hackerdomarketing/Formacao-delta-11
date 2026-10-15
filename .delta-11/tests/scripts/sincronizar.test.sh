#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do sincronizar.sh (v6.3 — C-051 a C-058, C-147, C-150, D1)
# ════════════════════════════════════════════════════════════════
#
# Tudo acontece numa pasta temporária: HOME, registro (DELTA11_REGISTRY),
# fonte falsa e projetos falsos (DELTA11_SEARCH_PATHS). Nunca toca nos
# projetos reais nem no ~/.delta-11-registry.json real (C-129).
#
#   1. --dry-run NÃO grava NADA (impressão digital de todos os arquivos
#      antes e depois é idêntica) — inclusive skills (C-051)
#   2. --diff também não grava nada
#   3. origem vazia no registro → para sem copiar (C-055)
#   4. rodada real:
#      - .modo-selo do projeto é preservado; projeto sem ele recebe o da fonte (C-052, D1)
#      - scripts vão para .delta-11/scripts/ e saem da raiz (C-053)
#      - disparar.sh (listado em removidos.txt) é apagado (C-054)
#      - pastas inteiras chegam, inclusive tests/operativos (C-054)
#      - cópias/clones do sistema e sistema-atual NÃO são tocados (C-057)
#      - hooks do Δ-11 trocados pelos do modelo, hooks do usuário mantidos (C-058)
#      - .gitignore ganha a proteção de segredos (C-147)
#      - dados do projeto (kanban, memória) ficam intactos
#      - projeto do registro fora das pastas varridas também é sincronizado (C-049)
# ════════════════════════════════════════════════════════════════

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SINCRONIZAR="$RAIZ/sincronizar.sh"

if [ ! -f "$SINCRONIZAR" ]; then
    echo -e "${GREEN}[SKIP]${NC} sincronizar.sh só existe na distribuição oficial (isto é um projeto)"
    exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
    echo -e "${GREEN}[SKIP]${NC} jq não instalado (o sincronizar.sh precisa dele)"
    exit 0
fi

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/delta11-sincronizar-test-XXXXXX")"
SANDBOX="$(cd "$SANDBOX" && pwd -P)"
cleanup() { [ -n "$SANDBOX" ] && [ -d "$SANDBOX" ] && rm -rf "$SANDBOX"; }
trap cleanup EXIT

export HOME="$SANDBOX/home"
export DELTA11_REGISTRY="$HOME/registro.json"
export DELTA11_SEARCH_PATHS="$HOME/busca"
mkdir -p "$HOME/.claude/skills" "$DELTA11_SEARCH_PATHS"

# ─── Fonte falsa (mínima, com os scripts reais) ───────────────
FONTE="$SANDBOX/fonte"
mkdir -p "$FONTE/.delta-11/operativos" "$FONTE/.delta-11/hooks" "$FONTE/.delta-11/templates" \
         "$FONTE/.delta-11/tests/operativos" "$FONTE/skills/skill-de-teste"
for s in sincronizar.sh task-done.sh monitor-delta11.sh vigilante.sh; do cp "$RAIZ/$s" "$FONTE/$s"; done
cp "$RAIZ/.delta-11/removidos.txt" "$FONTE/.delta-11/removidos.txt"
echo "# CLAUDE v6.3" > "$FONTE/CLAUDE.md"
echo "# ATLAS v6.3" > "$FONTE/.delta-11/operativos/ATLAS.md"
echo "print('vigia')" > "$FONTE/.delta-11/hooks/vigia-novo.py"
echo "echo teste" > "$FONTE/.delta-11/tests/operativos/dispatch-ap3.test.sh"
echo "<html>painel</html>" > "$FONTE/.delta-11/painel.html"
echo "automatico" > "$FONTE/.delta-11/.modo-selo"
echo "# Gotchas do Projeto" > "$FONTE/.delta-11/templates/gotchas-inicial.md"
echo "skill nova" > "$FONTE/skills/skill-de-teste/SKILL.md"
cat > "$FONTE/.delta-11/templates/settings-hooks.json" <<'EOF'
{"hooks":{"Stop":[{"matcher":"","hooks":[{"type":"command","command":"python3 \"$CLAUDE_PROJECT_DIR/.delta-11/hooks/release-locks.py\"","timeout":5}]}],
 "PreToolUse":[{"matcher":"Write","hooks":[{"type":"command","command":"python3 \"$CLAUDE_PROJECT_DIR/.delta-11/hooks/vigia-novo.py\"","timeout":5}]}]}}
EOF

# ─── Projetos falsos ──────────────────────────────────────────
PA="$DELTA11_SEARCH_PATHS/projeto-a"
mkdir -p "$PA/.delta-11/memoria" "$PA/.delta-11/scripts" "$PA/.claude"
echo "manual" > "$PA/.delta-11/.modo-selo"
echo "# meu kanban com tarefas" > "$PA/.delta-11/kanban.md"
echo "minha memoria" > "$PA/.delta-11/memoria/ATLAS-produto.md"
printf '#!/bin/bash\n# FORMAÇÃO Δ-11 — task-done antigo\n' > "$PA/task-done.sh"
printf '#!/bin/bash\n# FORMAÇÃO Δ-11 — disparar\n' > "$PA/disparar.sh"
printf '#!/bin/bash\n# FORMAÇÃO Δ-11 — disparar\n' > "$PA/.delta-11/scripts/disparar.sh"
printf '#!/bin/bash\n# script do usuario, nao e do sistema\n' > "$PA/vigilante.sh"
cat > "$PA/.claude/settings.json" <<'EOF'
{"model":"opus","hooks":{"Stop":[{"matcher":"","hooks":[
  {"type":"command","command":"node .delta-11/hooks/release-locks.js"},
  {"type":"command","command":"node .delta-11/hooks/release-locks.js"},
  {"type":"command","command":"say terminei"}]}],
 "PostToolUse":[{"matcher":"Write","hooks":[{"type":"command","command":"python3 .delta-11/hooks/vigia-velho-errado.py || python .delta-11/hooks/vigia-velho-errado.py"}]}]}}
EOF

PB="$SANDBOX/fora-da-varredura/projeto-b"     # só no registro (C-049)
mkdir -p "$PB/.delta-11"

COPIA="$DELTA11_SEARCH_PATHS/copia-do-sistema"  # C-057
mkdir -p "$COPIA/.delta-11" "$COPIA/boilerplate-delta-11-nextjs"
CLONE="$DELTA11_SEARCH_PATHS/clone-do-sistema"
mkdir -p "$CLONE/.delta-11"; echo "# changelog" > "$CLONE/.delta-11/CHANGELOG.md"; echo "#!/bin/bash" > "$CLONE/sincronizar.sh"
ANTIGO="$DELTA11_SEARCH_PATHS/projeto-de-instalador-antigo"  # projeto real com sobras do sistema na raiz
mkdir -p "$ANTIGO/.delta-11" "$ANTIGO/src"; echo "# changelog" > "$ANTIGO/.delta-11/CHANGELOG.md"
printf '#!/bin/bash\n# FORMAÇÃO Δ-11 — Sincronizar (cópia velha)\n' > "$ANTIGO/sincronizar.sh"
printf '#!/bin/bash\n# instalador do usuario, sem relacao com o sistema\n' > "$ANTIGO/instalar.sh"
echo "export const app = 1" > "$ANTIGO/src/app.ts"
ATUAL="$DELTA11_SEARCH_PATHS/construcao-delta-11/sistema-atual"
mkdir -p "$ATUAL/.delta-11"

cat > "$DELTA11_REGISTRY" <<EOF
{"version":"6.2","source":"$FONTE","projects":["$PB","$SANDBOX/nao-existe-mais"]}
EOF

impressao_digital() {
    # Lista de TODOS os arquivos e pastas com tamanho, data de modificação,
    # permissões e conteúdo — qualquer gravação muda o resultado.
    python3 - "$SANDBOX" <<'PY_DIGITAL'
import hashlib, os, sys
raiz = sys.argv[1]
h = hashlib.sha256()
for pasta, subpastas, arquivos in os.walk(raiz):
    subpastas.sort()
    for nome in sorted(subpastas + arquivos):
        caminho = os.path.join(pasta, nome)
        st = os.lstat(caminho)
        h.update(("%s|%d|%d|%o\n" % (os.path.relpath(caminho, raiz), st.st_size, st.st_mtime_ns, st.st_mode)).encode())
        if os.path.isfile(caminho) and not os.path.islink(caminho):
            with open(caminho, "rb") as f:
                h.update(f.read())
print(h.hexdigest())
PY_DIGITAL
}

# ─── 1. DRY RUN não grava nada ────────────────────────────────
ANTES="$(impressao_digital)"
SAIDA_DRY="$(bash "$FONTE/sincronizar.sh" --dry-run 2>&1)" || err "--dry-run terminou com erro"
DEPOIS="$(impressao_digital)"
if [ "$ANTES" = "$DEPOIS" ]; then
    ok "1: --dry-run não criou, mudou nem apagou nenhum arquivo"
else
    err "1: --dry-run ALTEROU arquivos"
fi
[ -d "$HOME/.claude/skills/skill-de-teste" ] && err "1: --dry-run copiou skill para ~/.claude/skills (C-051)" || ok "1: --dry-run não copiou skills (C-051)"
grep -q "DRY RUN — Nenhum arquivo foi alterado" <<< "$SAIDA_DRY" && ok "1: relatório do dry-run confirma" || err "1: relatório do dry-run ausente"
grep -q "disparar.sh.*seria apagado" <<< "$SAIDA_DRY" && ok "1: dry-run mostra o que seria apagado" || err "1: dry-run não mostrou remoções"

# ─── 2. --diff não grava nada ─────────────────────────────────
bash "$FONTE/sincronizar.sh" --diff > /dev/null 2>&1 || err "--diff terminou com erro"
[ "$ANTES" = "$(impressao_digital)" ] && ok "2: --diff não alterou nada" || err "2: --diff ALTEROU arquivos"

# ─── 3. Origem vazia ──────────────────────────────────────────
REG_VAZIO="$SANDBOX/registro-vazio.json"
echo '{"projects":[]}' > "$REG_VAZIO"
if DELTA11_REGISTRY="$REG_VAZIO" bash "$FONTE/sincronizar.sh" > /dev/null 2>&1; then
    err "3: seguiu mesmo sem fonte no registro (C-055)"
else
    ok "3: sem fonte no registro, para antes de copiar (C-055)"
fi

# ─── 4. Rodada real ───────────────────────────────────────────
SAIDA="$(bash "$FONTE/sincronizar.sh" 2>&1)" || { err "4: rodada real terminou com erro"; echo "$SAIDA" | tail -20; }

[ "$(cat "$PA/.delta-11/.modo-selo")" = "manual" ] && ok "4: .modo-selo 'manual' do projeto preservado (C-052)" || err "4: .modo-selo do projeto foi sobrescrito"
[ "$(cat "$PB/.delta-11/.modo-selo" 2>/dev/null)" = "automatico" ] && ok "4: projeto sem .modo-selo recebeu 'automatico' (D1)" || err "4: projeto sem .modo-selo não recebeu o padrão"
[ -x "$PA/.delta-11/scripts/task-done.sh" ] && [ -x "$PA/.delta-11/scripts/monitor-delta11.sh" ] && [ -x "$PA/.delta-11/scripts/vigilante.sh" ] \
    && ok "4: scripts em .delta-11/scripts/ (C-053)" || err "4: scripts não chegaram em .delta-11/scripts/"
[ -e "$PA/task-done.sh" ] && err "4: task-done.sh velho continua na raiz" || ok "4: task-done.sh velho saiu da raiz (C-053)"
[ -f "$PA/vigilante.sh" ] && ok "4: vigilante.sh do USUÁRIO (não é do Δ-11) foi preservado" || err "4: apagou um arquivo do usuário"
[ -e "$PA/disparar.sh" ] || [ -e "$PA/.delta-11/scripts/disparar.sh" ] && err "4: disparar.sh continua no projeto" || ok "4: disparar.sh apagado pela lista removidos.txt (C-054)"
[ -f "$PA/.delta-11/tests/operativos/dispatch-ap3.test.sh" ] && ok "4: tests/operativos chegou ao projeto (C-054)" || err "4: tests/operativos não foi sincronizado"
[ -f "$PA/.delta-11/hooks/vigia-novo.py" ] && ok "4: vigias .py chegam aos projetos" || err "4: vigia .py não chegou"
[ -f "$PB/CLAUDE.md" ] && ok "4: projeto só do registro (fora da varredura) sincronizado (C-049)" || err "4: projeto do registro foi ignorado"

for c in "$COPIA" "$CLONE" "$ATUAL"; do
    [ -e "$c/CLAUDE.md" ] && err "4: cópia do sistema tratada como projeto: $c"
done
ok "4: cópias, clones e sistema-atual não foram tocados (C-057)"
[ -f "$ANTIGO/CLAUDE.md" ] && ok "4: projeto real com sobras do sistema na raiz É sincronizado" || err "4: projeto real com CHANGELOG + sincronizar.sh foi tratado como cópia"
[ -e "$ANTIGO/sincronizar.sh" ] && err "4: sincronizar.sh velho do Δ-11 continua na raiz do projeto" || ok "4: sincronizar.sh velho saiu da raiz do projeto"
[ -f "$ANTIGO/instalar.sh" ] && ok "4: instalar.sh do USUÁRIO (não é do Δ-11) foi preservado" || err "4: apagou um instalar.sh do usuário"
[ -f "$ANTIGO/src/app.ts" ] && ok "4: código do projeto intacto" || err "4: código do projeto sumiu"

S="$PA/.claude/settings.json"
if jq -e '.model == "opus"' "$S" >/dev/null \
   && [ "$(jq '[.. | .command? // empty | select(test("release-locks"))] | length' "$S")" = "1" ] \
   && [ "$(jq '[.. | .command? // empty | select(test("vigia-velho-errado"))] | length' "$S")" = "0" ] \
   && [ "$(jq '[.. | .command? // empty | select(. == "say terminei")] | length' "$S")" = "1" ] \
   && [ "$(jq '[.. | .command? // empty | select(test("vigia-novo"))] | length' "$S")" = "1" ]; then
    ok "4: settings.json — vigias do Δ-11 trocados pelos do modelo, vigia do usuário mantido (C-058)"
else
    err "4: mescla do settings.json errada: $(jq -c '.hooks' "$S")"
fi

grep -Fxq ".env" "$PA/.gitignore" && grep -Fxq "*.pem" "$PA/.gitignore" && grep -Fxq ".delta-11/ativacoes/" "$PA/.gitignore" \
    && ok "4: .gitignore protege segredos e estado de execução (C-147)" || err "4: .gitignore sem proteção"

[ "$(cat "$PA/.delta-11/kanban.md")" = "# meu kanban com tarefas" ] && [ "$(cat "$PA/.delta-11/memoria/ATLAS-produto.md")" = "minha memoria" ] \
    && ok "4: kanban e memória do projeto intactos" || err "4: dados do projeto foram alterados"

if jq -e --arg a "$PA" --arg b "$PB" '(.projects | index($a)) and (.projects | index($b)) and ((.projects | map(test("nao-existe-mais")) | any) | not) and ((.projects | map(test("sistema")) | any) | not)' "$DELTA11_REGISTRY" >/dev/null; then
    ok "4: registro reescrito com a lista real (sem pastas sumidas nem cópias do sistema)"
else
    err "4: lista do registro errada: $(jq -c .projects "$DELTA11_REGISTRY")"
fi

# Segunda rodada: idempotente (nada mais a fazer nos settings)
SAIDA2="$(bash "$FONTE/sincronizar.sh" 2>&1)" || err "segunda rodada terminou com erro"
grep -q "settings.json" <<< "$SAIDA2" && err "segunda rodada mexeu de novo no settings.json" || ok "segunda rodada não mexe no que já está certo"

echo ""
[ "$falhou" -eq 0 ] && { echo -e "${GREEN}OK — sincronizar.sh${NC}"; exit 0; } || { echo -e "${RED}FALTA $falhou item(ns)${NC}"; exit 1; }
