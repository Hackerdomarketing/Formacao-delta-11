# PROTOCOLO DE SUB-AGENTES — FORMAÇÃO Δ-11 (v6.4)

## O QUE SÃO SUB-AGENTES

Sub-agentes são agentes especializados disparados POR um agente principal para uma tarefa específica de validação, análise ou verificação. Eles retornam um relatório estruturado e **nunca modificam código** do projeto.

Diferença chave:
- **Agentes principais** (ATLAS, CRONOS, FRONT, ENGINE, etc.) executam as tarefas do kanban e constroem o projeto.
- **Sub-agentes** são ferramentas que os agentes principais usam para validar e analisar. Quem disparou é quem decide o que fazer com o relatório.

Os sub-agentes podem ler o project-core inteiro (a restrição de leitura por fatias vale só para os executores).

**Em paralelo e em segundo plano (v6.4):** todo sub-agente é disparado com `run_in_background: true`. Quando há mais de um para disparar no mesmo momento, eles saem JUNTOS, na MESMA mensagem: o `build-validator` e o `contract-tester` de cada tarefa (Passos 3.5 e 3.7); e os revisores de fim de fase — `fresh-reviewer`, um `cold-start-tester` por `-produto.md` e o `qa-ui-tandem`. Quem disparou espera TODOS (a notificação de cada um chega sozinha) e então consolida. Nenhum revisor roda em primeiro plano e nenhum espera o outro terminar para começar.

---

## OS 10 SUB-AGENTES

Cada um tem um arquivo em `.delta-11/sub-agentes/`. A tabela diz quem dispara e quando; os detalhes vêm logo abaixo.

| # | Sub-agente | Quem dispara | Quando roda |
|---|---|---|---|
| 1 | `build-validator` | Cada executor (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT); SHIELD na Fase 6 | Passo 3.5 de toda tarefa de código; antes do deploy |
| 2 | `contract-tester` | SHIELD (Passo 2.7); cada executor (Passo 3.7, junto com o build-validator); CRONOS (depois que o ATLAS altera o project-core) | Fim da Fase 2; toda tarefa de código; após mudança de contrato |
| 3 | `code-architect` | CRONOS | Fim da Fase 4 (obrigatório); Fase 2.5 e durante a execução (sob demanda) |
| 4 | `verify-app` | SHIELD | Fase 6, antes do deploy, depois do merge da onda |
| 5 | `schema-validator` | SHIELD | Antes de criar/alterar SQL de teste ou seeds; depois de migration nova; quando o ATLAS altera o esquema |
| 6 | `impact-mapper` | CRONOS (só a pedido) | Depois que o ATLAS altera o project-core e o CRONOS quer saber o impacto no código pronto |
| 7 | `fresh-reviewer` | CRONOS | Fim de cada fase, depois de todas as tarefas aprovadas pelo SHIELD — junto com os outros revisores de fase |
| 8 | `cold-start-tester` | CRONOS | Fim de cada fase, junto com o fresh-reviewer — um disparo por `[AGENTE]-produto.md`, todos ao mesmo tempo |
| 9 | `tool-provisioner` | CRONOS | Fase 2.4; e quando uma integração nova entra no projeto |
| 10 | `qa-ui-tandem` | CRONOS | Fim de cada fase com interface navegável, junto com o fresh-reviewer e os cold-start-tester (selo experiencial) |

---

### 1. BUILD VALIDATOR — Validação de Build

**Arquivo:** `.delta-11/sub-agentes/build-validator.md`

**Quem dispara e quando:**
- Cada executor que escreve código (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT), no **Passo 3.5** de toda tarefa, dentro da própria worktree — na MESMA mensagem do `contract-tester` (3.7), os dois em segundo plano.
- O SHIELD, na Fase 6, antes do deploy.

**O que faz:** roda typecheck, lint, build e testes (incluindo os de contrato, se existirem); verifica vulnerabilidades (`npm audit`); procura segredos expostos; valida o `.gitignore`; aplica os limites de código como bloqueio.

**Resultado:** PASS/FAIL + lista de bloqueios e avisos.

**Regra de ouro:** FAIL com bloqueios → a tarefa NÃO é concluída até corrigir.

---

### 2. CONTRACT TESTER — Testes de Contrato

**Arquivo:** `.delta-11/sub-agentes/contract-tester.md`

O contract-tester **gera E roda** os testes de contrato e devolve o resultado. É **idempotente**: a mesma entrada gera exatamente os mesmos arquivos (sem data nem hora no índice gerado, rotas em ordem alfabética).

**Quem dispara e quando:**
1. **Geração inicial — Passo 2.7 (SHIELD):** ao fim da Fase 2, depois que o ATLAS salvou os contratos e o SHIELD terminou a revisão. Gera `tests/contracts/` a partir do project-core e roda uma vez.
2. **Por tarefa — Passo 3.7 (cada executor):** junto com o build-validator (Passo 3.5), na mesma mensagem, os dois em segundo plano; o executor espera os dois. Gera os testes do que mudou na tarefa, roda e devolve PASS/FAIL. Vale também para o SCOUT ao corrigir bug. Se o build-validator falhar, o executor corrige e roda os dois de novo.
3. **Depois de mudança no project-core (CRONOS):** o hook `regenerar-contratos.py` não dispara mais nada — ele só calcula o hash e grava `.delta-11/ativacoes/contratos-desatualizados.txt` (hash novo + hora). Quando o ATLAS termina as edições, o CRONOS dispara o contract-tester UMA vez para regenerar e rodar os testes e apaga o aviso.

**Uso dos testes sem disparar o sub-agente:**
- **Árbitro de merge:** o CRONOS roda `npm run test:contracts` (ou equivalente) nas versões candidatas — ver `merge-guiado-contratos.md`.
- **Fim de fase e antes de deploy:** os hooks `validar-contratos-fim-fase.py` e `validar-deploy.py` rodam os testes e bloqueiam a transição se falharem.

**Regra de ouro:** teste de contrato falhando = código violando o combinado. Não ignore.

---

### 3. CODE ARCHITECT — Análise Arquitetural

**Arquivo:** `.delta-11/sub-agentes/code-architect.md`

**Quem dispara:** sempre o CRONOS (a partir da pasta principal; lê o código das worktrees ativas via `git worktree list`).

**Quando:**
- Ao final da Fase 4 (OBRIGATÓRIO).
- Na Fase 2.5, para validar os mini-planos que o próprio CRONOS montou (opcional).
- Durante a execução, nos 10 casos de uso abaixo (sob demanda).

**O que faz:** compara o código REAL com a arquitetura PLANEJADA no project-core; identifica desvios, dívida técnica e falta de conformidade com os padrões; dá nota A/B/C/D/F.

**Regra de ouro:** nota C ou pior → o CRONOS cria tarefas de correção ANTES de avançar de fase. Problema que exige mudar contrato → o CRONOS dispara o ATLAS.

---

### 4. VERIFY APP — Teste de ponta a ponta no navegador

**Arquivo:** `.delta-11/sub-agentes/verify-app.md`

**Quem dispara:** o SHIELD, na Fase 6, a partir da pasta principal, DEPOIS do merge da onda (testa o estado consolidado). O hook de deploy também exige que ele tenha passado.

**O que faz:** abre a aplicação num navegador automatizado, percorre os fluxos críticos, verifica erros no console e falhas de rede, tira screenshots dos problemas.

**Resultado:** PASSED/FAILED + screenshots (em `.delta-11/evidencias/screenshots/AAAA-MM-DD/`).

**Regra de ouro:** FAILED → nada de deploy até corrigir.

**Não confundir com o `qa-ui-tandem`:** o verify-app é a verificação técnica pré-deploy da Fase 6; o qa-ui-tandem é o selo experiencial de cada fase.

---

### 5. SCHEMA VALIDATOR — SQL de teste contra as migrations

**Arquivo:** `.delta-11/sub-agentes/schema-validator.md`

**Quem dispara:** o SHIELD.

**Quando:**
1. Antes de qualquer tarefa que crie ou modifique arquivos SQL de teste (seeds, dados de teste).
2. Depois de qualquer migration nova (para ver se os seeds ainda valem).
3. Sempre que o ATLAS alterar o esquema no project-core (para detectar divergência).

**O que faz:** compara as colunas usadas nos SQL de teste e nos seeds com as migrations reais do banco e reporta colunas inexistentes, nomes errados e obrigatórios ausentes. Não modifica nada.

**Resultado:** PASS ou FIX FIRST (há pelo menos um bloqueio).

**Regra de ouro:** as migrations são a verdade do banco IMPLEMENTADO; o project-core é a verdade do CONTRATO. Se o schema-validator achar divergência entre os dois, é um bug: o SHIELD avisa o CRONOS, que dispara o ATLAS para decidir.

---

### 6. IMPACT MAPPER — Impacto de uma mudança de contrato

**Arquivo:** `.delta-11/sub-agentes/impact-mapper.md`

**Quem dispara:** o CRONOS, **só a pedido** — normalmente depois que o ATLAS altera o project-core com código já escrito. Nenhum hook o dispara.

**O que faz:**
- Lê a diferença do project-core (via git).
- Classifica cada mudança (rota nova, rota removida, campo alterado, tabela alterada etc.).
- Procura no código (pasta principal e worktrees ativas) os arquivos afetados.
- Cruza com o kanban para achar tarefas invalidadas.
- Escreve `.delta-11/memoria/impacto-mudanca-[AAAAMMDDTHHMMSSZ].md` com as tarefas `[IMPACTO-MUDANCA]` PROPOSTAS e os agentes afetados.

**O que NÃO faz:** não escreve no kanban e não corrige nada. O CRONOS revisa o relatório, aprova as tarefas, escreve-as no kanban e avisa cada agente afetado com `.delta-11/ativacoes/contrato-alterado-[AGENTE].txt` + `SendMessage`.

---

### 7. FRESH REVIEWER — Revisão por olhos virgens

**Arquivo:** `.delta-11/sub-agentes/fresh-reviewer.md`

**Quem dispara:** o CRONOS (único disparador).

**Quando:** ao final de cada fase, depois que todas as tarefas têm `[SHIELD] APROVADO` e ANTES do selo. Sai na MESMA mensagem dos `cold-start-tester` e do `qa-ui-tandem`, em segundo plano.

**O que faz:** recebe APENAS o caminho do projeto e a fase atual. NÃO lê project-core, mini-planos, memória de agentes nem contratos — é VIRGEM de contexto. Usa a aplicação como um usuário real e reporta o que quebra, o que incomoda, o que parece mal acabado ou genérico.

**Resultado:** PASSED / PASSED_COM_RESSALVAS / FAILED + problemas em 3 níveis (crítico, moderado, pequeno).

**Regra de ouro:** o valor dele está em NÃO SABER. Materializa a sub-etapa 5 do ciclo interno (revisão cruzada). Problema crítico → o CRONOS cria tarefas de correção antes do selo.

---

### 8. COLD START TESTER — Suficiência do `-produto.md`

**Arquivo:** `.delta-11/sub-agentes/cold-start-tester.md`

**Quem dispara:** o CRONOS (único disparador).

**Quando:** ao final de cada fase, JUNTO com o fresh-reviewer e ANTES do selo. Um disparo POR `[AGENTE]-produto.md` da fase — todos na mesma mensagem, em segundo plano (ele lê só o `-produto.md`, então não depende do resultado do fresh-reviewer).

**O que faz:** recebe APENAS o caminho de UM `[AGENTE]-produto.md`. Responde 4 perguntas (o que existe; o que a próxima fase pode usar; o que NÃO existe nem vai existir; qual a próxima tarefa) e dá a confiança de cada resposta (ALTA/BAIXA/IMPOSSÍVEL).

**Resultado:** APROVADO/REPROVADO + as 4 respostas + lacunas.

**Regra de ouro:** materializa o mecanismo M4b (teste do cold start). Reprovado → o agente responsável reescreve o `-produto.md` antes do selo.

---

### 9. TOOL PROVISIONER — Ferramentas externas verificadas

**Arquivo:** `.delta-11/sub-agentes/tool-provisioner.md`

**Quem dispara:** o CRONOS.

**Quando:** na Fase 2.4 (entre a Pesquisa Técnica e os Mini-planos) — obrigatório em projeto com integrações externas. Também quando uma integração nova entra no projeto (ex.: troca de fornecedor de IA).

**O que faz:**
- Monta o inventário (MCPs, chaves de API, contas, variáveis de ambiente, CLIs; o Sentry entra sempre que houver deploy planejado).
- Classifica cada item: AUTO-CLI, AUTO-BROWSER, CREDENCIAL (pede ao comandante, tudo de uma vez), HUMANO (pagamento/telefone — checklist em linguagem leiga).
- Verifica cada ferramenta com teste REAL, não só "a chave existe".
- Atualiza `.delta-11/memoria/ferramentas-do-projeto.md` e grava `.delta-11/memoria/tool-verification.md`.

**Regra de ouro:** ferramenta listada mas não configurada é promessa, não capacidade.

---

### 10. QA-UI-TANDEM — Selo experiencial pelo navegador

**Arquivo:** `.delta-11/sub-agentes/qa-ui-tandem.md`

**Quem dispara:** o CRONOS.

**Quando:** ao fim de cada fase que tem interface navegável, JUNTO com o fresh-reviewer e os cold-start-tester (mesma mensagem, em segundo plano) e antes do selo. Roda nos dois modos: em `automatico` o resultado decide o selo; em `manual` o relatório vai ao comandante junto com o pedido de `aprovar`.

**O que faz:** percorre, pelo Tandem Browser MCP, os fluxos críticos que o CRONOS gerou a partir do project-core (roteiro em `.delta-11/templates/selo-experiencial-template.md`), confere o estado esperado de cada passo e guarda a evidência. Não pergunta nada ao comandante.

**Resultado:** PASS/FAIL por fluxo + diagnóstico. FAIL → o CRONOS cria a tarefa `[SELO-FAIL]` e a fase volta para execução.

---

## QUANDO CADA SUB-AGENTE É OBRIGATÓRIO

| Sub-agente | Frequência | Fase | Disparado por | Obrigatório? |
|------------|-----------|------|---------------|--------------|
| build-validator | Após cada tarefa de código (Passo 3.5) | 3, 3.5, 4, 4.5, 5 | Executor dono da tarefa | SIM |
| build-validator | Antes do deploy | 6 | SHIELD | SIM |
| contract-tester — geração inicial | Fim da Fase 2 (Passo 2.7) | 2 | SHIELD | SIM |
| contract-tester — por tarefa | Junto com o build-validator (Passo 3.7) | 3 em diante | Executor dono da tarefa | SIM |
| contract-tester — após mudança no project-core | Uma vez, quando o ATLAS termina as edições | Qualquer | CRONOS | SIM |
| Testes de contrato — fim de fase | Antes de cada transição de fase | Qualquer | Hook `validar-contratos-fim-fase.py` | SIM — bloqueia a transição |
| Testes de contrato — antes de deploy | Ao pedir deploy | 6 | Hook `validar-deploy.py` | SIM — bloqueia o deploy |
| Testes de contrato — árbitro de merge | Conflito de merge entre worktrees | 3 em diante | CRONOS (`npm run test:contracts`) | SIM |
| code-architect | Fim da Fase 4 + sob demanda | 2.5, 4 | CRONOS | SIM no fim da Fase 4 |
| verify-app | Antes de deploy | 6 | SHIELD | SIM |
| schema-validator | SQL de teste, migration nova, esquema alterado | 3 em diante | SHIELD | SIM |
| impact-mapper | Mudança de contrato com código já escrito | Qualquer | CRONOS (a pedido) | Quando o CRONOS pede |
| fresh-reviewer | Fim de cada fase (junto com os outros revisores) | Todas com algo para usar | CRONOS | SIM |
| cold-start-tester | Fim de cada fase, 1 por `-produto.md`, todos juntos | Todas com `-produto.md` | CRONOS | SIM |
| tool-provisioner | Fase 2.4 + integração nova | 2.4 | CRONOS | SIM se há integrações externas |
| qa-ui-tandem | Fim de cada fase com interface | Fases com interface navegável | CRONOS | SIM |

---

## COMO DISPARAR UM SUB-AGENTE

Use o **Agent tool** (o nome antigo era "Task tool"):

```
Agent(
  description: "[NOME-DO-SUB-AGENTE] — [propósito] — T-XXX",
  subagent_type: "general-purpose",
  model: "sonnet",                      ← todos os sub-agentes rodam em sonnet (perfis/)
  run_in_background: true,              ← sempre em segundo plano; a notificação chega sozinha
  prompt: "[conteúdo de .delta-11/sub-agentes/[NOME].md] + contexto específico
           (caminho do projeto, tarefa, arquivos, fase)"
)
```

Vários sub-agentes no mesmo momento (3.5 + 3.7; revisores de fim de fase) = várias chamadas `Agent` na MESMA mensagem. Quem disparou espera a notificação de TODOS antes de agir.

Depois:
1. Leia o relatório retornado (de cada um).
2. Salve o relatório completo em `.delta-11/logs/sub-agentes/[AAAA-MM-DD]-[sub-agente]-[AGENTE]-[T-XXX].md` (Regra 17). O hook do evento `SubagentStop` grava sozinho a prova `logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log`.
3. Escreva a linha-resumo no seu `-produto.md` (`<sub-agente>: <PASS|FAIL> / <métrica chave>`).
4. Aja conforme o resultado (corrigir, aprovar, replanejar, avisar o CRONOS).

**IMPORTANTE:** sub-agentes só reportam. Quem disparou é responsável por AGIR com base no relatório.

---

## INTEGRAÇÃO COM WORKTREE

Executores trabalham cada um na sua worktree. Isso define ONDE cada sub-agente roda:

- **build-validator e contract-tester (Passos 3.5 e 3.7):** o executor dispara dentro da própria worktree; o resultado volta para ele.
- **code-architect, impact-mapper:** disparados pelo CRONOS a partir da pasta principal. Usam `git worktree list` para achar as worktrees ativas e `git show <branch>:<caminho>` para ler arquivos delas, e produzem um relatório único.
- **schema-validator:** disparado pelo SHIELD, que roda sem worktree e lê os arquivos da worktree do VAULT pelo caminho absoluto.
- **verify-app:** disparado pelo SHIELD na pasta principal DEPOIS do merge da onda.
- **fresh-reviewer, cold-start-tester, qa-ui-tandem:** disparados pelo CRONOS na pasta principal, depois do merge.
- **Árbitro de merge:** ver `.delta-11/protocolos/merge-guiado-contratos.md`.

**Regra geral:** o sub-agente roda na pasta de quem o disparou. Disparo dentro de uma worktree → contexto daquela worktree. Disparo na pasta principal → contexto da pasta principal. Arquivos compartilhados (logs, ativacoes, memoria) sempre na pasta principal.

---

## CODE ARCHITECT + CRONOS — 10 CASOS DE USO

O code-architect é especialmente útil para o CRONOS em projetos de alta complexidade:

### 1️⃣ ANTES da Fase 2.5 — Análise do estado atual

**Quando:** projeto em andamento (não começa do zero), antes de o CRONOS montar os mini-planos.
**O CRONOS dispara o code-architect para:**
- Analisar o código EXISTENTE
- Gerar relatório de conformidade com o project-core
- Identificar dívida técnica que precisa ser paga ANTES de funcionalidades novas
- Mapear acoplamentos críticos que vão afetar o planejamento

**Resultado:** os mini-planos nascem com informação REAL do estado do código.

---

### 2️⃣ Durante a Fase 2.5 — Validação dos mini-planos

**Quando:** o CRONOS terminou de montar os `planos/[AGENTE]-plan.md` e quer conferi-los antes de disparar a Onda 1.
**O CRONOS dispara o code-architect para:**
- Analisar se os mini-planos SEGUEM os padrões do project-core
- Identificar conflitos arquiteturais antes da execução
- Detectar abstrações prematuras ou faltantes
- Validar que os mini-planos respeitam as zonas de trabalho

**Resultado:** a Onda 1 começa com mini-planos arquiteturalmente sólidos.

---

### 3️⃣ Quando um agente reporta bloqueio — Diagnóstico arquitetural

**Quando:** o ENGINE avisa "não consigo implementar essa rota porque [razão]".
**O CRONOS dispara o code-architect para:**
- Diagnosticar se o bloqueio é ARQUITETURAL (falta infraestrutura, dependência circular) ou de IMPLEMENTAÇÃO (bug simples)
- Arquitetural → o CRONOS dispara o ATLAS para mudar o plano
- Implementação → o CRONOS dispara o SCOUT para corrigir

---

### 4️⃣ Ao final de cada fase — Validação de conformidade

**Quando:** todos os agentes concluíram as tarefas da fase.
**O CRONOS dispara o code-architect ANTES do selo para:**
- Validar que o código da fase SEGUE os mini-planos
- Identificar desvios (agente improvisou algo diferente do planejado)
- Medir a dívida técnica introduzida na fase

**Resultado:** a fase só é selada se a conformidade estiver OK.

---

### 5️⃣ Quando o ATLAS propõe mudança no contrato — Análise de impacto

**Quando:** o ATLAS quer mudar algo no project-core.
**O CRONOS dispara o code-architect (ou o impact-mapper) para:**
- Analisar o IMPACTO da mudança no código já escrito
- Listar arquivos e módulos que precisarão mudar
- Estimar o esforço e os RISCOS

**Resultado:** o CRONOS leva ao ATLAS o custo da mudança (impacto baixo → segue; alto → pede alternativa).

---

### 6️⃣ Para sequenciamento — Análise de acoplamento

**Quando:** o CRONOS precisa decidir qual agente disparar primeiro na próxima onda.
**O CRONOS dispara o code-architect para:**
- Mapear o acoplamento entre módulos
- Identificar módulos críticos (se quebrarem, quebra tudo)
- Recomendar a ordem de execução pelas dependências reais do código

---

### 7️⃣ Para validar estimativas — Análise de complexidade

**Quando:** um agente diz "essa tarefa vai demorar muito porque X".
**O CRONOS dispara o code-architect para:**
- Ver se a complexidade arquitetural JUSTIFICA o tempo estimado
- Achar forma mais simples (padrão existente, código reutilizável)
- Detectar exagero de engenharia

---

### 8️⃣ Para análise de risco — Pontos críticos

**Quando:** a próxima onda vai mexer em módulos críticos (autenticação, pagamento).
**O CRONOS dispara o code-architect para:**
- Identificar as partes que PODEM QUEBRAR
- Recomendar proteções extras (testes, chaves de funcionalidade, plano de volta atrás)
- Sugerir abordagem incremental

---

### 9️⃣ Durante a execução — Desvio arquitetural

**Quando:** o CRONOS percebe que um agente está demorando muito ou fazendo muitos commits.
**O CRONOS dispara o code-architect para:**
- Verificar se o agente segue o mini-plano ou está improvisando
- Sinalizar se é preciso parar o agente e replanejar

---

### 🔟 Pós-morte de fase — Captura de padrões

**Quando:** fase concluída, antes de arquivar.
**O CRONOS dispara o code-architect para:**
- Gerar o relatório de lições arquiteturais da fase
- Identificar padrões que FUNCIONARAM e anti-padrões que ATRASARAM
- Listar decisões arquiteturais que surgiram durante a execução — o CRONOS as encaminha ao ATLAS como propostas para o project-core (só o ATLAS escreve o project-core)

**Depois do pós-morte — memória entre projetos:**

O CRONOS acrescenta de 3 a 5 lições ao arquivo `~/.delta-11/aprendizados-entre-projetos.md` ao fim de cada ciclo e na Fase 7 (o arquivo é criado pelo `instalar.sh`/`novo-projeto.sh`; se faltar, o CRONOS o cria). Formato de cada lição:

```markdown
## [AAAA-MM-DD] [nome-do-projeto] — [título da lição]
- Situação: [quando isso acontece]
- Faça: [ação correta]
- Nunca faça: [o que evitar]
- Por quê: [justificativa técnica]
- Origem: Fase [N], tarefa [T-XXX]
```

**Regra:** só vão para esse arquivo lições que valem FORA deste projeto. Decisões específicas do projeto ficam no project-core. O ATLAS lê esse arquivo nas Fases 0 e 2 do próximo projeto.

---

## REGRAS DE OURO

1. **build-validator** = SEMPRE após código (Passo 3.5).
2. **contract-tester** = SEMPRE junto com o build-validator (Passo 3.7, os dois em segundo plano) — gera E roda.
3. **code-architect** = SEMPRE ao final da Fase 4 + sob demanda do CRONOS.
4. **verify-app** = SEMPRE antes de deploy.
5. **Revisores de selo** = fresh-reviewer + cold-start-tester (um por `-produto.md`) + qa-ui-tandem, disparados JUNTOS e em segundo plano ao fim de cada fase; o CRONOS espera todos e consolida.
6. **Sub-agentes NUNCA decidem sozinhos** — eles reportam, quem disparou decide.
7. **O CRONOS usa o code-architect para INFORMAR decisões de gestão**; decisão de arquitetura continua sendo do ATLAS.

---

## CHECKLIST ANTES DE AVANÇAR DE FASE

**Toda fase:**
- [ ] Todas as tarefas com `[SHIELD] APROVADO` no activity-log?
- [ ] fresh-reviewer sem problema crítico?
- [ ] cold-start-tester APROVADO para cada `-produto.md`?
- [ ] qa-ui-tandem PASS (se a fase tem interface)?
- [ ] Testes de contrato verdes (hook de fim de fase)?

**Ao final da Fase 4:**
- [ ] build-validator e contract-tester rodaram em CADA tarefa de código?
- [ ] code-architect deu nota B ou superior?
- [ ] Todos os problemas encontrados foram corrigidos?

**Ao final da Fase 4.5 (antes da Fase 5):**
- [ ] SCOUT fez a varredura preventiva completa (Dias 5 e 6)?
- [ ] Todos os problemas encontrados foram corrigidos?

**Ao final da Fase 6 (antes do deploy):**
- [ ] build-validator passou (typecheck, lint, build, testes, audit)?
- [ ] verify-app passou (navegação, fluxos críticos, erros no console)?
- [ ] Sentry ativo com erro de teste capturado?
- [ ] Comandante aprovou o deploy?

Se QUALQUER item faltar, a fase NÃO está concluída.
