# TEMPLATE — Ciclo Interno de 7 Sub-Etapas (parametrizado por fase)

> **O que é:** este template é usado pelo CRONOS (ao gerar mini-planos) ou por QUALQUER agente (ao executar uma fase) para garantir que as 7 sub-etapas da Metodologia Gênesis são cumpridas.
>
> **Quem usa:** CRONOS ao gerar `.delta-11/planos/[AGENTE]-plan.md` (integra este template); agente executor segue-o durante a fase.
>
> **Quando usar:** toda fase, toda mini-tarefa. Para tarefas triviais, use a versão reduzida no final deste template.
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → "O Ciclo Interno de 7 Sub-Etapas".
> **Protocolo formal:** `.delta-11/protocolos/ciclo-interno-7d.md`.

---

## Cabeçalho da fase

```markdown
# Mini-plano — {{FASE_OU_AGENTE}} {{NUMERO_FASE}}
# Tipo de tarefa: {{funcionalidade|correcao-de-bug|performance|seguranca|refatoracao|outro}}

**Data:** {{AAAA-MM-DD}}
**Autor:** {{NOME}}
**Fase D-11:** {{NUMERO}} ({{NOME_FASE}}) — {{correspondencia_dia_metodologia}}
**Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia {{N}}
```

---

## Sub-etapa 1 — Planejamento (baseado na fase anterior selada)

**Pergunta:** O que a fase anterior deixou pronto que eu construo em cima?

```markdown
## 1. O que esta tarefa precisa produzir

[Descrição funcional do entregável esperado — o QUE, não COMO. 3-5 frases.]

**Fase anterior (Selo):**
[Cite o `[AGENTE-ANTERIOR]-produto.md` ou equivalente. Use a etiqueta [Fonte: arquivo#seção]]
```

**Entregável esperado:** descrição em 3-5 frases; referência ao Selo anterior explícita.

---

## Sub-etapa 2 — Delegação com contexto isolado

**Pergunta:** O que o executor NÃO precisa saber?

```markdown
## 2. Recorte relevante da fase anterior

[APENAS o que afeta este agente. NÃO o projeto inteiro. Cada afirmação técnica com [Fonte: arquivo#seção].]

**O que NÃO precisa saber:**
- [item 1 — contexto que não afeta este agente]
- [item 2 — decisão de outra fase]

**Limites de Escopo (v4.0.3 — OBRIGATÓRIO):**
**O que está EXPLICITAMENTE FORA do escopo desta tarefa:**
- [item 1]
- [item 2]
- [etc]
```

**Entregável esperado:** recorte focado + limites explícitos. Sem limite, o agente pode "ajudar" antecipando outras fases.

---

## Sub-etapa 3 — Execução paralela

**Pergunta:** Quem roda em paralelo comigo? O que posso fazer já?

```markdown
## 3. Quem executa (paralelo onde possível)

| Agente | Tarefa | Pode rodar em paralelo com |
|--------|--------|-----------------------------|
| {{AGENTE-1}} | {{TAREFA-1}} | {{OUTROS-AGENTES-PARALELOS}} |
| {{AGENTE-2}} | {{TAREFA-2}} | {{OUTROS-AGENTES-PARALELOS}} |

**Quem dispara:** {{CRONOS ou outro}}
**Como:** `Agent tool` com `run_in_background: true`, `isolation: worktree`
```

**Entregável esperado:** mapa de paralelismo. Se fase é single-ator, escreva "(fase é 1 agente, paralelismo não se aplica)".

---

## Sub-etapa 4 — Comunicação entre executores

**Pergunta:** O que descobri que afeta quem está paralelo a mim?

```markdown
## 4. Comunicação esperada durante execução

**Quem devo avisar se descobrir:**
- {{AGENTE-X}} sobre {{TEMA}} → use `SendMessage`

**Quem me avisa sobre:**
- {{AGENTE-Y}} sobre {{TEMA}} → receber `SendMessage`

**Tópicos prováveis:**
- Schema mismatch descoberto em runtime
- Decisão ambígua que precisa alinhamento
- Mudança de escopo identificada durante execução
```

**Entregável esperado:** mapa de comunicação explícito. Em fase single-ator, escreva "N/A — sem paralelismo nesta fase".

---

## Sub-etapa 5 — Revisão cruzada externa

**Pergunta:** Quem de fora pode olhar isso sem ter construído?

```markdown
## 5. Quem revisa

- **Code Architect** — disparado por CRONOS ao final da Fase 4
- **SHIELD** — revisão contínua durante Fase 4 (por tarefa)
- **SCOUT** — varredura completa ao final da Fase 4
- **Comandante** — validações críticas (ex: LGPD em Fase 4.5)

**Quem NÃO pode revisar:**
- O próprio agente que escreveu
- Outro agente da MESMA onda (mesma fase, mesmo contexto)
```

**Entregável esperado:** quem revisa, em que momento. Em fase sem revisão, escreva "Fase sem agente externo — selagem fica com selador da fase".

---

## Sub-etapa 6 — Teste adversarial

**Pergunta:** O que pode quebrar aqui que o autor não previu?

```markdown
## 6. Teste adversarial

**Cadeia obrigatória por tarefa (D-11 v5.0+):**
- `build-validator` (por tarefa após cada edit)
- `contract-tester` (após finalização)
- `code-architect` (ao final da Fase 4)
- `SCOUT` varredura completa (final da Fase 4)
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

```markdown
## 7. Critérios de selagem desta tarefa

- [ ] {{CRITERIO-1}} — verificável por: {{COMO-VERIFICAR}}
- [ ] {{CRITERIO-2}} — verificável por: {{COMO-VERIFICAR}}
- [ ] {{CRITERIO-3}} — verificável por: {{COMO-VERIFICAR}}

**Quem sella:** {{NOME}} (papel: {{PAPEL}})
**Quem valida retroativamente (quando aplicável):** {{NOME}}

**Evidência exigida:**
- {{TIPO-EVIDENCIA-1}} (link para log / screenshot / hash)
- {{TIPO-EVIDENCIA-2}}
```

**Entregável esperado:** checklist verificável com responsável explícito.

---

## Resumo da fase

```markdown
## Resumo

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

O template `.delta-11/templates/mini-plano-agente-template.md` (usado pelo CRONOS para gerar `.delta-11/planos/[AGENTE]-plan.md`) já tem seções relacionadas às sub-etapas 2 e 5 deste protocolo (Delegação e Limites de Escopo). Está alinhado.

A partir do v6.0, o mini-plano **integra este protocolo** por padrão — as seções do mini-plano são derivadas deste template.

---

**Versão do template:** v6.0.0 (2026-07-12)
**Local canônico:** `.delta-11/templates/ciclo-interno-template.md`
**Proveniência:** criado na Etapa 8B do plano Nível 3 Profundo (auditoria 2026-07-10)