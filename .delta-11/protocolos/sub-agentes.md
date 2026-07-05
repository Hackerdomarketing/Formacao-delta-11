# PROTOCOLO DE SUB-AGENTES — FORMAÇÃO Δ-11

## O QUE SÃO SUB-AGENTES

Sub-agentes são agentes especializados que são disparados POR outros agentes para executar tarefas específicas de validação, análise, ou correção. Eles retornam relatórios estruturados e nunca modificam código diretamente.

Diferença chave:
- **Agentes principais** (ATLAS, FRONT, ENGINE, etc.) executam tarefas do kanban e constroem o projeto
- **Sub-agentes** são ferramentas que os agentes principais usam para validar, analisar, ou simplificar

---

## OS 9 SUB-AGENTES

### 1. BUILD VALIDATOR — Validação de Build

**Arquivo:** `.delta-11/sub-agentes/build-validator.md`

**Quando disparar:** OBRIGATÓRIO após TODA mudança de código

**Quem dispara:** ENGINE, BACK, FRONT, PIXEL, FORM, SCOUT (qualquer agente que escreve código)

**O que faz:**
- Roda typecheck, lint, build, testes
- Verifica vulnerabilidades (npm audit)
- Busca secrets expostos no código
- Valida .gitignore

**Output:** Relatório PASS/FAIL + lista de blockers e warnings

**Regra de ouro:** Se FAIL com blockers, NÃO marcar tarefa como concluída até corrigir.

---

### 2. CODE ARCHITECT — Análise Arquitetural

**Arquivo:** `.delta-11/sub-agentes/code-architect.md`

**Quando disparar:**
- Ao final da Fase 4 (OBRIGATÓRIO)
- Durante Phase 2.5 para validar planos (opcional)
- Quando CRONOS precisa de análise arquitetural para tomar decisão (sob demanda)

**Quem dispara:**
- ATLAS (ao final da Fase 4)
- CRONOS (durante Phase 2.5 ou durante execução)

**O que faz:**
- Compara código REAL vs arquitetura PLANEJADA (project-core.md)
- Identifica desvios arquiteturais
- Detecta dívida técnica
- Avalia conformidade com padrões
- Dá score: A/B/C/D/F

**Output:** Relatório com score + problemas estruturais + recomendações de refatoração

**Regra de ouro:** Se score C ou menor, criar tarefas de correção ANTES de avançar de fase.

---

### 3. VERIFY APP — Testes E2E no Browser

**Arquivo:** `.delta-11/sub-agentes/verify-app.md`

**Quando disparar:** OBRIGATÓRIO antes do deploy final (Fase 6)

**Quem dispara:** SHIELD (antes de apresentar relatório final ao comandante) — OU hook UserPromptSubmit automaticamente quando comandante menciona "deploy"/"produção"

**O que faz:**
- Testa aplicação no browser real (Puppeteer se disponível)
- Navega pelos fluxos críticos
- Verifica console errors, network failures
- Captura screenshots de problemas

**Output:** Relatório PASSED/FAILED + screenshots

**Regra de ouro:** Se FAILED, NÃO fazer deploy até corrigir.

---

### 4. CONTRACT TESTER — Geração e Arbitragem de Testes de Contrato

**Arquivo:** `.delta-11/sub-agentes/contract-tester.md`

**Quando disparar (v4.0 — três cenários):**
1. **Geração inicial (manual):** ao final da Fase 2, depois que ATLAS salvou contratos e SHIELD terminou revisão. Disparado pelo SHIELD.
2. **Regeneração automática (via hook):** toda vez que `project-core.md` muda, o hook PostToolUse `.delta-11/hooks/regenerar-contratos.py` dispara automaticamente.
3. **Árbitro de merge (Onda 2):** CRONOS usa os testes gerados por você como juiz objetivo quando há conflito de merge entre worktrees.

**Quem dispara:** SHIELD (cenário 1) · Hook de sistema (cenário 2) · CRONOS (cenário 3 indireto via `npm run test:contracts`)

**O que faz:**
- Converte contratos de `project-core.md` em arquivos de teste executáveis em `tests/contracts/`
- Detecta framework (Vitest, Jest, Pytest, Playwright)
- Gera testes para happy path, validação de obrigatórios, limites de segurança, autenticação, erros de domínio
- **Idempotente:** mesma entrada gera o mesmo output (essencial para hooks)

**Output:** Relatório com número de rotas cobertas, arquivos gerados, contratos incompletos detectados

**Regra de ouro:** Teste de contrato falhando = código violando o combinado. Não ignore.

---

### 5. SCHEMA VALIDATOR — Validação de Migrações de Banco

**Arquivo:** `.delta-11/sub-agentes/schema-validator.md`

**Quando disparar:** OBRIGATÓRIO antes de aplicar qualquer migração em ambiente compartilhado ou produção

**Quem dispara:** VAULT

**O que faz:**
- Valida sintaxe SQL
- Detecta migrações destrutivas sem backup
- Verifica se índices e constraints estão consistentes com o esquema do `project-core.md`
- Alerta sobre locks de tabela em produção

**Output:** Relatório PASS/FAIL + recomendações de ajuste

**Regra de ouro:** Migração é operação irreversível em produção. Sempre validar antes.

---

### 6. IMPACT MAPPER — Mapeamento de Impacto de Mudança de Contrato

**Arquivo:** `.delta-11/sub-agentes/impact-mapper.md`

**Quando disparar:** automaticamente junto com contract-tester no cenário 2 (hook PostToolUse sobre `project-core.md`)

**Quem dispara:** Hook de sistema `.delta-11/hooks/regenerar-contratos.py`

**O que faz:**
- Lê o diff de `project-core.md` (via git ou backup)
- Classifica cada mudança (rota nova, rota removida, campo alterado, tabela alterada, etc.)
- Busca no código-fonte quais arquivos são afetados por cada mudança
- Cruza com `kanban.md` para identificar tarefas invalidadas
- Gera `.delta-11/memoria/impacto-mudanca-[timestamp].md` com plano de correção
- Cria tarefas `[IMPACTO-MUDANCA]` automaticamente no kanban
- Notifica agentes ativos via `.delta-11/ativacoes/impacto-AGENTE.txt`

**Output:** Relatório resumido + arquivos persistidos

**Regra de ouro:** CRONOS revisa o relatório antes de disparar qualquer correção — impact-mapper apenas mapeia, nunca corrige.

---

### 7. FRESH REVIEWER — Revisão Cruzada por Olhos Virgens (v4.0.1)

**Arquivo:** `.delta-11/sub-agentes/fresh-reviewer.md`

**Quando disparar:** OBRIGATÓRIO ao final de cada fase, depois do SHIELD aprovar e ANTES do Protocolo do Viu que Era Bom

**Quem dispara:** CRONOS (único disparador)

**O que faz:**
- Recebe APENAS o path do projeto e a fase atual
- NÃO lê project-core.md, mini-planos, estado de agentes, contratos — é VIRGEM de contexto
- Navega a aplicação como usuário real (via Playwright/Puppeteer/curl)
- Tenta fluxos críticos: cadastro, login, navegação, formulários, casos extremos
- Reporta experiência: o que quebra, o que incomoda, o que parece mal acabado, o que parece genérico

**Output:** Relatório estruturado com status (PASSED/PASSED_COM_RESSALVAS/FAILED) + problemas em 3 níveis (crítico/moderado/pequeno) + recomendação

**Regra de ouro:** o valor do Fresh Reviewer está em NÃO SABER. Ele materializa o P4 sub-etapa 5 da Criação — Revisão Cruzada sem conhecer a intenção. Complementa SHIELD/Code Architect/Contract Tester que validam conformidade; Fresh Reviewer valida EXPERIÊNCIA.

---

### 8. COLD START TESTER — Validação de Suficiência de Handoff (v4.0.3)

**Arquivo:** `.delta-11/sub-agentes/cold-start-tester.md`

**Quando disparar:** OBRIGATÓRIO ao final de cada fase, DEPOIS do Fresh Reviewer aprovar e ANTES do Protocolo do Viu que Era Bom. Uma chamada POR cada `[AGENTE]-produto.md` da fase.

**Quem dispara:** CRONOS (único disparador)

**O que faz:**
- Recebe APENAS o path de UM `[AGENTE]-produto.md` — nada mais
- NÃO lê project-core.md, mini-planos, história, kanban, outros produtos
- Responde 4 perguntas sobre o que existe, o que pode construir em cima, o que NÃO existe, próxima tarefa
- Classifica confiança (ALTA/BAIXA/IMPOSSÍVEL) em cada resposta
- Sinaliza lacunas específicas se houver

**Output:** Relatório com veredito APROVADO/REPROVADO + 4 respostas + lacunas detectadas

**Regra de ouro:** materializa o Mecanismo 4b da Geometria da Criação (Teste do Cold Start). Gênesis 1:2 compacta estado inicial em UMA frase — se o produto aqui não é suficiente para fase nova entender, compactação foi mal feita. Último check antes do selo humano.

---

### 9. TOOL PROVISIONER — Provisionamento de Ferramentas Externas (v5.2)

**Arquivo:** `.delta-11/sub-agentes/tool-provisioner.md`

**Quando disparar:** na Fase 2.4 (entre a Pesquisa Técnica 2.3 e os Mini-planos 2.5) — OBRIGATÓRIO em projeto com integrações externas. Também sob demanda quando uma integração nova entra no projeto (ex: troca de vendor de IA).

**Quem dispara:** CRONOS

**O que faz:**
- Compila o inventário de ferramentas externas (MCPs, chaves de API, contas, variáveis de ambiente, CLIs)
- Classifica cada item: AUTO-CLI (instala sozinho), AUTO-BROWSER (configura via Playwright), CREDENCIAL (pede ao comandante em lote), HUMANO (pagamento/telefone — gera checklist leigo)
- Verifica cada ferramenta com teste REAL (chamada de API mínima, conexão de banco, ping de webhook) — não só "a chave existe"
- Atualiza `.delta-11/memoria/ferramentas-do-projeto.md`

**Output:** Relatório com status por ferramenta (OK/FAIL/PENDENTE-HUMANO) + checklist leigo do que só o comandante pode fazer

**Regra de ouro:** ferramenta listada mas não configurada é promessa, não capacidade. Nenhum agente de execução deve travar por ferramenta não provisionada.

---

## QUANDO CADA SUB-AGENTE É OBRIGATÓRIO (v4.0.3)

| Sub-agente | Frequência | Fase | Disparado por | Obrigatório? |
|------------|-----------|------|---------------|--------------|
| Build Validator | Após cada tarefa de código | Fase 4, 5 | ENGINE, BACK, FRONT, PIXEL, FORM, SCOUT, VAULT | ✅ SIM |
| Contract Tester — geração inicial | Final da Fase 2 | Fase 2 | SHIELD | ✅ SIM |
| Contract Tester — regeneração | Automática sempre que `project-core.md` muda | Qualquer fase | Hook PostToolUse (sistema) | ✅ SIM — impossível falhar |
| Contract Tester — fim de fase | Antes de transição de fase via kanban | Qualquer fase | Hook PreToolUse (sistema) | ✅ SIM — bloqueia transição |
| Contract Tester — antes de deploy | Mensagem com "deploy"/"produção" | Fase 6 | Hook UserPromptSubmit (sistema) | ✅ SIM — bloqueia deploy |
| Contract Tester — por tarefa | Após cada tarefa de código (Passo 3.7) | Fase 4 | Agente de código | ✅ SIM |
| Contract Tester — ao corrigir bug | Após cada correção do SCOUT | Fase 4, 5, 6 | SCOUT | ✅ SIM |
| Contract Tester — fim de onda | Quando CRONOS fecha uma onda | Fase 4 | CRONOS | ✅ SIM |
| Contract Tester — árbitro merge | Durante merge de worktrees (Onda 2) | Fase 4 | CRONOS (indireto) | ✅ SIM — Onda 2 |
| Impact Mapper | Automática sempre que `project-core.md` muda | Qualquer fase | Hook PostToolUse (sistema) | ✅ SIM — impossível falhar |
| Code Architect | Final de fase + sob demanda | Final da Fase 4 | CRONOS | ✅ SIM |
| Schema Validator | Antes de aplicar migração | Fase 3+ | VAULT | ✅ SIM |
| Verify App | Antes de deploy | Fase 6 | SHIELD + Hook UserPromptSubmit | ✅ SIM |
| Fresh Reviewer (v4.0.1) | Final de cada fase, antes do selo humano | Todas as fases após build | CRONOS | ✅ SIM — Revisão Cruzada P4/5 |
| Cold Start Tester (v4.0.3) | Final de cada fase, após Fresh Reviewer, antes do selo — 1 por agente | Todas as fases com produto | CRONOS | ✅ SIM — Mecanismo 4b da Criação |
| Tool Provisioner (v5.2) | Fase 2.4 + quando integração nova entra | Fase 2.4 | CRONOS | ✅ SIM — se há integrações externas |

---

## INTEGRAÇÃO COM WORKTREE (v4.0 Onda 2)

A partir da Onda 2, cada agente de execução trabalha em uma worktree isolada. Isso afeta COMO os sub-agentes são disparados:

- **build-validator, contract-tester:** o agente dispara dentro da sua própria worktree, usando path relativo para arquivos de código. O resultado volta para o próprio agente. NÃO disparados por outros agentes.
- **code-architect:** disparado pelo CRONOS a partir do repo principal. Lê código das worktrees ativas (via `git worktree list`) para ter visão consolidada. Produz relatório único cobrindo todas.
- **impact-mapper:** disparado pelo hook PostToolUse no repo principal quando `project-core.md` muda. Como a mudança em project-core é compartilhada, o impact-mapper precisa olhar código de todas as worktrees ativas + main. Pode usar `git worktree list` para descobrir branches e `git show <branch>:<path>` para ler arquivos de worktrees irmãs.
- **schema-validator:** disparado pelo VAULT dentro da própria worktree.
- **verify-app:** disparado pelo SHIELD no repo principal DEPOIS do merge da onda — testa o estado consolidado.
- **Contract Tester como árbitro de merge:** ver `.delta-11/protocolos/merge-guiado-contratos.md`. CRONOS roda os testes em versões candidatas quando há conflito, não invoca o sub-agente diretamente.

**Regra geral:** sub-agentes herdam o working directory do agente que os dispara. Se o disparo acontece dentro de uma worktree, ele roda no contexto dessa worktree. Se acontece no repo principal, roda no contexto do repo principal.

---

## CODE ARCHITECT + CRONOS — 10 CASOS DE USO

O Code Architect é especialmente útil para o CRONOS em projetos de alta complexidade. Aqui estão os 10 casos de uso:

### 1️⃣ ANTES da Phase 2.5 — Análise do Estado Atual

**Quando:** Projeto em andamento (não zero-to-one), antes dos agentes planejarem
**CRONOS dispara Code Architect para:**
- Analisar código EXISTENTE antes dos agentes planejarem
- Gerar relatório de conformidade vs project-core.md
- Identificar dívida técnica que precisa ser paga ANTES de novas features
- Mapear acoplamentos críticos que vão afetar o planejamento

**Resultado:** Agentes planejam com informação REAL do estado do código.

---

### 2️⃣ Durante Phase 2.5 — Validação de Planos

**Quando:** Agentes entregaram `*-plan.md`, CRONOS está revisando
**CRONOS dispara Code Architect para:**
- Analisar se os planos propostos SEGUEM os padrões do project-core.md
- Identificar conflitos arquiteturais ANTES de aprovar
- Detectar abstrações prematuras ou faltantes nos planos
- Validar que os planos respeitam as zonas de trabalho

**Resultado:** CRONOS aprova planos sabendo que são arquiteturalmente sólidos.

---

### 3️⃣ Quando Agente Reporta Bloqueio — Diagnóstico Arquitetural

**Quando:** ENGINE diz "não consigo implementar essa rota porque [razão]"
**CRONOS dispara Code Architect para:**
- Diagnosticar se o bloqueio é ARQUITETURAL (falta infraestrutura, dependência circular) ou IMPLEMENTAÇÃO (bug simples)
- Se arquitetural → CRONOS escala para ATLAS mudar o plano
- Se implementação → CRONOS escala para SCOUT corrigir

**Resultado:** CRONOS toma decisão informada sobre como desbloquear.

---

### 4️⃣ Ao Final de Cada Fase — Validação de Conformidade

**Quando:** Todos os agentes concluíram suas tarefas da Fase N
**CRONOS dispara Code Architect ANTES de aprovar transição para:**
- Validar que o código escrito na fase SEGUE os planos aprovados
- Identificar desvios (agente improvisou algo diferente do planejado)
- Medir dívida técnica introduzida na fase
- Garantir que a próxima fase vai começar com base sólida

**Resultado:** CRONOS só aprova transição de fase se conformidade estiver OK.

---

### 5️⃣ Quando ATLAS Propõe Mudança no Contrato — Análise de Impacto

**Quando:** ATLAS quer mudar algo no project-core.md
**CRONOS dispara Code Architect para:**
- Analisar IMPACTO da mudança no código já escrito
- Listar quais arquivos/módulos precisarão ser alterados
- Estimar esforço de refatoração
- Identificar RISCOS (o que pode quebrar)

**Resultado:** CRONOS decide se aprova a mudança (impacto baixo) ou pede alternativa.

---

### 6️⃣ Para Decisão de Sequenciamento — Análise de Acoplamento

**Quando:** CRONOS precisa decidir qual agente disparar primeiro na próxima fase
**CRONOS dispara Code Architect para:**
- Mapear acoplamento entre módulos (quais arquivos dependem de quais)
- Identificar módulos críticos (se quebrarem, quebra tudo)
- Recomendar ordem de execução baseada em dependências reais do código

**Resultado:** CRONOS dispara agentes na ordem ÓTIMA.

---

### 7️⃣ Para Validar Estimativas — Análise de Complexidade

**Quando:** Agente diz "essa tarefa vai demorar muito porque X"
**CRONOS dispara Code Architect para:**
- Analisar se a complexidade arquitetural JUSTIFICA o tempo estimado
- Identificar se há forma mais simples de fazer (padrão existente, código reutilizável)
- Detectar se o agente está overengineering

**Resultado:** CRONOS questiona estimativa se Code Architect disser "isso pode ser mais simples".

---

### 8️⃣ Para Análise de Risco — Mapeamento de Pontos Críticos

**Quando:** CRONOS sabe que a próxima fase vai mexer em módulos críticos (autenticação, pagamento)
**CRONOS dispara Code Architect para:**
- Identificar partes críticas do código que PODEM QUEBRAR
- Recomendar proteções extras (testes, feature flags, rollback plan)
- Sugerir abordagem incremental (fazer em etapas pequenas vs big bang)

**Resultado:** CRONOS prepara plano de mitigação de risco ANTES de autorizar execução.

---

### 9️⃣ Durante Execução — Monitoramento de Drift Arquitetural

**Quando:** CRONOS percebe que agente está demorando muito ou fazendo muitos commits
**CRONOS dispara Code Architect para:**
- Verificar se o agente está seguindo o plano ou improvisando
- Detectar drift arquitetural (código escrito diferente do planejado)
- Sinalizar se precisa parar o agente e replanejar

**Resultado:** CRONOS intervém ANTES do agente terminar uma implementação errada.

---

### 🔟 Pós-Mortem de Fase — Captura de Padrões

**Quando:** Fase concluída, antes de arquivar
**CRONOS dispara Code Architect para:**
- Gerar relatório de lições arquiteturais aprendidas na fase
- Identificar padrões que FUNCIONARAM (reutilizar nas próximas fases)
- Identificar anti-patterns que ATRASARAM (evitar nas próximas fases)
- Atualizar project-core.md com decisões arquiteturais que surgiram durante execução

**Resultado:** CRONOS alimenta memória institucional do projeto.

**APÓS PÓS-MORTEM — EXPORTAR PADRÕES UNIVERSAIS PARA A INTELIGÊNCIA PROGRESSIVA:**

Quando o Code Architect identificar padrões que funcionam em QUALQUER projeto (não só neste), CRONOS deve exportar para a Inteligência Progressiva central:

```bash
python3 ~/.claude/skills/inteligencia-progressiva/scripts/capturar.py --json '{
  "dominio": "[inferir do stack: supabase, extensoes-chrome, nextjs, etc.]",
  "tipo": "situacao",
  "titulo": "[nome do padrão]",
  "situacao_descricao": "[quando usar]",
  "se": "[condição]",
  "faca": "[ação correta]",
  "nunca_faca": "[o que evitar]",
  "porque": "[justificativa técnica]",
  "tags": ["[tags relevantes]"]
}'
```

**Regra:** Só exportar padrões que sejam UNIVERSAIS (funcionam fora deste projeto). Decisões específicas do projeto ficam apenas no project-core.md.

**Evidência obrigatória:** Incluir nome do projeto, fase e tarefa onde o padrão surgiu.

---

## COMO DISPARAR UM SUB-AGENTE

Use a ferramenta `Task` com `subagent_type="general-purpose"` e passe o conteúdo do arquivo do sub-agente como prompt:

```markdown
1. Leia o arquivo `.delta-11/sub-agentes/[NOME-DO-SUB-AGENTE].md`
2. Use Task tool com:
   - subagent_type: "general-purpose"
   - description: "Disparando [NOME] para [propósito]"
   - prompt: [conteúdo do arquivo] + contexto específico do projeto
3. Analise o relatório retornado
4. Tome ação baseada no resultado (corrigir, aprovar, replanejar)
```

**IMPORTANTE:** Sub-agentes retornam relatórios estruturados. O agente que disparou é responsável por AGIR baseado no relatório.

---

## REGRAS DE OURO

1. **Build Validator** = SEMPRE após código
2. **Code Architect** = SEMPRE ao final da Fase 4 + sob demanda do CRONOS
3. **Verify App** = SEMPRE antes de deploy

4. **Sub-agentes NUNCA decidem sozinhos** — eles reportam, o agente que disparou decide
5. **CRONOS usa Code Architect para INFORMAR decisões de gestão**
6. **ATLAS usa Code Architect para validar conformidade arquitetural**

---

## CHECKLIST ANTES DE AVANÇAR DE FASE

Antes de marcar qualquer fase como concluída, verificar:

**Ao final da Fase 4:**
- [ ] Build Validator rodou após CADA tarefa de código?
- [ ] Code Architect rodou e deu score B ou superior?
- [ ] SCOUT fez varredura preventiva completa?
- [ ] Todos os problemas encontrados foram corrigidos?

**Ao final da Fase 6 (antes de deploy):**
- [ ] Build Validator passou (typecheck, lint, build, tests, audit)?
- [ ] Verify App passou (navegação, fluxos críticos, console errors)?
- [ ] Comandante aprovou o deploy?

Se QUALQUER item faltar, a fase NÃO está concluída.
