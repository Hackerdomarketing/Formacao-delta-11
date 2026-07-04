# Plano de Sequenciamento — [Ciclo/Fase] ([data ISO])

> **Template v5.2 — Sequenciamento do CRONOS (Fase 2.5, Passo 4).**
> Salvo em `.delta-11/planos/CRONOS-sequenciamento[-ciclo].md`. Se REVISADO após replanejamento,
> declare no título e preserve os valores fundamentais que não mudaram (nota ao final).

**Visão da fase (1 frase):** [a visão única que todas as ondas servem — vai no prompt de ativação de cada agente]

## Status atual

[Se o ciclo já começou: o que está CONCLUÍDO (com commits), o que está DESCARTADO (com worktree preservada), o que roda agora.]

## Caminho Crítico

```
[AGENTE-1] T-XXX (~tempo)
    ↓
[AGENTE-2] T-YYY → T-ZZZ (sequencial interno)
    ↓
Merge — quando também [AGENTE-3] verde e [AGENTE-4] pronto
```

**Agente gargalo:** [quem] — [por quê]
**Agentes com folga:** [quem pode atrasar sem bloquear + quanto]

## Sequência de Ativação

### ONDA 1 (disparo imediato):
- [AGENTE] — [tarefas] — [por que primeiro] — worktree: [nome]

### ONDA 2 (dispara quando [sinal]):
- [AGENTE] — [tarefas] — depende de: [o quê]

## Sinais de desbloqueio

| Agente | Sinal esperado | Onde monitorar |
|---|---|---|
| [AGENTE] | SendMessage com payload `{tarefas_concluidas: [...]}` | inbox do CRONOS |

## Tarefas no caminho crítico (NUNCA podem atrasar)

- [T-XXX] — [por quê é crítica]

## Merge final da onda

1. Ordem de consolidação: [VAULT → ENGINE → SHIELD → PIXEL — adaptar]
2. Validação final: `tsc --noEmit` + `npm run test:contracts` + `npm run build` (adaptar ao stack)
3. Roteiro do Viu que Era Bom (usar `.delta-11/templates/selo-experiencial-template.md`)
4. Selo do comandante → ciclo fechado

## Notas de contorno

[Bugs de plataforma conhecidos que afetam este ciclo (ex: worktree de origin/main velho),
mitigações aplicadas, pendências que aguardam decisão do comandante.]

## Nota sobre planejamento anterior

[Se este documento substitui outro: o que foi preservado, o que mudou e por quê. Onde a versão anterior vive (história do CRONOS).]
