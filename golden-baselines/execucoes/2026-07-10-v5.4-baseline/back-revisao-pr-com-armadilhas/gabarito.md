## Gabarito (checklist de Corretude — avaliador confere item a item)

### Detecção dos problemas

1. [ ] **PROBLEMA 1 detectado:** uso de `SUPABASE_SERVICE_ROLE_KEY` (cria cliente admin) em vez de cliente com sessão do usuário — isso IGNORA RLS. Resultado: o endpoint retorna pedidos de QUALQUER usuário desde que autenticado, não só do usuário da sessão. Severidade: crítica.
2. [ ] **PROBLEMA 2 detectado:** N+1 — `select('*, items:order_items(*)')` faz UMA query para orders e UMA para items por pedido. Para usuário com 100 pedidos, são 101 queries. Severidade: grave (não derruba o sistema mas derruba performance em produção).
3. [ ] Ambos problemas têm explicação de POR QUE importam, não só "isso está errado"

### Qualidade da revisão

4. [ ] Comentário do PROBLEMA 1 inclui sugestão concreta (usar `createServerClient` com cookies do request, ou `supabase.auth.setSession(session.token)` antes da query) — não só "use cliente do usuário"
5. [ ] Comentário do PROBLEMA 2 inclui sugestão concreta (fazer o JOIN numa única query com `select('*, items:order_items(*)')` mas trazendo via foreign key explícita, OU usar RPC no banco) — não só "evite N+1"
6. [ ] Cada comentário tem referência à regra violada (regra-codigo §X, OWASP, etc)
7. [ ] Não inventou TERCEIRO problema falso (ex: "falta testes" quando o PR não está pedindo) — manter foco no escopo
8. [ ] Tom profissional, sem agressividade nem sarcasmo (revisor em time real)

### Verificações POSITIVAS (BACK deve reconhecer o que está certo)

9. [ ] Reconhece que a validação de sessão está presente (não é NULL)
10. [ ] Reconhece que o tratamento de erro 500 existe
11. [ ] Reconhece que o uso de status codes apropriados (401 vs 500) está correto

### Convenções

12. [ ] Usa linguagem técnica em inglês para nomes/código (regra §9)
13. [ ] Comentários da revisão em português
14. [ ] Comentário cita path do arquivo e linha aproximada
15. [ ] Sem código novo criado (revisão não vira feature) — se back-end propuser patch alternativo, deve vir como SUGESTÃO em texto, não como commit

### Disciplina v5 — anti-tells

- Revisão que aprova com 1 fix genérico ("refatorar pra ficar melhor") = reprovável
- Revisão que ignora N+1 achando que é "detalhe" = reprovável
- Revisão que ignora RLS bypass achando que "middleware vai cobrir" = reprovável
- Revisão com 10 problemas menores e NENHUM dos 2 críticos = reprovável (sinal de que não entendeu o código)
