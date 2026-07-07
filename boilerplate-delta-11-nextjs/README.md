# Boilerplate Δ-11 — Next.js + Supabase (formato overlay)

**O que é:** o esqueleto padrão que faz todo projeto novo do Δ-11 NASCER em conformidade — limites de código no linter, formato único de erro, validação de ambiente, pasta de monitoramento de erros, estrutura de testes de contrato. Em vez de cada projeto reconstruir isso do zero (e cada agente inventar um jeito), a Fase 3 aplica este overlay e ganha tudo pronto.

**Por que "overlay" e não repositório completo:** um repo completo congela versões (Next.js, dependências) e apodrece em meses. O overlay são só os ARQUIVOS NOSSOS, aplicados por cima de um `create-next-app@latest` sempre atual — evergreen por construção.

**Este diretório NÃO é sincronizado para os projetos** — vive no repositório de distribuição; o script copia o que precisa.

## Como usar (VAULT/ENGINE na Fase 3 — Fundação)

```bash
# 1. Criar o projeto com a versão mais atual (responda os prompts: TypeScript sim, ESLint sim, App Router sim, Tailwind sim)
npx create-next-app@latest nome-do-projeto

# 2. Aplicar o overlay Δ-11
~/projetos/Formacao-delta-11/boilerplate-delta-11-nextjs/aplicar-boilerplate.sh /caminho/do/nome-do-projeto

# 3. Seguir os "PRÓXIMOS PASSOS" que o script imprime (ligar o config do ESLint, ~2 min)

# 4. Instalar o Δ-11 no projeto normalmente (instalar.sh) e seguir o fluxo
```

## O que o overlay entrega

| Arquivo | O que faz |
|---|---|
| `eslint-limites-delta11.mjs` | Limites estruturais da seção 8 do regras-codigo.md como regras de linter (build-validator bloqueia violação) |
| `src/lib/env.ts` | Validação de variáveis de ambiente na inicialização — falha ruidosa no boot, não silenciosa em produção |
| `src/lib/api/error-response.ts` | Formato único de erro da API (`{ error, message, details }`) — campos em inglês, mensagens em português |
| `src/lib/observabilidade/monitoramento-de-erros/README.md` | Endereço canônico da integração Sentry (Regra 15 — nome pela função, não pelo vendor) com o passo a passo de instalação |
| `tests/contracts/README.md` | Pasta dos testes de contrato que o contract-tester gera na Fase 2 |
| `.env.example` | Nomes das variáveis padrão (SEM valores) — Supabase + Sentry |

## Manutenção

Mudou uma convenção do sistema (limite, formato de erro, variável padrão)? Atualize o arquivo correspondente AQUI no mesmo commit — o overlay é a materialização das regras; overlay desatualizado distribui regra velha.
