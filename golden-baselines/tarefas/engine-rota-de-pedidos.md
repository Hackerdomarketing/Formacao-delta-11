# Tarefa Canônica — ENGINE — Rota de criação de pedidos

**Agente-alvo:** ENGINE · **Duração esperada:** 1 janela · **Criada em:** 2026-07-07 (não alterar — ver README)

## Bloco de ativação (colar na janela do ENGINE, simulando o mini-plano do CRONOS)

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é ENGINE. Leia seu operativo e sua base de conhecimento normalmente.

# Mini-plano — ENGINE | Golden | ONDA G-1
Tipo de tarefa: funcionalidade

## 1. O que esta tarefa precisa produzir
Rota POST /api/orders que cria um pedido.

## 2. Recorte relevante da fase anterior
Contrato [Fonte: esta tarefa canônica]:
- ENTRADA: { product_id: uuid, quantity: número inteiro 1-99, coupon_code: string opcional máx 32 }
- SAÍDA 201: { order_id: uuid, total_cents: inteiro, status: "pending" }
- ERROS: 401 sem sessão · 404 produto inexistente · 409 sem estoque · 422 validação
- Tabela products existe com: id, name, price_cents, stock [Fonte: esta tarefa canônica]
- Pagamento é registrado via serviço externo de cobrança usando o cliente fictício `billing` com a interface fixa [Fonte: esta tarefa canônica]:
  ```typescript
  billing.createCharge({ amount_cents: number, order_id: string }): Promise<
    | { ok: true; charge_id: string }
    | { ok: false; reason: 'insufficient_funds' | 'not_configured' | 'network_error' }
  >
  ```
  Sem `throw`; retorno tipado. Timeout externo cabe ao ENGINE (billing só responde ok/reason).

## 3. Critérios de sucesso
- Rota implementada conforme contrato, com validação Zod completa
- Estoque verificado e decrementado SEM race condition
- Serviço de cobrança inicializado sob demanda, com timeout e tratamento de falha
- Testes: caminho feliz, input inválido, não autorizado

## 4. Dependências — nenhuma (projeto de teste)

## 5. LIMITES DE ESCOPO
- NÃO criar tela/componente
- NÃO criar outras rotas (GET, listagem, etc.)
- NÃO mexer no esquema do banco além do que o contrato dá

## 6. CONVENÇÕES — as fixas do template (limites §8 + idioma §9)
```

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
