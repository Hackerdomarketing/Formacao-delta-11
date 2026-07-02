# [NOME-AGENTE] — Produto

**⚠️ LIMITE DURO: 500 tokens (≈ 2000 caracteres) para os 8 agentes executores (BACK, FRONT, PIXEL, FORM, ENGINE, VAULT, SHIELD, SCOUT). Hook `pre-selo.py` bloqueia transição de fase se ultrapassar.**

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
- "code-simplifier: APLICADO / 3 simplificações"
- "contract-tester: PASS / 0 desvios"]

## PRÓXIMA TAREFA
[1 linha. Se não há, escreva "aguardando próxima fase".]

---

**O QUE NÃO ENTRA AQUI** (vai para `[NOME-AGENTE]-historia.md`):
- Como chegou aqui · Tentativas · Deliberações · Versões descartadas · Logs · Métricas detalhadas · Notas para eu-futuro

**Teste de Cold Start:** se o sub-agente `cold-start-tester` consegue descrever o sistema corretamente lendo apenas este arquivo, está pronto. Se não conseguir, você compactou mal.

**Disciplina v5:** as novas seções (PORQUÊS / DESVIOS / RELATÓRIOS) precisam caber junto com tudo nos 500 tokens. Se estourar, compacte MAIS — não suba o limite. Se um porquê precisa de 3 linhas pra explicar, ele provavelmente é uma decisão de história (vai pro historia.md), não de produto.
