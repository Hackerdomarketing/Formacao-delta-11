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

## PRÓXIMA TAREFA
[1 linha. Se não há, escreva "aguardando próxima fase".]

---

**O QUE NÃO ENTRA AQUI** (vai para `[NOME-AGENTE]-historia.md`):
- Como chegou aqui · Tentativas · Deliberações · Versões descartadas · Logs · Métricas detalhadas · Notas para eu-futuro

**Teste de Cold Start:** se o sub-agente `cold-start-tester` consegue descrever o sistema corretamente lendo apenas este arquivo, está pronto. Se não conseguir, você compactou mal.
