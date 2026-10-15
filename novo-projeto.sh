#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Iniciar Projeto Novo (v6.3)
# ═══════════════════════════════════════════════════════════════
#
# Copia os arquivos de SISTEMA da Formação Δ-11 para a pasta de um
# projeto e deixa tudo pronto para digitar "d11".
#
# O projeto novo NÃO herda nada da execução de outros projetos (C-048):
# só as pastas de sistema são copiadas; quadro de tarefas (kanban) e
# memória central (project-core) nascem dos modelos, zerados.
#
# Como usar:
#   ./novo-projeto.sh /caminho/para/meu-projeto
#   ./novo-projeto.sh ~/projetos/meu-app
#
# Variável opcional (usada pelos testes):
#   DELTA11_REGISTRY   caminho do registro (padrão ~/.delta-11-registry.json)
#
# ═══════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Fonte = pasta onde este script está
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REGISTRY="${DELTA11_REGISTRY:-$HOME/.delta-11-registry.json}"
APRENDIZADOS="$HOME/.delta-11/aprendizados-entre-projetos.md"

# Pastas de SISTEMA dentro de .delta-11/ (as mesmas do sincronizar.sh)
PASTAS_DE_SISTEMA="operativos protocolos sub-agentes templates conhecimento hooks ferramentas perfis mcp tests"
SCRIPTS_DE_OPERACAO="task-done.sh monitor-delta11.sh vigilante.sh"

# ─── Argumento ─────────────────────────────────────────────────

if [ -z "${1:-}" ]; then
    echo ""
    echo -e "${BOLD}Uso:${NC} ./novo-projeto.sh /caminho/para/meu-projeto"
    echo ""
    echo "Exemplo:"
    echo "  ./novo-projeto.sh ~/projetos/meu-app"
    echo "  ./novo-projeto.sh ./meu-novo-site"
    echo ""
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/CLAUDE.md" ] || [ ! -d "$SCRIPT_DIR/.delta-11/operativos" ]; then
    echo -e "${RED}✗ Este script precisa rodar de dentro da pasta da Formação Δ-11 (onde ficam CLAUDE.md e .delta-11/).${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FORMAÇÃO Δ-11 — Novo Projeto${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── Pasta do projeto ──────────────────────────────────────────

mkdir -p "$1"
TARGET_DIR="$(cd "$1" && pwd -P)"
[ -z "$TARGET_DIR" ] && echo -e "${RED}ERRO: caminho do projeto vazio, abortando${NC}" && exit 1

case "$TARGET_DIR/" in
    "$SCRIPT_DIR/"*)
        echo -e "${RED}✗ O projeto não pode ficar dentro da própria pasta da Formação Δ-11 ($SCRIPT_DIR).${NC}"
        exit 1 ;;
esac
echo -e "  ${GREEN}✓${NC} Pasta do projeto: $TARGET_DIR"

CARIMBO="$(date +%Y%m%d-%H%M%S)"

# Já tem Δ-11? Nada é apagado: a instalação antiga é guardada ao lado (C-150).
if [ -d "$TARGET_DIR/.delta-11" ]; then
    echo -e "${YELLOW}  ⚠ Este projeto já tem a Formação Δ-11 instalada.${NC}"
    echo "  Conteúdo atual de .delta-11/ (será guardado, não apagado):"
    ls -la "$TARGET_DIR/.delta-11" | sed 's/^/    /'
    read -r -p "  Guardar a instalação atual como .delta-11.antigo-$CARIMBO e instalar do zero? (s/n): " OVERWRITE || OVERWRITE=""
    if [[ "$OVERWRITE" != "s" && "$OVERWRITE" != "S" ]]; then
        echo "  Abortado. Nada foi alterado."
        echo "  Dica: para só ATUALIZAR os arquivos de sistema sem perder nada, use o sincronizar.sh."
        exit 1
    fi
    mv "$TARGET_DIR/.delta-11" "$TARGET_DIR/.delta-11.antigo-$CARIMBO"
    [ -f "$TARGET_DIR/CLAUDE.md" ] && mv "$TARGET_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md.antigo-$CARIMBO"
    echo -e "  ${GREEN}✓${NC} Instalação anterior guardada em .delta-11.antigo-$CARIMBO"
fi

# ─── v5.2 (M-17): migração interativa de memórias legadas ───
# Projetos que existiam ANTES do Δ-11 podem ter arquivos .memoria-* na raiz.
# Perguntar antes de mover — nunca mover silenciosamente.
LEGADOS=""
for f in "$TARGET_DIR/.memoria-do-dia.md" "$TARGET_DIR/.memoria-projeto.md" "$TARGET_DIR/.memoria-ultimas-tarefas.md"; do
    [ -f "$f" ] && LEGADOS="$LEGADOS $(basename "$f")"
done
MIGRAR="n"
if [ -n "$LEGADOS" ]; then
    echo -e "${YELLOW}  ⚠ Encontrei arquivos de memória de um sistema antigo na raiz:${NC}"
    echo "   $LEGADOS"
    read -r -p "  Mover para .delta-11/memoria/legado/ ? (s/n): " MIGRAR || MIGRAR="n"
fi

# ─── Copiar SÓ os arquivos de sistema (C-048) ─────────────────

echo "  Copiando arquivos de sistema da Formação Δ-11..."

ORIGEM="$SCRIPT_DIR/.delta-11"
DESTINO="$TARGET_DIR/.delta-11"
mkdir -p "$DESTINO"

copiar_arquivo() {
    # copiar_arquivo <origem-absoluta> <destino-absoluto>
    mkdir -p "$(dirname "$2")"
    cp "$1" "$2"
    [ -x "$1" ] && chmod +x "$2"
    return 0
}

for pasta in $PASTAS_DE_SISTEMA; do
    [ -d "$ORIGEM/$pasta" ] || continue
    while IFS= read -r arquivo; do
        copiar_arquivo "$arquivo" "$DESTINO/${arquivo#"$ORIGEM/"}"
    done < <(find "$ORIGEM/$pasta" -type f ! -name ".DS_Store" ! -name "*.pyc" ! -path "*/__pycache__/*")
done

for rel in painel.html .modo-selo .config-limites.json \
           scratch/README.md evidencias/screenshots/README.md logs/sub-agentes/README.md; do
    [ -f "$ORIGEM/$rel" ] && copiar_arquivo "$ORIGEM/$rel" "$DESTINO/$rel"
done
for f in "$ORIGEM/"CHANGELOG*.md; do
    [ -f "$f" ] && copiar_arquivo "$f" "$DESTINO/$(basename "$f")"
done

# Modo do selo: se a fonte não tiver, o padrão é automático (D1)
[ -f "$DESTINO/.modo-selo" ] || echo "automatico" > "$DESTINO/.modo-selo"

cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"

# ─── Quadro de tarefas e memória central a partir dos MODELOS ──
# Os modelos são as versões limpas guardadas na fonte. Nada de execução
# (activity-log, ativacoes, locks, logs, memórias de agente, planos) vem junto.
for modelo in kanban.md kanban-data.js pulsos-data.js monitor-data.js memoria/project-core.md; do
    if [ -f "$ORIGEM/$modelo" ]; then
        copiar_arquivo "$ORIGEM/$modelo" "$DESTINO/$modelo"
    fi
done
# Fatias do project-core (D6), se a fonte tiver os modelos
if [ -d "$ORIGEM/memoria/project-core" ]; then
    for f in "$ORIGEM/memoria/project-core/"*.md; do
        [ -f "$f" ] && copiar_arquivo "$f" "$DESTINO/memoria/project-core/$(basename "$f")"
    done
fi
if [ ! -f "$DESTINO/kanban-data.js" ]; then
    cat > "$DESTINO/kanban-data.js" << 'EOF'
window.KANBAN_DATA = {
  projeto: "", complexidade: "", fase_atual: "",
  ultima_atualizacao: "", agente_atualizador: "",
  a_fazer: { ATLAS: [], CRONOS: [], FRONT: [], PIXEL: [], FORM: [], BACK: [], ENGINE: [], VAULT: [], SHIELD: [], SCOUT: [] },
  fazendo: [], revisao: [], concluido: [], bloqueado: []
};
EOF
fi
echo -e "  ${GREEN}✓${NC} Quadro de tarefas e memória central criados a partir dos modelos (zerados)"

# gotchas.md desde o dia 1 (v5.4 F5)
if [ ! -f "$DESTINO/memoria/gotchas.md" ] && [ -f "$ORIGEM/templates/gotchas-inicial.md" ]; then
    copiar_arquivo "$ORIGEM/templates/gotchas-inicial.md" "$DESTINO/memoria/gotchas.md"
    echo -e "  ${GREEN}✓${NC} gotchas.md criado em .delta-11/memoria/"
fi

# Memórias legadas (M-17)
if [[ "$MIGRAR" == "s" || "$MIGRAR" == "S" ]]; then
    mkdir -p "$DESTINO/memoria/legado"
    for f in "$TARGET_DIR/.memoria-do-dia.md" "$TARGET_DIR/.memoria-projeto.md" "$TARGET_DIR/.memoria-ultimas-tarefas.md"; do
        [ -f "$f" ] && mv "$f" "$DESTINO/memoria/legado/"
    done
    echo -e "  ${GREEN}✓${NC} Memórias legadas em .delta-11/memoria/legado/"
fi

# ─── Pastas canônicas (vazias, mas presentes desde o dia 1) ────
for pasta in ".delta-11/bugs" ".delta-11/logs/autocritica" ".delta-11/memoria/decisoes" ".delta-11/locks"; do
    mkdir -p "$TARGET_DIR/$pasta"
    [ -f "$TARGET_DIR/$pasta/.gitkeep" ] || : > "$TARGET_DIR/$pasta/.gitkeep"
done
mkdir -p "$DESTINO/ativacoes" "$DESTINO/scratch" "$DESTINO/logs/sub-agentes"
mkdir -p "$TARGET_DIR/docs/comandante"

# ─── Scripts de operação em .delta-11/scripts/ (C-053) ─────────
mkdir -p "$DESTINO/scripts"
for script in $SCRIPTS_DE_OPERACAO; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        cp "$SCRIPT_DIR/$script" "$DESTINO/scripts/$script"
        chmod +x "$DESTINO/scripts/$script"
    fi
done
echo -e "  ${GREEN}✓${NC} Scripts de operação em .delta-11/scripts/ (a raiz do projeto fica limpa)"

# ─── Vigias (hooks) ligados desde o primeiro dia ───────────────
MODELO_SETTINGS="$ORIGEM/templates/settings-hooks.json"
mkdir -p "$TARGET_DIR/.claude"
if [ -f "$MODELO_SETTINGS" ]; then
    if [ ! -f "$TARGET_DIR/.claude/settings.json" ]; then
        cp "$MODELO_SETTINGS" "$TARGET_DIR/.claude/settings.json"
        echo -e "  ${GREEN}✓${NC} Vigias ativados (.claude/settings.json criado do modelo)"
    else
        echo -e "  ${YELLOW}⚠${NC} O projeto já tinha .claude/settings.json — não mexi nele."
        echo "     Rode o sincronizar.sh para trocar os vigias do Δ-11 pelos do modelo (os seus ficam)."
    fi
fi

# ─── .gitignore com proteção de segredos e do estado de execução (C-147) ───
GITIGNORE="$TARGET_DIR/.gitignore"
FALTANDO=""
for linha in ".env" ".env.*" "!.env.example" "*.pem" "*.key" "credentials.json" \
             ".claude/settings.local.json" ".DS_Store" \
             ".delta-11/activity-log.md" ".delta-11/monitor-status.json" ".delta-11/monitor-data.js" \
             ".delta-11/pulsos-data.js" ".delta-11/ativacoes/" ".delta-11/locks/*" "!.delta-11/locks/.gitkeep" \
             ".delta-11/scratch/*" "!.delta-11/scratch/README.md" ".delta-11/logs/sub-agentes/*.log" \
             ".claude/worktrees/" ".delta-11.antigo-*/" "CLAUDE.md.antigo-*" "__pycache__/" "*.pyc"; do
    if [ ! -f "$GITIGNORE" ] || ! grep -Fxq -- "$linha" "$GITIGNORE"; then
        FALTANDO="${FALTANDO}${linha}"$'\n'
    fi
done
if [ -n "$FALTANDO" ]; then
    {
        [ -s "$GITIGNORE" ] && echo ""
        echo "# ─── Formação Δ-11 (v6.3): segredos e estado de execução nunca vão ao GitHub ───"
        printf '%s' "$FALTANDO"
    } >> "$GITIGNORE"
    echo -e "  ${GREEN}✓${NC} .gitignore protege senhas, chaves e o estado de execução"
fi

# ─── Registro central (C-049) ──────────────────────────────────
registrar_projeto() {
    if command -v jq &> /dev/null; then
        if [ ! -f "$REGISTRY" ]; then
            jq -n --arg fonte "$SCRIPT_DIR" '{version: "6.3", source: $fonte, projects: []}' > "$REGISTRY"
        fi
        local tmp
        tmp=$(mktemp "${REGISTRY}.XXXXXX")
        if jq --arg p "$TARGET_DIR" '.projects = (((.projects // []) + [$p]) | unique)' "$REGISTRY" > "$tmp"; then
            mv "$tmp" "$REGISTRY"
            return 0
        fi
        rm -f "$tmp"
        return 1
    elif command -v python3 &> /dev/null; then
        python3 - "$REGISTRY" "$TARGET_DIR" "$SCRIPT_DIR" << 'PY'
import json, os, sys, tempfile
registro, projeto, fonte = sys.argv[1:4]
dados = {"version": "6.3", "source": fonte, "projects": []}
if os.path.exists(registro):
    with open(registro, encoding="utf-8") as f:
        dados = json.load(f)
lista = dados.get("projects") or []
if projeto not in lista:
    lista.append(projeto)
dados["projects"] = sorted(set(lista))
pasta = os.path.dirname(os.path.abspath(registro))
fd, tmp = tempfile.mkstemp(dir=pasta)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
os.replace(tmp, registro)
PY
        return $?
    fi
    return 1
}
if registrar_projeto; then
    echo -e "  ${GREEN}✓${NC} Projeto anotado no registro central ($REGISTRY)"
else
    echo -e "  ${YELLOW}⚠${NC} Não consegui anotar o projeto no registro central (instale o jq: brew install jq)"
fi

# ─── Memória entre projetos (D38) ──────────────────────────────
if [ ! -f "$APRENDIZADOS" ]; then
    mkdir -p "$(dirname "$APRENDIZADOS")"
    cat > "$APRENDIZADOS" << 'EOF'
# Aprendizados entre projetos — Formação Δ-11

> Lições que valem para QUALQUER projeto. O ATLAS lê este arquivo na Fase 0 e na Fase 2.
> O CRONOS acrescenta de 3 a 5 lições ao fim de cada ciclo e na Fase 7.
> Formato de cada lição: `- [AAAA-MM-DD] [projeto] lição em uma frase — por quê`.

## Lições
EOF
    echo -e "  ${GREEN}✓${NC} Memória entre projetos criada em $APRENDIZADOS"
fi

FILE_COUNT=$(find "$DESTINO" -type f | wc -l | xargs)
echo -e "  ${GREEN}✓${NC} ${FILE_COUNT} arquivos de sistema instalados"
echo ""

# Abrir no VS Code se disponível
if command -v code &> /dev/null; then
    read -r -p "  Abrir no VS Code? (s/n): " OPEN_VSCODE || OPEN_VSCODE="n"
    if [[ "$OPEN_VSCODE" == "s" || "$OPEN_VSCODE" == "S" ]]; then
        code "$TARGET_DIR"
        echo -e "  ${GREEN}✓${NC} VS Code aberto"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}  ✓ Projeto pronto!${NC}"
echo ""
echo -e "  ${BOLD}Próximo passo:${NC}"
echo -e "  1. Abra o Claude Code na pasta do projeto"
echo -e "  2. Digite: ${CYAN}d11${NC} (o painel abre sozinho)"
echo -e "  3. Descreva o que quer construir"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
