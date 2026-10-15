# Plano de Sequenciamento — [Ciclo/Fase] ([data ISO])

> **Template v6.4 (2026-10-15) — Sequenciamento do CRONOS (Fase 2.5, Passo 4).**
> **Regras de onda (v6.4):** a onda sai INTEIRA de uma vez (todas as chamadas `Agent` na mesma mensagem, em segundo
> plano), até `paralelo_max` (padrão 5); acima disso, fila por vaga. Só fica para a onda seguinte a tarefa que edita
> o MESMO arquivo de outra ou que tem dependência declarada. Tarefa grande vira sub-tarefas PARALELAS.
> Cada agente da onda recebe UM mini-plano em `.delta-11/planos/[AGENTE]-plan.md` (sobrescrito a cada onda; o
> anterior vai para `planos/arquivo/` — D17). Executores são despachados pelo CRONOS com `isolation: "worktree"`
> e `model` do `perfis/[AGENTE].json` (D2, D26).
> Salvo em `.delta-11/planos/CRONOS-sequenciamento[-ciclo].md`. Se REVISADO após replanejamento,
> declare no título e preserve os valores fundamentais que não mudaram (nota ao final).

**Visão da fase (1 frase):** [a visão única que todas as ondas servem — vai no prompt de ativação de cada agente]

**Ciclo:** [N] · **Ciclo 2 em diante:** [Fase 2.3: "sem tecnologia nova" ou a lista do que foi pesquisado] ·
[Fase 2.4: "sem ferramenta nova" ou a lista do que foi provisionado]

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

(Uma tarefa só vai para uma onda posterior se tiver DEPENDÊNCIA DECLARADA ou precisar editar o MESMO arquivo de
outra. Tudo o que não depende de nada entra na ONDA 1.)

### ONDA 1 (disparo imediato — todos na mesma mensagem):
- [AGENTE] — [tarefas] — [por que agora] — worktree: [nome]   ex.: VAULT — tabelas — caminho crítico
- [AGENTE] — [tarefas] — depende de: nada de código — worktree: [nome]   ex.: FRONT — layouts, em paralelo com o VAULT
**Fila (se passar de `paralelo_max`):** [AGENTE] — [tarefas] — sai na primeira vaga livre

### ONDA 2 (dispara quando [sinal — ex.: tabelas do VAULT aprovadas pelo SHIELD da Onda 1 e juntadas]):
- [AGENTE] — [tarefas] — depende de: [o quê — mesmo arquivo de T-XXX, ou dependência declarada de T-XXX]
- [AGENTE] — [tarefas] — **sem dependência do código da Onda 1** → pipeline: sai na MESMA mensagem do SHIELD da
  Onda 1, enquanto ele revisa

### Revisão (V6, V7)
- SHIELD — UM por onda (ou um por zona, em paralelo, se a onda for grande), disparado quando os executores da onda
  terminam. Enquanto ele revisa a onda N, a onda N+1 já roda nas tarefas que não dependem do código da onda N.

## Sinais de desbloqueio

| Agente | Sinal esperado | Onde monitorar |
|---|---|---|
| [AGENTE] | SendMessage com payload `{tarefas_concluidas: [...]}` | inbox do CRONOS |

## Tarefas no caminho crítico (NUNCA podem atrasar)

- [T-XXX] — [por quê é crítica]

## Merge final da onda

1. Revisão: UM SHIELD para a onda inteira (onda grande: um SHIELD por zona, em paralelo), veredito por tarefa.
2. Ordem de consolidação (só branches com todas as tarefas APROVADAS): [VAULT → ENGINE → SHIELD → PIXEL — adaptar]
3. Validação final: `tsc --noEmit` + `npm run test:contracts` + `npm run build` (adaptar ao stack)
4. Fim de fase: Fresh Reviewer + Cold Start Tester (um por `-produto.md`) + `qa-ui-tandem` (Selo Experiencial;
   roteiro em `planos/selo-experiencial-fase-[N].md`, a partir de `.delta-11/templates/selo-experiencial-template.md`)
   — disparados JUNTOS, em segundo plano; o CRONOS espera todos
5. Selo: modo `automatico` = revisores verdes fecham a fase sozinhos; `modo manual` = comandante digita `aprovar`

## Notas de contorno

[Bugs de plataforma conhecidos que afetam este ciclo (ex: worktree de origin/main velho),
mitigações aplicadas, pendências que aguardam decisão do comandante (só as 3 situações da D4).]

## Nota sobre planejamento anterior

[Se este documento substitui outro: o que foi preservado, o que mudou e por quê. Onde a versão anterior vive (história do CRONOS).]
