# TEMPLATE — Configuração ESLint dos Limites Estruturais de Código

**O que é:** a tradução técnica da seção 8 do `.delta-11/protocolos/regras-codigo.md` em regras prontas do ESLint [o corretor automático que verifica o código sozinho, como um revisor incansável]. Com isso, os limites deixam de depender de agente lembrar — o linter bloqueia.

**Quem usa:** ENGINE ou FRONT ativa estas regras na Fase 3/4 (primeiro contato com o projeto). O **build-validator** roda o lint e trata violação como BLOCKER.

**Como aplicar:** mesclar o bloco `rules` abaixo no arquivo de configuração ESLint do projeto (`eslint.config.mjs` em projetos Next.js 15+, formato flat config).

```js
// Limites estruturais de código — Formação Δ-11
// Fonte: .delta-11/protocolos/regras-codigo.md seção 8
// NÃO afrouxar valores sem aprovação do comandante.
{
  rules: {
    'max-params': ['error', 3],
    'max-lines-per-function': ['error', { max: 50, skipBlankLines: true, skipComments: true }],
    'max-lines': ['error', { max: 400, skipBlankLines: true, skipComments: true }],
    'max-classes-per-file': ['error', 1],
    'max-depth': ['error', 3],
    'complexity': ['error', 10],
  },
}
```

**Complexidade cognitiva (opcional, recomendado):** exige o plugin `eslint-plugin-sonarjs`:

```bash
npm install --save-dev eslint-plugin-sonarjs
```

```js
import sonarjs from 'eslint-plugin-sonarjs';
// ...no array de configs:
{
  plugins: { sonarjs },
  rules: { 'sonarjs/cognitive-complexity': ['error', 15] },
}
```

**Exceções por arquivo** (gerados, migrations, seeds — regra 8.3):

```js
{
  files: ['supabase/migrations/**', '**/*.generated.*', 'src/lib/database.types.ts'],
  rules: { 'max-lines': 'off', 'max-lines-per-function': 'off' },
}
```

**Componente React ≤ 150 linhas / ≤ 5 props e rota ≤ 150 linhas:** não têm regra ESLint pronta — são verificados pelo build-validator (contagem) e pelo SHIELD na revisão.
