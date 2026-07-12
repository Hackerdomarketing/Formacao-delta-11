# Protocolo da Fase 3.5 — Ritmo Temporal (Dia 4 da Metodologia Gênesis)

> **Protocolo formal da Fase 3.5 que existe no fluxo entre a Fase 3 (Fundação) e a Fase 4 (Desenvolvimento).**
> **Esta fase foi adicionada no v6.0.0 para corrigir o achado #4 da auditoria (Furo Principal).**
>
> **Cross-references:**
> - Fluxo principal: `.delta-11/protocolos/fluxo-zero-ao-lancamento.md` → seção "FASE 3.5 — RITMO TEMPORAL"
> - Base conceitual: `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4 (Os Astros — o Ritmo Temporal do Sistema)
> - Template dos 10 artefatos: `.delta-11/templates/fase-ritmo-template.md`
> - Hook bloqueante: `.delta-11/hooks/fase-ritmo-checker.py`

## O que é o Dia 4 — em linguagem da Metodologia Gênesis

Texto hebraico chave (Gênesis 1:14-19):

> *yehi meorot bi-rekia ha-shamayim le-havdil bein ha-yom u-vein ha-laila* — "haja luminares no firmamento dos céus para separar entre o dia e entre a noite"
> *le-memshelet ha-yom u-le-memshelet ha-laila* — "para governança do dia e para governança da noite"

Significado: antes de existir qualquer habitante (Dia 5), Deus cria os **astros** — os marcadores de **tempo** que governam quando cada coisa acontece. No software, isso é o **ritmo temporal do sistema**: como requisições, eventos, jobs, caches e deploys se comportam no tempo.

## Quando NÃO aplicar esta fase (exceções legítimas)

A Fase 3.5 **não se aplica** em um número muito pequeno de casos. É mais honesto listar explicitamente para que a regra não vire burocracia cega:

1. **Projetos descartáveis (prototipação rápida, hackathon, prova de conceito de 1 dia)** — se o projeto vai ser jogado fora, o Dia 4 pode ser pulado conscientemente. Documentar no kanban: "Projeto X sem Fase 3.5 — escopo descartável, sem operação autônoma esperada".
2. **Sistema toy sem produção** — se o projeto NUNCA vai a produção (ex: exemplo didático, demo), o ritmo temporal é trivial. Mas se for para produção, Fase 3.5 é OBRIGATÓRIA mesmo que "mínima".

Em QUALQUER outro caso (incluindo MVP, produto real, sistema interno, B2B, B2C), **a Fase 3.5 é obrigatória**.

## Os 10 artefatos do Dia 4 — declaração completa

Cada artefato vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<N>-<slug>.md` (template em `fase-ritmo-template.md`). Cada arquivo tem pelo menos: descrição, escolha tecnológica, justificativa, link para documentação.

### Artefato 1 — Sistema de eventos declarado

**O que:** Catálogo de todos os eventos assíncronos do sistema (não implementação). Quais eventos existem, quem produz, quem consome.

**Por que:** sem catálogo, ninguém sabe quem dispara o quê. Quando um consumidor é criado, ele não tem onde achar o contrato do produtor.

**Exemplos de eventos comuns:** `order.created`, `payment.confirmed`, `user.registered`, `email.sent`, `webhook.received`. Cada um com: nome, schema (Zod/JSON Schema), produtor, consumidores, retenção.

**Não confundir com:** sistema de mensageria (artefato 2). Eventos são conceitos; filas são implementação.

### Artefato 2 — Sistema de mensageria e filas configurado

**O que:** Decisão e configuração da tecnologia de filas.

**Opções comuns:**
- **Inngest** — bom para Next.js + funções serverless
- **BullMQ** — bom para Node.js + Redis
- **RabbitMQ** — bom para sistemas com alta vazão
- **Kafka** — bom para event sourcing / stream processing
- **SQS / PubSub** — bom para serverless puro (AWS / GCP)
- **Redis Streams** — bom para baixa-média escala
- **pg_listen / Supabase Realtime** — bom se já usa Postgres

A escolha vira um ADR ou secção no `project-core.md`.

### Artefato 3 — Jobs agendados mapeados

**O que:** Lista de todos os jobs recorrentes do sistema com cron expression, dono, e último log de execução.

**Por que:** sem mapa, ninguém sabe que existe o job das 3h da manhã que limpa tokens expirados.

**Formato:** tabela com colunas `[nome | expressão cron | dono | última execução | propósito]`. Em código: arquivo `src/lib/jobs/` ou `ops/cron/` listando todos.

### Artefato 4 — Estratégia de cache com TTL por tipo de dado

**O que:** Para cada categoria de dado, declarar: o que cachear, em qual camada (edge, app, DB), TTL específico, política de invalidação.

**Por que:** sem TTL explícito, cache vira problema (dados stale). O número "5 minutos" sozinho não serve — cada dado tem seu TTL.

**Exemplo:**
```
| Dado              | Camada | TTL      | Invalidação       |
|-------------------|--------|----------|-------------------|
| User profile      | Edge   | 1 hora   | On update         |
| Listagem produtos | App    | 15 min   | On product change |
| Static assets     | CDN    | 30 dias  | On deploy         |
```

### Artefato 5 — Timeouts declarados por tipo de operação

**O que:** Cada tipo de operação tem timeout numérico explícito.

**Padrão recomendado:**
- HTTP request: 5s
- Database query: 3s
- RPC síncrono: 5s
- Fila consumer: 30s (ou conforme trabalho)
- Email send: 10s
- Webhook receiver: 5s (responde rápido)

`regras-codigo.md:81-93` já documenta timeout 5s para APIs externas. Este artefato **generaliza** para qualquer tipo.

### Artefato 6 — Retries com backoff exponencial

**O que:** Política de retry documentada por dependência externa.

**Padrão:** 3 tentativas com backoff 1s, 2s, 4s. Jitter opcional para evitar thundering herd.

`regras-codigo.md:84-93` já documenta. Este artefato vira **delcaração obrigatória** (não sugestão) por dependência.

### Artefato 7 — Circuit breakers para dependências externas

**O que:** Para cada dependência externa crítica (Stripe, Resend, OpenAI, etc.), circuit breaker configurado.

**Padrão:** após 5 falhas consecutivas, pausa 60s antes de tentar novamente.

`regras-codigo.md:93` já documenta. Aqui vira entregável: lista de quais dependências têm circuit breaker E evidência (arquivo de config, teste, ou ADR).

### Artefato 8 — CI/CD funcionando de ponta a ponta em staging

**O que:** Pipeline real executando: lint, typecheck, testes, build, deploy em staging. Não pode ser placeholder.

**Componentes mínimos:**
- Arquivo `.github/workflows/ci.yml` ou equivalente (GitLab CI, CircleCI)
- Step de lint
- Step de typecheck
- Step de testes unitários
- Step de testes E2E (se aplicável)
- Step de build
- Step de deploy em staging
- Status badge no README

**Por que é artefato obrigatório:** sem CI/CD real, cada deploy é manual e propenso a erro. A Metodologia exige que o ritmo do sistema seja **confiável**, não manual.

### Artefato 9 — Observabilidade configurada

**O que:** Logs estruturados, métricas (latência, erro, saturação), traces distribuídos, dashboards visíveis.

**Componentes mínimos:**
- Logs: Winston/Pino/etc com JSON estruturado. Convenção de campos.
- Métricas: RED (Rate, Errors, Duration) + USE (Utilization, Saturation, Errors). Provider: Datadog, Grafana, Sentry, ou similar.
- Traces: OpenTelemetry. Cada request tem trace ID propagado.
- Dashboards: 1 dashboard principal com golden signals. Outro dashboard por serviço crítico.
- Alertas: regras para saturação, error rate, latency p95.

**Diferença do Sentry** (que já é obrigatório em outra fase): Sentry captura **erros**. Observabilidade captura **comportamento normal** também.

### Artefato 10 — Sub-contraposição hierárquica declarada

**O que:** Declaração explícita de quais processos são **dominantes ativos** (governam) e quais são **testemunhas passivos** (observam).

**Formato:** tabela com colunas `[Processo | Tipo (dominante/testemunha) | Função | Exemplo]`.

**Exemplo:**
```
| Processo                    | Tipo        | Função                       |
|-----------------------------|-------------|------------------------------|
| Cron scheduler              | Dominante   | Dispara jobs no tempo certo  |
| Event dispatcher            | Dominante   | Roteia eventos para handlers |
| Structured logger           | Testemunha  | Reporta o que aconteceu      |
| Metrics collector (Prom)    | Testemunha  | Coleta RED/USE               |
| Health check endpoint       | Testemunha  | Responde "está vivo?"        |
| Dashboard (Grafana)         | Testemunha  | Mostra o estado              |
```

**Por que importa:** sem essa divisão explícita, processos testemunhas viram bloqueantes (ex: loggers viram single point of failure) ou processos dominantes viram invisíveis (ex: scheduler sem métricas ninguém sabe se rodou).

## Endereço canônico dos artefatos

Cada um dos 10 artefatos vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<N>-<slug>.md` (onde `<N>` é 1 a 10 e `<slug>` é nome curto descritivo).

**Exemplo para o projeto hipotético "cofre-de-keys" iniciado em 2026-08-15:**
- `2026-08-15-ritmo-temporal-01-sistema-eventos.md`
- `2026-08-15-ritmo-temporal-02-filas-inngest.md`
- ...
- `2026-08-15-ritmo-temporal-10-sub-contraposicao.md`

Use o template `.delta-11/templates/fase-ritmo-template.md` para preencher cada um.

## Quem sella

A Fase 3.5 consagra com a presença de:
- **Líder técnico da Fundação** (quem desenhou os 10 artefatos)
- **Comandante** (aprovação final)

Sem ambos os selos, a Fase 4 (Desenvolvimento) NÃO pode começar. O hook `fase-ritmo-checker.py` (Etapa 5C do v6.0) bloqueia a transição automaticamente.

## Critério objetivo de selo

Os 10 arquivos `.delta-11/memoria/decisoes/...` existem, cada um com pelo menos 4 seções preenchidas (descrição, escolha, justificativa, link). O líder técnico declara formalmente "Fase 3.5 selada" no kanban com resposta **SUSTENTA**. O Comandante digita `aprovar`.

A partir daí, a Fase 4 pode começar com a confiança de que os habitats do Dia 5 têm ritmo temporal para governá-los.

## Relação com o Roadmap dos 7 Ciclos

O roadmap (`ATLAS.md:411-418`) define "Ciclo 4 — Tempo" como um dos 7 ciclos de **entrega**. A Fase 3.5 **não conflita** com esse ciclo — pelo contrário. A Fase 3.5 constrói a **infraestrutura de ritmo** que sustenta todos os 7 ciclos. O "Ciclo 4 — Tempo" continua sendo a fase de **entrega** de features temporais (notificações, recorrências, métricas temporais). A Fase 3.5 é a **fundação invisível** sem a qual o Ciclo 4 não se sustentaria.

## Manutenção

Este protocolo evolui conforme o sistema amadurece. Mudanças aqui passam por:
1. Proposta via issue
2. Discussão em equipe
3. Decisão via ADR
4. Atualização deste arquivo + template + hook + testes

**Versão do protocolo:** v6.0.0 (2026-07-11)
**Manutenção:** manter sincronizado com `metodologia-genesis-camadas.md` (Dia 4) e `fase-ritmo-template.md`.

---
*Este documento é IMUTÁVEL após publicação. Correções em ADIÇÕES POSTERIORES no CHANGELOG.*