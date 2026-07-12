# Protocolo da Fase 4.5 — Consciência Dominante (Dia 6 da Metodologia Gênesis)

> **Protocolo formal da Fase 4.5 que existe no fluxo entre a Fase 4 (Desenvolvimento) e a Fase 5 (Testes de Integração).**
> **Esta fase foi adicionada no v6.0.0 para corrigir o achado #6 da auditoria (parcial — consciência de domínio fraca).**
>
> **Cross-references:**
> - Fluxo principal: `.delta-11/protocolos/fluxo-zero-ao-lancamento.md` → seção "FASE 4.5 — CONSCIÊNCIA DOMINANTE"
> - Base conceitual: `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6
> - Template dos 5 entregáveis: `.delta-11/templates/fase-consciencia-template.md`
> - Hook bloqueante: `.delta-11/hooks/fase-consciencia-checker.py`
> - Skills globais v5.4 que cobrem parte do conteúdo: `~/.claude/skills/supabase-rls/` (Dia 6 — multi-tenancy) e `~/.claude/skills/owasp-top10/` (Dia 6 — segurança, CVEs)

## O que é o Dia 6 — em linguagem da Metodologia Gênesis

Texto hebraico chave (Gênesis 1:24-31):

> *naaseh adam be-tzalmenu ki-dmutenu* — "façamos o homem em nossa imagem, conforme nossa semelhança"
> *zachar u-nekevá bara otam* — "masculino e feminino criou-os"
> *tov meod* — "muito bom" (a única vez no relato da Criação em que Deus avalia a obra como mais que "boa" — é "muito boa")

Significado: depois dos habitantes existirem (Dia 5), Deus cria a **consciência dominante** sobre eles — uma camada que governa, decide, audita, protege. No software, isso é tudo que fica **acima** do código de funcionalidade: autenticação, autorização, auditoria, regras de negócio conscientes, compliance.

**Por que esta fase é DEPOIS da Fase 4 (não durante):** a consciência governa os habitantes que já existem. Não se pode governar código que ainda não foi escrito. Por isso Dia 6 vem depois do Dia 5 na Metodologia — e a Fase 4.5 do fluxo vem depois da Fase 4.

## Quando NÃO aplicar esta fase

A Fase 4.5 é mais permissiva do que a Fase 3.5 em exceções — porque consciência de domínio é menos crítico para sobrevivência do software do que ritmo temporal. Mas há limites:

1. **Projetos genuinamente single-tenant com zero dado pessoal** — por exemplo, ferramenta interna que roda na rede local sem nenhum dado pessoal identificável, sem integração externa, sem multi-usuário. Nesses casos, a Fase 4.5 pode ser minimal (skipar LGPD e multi-tenancy; manter rate limiting mínimo e regras conscientes básicas).
2. **Provas de conceito de 1 dia** com público zero — mesma lógica. Mas se for pra deploy real, Fase 4.5 é obrigatória.

**Em qualquer caso com:** dados pessoais (PII), multi-usuário, integração externa que processa dados sensíveis, ou exposição à internet **a Fase 4.5 é obrigatória**.

## Os 5 entregáveis do Dia 6 — declaração completa

Cada entregável vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<N>-<slug>.md` (template em `fase-consciencia-template.md`). Cada arquivo tem: descrição, escolha, justificativa, link.

### Entregável 1 — Auditoria imutável de ações

**O que:** sistema que registra *quem fez o quê e quando* em todas as tabelas com dados sensíveis (PII, financeiras, admins, etc.). Logs são append-only (não-editáveis) com hash chain ou similar.

**Diferença crítica do Sentry:** o Sentry registra **erros não intencionais** que acontecem na aplicação. Auditoria registra **ações intencionais** do usuário no banco (CRUD). São ortogonais — ambos precisam existir.

**Implementação comum:** trigger PostgreSQL em cada tabela crítica que escreve em tabela `audit_log` (id, user_id, table_name, operation, old_value, new_value, timestamp, ip). Pode usar `pg_audit` ou implementação manual.

**Para multi-tenant:** adicionar campo `tenant_id` no `audit_log` para isolar por organização.

**Skill global relevante:** `supabase-rls` (especialmente RLS policies para `audit_log`).

### Entregável 2 — Rate limiting por endpoint crítico

**O que:** cada endpoint sensível tem rate limit configurado. Lista canônica:
- `/api/auth/login` — 5 tentativas / 15 min por IP
- `/api/auth/register` — 3 contas / 1 hora por IP
- `/api/auth/reset-password` — 3 requests / 1 hora por email
- Qualquer rota que **consuma crédito** (pagamentos, envio de email, SMS, etc.) — limite por usuário/hora
- Qualquer rota que **execute trabalho pesado** — limite por IP/minuto

**Implementação comum:** Chain of Responsibility após middleware de auth (ver `conhecimento/design-patterns-praticos.md` — Chain of Responsibility). Provedor: Upstash Ratelimit (serverless-friendly), Redis nativo, ou similar.

**Teste de aceitação:** tentar 100 logins em 1 minuto → após 5, retorna 429 Too Many Requests.

**Skill global relevante:** `owasp-top10` (A04 Insecure Design — "sem rate limiting" é item explícito).

### Entregável 3 — Motor de regras de negócio central

**O que:** extrair regras de negócio espalhadas pelo código para um módulo central. Para cada regra:
- Tem teste próprio
- Tem log de quando foi acionada
- Tem métrica de quantas vezes foi acionada
- É declarada de forma legível (não enterrada em if/else)

**Implementação comum:**
- Para regras simples: pasta `src/lib/regras-de-negocio/` com uma função pura por regra
- Para regras complexas: motor tipo `json-rules-engine` ou DSL interna
- Para regras que mudam: admin UI que edita regras em runtime (com auditoria dupla!)

**Justificativa:** sem motor central, regras ficam enterradas em if/else, são impossíveis de auditar, e mudam de forma não-rastreável em cada commit.

**Exceção honesta:** se as regras são TÃO SIMPLES (ex: "se user.role === 'admin', pode ver X") que extraí-las para um módulo seria overhead, é legítimo justificar "regra X é distribuída por design, com teste em Y, log em Z". **Documentar a justificativa** no entregável.

### Entregável 4 — Sistema de consentimento LGPD/GDPR

**O que:** sistema que atende aos direitos do titular previstos em LGPD (Brasil) e GDPR (Europa):
- **Banner de cookies opt-in** (não opt-out, que é ilegal na UE)
- **Registro de consentimento** com timestamp + versão da política
- **Direito de acesso** — usuário pode exportar TODOS seus dados pessoais
- **Direito de correção** — usuário pode corrigir dados pessoais via UI
- **Direito ao esquecimento** — usuário pode pedir exclusão dos dados (com cuidado: existem exceções legais)
- **Portabilidade** — export em formato estruturado (JSON, CSV)
- **DPO (Data Protection Officer) designado** — pelo menos um email de contato

**Mínimo aceitável para um MVP B2C:** banner + registro de consentimento + export de dados + DPO.

**Skill global:** nenhuma cobre isso integralmente. Contratar DPO + auditoria humana para compliance total é a recomendação formal (ver `skills-globais-v5-4.md:127`).

### Entregável 5 — Fluxos de aprovação para operações críticas

**O que:** operações que mudam estado de forma irreversível ou sensível NÃO podem ser executadas direto pelo usuário. Precisam de aprovação explícita.

**Lista canônica:**
- Delete em massa (>10 registros de uma vez)
- Transações financeiras (qualquer movimentação real de dinheiro)
- Mudança de role/permissão de outro usuário
- Alteração de dados de outro usuário
- Desativação/bloqueio de conta de outro usuário
- Operações que dependem de limite de crédito
- Aprovação de pedidos grandes (B2B)

**Modelos de fluxo:**
- **Single-step:** usuário pede → aprovador AprovA ou Rejeita
- **Multi-step:** pedido → aprovador 1 → aprovador 2 → executa
- **Regra-based:** aprovação automática se valor < X, manual se ≥ X

**Implementação comum:** máquina de estados (`conhecimento/design-patterns-praticos.md` — State Machine). Cada estado com: quem pode aprovar, quais transições são válidas, em que momento é executada.

**Auditoria de aprovações:** cada aprovação REJEITA ou ACEITA é registrada no `audit_log` (entregável 1).

**Quem aprova:** idealmente uma pessoa diferente de quem pediu. Separação de funções.

## Endereço canônico dos entregáveis

Cada um dos 5 entregáveis vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<N>-<slug>.md`.

**Exemplo para o projeto hipotético "cofre-de-keys" iniciado em 2026-08-15:**
- `2026-08-15-consciencia-01-auditoria-imutavel.md`
- `2026-08-15-consciencia-02-rate-limiting.md`
- `2026-08-15-consciencia-03-motor-regras.md`
- `2026-08-15-consciencia-04-lgpd.md`
- `2026-08-15-consciencia-05-fluxos-aprovacao.md`

Use o template `.delta-11/templates/fase-consciencia-template.md` para preencher cada um.

## Quem sella

A Fase 4.5 consagra com a presença de:
- **SHIELD** (auditoria + rate limiting)
- **Comandante** (LGPD + aprovações)
- **Líder de produto** (regras de negócio)
- **Compliance / DPO** (se aplicável)

Sem SHIELD + Comandante, a Fase 5 NÃO pode começar. O hook `fase-consciencia-checker.py` bloqueia a transição automaticamente.

## Critério objetivo de selo

Os 5 arquivos `.delta-11/memoria/decisoes/...` existem. SHIELD declara "Fase 4.5 selada" no kanban. Comandante digita `aprovar`.

Cross-test: o `audit_log` realmente captura uma ação simulada (fazer login + 1 update + ver se foi registrado). O rate limiter rejeita a 6ª tentativa de login.

## Relação com o Dia 5 (Habitantes)

A Fase 4.5 **governa o código de funcionalidade** entregue na Fase 4. Cada endpoint que existe na Fase 4 precisa ser classificado:
- É endpoint público (auth, recovery) → recebe rate limiting obrigatório
- É endpoint administrativo → recebe auditoria obrigatória
- É endpoint que muda dados financeiros → recebe fluxo de aprovação
- É endpoint que expõe dados de outros usuários → passa por RLS (já garantido pelo Dia 6) + auditoria de leitura (opcional mas recomendado)

Sem essa cobertura, os habitantes do Dia 5 funcionam **sem dono consciente**. O sistema aparenta funcionar mas é irresponsável.

## Relação com as Skills Globais v5.4

O conteúdo deste protocolo **NÃO duplica** as skills globais. Pelo contrário, o conteúdo das skills é referenciado:

- `~/.claude/skills/supabase-rls/` → cobre RLS, isolamento multi-tenant (parte do Entregável 1, Auditoria). v6.0 **integra** a skill como referência obrigatória do VAULT.
- `~/.claude/skills/owasp-top10/` → cobre segurança, CVEs, incident response (parte do Entregável 2, Rate Limiting). v6.0 **integra** como referência do SHIELD.

Nenhum conteúdo novo de segurança é criado aqui — as skills globais já existem. O que o D-11 garante é que **os agentes consultem** as skills ao executar esta fase.

## Manutenção

Este protocolo evolui conforme o sistema amadurece. Mudanças aqui passam por:
1. Proposta via issue
2. Discussão em equipe
3. Decisão via ADR (especialmente se a LGPD/GDPR mudar)
4. Atualização deste arquivo + template + hook + testes

**Versão do protocolo:** v6.0.0 (2026-07-12)
**Manutenção:** manter sincronizado com `metodologia-genesis-camadas.md` (Dia 6), `fase-consciencia-template.md`, e as skills globais v5.4.

---
*Este documento é IMUTÁVEL após publicação. Correções em ADIÇÕES POSTERIORES no CHANGELOG.*