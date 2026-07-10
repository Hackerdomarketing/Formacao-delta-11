#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste da base design-patterns-praticos.md (G3 — F7 + F15)
# ════════════════════════════════════════════════════════════════
#
# Verifica que:
#   F7  — todas as cross-refs a outras bases batem com seções reais
#   F15 — seção Adapter menciona a Regra 14 (não só a Regra 15)
#
# Saída: exit 0 se tudo OK.
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/templates/ → tests/ → .delta-11/ → conhecimento/
BASE="$SCRIPT_DIR/../../conhecimento/design-patterns-praticos.md"

if [ ! -f "$BASE" ]; then
    echo -e "${RED}[FAIL]${NC} base nao encontrada: $BASE"
    exit 1
fi

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC} $1"; }
err() { echo -e "  ${RED}[FAIL]${NC} $1"; falhou=$((falhou + 1)); }

# ─── F7: cross-refs válidas ──────────────────────────────────
# Extrai todas as refs `arquivo §N` e checa que §N existe no arquivo alvo.
echo "[F7] cross-refs:"
refs_validas=$(python3 - "$BASE" << 'PY'
import re, sys, pathlib
base_path = pathlib.Path(sys.argv[1])
content = base_path.read_text()
root = base_path.parent
protocolos = pathlib.Path('.delta-11/protocolos')

# Captura refs em formato de cross-ref de SEÇÃO: "nome-arquivo §N" OU "nome-arquivo"
# seguido de seção. Ignora menções dentro de path de skill (começa com `~/.claude/skills/`).
# Estrategia: dividir o texto por linhas e capturar refs que aparecem como
# "ARQUIVO §N" em contexto de tabela/lista, NAO dentro de paths `~/.claude/skills/`.

refs = set()
# Padrao 1: refs com secao numerica (lookahead barra hifem tambem — evita match em "design-patterns-padroes-...")
for match in re.finditer(r'(?<![\w\-/.])([a-z][a-z0-9-]*-patterns?)(?: §(\d+))?(?![-\w])', content):
    start = match.start()
    # Ignorar se dentro de path de skill (200 chars antes OU depois)
    around = content[max(0, start-200):start+200]
    if '~/.claude/skills/' in around or '.claude/skills/' in around:
        continue
    refs.add((match.group(1), match.group(2)))
# Padrao 2: refs em tabela "| ... nome-patterns §N |"
for match in re.finditer(r'\|\s*([a-z-]+-patterns?)\s*§(\d+)\s*\|', content):
    refs.add((match.group(1), match.group(2)))
# backend-integracao e regras-codigo sao refs conhecidas
for match in re.finditer(r'(backend-integracao|regras-codigo)(?: §(\d+))?', content):
    refs.add((match.group(1), match.group(2)))

# Filtrar refs com arquivo vazio (defensivo)
refs = {(name, sec) for name, sec in refs if name}

total = 0
ok_count = 0
for ref, sec in sorted(refs, key=lambda x: (x[0], x[1] or '')):
    total += 1
    candidates = [
        root / f'{ref}.md',
        root / f'{ref}-patterns.md',
        protocolos / f'{ref}.md',
    ]
    found_file = None
    for cand in candidates:
        if cand.exists():
            found_file = cand
            break
    if not found_file:
        print(f'FALTA: {ref}')
        continue
    if sec:
        text = found_file.read_text()
        if re.search(rf'^## {re.escape(sec)}\.', text, re.MULTILINE):
            ok_count += 1
        else:
            print(f'SECAO_NAO_ENCONTRADA: {ref} §{sec}')
    else:
        ok_count += 1
print(f'TOTAL:{total} OK:{ok_count}')
PY
)
total=$(echo "$refs_validas" | grep "^TOTAL:" | cut -d: -f2)
ok_count=$(echo "$refs_validas" | grep "^TOTAL:" | cut -d: -f3)
falhas_ref=$(echo "$refs_validas" | grep -E "^(FALTA|SECAO_NAO_ENCONTRADA):" || true)

if [ -n "$falhas_ref" ]; then
    err "F7 cross-refs quebradas:"
    echo "$falhas_ref" | sed 's/^/        /'
else
    ok "F7 cross-refs: $ok_count/$total validas"
fi

# ─── F15: seção Adapter menciona Regra 14 ────────────────────
echo ""
echo "[F15] Adapter cita Regra 14:"
# Pegar a secao Adapter: tudo entre "### Adapter" e a proxima "### " ou "## "
adapter_section=$(awk '/^### Adapter/{flag=1; next} /^### /{flag=0} flag' "$BASE")
if echo "$adapter_section" | grep -q "Regra 14\|REGRA 14"; then
    ok "F15 secao Adapter cita Regra 14"
else
    err "F15 secao Adapter NAO cita Regra 14 (sequencia Regra 14 -> Regra 15 -> Adapter quebrada)"
fi

# Tambem verificar que o fluxo explicito existe
if echo "$adapter_section" | grep -q "ferramentas-do-projeto"; then
    ok "F15 Adapter referencia ferramentas-do-projeto.md (Regra 14)"
else
    err "F15 Adapter nao referencia o path da Regra 14"
fi

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} design-patterns-praticos: F7 + F15 verificados"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi