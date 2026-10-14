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
| Ferramentas e contas do projeto (o que está instalado, onde, quanto custa) | (registro do projeto) | `.delta-11/memoria/ferramentas-do-projeto.md` |
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
- SKILL.md — navegação por sintoma
- 01-fundamentos-de-rls.md — 4 roles, USING vs WITH CHECK, auth.uid vs auth.jwt
- 02-padroes-basicos.md — P1-P5 com SQL copy-pastable
- 03-padroes-avancados.md — P6 multi-tenancy + P7 Custom Hook
- 04-multi-tenancy-detalhado.md — 3 estratégias comparadas
- 05-casos-especiais.md — Storage, Realtime, Edge Functions, RPC, migrations
- 06-auditoria-e-performance.md — EXPLAIN, índices, wrap
- 07-troubleshooting.md — debugging avançado
- 08-mental-model-e-principios.md — 4 analogias, 14 princípios
- 09-validation-tests-completos.md — 32 testes SQL/psql
- 10-heuristicas-de-bolso.md — 26 regras de bolso

**Base curta D-11 (oficial do VAULT):** `.delta-11/conhecimento/supabase-rls-patterns.md`

---

## 2. `owasp-top10` (Estágio 5)

**Quando ativar:**
- Code review focado em segurança
- Sintoma: IDOR, XSS, SQLi, headers ausentes, SSRF
- CVE específico (CVE-2024-34351, CVE-2025-29927, etc)
- Auditoria pré-deploy (47 testes)
- Incident response (4 fases + contenção específica para 9 categorias)

**Categorias OWASP (10/10 cobertas):**
- A01 Broken Access Control · A02 Cryptographic Failures · A03 Injection
- A04 Insecure Design · A05 Security Misconfiguration · A06 Vulnerable Components
- A07 Auth Failures · A08 Data Integrity · A09 Logging · A10 SSRF

**Arquivos principais:**
- SKILL.md — navegação por sintoma + 5 CVEs principais
- 01-fundamentos-owasp.md — A01-A10 com taxonomia
- 02-padroes-corretos.md — 25 PATs
- 03-stack-specific.md — mapa componente → categoria
- 04-anti-patterns.md — 44 ANTIs com CVEs
- 05-configs-seguras.md — 5 configs canônicas
- 06-monitoring-audit.md — 3 camadas de detecção
- 07-incident-response.md — 4 fases (detectar, conter, remediar, post-mortem) + contenção para 9 categorias
- 08-mental-model.md — 5 analogias
- 09-testes-executaveis.md — 47 testes
- 10-heuristicas-bolso.md — 32 regras

**Bases D-11:** `.delta-11/conhecimento/owasp-top10-resumo.md` (OFICIAL do SHIELD) + `.delta-11/conhecimento/owasp-top10-overview.md` (apêndice curto desta skill)

---

## 3. `react-next` (Estágio 6)

**Quando ativar:**
- Criar/revisar/debugar componente React, Server Component, Client Component
- Sintoma: hydration mismatch, infinite loop, useEffect deps, memory leak
- Server Action (form, mutations, revalidation, race condition)
- Performance (bundle, memo, virtualization)
- Testing (Vitest, RTL, Playwright, MSW)

**Arquivos principais:**
- SKILL.md — navegação por sintoma (12 entradas) + 8 mandamentos
- 01-fundamentos-react-next.md — Server vs Client, hooks React 19, RSC
- 02-debugging-preventivo.md — 10 perguntas antes de commitar
- 03-patterns-corretos.md — 22 PATs
- 04-anti-patterns.md — 32 ANTIs
- 05-server-actions.md — forms, mutations, revalidate, race
- 06-performance.md — streaming, Suspense, memo, bundle
- 07-testing.md — Vitest, RTL, MSW, Playwright
- 08-debugging-reativo.md — 5 árvores: hydration/infinite loop/memory/race/RSC
- 09-stack-specific.md — App Router, PPR, Image, Link
- 10-heuristicas-bolso.md — 31 regras

**Base curta D-11:** `.delta-11/conhecimento/react-next-overview.md` (apêndice consultado por FRONT, PIXEL e FORM, além das bases oficiais deles)

---

## 4. As bases OFICIAIS de cada agente (v6.3)

Cada agente tem UMA base oficial — a que está no `perfis/[AGENTE].json`. Nenhuma delas é "legado": todas estão
em uso. Os apêndices curtos das skills (overview) complementam, não substituem.

| Base | Dono (oficial) | Cobre |
|---|---|---|
| `arquitetura-software-patterns.md` | ATLAS | Descoberta, arquitetura por complexidade, formato de contrato, tabelas base, nomenclatura, checklist da Fase 2 |
| `coordenacao-projeto-patterns.md` | CRONOS | Caminho crítico, dependências, sinais de bloqueio, playbooks, replanejamento |
| `react-component-patterns.md` | FRONT | Server/Client Components, estado, layouts, loading/error, composição |
| `tailwind-animation-patterns.md` | PIXEL | Responsivo, transições, animações, skeleton, modo escuro |
| `react-form-patterns.md` | FORM | React Hook Form + Zod, acessibilidade de campo, multi-etapas, upload, erros |
| `backend-integracao-patterns.md` | BACK | Integrações server-side (Stripe, webhooks, e-mail), cache, paginação, N+1 |
| `nextjs-api-patterns.md` | ENGINE | Route Handlers, `@supabase/ssr` + `getUser()`, Zod, formato único de erro, fetch com tempo-limite |
| `supabase-rls-patterns.md` | VAULT | RLS: mandamentos, papéis, P1–P7, antipadrões, G-001 |
| `owasp-top10-resumo.md` | SHIELD | OWASP A01–A10 detectar/corrigir, checklists, protocolo de auditoria |
| `debugging-preventivo-patterns.md` | SCOUT | Diagnóstico de bugs de aplicações Next.js + Supabase: método de 5 passos, armadilhas, scan pré-deploy |
| `design-patterns-praticos.md` | BACK e FRONT leem inteira; os demais consultam | Padrões de projeto já usados no sistema e quando NÃO usar |
| `metodologia-genesis-camadas.md` | todos (referência) | Os 7 Dias, contraposições, critérios de selo |

**Apêndices curtos das skills globais:** `owasp-top10-overview.md`, `react-next-overview.md`.

**Onde cada lição repetida vive (uma só fonte):**
- Tempos-limite, novas tentativas e circuit breaker → `protocolos/regras-codigo.md` (tabela única, D19)
- Formato de erro de API → `nextjs-api-patterns.md` seção "Formato único de erro" (D13)
- N+1 → `backend-integracao-patterns.md`
- Inicialização sob demanda do Stripe (`getStripe`) → `backend-integracao-patterns.md`
- G-001 (RLS que devolve lista vazia sem erro) → `supabase-rls-patterns.md`

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

**Versão da base:** v6.3 (2026-10-14) — nomes reais dos arquivos das skills, sem contagens de linha (envelhecem), bases oficiais declaradas. Antes: v5.4 (2026-07-10)
**Manutenção:** atualize quando uma skill nova for adicionada.
**Proveniência:** criada no Estágio 7 (consolidação final) do plano de execução v5.4.