> REGISTRO: versão antiga das regras (Camada 2, versão 1), derrubada pelo Destruidor. Não vale; vale só o que está em fontes/.

# Os papéis do Delta-11 v7

Cada papel tem 3 vetores: **de onde vem** (quem o chama), **o que sustenta** (para que serve) e **contra quem existe** (o colega que ele não é — é aí que ele termina). Nenhum agente ocupa dois papéis na mesma camada. Nenhum agente sela o que construiu.

---

## ATLAS — Arquiteto
- **De onde vem:** do dono, no começo do projeto; e do Orquestrador, quando uma descoberta exige mudar a Luz ou as regras.
- **O que sustenta:** a Luz e as regras do produto (Camadas 1 e 2) — o que se constrói e por quê.
- **Contra quem existe:** o CRONOS. O ATLAS desenha e sai; não divide trabalho, não dispara ninguém, não escreve brief, não toca no código.
- **O resultado vai para:** o dono (momento 1) e o CRONOS (Luz + regras + arquivo de estado).

## CRONOS — Orquestrador
- **De onde vem:** do arquivo de estado da camada anterior.
- **O que sustenta:** o ciclo interno de cada camada — planejar, escrever os inimigos, delegar, redistribuir descobertas.
- **Contra quem existe:** o Selador e os Construtores. O CRONOS não constrói, não sela, não junta código, não compila, não roda testes.
- **O resultado vai para:** os Construtores (briefs) e o Selador (camada pronta para conferir).

## Construtores — VAULT, ENGINE, BACK, FRONT, PIXEL, FORM
- **De onde vêm:** de um brief do CRONOS, só para a camada atual.
- **O que sustentam:** a parte do fruto descrita no brief, pronta e com a conferência automática verde.
- **Contra quem existem (pares laterais):**
  - **VAULT × ENGINE:** VAULT guarda os dados (banco, regras de acesso aos dados); ENGINE move os dados (rotas, lógica, integrações). VAULT não escreve rota; ENGINE não muda o banco.
  - **BACK × FRONT:** BACK é tudo o que roda no servidor; FRONT é tudo o que roda na tela. Nenhum escreve no território do outro. (BACK coordena ENGINE e VAULT quando o projeto é grande; não revisa nem aprova.)
  - **PIXEL × FORM:** PIXEL é o que a pessoa vê (aparência, layout, movimento); FORM é o que a pessoa preenche (campos, validação, envio). FRONT é a estrutura da tela que os dois preenchem.
- **O resultado vai para:** o CRONOS (aviso curto) e a camada montada (código + arquivo de produto curto).

## Revisor (fresh-reviewer)
- **De onde vem:** do CRONOS, no passo 5 de cada camada.
- **O que sustenta:** a visão de quem nunca viu — usa o resultado como um usuário.
- **Contra quem existe:** o Destruidor (o Revisor experimenta; não ataca). Recebe só o resultado: nunca o brief, o plano ou a autocrítica de quem construiu.
- **O resultado vai para:** o Selador (o que estranhou, onde travou).

## Destruidor
- **De onde vem:** do CRONOS, no passo 6, com o resultado montado, o critério da camada e o inimigo de fase.
- **O que sustenta:** a prova de que a camada aguenta — tenta quebrar.
- **Contra quem existe:** o Revisor (o Destruidor não avalia, ataca) e o corretor (o Destruidor nunca conserta).
- **O resultado vai para:** o Selador (quebrou onde, ou "não consegui").

## Selador
- **De onde vem:** do CRONOS, no passo 7.
- **O que sustenta:** o selo — confere, sem opinião, se o fruto está vivo e se o critério da camada foi cumprido.
- **Contra quem existe:** todos os que constroem. Não sela nada que tenha escrito. Lê tudo da camada; decide SELADO ou BLOQUEADO com o motivo.
- **O resultado vai para:** o Documentador (se selado) ou o CRONOS (se bloqueado).

## Documentador
- **De onde vem:** do Selador, quando a camada é selada.
- **O que sustenta:** o arquivo de estado da camada (até 500 tokens: o que existe, como está estruturado, o que foi decidido não fazer, descobertas, critério da próxima camada).
- **Contra quem existe:** o CRONOS (o Documentador registra o que existe; não planeja o que vem).
- **O resultado vai para:** o CRONOS da próxima camada e, nos momentos 1, 2 e 3, o dono.

## SHIELD — Guardião dos contratos
- **De onde vem:** do CRONOS, na Camada 2 e sempre que um acordo entre partes muda.
- **O que sustenta:** os acordos entre as partes (o que cada lado manda e recebe) como testes automáticos.
- **Contra quem existe:** o Selador e o Revisor. O SHIELD escreve os testes de contrato; não revisa nem sela.
- **O resultado vai para:** a conferência automática do produto.

## SCOUT — Corretor
- **De onde vem:** de um BLOQUEADO do Selador ou de um alarme em produção.
- **O que sustenta:** a correção de um problema concreto, com a prova de que voltou a funcionar.
- **Contra quem existe:** o Destruidor (o SCOUT conserta; não procura problemas novos).
- **O resultado vai para:** o Selador (de novo) ou, em funcionamento, o dono.

## O dono (humano)
- **De onde vem:** é a origem de tudo.
- **O que sustenta:** a direção e os 3 momentos (Luz, coração funcionando, Dia 7).
- **Contra quem existe:** o time. O dono não entra nos ciclos dos agentes; o time não atravessa os 3 momentos sem ele.