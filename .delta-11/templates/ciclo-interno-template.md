# TEMPLATE — Ciclo Interno de 7 Sub-Etapas (parametrizado por fase)

> **O que é:** este template é usado pelo CRONOS (ao gerar mini-planos) ou por QUALQUER agente (ao executar uma fase) para garantir que as 7 sub-etapas da Metodologia Gênesis são cumpridas.
>
> **Quem usa:** CRONOS ao gerar `.delta-11/planos/[AGENTE]-plan.md` (o mini-plano tem a seção "Checklist do ciclo interno", derivada deste guia); agente executor segue-o durante a fase.
>
> **Como ler este guia (v6.3):** cada sub-etapa diz a pergunta, o que escrever e **em qual seção do mini-plano**
> isso entra. O mini-plano (`templates/mini-plano-agente-template.md`, D17) tem 6 seções: 1 Objetivo da onda ·
> 2 Recorte da fase anterior · 3 Tarefas · 4 Critérios de aceite · 5 Limites de escopo · 6 Convenções — mais o
> checklist das 7 sub-etapas. Os blocos abaixo NÃO são seções novas: são o conteúdo que vai nas seções 1–6.
>
> **Quando usar:** toda fase, toda mini-tarefa. Para tarefas triviais, use a versão reduzida no final deste template.
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → "O Ciclo Interno de 7 Sub-Etapas".
> **Protocolo formal:** `.delta-11/protocolos/ciclo-interno-7d.md`.

---

## Cabeçalho da fase

```markdown
# Mini-plano — {{AGENTE}} | Fase {{NUMERO_FASE}} | Onda {{N}}
Tipo de tarefa: {{funcionalidade|correcao-de-bug|performance|seguranca|refatoracao}}

**Data:** {{AAAA-MM-DD}}
**Autor:** {{NOME}}
**Fase D-11:** {{NUMERO}} ({{NOME_FASE}}) — {{correspondencia_dia_metodologia}}
**Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia {{N}}
```

---

## Sub-etapa 1 — Planejamento (baseado na fase anterior selada)

**Pergunta:** O que a fase anterior deixou pronto que eu construo em cima?

**→ Vai nas seções 1 (Objetivo da onda) e 2 (Recorte da fase anterior) do mini-plano.**

```markdown
## 1. Objetivo da onda
[Descrição funcional do entregável esperado — o QUE, não COMO. 3-5 frases.]

## 2. Recorte da fase anterior
**Produto que você recebe:** [Fonte: memoria/[AGENTE-ANTERIOR]-produto.md#o-que-existe-agora]
```

**Entregável esperado:** descrição em 3-5 frases; referência ao Selo anterior explícita.

---

## Sub-etapa 2 — Delegação com contexto isolado

**Pergunta:** O que o executor NÃO precisa saber?

**→ Vai nas seções 2 (fatias permitidas + recorte) e 5 (Limites de escopo) do mini-plano.**

```markdown
## 2. Recorte da fase anterior
**Fatias do project-core que você lê (D6):** [contratos.md | banco.md | visual.md | decisoes-tecnicas.md]
[APENAS o que afeta este agente. Cada afirmação técnica com [Fonte: arquivo#seção].]

**O que NÃO precisa saber:**
- [item 1 — contexto que não afeta este agente]
- [item 2 — decisão de outra fase]

## 5. Limites de escopo (OBRIGATÓRIO)
**O que está EXPLICITAMENTE FORA do escopo desta onda:**
- [item 1]
- [item 2]
```

**Entregável esperado:** recorte focado + limites explícitos. Sem limite, o agente pode "ajudar" antecipando outras fases.

---

## Sub-etapa 3 — Execução paralela

**Pergunta:** Quem roda em paralelo comigo? O que posso fazer já?

**→ Vai na seção 3 (Tarefas) do mini-plano.**

```markdown
## 3. Tarefas
| ID | O que fazer | Arquivos | Depende de | Desbloqueia |
|----|-------------|----------|------------|-------------|
| {{T-NNN}} | {{TAREFA}} | {{PATHS}} | {{DEPENDENCIA}} | {{QUEM_ESPERA}} |

**Paralelismo:** {{AGENTES-QUE-RODAM-JUNTO}}
**Quem dispara:** sempre o CRONOS (D5) — `Agent tool` com `run_in_background: true` e `isolation: "worktree"` para executores
```

**Entregável esperado:** mapa de paralelismo. Se fase é single-ator, escreva "(fase é 1 agente, paralelismo não se aplica)".

---

## Sub-etapa 4 — Comunicação entre executores

**Pergunta:** O que descobri que afeta quem está paralelo a mim?

**→ Vai na seção 3 (Tarefas — "Avise o CRONOS se descobrir") do mini-plano.**

```markdown
**Avise por SendMessage ao CRONOS se descobrir:**
- {{TEMA}} que afeta {{AGENTE-X}} → o CRONOS repassa (executores não disparam outros agentes — D5)

**O CRONOS te avisa sobre:**
- {{TEMA}} vindo de {{AGENTE-Y}}

**Tópicos prováveis:**
- Schema mismatch descoberto em runtime
- Decisão ambígua que precisa alinhamento
- Mudança de escopo identificada durante execução
```

**Entregável esperado:** mapa de comunicação explícito. Mensagens são aviso; o registro fica nos arquivos (`-produto.md`, kanban escrito pelo CRONOS — D18). Em fase single-ator, escreva "N/A — sem paralelismo nesta fase".

---

## Sub-etapa 5 — Revisão cruzada externa

**Pergunta:** Quem de fora pode olhar isso sem ter construído?

**→ Vai no checklist do ciclo interno (linha 5) do mini-plano.**

```markdown
- **SHIELD** — revisão de toda tarefa de executor (Passo 3.8, pedida ao CRONOS por SendMessage)
- **Code Architect** — disparado pelo CRONOS ao final da Fase 4
- **SCOUT** — varredura completa ao final da Fase 4
- **Fresh Reviewer → Cold Start Tester → qa-ui-tandem (Selo Experiencial)** — fim de cada fase, pelo CRONOS
- **Comandante** — só decisões de negócio/escopo (D4) e, no `modo manual`, o selo da fase

**Quem NÃO pode revisar:**
- O próprio agente que escreveu
- Outro agente da MESMA onda (mesma fase, mesmo contexto)
```

**Entregável esperado:** quem revisa, em que momento. Em fase sem revisão, escreva "Fase sem agente externo — selagem fica com selador da fase".

---

## Sub-etapa 6 — Teste adversarial

**Pergunta:** O que pode quebrar aqui que o autor não previu?

**→ Vai na seção 4 (Critérios de aceite) e no checklist (linha 6) do mini-plano.**

```markdown
**Cadeia obrigatória por tarefa:**
- `build-validator` (Passo 3.5)
- `contract-tester` — gera E roda os testes de contrato do que mudou (Passo 3.7)
**Cadeia de fase:**
- `code-architect` e `SCOUT` (final da Fase 4)
- `fresh-reviewer` → `cold-start-tester` → `qa-ui-tandem` (fim de cada fase)
- `verify-app` (antes de deploy)

**Cenários adversariais que o teste deve cobrir:**
- [ ] Caminho feliz do usuário
- [ ] Inputs maliciosos (XSS, SQLi, injection)
- [ ] Carga extrema (1000 req/s, race conditions)
- [ ] Falha de dependência externa (API cai no meio)
- [ ] Estado inconsistente (usuário deslogado mid-flow)
- [ ] Permissões (user sem role, role sem permissão)
```

**Entregável esperado:** lista de cenários cobertos + sub-agentes disparados.

---

## Sub-etapa 7 — Selagem por critérios objetivos

**Pergunta:** O que prova que esta fase está pronta, verificável por máquina?

**→ Vai na seção 4 (Critérios de aceite) do mini-plano.**

```markdown
## 4. Critérios de aceite

- [ ] {{CRITERIO-1}} — verificável por: {{COMO-VERIFICAR}}
- [ ] {{CRITERIO-2}} — verificável por: {{COMO-VERIFICAR}}
- [ ] {{CRITERIO-3}} — verificável por: {{COMO-VERIFICAR}}

**Quem sela:** {{NOME}} (papel: {{PAPEL}})
**Quem valida retroativamente (quando aplicável):** {{NOME}}

**Evidência exigida:**
- {{TIPO-EVIDENCIA-1}} (link para log / screenshot / hash)
- {{TIPO-EVIDENCIA-2}}
```

**Entregável esperado:** checklist verificável com responsável explícito.

---

## Resumo da fase (opcional — vai na seção 1 do mini-plano, se usado)

```markdown

**Critérios de sucesso:**
1. {{CS-1}}
2. {{CS-2}}
3. {{CS-3}}

**Risco principal:** {{RISCO}}
**Mitigação:** {{MITIGACAO}}

**Próxima fase / desbloqueia:** {{NOME_PROXIMA_FASE}}
```

---

## Versão reduzida — para tarefas triviais

Para tarefas pequenas (atualizar README, corrigir typo, ajustar versão), use só 3 sub-etapas:

```markdown
# {{TAREFA}}

**Data:** {{AAAA-MM-DD}}

## 1. Planejamento
[1 frase: o que vou fazer]

## 3. Execução
[Ação concreta executada]

## 7. Selagem
- [ ] Alteração commitada
- [ ] Teste passa (se aplicável)
```

NÃO usar esta versão reduzida para tarefas de Fase 4 (desenvolvimento de funcionalidade), Fase 4.5 (consciência), Fase 7 (descanso), ou qualquer tarefa que toque banco/contrato.

---

## Integração com mini-plano-agente-template.md

| Sub-etapa | Seção do mini-plano (`planos/[AGENTE]-plan.md`) |
|---|---|
| 1 Planejamento | 1 Objetivo da onda + 2 Recorte (cita o `-produto.md` anterior) |
| 2 Delegação | 2 Recorte (fatias permitidas, "o que NÃO precisa saber") + 5 Limites de escopo |
| 3 Execução paralela | 3 Tarefas (paralelismo) |
| 4 Comunicação | 3 Tarefas ("avise o CRONOS se descobrir") |
| 5 Revisão cruzada | Checklist do ciclo interno, linha 5 |
| 6 Teste adversarial | 4 Critérios de aceite + checklist, linha 6 |
| 7 Selagem | 4 Critérios de aceite (cada um com evidência) |

Desde a v6.3 o mini-plano traz a seção "Checklist do ciclo interno" com as 7 linhas acima — a integração está
feita no próprio modelo, não depende de o CRONOS lembrar.

---

**Versão do template:** v6.3 (2026-10-14) — antes v6.0.0 (2026-07-12)
**Local canônico:** `.delta-11/templates/ciclo-interno-template.md`
**Proveniência:** criado na Etapa 8B do plano Nível 3 Profundo (auditoria 2026-07-10)