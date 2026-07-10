#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do runner de golden baselines (rodar-comparacao.sh)
# ════════════════════════════════════════════════════════════════
#
# Estratégia (v5.4 E0): o runner é ferramenta do COMANDANTE (dispara
# prompts em janelas Claude Code dedicadas), mas precisamos validar que
# ele não quebra em regressão. Este teste:
#
#   1. Cria diretório temporário com 2 tarefas-fake em
#      golden-baselines/tarefas/ (em sandbox, não no repo real).
#   2. Executa o runner apontando para esse diretório.
#   3. Verifica que:
#      - Criou execucoes/AAAA-MM-DD-vTEST/
#      - MANIFESTO.md existe e tem tabela
#      - Cada subdiretório tem prompt-de-ativacao.txt + gabarito.md
#      - Exit code = 0
#
# IMPORTANTE: NÃO tocamos em execucoes/ real nem em golden-baselines/
# real. Tudo dentro de /tmp.
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Setup sandbox
SANDBOX="$(mktemp -d /tmp/delta11-golden-test-XXXXXX)"
FAKE_TAREFAS="$SANDBOX/tarefas"
FAKE_RUBRICA="$SANDBOX/rubrica-de-avaliacao.md"
mkdir -p "$FAKE_TAREFAS"

cleanup() { rm -rf "$SANDBOX"; }
trap cleanup EXIT

# Criar 2 tarefas-fake no padrão do runner
cat > "$FAKE_TAREFAS/engine-tarefa-fake.md" << 'EOF'
# Tarefa Canônica: ENGINE — Tarefa Fake (TESTE)

## Contexto
Brief curto só para o teste automatizado.

## Bloco de Ativação

```
Ativar agente ENGINE.
Tarefa: criar endpoint de teste.
Saída esperada: src/api/test.ts
```

## Gabarito

- [ ] Endpoint retorna 200
- [ ] Validação de input presente
- [ ] Testes cobrem happy path
EOF

cat > "$FAKE_TAREFAS/vault-tarefa-fake.md" << 'EOF'
# Tarefa Canônica: VAULT — Tarefa Fake (TESTE)

## Contexto
Brief curto só para o teste automatizado.

## Bloco de Ativação

```
Ativar agente VAULT.
Tarefa: criar tabela de teste.
Saída esperada: supabase/migrations/test.sql
```

## Gabarito

- [ ] Tabela com PK
- [ ] RLS habilitado
- [ ] Política usuário-próprio
EOF

cat > "$FAKE_RUBRICA" << 'EOF'
# Rubrica de Avaliação (TESTE)
EOF

# Adaptar o runner para usar o sandbox via variáveis
# (mais simples: copiar o runner e patchar paths com sed)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# tests/scripts/ → tests/ → .delta-11/ → raiz do repo → golden-baselines/
RUNNER_ORIG="$SCRIPT_DIR/../../../golden-baselines/rodar-comparacao.sh"

if [ ! -f "$RUNNER_ORIG" ]; then
    echo -e "${RED}[FAIL]${NC} runner nao encontrado: $RUNNER_ORIG"
    exit 1
fi

RUNNER_TESTE="$SANDBOX/runner-teste.sh"
cp "$RUNNER_ORIG" "$RUNNER_TESTE"
sed -i '' "s|TAREFAS_DIR=\\\"\$SCRIPT_DIR/tarefas\\\"|TAREFAS_DIR=\\\"$FAKE_TAREFAS\\\"|" "$RUNNER_TESTE" 2>/dev/null \
    || sed -i "s|TAREFAS_DIR=\\\"\$SCRIPT_DIR/tarefas\\\"|TAREFAS_DIR=\\\"$FAKE_TAREFAS\\\"|" "$RUNNER_TESTE"
sed -i '' "s|EXECUCOES_DIR=\\\"\$SCRIPT_DIR/execucoes\\\"|EXECUCOES_DIR=\\\"$SANDBOX/execucoes\\\"|" "$RUNNER_TESTE" 2>/dev/null \
    || sed -i "s|EXECUCOES_DIR=\\\"\$SCRIPT_DIR/execucoes\\\"|EXECUCOES_DIR=\\\"$SANDBOX/execucoes\\\"|" "$RUNNER_TESTE"
sed -i '' "s|RUBRICA=\\\"\$SCRIPT_DIR/rubrica-de-avaliacao.md\\\"|RUBRICA=\\\"$FAKE_RUBRICA\\\"|" "$RUNNER_TESTE" 2>/dev/null \
    || sed -i "s|RUBRICA=\\\"\$SCRIPT_DIR/rubrica-de-avaliacao.md\\\"|RUBRICA=\\\"$FAKE_RUBRICA\\\"|" "$RUNNER_TESTE"

# Executar
if ! bash "$RUNNER_TESTE" vTEST >/dev/null 2>&1; then
    echo -e "${RED}[FAIL]${NC} runner retornou exit != 0"
    exit 1
fi

# Verificações
DATA="$(date +%Y-%m-%d)"
DESTINO="$SANDBOX/execucoes/$DATA-vTEST"

falhou=0

# 1. MANIFESTO.md existe
if [ ! -f "$DESTINO/MANIFESTO.md" ]; then
    echo -e "${RED}[FAIL]${NC} MANIFESTO.md nao criado em $DESTINO"
    falhou=$((falhou + 1))
fi

# 2. Tem 2 subdiretórios
subdirs=$(find "$DESTINO" -mindepth 1 -maxdepth 1 -type d | wc -l | xargs)
if [ "$subdirs" -ne 2 ]; then
    echo -e "${RED}[FAIL]${NC} esperado 2 subdiretorios, encontrado $subdirs"
    falhou=$((falhou + 1))
fi

# 3. Cada subdiretório tem prompt-de-ativacao.txt + gabarito.md
for d in "$DESTINO"/*/; do
    [ -d "$d" ] || continue
    if [ ! -f "$d/prompt-de-ativacao.txt" ]; then
        echo -e "${RED}[FAIL]${NC} $(basename "$d"): prompt-de-ativacao.txt ausente"
        falhou=$((falhou + 1))
    fi
    if [ ! -f "$d/gabarito.md" ]; then
        echo -e "${RED}[FAIL]${NC} $(basename "$d"): gabarito.md ausente"
        falhou=$((falhou + 1))
    fi
done

# 4. MANIFESTO tem tabela com 2 linhas (após o cabeçalho markdown)
linhas_tabela=$(grep -c "^| " "$DESTINO/MANIFESTO.md" || true)
if [ "$linhas_tabela" -lt 2 ]; then
    echo -e "${RED}[FAIL]${NC} MANIFESTO sem tabela com 2 entradas (encontradas: $linhas_tabela)"
    falhou=$((falhou + 1))
fi

if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} golden runner: MANIFESTO + 2 subdirs + prompts + gabaritos criados"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} $falhou verificacao(oes) falharam"
    exit 1
fi