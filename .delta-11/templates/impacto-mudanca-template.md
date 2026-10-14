# Impacto da mudança em project-core.md

> **Template v6.3 (2026-10-14) — Artefato do sub-agente impact-mapper.**
> Gerado quando o CRONOS dispara o impact-mapper (só a pedido — D31), depois que o ATLAS terminou de mudar o
> contrato. Nenhum vigia dispara o impact-mapper.
> Salvo em `.delta-11/memoria/impacto-mudanca-[YYYYMMDDTHHMMSSZ].md`.
> O impact-mapper preenche e PROPÕE tarefas; o CRONOS revisa, decide e é o único que cria tarefas no kanban
> (D10). NUNCA editado à mão.

**Timestamp:** [ISO 8601]
**Gerado por:** impact-mapper (sub-agente Δ-11)
**Método do diff:** [git diff / comparação com backup / não-disponível]

## Resumo executivo

- **Mudanças detectadas:** [N]
- **Arquivos afetados:** [N]
- **Tarefas do kanban invalidadas:** [N]
- **Agentes notificados:** [lista ou "nenhum ativo"]

## Mudanças classificadas

### [N]. [Categoria — ex: Rota alterada] [identificador — ex: POST /api/auth/register]

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

## Tarefas propostas (aguardam aprovação do CRONOS — NÃO estão no kanban)

[Uma proposta `[IMPACTO-MUDANCA]` por correção, cada uma com `resumo_humano` para o painel. O número T-NNN é dado
pelo CRONOS quando ele aprovar e criar a tarefa:]

- [IMPACTO-MUDANCA] [AGENTE]: [descrição] — resumo_humano: [1 frase leiga]

## Próximos passos do CRONOS

1. Revisar este relatório e aprovar/ajustar as tarefas propostas
2. Criar no kanban as tarefas aprovadas (só o CRONOS escreve `kanban.md` e `kanban-data.js`)
3. Decidir se alguma exige disparar o ATLAS (mudança estrutural grande)
4. Disparar agentes com as novas tarefas seguindo o sequenciamento
5. Confirmar que agentes ativos leram `ativacoes/contrato-alterado-[AGENTE].txt`
