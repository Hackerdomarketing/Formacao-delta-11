# Design Patterns Práticos — Base de Conhecimento Δ-11

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Padrão aplicado sem sintoma real no código = cargo cult = reprovável.

**Quem lê:** BACK e FRONT (líderes técnicos/revisores) leem INTEIRA na primeira ativação de fase de código. ENGINE, PIXEL, FORM, VAULT, SCOUT consultam a seção do padrão ANTES de criar estrutura nova (fábrica, fila, cache, variação de algoritmo, undo). SHIELD usa a seção "Quando REPROVAR" em toda revisão.

**Curso completo (aprofundamento):** cada padrão tem um mini-curso de 1.000-1.800 linhas em `~/.claude/skills/design-patterns-padroes-de-projetos-de-codigo/references/` (fundamentos em `00-fundamentos-de-padroes-de-projeto.md`). REGRA: ao APLICAR um padrão não trivial, ler o arquivo daquele padrão antes de codificar — o material tem erros comuns e controvérsias que a memória do modelo não tem.

---

## 1. O que é padrão de projeto (e o que NÃO é)

Padrão de projeto é uma solução com nome para um problema recorrente de estrutura de código. O valor para o Δ-11 é dobro: (1) vocabulário comum — o revisor diz "troque por Factory" em vez de reexplicar o conceito; (2) soluções já testadas por décadas em vez de improviso.

**Padrão é remédio para dor real, não vitamina.** A causa nº 1 de código ruim com padrões é aplicá-los sem sintoma ("cargo cult").

## 2. AS 5 PERGUNTAS DE VALIDAÇÃO (obrigatórias ANTES de aplicar qualquer padrão)

1. O problema realmente existe HOJE no código? (não projetar para futuro imaginado)
2. Existe solução mais simples? (uma função, uma classe, um objeto simples)
3. Consigo explicar o problema que o padrão resolve em termos DESTE código específico?
4. O padrão está no contrato/mini-plano ou é invenção minha? (invenção estrutural → SendMessage ao CRONOS)
5. A linguagem já resolve isso nativamente? (módulos em Node/TypeScript JÁ são singletons; funções de primeira classe substituem Strategy simples; `for...of` já é Iterator)

Qualquer dúvida em qualquer resposta → use a solução simples e registre no `[AGENTE]-produto.md` por que o padrão foi dispensado.

## 3. Padrões que o Δ-11 JÁ USA (agora com nome)

Estes já estão nas outras bases de conhecimento — aqui ganham o nome oficial, para o vocabulário do time:

| O que o Δ-11 já faz | Nome do padrão | Onde está documentado |
|---|---|---|
| `getStripe()` — serviço externo inicializado sob demanda dentro de função, com cache da instância | **Factory** (com lazy initialization) | nextjs-api-patterns §8, backend-integracao §5 |
| Timeout + retry com backoff + pausa após 5 falhas | **Circuit Breaker** (padrão de resiliência) | regras-codigo §3 |
| Integração externa atrás de pasta nomeada pela FUNÇÃO (`observabilidade/monitoramento-de-erros/`), vendor trocável | **Adapter** | Regra Inviolável 15 |
| Funções de `src/lib/` que escondem subsistema complexo atrás de chamada simples | **Facade** | estrutura padrão do projeto |
| Middleware de autenticação → validação → handler | **Chain of Responsibility** | nextjs-api-patterns §4 |
| Webhooks e eventos que notificam interessados | **Observer** | regras-codigo §3 (idempotência) |
| Compound components do React (`<Tabs><Tabs.Panel/></Tabs>`) | **Composite** (composição) | react-component-patterns §7 |
| Cache na frente de query cara | **Proxy** (de cache) | backend-integracao §2 |

**Implicação prática:** se você vai fazer uma dessas coisas, o padrão de referência JÁ EXISTE nas bases — siga o exemplo documentado, não invente estrutura nova.

## 4. Árvore de decisão rápida (qual padrão para qual sintoma)

```
O problema é CRIAR objetos?
├── Serviço externo/objeto caro que não pode nascer no nível do módulo → Factory (getX() sob demanda)
├── Objeto com muitos parâmetros opcionais (construtor telescópico) → Builder
└── Exatamente uma instância → em Node/TS, o MÓDULO já é singleton; não crie classe Singleton

O problema é ESTRUTURAR/COMPOR?
├── Interface de vendor incompatível com o que o código espera → Adapter (e Regra 15)
├── Subsistema complexo que todo mundo chama errado → Facade em src/lib/
├── Árvore de itens (categoria contém categoria contém produto) → Composite
├── Somar comportamento sem explosão de variações → Decorator
└── Controlar acesso (cache, lazy, permissão) → Proxy

O problema é COMPORTAMENTO?
├── Cadeia de verificações (auth → rate limit → validação → handler) → Chain of Responsibility
├── Ação como objeto: fila de jobs, undo, agendamento → Command
├── Um evento, muitos interessados (webhook, pub/sub, estado React) → Observer
├── Comportamento muda com o status (pedido: rascunho→pago→enviado) → State
├── Algoritmos intercambiáveis (frete por transportadora, desconto por plano) → Strategy
└── Esqueleto fixo com passos variáveis (pipeline de importação) → Template Method
```

Padrões que quase nunca cabem na stack Δ-11 (Next.js + Supabase, apps de negócio): Flyweight, Visitor, Interpreter, Bridge, Prototype, Mediator. Se parecer que precisa de um deles, releia as 5 perguntas — e leia o curso do padrão antes (`references/NN-*.md`), especialmente a seção "Quando NÃO usar".

## 5. Os 4 padrões mais úteis no Δ-11 — forma canônica

### Factory (criação sob demanda) — o mais usado

```typescript
// Padrão canônico do Δ-11 para TODO serviço externo (Stripe, Resend, etc.)
let stripeInstance: Stripe | null = null;

function getStripe(): Stripe {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error('Configuração de pagamento ausente'); // mensagem em português
  }
  if (!stripeInstance) {
    stripeInstance = new Stripe(process.env.STRIPE_SECRET_KEY);
  }
  return stripeInstance;
}
```

### Strategy (variações de regra de negócio sem if/else gigante)

```typescript
// Sintoma que pede Strategy: switch/if-else que cresce a cada variação nova
const shippingCalculators: Record<CarrierName, ShippingCalculator> = {
  correios: calculateCorreiosShipping,
  jadlog: calculateJadlogShipping,
  retirada: () => 0,
};

function calculateShipping(carrier: CarrierName, order: Order): number {
  const calculate = shippingCalculators[carrier];
  if (!calculate) throw new Error(`Transportadora não suportada: ${carrier}`);
  return calculate(order);
}
// Em TypeScript, Strategy = objeto de funções. NÃO criar hierarquia de classes pra isso.
```

### State (status que muda comportamento)

```typescript
// Sintoma: if (status === 'x') espalhado por vários arquivos
const orderTransitions: Record<OrderStatus, OrderStatus[]> = {
  draft: ['paid', 'cancelled'],
  paid: ['shipped', 'refunded'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
  refunded: [],
};

function canTransition(from: OrderStatus, to: OrderStatus): boolean {
  return orderTransitions[from].includes(to);
}
// A tabela de transições vira a ÚNICA fonte de verdade do fluxo — e vira teste de contrato.
```

### Adapter (vendor trocável — materializa a Regra 15)

**Fluxo obrigatório (v5.4 E1 — F15):** ANTES de escrever o Adapter,
cumprir a **Regra 14** (registrar a ferramenta externa em
`.delta-11/memoria/ferramentas-do-projeto.md`). A sequência completa:

1. **Regra 14** — registrar a ferramenta (vendor, plano, chaves, docs) em
   `.delta-11/memoria/ferramentas-do-projeto.md` usando o template
   `.delta-11/templates/ferramentas-do-projeto-template.md`.
2. **Regra 15** — criar a pasta `src/lib/[dominio]/[etapa]/` nomeada pela
   FUNÇÃO (não pelo vendor), com `README.md` ao lado do código documentando
   a integração.
3. **Adapter propriamente dito** — interface interna que o resto do código
   consome; o vendor fica escondido atrás dela.

```typescript
// src/lib/observabilidade/monitoramento-de-erros/index.ts
// O resto do código chama ESTA interface; o vendor (Sentry) fica escondido atrás dela.
export function captureError(error: unknown, context: ErrorContext): void {
  Sentry.captureException(error, { extra: context });
}
// Trocar de vendor = reescrever 1 arquivo, não caçar chamadas no projeto inteiro.
```

**Erro comum (v5.4 — F15):** pular a Regra 14 e ir direto para a Regra 15
(escrever o Adapter) "porque é mais rápido". Resultado: 3 meses depois,
ninguém lembra qual é a chave de produção, quem tem acesso, ou como
rotacionar — o Adapter virou dependência invisível.

## 6. Erros de nomenclatura que REPROVAM em revisão

- `@decorator` do Python/TypeScript NÃO é o padrão Decorator (é metaprogramação)
- Simple Factory (função que faz `switch` e retorna instância) NÃO é Factory Method GoF — é um idioma, e geralmente é o SUFICIENTE
- Strategy ≠ State: estrutura igual, intenção diferente — State transiciona sozinho, Strategy é escolhido de fora
- Adapter ≠ Facade ≠ Proxy: forma parecida; a INTENÇÃO define o padrão (converter interface ≠ simplificar acesso ≠ controlar acesso)
- Classe Singleton stateful global em Next.js = bug em potencial (serverless recria processos; estado global não sobrevive) — cache por módulo é o limite

## 7. Quando REPROVAR (SHIELD, BACK e FRONT como revisores)

1. **Padrão sem sintoma** — estrutura de padrão onde uma função resolvia: reprovar como over-engineering (cita a pergunta 2)
2. **Padrão errado para o problema** — ex: Strategy onde era State; exigir o nome certo e a forma canônica
3. **Singleton com estado mutável global** — reprovar sempre em Next.js
4. **Hierarquia de classes onde objeto de funções basta** — TypeScript tem funções de primeira classe; herança para Strategy/Command simples é ruído
5. **Padrão que viola limites estruturais** — padrão não é licença para arquivo de 600 linhas; se a estrutura estourou os limites da seção 8, a decomposição está errada

## Fonte

Derivado da skill `design-patterns-padroes-de-projetos-de-codigo` (curso de 23 padrões GoF triangulado de refactoring.guru pt-br + GoF 1994 + fontes independentes, criado em 2026-07-07) — os cursos completos com exercícios, controvérsias e exemplos em 3 linguagens vivem em `~/.claude/skills/design-patterns-padroes-de-projetos-de-codigo/references/`.
