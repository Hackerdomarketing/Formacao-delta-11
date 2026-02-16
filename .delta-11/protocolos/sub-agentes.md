# PROTOCOLO DE SUB-AGENTES — FORMAÇÃO Δ-11

## O QUE SÃO SUB-AGENTES

Sub-agentes são agentes especializados que são disparados POR outros agentes para executar tarefas específicas de validação, análise, ou correção. Eles retornam relatórios estruturados e nunca modificam código diretamente (exceto Code Simplifier).

Diferença chave:
- **Agentes principais** (ATLAS, FRONT, ENGINE, etc.) executam tarefas do kanban e constroem o projeto
- **Sub-agentes** são ferramentas que os agentes principais usam para validar, analisar, ou simplificar

---

## OS 4 SUB-AGENTES

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

### 2. CODE SIMPLIFIER — Simplificação de Código

**Arquivo:** `.delta-11/sub-agentes/code-simplifier.md`

**Quando disparar:** OBRIGATÓRIO ao final de cada fase de desenvolvimento

**Quem dispara:**
- Último agente a terminar a Fase 4
- SCOUT ao final da Fase 5 (se ainda houver código para simplificar)

**O que faz:**
- Simplifica código mantendo funcionalidade idêntica
- Remove duplicação, variáveis genéricas, condicionais aninhadas
- Renomeia para clareza
- Remove imports não usados

**Output:** Relatório de simplificações + testes antes/depois

**Regra de ouro:** NUNCA disparar durante desenvolvimento ativo — só ao final de fases completas.

---

### 3. CODE ARCHITECT — Análise Arquitetural

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

### 4. VERIFY APP — Testes E2E no Browser

**Arquivo:** `.delta-11/sub-agentes/verify-app.md`

**Quando disparar:** OBRIGATÓRIO antes do deploy final (Fase 6)

**Quem dispara:** SHIELD (antes de apresentar relatório final ao comandante)

**O que faz:**
- Testa aplicação no browser real (Puppeteer se disponível)
- Navega pelos fluxos críticos
- Verifica console errors, network failures
- Captura screenshots de problemas

**Output:** Relatório PASSED/FAILED + screenshots

**Regra de ouro:** Se FAILED, NÃO fazer deploy até corrigir.

---

## QUANDO CADA SUB-AGENTE É OBRIGATÓRIO

| Sub-agente | Frequência | Fase | Disparado por | Obrigatório? |
|------------|-----------|------|---------------|--------------|
| Build Validator | Após cada tarefa de código | Fase 4, 5 | ENGINE, BACK, FRONT, PIXEL, FORM, SCOUT | ✅ SIM |
| Code Simplifier | Final de fase | Final da Fase 4 | Último agente a terminar Fase 4 | ✅ SIM |
| Code Architect | Final de fase | Final da Fase 4 | ATLAS ou CRONOS | ✅ SIM |
| Verify App | Antes de deploy | Fase 6 | SHIELD | ✅ SIM |

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
2. **Code Simplifier** = SEMPRE ao final de fase (nunca no meio)
3. **Code Architect** = SEMPRE ao final da Fase 4 + sob demanda do CRONOS
4. **Verify App** = SEMPRE antes de deploy

5. **Sub-agentes NUNCA decidem sozinhos** — eles reportam, o agente que disparou decide
6. **CRONOS usa Code Architect para INFORMAR decisões de gestão**
7. **ATLAS usa Code Architect para validar conformidade arquitetural**
8. **SCOUT usa Code Simplifier para limpar código ao final de fases**

---

## CHECKLIST ANTES DE AVANÇAR DE FASE

Antes de marcar qualquer fase como concluída, verificar:

**Ao final da Fase 4:**
- [ ] Build Validator rodou após CADA tarefa de código?
- [ ] Code Simplifier rodou ao final da fase?
- [ ] Code Architect rodou e deu score B ou superior?
- [ ] SCOUT fez varredura preventiva completa?
- [ ] Todos os problemas encontrados foram corrigidos?

**Ao final da Fase 6 (antes de deploy):**
- [ ] Build Validator passou (typecheck, lint, build, tests, audit)?
- [ ] Verify App passou (navegação, fluxos críticos, console errors)?
- [ ] Comandante aprovou o deploy?

Se QUALQUER item faltar, a fase NÃO está concluída.
