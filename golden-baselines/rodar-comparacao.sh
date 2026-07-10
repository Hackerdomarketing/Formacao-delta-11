#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Runner de Comparação de Golden Baselines
# ════════════════════════════════════════════════════════════════
#
# O que faz:
#   1. Cria diretório execucoes/AAAA-MM-DD-vX.X/ (datado)
#   2. Para cada tarefa canônica em golden-baselines/tarefas/:
#      - Lê o bloco de ativação
#      - Cria subdiretório execucoes/.../[agente]-[tarefa]/
#      - Escreve um MANIFESTO com metadados (data, versão, agente, tarefa)
#      - Escreve o prompt de ativação pronto para colar no agente
#   3. Mostra resumo: "X tarefas preparadas em execucoes/YYYY-MM-DD-vX.X/"
#
# O QUE NÃO FAZ (propositalmente — runner ≠ executor):
#   - Não dispara agentes automaticamente (cada agente precisa de uma janela
#     Claude Code dedicada; o runner é ferramenta do COMANDANTE)
#   - Não avalia resultado (avaliação é feita em sessão limpa separada)
#   - Não commita nada (decisão do comandante)
#
# Uso:
#   bash golden-baselines/rodar-comparacao.sh [versao]
#
# Exemplo:
#   bash golden-baselines/rodar-comparacao.sh v5.4
#   bash golden-baselines/rodar-comparacao.sh v5.4.1
#
# Saída:
#   golden-baselines/execucoes/2026-07-10-v5.4/
#   ├── MANIFESTO.md
#   ├── engine-rota-de-pedidos/
#   │   ├── prompt-de-ativacao.txt
#   │   └── gabarito.md
#   ├── pixel-tela-de-lista-de-produtos/
#   │   ├── prompt-de-ativacao.txt
#   │   └── gabarito.md
#   └── vault-esquema-de-assinaturas/
#       ├── prompt-de-ativacao.txt
#       └── gabarito.md
# ════════════════════════════════════════════════════════════════

set -euo pipefail

# Cores
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# Localização
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TAREFAS_DIR="$SCRIPT_DIR/tarefas"
EXECUCOES_DIR="$SCRIPT_DIR/execucoes"
RUBRICA="$SCRIPT_DIR/rubrica-de-avaliacao.md"

# Versão (default = v5.4)
VERSAO="${1:-v5.4}"
DATA="$(date +%Y-%m-%d)"
DESTINO="$EXECUCOES_DIR/$DATA-$VERSAO"

echo ""
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}  Δ-11 — Runner de Golden Baselines ($VERSAO)${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""

# Pré-condições
if [ ! -d "$TAREFAS_DIR" ]; then
    echo -e "${RED}ERRO: pasta de tarefas nao encontrada: $TAREFAS_DIR${NC}" >&2
    exit 1
fi
if [ ! -f "$RUBRICA" ]; then
    echo -e "${YELLOW}AVISO: rubrica nao encontrada em $RUBRICA — notas serao livres${NC}" >&2
fi

# Criar destino
mkdir -p "$DESTINO"
echo -e "  ${GREEN}✓${NC} Destino criado: ${BOLD}$DESTINO${NC}"
echo ""

# Manifesto
CONTADOR=0
TOTAL=$(find "$TAREFAS_DIR" -maxdepth 1 -name "*.md" | wc -l | xargs)

cat > "$DESTINO/MANIFESTO.md" << EOF
# Rodada de Golden Baselines — $DATA ($VERSAO)

**Data:** $DATA
**Versão do Δ-11:** $VERSAO
**Tarefas canônicas previstas:** $TOTAL
**Rubrica:** $(basename "$RUBRICA" 2>/dev/null || "(ausente)")

## Estrutura

| Agente | Tarefa | Status | Nota |
|--------|--------|--------|------|
EOF

# Para cada tarefa canônica
for tarefa_file in "$TAREFAS_DIR"/*.md; do
    [ -f "$tarefa_file" ] || continue
    tarefa_nome="$(basename "$tarefa_file" .md)"
    # Extrair agente do nome do arquivo (formato: agente-descrição-curta.md)
    agente="$(echo "$tarefa_nome" | cut -d'-' -f1)"
    agente="$(echo "$agente" | tr '[:lower:]' '[:upper:]')"

    subdir="$DESTINO/$tarefa_nome"
    mkdir -p "$subdir"

    # Extrair bloco de "Ativação" da tarefa canônica
    # Formato esperado no .md: linha "## Bloco de Ativação" seguida de bloco de código \`\`\`
    if grep -q "^## Bloco de Ativação" "$tarefa_file" 2>/dev/null; then
        sed -n '/^## Bloco de Ativação/,/^```$/p' "$tarefa_file" \
            | sed '1d;$d' > "$subdir/prompt-de-ativacao.txt" || true
    else
        echo "# Bloco de ativação não encontrado em $tarefa_nome.md (esperado heading '## Bloco de Ativação')" \
            > "$subdir/prompt-de-ativacao.txt"
    fi

    # Extrair gabarito/checklist (heading "## Gabarito" ou "## Checklist")
    if grep -q "^## Gabarito\|^## Checklist" "$tarefa_file" 2>/dev/null; then
        sed -n '/^## \(Gabarito\|Checklist\)/,$p' "$tarefa_file" \
            > "$subdir/gabarito.md" || true
    else
        echo "# Gabarito não encontrado em $tarefa_nome.md" \
            > "$subdir/gabarito.md"
    fi

    # Adicionar linha no manifesto
    echo "| $agente | $tarefa_nome | ⏳ pendente | — |" >> "$DESTINO/MANIFESTO.md"

    CONTADOR=$((CONTADOR + 1))
    echo -e "  ${GREEN}✓${NC} $agente: ${BOLD}$tarefa_nome${NC}"
done

# Adicionar bloco de instruções ao manifesto
cat >> "$DESTINO/MANIFESTO.md" << EOF

## Próximos passos (protocolo do comandante)

1. Abra uma janela do Claude Code por agente da coluna "Agente" acima.
2. Cole o conteúdo de \`prompt-de-ativacao.txt\` correspondente.
3. Aguarde o agente executar até o fim (autocrítica → build-validator → contract-tester).
4. Copie o resultado (código + logs) para este subdiretório.
5. Avalie com a rubrica em sessão limpa separada.
6. Atualize a coluna "Nota" no MANIFESTO acima.

## Comparação com execuções anteriores

Compare esta rodada com a imediatamente anterior em \`execucoes/\`:
- Se TODAS as notas subiram → a mudança do Δ-11 foi benéfica.
- Se ALGUMA nota caiu mais que 5 pontos → regressão; investigar antes de propagar.
EOF

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Rodada preparada: $CONTADOR tarefa(s) em $DESTINO${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Próximo passo: abra o MANIFESTO.md em ${BOLD}$DESTINO${NC}"
echo -e "  e cole cada prompt em uma janela Claude Code dedicada."
echo ""