# GUIA DO COMANDANTE — FORMAÇÃO Δ-11 (v6.3)

Este guia é para você, comandante: a pessoa que diz **o que** quer construir. Você não precisa saber programar.
Tudo aqui está em linguagem simples. Quando aparecer uma palavra técnica, a explicação vem logo depois, entre
colchetes.

---

## 1. O QUE É A FORMAÇÃO Δ-11

A Formação Δ-11 é um time de **10 agentes de inteligência artificial** que constroem um sistema (um site, um
aplicativo, uma ferramenta) do começo ao fim, dentro do **Claude Code** [o programa da Anthropic onde a inteligência
artificial lê e escreve os arquivos do seu projeto — funciona no VS Code ou no Terminal].

O time tem 10 agentes e **1 comandante: você**.

| Agente | Papel, em palavras simples |
|---|---|
| ATLAS | Arquiteto. Conversa com você no começo e desenha o sistema inteiro. |
| CRONOS | Gerente. Divide o trabalho, chama cada agente na hora certa e acompanha tudo. |
| VAULT | Banco de dados [o "arquivo" onde o sistema guarda as informações]. |
| BACK | Servidor [a parte do sistema que roda escondida, recebendo e respondendo pedidos]. |
| ENGINE | Motor: as regras de negócio e as integrações com outros serviços. |
| FRONT | Interface: as telas que o usuário vê. |
| PIXEL | Visual: cores, fontes, espaçamentos, a aparência das telas. |
| FORM | Formulários: os campos que o usuário preenche. |
| SHIELD | Qualidade e segurança: revisa tudo antes de valer. |
| SCOUT | Diagnóstico: quando algo quebra, ele descobre por quê e conserta. |

**Como funciona, em 30 segundos:**

1. Você digita `d11` e descreve o que quer.
2. O ATLAS conversa com você até entender o projeto e mostra o plano para você aprovar.
3. O ATLAS entrega o plano ao CRONOS.
4. O CRONOS chama todos os outros agentes sozinho, na ordem certa, vários ao mesmo tempo.
5. Você acompanha por um **painel** [uma página no navegador que mostra o andamento] que abre sozinho.
6. Você só é chamado quando há uma decisão que só você pode tomar.

Você não precisa decorar o nome de nenhum agente nem chamar nenhum deles. Quem chama é o CRONOS.

---

## 2. O QUE PRECISA ESTAR INSTALADO NO COMPUTADOR

| Programa | Para que serve | Obrigatório? |
|---|---|---|
| Claude Code | é onde os agentes trabalham | sim |
| git | guarda o histórico de cada mudança, como um "desfazer" infinito | sim |
| python3 | roda os **vigias** [pequenos programas que conferem, sozinhos, se os agentes seguem as regras] | sim |
| node | roda alguns vigias e o sistema que os agentes constroem | sim |
| jq | ajuda a ler o registro de projetos; só o comando de atualizar (`sincronizar.sh`) precisa dele | opcional |
| VS Code | editor onde você vê os arquivos do projeto | opcional, mas recomendado |
| gh (GitHub CLI) | guarda uma cópia do sistema no seu GitHub, se você quiser | opcional |

Funciona no **macOS** (completo), no **Linux** e no **Windows** (pelo Git Bash ou pelo WSL [um Linux que roda dentro
do Windows]). O monitor automático que fica de olho nos projetos a cada 5 minutos é só do macOS.

---

## 3. INSTALAR (uma vez só)

**Passo 1: abra o Terminal.**
No Mac, aperte as teclas `Command` e `Espaço` ao mesmo tempo. Vai aparecer uma barra de busca no meio da tela.
Digite `Terminal` e aperte `Enter`. Abre uma tela com fundo branco ou preto e um cursor piscando.

**Passo 2: entre na pasta da Formação Δ-11.**
Digite o comando abaixo (troque o caminho se a sua pasta estiver em outro lugar) e aperte `Enter`:

```bash
cd ~/Documents/VSCODE/Formacao-delta-11
```

Nada de especial aparece: o Terminal só passa a "estar" dentro dessa pasta.

**Passo 3: rode o instalador.**

```bash
bash instalar.sh
```

O instalador mostra 7 etapas, de `[1/7]` a `[7/7]`, com um `✓` verde em cada coisa que deu certo:

1. confere se os programas da seção 2 estão instalados (se faltar algum, ele diz como instalar);
2. confere se os arquivos da Formação estão na pasta;
3. protege suas senhas: garante que arquivos secretos nunca vão para a internet;
4. anota esta pasta como a sua **fonte oficial** [a pasta "mãe", de onde saem as cópias para todos os projetos] e
   cria o arquivo de lições entre projetos;
5. (Mac) pergunta se pode ligar o monitor automático — responda `s` e aperte `Enter`. Se os seus projetos ficam
   nas pastas Documentos ou Downloads, o próprio instalador mostra como liberar o acesso do monitor nos Ajustes do
   Sistema;
6. pergunta se você quer guardar uma cópia privada no seu GitHub — responda `s` ou `n`. Antes de enviar qualquer
   coisa, ele mostra a lista do que vai e pede confirmação;
7. abre o VS Code e o painel.

No fim aparece **"✓ INSTALAÇÃO COMPLETA"**.

---

## 4. CRIAR UM PROJETO NOVO

Para cada sistema que você quiser construir, crie uma pasta de projeto. No Terminal, digite (troque `meu-app` pelo
nome do seu projeto, sem espaços):

```bash
bash ~/Documents/VSCODE/Formacao-delta-11/novo-projeto.sh ~/projetos/meu-app
```

O script copia os arquivos da Formação para a pasta nova, liga os vigias, protege as senhas e anota o projeto no
registro central. O quadro de tarefas e a memória nascem zerados: nada de outro projeto vem junto.

No fim aparece **"✓ Projeto pronto!"** e o próximo passo.

---

## 5. ATIVAR O TIME: `d11`

**Passo 1:** abra a pasta do projeto no VS Code (menu `File` → `Open Folder...` → escolha a pasta `meu-app`).

**Passo 2:** abra o Claude Code. No VS Code, é o ícone do Claude na barra lateral ou no canto superior direito. Abre
um painel com uma caixa de texto embaixo.

**Passo 3:** digite `d11` e, logo depois, descreva o que você quer construir, com o máximo de detalhe:

```
d11

Quero um aplicativo para minha clínica em que o paciente marca consulta pelo celular,
recebe lembrete no WhatsApp e eu vejo a agenda do dia numa tela só.
```

Aperte `Enter`. O que acontece:

- o **painel abre sozinho** no seu navegador (no máximo uma vez a cada 8 horas, para não ficar abrindo de novo);
- o **ATLAS se apresenta** e começa a fazer perguntas sobre o seu projeto.

Se o painel não abrir, abra você mesmo: no Finder, entre na pasta do projeto, depois em `.delta-11` (no Mac, aperte
`Command` + `Shift` + `.` para ver pastas que começam com ponto) e dê dois cliques em `painel.html`.

---

## 6. O QUE VOCÊ FAZ (E O QUE O SISTEMA FAZ SOZINHO)

**Na Fase 0, você trabalha junto com o ATLAS.** Ele pergunta quem é o seu cliente, o que vai deixar o seu produto
diferente, como cada tela deve fazer a pessoa se sentir e qual é a identidade visual. Responda com calma. No fim, ele
mostra o **PRD** [documento de requisitos do produto: o "contrato" que diz o que vai ser construído]. Leia e, se
estiver certo, digite `aprovar`.

**Depois da Fase 0, você só é chamado em 3 situações:**

1. **Decisão de negócio ou de escopo** que só você pode tomar. Exemplo: "o aplicativo vai cobrar assinatura?"
2. **Credencial, conta, pagamento ou CAPTCHA** [aquele teste "não sou um robô"]. Exemplo: criar a conta num serviço
   ou informar uma chave de acesso.
3. **Risco de perder dados ou de publicar algo para o mundo.** Exemplo: colocar o sistema no ar (o "deploy").

Fora disso, o time decide e segue. Ninguém vai te perguntar "posso continuar?".

**Os dois modos de trabalho:**

- **`modo automatico` (o padrão):** quando uma fase termina e todas as revisões ficam verdes, o CRONOS abre a próxima
  sozinho.
- **`modo manual`:** no fim de cada fase, o CRONOS mostra o resultado e espera você digitar `aprovar`. Bom para quem
  quer acompanhar cada passo de perto.

---

## 7. OS COMANDOS

Digite os comandos na mesma conversa do Claude Code onde você digitou `d11`.

| Você digita | O que acontece |
|---|---|
| `status` | O time conta o que está sendo feito agora, quanto falta e qual é o próximo passo. |
| `pausar` | Todo mundo salva onde parou. Use quando precisar parar por um tempo. |
| `retomar` | O time lê onde parou e continua dali. |
| `aprovar` | Você aprova o que foi mostrado (o PRD na Fase 0, o fim de fase no `modo manual`, o deploy). |
| `modo automatico` | Volta ao padrão: as fases avançam sozinhas quando tudo fica verde. |
| `modo manual` | O CRONOS para no fim de cada fase e espera o seu `aprovar`. |
| `aprovar automatico ate fase X` | Avança sozinho até a fase X e, nela, espera o seu `aprovar`. |
| `vigilante` | Mostra os alertas do monitor: agente parado, agente em silêncio, tarefa sem dono. |
| `avançar` | Pede para fechar a tarefa atual e puxar a próxima. |

---

## 8. COMO LER O PAINEL

O painel atualiza sozinho a cada 5 segundos. De cima para baixo:

1. **Topo:** "Δ-11 · Centro de comando" e, à direita, há quanto tempo os dados foram atualizados.
2. **Fase atual e nome do projeto.**
3. **O selo** (um cartão grande com uma palavra): o resumo de tudo. Veja a tabela abaixo.
4. **Progresso da missão:** a porcentagem pronta e quantas tarefas estão feitas, em curso, em revisão e pendentes.
5. **Transmissão do gerente:** a mensagem do CRONOS para você, em 1 a 3 frases. Ela sempre termina dizendo se você é
   necessário ("Nada requer você agora" ou "Preciso de você em...").
6. **Alertas do vigia:** avisos do monitor automático.
7. **Progresso por operativo:** quanto cada agente já fez.
8. **Sinais de vida:** a última vez que cada agente deu sinal.
9. **Operações em curso:** o que cada agente está fazendo, numa frase simples, e o que está **em revisão do Shield**.

Na lateral direita há uma aba **"Operativos"** (ou aperte a tecla `O`): ela abre uma gaveta com os 10 agentes.

### O selo

| Cor do cartão | Palavra | O que quer dizer | O que você faz |
|---|---|---|---|
| Verde | **Seguro fechar** | Todos os agentes com tarefa estão dando sinal. | Nada. Pode fechar o painel e ir fazer outra coisa. |
| Verde | **Descansando** / **Aguardando** | Ninguém está com tarefa agora. | Nada. |
| Amarelo | **Monitoramento parcial** | Um agente tem tarefa aberta, mas o painel não recebe o sinal dele. O painel não consegue confirmar que ele está trabalhando. | Espere uns minutos antes de sair. Se continuar, digite `status`. |
| Vermelho, pulsando devagar | **Agente parou**, **Agente em silêncio**, **Tarefa sem dono**, **Agente sem sinal**, **Tarefa demorando** | Algo pode ter travado. O CRONOS costuma resolver sozinho. | Espere alguns minutos. Se não mudar, veja a seção 10. |
| Vermelho, pulsando devagar | **Precisa de você** | Uma das 3 situações chegou. | Leia a Transmissão do gerente e responda no Claude Code. |
| Vermelho forte, piscando | **Travado** (ou "2 travados") | Uma tarefa está bloqueada esperando uma decisão sua. | Leia o motivo em "Operações em curso" e responda no Claude Code. |

### As cores dos sinais de vida

Cada agente tem uma bolinha:

- **verde:** deu sinal há até 2 minutos;
- **amarela:** deu sinal há até 10 minutos;
- **vermelha:** está há mais de 10 minutos sem dar sinal;
- **"sem sinal":** o painel nunca recebeu sinal dele.

Ao lado aparece onde ele está trabalhando: "na pasta principal" ou "na cópia ..." [cada agente que escreve código
trabalha numa cópia separada do projeto, chamada worktree, para ninguém atrapalhar o trabalho do outro; no fim, o
CRONOS junta tudo].

**Importante:** os agentes trabalham dentro do Claude Code. Se você fechar o Claude Code ou o computador desligar ou
dormir, eles param. "Seguro fechar" fala do painel, não do Claude Code.

---

## 9. AS 13 FASES, EM LINGUAGEM SIMPLES

O trabalho segue 13 fases, sempre nesta ordem. Sete delas são os **7 Dias** da Metodologia Gênesis [o método do
Rafa, inspirado na ordem da Criação: cada camada só existe depois que a anterior está firme]. As outras seis são
fases de apoio.

| Fase | Nome | Dia | O que acontece | Você participa? |
|---|---|---|---|---|
| 0 | Descoberta e Design | Dia 1 — Luz | O ATLAS entende o propósito, o cliente, o diferencial e o visual. Sai o PRD. | **Sim**: responde e aprova o PRD. |
| 1 | Classificação | apoio | O ATLAS mede o tamanho do projeto (baixo, médio ou alto). | Só se houver dúvida de escopo. |
| 2 | Arquitetura e Contratos | Dia 2 — Container | O ATLAS desenha a estrutura e os "contratos" [as regras de como cada parte conversa com a outra]. | Não. |
| 2.3 | Pesquisa Técnica | apoio | Pesquisa das ferramentas e versões certas. | Não. |
| 2.4 | Provisionamento de Ferramentas | apoio | Prepara contas, chaves e serviços. | Talvez: conta, chave ou pagamento. |
| 2.5 | Sequenciamento | apoio | O CRONOS divide o trabalho em ondas e faz um mini-plano para cada agente. | Não. |
| 3 | Fundação | Dia 3 — Superfícies | Banco de dados, estrutura do servidor e testes dos contratos. | Não. |
| 3.5 | Ritmo Temporal | Dia 4 — Astros | Tudo o que depende do tempo: tarefas agendadas, tempos-limite, novas tentativas. | Não. |
| 4 | Desenvolvimento | Dia 5 — Habitantes | As funcionalidades e as telas são construídas, várias ao mesmo tempo. | Não. |
| 4.5 | Consciência Dominante | Dia 6 — Consciência | Segurança, permissões, regras de negócio, registro de auditoria, LGPD. | Sim, em decisões de negócio (ex.: quem cuida dos dados). |
| 5 | Testes de Integração | apoio | Testa o sistema inteiro funcionando junto. | Não. |
| 6 | Preparação para Lançamento | apoio | Revisão final e colocação no ar. | **Sim**: aprova o deploy. |
| 7 | Descanso Consagrado | Dia 7 — Descanso | Documentação, cópias de segurança, alertas e o **teste supremo**: o sistema roda 2 semanas sem depender do criador. | Sim: confirma o teste supremo. |

Em cada fase, o SHIELD revisa cada tarefa e o CRONOS só fecha a fase quando todas as revisões ficam verdes.

---

## 10. SE ALGO PARAR

**O painel ficou amarelo ou vermelho.**
Espere 5 a 10 minutos. O monitor e o vigilante [os dois "seguranças" que ficam de olho nos agentes] avisam o CRONOS
quando algo para, e ele resolve sozinho na maior parte das vezes.

**Continua igual depois de 10 minutos.**
Digite `status` no Claude Code. Depois digite `vigilante` para ver os alertas. O time explica o que aconteceu em
linguagem simples.

**Apareceu uma notificação no canto da tela do Mac** dizendo que um agente parou.
É o monitor automático. Olhe o painel e siga os dois passos acima.

**O Claude Code fechou, o computador desligou ou você quer continuar outro dia.**
1. Abra a pasta do projeto no VS Code.
2. Abra o Claude Code.
3. Digite `d11` (não precisa descrever o projeto de novo).
O ATLAS lê onde o projeto parou, conta em poucas linhas o estado atual e continua dali.

**Um agente ficou sem memória** [o espaço de conversa dele encheu].
Não precisa fazer nada. Ele salva onde parou e o CRONOS chama uma versão nova dele, que continua do mesmo ponto.

**Nada disso resolveu.**
Digite `pausar`, espere a confirmação, e depois `retomar`.

---

## 11. COMO ATUALIZAR O SISTEMA

Quando sair uma versão nova da Formação Δ-11, você atualiza a fonte oficial e leva a melhoria para todos os seus
projetos de uma vez. Isso é feito pelo `sincronizar.sh`, que sempre roda a partir da fonte oficial
(`~/Documents/VSCODE/Formacao-delta-11`).

**Passo 1:** no Terminal, entre na fonte oficial:

```bash
cd ~/Documents/VSCODE/Formacao-delta-11
```

**Passo 2:** traga a versão mais nova do GitHub para a fonte oficial:

```bash
git pull
```

Aparece a lista dos arquivos que mudaram (ou "Already up to date", se você já estava na versão mais nova).

**Passo 3:** veja antes o que vai mudar nos projetos, sem gravar nada:

```bash
bash sincronizar.sh --dry-run
```

Aparece a lista de projetos encontrados e, em cada um, o que seria atualizado.

**Passo 4:** se a lista estiver certa, rode de verdade:

```bash
bash sincronizar.sh --nota "atualização para a versão nova"
```

O que ele faz: leva para cada projeto só os arquivos do **sistema** (agentes, regras, vigias, painel). Ele
**nunca** mexe nos dados do seu projeto: o quadro de tarefas, a memória, os planos e o modo de trabalho (`automatico`
ou `manual`) ficam como estão. No fim mostra quantos projetos foram atualizados.

O `sincronizar.sh` precisa do `jq`. Se aparecer "jq não encontrado", instale com `brew install jq` e rode de novo.

---

## 12. PARA SABER MAIS

- **`README.md`** — a apresentação curta do sistema.
- **`.delta-11/CHANGELOG.md`** — a história de cada versão e o que mudou nela.
- **`CLAUDE.md`** — o manual completo que os agentes leem. Você não precisa ler.
