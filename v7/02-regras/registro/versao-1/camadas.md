> REGISTRO: versão antiga das regras (Camada 2, versão 1), derrubada pelo Destruidor. Não vale; vale só o que está em fontes/.

# As 7 camadas de todo produto (Delta-11 v7)

**Regra-mãe:** uma camada só está selada quando o **fruto** dela está **vivo** — funciona e se sustenta sozinho. Documento escrito não é fruto. Tarefa concluída não é fruto.

| Camada | Fruto (o que precisa estar vivo) | Teste do fruto | Quem sela |
|---|---|---|---|
| 1. Luz | Orientação: qualquer agente, lendo só a Luz, sabe se o que fez serve | O dono diz "é exatamente isso" | Humano (momento 1) |
| 2. Regras | Coesão: um agente novo cria algo que pertence ao sistema lendo só as regras | Agente novo cria uma peça coerente; o Destruidor tenta criar uma incoerente seguindo as regras e não consegue | Selador |
| 3. Coração | O fluxo principal funciona de ponta a ponta sem intervenção (entrada → processamento → saída) | O dono usa com as mãos e diz "entrega valor"; o Destruidor atacou o fluxo e não quebrou; a arquitetura da Camada 2 aguentou | Humano (momento 2) |
| 4. Ritmo | O produto sabe se está saudável sem ninguém olhar | Uma falha provocada de propósito dispara um alarme que chega ao dono; a conferência automática roda a cada mudança | Selador |
| 5. Expansão | As demais funcionalidades vivem sobre o coração sem quebrá-lo | Conferência automática verde; Revisor usa como usuário; Destruidor ataca os caminhos novos; o coração continua funcionando | Selador |
| 6. Consciência | O produto governa quem pode o quê e decide por dados reais | Destruidor tenta contornar as permissões e não consegue; os limites de uso disparam sozinhos | Selador |
| 7. Centro | O automático está ligado: o produto roda sozinho | 2 semanas sem ninguém, medido pela máquina; um pedido pequeno resolvido por um agente em minutos | Humano (momento 3) |

**Ordem:** nenhuma camada começa antes de a anterior estar selada. Exceção única: o selo da Camada 2 é provisório até a Camada 3 provar que a estrutura aguentou (se não aguentou, a Camada 2 é refeita agora, não depois).

## O ciclo interno (uma vez por camada, nunca por tarefa)
1. **Planejar:** o Orquestrador lê o arquivo de estado da camada anterior, a Luz e o critério desta camada; escreve os 4 inimigos da camada; divide o trabalho.
2. **Delegar:** cada Construtor recebe um brief de 2 a 4 páginas (o que produzir, o recorte que lhe cabe, critério, dependências, limites).
3. **Construir em paralelo:** todos na mesma camada, com a mesma meta pequena.
4. **Descobrir e redistribuir:** quem descobre algo avisa o Orquestrador, que ajusta dentro da camada sem reiniciar nada.
5. **Revisar:** o Revisor usa o resultado montado sem saber como foi feito.
6. **Destruir:** o Destruidor ataca o resultado montado, mirando o inimigo de fase.
7. **Selar:** o Selador confere se o fruto está vivo; o Documentador escreve o arquivo de estado; o humano entra só se for momento 1, 2 ou 3.

Entre um passo e outro de uma tarefa, a única conferência é a **automática** (as leis do produto). Nenhum agente revisa tarefa por tarefa.

## Depois não existe
Problema achado numa camada se resolve nessa camada, ou a camada fica **bloqueada**. Não existem "lacuna", "dívida", "ressalva" nem "para o próximo ciclo". A única saída aceita: **"decidido não fazer"**, escrito no arquivo de estado, com o motivo.

## Modo de funcionamento (depois do selo da Camada 7)
Os agentes dormem; as leis do produto trabalham. Cada pedido é tratado pelo tamanho:
- **Pequeno** (texto, cor, ajuste): um Construtor faz; a conferência automática roda; o dono olha.
- **Muda uma camada** (ex.: novo tipo de login): reabre só aquela camada, com o ciclo interno dela, e sela de novo.
- **Erro em produção:** o alarme avisa; um Construtor corrige; a conferência automática roda; o dono olha.
Não se abre um projeto inteiro de novo para mexer num produto pronto.