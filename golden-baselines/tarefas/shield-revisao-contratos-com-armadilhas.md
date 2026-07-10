# Tarefa Canônica — SHIELD — Revisão de contratos com armadilhas plantadas

**Agente-alvo:** SHIELD · **Duração esperada:** 1 janela · **Criada em:** 2026-07-10 (não alterar — ver README)
**Última atualização:** 2026-07-10 (v5.4 baseline) — se a tarefa precisar mudar, versione (crie v2 em arquivo novo, mantendo a v1 para histórico)

## Bloco de ativação (colar na janela do SHIELD)

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é SHIELD. Leia seu operativo e o protocolo de validação de contratos normalmente.

# Mini-plano — SHIELD | Golden | ONDA G-2
Tipo de tarefa: revisão de contratos da Fase 2

## 1. O que esta tarefa precisa produzir
Análise do project-core.md abaixo, identificando TODOS os
problemas de contrato ANTES que vire código. O objetivo é
pegar o que testes automáticos (contract-tester) NÃO pegam:
contratos INTERNAMENTE inconsistentes.

## 2. O contrato sob revisão (recorte do project-core.md)

## API — Fase 2 do projeto "lista de compras compartilhada"

### POST /api/lists
REQUEST: { name: string (1-100 chars), members?: string[] (emails) }
RESPONSE 201: { id: uuid, name: string, owner_id: uuid, created_at: ISO }
RESPONSE 422: { error: 'validation', details: [...] }
RESPONSE 500: { error: 'internal' }

### GET /api/lists/:id
REQUEST: (path param :id = uuid)
RESPONSE 200: { id, name, owner_id, members: [{ user_id, email, role }], items: [{ id, name, purchased_by, created_at }] }
RESPONSE 404: { error: 'not_found' }

### POST /api/lists/:id/items
REQUEST: { name: string (1-80 chars), added_by: uuid }
RESPONSE 201: { id, name, added_by, purchased_by: null, created_at }
RESPONSE 422: validation
RESPONSE 403: caller is not a member of list :id
RESPONSE 404: list :id doesn't exist

### PATCH /api/lists/:id/items/:itemId
REQUEST: { purchased_by: uuid | null }
RESPONSE 200: { id, name, purchased_by, created_at }
RESPONSE 403: not a member
RESPONSE 404: list OR item not found

### GET /api/users/:id/orders   <-- rota herdada de outro projeto, não deveria estar aqui
REQUEST: (path param :id)
RESPONSE 200: { orders: [...] }

## 3. Sua entrega
Lista priorizada de problemas de contrato, com severidade
(crítico / grave / menor) e patch textual sugerido para cada.
```

## Gabarito (checklist de Corretude — avaliador confere item a item)

### Problemas que SHIELD DEVE detectar

1. [ ] **PROBLEMA CRÍTICO 1:** POST /api/lists não cita rate limit nem rate-limit error (5xx só tem 'internal') — contrato não diz o que acontece se usuário cria 1000 listas em 1 minuto. Severidade: crítica.
2. [ ] **PROBLEMA CRÍTICO 2:** GET /api/users/:id/orders NÃO PERTENCE a este projeto (projeto é "lista de compras"). Rota órfã de outro sistema que entrou por engano. Severidade: crítica (escopo errado).
3. [ ] **PROBLEMA GRAVE 1:** POST /api/lists/:id/items — quem define `added_by`? O cliente manda no body, mas isso permite SPOOFING (usuário A adiciona item "comprado por usuário B" sem B ter comprado). Deveria ser SEMPRE o caller autenticado. Severidade: grave.
4. [ ] **PROBLEMA GRAVE 2:** PATCH /api/lists/:id/items/:itemId — sem constraint de role. Viewer deveria conseguir marcar comprado? Editor? Só owner? Contrato não define. Severidade: grave (vai virar bug de permissão).
5. [ ] **PROBLEMA GRAVE 3:** GET /api/lists/:id não cita autenticação. 404 com lista privada vazia vs 401 sem auth vs 403 sem ser membro — são casos DIFERENTES, contrato não distingue. Severidade: grave (vazamento de existência).
6. [ ] **PROBLEMA MENOR 1:** nomes de campos são em inglês mas comentários em português — sem consistência (regra §9 pede EN em código, PT em conteúdo; campos de API são código, deveriam ser EN, mas `members: [{ email }]` mistura inglês e email já é inglês mesmo — verificar uniformidade).

### O que SHIELD NÃO deve achar (anti-falso-positivo)

7. [ ] NÃO deve reprovar a existência de error 500 'internal' em todas as rotas (é padrão válido)
8. [ ] NÃO deve exigir UUIDs em vez de strings em path params (UUID é decisão de implementação, não de contrato)
9. [ ] NÃO deve reprovar a falta de paginação em GET /api/lists/:id (escopo MVP não exige; fase 3 talvez)

### Qualidade da revisão

10. [ ] Cada problema tem citação do trecho do contrato (linha ou parágrafo)
11. [ ] Cada problema tem severidade justificada em 1 linha
12. [ ] Cada problema tem patch sugerido (em pseudo-código do contrato, não código de implementação)
13. [ ] Lista priorizada (críticos primeiro, graves no meio, menores no fim)
14. [ ] Sem moralismo / alarmismo ("vai destruir a empresa" — tom profissional)

### Disciplina v5 — anti-tells

- SHIELD que só acha 1-2 problemas = reprovável (não leu com cuidado)
- SHIELD que acha 15 problemas (maioria inventada) = reprovável (alarme falso queima confiança do time)
- Patch sugerido em código TS = sinal de scope creep (SHIELD revisa contrato, não implementa)
- Problema sem patch = reprovável (achou mas não ajudou a resolver)