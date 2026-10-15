# PROTOCOLO DE COMUNICAÇÃO — FORMAÇÃO Δ-11 (v6.4)

## COMO OS AGENTES SE COMUNICAM

Cada agente roda como **sub-agente disparado pelo CRONOS** com o Agent tool do Claude Code. Ninguém abre janela, sessão ou terminal à mão, ninguém cola bloco de ativação e ninguém roda script manual de disparo. A coordenação usa dois meios, com papéis diferentes:

1. **ARQUIVOS** — são a **fonte de verdade**. O que não está escrito em arquivo não aconteceu.
2. **MENSAGENS (`SendMessage`)** — são **aviso**, não registro. Servem para acordar ou chamar alguém nomeado. Toda mensagem importante também fica registrada em arquivo.

---

## 1. QUEM DISPARA QUEM

| Quem | Dispara | Como avisa os outros |
|---|---|---|
| **ATLAS** | SOMENTE o CRONOS (ao fim da Fase 2, ou quando foi chamado e terminou) | Escreve no project-core (só ele escreve) e no `ATLAS-produto.md` |
| **CRONOS** | Executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM), SHIELD, SCOUT, sub-agentes, e o ATLAS quando há bloqueio de contrato/arquitetura ou replanejamento | Escreve kanban, mini-planos, `CRONOS-abertura-fase-N.md`; manda `SendMessage` aos agentes nomeados |
| **Executores** | Ninguém (só os próprios sub-agentes de validação: `build-validator`, `contract-tester`) | `SendMessage` ao CRONOS + `[NOME]-produto.md` |
| **SHIELD** | Os sub-agentes de validação dele (`contract-tester` no Passo 2.7, `schema-validator`, `verify-app`) | Revisa a ONDA inteira e grava uma linha POR TAREFA: `[SHIELD] APROVADO T-XXX [AGENTE]` ou `[SHIELD] REPROVADO T-XXX [AGENTE] motivo` no activity-log + `SendMessage` ao CRONOS |
| **SCOUT** | Ninguém. SCOUT nunca dispara SCOUT | `SendMessage` ao CRONOS |

Quando o ATLAS precisa que o SHIELD revise contratos, ele **registra o pedido** no `ATLAS-produto.md` e o **CRONOS dispara o SHIELD**. Quando um executor descobre algo que afeta outro executor, ele avisa o **CRONOS**, que repassa ao agente afetado (por `SendMessage`, usando o `name` dele) ou, se mexer no contrato, dispara o ATLAS.

### Como o CRONOS dispara

```
Agent(
  description: "Ativação [AGENTE] — onda [N]",
  subagent_type: "general-purpose",
  model: "<lido de .delta-11/perfis/[AGENTE].json>",
  run_in_background: true,
  isolation: "worktree",          ← executores: VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT
  name: "[agente-em-minusculo]-onda-[N]",
  prompt: "<prompt de ativação — estrutura no CLAUDE.md>"
)
```

- **Executores** (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT): COM `isolation: "worktree"`, prompt com `NASCEU_EM_WORKTREE: sim`.
- **CRONOS**: SEMPRE sem worktree, `name: "cronos"`, `NASCEU_EM_WORKTREE: nao`. A auto-retomada do CRONOS também é sem worktree e com `name: "cronos"`.
- **SHIELD revisor**: sem worktree. Lê o código das worktrees pelo caminho absoluto que o CRONOS passa no prompt.
- **Modelo por papel**: o CRONOS lê `perfis/[AGENTE].json` e passa `model` no disparo (opus: ATLAS, CRONOS, SHIELD; sonnet: demais executores e sub-agentes).
  Se algum agente for trocado para Haiku, o vigia de contexto usa 200 mil tokens para ele (alerta em 170 mil); os demais seguem com 1 milhão.
- **Onda inteira de uma vez (v6.4)**: o CRONOS dispara TODOS os agentes independentes da onda na MESMA mensagem — várias chamadas `Agent` juntas, todas com `run_in_background: true` —, até `paralelo_max` (padrão 5, em `.delta-11/.config-limites.json`). Acabou o "lança 3, espera 1, lança mais 2".
- **Fila por vaga**: se a onda tem mais tarefas que o limite, assim que UM agente termina (notificação automática), o próximo da fila sai NA HORA. Nunca se espera a rodada inteira acabar.
- **Em série, só o mesmo arquivo ou dependência declarada (V5)**: (a) dois agentes que precisam editar o MESMO arquivo (zona igual na tabela de zonas do CLAUDE.md, ou arquivo com trava); (b) dependência declarada (uma tarefa precisa do resultado da outra). Todo o resto roda junto.
- **Tarefa grande**: brief acima de `brief_max_tokens` (padrão 4000) vira sub-tarefas por sub-domínio que rodam AO MESMO TEMPO (agentes irmãos, cada um na sua worktree), não ondas em série.
- **Resultado**: quando um sub-agente termina, o CRONOS recebe a notificação automática do Claude Code. Não é preciso ficar perguntando. Ao receber a notificação, o CRONOS lê SÓ o retorno curto: o payload JSON do Passo 3.8 e o `-produto.md` (≤ 500 tokens). Relatório longo fica no log e só é aberto se houver problema — é isso que protege o contexto do CRONOS, não o conta-gotas.

### Revisão por onda e pipeline (v6.4)

- **Executor:** faz a autocrítica (3.4) e dispara o `build-validator` (3.5) e o `contract-tester` (3.7) JUNTOS, os dois com `run_in_background: true`, e espera os dois. Depois avisa o CRONOS (3.8).
- **CRONOS → SHIELD:** o CRONOS NÃO dispara um SHIELD por tarefa. Quando os executores da onda terminam, ele dispara UM SHIELD que revisa a onda inteira, com a lista de tarefas, worktrees e branches no prompt. Onda grande: vários SHIELD em paralelo, um por zona. O SHIELD grava o veredito POR TAREFA (formato acima).
- **Pipeline:** enquanto o SHIELD revisa a onda N, o CRONOS já dispara a onda N+1 nas tarefas que NÃO dependem de nada da onda N. Só esperam o APROVADO as tarefas que dependem de código da onda N.
- **Merge:** só tarefas com `[SHIELD] APROVADO` entram na pasta principal (`merge-guiado-contratos.md`). Reprovação vira tarefa de correção na próxima vaga livre.
- **O que reprova:** código e contrato — o que é falso, contradiz o contrato ou deixa risco técnico. Erro de redação em documento (português, formatação, sinônimo) NUNCA reprova; vira observação.

---

## 2. OS ARQUIVOS (fonte de verdade)

Todos os arquivos compartilhados ficam na **pasta principal do projeto** (nunca na cópia dentro de uma worktree). O agente em worktree usa o **caminho absoluto** que o CRONOS passou no prompt. Os hooks descobrem essa pasta com `git rev-parse --git-common-dir` (a pasta principal é o diretório pai do resultado).

| Arquivo | O que é | Quem escreve | Quem lê |
|---|---|---|---|
| `.delta-11/kanban.md` + `kanban-data.js` | Estado das tarefas | **Só o CRONOS** | Todos (cada executor, a própria coluna) |
| `.delta-11/memoria/project-core.md` e as fatias em `memoria/project-core/` (`banco.md`, `contratos.md`, `visual.md`, `decisoes-tecnicas.md`) | Contrato do projeto: o que DEVE ser | **Só o ATLAS** | ATLAS, CRONOS, SHIELD, SCOUT e sub-agentes leem o inteiro; executores leem só as fatias do seu papel |
| `.delta-11/planos/[AGENTE]-plan.md` | Mini-plano da onda (6 seções + checklist do ciclo interno) | CRONOS | O próprio agente |
| `.delta-11/memoria/[NOME]-produto.md` | O que existe agora (≤ 500 tokens para executores; ATLAS e CRONOS isentos) + seção `PROPOSTAS PARA O PROJECT-CORE` | O próprio agente | CRONOS, próximas fases, `cold-start-tester` |
| `.delta-11/memoria/[NOME]-historia.md` | Diário do agente, sem limite | O próprio agente | Quem precisar de detalhe |
| `.delta-11/memoria/CRONOS-abertura-fase-N.md` | Abertura de cada fase (o que foi selado, desvios, ajustes) | CRONOS | Todos |
| `.delta-11/ativacoes/` | ACKs, retomadas, avisos (`contrato-alterado-[AGENTE].txt`, `contratos-desatualizados.txt`), pulsos | Agentes e hooks | CRONOS, hooks, painel |
| `.delta-11/activity-log.md` | Registro automático de tudo | Hooks (e as linhas de aprovação do SHIELD) | Todos |
| `.delta-11/logs/` | Autocrítica, relatórios de sub-agentes, falhas do SHIELD | Agentes e hooks | CRONOS, SHIELD, auditoria |

O arquivo `[NOME]-estado.md` é **legado**: pode ser lido se existir num projeto antigo, mas nunca mais é escrito.

Quando um agente tem algo para o project-core, ele escreve na seção `PROPOSTAS PARA O PROJECT-CORE` do seu `-produto.md` e avisa o CRONOS; o CRONOS encaminha ao ATLAS.

---

## 3. AS MENSAGENS (`SendMessage`)

`SendMessage` manda mensagem a um sub-agente nomeado (o `name` do disparo) e também serve para retomar um sub-agente que parou. Não precisa de Agent Teams.

**Executor → CRONOS** (fim de tarefa, Passo 3.8 — entra na revisão do SHIELD da onda; NÃO cria arquivo `.txt` de pedido). É o retorno curto que o CRONOS lê ao ser notificado:

```json
{
  "agente": "ENGINE",
  "worktree": "<caminho da worktree>",
  "branch": "delta-11/engine-onda-2",
  "tarefas_concluidas": ["T-042"],
  "arquivos_modificados": ["src/app/api/users/route.ts"],
  "build_validator": "PASS",
  "contract_tests": "PASS",
  "autocritica": ".delta-11/logs/autocritica/<arquivo>.md",
  "pedido": "revisão do SHIELD",
  "mensagem": "Descrição curta do que foi feito"
}
```

A mesma informação já está no `ENGINE-produto.md` (Passo 1a). A mensagem só avisa.

**Outras mensagens comuns:**
- Executor → CRONOS: erro que não resolveu em 3 tentativas (ver `correcao-de-erros.md`), contexto esgotado, dependência descoberta, proposta para o project-core.
- CRONOS → agente nomeado: "o contrato mudou, releia a fatia X" (junto com `ativacoes/contrato-alterado-[AGENTE].txt`), "retome a tarefa T-XXX", "a revisão do SHIELD reprovou: motivo".
- SHIELD → CRONOS: resultado da revisão da onda, com o veredito de cada tarefa (o registro oficial são as linhas no activity-log).

---

## 4. ROTINA DE TAREFA (todos os executores, ordem única)

**Início:**
- **Passo 0** — ACK: escreve a hora em `.delta-11/ativacoes/ack-[NOME].txt`.
- **Passo 0.VW** — confere se nasceu na worktree (`git rev-parse --show-toplevel` diferente da pasta principal). Informa o caminho ao CRONOS no primeiro `SendMessage`.
- **Passo 0.3** — travas: para cada arquivo que vai editar, `mkdir .delta-11/locks/[caminho--do--arquivo].lock` (é uma **pasta**; se o `mkdir` falhar, outro agente está com o arquivo).
- **Passo 0.5** — lê as fatias do project-core do seu papel, o próprio mini-plano, a própria coluna do kanban, `memoria/pesquisa-tecnica.md` e a própria base de conhecimento.

**Finalização:**
- **1a** — atualiza `[NOME]-produto.md` (com a linha `autocritica: <caminho>`).
- **1b** — acrescenta ao `[NOME]-historia.md`.
- **3.4** — autocrítica em 2 paradas, salva em `.delta-11/logs/autocritica/`.
- **3.5 e 3.7, juntos** — `build-validator` e `contract-tester` (que gera E roda os testes de contrato do que mudou) disparados na MESMA mensagem, os dois com `run_in_background: true`; o executor espera os dois. FAIL de qualquer um → corrige e roda de novo.
- **3.8** — `SendMessage` ao CRONOS com o payload curto (a revisão do SHIELD é feita por onda).
- **3.9** — libera as travas (apaga as próprias pastas em `.delta-11/locks/`).

Todos os executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT) passam pela revisão do SHIELD, que é feita por onda e dá o veredito por tarefa. A tarefa só vira CONCLUÍDA no kanban — escrita pelo CRONOS — depois da linha `[SHIELD] APROVADO T-XXX [AGENTE]`.

---

## 5. RETOMADA (contexto esgotado)

Quem dispara qualquer retomada é o **CRONOS**. Nenhum agente se "auto-dispara" e nenhum pede ao comandante para abrir sessão.

- **Executor com contexto esgotado:** atualiza `-produto.md` e `-historia.md`, escreve `.delta-11/ativacoes/retomada-[NOME].txt` e manda `SendMessage` ao CRONOS. O CRONOS retoma o agente por `SendMessage` (mesmo `name`) ou dispara um novo com o mesmo `name` e a palavra "retomar" no prompt, apontando para `retomada-[NOME].txt` e para o `-produto.md`.
- **O próprio CRONOS com contexto esgotado:** escreve `.delta-11/ativacoes/retomada-CRONOS.txt` e dispara a si mesmo com o Agent tool, **sem worktree** e com `name: "cronos"`.
- Só se o Agent tool falhar 3 vezes seguidas (cadeia de tentativas do CLAUDE.md) o CRONOS escreve `.delta-11/ativacoes/pendente-[AGENTE].txt` e o painel avisa o comandante.

---

## 6. FORMATO DE CONTRATO DE INTERFACE DE PROGRAMAÇÃO DE APLICAÇÕES

```
ROTA: [MÉTODO] [/caminho]               ← nomes em inglês: /api/users
DESCRIÇÃO: [o que faz]
AUTENTICAÇÃO: [público / requer token / apenas administrador]

ENTRADA:
{
  field: tipo (obrigatório/opcional) — descrição
}

SAÍDA SUCESSO (código [número]):
{
  field: tipo — descrição
}

SAÍDA ERRO (código [número]):
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "texto para humano",
    "details": [...]
  }
}
```

Validação falhou ou campo faltando = HTTP **400** com `code: "VALIDATION_ERROR"`. É o único formato de erro do sistema.

---

## 7. QUANDO O CONTRATO PODE MUDAR

1. Qualquer agente identifica a necessidade e escreve a proposta na seção `PROPOSTAS PARA O PROJECT-CORE` do seu `-produto.md`.
2. Avisa o CRONOS por `SendMessage`. O CRONOS registra o bloqueio no kanban.
3. O CRONOS dispara o ATLAS com a proposta.
4. O ATLAS avalia, aprova ou rejeita. Só se for decisão de negócio ou de escopo o comandante é consultado.
5. Se aprovado: o ATLAS atualiza o project-core (e as fatias).
6. O hook `regenerar-contratos.py` só calcula o novo hash e grava `.delta-11/ativacoes/contratos-desatualizados.txt` (hash novo + hora). Ele NÃO dispara nada.
7. Quando o ATLAS termina as edições, o CRONOS roda o `contract-tester` UMA vez, apaga o aviso e, se precisar, pede o `impact-mapper` (que só mapeia e propõe; tarefas no kanban só entram com a aprovação do CRONOS).
8. O CRONOS avisa cada agente afetado com `.delta-11/ativacoes/contrato-alterado-[AGENTE].txt` + `SendMessage`.

---

## 8. RASTREAMENTO EM TEMPO REAL

### Activity log (`.delta-11/activity-log.md`)
- Gerado automaticamente pelos hooks (PostToolUse etc.). Nenhum agente precisa "lembrar" de escrever.
- Formato único de linha: `- [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem`.
- A exceção são as linhas de aprovação que o SHIELD grava: `[SHIELD] APROVADO T-XXX [AGENTE]` ou `[SHIELD] REPROVADO T-XXX [AGENTE] motivo`.

### Travas (`.delta-11/locks/`)
- Cada trava é uma **pasta** criada com `mkdir` (Passo 0.3) — o `mkdir` é atômico, então dois agentes nunca pegam o mesmo arquivo.
- O hook PreToolUse confere as travas antes de cada Write/Edit; arquivo travado por outro agente → operação BLOQUEADA com mensagem clara.
- Ao finalizar a tarefa, o agente apaga as próprias travas (Passo 3.9). Se a sessão acabar antes, o hook de parada libera as travas do agente.
- Travas com mais de 2 horas (`lock_horas` em `.delta-11/.config-limites.json`) são removidas automaticamente.

### Pulsos e painel
- O `heartbeat.sh` grava `ativacoes/pulso-[AGENTE].json` na pasta principal e regenera `.delta-11/pulsos-data.js`. O painel (`.delta-11/painel.html`) lê `kanban-data.js`, `pulsos-data.js` e `monitor-data.js` e abre sozinho no início da sessão (no máximo uma vez a cada 8 horas).

### Registro dos sub-agentes
- Quando qualquer sub-agente termina, o hook do evento `SubagentStop` grava `logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log`.
- O relatório completo do sub-agente é salvo pelo agente que o disparou (Regra 17).

### Hooks do sistema (`.claude/settings.json`)
- São instalados pelo `sincronizar.sh` a partir de `templates/settings-hooks.json` e não dependem de cooperação do agente. Todo comando de hook usa `"$CLAUDE_PROJECT_DIR"`.

---

## 9. ESQUEMA DE BANCO CONGELADO

Durante uma onda, o esquema de banco NÃO MUDA (no pipeline de ondas, isso vale para a onda que está rodando e para a que está em revisão). Agentes podem confiar na estabilidade. Mudanças seguem o mesmo processo do contrato (seção 7, via ATLAS). Lembrete: o project-core é a verdade do contrato; as migrations são a verdade do banco implementado; se divergirem, é bug para o ATLAS decidir.

---

## 10. ARQUIVOS TEMPORÁRIOS

Nada vai para a pasta temporária do sistema. Use `.delta-11/scratch/` (expira em 7 dias).
