# TEMPLATE — Fase 3.5: Artefato de Ritmo Temporal (Dia 4 da Metodologia Gênesis)

> **O que é:** este template é usado para preencher CADA UM dos 10 artefatos do Dia 4 (Ritmo Temporal).
> Um artefato = um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<N>-<slug>.md`.
> Copie o bloco, substitua os placeholders `{{VARIAVEL}}`, e salve no endereço correto.
>
> **Quem escreve:** Engenheiro de DevOps/SRE + Líder Técnico da Fundação (Etapa 3.5 do fluxo v6.0).
>
> **Quem sella:** Líder técnico + Comandante.
>
> **Quando NÃO preencher:** projetos descartáveis (ver protocolo `fase-ritmo.md` para lista completa).
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4 (Os Astros).
> **Protocolo formal:** `.delta-11/protocolos/fase-ritmo.md`.

---

## Cabeçalho do artefato (preencher uma vez)

```markdown
# Artefato {{NUMERO}} de 10 — {{NOME_ARTEFATO}} (Dia 4 / Fase 3.5)

- **Projeto:** {{NOME_PROJETO}}
- **Data:** {{AAAA-MM-DD}}
- **Autor:** {{NOME_AUTOR}} (VAULT / DevOps / Líder Técnico)
- **Status:** proposta | aceita | substituída
- **Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4

## Descrição

O QUE é este artefato. Por que o sistema precisa dele. NÃO como ele será implementado (isso vem depois, na Fase 4).

Máximo 200 palavras. Deve caber em uma respiração. Se ficou longo, está descrevendo mais de um artefato.

## Escolha

A tecnologia / padrão / formato escolhido. Em uma frase.

Exemplos de escolhas:
- "Inngest" (sistema de filas)
- "Redis com TTL de 15 minutos" (cache)
- "GitHub Actions + Vercel" (CI/CD)
- "Pino + Sentry + Grafana Cloud" (observabilidade)

## Justificativa

Por que ESSA escolha e não outra. Compare com 1-2 alternativas e por que foram descartadas.

Máximo 150 palavras. Foco em: custo, latência, operacional, complexidade.

## Link

URL da documentação oficial ou referência canônica. Se houver ADR relacionado, linkar aqui:
- [ADR-XXX — decisão arquitetural]
- (docs oficiais do provider)

## Implementação (referência — não preencher nesta fase)

Onde isso vai ser codificado na Fase 4:

- Arquivo(s) de código: `{{CAMINHO_ARQUIVOS}}`
- Hooks / módulos: `{{NOMES}}`
- Variáveis de ambiente: `{{ENV_VARS}}`
- Como testar: `{{COMO_TESTAR}}`

---
*Preenchido em {{DATA_PREENCHIMENTO}} | Selado: [ ] Líder técnico | [ ] Comandante*
```

---

## Como preencher os 10 artefatos

Para cada um dos 10 artefatos do Dia 4, copie o cabeçalho acima e preencha as seções. Salve cada artefato em arquivo separado:

| # | Artefato | Slug sugerido | Nome do arquivo |
|---|----------|---------------|-----------------|
| 1 | Sistema de eventos declarado | `sistema-eventos` | `{{DATA}}-ritmo-temporal-01-sistema-eventos.md` |
| 2 | Sistema de mensageria e filas | `filas` | `{{DATA}}-ritmo-temporal-02-filas-{{PROVEDOR}}.md` |
| 3 | Jobs agendados | `jobs` | `{{DATA}}-ritmo-temporal-03-jobs-agendados.md` |
| 4 | Estratégia de cache com TTL | `cache-ttl` | `{{DATA}}-ritmo-temporal-04-cache-ttl.md` |
| 5 | Timeouts declarados | `timeouts` | `{{DATA}}-ritmo-temporal-05-timeouts.md` |
| 6 | Retries com backoff | `retries` | `{{DATA}}-ritmo-temporal-06-retries.md` |
| 7 | Circuit breakers | `circuit-breakers` | `{{DATA}}-ritmo-temporal-07-circuit-breakers.md` |
| 8 | CI/CD em staging | `ci-cd` | `{{DATA}}-ritmo-temporal-08-ci-cd-staging.md` |
| 9 | Observabilidade | `observabilidade` | `{{DATA}}-ritmo-temporal-09-observabilidade.md` |
| 10 | Sub-contraposição declarada | `sub-contraposicao` | `{{DATA}}-ritmo-temporal-10-sub-contraposicao.md` |

Substitua `{{DATA}}` pela data real (`date +%Y-%m-%d`) e `{{PROVEDOR}}` pelo provedor escolhido (inngest/bullmq/etc).

---

## ⚠️ IMPORTANTE — Não avançar para Fase 4 sem preencher

A Fase 4 (Desenvolvimento de Funcionalidade) **não pode começar** antes que os 10 artefatos estejam preenchidos E selados pelo Líder técnico e Comandante. Razão: a Metodologia Gênesis é explícita: "Astros para governar o tempo não foram feitos antes de existir dia e noite". Construir código de funcionalidade sem ritmo temporal é "fazer os peixes antes das águas" — o sistema nasce sem governança de tempo.

O hook `fase-ritmo-checker.py` (Etapa 5C do v6.0) bloqueia automaticamente tentativas de avançar sem os 10 artefatos. Não é burocracia — é o método funcionando.

---

## Exemplo preenchido (artefato #1)

Para referência, eis como fica o Artefato #1 preenchido:

```markdown
# Artefato 1 de 10 — Sistema de eventos declarado (Dia 4 / Fase 3.5)

- **Projeto:** cofre-de-keys
- **Data:** 2026-08-15
- **Autor:** Rafa Marks (CTO)
- **Status:** aceita
- **Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4

## Descrição

O cofre-de-keys é uma plataforma onde cada usuário guarda suas chaves de API de serviços externos. Quando uma chave é criada, diversos eventos precisam acontecer: notificação inicial, entrada em auditoria, integração com sistema de alertas, etc.

Sem catálogo de eventos, cada consumidor novo precisa adivinhar quem produz. O catálogo é o **contrato de eventos** — assim como contratos de API existem para rotas HTTP, contratos de eventos existem para async.

## Escolha

Catálogo versionado em `docs/eventos.md` com schemas Zod. Protobuf seria overkill; JSON Schema permite validação runtime nas bibliotecas consumidoras.

## Justificativa

- Markdown + Zod = legível por humanos + validável por código
- Versionado em git = histórico de mudanças
- Sem dependência externa adicional (Kafka Schema Registry, etc)

Alternativas descartadas:
- Protobuf (overhead desnecessário para 5-10 eventos)
- AsyncAPI (interessante mas adiciona dependência; manter catálogo em MD + Zod é suficiente)

## Link

- [AsyncAPI spec](https://www.asyncapi.com/) (consultado para vocabulário, não adotado)

## Implementação (referência — não preencher nesta fase)

- Arquivo de código: `src/lib/eventos/catalogo.ts` (gerado de eventos.md via ts-codegen)
- Hooks: cada evento tem handler em `src/lib/eventos/handlers/`
- Variáveis: nenhuma
- Como testar: cada handler tem teste que valida schema de input
```

---

**Versão do template:** v6.0.0 (2026-07-11)
**Local canônico:** `.delta-11/templates/fase-ritmo-template.md`
**Proveniência:** criado na Etapa 5B do plano Nível 3 Profundo (auditoria 2026-07-10)