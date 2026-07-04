# Impacto da mudança em project-core.md

> **Template v5.2 — Artefato do sub-agente impact-mapper.**
> Gerado automaticamente quando o contrato muda (hook PostToolUse → regenerar-contratos.py → impact-mapper).
> Salvo em `.delta-11/memoria/impacto-mudanca-[YYYYMMDDTHHMMSSZ].md`.
> O impact-mapper preenche; o CRONOS revisa e decide. NUNCA editado à mão.

**Timestamp:** [ISO 8601]
**Gerado por:** impact-mapper (sub-agente Δ-11)
**Método do diff:** [git diff / comparação com backup / não-disponível]

## Resumo executivo

- **Mudanças detectadas:** [N]
- **Arquivos afetados:** [N]
- **Tarefas do kanban invalidadas:** [N]
- **Agentes notificados:** [lista ou "nenhum ativo"]

## Mudanças classificadas

### [N]. [Categoria — ex: Rota alterada] [identificador — ex: POST /api/auth/registrar]

**Natureza:** [o que mudou exatamente — ex: campo `password` de min 6 para min 8]
**Risco:** [o que o código existente faz de incompatível agora]

**Arquivos afetados:**
- `[path]` — [papel — implementação/consumidor/teste] ([agente dono])

**Agentes responsáveis:** [lista]

[... repetir por mudança ...]

## Tarefas do kanban invalidadas

| ID | Descrição | Agente | Status atual | Ação recomendada |
|---|---|---|---|---|
| [T-XXX] | [desc] | [AGENTE] | [CONCLUIDO/REVISAO/FAZENDO] | [o que refazer] |

## Tarefas novas criadas automaticamente

[Tarefas com tag `[IMPACTO-MUDANCA]` adicionadas ao kanban — cada uma com `resumo_humano` para o painel:]

- T-[NNN] [IMPACTO-MUDANCA] [AGENTE]: [descrição]

## Próximos passos do CRONOS

1. Revisar este relatório e aprovar/ajustar as tarefas criadas
2. Decidir se alguma exige reativar ATLAS (mudança estrutural grande)
3. Disparar agentes com as novas tarefas seguindo o sequenciamento
4. Confirmar que agentes ativos leram `ativacoes/impacto-[AGENTE].txt`
