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
