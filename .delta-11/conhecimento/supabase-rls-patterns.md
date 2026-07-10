# Supabase RLS — Referência Curta para VAULT

> **Esta é a base CURTA.** A versão COMPLETA (24k+ linhas, 32 armadilhas catalogadas, 14 princípios operacionais, 5 padrões canônicos com SQL copy-pastable) vive em `~/.claude/skills/supabase-rls/` (skill global instalada em v5.4 Estágio 4.1).
>
> **Quando consultar esta base vs a skill:**
> - Esta base: criação rápida de policy que segue padrão conhecido; review rápido sem precisar mergulhar
> - Skill (`~/.claude/skills/supabase-rls/`): dúvida sobre qual padrão usar; armadilha nova não documentada; auditoria completa pré-deploy; troubleshooting de bug; migração de RLS em produção
>
> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Tabelas e colunas em inglês · 1 assunto por migration · comentários SQL em português.

---

## 1. Os 5 mandamentos (não viole nenhum)

1. **RLS desligada por default.** `ALTER TABLE x ENABLE ROW LEVEL SECURITY` é obrigatório, sempre. Esquecer = vazamento público.
2. **Service role bypassa tudo.** `SUPABASE_SERVICE_ROLE_KEY` é chave de produção. Nunca no client-side.
3. **Wrap funções em `(select fn())`.** `auth.uid()` sem wrap = 1M execuções em 1M rows = 178s. Com wrap = 10ms (1000x).
4. **USING filtra linhas existentes. WITH CHECK valida linhas novas.** Em UPDATE, as duas coexistem. UPDATE sem WITH CHECK = user transfere ownership.
5. **STABLE + SECURITY DEFINER não substitui o wrap.** O wrap é o que ativa initPlan no planner.

Para os 14 princípios completos (incluindo P5 search_path, P6 user_metadata vs app_metadata, P7 USING+WITH CHECK em UPDATE), veja `references/02-operational-principles.md` na skill.

---

## 2. As 4 roles do Supabase

| Role | Quem é | Bypassa RLS? |
|---|---|---|
| `anon` | Visitante sem JWT | Não |
| `authenticated` | Logado (Supabase Auth com JWT válido) | Não |
| `service_role` | Backend confiável (Server Component, Edge Function, cron) | **Sim** |
| `postgres` | DBA / migrations | Sim |

`anon` ≠ "anonymous user do Supabase Auth" (que usa `authenticated` com claim `is_anonymous: true`).

---

## 3. Os 7 padrões canônicos (regra de bolso)

| Padrão | Quando usar | SQL canônico |
|---|---|---|
| **P1 User-Owns-Row** | Tabela com `user_id`, sem compartilhamento | `using ((select auth.uid()) = user_id)` |
| **P2 Public-Read** | Conteúdo público com rascunho privado | `using (published = true or (select auth.uid()) = author_id)` para authenticated; `using (published = true)` para anon |
| **P3 Admin-Override** | Admin vê tudo, user vê seus | função `is_admin()` lê `app_metadata->>'is_admin'` (NUNCA user_metadata) |
| **P4 RBAC** | Permissões granulares por documento | tabela de permissões + função `doc_role(doc_id, user_id)` |
| **P5 Team** | Workspace/equipe compartilhada | tabela `team_members` + função `is_team_member(team_id, user_id)` |
| **P6 Multi-Tenant** | SaaS B2B com isolamento por tenant | `tenant_id` no JWT (via P7) + policy `using (tenant_id = (select auth.jwt()->>'tenant_id')::uuid)` |
| **P7 Custom Hook** | Setup auxiliar: injeta claims no JWT no signin | `create function custom_access_token_hook(event jsonb) returns jsonb ...` |

P1-P5 cobrem ~80% dos casos. P6 é obrigatório em SaaS B2B. P7 é infraestrutura do P6.

**Árvore de decisão:**
```
Tabela tem dados por user com user_id?
├── Sim, sem compartilhamento                  → P1
├── Sim, com publicado/rascunho                → P2
├── Sim, com admin que vê tudo                 → P3
├── Não, permissões por documento              → P4
├── Não, é por time/equipe                     → P5
├── Não, é multi-tenant (SaaS B2B)             → P6 (requer P7)
└── Misturei                                    → decomponha
```
Tabela tem dados por user com user_id?
├── Sim, sem compartilhamento                  → P1
├── Sim, com publicado/rascunho                → P2
├── Sim, com admin que vê tudo                 → P3
├── Não, permissões por documento              → P4
├── Não, é por time/equipe                     → P5
├── Não, é multi-tenant                        → P6 (ver skill)
└── Misturei                                    → decomponha
```

---

## 4. Template de policy padrão (P1, o mais comum)

```sql
-- 1. Setup
create table public.notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  body text not null default '',
  created_at timestamptz not null default now()
);

alter table public.notes enable row level security;
grant select, insert, update, delete on public.notes to authenticated;

-- 2. 4 policies, uma por operação
create policy policy_select_own_notes on public.notes
  for select to authenticated
  using ((select auth.uid()) = user_id);

create policy policy_insert_own_notes on public.notes
  for insert to authenticated
  with check ((select auth.uid()) = user_id);

create policy policy_update_own_notes on public.notes
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);  -- bloqueia transferência de ownership

create policy policy_delete_own_notes on public.notes
  for delete to authenticated
  using ((select auth.uid()) = user_id);

-- 3. Índice em user_id (CRÍTICO)
create index notes_user_id_idx on public.notes (user_id);
```

---

## 5. Os 5 antipadrões mais comuns

1. **Esquecer `enable row level security`** — tabela pública
2. **`for all` em vez de policies separadas** — confunde USING (SELECT) com WITH CHECK (INSERT)
3. **UPDATE sem `with check`** — user transfere ownership
4. **`auth.uid()` sem wrap** — 1000x slowdown
5. **`is_admin()` lendo `user_metadata`** — user se auto-promove

---

## 6. Gotcha G-001 (canônico)

> **Supabase retorna lista vazia sem erro quando RLS bloqueia.**
> - **EVITE:** tratar `data: []` como "não existem registros" sem verificar política RLS
> - **PORQUE:** query com RLS ativo e política ausente retorna vazio SILENCIOSAMENTE — parece bug de dados, é permissão
> - **FAÇA:** ao receber vazio inesperado, rodar a mesma query com service_role em ambiente dev; se retornar dados, o problema é política RLS

---

## 7. Quando aprofundar na skill completa

| Situação | Vá para |
|---|---|
| Dúvida "qual padrão usar pra X?" | skill `references/02-padroes-basicos.md` |
| Query retorna vazio sem erro | skill `references/07-troubleshooting.md` (sessão 4.4) |
| Auditoria pré-deploy (32 testes) | skill `references/09-validation-tests-completos.md` (sessão 4.4) |
| Multi-tenancy (P6, P7) | skill `references/03-padroes-avancados.md` (sessão 4.2) |
| Storage / Realtime / RPC com RLS | skill `references/05-casos-especiais.md` (sessão 4.3) |
| Performance de policy (EXPLAIN) | skill `references/06-auditoria-e-performance.md` (sessão 4.4) |
| Migrar RLS em produção | skill `references/09-migration-strategies.md` (sessão 4.4) |

---

## 8. Quem escreve RLS no projeto

| Quem | Quando |
|---|---|
| **VAULT** | Cria schema, RLS, migrations. **TODA tabela nova passa por VAULT antes de qualquer agente tocar.** |
| **ENGINE** | Cria Server Actions / Edge Functions que usam `service_role` para tarefas admin. Valida que o fluxo bypassa explicitamente (não implícito). |
| **SHIELD** | Revisa toda policy nova; roda auditoria automatizada antes do deploy. |
| **CRONOS** | Despacha a migration de RLS em fase separada, ANTES do ENGINE (dependência: VAULT → ENGINE). |

---

**Proveniência:** Esta base é a versão resumida (gate) da skill completa `~/.claude/skills/supabase-rls/` construída via Skill Forge v3 (Deep Path, Estágio 4.1 do plano de execução v5.4). A skill é o lugar de verdade; esta base existe para evitar que o VAULT tenha que abrir a skill inteira para fazer 80% das policies triviais (P1).