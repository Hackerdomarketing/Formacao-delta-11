# ESQUEMA DE BANCO — [NOME DO PROJETO]

> **Template v6.3 (2026-10-14) — Fatia de domínio "banco".**
> Salvo em `.delta-11/memoria/project-core/banco.md` (fatia do project-core). Gerado pelo ATLAS na Fase 2.
> Consumido por: VAULT (implementa), BACK/ENGINE (consultam), SHIELD/SCOUT (verificam).
> **Duas verdades (D24):** este documento é a verdade do CONTRATO (o que o banco DEVE ser); as migrations em
> `supabase/migrations/` são a verdade do banco IMPLEMENTADO (o que o banco É). O `schema-validator` compara os
> dois; divergência é bug para o ATLAS decidir (corrigir este documento ou pedir nova migration).
> Somente o ATLAS edita (D7). Nomes de tabela e coluna em inglês, `snake_case`, sem abreviação (D20).

## Visão geral do modelo

[2-4 frases: as entidades principais e como se relacionam, em linguagem leiga.]

## Tabelas

### [nome_da_tabela]

**Propósito:** [1 frase]

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| id | uuid | PK, default gen_random_uuid() | identificador |
| [coluna] | [tipo] | [NOT NULL / UNIQUE / CHECK (...) / default] | [o que guarda] |
| created_at | timestamptz | NOT NULL default now() | quando foi criado |
| updated_at | timestamptz | NOT NULL default now() | última alteração (trigger `trg_set_updated_at`) |

**Foreign keys:**
- `[coluna]` → `[tabela].[coluna]` — ON DELETE [CASCADE/SET NULL/RESTRICT] — [justificativa da escolha]

**Índices:**
- `[nome_idx]` em `([colunas])` — [por quê: usado em WHERE/ORDER BY/JOIN de qual rota]

**RLS (Row Level Security):**
- HABILITADO: [sim — obrigatório para tabelas com dados de usuário]
- Políticas: [quem pode SELECT/INSERT/UPDATE/DELETE o quê — 1 linha por política]

[... repetir por tabela ...]

## Regras de negócio no banco

[Constraints que codificam regra de negócio — ex: "CHECK (available_credits >= 0) em profiles:
saldo nunca negativo, protege contra race condition de débito duplo".]

## Funções, triggers e RPCs

| Nome | Tipo | O que faz | Por que existe (vs fazer na aplicação) |
|---|---|---|---|
| [nome] | function/trigger/RPC | [descrição] | [ex: atomicidade que a aplicação não garante] |

## Ordem de migrations

| # | Arquivo | O que cria | Depende de |
|---|---|---|---|
| 1 | [20261014130500_create_profiles.sql] | [tabelas] | — |

**Regras de migration safety:**
- NUNCA remover coluna antes do código que a usa ser removido e deployado
- Migrations idempotentes (IF NOT EXISTS / IF EXISTS / OR REPLACE)
- Aplicação em produção: só após merge, com aprovação do comandante, executada pelo [VAULT/SHIELD]

## Mapeamentos nome-de-coluna → campo-de-API

[Onde o contrato de API usa nome diferente da coluna real — causa comum de SQL de teste com coluna errada
(ver `sub-agentes/schema-validator.md`):]

| Tabela.coluna (real) | Campo na API | Rota |
|---|---|---|
| [customers.name] | [customerName] | [GET /api/customers] |

[Se não houver mapeamentos: "Nenhum — nomes de API espelham colunas 1:1."]
