# OWASP Top 10 — Referência Curta para Code Review

> **Esta é a base CURTA.** A versão COMPLETA (16 fontes, 53 claims, 51 armadilhas catalogadas, 36 princípios, 32 heurísticas, 47 testes) vive em `~/.claude/skills/owasp-top10/` (skill global instalada em v5.4 Estágio 5.1).
>
> **Quando consultar esta base vs a skill:**
> - Esta base: code review rápido de uma PR; checklist pré-deploy; lembrar uma categoria OWASP específica
> - Skill (`~/.claude/skills/owasp-top10/`): dúvida sobre qual categoria investigar dado um sintoma; auditoria completa; implementação de padrão; incident response; CVEs específicos
>
> **CROSS-REFERENCE com outras skills:**
> - **RLS, BYPASSRLS, search_path hijack, service_role:** use `~/.claude/skills/supabase-rls/` (A01 + A02)
> - **Auditoria do D-11:** use `ferramentas-do-projeto.md` + `validar-deploy.py`
> - **Pentest externo / compliance:** contrate auditoria humana; skill é defesa em profundidade, não substitui profissional

## 1. As 10 categorias OWASP (regra de bolso)

| # | Categoria | O que protege | Vetor principal | Onde cai em Next.js+Supabase |
|---|---|---|---|---|
| **A01** | Broken Access Control | Quem pode fazer o quê | IDOR, RLS bypass, privilege escalation | Middleware + RLS + Server Action validation |
| **A02** | Cryptographic Failures | Dados em trânsito/repouso | HTTP, hash fraco, secret leak | next.config.js + env vars + bcrypt |
| **A03** | Injection | Input do user → código | SQLi, XSS, command injection | Query param + Zod + escape JSX |
| **A04** | Insecure Design | Decisões arquiteturais | Sem rate limit, sem threat model | Middleware + threat model STRIDE |
| **A05** | Security Misconfiguration | Defaults | Headers ausentes, CORS `*`, debug em prod | next.config.js + Supabase Storage |
| **A06** | Vulnerable Components | Dependências | npm audit, supply chain | `npm audit` em CI + lockfile |
| **A07** | Auth Failures | Quem é o user | Credential stuffing, session fixation | Supabase Auth + cookies httpOnly |
| **A08** | Data Integrity | Pipeline CI/CD | Auto-update sem signature, deserialization | Vercel build hooks + PR review |
| **A09** | Logging Failures | Detecção | Sem alertas, PII em logs | Postgres trigger + structured logs |
| **A10** | SSRF | Fetch server-side | Image proxy, OAuth callback, webhooks | Server Actions image + Edge Functions |

## 2. Os 8 mandamentos de segurança (não viole nenhum)

1. **HTTPS obrigatório + HSTS.** NUNCA HTTP em prod. HSTS max-age >= 1 ano.
2. **Secrets em env vars.** `NEXT_PUBLIC_*` = bundle JS = público. NUNCA ponha service_role lá.
3. **JWT secret ≥ 64 chars random.** Rotacione a cada 6-12 meses.
4. **Bcrypt/argon2 para senha.** MD5/SHA1 = inseguro. Supabase Auth já faz isso.
5. **Parametrize queries.** `concat()` + user input = SQLi. Use Supabase client.
6. **Validate no servidor.** Client pode ser bypassado. Zod em todo Server Action.
7. **RLS em toda tabela user-facing.** Tabela sem RLS = leitura pública.
8. **Audit log captura quem/o quê/quando.** Sem log = incidente detectado tarde demais.

## 3. Os 5 CVEs que você PRECISA conhecer (ecossistema Next.js+Supabase)

| CVE | Sev | O que | Fix |
|---|---|---|---|
| **CVE-2024-34351** | HIGH (7.5) | SSRF via Server Actions image optimization | Next.js ≥ 14.1.1; nunca passar URL user para Image |
| **CVE-2025-29927** | CRITICAL (9.1) | Middleware bypass via `x-middleware-subrequest` | Next.js ≥ 14.2.25/15.2.3; nunca confiar SÓ em middleware |
| **CVE-2022-24834** (event-stream) | CRITICAL | Dep npm com código malicioso | `npm audit` em CI; lockfile obrigatório |
| **CVE-2023-XXXXX** (Supabase Auth) | HIGH | Token não expira em algumas rotas | Rotação JWT secret + revisão de policies |
| **MS-2021-XXXX** (log4j) | CRITICAL | RCE via log injection (exemplo A06) | Não usar Java (irrelevante p/ Next.js) |

## 4. Anti-tabela: 12 coisas que você NÃO faz

| # | ❌ Não faça | Por que |
|---|---|---|
| 1 | `service_role` no client (NEXT_PUBLIC_*) | Bypassa RLS; atacante apaga tudo |
| 2 | `using (true)` em policy de dados privados | Vaza TODOS os dados |
| 3 | `NEXT_PUBLIC_*` com secret | Vai pro bundle JS |
| 4 | HTTP em produção | Credenciais em claro |
| 5 | MD5/SHA1 para senha | Quebrado em segundos |
| 6 | `concat()` + user input em SQL | SQL injection |
| 7 | Middleware como única defesa | CVE-2025-29927 bypass |
| 8 | `debug = true` em prod | Stack trace exposto |
| 9 | `Access-Control-Allow-Origin: *` com credentials | CSRF via cross-origin |
| 10 | Sem rate limit em login | Credential stuffing |
| 11 | Logs com PII (email, token, password) | LGPD/GDPR violation |
| 12 | `npm install` sem lockfile | Deps fantasma em prod (supply chain) |

## 5. Quando aprofundar na skill completa

| Situação | Vá para |
|---|---|
| Dúvida "qual categoria investigar dado sintoma X" | skill SKILL.md (navegação por sintoma) |
| Implementar corretamente uma categoria | skill `references/02-padroes-corretos.md` (PAT-001 a PAT-025) |
| Como cada categoria se manifesta em Next.js+Supabase | skill `references/03-stack-specific.md` |
| Ver 44 anti-padrões com CVEs antes de aprovar PR | skill `references/04-anti-patterns.md` |
| Configurar security headers, CORS, cookies | skill `references/05-configs-seguras.md` |
| Audit log no Postgres + alerting | skill `references/06-monitoring-audit.md` |
| Incident response (detectar → conter → remediar) | skill `references/07-incident-response.md` |
| 47 testes executáveis (curl/SQL/DevTools/npm) | skill `references/09-testes-executaveis.md` |
| 32 heurísticas de code review, deploy, IR | skill `references/10-heuristicas-bolso.md` |
| Onboarding do time / entender "por que" | skill `references/08-mental-model.md` |

## 6. Quem audita segurança no projeto

| Quem | Quando |
|---|---|
| **SHIELD** | Code review de toda PR com mudança de auth, RLS, route, env var |
| **ENGINE** | Implementa Server Actions e Route Handlers com validação dupla |
| **VAULT** | Cria tabelas com RLS habilitada desde o dia 1 |
| **FRONT** | Configura `next.config.js` com security headers |
| **CRONOS** | Despacha migration de schema RLS ANTES de ENGINE (dependência) |
| **Comandante** | Roda `audit-security.sh` antes de cada deploy em staging |

---

**Proveniência:** Esta base é a versão resumida (gate) da skill completa `~/.claude/skills/owasp-top10/` construída via Skill Forge v3 (Deep Path, Estágio 5.1 do plano de execução v5.4). A skill é o lugar de verdade; esta base existe para o time ter o essencial de OWASP em 5 minutos de leitura.