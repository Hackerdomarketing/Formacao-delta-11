#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# VAULT — Validacao de SQL e Migrations (v6.3 — 2026-10-14)
# ═══════════════════════════════════════════════════════════════
#
# Valida arquivos SQL:
#   1. Estilo SQL (sqlfluff lint) — so aviso
#   2. Ordem de migrations (timestamps duplicados = FALHA)
#   3. Checklist de seguranca:
#      - toda tabela criada tem "ENABLE ROW LEVEL SECURITY" (RLS)
#      - toda chave estrangeira (REFERENCES) declara ON DELETE
#
# Como le o SQL (C-138): comentarios "--" sao removidos, tudo vira
# minusculas (SQL nao diferencia maiusculas) e o texto e dividido em
# instrucoes pelo ";". Assim "alter table ... enable row level security"
# em minusculas conta, e o ON DELETE e conferido NA MESMA definicao da
# chave estrangeira — nao mais "toda linha com REFERENCES".
#
# Uso: bash .delta-11/ferramentas/vault-validate-sql.sh [diretorio]
#
# Saida (convencao das ferramentas v6.3): 0 = PASS ou ALERTA (so avisos);
# 1 = FAIL (timestamps duplicados) ou uso errado.
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

ALVO="${1:-.}"
RESULTADO_FINAL="PASS"
RELATORIO=""

if [ ! -d "$ALVO" ]; then
    echo "ERRO: '$ALVO' nao e uma pasta."
    echo "Uso: vault-validate-sql.sh [diretorio]"
    exit 1
fi

marcar_alerta() {
    if [ "$RESULTADO_FINAL" = "PASS" ]; then
        RESULTADO_FINAL="ALERTA"
    fi
}

echo "═══════════════════════════════════════════════════"
echo "  VAULT VALIDATE — SQL e Migrations"
echo "  Alvo: $ALVO"
echo "═══════════════════════════════════════════════════"
echo ""

MIGRATION_DIR=""
for dir in "$ALVO/supabase/migrations" "$ALVO/migrations" "$ALVO/sql"; do
    if [ -d "$dir" ]; then
        MIGRATION_DIR="$dir"
        break
    fi
done

SQL_FILES=()
if [ -n "$MIGRATION_DIR" ]; then
    while IFS= read -r arquivo; do
        SQL_FILES+=("$arquivo")
    done < <(find "$MIGRATION_DIR" -maxdepth 1 -type f -name "*.sql" | sort)
fi

# ───────────────────────────────────────────────────────
# 1. SQLFLUFF LINT
# ───────────────────────────────────────────────────────

echo "[1/3] sqlfluff lint..."

if [ -z "$MIGRATION_DIR" ]; then
    echo "  NAO SE APLICA — pasta de migrations nao encontrada"
elif ! command -v sqlfluff &>/dev/null; then
    echo "  AVISO — sqlfluff nao instalado: a checagem de ESTILO nao rodou (pip install sqlfluff)"
    RELATORIO="$RELATORIO\n[SQLFLUFF] nao rodou — sqlfluff nao instalado"
    marcar_alerta
else
    SQLFLUFF_OUTPUT=$(sqlfluff lint "$MIGRATION_DIR" --dialect postgres 2>&1 || true)
    # grep -c imprime "0" e sai com 1 quando nao acha: "|| true" (C-134).
    SQLFLUFF_ERRORS=$(printf '%s\n' "$SQLFLUFF_OUTPUT" | grep -cE "ERROR|L:" || true)
    SQLFLUFF_ERRORS="${SQLFLUFF_ERRORS:-0}"

    if [ "$SQLFLUFF_ERRORS" -gt 0 ]; then
        RELATORIO="$RELATORIO\n[SQLFLUFF] $SQLFLUFF_ERRORS problema(s) de estilo SQL"
        echo "  AVISO — $SQLFLUFF_ERRORS problema(s) de estilo"
        marcar_alerta
    else
        echo "  PASS — SQL bem formatado"
    fi
fi

# ───────────────────────────────────────────────────────
# 2. ORDEM DE MIGRATIONS
# ───────────────────────────────────────────────────────

echo "[2/3] Verificando ordem de migrations..."

if [ -z "$MIGRATION_DIR" ]; then
    echo "  NAO SE APLICA — pasta de migrations nao encontrada"
elif [ "${#SQL_FILES[@]}" -eq 0 ]; then
    echo "  NAO SE APLICA — nenhum arquivo .sql em $MIGRATION_DIR"
else
    DUPLICATAS=$(for arquivo in "${SQL_FILES[@]}"; do basename "$arquivo"; done \
        | grep -oE '^[0-9]+' | sort | uniq -d || true)

    if [ -n "$DUPLICATAS" ]; then
        RESULTADO_FINAL="FAIL"
        RELATORIO="$RELATORIO\n[MIGRATIONS] Timestamps duplicados: $(echo "$DUPLICATAS" | tr '\n' ' ')"
        echo "  FAIL — timestamps duplicados encontrados"
    else
        echo "  PASS — ${#SQL_FILES[@]} migration(s) em ordem"
    fi
fi

# ───────────────────────────────────────────────────────
# 3. CHECKLIST DE SEGURANCA SQL
# ───────────────────────────────────────────────────────

echo "[3/3] Checklist de seguranca SQL..."

if [ "${#SQL_FILES[@]}" -eq 0 ]; then
    echo "  NAO SE APLICA — sem migrations para verificar"
else
    # Uma instrucao SQL por linha, em minusculas e sem comentarios "--".
    INSTRUCOES=$(sed 's/--.*$//' "${SQL_FILES[@]}" | tr '[:upper:]' '[:lower:]' | tr '\n\t' '  ' | tr ';' '\n')

    # Nomes das tabelas criadas (sem "if not exists", sem "public.", sem aspas).
    TABELAS=$(printf '%s\n' "$INSTRUCOES" \
        | grep -oE 'create[[:space:]]+table[[:space:]]+(if[[:space:]]+not[[:space:]]+exists[[:space:]]+)?[a-z0-9_."]+' \
        | awk '{print $NF}' | tr -d '"' | sed 's/^public\.//' | sort -u || true)

    TABELAS_SEM_RLS=0
    for tabela in $TABELAS; do
        tabela_regex="${tabela//./\\.}"
        if ! printf '%s\n' "$INSTRUCOES" | grep -qE "alter[[:space:]]+table[[:space:]]+(if[[:space:]]+exists[[:space:]]+)?(only[[:space:]]+)?(public\.)?\"?${tabela_regex}\"?[[:space:]]+enable[[:space:]]+row[[:space:]]+level[[:space:]]+security"; then
            TABELAS_SEM_RLS=$((TABELAS_SEM_RLS + 1))
            RELATORIO="$RELATORIO\n  - Tabela sem RLS: $tabela"
        fi
    done

    if [ "$TABELAS_SEM_RLS" -gt 0 ]; then
        RELATORIO="$RELATORIO\n[SEGURANCA] $TABELAS_SEM_RLS tabela(s) sem Row Level Security"
        echo "  AVISO — $TABELAS_SEM_RLS tabela(s) sem RLS"
        marcar_alerta
    else
        echo "  PASS — todas as tabelas com RLS"
    fi

    # Chaves estrangeiras: divide cada instrucao nas virgulas de nivel 1 (as
    # definicoes de coluna/constraint dentro de "create table (...)"); cada
    # pedaco com "references" precisa ter "on delete" no mesmo pedaco.
    FK_SEM_DELETE=$(printf '%s\n' "$INSTRUCOES" | awk '
        {
            depth = 0; piece = ""
            for (i = 1; i <= length($0); i++) {
                c = substr($0, i, 1)
                if (c == "(") depth++
                if (c == ")") depth--
                if ((c == "," && depth == 1) || i == length($0)) {
                    piece = piece c
                    if (piece ~ /references/ && piece !~ /on[ \t]+delete/) missing++
                    piece = ""
                } else {
                    piece = piece c
                }
            }
        }
        END { print missing + 0 }
    ')

    if [ "$FK_SEM_DELETE" -gt 0 ]; then
        RELATORIO="$RELATORIO\n[SEGURANCA] $FK_SEM_DELETE chave(s) estrangeira(s) sem ON DELETE definido"
        echo "  AVISO — $FK_SEM_DELETE FK(s) sem ON DELETE"
        marcar_alerta
    else
        echo "  PASS — toda chave estrangeira declara ON DELETE"
    fi
fi

# ───────────────────────────────────────────────────────
# RELATORIO FINAL
# ───────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════"
echo "  RESULTADO: $RESULTADO_FINAL"
echo "═══════════════════════════════════════════════════"

if [ -n "$RELATORIO" ]; then
    echo -e "$RELATORIO"
fi

echo ""
if [ "$RESULTADO_FINAL" = "FAIL" ]; then
    exit 1
fi
exit 0
