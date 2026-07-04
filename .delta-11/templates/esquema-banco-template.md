# ESQUEMA DE BANCO — [NOME DO PROJETO]

> **Template v5.2 — Fatia de domínio "banco" (v4.0.1).**
> Documento complementar ao project-core.md. Gerado por ATLAS na Fase 2. Salvo em
> `.delta-11/memoria/esquema-banco.md` (ou `.delta-11/memoria/project-core/banco.md`).
> Consumido por: VAULT (implementa), BACK/ENGINE (consultam), SHIELD/SCOUT (verificam).
> ATENÇÃO (lição T-017): as MIGRATIONS são a fonte de verdade final para nomes de colunas.
> Este documento define a INTENÇÃO; o `schema-validator` compara os dois e acusa drift.
> Somente o ATLAS edita.

## Visão geral do modelo

[2-4 frases: as entidades principais e como se relacionam, em linguagem leiga.]

## Tabelas

### [nome_da_tabela]

**Propósito:** [1 frase]

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| id | uuid | PK, default gen_random_uuid() | identificador |
| [coluna] | [tipo] | [NOT NULL / UNIQUE / CHECK (...) / default] | [o que guarda] |
| criado_em | timestamptz | NOT NULL default now() | |

**Foreign keys:**
- `[coluna]` → `[tabela].[coluna]` — ON DELETE [CASCADE/SET NULL/RESTRICT] — [justificativa da escolha]

**Índices:**
- `[nome_idx]` em `([colunas])` — [por quê: usado em WHERE/ORDER BY/JOIN de qual rota]

**RLS (Row Level Security):**
- HABILITADO: [sim — obrigatório para tabelas com dados de usuário]
- Políticas: [quem pode SELECT/INSERT/UPDATE/DELETE o quê — 1 linha por política]

[... repetir por tabela ...]

## Regras de negócio no banco

[Constraints que codificam regra de negócio — ex: "CHECK (creditos_disponiveis >= 0) em usuarios:
saldo nunca negativo, protege contra race condition de débito duplo".]

## Funções, triggers e RPCs

| Nome | Tipo | O que faz | Por que existe (vs fazer na aplicação) |
|---|---|---|---|
| [nome] | function/trigger/RPC | [descrição] | [ex: atomicidade que a aplicação não garante] |

## Ordem de migrations

| # | Arquivo | O que cria | Depende de |
|---|---|---|---|
| 001 | [nome] | [tabelas] | — |

**Regras de migration safety:**
- NUNCA remover coluna antes do código que a usa ser removido e deployado
- Migrations idempotentes (IF NOT EXISTS / IF EXISTS / OR REPLACE)
- Aplicação em produção: só após merge, com aprovação do comandante, executada pelo [VAULT/SHIELD]

## Mapeamentos nome-de-coluna → campo-de-API

[Onde o contrato de API usa nome diferente da coluna real — a causa raiz do bug T-017:]

| Tabela.coluna (real) | Campo na API | Rota |
|---|---|---|
| [licenses.name] | [client_name] | [GET /api/licenses] |

[Se não houver mapeamentos: "Nenhum — nomes de API espelham colunas 1:1."]
