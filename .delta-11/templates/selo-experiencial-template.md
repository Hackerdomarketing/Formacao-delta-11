# 🔍 SELO EXPERIENCIAL — [Ciclo/Fase]

> **Template v5.2 — Roteiro do "Viu que Era Bom" (P4 etapa 7 da Criação).**
> Gerado pelo CRONOS ao final da cadeia automatizada (SHIELD → Fresh Reviewer → Cold Start Tester),
> ANTES do comandante aprovar. Salvo em `.delta-11/planos/SELO-EXPERIENCIAL-[ciclo].md`.
>
> REGRAS DE ESCRITA: português leigo, zero jargão, cada passo tem URL/comando + o que esperar +
> sinal de sucesso + "se falhar, me diga X". O comandante OPERA o produto, não lê relatório.
>
> Modo `.delta-11/.modo-selo`: [manual / automatico]. Em manual, CRONOS aguarda `aprovar`.

---

## O que mudou neste ciclo (resumo para o comandante)

- **[N] problemas críticos resolvidos** ([lista curta em linguagem leiga])
- **[N] melhorias aplicadas** ([idem])
- **Estado dos testes:** [ex: 277/277 verificações verdes]

---

## Como executar o selo — [tempo estimado]

### Passo 1 — [ação única e simples]

```bash
[comando exato, com export PATH se necessário]
```

[Onde clicar / o que abrir, com descrição visual]

**Sinal de que deu certo:** [o que o comandante VÊ quando funciona]
**Se falhar:** [causa provável + "me diga que eu [ação de contorno]"]

### Passo 2 — [próxima ação]

[Se este passo verifica correção de bug de selo anterior, diga qual — cria continuidade de confiança.]

1. [sub-passo com URL exata]
2. [sub-passo]

**Sinal de sucesso:** [...]
**Se falhar:** [...]

[... repetir o padrão para cada passo — SEMPRE incluir navegação manual pelos fluxos críticos
quando a fase tem UI: o comandante precisa USAR o produto, não só ver testes verdes ...]

### Passo final — testes menores (opcional)

- [verificações rápidas de menor risco]

---

## O que faz sentido REJEITAR

Se encontrar QUALQUER um destes, me diga antes de aprovar:

- [sintoma concreto e visível 1 — ex: 'texto X aparecendo na tela (violaria regra Y)']
- [sintoma 2 — ex: 'barra de progresso travada em 0%']
- [sintoma 3 — ex: 'página branca ou erro genérico']

---

## Ordem final

Se tudo funcionou E pareceu sólido: digite **`aprovar`**.
Se algo estranhar: descreva o que viu — abro tarefa de correção ANTES do selo. Não fecho ciclo com bug pendente.

## Depois do `aprovar`

1. [limpeza — ex: remover worktrees mergeadas]
2. [registro — ex: encerramento no project-core.md]
3. [próximos ciclos propostos — lista com 1 frase cada]
