# Tarefa Canônica — CRONOS — Mini-planos para onda com 3 agentes e dependências

**Agente-alvo:** CRONOS · **Duração esperada:** 1 janela · **Criada em:** 2026-07-10 (não alterar — ver README)
**Última atualização:** 2026-07-10 (v5.4 baseline) — se a tarefa precisar mudar, versione (crie v2 em arquivo novo, mantendo a v1 para histórico)

## Bloco de ativação (colar na janela do CRONOS, simulando contexto pós-Fase 2)

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é CRONOS. Leia seu operativo e o protocolo de sequenciamento normalmente.

# Contexto — CRONOS | Golden | ONDA G-2
Você está no FINAL da Fase 2 (Planejamento). O ATLAS já entregou
o project-core.md com o seguinte recorte:

# Project-core (recorte relevante)
## Stack
- Next.js 15 (App Router) + Supabase (banco + auth + storage)
- Sem backend separado (rotas em src/app/api/)

## Banco de dados
- Tabela `lists`: id, owner_id (FK auth.users), name, created_at
- Tabela `list_items`: id, list_id (FK), name, added_by (FK), purchased_by (FK nullable), created_at
- Tabela `list_members`: list_id, user_id, role (owner|editor|viewer), added_at
- RLS em todas: usuário lê/escreve só listas onde é member

## API (Fase 2)
- POST /api/lists — criar lista
- POST /api/lists/:id/members — adicionar membro (só owner)
- POST /api/lists/:id/items — adicionar item
- PATCH /api/lists/:id/items/:itemId — marcar comprado
- GET /api/lists/:id — detalhes + items + members

# Sua tarefa
Sequenciar a ONDA 1 do projeto, que tem 3 agentes de execução:
- VAULT (criar migrations + RLS + seed)
- ENGINE (criar as 5 rotas da API)
- FRONT (criar layout base + página de detalhe da lista)

Gere o sequenciamento da onda: ordem de despacho, dependências,
e os 3 mini-planos (um por agente) prontos para copiar e colar.
```

## Gabarito (checklist de Corretude — avaliador confere item a item)

### Sequenciamento

1. [ ] Identificou as dependências: VAULT antes de ENGINE (rotas dependem de tabelas), ENGINE antes de FRONT (FRONT consome API)
2. [ ] Não disparou FRONT em paralelo com ENGINE (mesmo que zonas diferentes conceitualmente, FRONT precisa do contrato da API estável)
3. [ ] Especificou paralelismo real: VAULT roda sozinho primeiro, ENGINE e FRONT não rodam juntos (FRONT é dependente)
4. [ ] Cada mini-plano tem path absoluto dos arquivos que será criado (não só "rotas em src/app/api/")
5. [ ] Cada mini-plano tem referência explícita ao contrato: "ENVIAR REQUEST: { user_id, list_id }" etc
6. [ ] Cada mini-plano cabe em 1 janela (escopo fechado, sem "e depois faça também...")
7. [ ] Menciona onde os sub-agentes obrigatórios rodam no final (build-validator, contract-tester) — sem isso o agente pensa que acabou e pula a cadeia

### Mini-plano VAULT

8. [ ] Cita migrations específicas em ordem (criar lists, list_items, list_members, índices, RLS)
9. [ ] Cita RLS por tabela (SELECT, INSERT, UPDATE, DELETE explícitos) — não genérico
10. [ ] Cita criação de seed mínimo (1 usuário, 1 lista, 2 itens, 2 membros) para ENGINE poder testar

### Mini-plano ENGINE

11. [ ] Tem exemplos de REQUEST e RESPONSE para cada uma das 5 rotas
12. [ ] Marca quais rotas precisam de validação Zod (entrada do usuário)
13. [ ] Marca quais rotas fazem verificação de permissão (não basta JWT — checa role em list_members)
14. [ ] Marca quais rotas retornam 404 vs 403 vs 401 (diferença importa para o FRONT)

### Mini-plano FRONT

15. [ ] Define layout raiz com navegação mínima (já que é uma app autenticada)
16. [ ] Define a página /lists/:id com: lista de items, form de adicionar item, marcar como comprado, ver quem comprou
17. [ ] Marca componentes compartilhados que dependem de FRONT (não PIXEL/FORM) — ex: layout, header, footer
18. [ ] Define estados visuais obrigatórios (skeleton, erro, sucesso) — não só "bonito"

### Convenções

19. [ ] Todos os mini-planos seguem o template `mini-plano-agente-template.md`
20. [ ] Sem CLI-dispatch direto (CRONOS dispara via Agent tool nativo, não AppleScript)
21. [ ] Heartbeats configurados (CRONOS precisa monitorar os 3 agentes em paralelo)
22. [ ] Caminhos absolutos dos arquivos do projeto (não relativos à worktree)

### Disciplina v5 — anti-tells

- Mini-plano sem exemplo de REQUEST/RESPONSE = reprovável (agente vai improvisar contrato)
- Mini-plano que diz "ver contrato no project-core.md" sem recortar o trecho relevante = reprovável (CRONOS economiza contexto do agente)
- Sequenciamento que ignora dependência real (ex: FRONT antes de ENGINE) = reprovável
- Mini-plano sem gates de qualidade no fim (build-validator, contract-tester) = reprovável