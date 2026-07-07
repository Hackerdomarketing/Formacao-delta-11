#!/bin/bash
# Aplica o overlay do boilerplate Δ-11 sobre um projeto Next.js recém-criado.
# Uso: ./aplicar-boilerplate.sh /caminho/do/projeto

DESTINO="$1"

# Validação de variável vazia antes de qualquer operação (regra global de comandos)
[ -z "$DESTINO" ] && echo "ERRO: informe o caminho do projeto. Uso: ./aplicar-boilerplate.sh /caminho/do/projeto" && exit 1
[ ! -d "$DESTINO" ] && echo "ERRO: pasta nao existe: $DESTINO" && exit 1
[ ! -f "$DESTINO/package.json" ] && echo "ERRO: $DESTINO nao parece um projeto Node (sem package.json). Rode 'npx create-next-app@latest' primeiro." && exit 1

ORIGEM="$(cd "$(dirname "$0")/overlay" && pwd)"
[ -z "$ORIGEM" ] && echo "ERRO: pasta overlay nao encontrada ao lado deste script." && exit 1

echo "Aplicando overlay Δ-11:"
echo "  de:   $ORIGEM"
echo "  para: $DESTINO"
echo ""

cp -R "$ORIGEM/src" "$DESTINO/" && echo "  OK src/lib (env, error-response, monitoramento-de-erros)"
cp -R "$ORIGEM/tests" "$DESTINO/" && echo "  OK tests/contracts"
cp "$ORIGEM/eslint-limites-delta11.mjs" "$DESTINO/" && echo "  OK eslint-limites-delta11.mjs"

if [ -f "$DESTINO/.env.example" ]; then
  echo "  AVISO: .env.example ja existe no destino — conteudo do overlay NAO copiado (mescle manualmente com $ORIGEM/env.example)"
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
