#!/usr/bin/env bash
# Teste do REGISTRO dos vigias — Delta-11 v6.3
# Confere templates/settings-hooks.json (vai para os projetos) e o
# .claude/settings.json da fonte (C-011: os dois registram os mesmos vigias).
# Cobre C-001 (sem "|| python"; código 2 sobrevive ao comando exato),
# C-002, C-003, C-004, C-005/D30, C-006/D25, C-007, C-008, C-009, C-040, N-001.
set -uo pipefail
source "$(cd "$(dirname "$0")" && pwd)/apoio-testes-vigias.sh"
SETTINGS_FONTE="$(cd "$APOIO_DIR/../../.." && pwd)/.claude/settings.json"

for f in "$SETTINGS" "$SETTINGS_FONTE"; do
    json_valido "$f" && ok "JSON valido: ${f##*/Formacao-delta-11/}" || err "JSON invalido: $f"
done

python3 - "$SETTINGS" "$SETTINGS_FONTE" "$HOOKS_DIR" <<'PY'
import json, os, re, sys
template, fonte, pasta = sys.argv[1], sys.argv[2], sys.argv[3]
t = json.load(open(template, encoding="utf-8"))
f = json.load(open(fonte, encoding="utf-8"))
falhas = []
def checar(condicao, texto):
    print(("  OK     " if condicao else "  FALTA  ") + texto)
    if not condicao:
        falhas.append(texto)

checar(t["hooks"] == f["hooks"], "C-011: .claude/settings.json da fonte registra exatamente os mesmos hooks do template")

registros = []   # (evento, matcher, arquivo, comando, timeout)
for evento, grupos in t["hooks"].items():
    for g in grupos:
        for h in g["hooks"]:
            m = re.search(r"/\.delta-11/hooks/([^\"/]+)\"$", h["command"])
            registros.append((evento, g.get("matcher", ""), m.group(1) if m else None, h["command"], h.get("timeout")))

no_disco = sorted(x for x in os.listdir(pasta) if x.rsplit(".", 1)[-1] in ("py", "js", "sh") and not x.startswith("_"))  # _comum.py etc. são apoio, não vigias
registrados = sorted({r[2] for r in registros if r[2]})
checar(set(no_disco) == set(registrados),
       "todo vigia de .delta-11/hooks/ esta registrado e vice-versa (%d arquivos)" % len(no_disco))
for faltando in sorted(set(no_disco) - set(registrados)):
    checar(False, "NAO registrado: " + faltando)

padrao = re.compile(r'^(python3|node|bash) "\$CLAUDE_PROJECT_DIR/\.delta-11/hooks/[A-Za-z0-9_.-]+"$')
checar(all(padrao.match(r[3]) for r in registros),
       'C-001/C-006: todo comando e "<python3|node|bash> \\"$CLAUDE_PROJECT_DIR/.delta-11/hooks/X\\"" (sem "|| python", sem caminho relativo)')
checar(all(("python3" in r[3]) == r[3].endswith('.py"') for r in registros), ".py roda com python3, .js com node, .sh com bash")

esperado = {"validar-contratos-fim-fase.py": 120, "validar-deploy.py": 120}
checar(all(r[4] == esperado.get(r[2], 5) for r in registros),
       "C-005/D30: timeouts em SEGUNDOS (5; 120 para validar-contratos-fim-fase e validar-deploy)")

def eventos(arquivo):
    return {r[0] for r in registros if r[2] == arquivo}
def matchers(evento, arquivo):
    return [r[1] for r in registros if r[0] == evento and r[2] == arquivo]

checar(all(r[1] != "SessionStart" for r in registros if r[0] == "PreToolUse"), "C-002: nenhum matcher \"SessionStart\" dentro de PreToolUse")
for arq in ("worktree-prune.py", "3-tentativas-shield.py", "gc-locks.py", "abrir-painel.sh"):
    checar("SessionStart" in eventos(arq), "%s registrado em SessionStart" % arq)
checar(any("Agent" in m for m in matchers("PreToolUse", "3-tentativas-shield.py")),
       "C-002: 3-tentativas-shield tambem em PreToolUse Agent|Task (no SessionStart o codigo 2 nao bloqueia)")
checar(eventos("brief-preservado.py") == {"PostToolUse"}, "C-003: brief-preservado so em PostToolUse")
checar(matchers("PreToolUse", "pre-despacho.py") == ["Agent|Task"], 'C-004: pre-despacho com matcher "Agent|Task"')
checar(matchers("PreToolUse", "anti-autocompact.py") == ["Edit|Write|Agent|Task|Bash"], "anti-autocompact cobre Agent")
checar(any("Bash" in m.split("|") for m in matchers("PreToolUse", "topologia-deploy.py")), "C-040: topologia-deploy vigia Bash")
checar(eventos("on-stop.sh") == {"Stop", "SessionEnd"}, "C-007: on-stop em Stop (so renova pulso) e SessionEnd (encerramento)")
checar(eventos("release-locks.js") == {"SubagentStop", "SessionEnd"}, "C-007/C-008: release-locks em SubagentStop e SessionEnd, nao em Stop")
checar(sum(1 for r in registros if r[2] == "release-locks.js") == 2, "C-009: release-locks registrado uma vez por evento")
checar(eventos("fim-subagente.sh") == {"SubagentStop"}, "D32: fim-subagente em SubagentStop")
checar(eventos("pre-compact.sh") == {"PreCompact", "SessionStart"} and matchers("SessionStart", "pre-compact.sh") == ["compact"],
       "C-033: pre-compact em PreCompact e SessionStart \"compact\"")
checar(eventos("validar-deploy.py") == {"UserPromptSubmit"}, "validar-deploy em UserPromptSubmit")
checar(all("~/.claude/skills" in p for p in t["permissions"]["allow"]),
       "permissoes de leitura das skills com ~/ (sem caminho pessoal /Users/...)")

duplicados = {(r[0], r[1], r[2]) for r in registros if [(x[0], x[1], x[2]) for x in registros].count((r[0], r[1], r[2])) > 1}
checar(not duplicados, "nenhum registro duplicado (mesmo evento, matcher e vigia)")
sys.exit(1 if falhas else 0)
PY
[ $? -eq 0 ] && ok "conferencia do registro" || err "conferencia do registro falhou (ver FALTA acima)"

# ── C-001 de verdade: o código 2 sobrevive ao COMANDO EXATO do registro ──
P=$(novo_projeto) || exit 1; PASTAS_TEMP+=("$P")
EVENTO_EDIT='{"hook_event_name":"PreToolUse","session_id":"S1","cwd":"'"$P"'","tool_name":"Edit","tool_input":{"file_path":"'"$P"'/src/a.ts","old_string":"a","new_string":"b"}}'

# (a) Cada vigia de PreToolUse/UserPromptSubmit trocado por um dublê que lê o stdin e sai com 2:
#     se algum comando perder o 2 (ex.: "|| python"), o teste acusa.
DUBLE_PY=$'import sys\nsys.stdin.read()\nsys.stderr.write("duble bloqueou\\n")\nsys.exit(2)\n'
perdidos=0; total=0
while IFS=$'\t' read -r evento arquivo comando; do
    [ -n "$arquivo" ] || continue
    total=$((total + 1))
    cp "$HOOKS_DIR/$arquivo" "$P/.delta-11/hooks/$arquivo.original"
    case "$arquivo" in
        *.py) printf '%s' "$DUBLE_PY" > "$P/.delta-11/hooks/$arquivo" ;;
        *.js) printf 'process.stdin.resume();process.stdin.on("end",()=>{process.stderr.write("duble\\n");process.exit(2)});\n' > "$P/.delta-11/hooks/$arquivo" ;;
        *.sh) printf 'cat >/dev/null\necho duble >&2\nexit 2\n' > "$P/.delta-11/hooks/$arquivo" ;;
    esac
    rodar "$P" "$P" "$comando" "$EVENTO_EDIT"
    [ "$CODIGO" = "2" ] || { perdidos=$((perdidos + 1)); err "comando de $arquivo ($evento) terminou com $CODIGO em vez de 2"; }
    mv "$P/.delta-11/hooks/$arquivo.original" "$P/.delta-11/hooks/$arquivo"
done < <(python3 - "$SETTINGS" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
vistos = set()
for evento in ("PreToolUse", "UserPromptSubmit"):
    for g in d["hooks"].get(evento, []):
        for h in g["hooks"]:
            arq = re.search(r"/hooks/([^\"/]+)\"$", h["command"]).group(1)
            if (evento, arq) not in vistos:
                vistos.add((evento, arq))
                print("%s\t%s\t%s" % (evento, arq, h["command"]))
PY
)
[ "$perdidos" -eq 0 ] && [ "$total" -gt 0 ] && ok "C-001: os $total comandos de bloqueio devolvem o codigo 2 do vigia via sh -c" || err "$perdidos de $total comandos perdem o codigo 2"

# (b) Vigia REAL, comando exato: check-lock.js bloqueia edição de arquivo travado por outro agente
mkdir -p "$P/.delta-11/locks/src--a.ts.lock"; printf 'AGENTE: FRONT\nTAREFA: T-001\n' > "$P/.delta-11/locks/src--a.ts.lock/meta"
rodar "$P" "$P" "$(comando_do_registro PreToolUse check-lock.js)" "$EVENTO_EDIT"
[ "$CODIGO" = "2" ] && ok "vigia real check-lock.js pelo comando do registro: exit 2 (motivo: ${ERRO:0:60}...)" || err "check-lock real terminou com $CODIGO"

# (c) Vigia REAL em Python, comando exato: pre-criacao-arquivo.py barra o "caso Kimi"
EVENTO_KIMI='{"hook_event_name":"PreToolUse","session_id":"S1","cwd":"'"$P"'","tool_name":"Write","tool_input":{"file_path":"'"$P"'/docs/configuracao-kimi-moonshot.md","content":"# chave"}}'
rodar "$P" "$P" "$(comando_do_registro PreToolUse pre-criacao-arquivo.py)" "$EVENTO_KIMI"
[ "$CODIGO" = "2" ] && ok "vigia real pre-criacao-arquivo.py pelo comando do registro: exit 2" || err "pre-criacao-arquivo real terminou com $CODIGO"

# (d) Prova do defeito antigo: o mesmo bloqueio com "|| python" perde o 2
if ! command -v python >/dev/null 2>&1; then
    rodar "$P" "$P" "python3 \"\$CLAUDE_PROJECT_DIR/.delta-11/hooks/pre-criacao-arquivo.py\" || python \"\$CLAUDE_PROJECT_DIR/.delta-11/hooks/pre-criacao-arquivo.py\"" "$EVENTO_KIMI"
    [ "$CODIGO" != "2" ] && ok "controle: o formato antigo \"|| python\" terminaria com $CODIGO (bloqueio perdido)" || err "controle inesperado"
fi

resultado_final "registro dos vigias"
