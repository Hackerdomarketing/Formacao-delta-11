# Golden Baselines — Testes Canônicos dos Agentes Δ-11

**O que é:** um conjunto de tarefas-padrão ("canônicas") com gabarito de avaliação, para medir se uma mudança no sistema Δ-11 (operativo, base de conhecimento, protocolo, CLAUDE.md) melhorou ou PIOROU a qualidade do output dos agentes. É o teste de regressão DO SISTEMA, não dos projetos.

**Por que existe:** o comandante testa versões do Δ-11 comparativamente. Sem gabarito fixo, a comparação é "olhômetro". Com golden baselines, cada versão executa as MESMAS tarefas e é avaliada pela MESMA rubrica — a regressão de qualidade vira número.

**Este diretório NÃO é sincronizado para os projetos** — é ferramenta do repositório de distribuição.

## Estrutura

```
golden-baselines/
├── README.md                      ← este arquivo
├── rubrica-de-avaliacao.md        ← como dar nota (mesma régua para toda execução)
├── tarefas/                       ← as tarefas canônicas (1 arquivo por tarefa)
│   ├── engine-rota-de-pedidos.md
│   ├── pixel-tela-de-lista-de-produtos.md
│   └── vault-esquema-de-assinaturas.md
└── execucoes/                     ← resultados datados (criados a cada rodada)
    └── AAAA-MM-DD-vX.X-[agente]-[tarefa]/   ← código gerado + nota preenchida
```

## Como rodar uma rodada de comparação (protocolo do comandante)

1. **Prepare um projeto de teste descartável** (ex: `testando-versoes-delta-11-c`) com a versão do Δ-11 que quer medir instalada.
2. **Para cada tarefa canônica:** abra uma janela nova do agente correspondente e cole o bloco de ativação que está no arquivo da tarefa (ele simula o mini-plano que o CRONOS geraria).
3. **Deixe o agente executar até o fim** (incluindo a cadeia autocrítica → build-validator → contract-tester).
4. **Copie o resultado** para `execucoes/AAAA-MM-DD-vX.X-[agente]-[tarefa]/` (código gerado + arquivo de autocrítica + relatórios).
5. **Avalie com a rubrica** (`rubrica-de-avaliacao.md`) — pode pedir a uma sessão LIMPA do Claude: "avalie esta execução contra este gabarito e esta rubrica" (avaliador nunca é a mesma sessão que gerou).
6. **Compare com a execução anterior** da mesma tarefa: nota subiu, manteve ou caiu → decisão sobre a mudança de versão.

## Regras

- **Nunca altere uma tarefa canônica depois de usada em comparação** — mudou a tarefa, zera o histórico dela (crie tarefa nova em vez de editar).
- **Avaliador ≠ gerador:** quem dá nota nunca é a sessão que produziu o código (princípio executor ≠ quality gate).
- **Mínimo 2 execuções por versão** quando o resultado for decisivo (variância de LLM existe; uma execução é anedota).
- **Adicionar golden novo:** copie o formato de uma tarefa existente — tarefa realista, pequena o bastante para caber em 1 janela, com gabarito por CHECKLIST (não por código exato: existem várias implementações corretas).
