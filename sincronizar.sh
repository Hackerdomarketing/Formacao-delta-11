#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Sincronizar o Sistema em Todos os Projetos (v6.3)
# ═══════════════════════════════════════════════════════════════
#
# Leva os arquivos de SISTEMA da fonte oficial para cada projeto que
# usa o Δ-11. Nunca mexe nos dados do projeto.
#
# De onde vêm os projetos:
#   1. a lista "projects" do registro central (~/.delta-11-registry.json);
#   2. uma varredura de pastas (SEARCH_PATHS abaixo).
#   O registro é reescrito no fim com a lista real (sem pastas que sumiram).
#
# NUNCA são tratados como projeto (C-057):
#   - a própria fonte e a pasta de onde este script roda;
#   - worktrees de agentes (.claude/worktrees/...);
#   - cópias e clones do próprio sistema: pasta com
#     boilerplate-delta-11-nextjs/, ou com .delta-11/CHANGELOG.md
#     + sincronizar.sh na raiz E nada além dos arquivos do sistema
#     (v6.4.1), ou com .delta-11/.e-copia-do-sistema,
#     e a pasta construcao-delta-11/sistema-atual.
#
# O que ELE SINCRONIZA (arquivos de sistema, por cima):
#   - CLAUDE.md
#   - .delta-11/{operativos,protocolos,sub-agentes,templates,conhecimento,
#                hooks,ferramentas,perfis,mcp,tests}/**   (pastas inteiras)
#   - .delta-11/painel.html, .delta-11/CHANGELOG*.md e os README das
#     pastas canônicas (scratch, evidencias/screenshots, logs/sub-agentes)
#   - task-done.sh, monitor-delta11.sh, vigilante.sh  →  .delta-11/scripts/
#     (C-053; as cópias velhas na raiz do projeto são retiradas)
#   - perfis/*.json: vêm da fonte, MAS o campo "model" que o projeto já
#     tinha é mantido (o modelo de cada agente é decisão do projeto — v6.4.1)
#   - .claude/settings.json: os vigias (hooks) do Δ-11 são SUBSTITUÍDOS
#     pelos do modelo; vigias do usuário são preservados (C-058)
#
# O que ele cria SÓ SE FALTAR (nunca sobrescreve):
#   - .delta-11/.modo-selo           (D1 — o modo de cada projeto é dele)
#   - .delta-11/.config-limites.json (D36)
#   - .delta-11/memoria/gotchas.md   (a partir do modelo)
#   - .delta-11/pulsos-data.js e .delta-11/monitor-data.js (modelos do painel)
#   - linhas de proteção no .gitignore (segredos + estado de execução)
#
# O que ele APAGA (C-054):
#   - só os arquivos listados em .delta-11/removidos.txt da fonte, e só
#     se eles não existirem mais na fonte. Mostra cada um antes de apagar.
#
# O que ELE NUNCA TOCA (dados do projeto):
#   - .delta-11/kanban.md, .delta-11/kanban-data.js
#   - .delta-11/pulsos-data.js, .delta-11/monitor-data.js (só criados se faltarem)
#   - .delta-11/memoria/** (exceto criar gotchas.md se faltar)
#   - .delta-11/ativacoes/**, locks, logs, planos/, scratch
#   (a imagem e os sprites antigos do painel saíram da fonte e são
#    retirados dos projetos pela lista removidos.txt — C-056)
#   - .delta-11/.dispatch-mode, .delta-11/.nao-abrir-painel
#   - .delta-11/ativacoes/agentes-sessao.json (vínculos de sessão, tempo de execução)
#
# Como usar:
#   ./sincronizar.sh                    # sincroniza tudo
#   ./sincronizar.sh --dry-run          # só MOSTRA o que faria (não grava nada)
#   ./sincronizar.sh --diff             # compara fonte × projetos (não grava nada)
#   ./sincronizar.sh --pull             # git pull na fonte antes de sincronizar
#   ./sincronizar.sh --nota "mensagem"  # nota gravada no .last-update
#
# Variáveis opcionais (usadas pelos testes):
#   DELTA11_REGISTRY      caminho do registro (padrão ~/.delta-11-registry.json)
#   DELTA11_SEARCH_PATHS  pastas de varredura separadas por ":"
#
# REQUER: jq (brew install jq)
#
# ═══════════════════════════════════════════════════════════════

set -e
set -o pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

REGISTRY="${DELTA11_REGISTRY:-$HOME/.delta-11-registry.json}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
DRY_RUN=false
DO_PULL=false
DO_DIFF=false
NOTA=""

# ─── Pastas onde o script procura projetos com Δ-11 ──────────
if [ -n "${DELTA11_SEARCH_PATHS:-}" ]; then
    IFS=':' read -r -a SEARCH_PATHS <<< "$DELTA11_SEARCH_PATHS"
else
    SEARCH_PATHS=(
        "$HOME/Documents/VSCODE"
        "$HOME/projetos"
        "$HOME/Downloads"
    )
fi

# Pastas de SISTEMA dentro de .delta-11/ (copiadas inteiras, recursivamente)
PASTAS_DE_SISTEMA="operativos protocolos sub-agentes templates conhecimento hooks ferramentas perfis mcp tests"

# Scripts de operação: na fonte ficam na raiz; nos projetos, em .delta-11/scripts/
SCRIPTS_DE_OPERACAO="task-done.sh monitor-delta11.sh vigilante.sh"
# Ferramentas da FONTE que instaladores antigos copiavam para a raiz dos projetos: saem dos projetos
# (rodar uma cópia velha de dentro do projeto usava regras antigas). Só a fonte oficial as executa.
SCRIPTS_DA_FONTE="sincronizar.sh instalar.sh novo-projeto.sh"
# Tudo o que pode existir na raiz de uma CÓPIA do sistema (qualquer outra coisa = projeto de verdade).
RAIZ_DO_SISTEMA=".claude .delta-11 .git .gitignore .DS_Store .vscode CLAUDE.md AGENTS.md GUIA-DO-COMANDANTE.md README.md LICENSE disparar.sh instalar.sh monitor-delta11.sh novo-projeto.sh sincronizar.sh task-done.sh vigilante.sh com.delta11.monitor.plist golden-baselines boilerplate-delta-11-nextjs"

# ─── Argumentos ────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --pull) DO_PULL=true; shift ;;
        --diff) DO_DIFF=true; DRY_RUN=true; shift ;;
        --nota)
            if [ -z "${2:-}" ]; then
                echo -e "${RED}--nota precisa de um texto${NC}"; exit 1
            fi
            NOTA="$2"; shift 2 ;;
        -h|--help|--ajuda)
            sed -n '3,64p' "$0"; exit 0 ;;
        *) echo -e "${RED}Argumento desconhecido: $1${NC}"; exit 1 ;;
    esac
done

# ─── Cabeçalho ─────────────────────────────────────────────────

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
if [ "$DO_DIFF" = true ]; then
    echo -e "${BOLD}  FORMAÇÃO Δ-11 — Comparação fonte × projetos (nada é gravado)${NC}"
elif [ "$DRY_RUN" = true ]; then
    echo -e "${BOLD}  FORMAÇÃO Δ-11 — Sincronização (DRY RUN: nada é gravado)${NC}"
else
    echo -e "${BOLD}  FORMAÇÃO Δ-11 — Sincronizando Sistema${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# ─── Pré-requisitos ────────────────────────────────────────────

if ! command -v jq &> /dev/null; then
    echo -e "${RED}x jq não encontrado. Instale com: brew install jq${NC}"
    exit 1
fi

if [ ! -f "$REGISTRY" ]; then
    echo -e "${RED}x Registro não encontrado em $REGISTRY${NC}"
    echo "  Rode o instalar.sh na pasta da fonte oficial para criar o registro."
    exit 1
fi

if ! jq empty "$REGISTRY" 2>/dev/null; then
    echo -e "${RED}x O registro $REGISTRY não é um JSON válido. Nada foi feito.${NC}"
    exit 1
fi

# ─── Funções auxiliares ────────────────────────────────────────

caminho_real() {
    # Caminho absoluto sem links simbólicos; vazio se a pasta não existir
    (cd "$1" 2>/dev/null && pwd -P) || true
}

expandir_til() {
    local p="$1"
    case "$p" in
        "~") p="$HOME" ;;
        "~/"*) p="$HOME/${p#\~/}" ;;
    esac
    echo "$p"
}

e_copia_do_sistema() {
    # C-057: verdadeiro (0) se a pasta é uma cópia/clone do PRÓPRIO sistema
    local pasta="$1"
    [ -d "$pasta/boilerplate-delta-11-nextjs" ] && return 0
    # CHANGELOG + sincronizar.sh na raiz só indica cópia se a pasta NÃO tem mais nada além dos arquivos do
    # próprio sistema. Projeto de verdade criado por instalador antigo (que copiava tudo para a raiz) também tem
    # esses dois arquivos, mas tem o seu próprio conteúdo (código, docs...) e precisa ser sincronizado.
    if [ -f "$pasta/.delta-11/CHANGELOG.md" ] && [ -f "$pasta/sincronizar.sh" ]; then
        local item nome
        for item in "$pasta"/* "$pasta"/.[!.]*; do
            [ -e "$item" ] || continue
            nome=$(basename "$item")
            case " $RAIZ_DO_SISTEMA " in
                *" $nome "*) ;;
                *) return 1 ;;  # tem conteúdo próprio: é projeto
            esac
        done
        return 0
    fi
    [ -f "$pasta/.delta-11/.e-copia-do-sistema" ] && return 0
    case "$pasta" in
        */construcao-delta-11/sistema-atual|*/construcao-delta-11/sistema-atual/*) return 0 ;;
    esac
    return 1
}

# ─── Fonte e backup (C-055: nunca seguir com origem vazia) ────

SOURCE_BRUTA=$(jq -r '.source // empty' "$REGISTRY" 2>/dev/null) || SOURCE_BRUTA=""
if [ -z "$SOURCE_BRUTA" ] || [ "$SOURCE_BRUTA" = "null" ]; then
    echo -e "${RED}x O registro não diz onde está a fonte oficial (campo \"source\" vazio).${NC}"
    echo "  Nada foi copiado. Rode o instalar.sh na pasta da fonte oficial."
    exit 1
fi
SOURCE_BRUTA=$(expandir_til "$SOURCE_BRUTA")
SOURCE=$(caminho_real "$SOURCE_BRUTA")
if [ -z "$SOURCE" ] || [ ! -d "$SOURCE/.delta-11" ] || [ ! -f "$SOURCE/CLAUDE.md" ]; then
    echo -e "${RED}x A fonte \"$SOURCE_BRUTA\" não existe ou não tem CLAUDE.md + .delta-11/.${NC}"
    echo "  Nada foi copiado."
    exit 1
fi

BACKUP_BRUTO=$(jq -r '.backup // empty' "$REGISTRY" 2>/dev/null) || BACKUP_BRUTO=""
BACKUP=""
if [ -n "$BACKUP_BRUTO" ] && [ "$BACKUP_BRUTO" != "null" ]; then
    BACKUP_BRUTO=$(expandir_til "$BACKUP_BRUTO")
    BACKUP=$(caminho_real "$BACKUP_BRUTO")
fi

if [ "$SOURCE" != "$SCRIPT_DIR" ]; then
    echo -e "${YELLOW}  AVISO: este script está em $SCRIPT_DIR, mas a fonte do registro é $SOURCE.${NC}"
    echo -e "${YELLOW}  Os arquivos serão copiados DA FONTE DO REGISTRO (não desta pasta).${NC}"
    echo ""
fi

# ─── Montar a lista de projetos ────────────────────────────────

PROJECTS=()
PROJETOS_VISTOS=$'\n'
PULADOS=()

motivo_para_pular() {
    local pasta="$1"
    [ -d "$pasta/.delta-11" ] || { echo "sem pasta .delta-11"; return; }
    [ "$pasta" = "$SOURCE" ] && { echo "é a fonte oficial"; return; }
    [ "$pasta" = "$SCRIPT_DIR" ] && { echo "é a pasta deste script (self-sync)"; return; }
    [ -n "$BACKUP" ] && [ "$pasta" = "$BACKUP" ] && { echo "é o backup do sistema"; return; }
    case "$pasta" in
        */.claude/worktrees/*) echo "é worktree de agente"; return ;;
    esac
    if e_copia_do_sistema "$pasta"; then
        echo "é cópia/clone do próprio sistema"; return
    fi
    echo ""
}

adicionar_projeto() {
    local bruto real motivo
    bruto=$(expandir_til "$1")
    real=$(caminho_real "$bruto")
    if [ -z "$real" ]; then
        PULADOS+=("$bruto — pasta não existe mais")
        return
    fi
    case "$PROJETOS_VISTOS" in
        *$'\n'"$real"$'\n'*) return ;;
    esac
    PROJETOS_VISTOS="${PROJETOS_VISTOS}${real}"$'\n'
    motivo=$(motivo_para_pular "$real")
    if [ -n "$motivo" ]; then
        PULADOS+=("$real — $motivo")
        return
    fi
    PROJECTS+=("$real")
}

echo -e "  ${BOLD}Procurando projetos com Δ-11...${NC}"
echo -e "  ${DIM}Registro: $REGISTRY${NC}"
echo -e "  ${DIM}Varredura: ${SEARCH_PATHS[*]}${NC}"
echo ""

# 1. Lista do registro (C-049: projetos fora das pastas varridas também entram)
while IFS= read -r linha; do
    [ -n "$linha" ] && adicionar_projeto "$linha"
done < <(jq -r '(.projects // [])[] | if type == "string" then . elif type == "object" then (.path // empty) else empty end' "$REGISTRY" 2>/dev/null || true)

# 2. Varredura de pastas
for search_path in "${SEARCH_PATHS[@]}"; do
    [ -d "$search_path" ] || continue
    while IFS= read -r delta11_dir; do
        adicionar_projeto "$(dirname "$delta11_dir")"
    done < <(find "$search_path" -maxdepth 3 \( -name node_modules -o -name .git -o -path '*/.claude/worktrees' \) -prune -o -type d -name ".delta-11" -print 2>/dev/null | sort)
done

echo -e "  ${BOLD}Fonte:${NC}    $SOURCE"
echo -e "  ${BOLD}Backup:${NC}   ${BACKUP:-(nenhum configurado)}"
echo -e "  ${BOLD}Projetos:${NC} ${#PROJECTS[@]}"
for proj in "${PROJECTS[@]}"; do
    echo -e "  ${DIM}  - $(basename "$proj") ($proj)${NC}"
done
if [ ${#PULADOS[@]} -gt 0 ]; then
    echo -e "  ${BOLD}Ignorados:${NC} ${#PULADOS[@]}"
    for p in "${PULADOS[@]}"; do
        echo -e "  ${DIM}  - $p${NC}"
    done
fi
echo ""

# ─── Git pull (opcional) ───────────────────────────────────────

if [ "$DO_PULL" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY]${NC} faria git pull na fonte (pulado: modo sem gravação)"
    else
        echo -e "  ${YELLOW}[PULL]${NC} Atualizando a fonte oficial..."
        git -C "$SOURCE" pull --ff-only 2>&1 | while read -r line; do echo "    $line"; done
        echo -e "  ${GREEN}OK${NC} Pull concluído"
    fi
    echo ""
fi

# ─── Lista de arquivos de sistema ──────────────────────────────
# Cada item é "origem|destino" (caminhos relativos à raiz).

SYNC_PARES=()
adicionar_par() { SYNC_PARES+=("$1|$2"); }

[ -f "$SOURCE/CLAUDE.md" ] && adicionar_par "CLAUDE.md" "CLAUDE.md"

for pasta in $PASTAS_DE_SISTEMA; do
    [ -d "$SOURCE/.delta-11/$pasta" ] || continue
    while IFS= read -r arquivo; do
        rel=".delta-11/${arquivo#"$SOURCE/.delta-11/"}"
        adicionar_par "$rel" "$rel"
    done < <(find "$SOURCE/.delta-11/$pasta" -type f ! -name ".DS_Store" ! -name "*.pyc" ! -path "*/__pycache__/*" | sort)
done

# Painel
for rel in .delta-11/painel.html \
           .delta-11/scratch/README.md \
           .delta-11/evidencias/screenshots/README.md \
           .delta-11/logs/sub-agentes/README.md; do
    [ -f "$SOURCE/$rel" ] && adicionar_par "$rel" "$rel"
done

for f in "$SOURCE/.delta-11/"CHANGELOG*.md; do
    [ -f "$f" ] && adicionar_par ".delta-11/$(basename "$f")" ".delta-11/$(basename "$f")"
done

# C-053: scripts de operação → .delta-11/scripts/
for s in $SCRIPTS_DE_OPERACAO; do
    [ -f "$SOURCE/$s" ] && adicionar_par "$s" ".delta-11/scripts/$s"
done

# Criados só se faltarem no destino (nunca sobrescritos)
SE_FALTAR_PARES=()
[ -f "$SOURCE/.delta-11/.modo-selo" ] && SE_FALTAR_PARES+=(".delta-11/.modo-selo|.delta-11/.modo-selo")
[ -f "$SOURCE/.delta-11/.config-limites.json" ] && SE_FALTAR_PARES+=(".delta-11/.config-limites.json|.delta-11/.config-limites.json")
[ -f "$SOURCE/.delta-11/pulsos-data.js" ] && SE_FALTAR_PARES+=(".delta-11/pulsos-data.js|.delta-11/pulsos-data.js")
[ -f "$SOURCE/.delta-11/monitor-data.js" ] && SE_FALTAR_PARES+=(".delta-11/monitor-data.js|.delta-11/monitor-data.js")
[ -f "$SOURCE/.delta-11/templates/gotchas-inicial.md" ] && SE_FALTAR_PARES+=(".delta-11/templates/gotchas-inicial.md|.delta-11/memoria/gotchas.md")

SETTINGS_HOOKS_SOURCE="$SOURCE/.delta-11/templates/settings-hooks.json"
REMOVIDOS_LISTA="$SOURCE/.delta-11/removidos.txt"

echo -e "  ${BOLD}Arquivos de sistema:${NC} ${#SYNC_PARES[@]}"
echo ""

# ─── Mescla de .claude/settings.json (C-058) ──────────────────
# Todo vigia cujo comando aponta para .delta-11/hooks/ é do Δ-11: sai inteiro e
# entra o que está no modelo (assim registros velhos ou errados somem).
# Vigias do usuário (qualquer outro comando) ficam. Permissões: união.
FILTRO_MESCLA='
def e_do_delta11: ((.command // "") | test("\\.delta-11/hooks/"));
.[0] as $proj | .[1] as $modelo |
($proj.hooks // {}) as $ph |
($modelo.hooks // {}) as $mh |
($ph | with_entries(
    .value |= ( map(.hooks = ((.hooks // []) | map(select(e_do_delta11 | not))))
                | map(select((.hooks | length) > 0)) )
  ) | with_entries(select((.value | length) > 0))) as $usuario |
((($usuario | keys) + ($mh | keys)) | unique) as $eventos |
($eventos | map({ (.): (($mh[.] // []) + ($usuario[.] // [])) }) | add // {}) as $hooks |
$proj
| .hooks = $hooks
| if ($modelo.permissions // null) != null then
    .permissions = (
      (($modelo.permissions | del(.allow, .ask, .deny)) * (($proj.permissions // {}) | del(.allow, .ask, .deny)))
      + ( ["allow", "ask", "deny"]
          | map(. as $k | { ($k): ((($proj.permissions // {})[$k] // []) + ($modelo.permissions[$k] // []) | unique) })
          | add )
    )
  else . end
'

# ─── Proteção do .gitignore (C-147) ───────────────────────────
LINHAS_GITIGNORE=(
    ".env"
    ".env.*"
    "!.env.example"
    "*.pem"
    "*.key"
    "credentials.json"
    ".claude/settings.local.json"
    ".DS_Store"
    ".delta-11/activity-log.md"
    ".delta-11/monitor-status.json"
    ".delta-11/monitor-data.js"
    ".delta-11/pulsos-data.js"
    ".delta-11/ativacoes/"
    ".delta-11/locks/*"
    "!.delta-11/locks/.gitkeep"
    ".delta-11/scratch/*"
    "!.delta-11/scratch/README.md"
    ".delta-11/logs/sub-agentes/*.log"
    ".claude/worktrees/"
)

garantir_gitignore() {
    local destino="$1" arquivo="$1/.gitignore" faltando=() linha
    for linha in "${LINHAS_GITIGNORE[@]}"; do
        if [ ! -f "$arquivo" ] || ! grep -Fxq -- "$linha" "$arquivo"; then
            faltando+=("$linha")
        fi
    done
    [ ${#faltando[@]} -eq 0 ] && return 0
    if [ "$DRY_RUN" = true ]; then
        echo -e "    ${YELLOW}~ .gitignore${NC} (acrescentaria ${#faltando[@]} linha(s) de proteção)"
    else
        {
            [ -f "$arquivo" ] && [ -s "$arquivo" ] && echo ""
            echo "# ─── Formação Δ-11 (v6.3): segredos e estado de execução nunca vão ao GitHub ───"
            printf '%s\n' "${faltando[@]}"
        } >> "$arquivo"
        echo -e "    ${YELLOW}~ .gitignore${NC} (${#faltando[@]} linha(s) de proteção acrescentadas)"
    fi
    return 0
}

# ─── Apagar o que saiu da fonte (C-054, C-150) ────────────────
aplicar_removidos() {
    local destino="$1" rel alvo
    [ -n "$destino" ] || { echo -e "    ${RED}ERRO: destino vazio, abortando remoções${NC}"; return 1; }
    [ -f "$REMOVIDOS_LISTA" ] || return 0
    while IFS= read -r rel || [ -n "$rel" ]; do
        rel="${rel%%#*}"
        rel="$(echo "$rel" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
        [ -z "$rel" ] && continue
        case "$rel" in
            /*|*..*) echo -e "    ${RED}! removidos.txt: caminho recusado: $rel${NC}"; continue ;;
        esac
        [ -e "$SOURCE/$rel" ] && continue   # voltou para a fonte: não apagar
        alvo="$destino/$rel"
        [ -f "$alvo" ] || continue
        if [ "$DRY_RUN" = true ]; then
            echo -e "    ${RED}- $rel${NC} (seria apagado: saiu da fonte)"
        else
            echo -e "    ${RED}- apagando (saiu da fonte):${NC}"
            ls -l "$alvo" | sed 's/^/        /'
            rm -f "$alvo"
        fi
    done < "$REMOVIDOS_LISTA"
    return 0
}

# ─── Sincronizar UM projeto ───────────────────────────────────

sincronizar_destino() {
    local destino="$1"
    local copiados=0 ignorados=0 par src_rel dst_rel src dst modelo_mantido perfil_mesclado

    if [ -z "$destino" ] || [ ! -d "$destino" ]; then
        echo -e "    ${RED}x Pasta não encontrada: $destino${NC}"
        return 1
    fi

    # Pastas de infraestrutura
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$destino/.delta-11/hooks" "$destino/.delta-11/scripts" \
                 "$destino/.delta-11/ativacoes" "$destino/.delta-11/locks" \
                 "$destino/.delta-11/scratch" "$destino/.claude"
        [ -f "$destino/.delta-11/locks/.gitkeep" ] || touch "$destino/.delta-11/locks/.gitkeep"
        for pasta_canonica in ".delta-11/bugs" ".delta-11/logs/autocritica" ".delta-11/memoria/decisoes"; do
            mkdir -p "$destino/$pasta_canonica"
            [ -f "$destino/$pasta_canonica/.gitkeep" ] || touch "$destino/$pasta_canonica/.gitkeep"
        done
    fi

    # 1. Arquivos de sistema (por cima)
    for par in "${SYNC_PARES[@]}"; do
        src_rel="${par%%|*}"
        dst_rel="${par#*|}"
        src="$SOURCE/$src_rel"
        dst="$destino/$dst_rel"
        modelo_mantido=""
        perfil_mesclado=""

        # Perfis: o MODELO é escolha do projeto (ex.: salvahacks decidiu SHIELD = sonnet). O resto do perfil vem da
        # fonte, mas o campo "model" que o projeto já tinha é preservado — senão cada sincronização desfaz a decisão.
        if [[ "$dst_rel" == .delta-11/perfis/*.json ]] && [ -f "$dst" ]; then
            local modelo_projeto modelo_fonte
            modelo_projeto=$(jq -r '.model // empty' "$dst" 2>/dev/null) || modelo_projeto=""
            modelo_fonte=$(jq -r '.model // empty' "$src" 2>/dev/null) || modelo_fonte=""
            if [ -n "$modelo_projeto" ] && [ "$modelo_projeto" != "$modelo_fonte" ]; then
                perfil_mesclado=$(mktemp)
                if jq --arg m "$modelo_projeto" '.model = $m' "$src" > "$perfil_mesclado" 2>/dev/null; then
                    src="$perfil_mesclado"
                    modelo_mantido="$modelo_projeto"
                fi
            fi
        fi

        if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
            ignorados=$((ignorados + 1))
            [ -n "$perfil_mesclado" ] && rm -f "$perfil_mesclado"
            continue
        fi

        if [ "$DRY_RUN" = true ]; then
            if [ ! -f "$dst" ]; then
                echo -e "    ${GREEN}+ $dst_rel${NC} (novo)"
            else
                echo -e "    ${YELLOW}~ $dst_rel${NC} (atualizado)"
            fi
        else
            mkdir -p "$(dirname "$dst")"
            cp "$src" "$dst"
            if [ -x "$src" ] || [[ "$dst_rel" == .delta-11/scripts/*.sh ]]; then
                chmod +x "$dst"
            fi
        fi
        if [ -n "$modelo_mantido" ]; then
            echo -e "    ${GREEN}= $dst_rel${NC}: modelo do projeto mantido (\"$modelo_mantido\")"
        fi
        [ -n "$perfil_mesclado" ] && rm -f "$perfil_mesclado"
        copiados=$((copiados + 1))
    done

    # 2. Criados só se faltarem (D1: o .modo-selo do projeto é preservado)
    for par in "${SE_FALTAR_PARES[@]}"; do
        src_rel="${par%%|*}"
        dst_rel="${par#*|}"
        dst="$destino/$dst_rel"
        [ -f "$dst" ] && continue
        if [ "$DRY_RUN" = true ]; then
            echo -e "    ${GREEN}+ $dst_rel${NC} (novo, só porque faltava)"
        else
            mkdir -p "$(dirname "$dst")"
            cp "$SOURCE/$src_rel" "$dst"
        fi
        copiados=$((copiados + 1))
    done

    # 3. C-053: cópias velhas dos scripts de operação na raiz do projeto
    local s alvo
    for s in $SCRIPTS_DE_OPERACAO; do
        alvo="$destino/$s"
        [ -f "$alvo" ] || continue
        # Só apaga se for mesmo um script do Δ-11 (nunca um arquivo do usuário com o mesmo nome)
        if ! sed -n '1,25p' "$alvo" 2>/dev/null | grep -E "Δ-11|D-11|DELTA-11|Delta-11" > /dev/null; then
            continue
        fi
        if [ "$DRY_RUN" = true ]; then
            echo -e "    ${RED}- $s${NC} (sairia da raiz: agora mora em .delta-11/scripts/)"
        else
            echo -e "    ${RED}- retirando da raiz (agora mora em .delta-11/scripts/):${NC}"
            ls -l "$alvo" | sed 's/^/        /'
            rm -f "$alvo"
        fi
    done

    # 3b. Ferramentas da fonte copiadas por instaladores antigos (sincronizar/instalar/novo-projeto)
    for s in $SCRIPTS_DA_FONTE; do
        alvo="$destino/$s"
        [ -f "$alvo" ] || continue
        if ! sed -n '1,25p' "$alvo" 2>/dev/null | grep -E "Δ-11|D-11|DELTA-11|Delta-11" > /dev/null; then
            continue
        fi
        if [ "$DRY_RUN" = true ]; then
            echo -e "    ${RED}- $s${NC} (sairia da raiz: é ferramenta da fonte oficial, não do projeto)"
        else
            echo -e "    ${RED}- retirando da raiz (ferramenta da fonte oficial, não do projeto):${NC}"
            ls -l "$alvo" | sed 's/^/        /'
            rm -f "$alvo"
        fi
        copiados=$((copiados + 1))
    done

    # 4. C-054: arquivos que saíram da fonte
    aplicar_removidos "$destino"

    # 5. C-058: .claude/settings.json
    if [ -f "$SETTINGS_HOOKS_SOURCE" ]; then
        local settings_dst="$destino/.claude/settings.json" mesclado
        if [ -f "$settings_dst" ]; then
            if mesclado=$(jq -s "$FILTRO_MESCLA" "$settings_dst" "$SETTINGS_HOOKS_SOURCE" 2>/dev/null) && [ -n "$mesclado" ]; then
                if [ "$(printf '%s\n' "$mesclado" | jq -S .)" = "$(jq -S . "$settings_dst")" ]; then
                    :
                elif [ "$DRY_RUN" = true ]; then
                    echo -e "    ${YELLOW}~ .claude/settings.json${NC} (vigias do Δ-11 seriam trocados pelos do modelo)"
                    copiados=$((copiados + 1))
                else
                    local tmp_settings
                    tmp_settings=$(mktemp "$settings_dst.XXXXXX")
                    printf '%s\n' "$mesclado" > "$tmp_settings"
                    mv "$tmp_settings" "$settings_dst"
                    echo -e "    ${YELLOW}~ .claude/settings.json${NC} (vigias do Δ-11 trocados pelos do modelo; os seus foram mantidos)"
                    copiados=$((copiados + 1))
                fi
            else
                # NUNCA sobrescrever um settings.json que não deu para ler
                echo -e "    ${RED}! .claude/settings.json inválido — NÃO foi alterado. Corrija o JSON e rode de novo.${NC}"
            fi
        else
            if [ "$DRY_RUN" = true ]; then
                echo -e "    ${GREEN}+ .claude/settings.json${NC} (novo, do modelo)"
            else
                cp "$SETTINGS_HOOKS_SOURCE" "$settings_dst"
            fi
            copiados=$((copiados + 1))
        fi
    fi

    # 6. C-147: proteção do .gitignore
    garantir_gitignore "$destino"

    if [ $copiados -eq 0 ]; then
        echo -e "    ${GREEN}OK Já estava atualizado${NC}"
    elif [ "$DRY_RUN" = true ]; then
        echo -e "    ${YELLOW}${copiados} mudança(s) seriam feitas${NC}, ${ignorados} arquivo(s) já iguais"
    else
        echo -e "    ${GREEN}OK ${copiados} arquivo(s) sincronizado(s)${NC}, ${ignorados} já iguais"
    fi
    return 0
}

# ─── Sincronizar todos os projetos ────────────────────────────

if [ ${#PROJECTS[@]} -eq 0 ]; then
    echo -e "${YELLOW}! Nenhum projeto com Δ-11 encontrado.${NC}"
fi

PROJ_OK=0
PROJ_FAIL=0
PROJ_SINCRONIZADOS=()

for proj in "${PROJECTS[@]}"; do
    echo -e "  ${CYAN}[$(basename "$proj")]${NC}"
    echo -e "  ${DIM}$proj${NC}"
    if sincronizar_destino "$proj"; then
        PROJ_OK=$((PROJ_OK + 1))
        PROJ_SINCRONIZADOS+=("$proj")
    else
        PROJ_FAIL=$((PROJ_FAIL + 1))
    fi
    echo ""
done

if [ "$DO_DIFF" = true ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Comparação concluída — nenhum arquivo foi alterado${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo ""
    exit 0
fi

# ─── Skills globais (só se a fonte tiver a pasta skills/) ─────
# C-051: o modo de teste NUNCA copia. Antes de sobrescrever uma skill,
# guardamos uma cópia dela (C-150).
SKILLS_UPDATED=0
if [ -d "$SOURCE/skills" ]; then
    for skill_dir in "$SOURCE"/skills/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")
        [ -n "$skill_name" ] || continue
        skill_dest="$HOME/.claude/skills/$skill_name"
        if [ -d "$skill_dest" ] && diff -rq "$skill_dir" "$skill_dest" &> /dev/null; then
            continue
        fi
        if [ "$DRY_RUN" = true ]; then
            echo -e "  ${YELLOW}[DRY]${NC} Atualizaria/instalaria a skill: $skill_name"
            continue
        fi
        if [ -d "$skill_dest" ]; then
            copia_skill="$HOME/.claude/skills/.backup-delta-11/${skill_name}-$(date +%Y%m%d-%H%M%S)"
            mkdir -p "$(dirname "$copia_skill")"
            cp -R "$skill_dest" "$copia_skill"
            echo -e "  ${DIM}Cópia de segurança da skill $skill_name em $copia_skill${NC}"
        fi
        mkdir -p "$skill_dest"
        cp -R "$skill_dir/." "$skill_dest/"
        SKILLS_UPDATED=$((SKILLS_UPDATED + 1))
    done
    [ "$SKILLS_UPDATED" -gt 0 ] && echo -e "  ${BOLD}Skills atualizadas:${NC} ${SKILLS_UPDATED}" && echo ""
fi

# ─── Backup (espelho da distribuição) ─────────────────────────
# C-055: a cópia do backup roda dentro de um "if" e nunca derruba o script.

espelhar_backup() {
    local destino="$1" arquivo n=0
    [ -n "$destino" ] && [ -d "$destino" ] || return 1
    if git -C "$SOURCE" rev-parse --is-inside-work-tree &>/dev/null; then
        LISTA_DISTRIBUICAO=$(git -C "$SOURCE" ls-files --cached --others --exclude-standard)
    else
        LISTA_DISTRIBUICAO=$(cd "$SOURCE" && find . -type f ! -path "./.git/*" ! -name ".DS_Store" | sed 's|^\./||')
    fi
    while IFS= read -r arquivo; do
        [ -n "$arquivo" ] && [ -f "$SOURCE/$arquivo" ] || continue
        if [ -f "$destino/$arquivo" ] && cmp -s "$SOURCE/$arquivo" "$destino/$arquivo"; then
            continue
        fi
        if [ "$DRY_RUN" = true ]; then
            echo -e "    ${YELLOW}~ $arquivo${NC}"
        else
            mkdir -p "$(dirname "$destino/$arquivo")"
            cp -p "$SOURCE/$arquivo" "$destino/$arquivo"
        fi
        n=$((n + 1))
    done <<< "$LISTA_DISTRIBUICAO"
    aplicar_removidos "$destino" || return 1
    echo -e "    ${GREEN}OK${NC} $n arquivo(s) $([ "$DRY_RUN" = true ] && echo "seriam copiados" || echo "copiados")"
    return 0
}

BACKUP_STATUS="nenhum configurado"
if [ -n "$BACKUP" ]; then
    echo -e "  ${BOLD}Backup:${NC} ${CYAN}[$(basename "$BACKUP")]${NC}"
    if [ "$BACKUP" = "$SOURCE" ]; then
        echo -e "    ${RED}! O backup aponta para a própria fonte — pulado${NC}"
        BACKUP_STATUS="pulado (aponta para a fonte)"
    elif [ -d "$BACKUP/.delta-11" ] && ! e_copia_do_sistema "$BACKUP"; then
        echo -e "    ${RED}! O backup parece um PROJETO, não uma cópia do sistema — pulado${NC}"
        BACKUP_STATUS="pulado (parece projeto)"
    elif espelhar_backup "$BACKUP"; then
        BACKUP_STATUS="atualizado"
    else
        echo -e "    ${RED}! Falha ao atualizar o backup (os projetos já foram sincronizados)${NC}"
        BACKUP_STATUS="falhou"
    fi
    echo ""
elif [ -n "$BACKUP_BRUTO" ] && [ "$BACKUP_BRUTO" != "null" ]; then
    echo -e "  ${YELLOW}! Pasta de backup não encontrada: $BACKUP_BRUTO${NC}"
    BACKUP_STATUS="pasta não encontrada"
    echo ""
fi

# ─── .last-update e registro central ──────────────────────────

if [ "$DRY_RUN" = false ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    UPDATE_NOTE="${NOTA:-Sincronização automática}"

    for proj in "${PROJ_SINCRONIZADOS[@]}"; do
        if [ -d "$proj/.delta-11" ]; then
            cat > "$proj/.delta-11/.last-update" << UPDATEEOF
$TIMESTAMP
Atualização: $UPDATE_NOTE
Fonte: $SOURCE
Arquivos de sistema conferidos: ${#SYNC_PARES[@]}
UPDATEEOF
        fi
    done

    # A lista projects[] passa a ser a lista REAL (registro + varredura, sem
    # pastas que sumiram e sem cópias do sistema).
    if [ ${#PROJECTS[@]} -gt 0 ]; then
        PROJECTS_JSON=$(printf '%s\n' "${PROJECTS[@]}" | jq -R . | jq -s .)
    else
        PROJECTS_JSON='[]'
    fi
    TMP_REG=$(mktemp "${REGISTRY}.XXXXXX")
    if jq --arg ts "$TIMESTAMP" --argjson projetos "$PROJECTS_JSON" \
          '.last_sync = $ts | .projects = $projetos' "$REGISTRY" > "$TMP_REG"; then
        mv "$TMP_REG" "$REGISTRY"
    else
        rm -f "$TMP_REG"
        echo -e "  ${RED}! Não consegui atualizar o registro (ele continua como estava)${NC}"
    fi
fi

# ─── Relatório final ──────────────────────────────────────────

echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}${BOLD}  DRY RUN — Nenhum arquivo foi alterado${NC}"
else
    echo -e "${GREEN}${BOLD}  OK Sincronização concluída${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Projetos: ${GREEN}$PROJ_OK OK${NC}"
if [ $PROJ_FAIL -gt 0 ]; then
    echo -e "  Falhas:   ${RED}$PROJ_FAIL${NC}"
fi
echo -e "  Backup:   $BACKUP_STATUS"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "  ${DIM}Para conferir: ./sincronizar.sh --diff${NC}"
    echo ""
fi

[ $PROJ_FAIL -eq 0 ]
