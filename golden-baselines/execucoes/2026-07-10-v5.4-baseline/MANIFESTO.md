# Rodada de Golden Baselines — 2026-07-10 (v5.4-baseline)

**Data:** 2026-07-10
**Versão do Δ-11:** v5.4-baseline
**Tarefas canônicas previstas:** 10
**Rubrica:** rubrica-de-avaliacao.md

## Estrutura

| Agente | Tarefa | Status | Nota |
|--------|--------|--------|------|
| ATLAS | atlas-fase-zero-descoberta | ⏳ pendente | — |
| BACK | back-revisao-pr-com-armadilhas | ⏳ pendente | — |
| CRONOS | cronos-sequenciamento-onda-3-agentes | ⏳ pendente | — |
| ENGINE | engine-rota-de-pedidos | ⏳ pendente | — |
| FORM | form-wizard-multi-step-com-upload | ⏳ pendente | — |
| FRONT | front-layout-e-design-system | ⏳ pendente | — |
| PIXEL | pixel-tela-de-lista-de-produtos | ⏳ pendente | — |
| SCOUT | scout-diagnostico-rls-silencioso | ⏳ pendente | — |
| SHIELD | shield-revisao-contratos-com-armadilhas | ⏳ pendente | — |
| VAULT | vault-esquema-de-assinaturas | ⏳ pendente | — |

## Próximos passos (protocolo do comandante)

1. Abra uma janela do Claude Code por agente da coluna "Agente" acima.
2. Cole o conteúdo de `prompt-de-ativacao.txt` correspondente.
3. Aguarde o agente executar até o fim (autocrítica → build-validator → contract-tester).
4. Copie o resultado (código + logs) para este subdiretório.
5. Avalie com a rubrica em sessão limpa separada.
6. Atualize a coluna "Nota" no MANIFESTO acima.

## Comparação com execuções anteriores

Compare esta rodada com a imediatamente anterior em `execucoes/`:
- Se TODAS as notas subiram → a mudança do Δ-11 foi benéfica.
- Se ALGUMA nota caiu mais que 5 pontos → regressão; investigar antes de propagar.
