#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste CONSOLIDADO dos vigias Python — Delta-11 v6.3 (2026-10-14)
# (nome mantido por compatibilidade; cobre os 25 vigias Python)
#
# 1. Roda o teste de cada vigia Python (todos em projeto temporario).
# 2. Confere o utilitario comum (_comum.py) e o .config-limites.json (D36).
# 3. Confere o REGISTRO de cada vigia em templates/settings-hooks.json:
#    evento certo, matcher certo, comando
#    python3 "$CLAUDE_PROJECT_DIR/.delta-11/hooks/X.py" sem "|| python"
#    (C-001, C-002, C-006) e tempo-limite em segundos (D30).
#    O registro e da area 01 (settings); este teste so confere.
#    D11_SETTINGS_HOOKS=caminho troca o arquivo conferido (integracao).
# ════════════════════════════════════════════════════════════════
set -u
VERDE='\033[0;32m'; VERMELHO='\033[0;31m'; SEM_COR='\033[0m'
DIR="$(cd "$(dirname "$0")" && pwd)"
DELTA="$(cd "$DIR/../.." && pwd)"
falhou=0
ok()  { echo -e "  ${VERDE}[OK]${SEM_COR}   $1"; }
err() { echo -e "  ${VERMELHO}[FALHA]${SEM_COR} $1"; falhou=$((falhou + 1)); }

VIGIAS=(
  3-tentativas-shield anti-autocompact anti-stash brief-preservado contraposicao-checker
  contratos-minimos dia1-badal-checker fase-consciencia-checker fase-descanso-checker
  fase-ritmo-checker forca-despacho gc-locks guarda-worktree pre-criacao-arquivo
  pre-despacho pre-leitura pre-selo produto-atualizado regenerar-contratos shield-aprovado
  topologia-deploy urls-validas validar-arquitetura-vs-modelos validar-contratos-fim-fase
  validar-deploy worktree-prune
)

echo "[1] testes de cada vigia"
for v in "${VIGIAS[@]}"; do
    if [ -f "$DIR/$v.test.sh" ]; then t=(bash "$DIR/$v.test.sh")
    elif [ -f "$DIR/$v.test.py" ]; then t=(python3 "$DIR/$v.test.py")
    else err "teste AUSENTE para $v"; continue; fi
    if "${t[@]}" >/dev/null 2>&1; then ok "$v"; else err "$v FALHOU (rode: ${t[*]})"; fi
done

echo "[2] utilitario comum e limites"
[ -f "$DELTA/hooks/_comum.py" ] && python3 -m py_compile "$DELTA/hooks/_comum.py" 2>/dev/null && ok "_comum.py existe e compila" || err "_comum.py ausente ou quebrado"
rm -rf "$DELTA/hooks/__pycache__"
if python3 - "$DELTA/.config-limites.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
esperado = {"brief_max_tokens": 2000, "produto_max_tokens": 500, "paralelo_max": 3, "janela_horas": 4, "lock_horas": 2}
sys.exit(0 if d == esperado else 1)
PY
then ok ".config-limites.json com os valores do D36"; else err ".config-limites.json ausente ou diferente do D36"; fi
if grep -l "utcnow" "$DELTA"/hooks/*.py >/dev/null 2>&1; then err "algum vigia ainda usa datetime.utcnow (C-017)"; else ok "nenhum vigia usa datetime.utcnow (C-017)"; fi

echo "[3] registro em templates/settings-hooks.json"
python3 - "${D11_SETTINGS_HOOKS:-$DELTA/templates/settings-hooks.json}" <<'PY'
import json, sys
ESPERADO = {
    # vigia: (evento, matcher, timeout em segundos)
    "gc-locks": ("SessionStart", "", 5), "worktree-prune": ("SessionStart", "", 5),
    "validar-deploy": ("UserPromptSubmit", "", 120),
    "guarda-worktree": ("PreToolUse", "Edit|Write", 5), "contraposicao-checker": ("PreToolUse", "Edit|Write", 5),
    "pre-selo": ("PreToolUse", "Edit|Write", 5), "validar-contratos-fim-fase": ("PreToolUse", "Edit|Write", 120),
    "validar-arquitetura-vs-modelos": ("PreToolUse", "Edit|Write", 5), "fase-ritmo-checker": ("PreToolUse", "Edit|Write", 5),
    "fase-consciencia-checker": ("PreToolUse", "Edit|Write", 5), "fase-descanso-checker": ("PreToolUse", "Edit|Write", 5),
    "dia1-badal-checker": ("PreToolUse", "Edit|Write", 5), "anti-stash": ("PreToolUse", "Edit|Write", 5),
    "shield-aprovado": ("PreToolUse", "Edit|Write", 5), "urls-validas": ("PreToolUse", "Edit|Write", 5),
    "contratos-minimos": ("PreToolUse", "Edit|Write", 5), "produto-atualizado": ("PreToolUse", "Edit|Write", 5),
    "forca-despacho": ("PreToolUse", "Edit|Write", 5), "pre-criacao-arquivo": ("PreToolUse", "Write", 5),
    "pre-leitura": ("PreToolUse", "Read", 5), "pre-despacho": ("PreToolUse", "Agent|Task", 5),
    "anti-autocompact": ("PreToolUse", "Edit|Write|Agent|Task|Bash", 5),
    "topologia-deploy": ("PreToolUse", "Edit|Write|Bash", 5),
    "regenerar-contratos": ("PostToolUse", "Edit|Write", 5), "brief-preservado": ("PostToolUse", "Edit|Write|Bash", 5),
}
EXTRA = {"3-tentativas-shield": [("SessionStart", ""), ("PreToolUse", "Agent|Task")]}
VERDE, VERMELHO, SEM = "\033[0;32m", "\033[0;31m", "\033[0m"
falhas = 0
def ok(m): print(f"  {VERDE}[OK]{SEM}   {m}")
def err(m):
    global falhas
    falhas += 1
    print(f"  {VERMELHO}[FALHA]{SEM} {m}")
try:
    hooks = json.load(open(sys.argv[1]))["hooks"]
except Exception as e:  # noqa: BLE001
    err(f"settings-hooks.json ilegivel: {e}"); sys.exit(1)
achados = {}
for evento, blocos in hooks.items():
    for bloco in blocos:
        for h in bloco.get("hooks", []):
            cmd = h.get("command", "")
            for nome in list(ESPERADO) + list(EXTRA):
                if f"/{nome}.py" in cmd:
                    achados.setdefault(nome, []).append((evento, bloco.get("matcher", ""), h.get("timeout"), cmd))
for nome, (evento, matcher, tempo) in ESPERADO.items():
    regs = achados.get(nome, [])
    if not regs:
        err(f"{nome}: NAO registrado"); continue
    ev, mt, to, cmd = regs[0]
    erros = []
    if (ev, mt) != (evento, matcher): erros.append(f"evento/matcher {ev}/{mt!r} (esperado {evento}/{matcher!r})")
    if to != tempo: erros.append(f"timeout {to} (esperado {tempo} s)")
    if "|| python" in cmd: erros.append("tem '|| python'")
    if f'python3 "$CLAUDE_PROJECT_DIR/.delta-11/hooks/{nome}.py"' not in cmd: erros.append("comando sem $CLAUDE_PROJECT_DIR")
    if len(regs) > 1: erros.append(f"registrado {len(regs)} vezes")
    (err if erros else ok)(f"{nome}: " + ("; ".join(erros) if erros else f"{evento} {matcher!r} {tempo} s"))
for nome, pares in EXTRA.items():
    regs = {(r[0], r[1]) for r in achados.get(nome, [])}
    faltam = [p for p in pares if p not in regs]
    bons = all("|| python" not in r[3] and "$CLAUDE_PROJECT_DIR" in r[3] for r in achados.get(nome, []))
    (err if faltam or not bons else ok)(f"{nome}: " + (f"faltam {faltam}" if faltam else "SessionStart + PreToolUse Agent|Task"))
sys.exit(1 if falhas else 0)
PY
[ $? -eq 0 ] || falhou=$((falhou + 1))

echo ""
if [ "$falhou" -eq 0 ]; then echo -e "${VERDE}OK — vigias Python v6.3 consolidados${SEM_COR}"; exit 0; fi
echo -e "${VERMELHO}FALHA — $falhou grupo(s)/item(ns)${SEM_COR}"; exit 1
