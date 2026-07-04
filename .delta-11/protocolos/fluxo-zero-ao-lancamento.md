# FLUXO DO ZERO AO LANÇAMENTO — FORMAÇÃO Δ-11

## AS 7 FASES OBRIGATÓRIAS

Estas fases são executadas em ordem. Nenhuma fase pode ser pulada.

---

### FASE 0 — DESCOBERTA E DESIGN

**Quem:** ATLAS (como facilitador) + Comandante
**Janelas:** 1

Esta é a fase mais importante do projeto. Antes de classificar, arquitetar, ou escrever uma única linha de código, o ATLAS trabalha JUNTO com o comandante para entender profundamente:

1. **O AVATAR** — Quem é o usuário final? O que ele está passando? O que ele já tentou? O que o frustra nos produtos atuais? O que faria ele dizer "uau, isso é exatamente o que eu precisava"?

2. **O DIFERENCIAL** — O que vai tornar este projeto diferente e superior a TUDO que existe no mercado? Como isso pode ser uma nova categoria de produto, não apenas mais uma cópia do que já existe?

3. **A EXPERIÊNCIA** — Como cada tela deve fazer o usuário se sentir? Qual é o fluxo ideal da perspectiva do usuário (não do programador)?

4. **A IDENTIDADE VISUAL** — Se o comandante forneceu referências visuais, marca, ou estilo: absorver. Se não: construir junto, perguntando, mostrando opções, iterando.

O ATLAS conduz essa fase fazendo PERGUNTAS, não apresentando documentos. Ele extrai informações do comandante em blocos curtos, validando cada parte antes de avançar. No final, gera um documento de visão de produto que guia todas as decisões técnicas que vêm depois.

**Sobre geração de interfaces visuais:**
O ATLAS pode gerar prompts detalhados para ferramentas de design por inteligência artificial (como o Google Stitch ou similar) para que o comandante visualize cada tela antes de qualquer código ser escrito. O processo é:
- Discutir a tela com o comandante
- Gerar um prompt descritivo e detalhado da tela
- O comandante usa o prompt na ferramenta de design e mostra o resultado
- Iterar até o comandante aprovar o visual
- Repetir para cada tela do projeto
- Salvar os prompts aprovados e as referências visuais no `project-core.md`

**Resultado:** Documento de visão de produto aprovado pelo comandante. Identidade visual definida. Prompts de design para cada tela gerados e aprovados. Somente após esta fase o ATLAS avança para a classificação (Fase 1).

---

### FASE 1 — RECEPÇÃO E CLASSIFICAÇÃO

**Quem:** ATLAS + Comandante
**Janelas:** 1

O comandante descreve o projeto. O ATLAS classifica, pontua, e apresenta o plano. O comandante aprova ou ajusta.

**Resultado:** Documento de classificação aprovado pelo comandante.

---

### FASE 2 — ARQUITETURA E CONTRATOS

**Quem:** ATLAS + SHIELD (revisão) + CRONOS (ativado ao final — sempre, em todo projeto)
**Janelas:** 1 a 2

O ATLAS define tudo: contratos de interface de programação de aplicações com regras de validação detalhadas, esquema de banco, decisões técnicas críticas, padrões de implementação obrigatórios, armadilhas conhecidas das tecnologias escolhidas, fluxos completos de ponta a ponta, regras de autenticação e autorização, e popula o kanban com todas as tarefas.

**Antes de finalizar:** O ATLAS ativa o SHIELD para uma revisão de segurança dos contratos. O SHIELD verifica se as validações estão completas, se os fluxos estão mapeados, se as decisões técnicas cobrem as armadilhas, e se existe defesa em profundidade. O ATLAS corrige o que o SHIELD apontar.

**Ativação do CRONOS (v4.0 — OBRIGATÓRIA EM TODO PROJETO):** ao final desta fase, o ATLAS ativa o CRONOS, **independente da complexidade do projeto**. O CRONOS conduz o projeto a partir daqui: pesquisa técnica (Fase 2.3), sequenciamento (Fase 2.5), disparo de agentes de execução, monitoramento do kanban, ponto de contato do comandante até o deploy.

**Resultado:** `project-core.md` completo com contratos detalhados, decisões técnicas, padrões de implementação, e armadilhas documentadas. `kanban.md` populado. Contratos revisados pelo SHIELD. CRONOS ativado (sempre). ATLAS se retira da linha de frente.

---

### FASE 2.3 — PESQUISA TÉCNICA (v4.0 — OBRIGATÓRIA EM TODO PROJETO)

**Quem:** CRONOS + sub-agentes de pesquisa (disparados pelo CRONOS via Task `general-purpose`)
**Janelas:** 1 (CRONOS; sub-agentes rodam internos)

Antes de montar mini-planos ou disparar qualquer agente de execução, o CRONOS pesquisa documentação oficial atualizada das tecnologias escolhidas pelo ATLAS.

**Por que existe:** o ATLAS escolheu tecnologias na Fase 2 baseado em conhecimento de treinamento, que pode ter meses de defasagem. Bibliotecas mudam versões, APIs mudam, best practices mudam, aparecem deprecations e CVEs. Esta fase garante que a execução comece com informação fresca.

**Processo:**

1. CRONOS extrai do `project-core.md` a lista completa de tecnologias (Next.js, Supabase, Stripe, React Hook Form, Zod, etc.)
2. CRONOS dispara sub-agentes de pesquisa em paralelo (até 3 simultâneos) usando MCP Context7 se disponível, senão WebSearch + WebFetch
3. Cada sub-agente retorna: versão estável mais recente, breaking changes das últimas 3 versões, deprecations ativas, armadilhas conhecidas, padrões atuais vs antigos, links para docs oficiais
4. CRONOS consolida tudo em `.delta-11/memoria/pesquisa-tecnica.md`
5. Se a pesquisa revelar problema crítico (biblioteca deprecated, CVE ativo, padrão substituído), CRONOS PARA e reporta ao comandante antes de prosseguir — reativar ATLAS pode ser necessário para reavaliar escolhas técnicas
6. Os achados da pesquisa alimentam obrigatoriamente os mini-planos da Fase 2.5

**Resultado:** `.delta-11/memoria/pesquisa-tecnica.md` com documentação atualizada de cada tecnologia. Problemas críticos reportados ao comandante. Base sólida para os mini-planos.

---

### FASE 2.4 — PROVISIONAMENTO DE FERRAMENTAS (v5.2 — OBRIGATÓRIA EM TODO PROJETO)

**Quem:** CRONOS + sub-agente `tool-provisioner` (disparado via Task `general-purpose`)
**Janelas:** 1 (CRONOS; sub-agente roda interno)

Depois da pesquisa técnica e ANTES dos mini-planos, o CRONOS dispara o `tool-provisioner`, que transforma a lista de ferramentas do projeto em capacidade VERIFICADA:

1. Inventário completo: MCPs, chaves de API, contas, variáveis de ambiente, CLIs
2. Classificação: AUTO-CLI (instala sozinho) · AUTO-BROWSER (configura via Playwright) · CREDENCIAL (pede ao comandante em lote) · HUMANO (pagamento/telefone — checklist em linguagem leiga)
3. Verificação de CADA ferramenta com chamada real — não só "a chave existe"
4. Relatório em `.delta-11/memoria/tool-verification.md` + log completo em `.delta-11/logs/sub-agentes/`

**Por que existe:** setup manual de ferramentas era a maior fricção do comandante — tarefas de configuração ficavam penduradas no kanban por dias. Import aprovado do framework M2C1 (Phase 5) no ciclo v5.2.

**Resultado:** todas as ferramentas verificadas OU pendências explícitas com dono claro (comandante) e instruções passo a passo. FAIL que bloqueia a Fase 3 é resolvido ANTES dos mini-planos.

---

### FASE 2.5 — SEQUENCIAMENTO E MINI-PLANOS (v4.0 — OBRIGATÓRIA EM TODO PROJETO)

**Quem:** CRONOS (executa sozinho — agentes de execução NÃO criam planos próprios)
**Janelas:** 1 (CRONOS)

Esta fase existe para evitar que agentes "pensem enquanto fazem". A partir da v4.0, **o próprio CRONOS monta os mini-planos** de cada agente, usando como insumo os contratos do ATLAS + a pesquisa técnica da Fase 2.3. Agentes de execução NÃO criam planos próprios.

**Processo:**

1. **CRONOS lê as seções relevantes do `project-core.md`** (rotas, banco, decisões técnicas, padrões) + `.delta-11/memoria/pesquisa-tecnica.md`
2. **CRONOS constrói o mapa de dependências** entre as tarefas do kanban (veja operativo CRONOS PASSO 2)
3. **CRONOS identifica o caminho crítico** (qual agente bloqueia os outros)
4. **CRONOS cria um mini-plano específico para cada agente de execução** em `.delta-11/planos/[AGENTE]-plan.md` contendo:
   - Quais arquivos o agente deve criar/modificar (derivado dos contratos)
   - Dependências que precisa aguardar (de outros agentes)
   - Decisões técnicas aplicáveis (padrões do project-core.md + achados da pesquisa técnica)
   - Checklist de tarefas ordenado
   - Armadilhas conhecidas da tecnologia a evitar
5. **CRONOS monta as ondas de ativação** (ONDA 1, ONDA 2, ONDA 3) e documenta em `.delta-11/planos/CRONOS-sequenciamento.md`
6. **CRONOS pode disparar Code Architect** para validar se os mini-planos propostos seguem a arquitetura do `project-core.md` (opcional, útil em projetos grandes)
7. **CRONOS apresenta ao comandante** o sequenciamento e aguarda aprovação para disparar a ONDA 1

**Resultado:** Cada agente tem um mini-plano específico pronto, alinhado com contratos e docs atualizadas. CRONOS tem ondas de ativação documentadas. Zero improviso durante execução.

---

### FASE 3 — FUNDAÇÃO

**Quem:** VAULT (obrigatório) + SHIELD (sempre acompanha para preparar testes) + CRONOS (orquestrando)
**Janelas:** 2 a 3

O VAULT cria o banco de dados, autenticação, e políticas de segurança. O SHIELD prepara infraestrutura e estratégia de testes em paralelo. Em projetos de baixa complexidade, o SHIELD foca mais em checklists rápidos; em projetos maiores, já monta suíte de testes. A decisão de escopo do SHIELD fica com o mini-plano que o CRONOS entregou.

**Resultado:** Banco pronto, autenticação funcionando, infraestrutura configurada. NENHUM agente de funcionalidade começa antes disso estar concluído.

---

### FASE 4 — DESENVOLVIMENTO

**Quem:** Agentes de execução definidos pela complexidade + CRONOS (sempre, orquestrando)
**Janelas:** 2 a 7

Cada agente já tem seu mini-plano aprovado em `.delta-11/planos/[AGENTE]-plan.md` (criado pelo CRONOS na Fase 2.5) e **DEVE seguir exatamente o mini-plano**. Qualquer desvio precisa ser aprovado pelo CRONOS (que pode disparar Code Architect para avaliar impacto).

Ao concluir cada tarefa, atualiza seu estado e o kanban. O SHIELD testa CONTINUAMENTE conforme as funcionalidades são entregues (não espera o final).

**Ciclo de cada tarefa:**
```
Agente puxa tarefa do kanban → Executa seguindo plano → Build Validator (OBRIGATÓRIO) → Atualiza estado e kanban → SHIELD verifica contra contrato → Aprovado? → Próxima tarefa
```

**Durante a Fase 4 — Validação contínua de build (REGRA OBRIGATÓRIA):**
Todo agente que escreve código (ENGINE, BACK, FRONT, PIXEL, FORM, SCOUT) **DEVE** disparar o sub-agente `build-validator` ANTES de marcar cada tarefa como concluída. Isso garante que erros de build são pegos na origem, não acumulados para o SHIELD descobrir depois.

- Se **PASS**: Continua normalmente
- Se **FAIL com blockers**: Corrige ANTES de marcar como concluída
- Se **FAIL com warnings apenas**: Pode marcar como concluída mas registra warnings no estado

**Monitoramento de drift arquitetural (CRONOS — em todo projeto):**
Se CRONOS percebe que um agente está demorando muito ou fazendo muitos commits, pode disparar Code Architect para verificar se o agente está seguindo o mini-plano ou improvisando. Se detectar drift significativo, CRONOS pode parar o agente e forçar replanejamento. Em projetos simples (score < 7), o drift costuma ser mais raro — mas a regra é a mesma.

**Ao final da Fase 4 (quando todos os agentes de desenvolvimento terminam):**
1. **Code Simplifier (OBRIGATÓRIO):** O último agente a terminar dispara o sub-agente `code-simplifier` para simplificar todo o código escrito na fase. Após simplificação, dispara `build-validator` para confirmar que nada quebrou.
2. **Varredura preventiva (OBRIGATÓRIO):** SCOUT é ativado automaticamente para varredura completa de todo o código antes da Fase 5. Busca: inicializações perigosas, bypass de contratos, validações ausentes, links quebrados, condições de corrida, falhas de segurança.
3. **Auditoria arquitetural (OBRIGATÓRIO):** CRONOS dispara o sub-agente `code-architect` para comparar código real vs arquitetura planejada no `project-core.md`. Se score for C ou menor, CRONOS cria tarefas de correção no kanban antes de avançar. Se detectar problema estrutural que exige mudança de contrato, CRONOS escala para o comandante reativar o ATLAS.

**Resultado:** Todas as funcionalidades implementadas, código simplificado, testadas individualmente pelo SHIELD, varridas pelo SCOUT, e auditadas arquiteturalmente. Problemas encontrados são corrigidos antes de avançar.

---

### FASE 5 — TESTES DE INTEGRAÇÃO

**Quem:** SHIELD + SCOUT (se houver erros) + CRONOS (orquestrando — sempre)
**Janelas:** 1 a 2

O SHIELD executa testes de ponta a ponta: cada fluxo completo (usuário se cadastra → faz login → executa ação → vê resultado). Verifica coerência total entre interface, servidor, e banco.

**Resultado:** Todos os fluxos passando nos testes. Todos os erros encontrados corrigidos.

**NOTA:** Code Simplifier já foi executado ao final da Fase 4. Esta fase foca 100% em testes de integração.

---

### FASE 6 — PREPARAÇÃO PARA LANÇAMENTO

**Quem:** SHIELD + Comandante
**Janelas:** 1

O SHIELD configura o ambiente de produção, executa auditoria de segurança, e apresenta relatório final ao comandante.

**Antes do deploy final, o SHIELD dispara 2 sub-agentes em sequência:**
1. `build-validator` — validação completa (typecheck, lint, build, testes, audit, secrets)
2. `verify-app` — teste real no browser (navegação, fluxos críticos, console errors)

Somente se AMBOS retornarem PASS, o deploy é apresentado ao comandante para aprovação.

**Resultado:** Sistema em produção.
