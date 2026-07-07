# Testes de Contrato

Esta pasta recebe os testes que o sub-agente `contract-tester` gera a partir dos contratos do
`project-core.md` (Fase 2 — Passo 2.7 do SHIELD). Os testes nascem VERMELHOS e vão ficando verdes
conforme a Fase 4 implementa cada rota — é o termômetro objetivo do progresso.

Regras:
- NUNCA ajustar um teste para acomodar código (teste falhou = código errado — Regra de Ouro do SHIELD)
- Rodar com `npm run test:contracts` (o build-validator executa em toda tarefa)
- Descrições de teste em português (`it('deve rejeitar email inválido', ...)`), código em inglês
