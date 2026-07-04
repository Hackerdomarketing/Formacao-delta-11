# [FUNÇÃO NO PRODUTO — ex: IA da Etapa de Análise Competitiva]

> **Template v5.2 — Configuração de Integração Externa (Regra Inviolável 15)**
> Este arquivo vive em `src/lib/[dominio]/[etapa]/README.md` — AO LADO do código que consome a integração.
> O NOME é pela FUNÇÃO no produto, NUNCA pelo vendor. Se o vendor trocar, o nome continua verdadeiro.
> Antes de preencher este arquivo, atualize também `.delta-11/memoria/ferramentas-do-projeto.md` (Regra Inviolável 14).

---

## Qual etapa do produto esta integração serve

[1-2 frases em linguagem leiga. Ex: "É a inteligência artificial que compara a página do usuário
com as dos concorrentes e gera as 81 análises. Roda dentro do processamento de scan, depois da
extração de conteúdo e antes da montagem dos relatórios."]

## Qual vendor/API implementa hoje

- **Vendor atual:** [ex: Moonshot AI (Kimi)]
- **Desde:** [AAAA-MM-DD]
- **Substituiu:** [vendor anterior, ou "primeira implementação"]
- **Motivo da escolha/troca:** [1-2 frases — custo, qualidade, limite de contexto, etc.]

## Chaves e variáveis de ambiente

| Variável | Onde obter | Onde configurar |
|---|---|---|
| [ex: KIMI_API_KEY] | [ex: platform.moonshot.ai → API Keys] | `.env.local` (dev) + painel da Vercel (produção) |

**NUNCA** colocar o valor real da chave neste arquivo — apenas o NOME da variável.

## Endpoint, modelo e parâmetros críticos

- **Endpoint:** [URL base]
- **Modelo:** [nome exato do modelo]
- **Parâmetros que importam:** [max_tokens, temperature, timeout — só os que afetam o produto]
- **Rate limits conhecidos:** [ex: 60 req/min — e o que o código faz quando bate]

## Fallback e comportamento em falha

- **Se a chave não existir:** [o que o código faz — erro explícito no servidor / degradação graciosa no cliente]
- **Se a API cair:** [retry? circuit breaker? fila? mensagem ao usuário?]
- **Onde está o tratamento:** [`caminho/do/arquivo.ts` — linha aproximada ou nome da função]

## Código que consome esta integração

- [`caminho/arquivo1.ts`] — [o que faz]
- [`caminho/arquivo2.ts`] — [o que faz]

## Histórico de trocas de vendor

| Data | De → Para | Motivo | Quem decidiu |
|---|---|---|---|
| [AAAA-MM-DD] | [Claude API → Kimi] | [custo por análise] | [comandante] |

---

### Checklist antes de dar por concluído

- [ ] Nome do arquivo/pasta é pela FUNÇÃO, não pelo vendor?
- [ ] `.delta-11/memoria/ferramentas-do-projeto.md` foi atualizado (Regra 14)?
- [ ] Variável adicionada ao `.env.example` SEM o valor real?
- [ ] Contrato da rota afetada em `contratos-api.md` continua verdadeiro? (se mudou, escalar ao ATLAS)
