# Rodada de Golden Baselines — 2026-07-10 (v5.3-baseline)

**Data:** 2026-07-10
**Versão do Δ-11:** v5.3-baseline
**Tarefas canônicas previstas:** 3
**Rubrica:** rubrica-de-avaliacao.md

## Estrutura

| Agente | Tarefa | Status | Nota |
|--------|--------|--------|------|
| ENGINE | engine-rota-de-pedidos | ⏳ pendente | — |
| PIXEL | pixel-tela-de-lista-de-produtos | ⏳ pendente | — |
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
