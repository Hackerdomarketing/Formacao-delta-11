# TEMPLATE — Bug Report

**O que é:** relato padronizado de um erro — o que era esperado, o que aconteceu, como reproduzir, evidência. Transforma "tá quebrado" em algo que o SCOUT diagnostica sem caçar às cegas.

**Onde salvar:** `.delta-11/bugs/BUG-NNN-titulo-curto.md` (numeração sequencial: BUG-001, BUG-002…)

**Quem escreve:**
- **SHIELD** — ao REPROVAR uma tarefa em revisão (toda reprovação com defeito funcional gera bug report; a tarefa de correção no kanban referencia o BUG-NNN)
- **CRONOS** — quando o fresh-reviewer ou o comandante relatam problema (CRONOS formaliza antes de despachar SCOUT)
- **Qualquer agente** — que encontrar erro fora do próprio escopo

**Quem consome:** **SCOUT** — o modo reativo dele COMEÇA lendo o bug report (passo "Reproduzir" já vem pronto). Se o projeto tem Sentry, colar o link/stack trace do evento na seção Evidência.

---

```markdown
# BUG-NNN: [título em 1 linha — sintoma, não causa]

- **Data:** AAAA-MM-DD
- **Relatado por:** [agente ou comandante]
- **Severidade:** 1-Crítico (sistema parado) | 2-Alto (funcionalidade crítica quebrada) | 3-Médio (funcionalidade secundária) | 4-Baixo
- **Status:** aberto | em diagnóstico (SCOUT) | corrigido (T-XXX) | não reproduzível
- **Tarefa de correção:** T-XXX (quando criada no kanban)

## Comportamento esperado

[1-2 frases: o que DEVERIA acontecer. Cite o contrato se houver: `[Fonte: contratos-api.md#rota]`]

## Comportamento real

[1-2 frases: o que ESTÁ acontecendo]

## Passos para reproduzir

1. [passo exato — URL, botão, dado de entrada]
2. [passo]
3. [resultado errado aparece]

## Evidência

- [stack trace, print em `.delta-11/evidencias/screenshots/AAAA-MM-DD/`, log, ou link do evento no Sentry]

## Contexto adicional

- **Ambiente:** dev | produção · **Navegador/dispositivo:** [se relevante]
- **Começou quando:** [commit/tarefa suspeita, se souber — NÃO chutar causa]
```

**Regra de ouro:** o report descreve o SINTOMA com precisão; a CAUSA é trabalho do SCOUT. Report que já "diagnostica" sem evidência contamina a investigação.
