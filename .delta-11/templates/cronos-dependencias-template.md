# Mapa de Dependências — [Ciclo/Fase] ([data ISO])

> **Template v5.2 — Mapa de dependências do CRONOS (Fase 2.5, Passo 2).**
> Salvo em `.delta-11/planos/CRONOS-dependencias[-ciclo].md`.

Gerado por: CRONOS
Base: [quais tarefas/decisões já concluídas este mapa assume — ex: "T-001 (ATLAS decisões) e T-002 (contratos) concluídas"]

## Dependências tarefa-a-tarefa

| Tarefa | Agente | Depende de | Motivo |
|---|---|---|---|
| T-XXX | [AGENTE] | (nenhuma — pode iniciar imediatamente) | [o que produz] |
| T-YYY | [AGENTE] | T-XXX | [o que consome de T-XXX] |

### Notas de paralelismo estratégico

[Onde dá para ganhar tempo: quais tarefas dependem SÓ de tipos/definições e podem começar antes
(TDD-friendly — testes vermelhos até implementação aterrissar), quais precisam de dados reais.]

## Caminho crítico

```
[AGENTE] T-XXX (~tempo)
    ↓
[cadeia mais longa de dependências sequenciais]
```

**Agente gargalo:** [quem + por quê]
**Agentes com folga:** [quem + quanta folga]

## Gaps resolvidos vs. spec original

[Para cada ambiguidade encontrada entre kanban/contratos/spec: qual era o gap, como foi resolvido,
qual tarefa ficou dona da resolução. Se nenhum: "Nenhum gap identificado".]

## Anti-padrões a evitar neste ciclo

- [erro previsível específico deste ciclo — ex: "VAULT criar migration sem necessidade (schema já comporta)"]
- [outro — ex: "PIXEL antecipar visual antes dos types aterrissarem"]

## Nota sobre planejamento anterior

[Se substitui mapa de ciclo anterior: onde o antigo está preservado.]
