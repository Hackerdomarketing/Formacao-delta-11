# Skills Globais v5.4 — Índice de Referência

> **Esta é a base CURTA que funciona como ÍNDICE CENTRAL das 3 skills globais instaladas em v5.4.** Se você não sabe qual skill consultar, comece aqui.
>
> **Cross-references com outras skills:**
> - As 3 skills globais vivem em `~/.claude/skills/` (auto-descobertas)
> - Cada skill tem sua própria base curta no D-11 (gate para a versão completa)
> - Use a navegação por sintoma dentro de cada skill (não leia linear)

## TL;DR — Quando usar qual skill

| Sintoma / Necessidade | Skill | Vá para |
|---|---|---|
| "User A vê dados de user B" / RLS bypass / IDOR | `supabase-rls` | `~/.claude/skills/supabase-rls/` |
| "Secret vazou" / "CVE-2024-34351" / "MFA bypass" | `owasp-top10` | `~/.claude/skills/owasp-top10/` |
| "Tela branca em prod" / "useState não atualiza" / "Server Action sem revalidate" | `react-next` | `~/.claude/skills/react-next/` |
| Auditoria do sistema D-11 (workflows, memoria) | Esta base | `.delta-11/ferramentas-do-projeto.md` |
| Performance de query (EXPLAIN, índice) | `supabase-rls/06-auditoria-e-performance.md` | (mesma skill RLS, 6º ref) |
| Setup de novo projeto Next.js | Doc oficial Next.js | https://nextjs.org/docs (não é skill) |

## 1. `supabase-rls` (Estágio 4)

**Quando ativar:**
- Criar/revisar/auditar/debugar/migrar RLS policies
- Sintoma de "RLS silenciosa" (query retorna vazio sem erro)
- Vazamento entre users / IDOR
- Multi-tenancy (3 estratégias: schema-per-tenant, row-per-tenant, claim-per-tenant)
- Custom Access Token Hook (P7) para claims custom

**Arquivos principais:**
- SKILL.md (172 linhas) — navegação por sintoma
- 01-fundamentos-de-rls.md (626) — 4 roles, USING vs WITH CHECK, auth.uid vs auth.jwt
- 02-padroes-basicos.md (1012) — P1-P5 com SQL copy-pastable
- 03-padroes-avancados.md (714) — P6 multi-tenancy + P7 Custom Hook
- 04-multi-tenancy-detalhado.md (349) — 3 estratégias comparadas
- 05-casos-especiais.md (749) — Storage, Realtime, Edge Functions, RPC, migrations
- 06-auditoria-e-performance.md (505) — EXPLAIN, índices, wrap
- 07-troubleshooting.md (513) — debugging avançado
- 08-mental-model-e-principios.md (288) — 4 analogias, 14 princípios
- 09-validation-tests-completos.md (615) — 32 testes SQL/psql
- 10-heuristicas-bolso.md (247) — 26 regras de bolso

**Base curta D-11:** `.delta-11/conhecimento/supabase-rls-patterns.md` (149 linhas)

---

## 2. `owasp-top10` (Estágio 5)

**Quando ativar:**
- Code review focado em segurança
- Sintoma: IDOR, XSS, SQLi, headers ausentes, SSRF
- CVE específico (CVE-2024-34351, CVE-2025-29927, etc)
- Auditoria pré-deploy (47 testes)
- Incident response (10 runbooks por categoria)

**Categorias OWASP (10/10 cobertas):**
- A01 Broken Access Control · A02 Cryptographic Failures · A03 Injection
- A04 Insecure Design · A05 Security Misconfiguration · A06 Vulnerable Components
- A07 Auth Failures · A08 Data Integrity · A09 Logging · A10 SSRF

**Arquivos principais:**
- SKILL.md (192 linhas) — navegação por sintoma + 5 CVEs principais
- 01-fundamentos-owasp.md (1713) — A01-A10 com taxonomia
- 02-padroes-corretos.md (1049) — 25 PATs
- 03-stack-specific.md (410) — mapa componente → categoria
- 04-anti-patterns.md (1162) — 44 ANTIs com CVEs
- 05-configs-seguras.md (518) — 5 configs canônicas
- 06-monitoring-audit.md (391) — 3 camadas de detecção
- 07-incident-response.md (449) — 10 runbooks
- 08-mental-model-e-principios.md (258) — 5 analogias
- 09-testes-executaveis.md (755) — 47 testes
- 10-heuristicas-bolso.md (256) — 32 regras

**Base curta D-11:** `.delta-11/conhecimento/owasp-top10-overview.md` (118 linhas)

---

## 3. `react-next` (Estágio 6)

**Quando ativar:**
- Criar/revisar/debugar componente React, Server Component, Client Component
- Sintoma: hydration mismatch, infinite loop, useEffect deps, memory leak
- Server Action (form, mutations, revalidation, race condition)
- Performance (bundle, memo, virtualization)
- Testing (Vitest, RTL, Playwright, MSW)

**Arquivos principais:**
- SKILL.md (167 linhas) — navegação por sintoma (12 entradas) + 8 mandamentos
- 01-fundamentos-react-next.md (767) — Server vs Client, hooks React 19, RSC
- 02-debugging-preventivo.md (343) — 10 perguntas antes de commitar
- 03-patterns-corretos.md (566) — 22 PATs
- 04-anti-patterns.md (731) — 32 ANTIs
- 05-server-actions.md (536) — forms, mutations, revalidate, race
- 06-performance.md (498) — streaming, Suspense, memo, bundle
- 07-testing.md (424) — Vitest, RTL, MSW, Playwright
- 08-debugging-reativo.md (648) — 5 árvores: hydration/infinite loop/memory/race/RSC
- 09-stack-specific.md (361) — App Router, PPR, Image, Link
- 10-heuristicas-bolso.md (239) — 31 regras

**Base curta D-11:** `.delta-11/conhecimento/react-next-overview.md` (102 linhas)

---

## 4. Outras bases D-11 (não são skills globais)

| Base | Cobre | Quando usar |
|---|---|---|
| `.delta-11/conhecimento/design-patterns-praticos.md` | 10 padrões GoF (Observer, Factory, etc) | Dúvida sobre design pattern clássico |
| `.delta-11/conhecimento/nextjs-api-patterns.md` | API routes, middleware, Route Handlers | Server Actions não cobrem |
| `.delta-11/conhecimento/react-form-patterns.md` | Forms em React (legado) | Para forms em React puro (não Next.js 15 App Router) |
| `.delta-11/conhecimento/react-component-patterns.md` | Componentes React (legado) | Server Components cobrem melhor |
| `.delta-11/conhecimento/backend-integracao-patterns.md` | Stripe, webhooks, OAuth | Integrações server-side |
| `.delta-11/conhecimento/tailwind-animation-patterns.md` | CSS, animação, design system | Estilização |
| `.delta-11/conhecimento/arquitetura-software-patterns.md` | Clean Architecture, Hexagonal | Decisões de arquitetura |
| `.delta-11/conhecimento/coordenacao-projeto-patterns.md` | D-11 workflow, agentes | Workflow do sistema D-11 |
| `.delta-11/conhecimento/debugging-preventivo-patterns.md` | D-11 debug flow | Debugging do D-11 em si |
| `.delta-11/conhecimento/owasp-top10-resumo.md` | Versão resumida de OWASP (legacy) | Use a versão global (mais completa) |

---

## 5. Quando NÃO usar nenhuma skill (use doc oficial)

| Caso | Vá para |
|---|---|
| Setup inicial de projeto Next.js do zero | https://nextjs.org/docs (oficial) |
| Criar conta Supabase / configurar RLS no Dashboard | https://supabase.com/docs |
| Compliance (LGPD, GDPR, HIPAA) | Contratar DPO + auditoria humana |
| Pentest externo | Empresa especializada |
| UI/UX design | Figma / designer |

---

## 6. Próximos passos (backlog pós-v5.4)

- **Refinar skills com evals** (Skill Forge v3 Fase 5) — rodar `forge_eval.py` para cada skill com `evals.json` correspondente
- **Skill de debugging cross-stack** — combinar RLS + OWASP + React para diagnosticar bugs que cruzam camadas
- **Skill de design system** — unificar Tailwind + componentes + acessibilidade
- **Skill de deploy Vercel** — Edge Functions, env vars, ISR, rollback

---

**Versão da base:** v5.4 (2026-07-10)
**Manutenção:** atualize quando uma skill nova for adicionada.
**Proveniência:** criada no Estágio 7 (consolidação final) do plano de execução v5.4.