# [NOME-AGENTE] — Produto

**⚠️ LIMITE DURO (Mecanismo M4): 500 tokens (≈ 2000 caracteres) para os 8 agentes que não são ATLAS nem CRONOS (BACK, FRONT, PIXEL, FORM, ENGINE, VAULT, SHIELD, SCOUT). O valor vem de `produto_max_tokens` em `.delta-11/.config-limites.json`; o hook `pre-selo.py` bloqueia a transição de fase se ultrapassar.**

**Onde fica:** `memoria/[NOME-AGENTE]-produto.md` na pasta PRINCIPAL do projeto (nunca dentro da worktree). Junto com ele existe `memoria/[NOME-AGENTE]-historia.md` (diário, sem limite). O antigo `[NOME-AGENTE]-estado.md` é LEGADO — pode ser lido se existir, nunca escrito (D8).

**EXCEÇÃO v4.0.4:** ATLAS (arquiteto) e CRONOS (orquestrador) ficam **SEM LIMITE** — carregam visão arquitetural multi-fase e estado de despachança multi-onda que legitimamente não cabem em 500 tokens. Aplica-se apenas a estes dois.

**Princípio (Gênesis 1:2):** "E a terra era sem forma e vazia" — estado inicial compactado em UMA frase. O que existe, não como foi feito.

---

## O QUE EXISTE AGORA (que não existia antes desta tarefa/fase)
[3-5 frases funcionais. Orientadas a RESULTADO, não a processo. Leia: um agente novo que nunca viu o projeto consegue entender o que existe agora só lendo isso?]

## COMO ESTÁ ESTRUTURADO
[Arquitetura, contratos, dependências — mínimo que a próxima fase/agente precisa saber para construir em cima sem ter que inspecionar o código.]

## O QUE FOI DECIDIDO NÃO FAZER
[Lista explícita. Cada item que alguém poderia assumir que existe mas NÃO existe. Evita suposição em fase seguinte.]

## DESCOBERTAS QUE AFETAM FASES FUTURAS
[Apenas o que muda critérios ou arquitetura das fases seguintes. NÃO descobertas interessantes sem impacto operacional.]

## PORQUÊS-CHAVE (v5 — máximo 3 itens, 1 linha cada)
[Decisões NÃO óbvias e o motivo curto. Só registre quando a escolha pareceria estranha sem o porquê. Ex:
- "Promise.race em /health (não Promise.all): previne cascata se FTS estiver lento"
- "LIMIT 1000 (não 500): equilibra round-trips vs timeout CPU"
- "Mantive sincronizarProdutosDaChave: 5 call sites legítimos ainda usam"]

## DESVIOS DO PLANO (v5 — máximo 3 itens, 1 linha cada)
[Só preencher se você mudou rota em relação ao mini-plano. Cite tarefa + desvio + motivo. Ex:
- "T-714: usei OFFSET em vez de cursor — projeto pequeno, OFFSET é OK por ora"
Se não houve desvios, escreva "Nenhum — segui o mini-plano exatamente."]

## RELATÓRIOS DE SUB-AGENTES (v5 — 1 linha por sub-agente disparado)
[OBRIGATÓRIO para os 8 executores. Formato: `<sub-agente>: <PASS|FAIL> / <métrica chave>`. Ex:
- "build-validator: PASS / 119 testes / 0 warnings"
- "contract-tester: PASS / 0 desvios"]

## AUTOCRÍTICA (v5.3 — OBRIGATÓRIO para os 8 executores; ver Passo 3.4 do CLAUDE.md)
[Uma linha com o path exato do log — o SHIELD lê este arquivo antes de revisar; ausência ou path errado = tarefa devolvida sem revisão. Formato:
- "autocritica: .delta-11/logs/autocritica/[AAAA-MM-DD]-[T-XXX]-[NOME].md"
A linha começa exatamente com `autocritica: ` — é obrigatória e é conferida pelo SHIELD e pelos vigias.]

autocritica: .delta-11/logs/autocritica/[AAAA-MM-DD]-[T-XXX]-[NOME].md

## PROPOSTAS PARA O PROJECT-CORE (v6.3 — D7)
[Só o ATLAS escreve no project-core e nas fatias. Se você descobriu algo que deveria entrar lá (contrato
ambíguo, coluna com nome diferente, decisão técnica nova), escreva aqui em 1 linha por item; o CRONOS encaminha
ao ATLAS. Padrão quando não há nada: "Nenhuma".]

Nenhuma

## PRÓXIMA TAREFA
[1 linha. Se não há, escreva "aguardando próxima fase".]

---

## EXEMPLO COMPLETO PREENCHIDO (v6.3 — pilha padrão Supabase, nomes de código em inglês)

> Para agentes novos: este é um exemplo realista de como o arquivo fica
> depois de uma tarefa de ENGINE. Use como referência visual do que
> "bem preenchido" significa — copy a estrutura, não os detalhes.

```markdown
# ENGINE — Produto

**⚠️ LIMITE 500 TOKENS — este exemplo tem ~470. Dentro do orçamento.**

## O QUE EXISTE AGORA
Rota `POST /api/v1/orders` cria pedido aplicando cupom no servidor e gravando
em `orders` + `order_items` numa única função do banco (transação). Idempotency-Key
no header evita duplicação em retry. Retorna 201 com Location header apontando para
`GET /api/v1/orders/{id}`. Campo inválido → 400 `VALIDATION_ERROR`.

## COMO ESTÁ ESTRUTURADO
- src/app/api/v1/orders/route.ts: handler com Zod + `@supabase/ssr` + `getUser()`
- src/lib/orders/calculate-cart-total.ts: função pura testada (cupom, frete, impostos)
- supabase/migrations/20261014130500_create_orders.sql: 3 tabelas (orders, order_items, coupons) + RLS + função `create_order`
- Contrato: ver .delta-11/memoria/project-core/contratos.md#post-api-v1-orders

## O QUE FOI DECIDIDO NÃO FAZER
- Sem webhook de pagamento (só síncrono) — futuro, fora desta fase
- Sem multi-currency (só BRL) — pre-requisito de i18n pendente
- Sem retry interno (idempotency-key no cliente é suficiente)

## DESCOBERTAS QUE AFETAM FASES FUTURAS
- `calculateCartTotal()` precisa virar exportável para o BACK usar no carrinho — não mexer
  em assinatura sem avisar

## PORQUÊS-CHAVE
- Transação via função SQL `create_order` (chamada com `supabase.rpc`): o cliente JS não abre transação; erro aborta tudo
- Idempotency-Key por header (não body): RFC padrão, clientes já conhecem
- LIMIT 1000 itens por order: equilibra round-trips vs timeout de transação

## DESVIOS DO PLANO
- T-042: usei `Promise.allSettled` em vez de `Promise.all` para sub-queries —
  estava no plano `Promise.all`, mas `allSettled` previne cascata se FTS falhar

## RELATÓRIOS DE SUB-AGENTES
- build-validator: PASS / 119 testes / 0 warnings
- contract-tester: PASS / 14 testes / 0 desvios

## AUTOCRÍTICA
- autocritica: .delta-11/logs/autocritica/2026-10-14-T-042-ENGINE.md

## PROPOSTAS PARA O PROJECT-CORE
- Nenhuma

## PRÓXIMA TAREFA
T-043: GET /api/v1/orders/{id} com paginação de order_items.
```

**Por que este exemplo importa:** sem exemplo preenchido, o
agente novo preenche cada seção na dúvida — formato inconsistente entre
agentes, SHIELD precisa reabrir tarefa para pedir reformatação. Com exemplo,
o caminho "óbvio" é copiar a estrutura e preencher com conteúdo real.

---

**O QUE NÃO ENTRA AQUI** (vai para `[NOME-AGENTE]-historia.md`):
- Como chegou aqui · Tentativas · Deliberações · Versões descartadas · Logs · Métricas detalhadas · Notas para eu-futuro

**Teste de Cold Start:** se o sub-agente `cold-start-tester` consegue descrever o sistema corretamente lendo apenas este arquivo, está pronto. Se não conseguir, você compactou mal.

**Disciplina v5:** as seções (PORQUÊS / DESVIOS / RELATÓRIOS / PROPOSTAS) precisam caber junto com tudo nos 500 tokens. Se estourar, compacte MAIS — não suba o limite. Se um porquê precisa de 3 linhas pra explicar, ele provavelmente é uma decisão de história (vai pro historia.md), não de produto.
