# Abertura da Fase [N+1] — [data ISO]

> **Template v5.2 — Protocolo de Abertura de Fase (v4.0.1, P3 da Criação).**
> Executado pelo CRONOS DEPOIS do selo da Fase N e ANTES de disparar qualquer agente da Fase N+1.
> Salvo em `.delta-11/planos/CRONOS-abertura-fase-[N+1].md`.

## O que foi selado na Fase [N]

[Resumo do acumulado REAL — não o planejado. Fontes: git log, ls migrations/, grep nas rotas,
arquivos [AGENTE]-produto.md da fase, relatório do Code Architect.]

- **Tabelas que existem (real):** [lista]
- **Rotas implementadas (real):** [lista ou contagem + referência]
- **Decisões técnicas que surgiram DURANTE a execução:** [o que não estava no plano original]

## Drift detectado

| Item | Tipo | Impacto | Ação |
|---|---|---|---|
| [descrição] | positivo (melhor que o plano) / negativo (diferente sem aprovação) / emergente / lacuna | [o que muda adiante] | absorver no contrato / escalar ao ATLAS / adicionar à próxima fase |

[Se nenhum drift: "Nenhum drift detectado — execução aderente ao plano."]

## Ajustes nos mini-planos da Fase [N+1]

[NÃO criar planos do zero — ajustar os da Fase 2.5 com base na realidade:]

- **[AGENTE]-plan:** [o que mudou e por quê — submetas removidas/adicionadas, nomes de campos REAIS]

## Mensagem enviada ao comandante

[Cópia da mensagem: fase selada + N ajustes + ajustes mais relevantes + pedido de aprovação para a primeira onda.]
