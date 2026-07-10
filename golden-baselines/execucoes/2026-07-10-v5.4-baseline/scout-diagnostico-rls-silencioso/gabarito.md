## Gabarito (checklist de Corretude — avaliador confere item a item)

### Investigação

1. [ ] Levantou hipóteses ANTES de chutar causa-raiz — pelo menos 4 hipóteses iniciais com chance plausível
2. [ ] HIPÓTESE A: "RLS está bloqueando e retorna array vazio para algumas linhas" — VERIFICADA — DESCARTADA (3 itens aparecem, não 0)
3. [ ] HIPÓTESE B: "filtro .eq('user_id', user.id) está pegando user_id errado (do Clerk vs do banco)" — VERIFICADA — CONFIRMADA COMO CAUSA
4. [ ] HIPÓTESE C: "paginação silenciosa (limit default = 10)" — VERIFICADA — DESCARTADA (3 < 10)
5. [ ] HIPÓTESE D: "cache do Next.js mostrando resposta antiga" — VERIFICADA — DESCARTADA (outros usuários ok)
6. [ ] HIPÓTESE E: "view no Supabase filtrando por outro critério" — VERIFICADA — DESCARTADA

### Causa-raiz (diagnóstico final)

7. [ ] Identifica que `user.id` do Clerk é DIFERENTE de `auth.uid()` do Supabase RLS (são 2 sistemas de auth paralelos)
8. [ ] Explica que o filtro `eq('user_id', user.id)` filtra pelo ID do Clerk, mas a coluna `user_id` no banco tem o ID do Supabase Auth (`auth.uid()`)
9. [ ] Resultado: query filtra por um ID que não existe na coluna → retorna matches parciais (3 pedidos que por algum motivo têm esse ID — provavelmente pedidos de TESTE antigos)
10. [ ] Cita a query exata e a policy RLS: `CREATE POLICY orders_select ON orders FOR SELECT USING (user_id = auth.uid())` — note que policy espera auth.uid(), não Clerk user.id

### Patch sugerido

11. [ ] Propõe 2 caminhos: (a) usar auth do Supabase em vez de Clerk; (b) criar mapping Clerk→Supabase user.id e usar o segundo no filtro
12. [ ] Recomenda o (a) por eliminar complexidade (1 sistema de auth em vez de 2)
13. [ ] Patch sugerido NÃO é código pronto — é direção + arquivos a mexer

### Teste de regressão

14. [ ] Propõe teste SQL: criar usuário de teste com 5 pedidos, logar como ele via Supabase Auth (não Clerk), verificar que getUser().id === auth.uid() e query retorna 5
15. [ ] Propõe teste E2E: simular login de João (via Supabase Auth diretamente), acessar /pedidos, contar items

### Documentação

16. [ ] Arquivo `decisoes/AAAA-MM-DD-bug-rls-silencioso.md` criado seguindo template `bug-report-template.md`
17. [ ] Gotcha escrito em `.delta-11/memoria/gotchas.md` se for padrão recorrente (G-NNN)
18. [ ] Manda SendMessage ao CRONOS com achados (não tenta consertar)
19. [ ] Sem `console.log` deixado no código de produção
20. [ ] Sem código alterado (SCOUT é read-only no fluxo reativo)

### Disciplina v5 — anti-tells

- SCOUT que pula direto pra causa sem levantar hipóteses = reprovável (pode ser viés de confirmação)
- SCOUT que conserta em vez de diagnosticar = reprovável (scope creep)
- SCOUT que ignora "3 itens aparecem" e foca só em "por que não 12" = reprovável (3 !== 0 é evidência importante)
- Diagnóstico sem patch + teste = reprovável (achou mas não ajudou a fechar o ciclo)
