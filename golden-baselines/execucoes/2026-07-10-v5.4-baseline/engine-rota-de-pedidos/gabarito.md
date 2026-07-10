## Gabarito (checklist de Corretude — avaliador confere item a item)

1. [ ] Rota em `src/app/api/orders/route.ts` com `export async function POST`
2. [ ] Validação Zod: `quantity` com min(1) e max(99); `coupon_code` com max(32); erro 422 com detalhes
3. [ ] Sessão verificada DENTRO da rota (não só middleware) → 401
4. [ ] Produto inexistente → 404; sem estoque → 409
5. [ ] Decremento de estoque atômico (`UPDATE ... WHERE stock >= quantity` ou RPC) — NÃO ler-depois-escrever
6. [ ] Cliente "billing" criado por função `getBilling()` sob demanda (nunca no nível do módulo), com timeout ~5s e falha tratada sem derrubar a rota
7. [ ] Resposta 201 exatamente `{ order_id, total_cents, status }` — sem campos extras
8. [ ] `total_cents` em centavos (inteiro), nunca float
9. [ ] 3 testes presentes e passando (feliz, inválido, não autorizado)
10. [ ] Mensagens de erro ao usuário em português; nomes de código em inglês; rota ≤ 150 linhas
