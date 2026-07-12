# TEMPLATE — Fase 4.5: Artefato de Consciência (Dia 6 da Metodologia Gênesis)

> **O que é:** este template preenche CADA UM dos 5 entregáveis do Dia 6 (Consciência Dominante). Um entregável = um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<N>-<slug>.md`. Copie o bloco, substitua os placeholders, salve.
>
> **Quem escreve:** SHIELD (auditoria + rate limiting) + Líder de produto (regras) + Compliance/LGPD + Comandante (aprovação final).
>
> **Quem sella:** SHIELD + Comandante.
>
> **Quando NÃO aplicar:** projetos genuinamente sem PII/multi-usuário (ver protocolo `fase-consciencia.md`).
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6.
> **Protocolo formal:** `.delta-11/protocolos/fase-consciencia.md`.
> **Skills globais (integrar, NÃO duplicar):** `~/.claude/skills/supabase-rls/`, `~/.claude/skills/owasp-top10/`.

---

## Cabeçalho do artefato (preencher uma vez)

```markdown
# Entregável {{NUMERO}} de 5 — {{NOME_ENTREGAVEL}} (Dia 6 / Fase 4.5)

- **Projeto:** {{NOME_PROJETO}}
- **Data:** {{AAAA-MM-DD}}
- **Autor:** {{NOME_AUTOR}} (SHIELD / Líder de produto / Compliance)
- **Status:** proposta | aceita | substituída
- **Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6
- **Cross-reference Skill Global:** {{LINK_SKILL_GLOBAL_RELEVANTE}}

## Descrição

O QUE é este entregável. Por que o sistema precisa dele. NÃO como ele será implementado.

Máximo 200 palavras. Foco no problema resolvido, não na solução técnica.

## Escolha

A tecnologia / padrão / formato escolhido. Em uma frase.

Exemplos:
- "PostgreSQL triggers + tabela audit_log append-only" (auditoria)
- "Upstash Ratelimit com sliding window" (rate limiting)
- "Máquina de estados em src/lib/fluxos-aprovacao/" (aprovação)
- "Banner opt-in com persistência em cookie + DB" (LGPD)

## Justificativa

Por que ESSA escolha e não outras. Compare com 1-2 alternativas e por que foram descartadas.

Máximo 150 palavras.

## Link

URL da documentação oficial ou ADR relacionado.

## Cross-references (skills globais e patterns)

Quais skills globais e patterns de `conhecimento/design-patterns-praticos.md` este entregável consulta:

- Skill: {{link}} — use a navegação por sintoma
- Pattern: {{nome pattern}} — referência em `.delta-11/conhecimento/design-patterns-praticos.md`

## Teste de Aceitação

Como provar que o entregável está funcionando:

1. [Ação concreta que o tester faz]
2. [Resultado esperado — código de status, log, métrica, etc.]
3. [Como verificar nos logs/dashboard/arquivo]

Exemplos:
- "Fazer login 6 vezes em 1 minuto → a partir do 6º recebe 429"
- "Inserir registro em tabela X → conferir que audit_log tem linha nova"
- "Pedir export de dados via /api/me/export → recebe JSON com PII em 1h"

## Implementação (referência — não preencher nesta fase)

- Arquivo(s) de código: `{{CAMINHO_ARQUIVOS}}`
- Migrations: `{{SQL_PATH}}`
- Variáveis de ambiente: `{{ENV_VARS}}`
- Documentação adicional: `{{LINK_DOCS}}`

---
*Preenchido em {{DATA_PREENCHIMENTO}} | Selado: [ ] SHIELD | [ ] Comandante*
```

---

## Como preencher os 5 entregáveis

Salve cada entregável em arquivo separado:

| # | Entregável | Slug sugerido | Nome do arquivo |
|---|-----------|---------------|------------------|
| 1 | Auditoria imutável de ações | `auditoria-imutavel` | `{{DATA}}-consciencia-01-auditoria-imutavel.md` |
| 2 | Rate limiting por endpoint crítico | `rate-limiting` | `{{DATA}}-consciencia-02-rate-limiting.md` |
| 3 | Motor de regras de negócio central | `motor-regras` | `{{DATA}}-consciencia-03-motor-regras.md` |
| 4 | Sistema LGPD/GDPR | `lgpd` | `{{DATA}}-consciencia-04-lgpd.md` |
| 5 | Fluxos de aprovação | `fluxos-aprovacao` | `{{DATA}}-consciencia-05-fluxos-aprovacao.md` |

Substitua `{{DATA}}` por `date +%Y-%m-%d`.

---

## ⚠️ IMPORTANTE — Não avançar para Fase 5 sem preencher

A Fase 5 (Testes de Integração) **não pode começar** antes que os 5 entregáveis estejam preenchidos E selados pelo SHIELD e Comandante. Razão: o Dia 6 da Metodologia é o único declarado **"muito bom"** — não basta funcionar, o sistema precisa funcionar **de forma responsável**. Construir testes de integração com código sem consciência de domínio é validar um sistema irresponsável.

O hook `fase-consciencia-checker.py` (Etapa 6C do v6.0) bloqueia automaticamente tentativas de avançar sem os 5 entregáveis.

---

## Exemplo preenchido (entregável #1)

Para referência:

```markdown
# Entregável 1 de 5 — Auditoria imutável de ações (Dia 6 / Fase 4.5)

- **Projeto:** cofre-de-keys
- **Data:** 2026-08-15
- **Autor:** Rafa Marks (CTO)
- **Status:** aceita
- **Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6
- **Cross-reference Skill Global:** `~/.claude/skills/supabase-rls/` (P6 multi-tenancy)

## Descrição

O cofre-de-keys armazena chaves de API pessoais dos usuários (dados altamente sensíveis). Cada operação em `api_keys` (criar, ler, atualizar, deletar) precisa de trilha de auditoria imutável para:
- Compliance (LGPD Art. 37 — relatório de impacto)
- Resposta a incidentes (saber quais chaves foram acessadas em dado ataque)
- Responsabilização (saber quem fez o quê)

## Escolha

PostgreSQL triggers AFTER INSERT/UPDATE/DELETE escrevendo em tabela `audit_log` (id, tenant_id, actor_id, table_name, op, old_row, new_row, ip, ts). Hash chain opcional para detectar adulteração.

## Justificativa

- Trigger no DB = impossível esquecer de chamar (vs middleware que algum endpoint pode pular)
- Append-only via permission GRANT (sem UPDATE/DELETE na tabela audit_log)
- Hash chain = integridade criptográfica (provável adulteração detecta)

Alternativas descartadas:
- Audit no nível de ORM (Prisma middleware) — fácil esquecer em SQL nativo
- Audit no nível de aplicação (rotas Next.js) — duplica lógica em cada rota

## Link

- [PostgreSQL Triggers](https://www.postgresql.org/docs/current/triggers.html)
- `~/.claude/skills/supabase-rls/` (P6 multi-tenancy)

## Cross-references (skills globais e patterns)

- Skill: `~/.claude/skills/supabase-rls/` — pattern P6 para audit_log RLS
- Pattern: Chain of Responsibility (middleware layers)

## Teste de Aceitação

1. Inserir registro em `api_keys` via SQL direto
2. Conferir que `audit_log` ganhou uma linha com `op = INSERT`
3. Tentar `UPDATE audit_log SET ...` → falha por permissão
4. Tentar `DELETE FROM audit_log` → falha por permissão

## Implementação (referência — não preencher nesta fase)

- Migrations: `supabase/migrations/2026-08-15-audit-log.sql`
- Triggers: `supabase/migrations/2026-08-15-audit-triggers.sql`
- Variáveis: nenhuma
- Documentação: `src/lib/auditoria/README.md`
```

---

## Relação com as Skills Globais

**NÃO duplique conteúdo de skills aqui.** Em vez disso:

- **Para Entregável 1 (Auditoria)**: consulte `~/.claude/skills/supabase-rls/references/04-multi-tenancy-detalhado.md` para RLS em audit_log e `03-padroes-avancados.md` (P6).
- **Para Entregável 2 (Rate Limiting)**: consulte `~/.claude/skills/owasp-top10/references/02-padroes-corretos.md` (A04) e `04-anti-patterns.md`.
- **Para Entregáveis 3, 4, 5**: as skills globais não cobrem diretamente. Use a base de conhecimento interna `.delta-11/conhecimento/design-patterns-praticos.md` (State Machine para Entregável 5).

---

**Versão do template:** v6.0.0 (2026-07-12)
**Local canônico:** `.delta-11/templates/fase-consciencia-template.md`
**Proveniência:** criado na Etapa 6B do plano Nível 3 Profundo (auditoria 2026-07-10)