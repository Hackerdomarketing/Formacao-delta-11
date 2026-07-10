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
