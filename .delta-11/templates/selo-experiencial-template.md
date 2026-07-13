# 🔍 SELO EXPERIENCIAL — [Ciclo/Fase] (v6.1+ — Automatizado via Tandem Browser)

> **Template v6.1 — Sub-agente de QA/UI autônomo.**
> Em vez de roteiro para humano operar, o selo é EXECUTADO por sub-agente
> usando Tandem Browser MCP (navegador Electron programável). Humano só vê o relatório.
>
> Modo `.delta-11/.modo-selo`: `automatico` (default v6.1+). Em automatico, sub-agente QA
> roda o roteiro e retorna PASS/FAIL. Em `manual`, humano recebe roteiro (legado).

---

## Quem executa este selo

**Sub-agente `qa-ui-tandem`** — disparado pelo CRONOS via `Agent tool` ao final da cadeia automatizada (SHIELD → Fresh Reviewer → Cold Start Tester), ANTES do comandante aprovar.

```
Agent(
  description: "Selo UI — projeto [NOME]",
  subagent_type: "general-purpose",
  run_in_background: false,
  prompt: "Formação Δ-11. Selo Experiencial. Use Tandem Browser MCP para
navegar autonomamente os fluxos críticos do projeto. Retorne PASS ou
FAIL com diagnostico. NAO pergunte ao humano — execute."
)
```

---

## Fluxos a serem testados pelo sub-agente

Para cada fluxo crítico do produto, o sub-agente QA:

1. **Acessa a URL** via `browser_navigate(url)` do Tandem Browser MCP
2. **Executa ações** via `browser_click`, `browser_type`, `browser_snapshot`
3. **Verifica resultados** via `browser_snapshot` para confirmar estado esperado
4. **Reporta** PASS ou FAIL com evidência (snapshot do estado)

### Fluxos críticos (gerados pelo CRONOS baseado no project-core.md)

- **[Fluxo 1]**: [URL inicial] → [ação esperada] → [resultado esperado]
- **[Fluxo 2]**: ...
- **[Fluxo N]**: ...

---

## O que muda em relação ao template v5.2

- ❌ Removido: roteiro de "Passo 1 — abra URL tal" (humano fazia)
- ✅ Adicionado: sub-agente `qa-ui-tandem` que faz via Tandem Browser MCP
- ❌ Removido: "o comandante OPERA o produto, não lê relatório"
- ✅ Adicionado: "sub-agente QA opera autonomamente e retorna relatório estruturado"
- ❌ Removido: modo manual como padrão
- ✅ Adicionado: modo automatico como padrão v6.1+; manual só sob comando explícito

---

## Se o sub-agente QA reportar FAIL

CRONOS recebe o diagnóstico e:
1. Decide se é fix trivial (1 tentativa de auto-correção via dispatch ao agente executor responsável)
2. Se fix não-trivial: cria tarefa no kanban com tag `[SELO-FAIL]` e bloqueia avanço de fase
3. Notifica o comandante via painel: "Sub-agente QA encontrou [problema]. Tarefa criada no kanban."
4. Continua trabalhando em paralelo nas fases que não dependem da bloqueada

Humano é notificado, mas **não é** o executor da correção — quem corrige é o agente de execução correspondente, via auto-dispatch.

---

## Compatibilidade com modo manual legado

Em projeto que ainda exige `.delta-11/.modo-selo = manual`, o template v5.2 original (com roteiro para humano) é restaurado. O comando do comandante é:

```
echo "manual" > .delta-11/.modo-selo
```

E o sub-agente QA é substituído pelo roteiro humano tradicional. Mas isso é **opt-in** — v6.1+ default é automatico.
