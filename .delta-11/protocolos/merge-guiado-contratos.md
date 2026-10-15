# PROTOCOLO DE MERGE GUIADO POR CONTRATOS — FORMAÇÃO Δ-11 (v6.4)

## Contexto

Cada agente de execução (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT) trabalha em uma **worktree isolada** — uma cópia do repositório em uma branch própria. Isso elimina conflitos em tempo de execução (dois agentes editando o mesmo arquivo ao mesmo tempo), mas cria um momento crítico: **o merge no final de cada onda**, quando o CRONOS combina as mudanças de todas as worktrees na branch principal.

Este protocolo define como o CRONOS conduz esse merge usando os testes de contrato como árbitro objetivo quando houver conflito. O CRONOS roda sempre na pasta principal, sem worktree.

## Princípio fundamental

**Separação clara entre o que é isolado e o que é compartilhado:**

| Fica na pasta principal (compartilhado) | Fica na worktree (isolado por agente) |
|---|---|
| `.delta-11/kanban.md` + `kanban-data.js` (só o CRONOS escreve) | Código-fonte (`src/`, `app/`, etc.) |
| `.delta-11/memoria/project-core.md` e as fatias em `memoria/project-core/` (só o ATLAS escreve) | Testes gerados pelo agente na própria worktree (`tests/contracts/` do que ele mudou) |
| `.delta-11/memoria/[AGENTE]-produto.md` e `[AGENTE]-historia.md` | Migrations que o agente está montando (até o merge) |
| `.delta-11/planos/` (mini-planos) | Qualquer outro arquivo de implementação |
| `.delta-11/ativacoes/` (ACKs, avisos, pulsos) | |
| `.delta-11/locks/` (travas) | |
| `.delta-11/logs/` e `.delta-11/activity-log.md` | |
| `.delta-11/.contract-hash` e `.delta-11/hooks/` | |
| `.delta-11/scratch/` (temporários, inclusive os do merge) | |

Consequência prática: o agente, na worktree dele, acessa os arquivos compartilhados pelo **caminho absoluto da pasta principal** que o CRONOS passou no prompt — nunca pelo caminho relativo da worktree. Se usar o relativo, estará lendo ou escrevendo uma cópia invisível aos outros.

## Fluxo do merge

### 1. Agente termina trabalho na worktree

Quando um agente finaliza as tarefas da onda atual, ele segue a rotina de finalização (ver `comunicacao.md`, seção 4):

1. Atualiza `[NOME]-produto.md` e `[NOME]-historia.md` na pasta principal (Passos 1a e 1b).
2. Faz a autocrítica e dispara JUNTOS, em segundo plano, o `build-validator` (3.5) e o `contract-tester` (3.7, gera E roda os testes do que mudou); espera os dois.
3. **Commita** na branch da worktree.
4. Envia `SendMessage` ao CRONOS (3.8) com o payload curto — a revisão do SHIELD é feita por onda:
   ```json
   {
     "agente": "ENGINE",
     "worktree": "<caminho da worktree>",
     "branch": "delta-11/engine-onda-2",
     "tarefas_concluidas": ["T-042", "T-043", "T-051"],
     "arquivos_modificados": ["src/app/api/users/route.ts", "..."],
     "build_validator": "PASS",
     "contract_tests": "PASS",
     "autocritica": ".delta-11/logs/autocritica/<arquivo>.md"
   }
   ```
5. Libera as próprias travas (3.9).

O agente NÃO escreve no kanban e NÃO faz merge. Quando os executores da onda terminam, o CRONOS dispara UM SHIELD para a onda inteira (onda grande: vários SHIELD em paralelo, um por zona), registra o resultado de cada tarefa no kanban e orquestra o merge.

### 2. CRONOS recebe e tenta merge automático — merge por ONDA, só tarefas APROVADAS (v6.4)

O merge é feito **uma vez por onda**, depois da revisão do SHIELD da onda, e **só entra a branch cujas tarefas têm TODAS a linha `[SHIELD] APROVADO T-XXX [AGENTE]`** no activity-log:
- **Branch toda aprovada** → entra no merge desta onda.
- **Branch com alguma tarefa REPROVADA** → fica FORA deste merge, sem travar as outras. A correção vira tarefa na próxima vaga livre (o CRONOS retoma o mesmo executor por `SendMessage`, na mesma worktree e branch, ou dispara um novo sobre ela); depois do APROVADO, a branch entra no merge seguinte.
- **Pipeline:** enquanto o SHIELD revisa a onda N e o CRONOS faz este merge, a onda N+1 já pode estar rodando nas tarefas que não dependem da onda N. As worktrees dela nasceram antes deste merge — por isso só vão para o pipeline tarefas SEM dependência de código da onda N, e o merge delas usa o mesmo árbitro abaixo.

Passos:

1. O CRONOS trabalha na pasta principal (nunca tenta merge dentro de uma worktree).
2. Para cada worktree APROVADA da onda, na ordem do caminho crítico:
   ```bash
   git merge --no-ff delta-11/[nome-da-branch]
   ```
3. Se o Git fizer merge automático sem conflito → sucesso. Próxima worktree.
4. Se o Git detectar conflito → **entram os testes de contrato como árbitro** (próxima seção).

### 3. Resolução de conflito pelos testes de contrato

Quando `git merge` retorna conflito, o CRONOS executa:

**Passo A — Identificar arquivos em conflito:**
```bash
git diff --name-only --diff-filter=U
```

**Passo B — Criar duas versões candidatas:**
- **Candidata 1 — "nossa":** a versão atual da branch principal (antes do merge)
- **Candidata 2 — "deles":** a versão da worktree sendo mergeada

As cópias temporárias ficam em `.delta-11/scratch/merge/` (nunca na pasta temporária do sistema — ela some sem aviso e mistura projetos; a `scratch/` expira em 7 dias):
```bash
MERGE_SCRATCH_DIR=".delta-11/scratch/merge/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$MERGE_SCRATCH_DIR"
git show :2:arquivo > "$MERGE_SCRATCH_DIR/candidata-nossa.ext"
git show :3:arquivo > "$MERGE_SCRATCH_DIR/candidata-deles.ext"
```

**Passo C — Rodar os testes de contrato em cada candidata:**

Para cada candidata, aplica-a temporariamente, roda `npm run test:contracts` (ou equivalente) e registra o resultado.

```bash
# Candidata "nossa"
cp "$MERGE_SCRATCH_DIR/candidata-nossa.ext" arquivo
result_ours=$(npm run test:contracts && echo PASS || echo FAIL)

# Candidata "deles"
cp "$MERGE_SCRATCH_DIR/candidata-deles.ext" arquivo
result_theirs=$(npm run test:contracts && echo PASS || echo FAIL)
```

**Passo D — Decidir com base em 4 casos:**

| Caso | Nossa | Deles | Decisão |
|---|---|---|---|
| 1 | PASS | FAIL | Manter "nossa". Descartar "deles". `git checkout --ours`. |
| 2 | FAIL | PASS | Manter "deles". `git checkout --theirs`. |
| 3 | PASS | PASS | Ambas respeitam o contrato: o CRONOS dispara o agente dono da branch (com as duas versões) para produzir uma versão única que mantém os dois comportamentos. Se a escolha depender de arquitetura ou contrato, o CRONOS dispara o ATLAS. |
| 4 | FAIL | FAIL | Ambas violam o contrato: é erro de dados (categoria B). O CRONOS dispara o SCOUT, seguindo `correcao-de-erros.md` (3 tentativas; depois um novo SCOUT com contexto limpo; depois de 6 falhas, o ATLAS). |

Nos casos 3 e 4, o CRONOS pausa o merge e registra `.delta-11/memoria/conflito-merge-[AAAAMMDDTHHMMSSZ].md` com o diff lado a lado + os resultados dos testes. Esse arquivo é o que ele passa no prompt do agente que vai resolver. O CRONOS só leva o conflito ao comandante se a escolha for uma **decisão de negócio** (ex.: duas regras de preço diferentes e o project-core não diz qual vale) — e aí apresenta as duas opções em linguagem simples, com o que cada uma significa para o produto.

### 4. Finalização do merge

Depois de resolver todos os conflitos:
1. `git add` nos arquivos resolvidos
2. `git commit` (commit de merge)
3. Rodar `npm run test:contracts` **uma vez no resultado do merge** — deve passar
4. Se passar, a onda está consolidada (as branches aprovadas dela). Se não passar, reverter o merge e tratar como caso 4 (SCOUT, via `correcao-de-erros.md`)
5. O activity-log recebe o registro do merge + decisões tomadas (formato único: `- [AAAA-MM-DDTHH:MM:SSZ] [merge-guiado] [CRONOS] mensagem`)
6. Apagar as worktrees mergeadas (as que ficaram de fora por reprovação continuam até o merge seguinte) e a pasta temporária do merge:
   ```bash
   git worktree remove delta-11-[agente]-[onda]
   git branch -d delta-11/[agente]-[onda]
   [ -n "$MERGE_SCRATCH_DIR" ] && ls "$MERGE_SCRATCH_DIR" && rm -r "$MERGE_SCRATCH_DIR"
   ```
7. O CRONOS atualiza o kanban.

## Regra anti-acúmulo aplicada ao merge

**O CRONOS NUNCA edita código para resolver conflito.** Se a decisão dos testes de contrato for clara (casos 1 e 2), o CRONOS aplica mecanicamente. Se não for clara (casos 3 e 4), o CRONOS dispara quem deve resolver — nunca inventa solução própria. Editar código é trabalho dos agentes de execução.

## Cross-platform

Este protocolo usa apenas `git`, `cp`, comandos de shell padrão e `npm run`/`pytest`. Funciona em:
- macOS e Linux (bash nativo)
- Windows (via Git Bash, WSL, ou PowerShell com os mesmos comandos)

O script de merge automatizado, se implementado, deve ser em Python para garantir execução idêntica em todos os sistemas.

## Mudança de contrato durante a onda

Se durante a onda o ATLAS alterou o project-core:
1. O hook `regenerar-contratos.py` apenas calculou o hash novo e gravou `.delta-11/ativacoes/contratos-desatualizados.txt` (hash + hora). Ele não dispara nada.
2. Quando o ATLAS terminou as edições, o CRONOS rodou o `contract-tester` UMA vez (testes regenerados e rodados) e apagou o aviso.
3. Se havia código já escrito, o CRONOS pediu o `impact-mapper`, que gravou `.delta-11/memoria/impacto-mudanca-[timestamp].md` com tarefas PROPOSTAS. O CRONOS aprovou, escreveu as tarefas `[IMPACTO-MUDANCA]` no kanban e avisou cada agente com `.delta-11/ativacoes/contrato-alterado-[AGENTE].txt`.

No fim do merge, o CRONOS confere: se `contratos-desatualizados.txt` ainda existe, roda o contract-tester antes de tudo; se alguma tarefa `[IMPACTO-MUDANCA]` ainda está aberta, bloqueia o avanço para a próxima fase até ela ser resolvida — o código pode estar mergeado mas ainda não alinhado com o contrato novo.

## Worktree é sempre ligada

Para executores, worktree é **sempre ligada**. Não há opção de desligar. Isso simplifica o comportamento do CRONOS: ele sempre assume que cada executor está em worktree, sempre faz merge, sempre usa os testes de contrato como árbitro.

Mesmo em projetos de BAIXA complexidade (FRONT acumulando PIXEL+FORM e BACK acumulando ENGINE+VAULT), em que há só 2 ou 3 worktrees e o merge é trivial, o protocolo é o mesmo.

## Bugs conhecidos da Anthropic

Os problemas #37549 e #39886 do Claude Code podem fazer `isolation: "worktree"` falhar silenciosamente. O modelo duplo (arquivos compartilhados na pasta principal + código na worktree) reduz o impacto:

- O hook `guarda-worktree.py` bloqueia edição de código na pasta principal enquanto houver worktrees de execução ativas — o sintoma exato do #39886.
- Se a worktree falhar e o código parar na pasta principal, o kanban e o `-produto.md` ainda mostram quem estava fazendo o quê → detectável.
- O SHIELD conferindo o hash do project-core pega divergências.
- O CRONOS verifica periodicamente `git worktree list` para detectar worktrees que "sumiram".

Se qualquer sinal de falha de worktree aparecer, o CRONOS pausa novas ondas, registra o diagnóstico no activity-log e segue a cadeia de tentativas do CLAUDE.md. O comandante só é avisado se houver risco de perda de código.
