# PROTOCOLO DE MERGE GUIADO POR CONTRATOS — FORMAÇÃO Δ-11 (v4.0 Onda 2)

## Contexto

A partir da Onda 2, cada agente de execução (ENGINE, BACK, FRONT, PIXEL, FORM, VAULT, SCOUT) trabalha em uma **worktree isolada** — uma cópia do repositório em uma branch própria. Isso elimina conflitos em tempo de execução (dois agentes editando o mesmo arquivo simultaneamente), mas cria um novo momento crítico: **o merge no final de cada onda**, quando o CRONOS precisa combinar as mudanças de todas as worktrees na branch principal.

Este protocolo define como o CRONOS conduz esse merge usando o `contract-tester` como árbitro objetivo quando houver conflito.

## Princípio fundamental

**Separação clara entre o que é isolado e o que é compartilhado:**

| Fica no repo principal (compartilhado) | Fica na worktree (isolado por agente) |
|---|---|
| `.delta-11/kanban.md` + `kanban-data.js` | Código fonte (`src/`, `app/`, etc.) |
| `.delta-11/memoria/project-core.md` | Arquivos de teste gerados (`tests/contracts/` gerado pelo agente na própria worktree) |
| `.delta-11/memoria/[AGENTE]-estado.md` | Migrações específicas que o agente está montando (até serem aprovadas) |
| `.delta-11/ativacoes/ack-*.txt` | Qualquer outro arquivo de implementação |
| `.delta-11/activity-log.md` | |
| `.delta-11/.contract-hash` | |
| `.delta-11/hooks/` | |

Consequência prática: o agente, na worktree dele, acessa `kanban.md` e `project-core.md` pelo **path absoluto do repo principal** — nunca pelo path relativo da worktree. Se usar path relativo, estará lendo/escrevendo no kanban clone dentro da worktree dele, invisível aos outros agentes.

## Fluxo do merge

### 1. Agente termina trabalho na worktree

Quando um agente finaliza todas as tarefas da onda atual:

1. Roda sua cadeia de sub-agentes (build-validator, contract-tester)
2. Atualiza `kanban.md` no repo principal (marca tarefas como REVISÃO ou CONCLUÍDO)
3. Atualiza seu arquivo de estado no repo principal
4. **Commita** na branch da worktree
5. Envia `SendMessage` para o CRONOS com payload:
   ```
   {
     "agente": "ENGINE",
     "worktree": "delta-11-engine-onda-2",
     "branch": "delta-11/engine-onda-2",
     "tarefas_concluidas": ["T-042", "T-043", "T-051"],
     "arquivos_modificados": ["src/app/api/users/route.ts", "..."],
     "contract_tests": "PASSED"
   }
   ```

O agente NÃO tenta fazer merge sozinho. CRONOS orquestra o merge.

### 2. CRONOS recebe e tenta merge automático

Quando o CRONOS tem todas as worktrees da onda prontas (todos os `SendMessage` recebidos):

1. CRONOS navega para o repo principal (nunca tenta merge dentro de uma worktree)
2. Para cada worktree na ordem do caminho crítico:
   ```bash
   git merge --no-ff delta-11/[nome-da-branch]
   ```
3. Se o Git fizer merge automático sem conflito → sucesso. Próxima worktree.
4. Se o Git detectar conflito → **entra o árbitro contract-tester** (próxima seção).

### 3. Resolução de conflito via contract-tester

Quando `git merge` retorna conflito, CRONOS executa:

**Passo A — Identificar arquivos em conflito:**
```bash
git diff --name-only --diff-filter=U
```

**Passo B — Criar duas versões candidatas:**
- **Candidata 1 — "nossa":** a versão atual do repo principal (antes do merge)
- **Candidata 2 — "deles":** a versão da worktree sendo mergeada

Para cada arquivo em conflito, cria cópias temporárias:
```bash
git show :2:arquivo > /tmp/candidata-nossa.ext
git show :3:arquivo > /tmp/candidata-deles.ext
```

**Passo C — Rodar contract-tester em cada candidata:**

Para cada candidata, aplica-a temporariamente, roda `npm run test:contracts` (ou equivalente), e registra resultado.

```bash
# Candidata "nossa"
cp /tmp/candidata-nossa.ext arquivo
resultado_nossa=$(npm run test:contracts && echo PASS || echo FAIL)

# Candidata "deles"
cp /tmp/candidata-deles.ext arquivo
resultado_deles=$(npm run test:contracts && echo PASS || echo FAIL)
```

**Passo D — Decidir com base em 4 casos:**

| Caso | Nossa | Deles | Decisão |
|---|---|---|---|
| 1 | PASS | FAIL | Manter "nossa". Descartar "deles". `git checkout --ours`. |
| 2 | FAIL | PASS | Manter "deles". `git checkout --theirs`. |
| 3 | PASS | PASS | **Escalar para comandante** — ambas respeitam o contrato, humano decide semanticamente |
| 4 | FAIL | FAIL | **Escalar para comandante** — ambas violam o contrato, precisa revisar e corrigir |

Escalar significa: CRONOS pausa o merge, cria `.delta-11/memoria/conflito-merge-[timestamp].md` com diff lado a lado + resultados dos testes, e apresenta ao comandante no formato:

```
🔴 CONFLITO DE MERGE — DECISÃO HUMANA NECESSÁRIA

Arquivo: src/app/api/users/route.ts
Caso: 3 (ambas versões passam nos testes de contrato)

Versão A (main) passa: SIM
Versão B (engine-onda-2) passa: SIM

Qual versão manter?
  A — diff em: .delta-11/memoria/conflito-merge-20260417T143000Z.md
  B — diff em: .delta-11/memoria/conflito-merge-20260417T143000Z.md

Digite: A, B, ou manual (para editar à mão)
```

### 4. Finalização do merge

Depois de resolver todos os conflitos:
1. `git add` nos arquivos resolvidos
2. `git commit` (commit de merge)
3. Rodar `npm run test:contracts` **uma vez no resultado do merge** — deve passar
4. Se passar, a onda está consolidada. Se não passar, reverter e escalar ao comandante
5. Atualizar `.delta-11/activity-log.md` com registro do merge + decisões tomadas
6. Deletar worktrees concluídas:
   ```bash
   git worktree remove delta-11-[agente]-[onda]
   git branch -d delta-11/[agente]-[onda]
   ```

## Regra anti-acúmulo aplicada ao merge

**CRONOS NUNCA deve editar código para resolver conflito.** Se a decisão do contract-tester for clara (Casos 1 e 2), CRONOS aplica mecanicamente. Se não for clara (Casos 3 e 4), CRONOS escala — nunca inventa solução própria. Editar código é trabalho dos agentes de execução.

## Cross-platform

Este protocolo usa apenas `git`, `cp`, comandos de shell padrão e `npm run`/`pytest`. Funciona em:
- macOS e Linux (bash nativo)
- Windows (via Git Bash, WSL, ou PowerShell com os mesmos comandos)

O script de merge automatizado, se implementado, deve ser em Python para garantir execução idêntica em todos os SOs.

## Integração com impact-mapper

Se durante a onda o ATLAS alterou `project-core.md` (gerando `impacto-mudanca-*.md`), o CRONOS verifica no final do merge se alguma tarefa `[IMPACTO-MUDANCA]` ainda está aberta. Se sim, bloqueia o avanço para próxima fase até elas serem resolvidas — o código pode estar mergeado mas ainda não alinhado com o contrato novo.

## Quando worktree é opcional

A partir da Onda 2 da v4.0, worktree é **sempre ligado**. Não há opção de desligar. Isso simplifica o comportamento do CRONOS: ele sempre assume que cada agente está em worktree, sempre faz merge, sempre usa contract-tester como árbitro.

Exceção única: em projetos de baixa complexidade com FRONT acumulando PIXEL+FORM e BACK acumulando ENGINE+VAULT, o número de worktrees é pequeno (geralmente 2-3), o merge é trivial, mas o protocolo continua o mesmo.

## Bugs conhecidos da Anthropic

Issues #37549 e #39886 do Claude Code podem fazer `isolation: worktree` falhar silenciosamente. O modelo duplo (kanban compartilhado + worktree isolado) mitiga o impacto:

- Se worktree falhar silenciosamente e o código for parar no repo principal, o kanban ainda mostra quem estava fazendo o quê → detectável
- O hook PostToolUse continua rodando independente de worktree funcionar ou não → contract-tester continua regenerando
- SHIELD verificando o hash de `project-core.md` pega divergências
- CRONOS verifica periodicamente `git worktree list` para detectar worktrees que "sumiram"

Se qualquer sinal de falha do worktree aparecer, CRONOS escala ao comandante e pausa novas ondas até diagnóstico.
