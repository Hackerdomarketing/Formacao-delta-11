# Tarefa Canônica — VAULT — Esquema de assinaturas com RLS

**Agente-alvo:** VAULT · **Duração esperada:** 1 janela · **Criada em:** 2026-07-07 (não alterar — ver README)

## Bloco de ativação

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é VAULT. Leia seu operativo e sua base de conhecimento normalmente.

# Mini-plano — VAULT | Golden | ONDA G-1
Tipo de tarefa: funcionalidade

## 1. O que esta tarefa precisa produzir
Migrations Supabase para um sistema de assinaturas.

## 2. Recorte relevante da fase anterior
Esquema [Fonte: esta tarefa canônica]:
- Tabela subscriptions: id, user_id (FK auth.users), plan (free|pro|enterprise), status (active|cancelled|past_due), current_period_end, created_at, updated_at
- Tabela subscription_events: id, subscription_id (FK), event_type, payload jsonb, created_at — histórico imutável
- Regra de negócio: usuário vê e altera APENAS a própria assinatura; eventos são só-leitura para o usuário; serviço administrativo escreve eventos

## 3. Critérios de sucesso
- Migrations aplicáveis em sequência, 1 assunto por migration
- RLS completa nas 2 tabelas (as 4 operações pensadas, não só SELECT)
- Índices para os acessos previstos; FKs com ON DELETE explícito e justificado

## 4. Dependências — nenhuma (projeto de teste)

## 5. LIMITES DE ESCOPO
- NÃO criar rotas de API nem código TypeScript
- NÃO criar tabelas além das 2 do contrato
- NÃO aplicar em banco compartilhado — só gerar as migrations

## 6. CONVENÇÕES — as fixas do template (limites §8 + idioma §9)
```

## Gabarito (checklist de Corretude)

1. [ ] Migrations numeradas em sequência em `supabase/migrations/`, 1 assunto por arquivo
2. [ ] `ENABLE ROW LEVEL SECURITY` nas DUAS tabelas
3. [ ] subscriptions: policies de SELECT/INSERT/UPDATE com `USING` E `WITH CHECK` amarrados a `auth.uid()` — UPDATE não permite trocar `user_id`
4. [ ] subscription_events: SELECT permitido só ao dono (via join/subquery à assinatura); INSERT/UPDATE/DELETE negados ao usuário comum (escrita só via service role)
5. [ ] Nenhuma policy `USING (true)` em dado privado
6. [ ] `plan` e `status` restritos (CHECK ou enum) aos valores do contrato
7. [ ] Índices em `subscriptions.user_id` e `subscription_events.subscription_id` (+ `status` se consultado)
8. [ ] FKs com `ON DELETE` explícito + comentário SQL justificando a escolha
9. [ ] Trigger de `updated_at` na tabela subscriptions
10. [ ] Nomes de tabelas/colunas em inglês; comentários SQL em português; timestamps com timezone
