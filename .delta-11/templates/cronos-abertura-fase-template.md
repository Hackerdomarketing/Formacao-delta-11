# Abertura da Fase [N+1] — [data ISO]

> **Template v6.3 (2026-10-14) — Protocolo de Abertura de Fase (P3 da Criação).**
> Executado pelo CRONOS DEPOIS do selo da Fase N e ANTES de disparar qualquer agente da Fase N+1.
> Salvo em `.delta-11/memoria/CRONOS-abertura-fase-[N+1].md` — NUNCA dentro do project-core (só o ATLAS escreve
> no project-core — D7). Drift que precise mudar o contrato vai para o ATLAS (o CRONOS o dispara).

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

## Aviso ao comandante (painel)

[Cópia do aviso mostrado no painel: fase selada + N ajustes + os ajustes mais relevantes, em linguagem leiga.
É um AVISO, não uma pergunta: no modo `automatico` a primeira onda já foi despachada. Só no `modo manual` o aviso
termina pedindo `aprovar` (fronteira entre fases — D4). Decisão de negócio/escopo que só ele pode tomar vai em
pergunta separada, objetiva.]
