# CLASSIFICAÇÃO DE PROJETOS — FORMAÇÃO Δ-11 (v6.3)

Esta é a **régua única** de complexidade do sistema. Qualquer outro arquivo que fale de pontuação de complexidade usa estes números.

## CRITÉRIOS (usado pelo ATLAS na Fase 1)

5 critérios, cada um vale de 1 a 3 pontos. A soma vai de 5 a 15.

| Critério | 1 ponto | 2 pontos | 3 pontos |
|---------|---------|----------|----------|
| Telas e rotas | Até 5 | 6 a 15 | Mais de 15 |
| Integrações externas | Nenhuma ou 1 | 2 a 3 | Mais de 3 |
| Modelo de dados | Até 5 tabelas | 6 a 15 tabelas | Mais de 15 |
| Tempo real | Sem | Notificações ao vivo | Edição colaborativa |
| Segurança | Básica | Dados pessoais | Financeiro ou saúde |

## RESULTADO

| Soma | Complexidade | Agentes que o CRONOS orquestra |
|------|-------------|---------|
| 5–8 | BAIXA | ATLAS + CRONOS + 2 líderes que acumulam papéis (FRONT faz PIXEL+FORM; BACK faz ENGINE+VAULT) + SHIELD + SCOUT sob demanda |
| 9–12 | MÉDIA | Todos os 10 (ATLAS, CRONOS, FRONT, PIXEL, FORM, BACK, ENGINE, VAULT, SHIELD, SCOUT sob demanda) |
| 13–15 | ALTA | Todos os 10, com acompanhamento reforçado do CRONOS pelo sub-agente `code-architect` |

Em qualquer faixa, o CRONOS dispara no máximo 3 agentes ao mesmo tempo (`paralelo_max` em `.delta-11/.config-limites.json`), em ondas. O comandante não abre nada: todo disparo é do CRONOS.

## PARA QUE O SCORE SERVE

O ATLAS usa o score na Fase 1 para decidir:
- **Acúmulo de papéis:** se a soma é **≤ 8** (faixa BAIXA), FRONT acumula PIXEL+FORM e BACK acumula ENGINE+VAULT. Com **9 ou mais**, eles são separados.
- Estimativa de escopo e prazo.
- Se o `code-architect` acompanha a execução de perto (faixa ALTA).

O score **NÃO** decide se a Fase 2.5 acontece: os mini-planos da Fase 2.5 são obrigatórios em TODO projeto (Regra 13).

## O CRONOS ENTRA SEMPRE

O score **NÃO determina se o CRONOS entra no projeto**. Desde a v4.0, o CRONOS é ativado em TODO projeto, independente da complexidade — inclusive na faixa BAIXA.

**Por quê:** em times de engenharia reais, o arquiteto entrega o blueprint e sai; o gerente de projeto orquestra a execução. Manter essa separação em todos os projetos (e não apenas nos complexos) torna o sistema previsível e escalável. Mesmo um projeto simples precisa de alguém cobrando, sequenciando e destravando.

O score indica a QUANTIDADE de agentes que o CRONOS orquestra, nunca SE o CRONOS orquestra.
