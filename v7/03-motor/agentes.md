# Os agentes do v7 — as escolhas do Agent Forge, num lugar só

> O corpo de cada agente é a página do papel (`v7/02-regras/paginas/`), mais o que o motor acrescenta, tirado de `lugares.md` e `rotas.md`. Este arquivo guarda só o que o Agent Forge pede além disso. `ferramentas/montar-agentes.py` junta tudo em `agentes/<nome>.md`; nunca edite os agentes à mão.

**Por que estas escolhas** (decididas pelo Claude em 2026-10-17, pelas regras seladas e pelo ensaio do motor; o Rafa pode trocar qualquer uma):
- **Modelo:** `opus` para os papéis de julgamento (ATLAS, ARQUITETO, CRONOS, Destruidor, Selador); `sonnet` para quem constrói, registra e para o leitor do teste. Nunca `haiku` (o Rafa não usa).
- **Memória entre sessões:** nenhuma. Cada papel nasce como agente novo e só sabe o que o quadro e o arquivo de estado contam.
- **Pasta única:** todos trabalham na pasta do produto; a trava deixa cada um escrever só no seu lugar (`lugares.md`). Cópia isolada só para as candidatas do coração, como a regra manda (`rotas.md`).
- **Terminal:** quem não escreve código não tem terminal (ATLAS, ARQUITETO, CRONOS, Documentador); Destruidor, Revisor e Selador têm o terminal **vigiado** (a trava barra gravar arquivo, mexer no git e tocar em `.delta-11/` pelo terminal); Construtores e SCOUT têm o terminal **livre**, dentro da caixa de areia (só gravam na pasta do produto e nos caches das ferramentas). Quem tem terminal roda o produto pela caixa do produto (`ganchos/caixa-do-produto.py`).
- **Chamar outros:** a lista `Agent(...)` do ATLAS vale para ele, o agente principal (pela documentação, não para os agentes que ele chama); quem segura todos é o porteiro, que barra o que não está em `rotas.md`.
- **Autonomia:** `auto` em todos os agentes chamados; o ATLAS segue o modo que o dono usa na conversa (no modo "pular permissões", o `auto` dos agentes é ignorado; a trava vale do mesmo jeito).
- **Cor:** uma por papel de julgamento ou registro; os Construtores e o SCOUT em verde (mexem no código); o leitor do teste em laranja, como o Selador que o chama.

| papel | nome | quando usar | ferramentas | modelo | terminal | só lê em | cor |
|---|---|---|---|---|---|---|---|
| ATLAS | atlas | Agente principal da pasta de um produto do Delta-11: é quem conversa com o dono, do primeiro pedido ao Dia 7 e depois. | Read, Grep, Glob, Write, Edit, WebFetch, SendMessage, TaskStop, CronCreate, CronList, CronDelete, Agent(arquiteto, cronos, destruidor, scout, back, engine, form, front, pixel, shield, vault, revisor, selador, documentador, leitor-do-teste) | opus | — | — | purple |
| ARQUITETO | arquiteto | Use quando o ATLAS ou o CRONOS precisarem de quem decide as camadas: abrir, reabrir ou parar uma camada, ou procurar uma rachadura. | Read, Grep, Glob, Write, Edit, WebFetch, WebSearch | opus | — | — | blue |
| CRONOS | cronos | Use quando o ATLAS ligar uma camada aberta pelo ARQUITETO ou um pedido do dono: conduz o ciclo da camada do começo ao selo. | Read, Grep, Glob, Write, Edit, SendMessage, TaskStop, Agent | opus | — | — | cyan |
| VAULT | vault | Use quando o CRONOS tiver um brief para o território Dados. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| ENGINE | engine | Use quando o CRONOS tiver um brief para o território Servidor. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| FRONT | front | Use quando o CRONOS tiver um brief para o território Estrutura da tela. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| PIXEL | pixel | Use quando o CRONOS tiver um brief para o território Aparência. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| FORM | form | Use quando o CRONOS tiver um brief para o território Formulários. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| BACK | back | Use quando o CRONOS tiver um brief para o território Leis do produto (esteira, publicação, alarmes, cofre). | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| SHIELD | shield | Use quando o CRONOS tiver um brief para o território Contratos, pulsos e provas, ou quando um Construtor pedir aval para mudar um teste. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| Destruidor | destruidor | Use no passo 5 do ciclo, com a camada montada, quando a abertura o chama; nas candidatas do coração (Camada 3); e quando o ATLAS propuser mudar a Luz. | Read, Grep, Glob, Bash, Write | opus | vigiado | — | red |
| Revisor | revisor | Use no passo 5 do ciclo, nas camadas que têm Revisor, com a camada montada. | Read, Grep, Glob, Bash, Write | sonnet | vigiado | — | yellow |
| Selador | selador | Use no passo 6 do ciclo, depois dos relatos do Destruidor e do Revisor; na escolha das candidatas do coração (Camada 3); e para testar o arquivo de estado no passo 7. | Read, Grep, Glob, Bash, Write, Agent | opus | vigiado | — | orange |
| Documentador | documentador | Use no passo 7 do ciclo, quando o Selador selar a camada; e na Camada 1, depois que o ATLAS escrever a Luz. | Read, Grep, Glob, Write, Edit | sonnet | — | — | pink |
| SCOUT | scout | Use quando o alarme do produto apontar um erro em produção. | Read, Grep, Glob, Write, Edit, Bash | sonnet | livre | — | green |
| leitor do teste | leitor-do-teste | Use só quando o Selador pedir um agente novo para um teste. | Read, Grep, Glob | sonnet | — | `.delta-11/leitor/` | orange |
