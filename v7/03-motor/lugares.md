# Onde fica cada coisa na pasta do produto — a fonte da trava

> `ferramentas/montar-agentes.py` lê esta tabela e monta, a partir dela, o trecho "Onde você escreve e lê" de cada agente e o mapa da trava (`agentes/lugares.json`). Edite aqui; nunca nos agentes.

Como ler: `<X>` é a pasta da camada ou do pedido (`camada-3`, `pedido-12`); `<nome>` é o nome do agente; `<n>` é um número. A primeira linha que bate com o arquivo decide. **Escreve:** os nomes dos agentes; `o dono da linha` (só a própria); `todos`; `todos, só arquivo novo` (cria, nunca reescreve o de outro); `ninguém`; `os Construtores do território` (só nas pastas do seu território, em `.delta-11/regras/enderecos.txt`; arquivo fora de todo território é do BACK; sem esse arquivo, qualquer Construtor no código); `os Construtores sem territórios` (qualquer Construtor, só sem esse arquivo: o caminho pequeno, com um Construtor só, que escreve todo o código, testes e `esteira-comandos.txt` inclusive). **Lê:** `todos`, `todos menos ...` ou `só ...`. Quem só lê numa pasta (o `leitor-do-teste`) está na tabela dos agentes.

| lugar | o que é | escreve | lê |
|---|---|---|---|
| `.delta-11/luz.md` | a Luz do produto | atlas | todos menos revisor |
| `.delta-11/luz-compacta.md` | a Luz compacta | documentador | todos menos revisor |
| `.delta-11/regras/enderecos.txt` | a pasta de cada território, uma por linha: `<nome> <pasta>/` | arquiteto | todos |
| `.delta-11/regras/` | as regras do produto (Camada 2) | arquiteto | todos menos revisor |
| `.delta-11/estado/` | o arquivo de estado de cada camada selada (`camada-<N>.md`) | documentador | todos menos revisor |
| `.delta-11/licoes.md` | as lições do produto | documentador | todos menos revisor, destruidor |
| `.delta-11/quadro/<X>/abertura.md` | o critério da camada e o decidido não fazer | arquiteto | todos menos revisor |
| `.delta-11/quadro/<X>/inimigos.md` | os inimigos da camada, um de cada tipo (na Camada 3, também o componente mais crítico) | cronos | todos menos revisor |
| `.delta-11/quadro/<X>/linhas/<nome>-<n>.md` | a linha de cada agente: o sinal de vida, o aviso de produto, os avisos, o relato | o dono da linha | todos menos revisor, destruidor |
| `.delta-11/quadro/<X>/selo.md` | a decisão do Selador | selador | todos menos revisor, destruidor |
| `.delta-11/quadro/<X>/escolha.md` | a candidata do coração que o Selador escolheu (Camada 3), e por quê | selador | todos menos revisor, destruidor |
| `.delta-11/quadro/<X>/candidatas/` | as linhas das candidatas, trazidas das cópias pela esteira antes de apagá-las (`<cópia>-<nome>-<n>.md`) | ninguém | todos menos revisor, destruidor |
| `.delta-11/quadro/<X>/` | o quadro (`quadro.md`: briefs, quem faz, dependências, avisos, descobertas, devolvidos, substituídos) e os briefs (`briefs/`) | cronos | todos menos revisor, destruidor |
| `.delta-11/teste-guardado/` | o teste das Camadas 1 e 2, um arquivo por Destruidor (`<X>-destruidor-<n>.md`) | destruidor | só destruidor, selador |
| `.delta-11/leitor/` | o que o teste deixa o agente novo ler, numa pasta nova por teste (`<X>-<n>/`), e `atual.txt`, com o nome da pasta do teste em curso | selador | só selador |
| `.delta-11/cofre/` | os segredos que o dono entrega (fica fora do git) | atlas | só atlas, back |
| `.delta-11/registro/para-o-delta-11/` | o que o produto ensina sobre o Delta-11, um arquivo por achado (quem mantém o Delta-11 recolhe) | todos, só arquivo novo | todos |
| `.delta-11/registro/` | a história do projeto, um arquivo novo por registro | todos, só arquivo novo | só documentador |
| `.delta-11/pausa.md` | o Pausar do dono: com `Situação: pausado`, a trava para todo mundo menos o ATLAS e o SCOUT, que mantém de pé o que já está no ar (na volta do dono, ele troca a linha por `Situação: retomado` antes de chamar qualquer agente; vale a última linha `Situação:`); cada um só deixa a própria linha em dia, e o CRONOS, o `quadro.md` | atlas | todos |
| `.delta-11/alarmes/` | o aviso que o alarme do produto deixa aqui (uma lei escreve) e, ao lado de cada um, `<aviso>.resolvido`, que o SCOUT escreve depois que a correção entrou e o erro sumiu; aviso reescrito depois dele volta a valer | scout | todos |
| `.delta-11/motor/modelos/testes-do-fruto.md` | o modelo dos testes (o Revisor usa a linha da camada dele) | ninguém | todos |
| `.delta-11/motor/modelos/linha.md` | o modelo da linha de cada agente | ninguém | todos |
| `.delta-11/pedidos-das-leis/` | o que uma lei do produto pede ao ATLAS, fora o alarme (uma lei escreve) e, ao lado, `<pedido>.tratado`, que o ATLAS escreve quando o encaminhou | atlas | todos |
| `.delta-11/motor/` | os outros modelos (com os números), que contam como o produto é feito, e a versão instalada | ninguém | todos menos revisor |
| `.delta-11/tela-liberada.md` | até quando o dono liberou a tela (`até: <AAAA-MM-DD HH:MM>`) | atlas | todos |
| `.delta-11/esteira/` | o relato inteiro de cada entrega e o sinal de cada esteira que roda (`rodando/`); a esteira escreve, fica fora do git | ninguém | todos menos revisor |
| `.delta-11/` | qualquer outro arquivo aqui | ninguém | todos menos revisor |
| `.claude/` | a configuração, os agentes, as travas e as cópias das candidatas (`worktrees/`) | ninguém | todos |
| `CLAUDE.md` | a porta de entrada do produto (a do motor) | ninguém | todos |
| `AGENTS.md` | instruções de outro sistema (ficam fora da conversa) | ninguém | todos |
| `CLAUDE.local.md` | instruções locais de outro sistema | ninguém | todos |
| `.mcp.json` | ferramentas de fora ligadas à pasta | ninguém | todos |
| `.worktreeinclude` | o que vai para as cópias das candidatas (do instalador) | ninguém | todos |
| `.env` | os segredos que a estrutura do cofre gera para o produto rodar aqui (fica fora do git; o terminal e a caixa o leem, porque os testes precisam) | back | só atlas, back |
| `.env.local` | os segredos locais do produto, como o `.env` (fica fora do git; o terminal e a caixa o leem, porque os testes precisam) | back | só atlas, back |
| `.gitignore` | o que fica fora do git; as linhas do Delta-11 não saem | back, scout, os Construtores sem territórios | todos |
| `esteira` | o programa da esteira, do motor (o instalador o põe e o troca; com defeito, é achado para o Delta-11); os comandos do produto ficam em `esteira-comandos.txt`, código do BACK (sem territórios, de qualquer Construtor) | ninguém | todos |
| `.git/` | o histórico do git (só a esteira e os ganchos mexem) | ninguém | todos menos revisor, destruidor |
| `.rascunho/` | os roteiros de ataque e de teste de quem confere, um arquivo novo por roteiro (fora do git; nada do produto os usa) | destruidor, revisor, selador | todos |
| o código do produto | todo o resto da pasta | os Construtores do território, scout | todos |
