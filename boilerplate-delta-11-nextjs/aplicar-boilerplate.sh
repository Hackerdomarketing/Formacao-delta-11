#!/bin/bash
# Aplica o overlay do boilerplate Δ-11 sobre um projeto Next.js recém-criado.
# Uso: ./aplicar-boilerplate.sh /caminho/do/projeto

DESTINO="$1"

# Validação de variável vazia antes de qualquer operação (regra global de comandos)
[ -z "$DESTINO" ] && echo "ERRO: informe o caminho do projeto. Uso: ./aplicar-boilerplate.sh /caminho/do/projeto" && exit 1
[ ! -d "$DESTINO" ] && echo "ERRO: pasta nao existe: $DESTINO" && exit 1
[ ! -f "$DESTINO/package.json" ] && echo "ERRO: $DESTINO nao parece um projeto Node (sem package.json). Rode 'npx create-next-app@latest' primeiro." && exit 1

# v5.4 (E1 — F11): checar que src/ existe no destino. O overlay ESPERA
# uma estrutura Next.js padrão (src/app, src/lib, src/components). Se o
# projeto foi criado com create-next-app mas o usuário escolheu NÃO usar
# a pasta src/ (--no-src-dir), a cópia silenciosa para $DESTINO/src/
# cria uma pasta fantasma que nunca é importada. Melhor avisar agora do
# que debugar 30 min depois.
if [ ! -d "$DESTINO/src" ]; then
  echo "ERRO: $DESTINO nao tem pasta src/ (F11)."
  echo "  O overlay do boilerplate Δ-11 ESPERA estrutura Next.js com src/."
  echo "  Solucao: recrie o projeto com 'npx create-next-app@latest' respondendo 'Yes'"
  echo "  para 'Would you like your code inside a src/ directory?', ou mova seu codigo"
  echo "  para dentro de src/ manualmente antes de rodar este script."
  exit 1
fi

ORIGEM="$(cd "$(dirname "$0")/overlay" && pwd)"
[ -z "$ORIGEM" ] && echo "ERRO: pasta overlay nao encontrada ao lado deste script." && exit 1

echo "Aplicando overlay Δ-11:"
echo "  de:   $ORIGEM"
echo "  para: $DESTINO"
echo ""

# v5.4 (E1 — F12): protecao contra sobrescrita. Antes, o script cop iava
# src/, tests/, eslint-limites-delta11.mjs DIRETO sobre o destino. Se o
# usuario ja tinha arquivos com mesmo nome, eram silenciosamente substituídos.
# Agora: se destino ja tem o que sera copiado, faz backup datado e AVISA,
# em vez de sobrescrever. Para forcar sobrescrita: --force na CLI.
FORCE=""
if [ "${2:-}" = "--force" ]; then
    FORCE=1
    echo "  (--force: sobrescrita habilitada, sem backup)"
fi

# Funcao de copia com backup opcional
copiar_com_backup() {
    local src="$1"
    local dst="$2"
    local nome="$(basename "$dst")"

    if [ -e "$dst" ] && [ -z "$FORCE" ]; then
        local backup="$dst.bak-$(date +%Y%m%d-%H%M%S)"
        mv "$dst" "$backup"
        echo "  BACKUP $nome (ja existia) → $(basename "$backup")"
    fi

    cp -R "$src" "$dst"
}

copiar_com_backup "$ORIGEM/src" "$DESTINO/src"
echo "  OK src/lib (env, error-response, monitoramento-de-erros)"

# tests/contracts — só copia se a pasta NÃO existir; se existir, backup
if [ -d "$DESTINO/tests" ]; then
    if [ -z "$FORCE" ]; then
        if [ -d "$DESTINO/tests/contracts" ]; then
            mv "$DESTINO/tests/contracts" "$DESTINO/tests/contracts.bak-$(date +%Y%m%d-%H%M%S)"
            echo "  BACKUP tests/contracts (ja existia)"
        fi
    fi
    mkdir -p "$DESTINO/tests"
fi
cp -R "$ORIGEM/tests/contracts" "$DESTINO/tests/" 2>/dev/null || true
echo "  OK tests/contracts"

copiar_com_backup "$ORIGEM/eslint-limites-delta11.mjs" "$DESTINO/eslint-limites-delta11.mjs"
echo "  OK eslint-limites-delta11.mjs"

if [ -f "$DESTINO/.env.example" ]; then
  if [ -z "$FORCE" ]; then
      local_env_backup="$DESTINO/.env.example.bak-$(date +%Y%m%d-%H%M%S)"
      mv "$DESTINO/.env.example" "$local_env_backup"
      echo "  BACKUP .env.example (ja existia) → $(basename "$local_env_backup")"
  fi
  cp "$ORIGEM/env.example" "$DESTINO/.env.example"
  echo "  OK .env.example (sobrescrito${FORCE:+, via --force} ou mesclado)"
else
  cp "$ORIGEM/env.example" "$DESTINO/.env.example" && echo "  OK .env.example"
fi

echo ""
echo "PROXIMOS PASSOS (manuais, ~2 minutos):"
echo "  1. No eslint.config.mjs do projeto, adicione:"
echo "       import limitesDelta11 from './eslint-limites-delta11.mjs';"
echo "     e inclua limitesDelta11 no array de configs exportado."
echo "  2. (Opcional, recomendado) npm install --save-dev eslint-plugin-sonarjs"
echo "     e ligue sonarjs/cognitive-complexity: ['error', 15]."
echo "  3. Importe assertRequiredEnv() no início do servidor (ex: instrumentation.ts ou layout raiz)."
echo "  4. Quando o projeto caminhar para producao: npx @sentry/wizard@latest -i nextjs"
echo "     (documentacao em src/lib/observabilidade/monitoramento-de-erros/README.md)"
echo ""
echo "OK — overlay aplicado."
