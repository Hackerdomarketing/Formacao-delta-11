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

**Boilerplate PRIMEIRO (v5.3 — projetos web Next.js):** antes de construir do zero, o agente da fundação cria o projeto com `npx create-next-app@latest` e aplica o overlay padrão do sistema:

```bash
~/projetos/Formacao-delta-11/boilerplate-delta-11-nextjs/aplicar-boilerplate.sh /caminho/do/projeto
```

Isso entrega pronto: limites de código no linter, formato único de erro, validação de ambiente, endereço do monitoramento de erros e pasta de testes de contrato (detalhes no README do boilerplate). Só depois o VAULT constrói o que é específico do projeto.

O VAULT cria o banco de dados, autenticação, e políticas de segurança. O SHIELD prepara infraestrutura e estratégia de testes em paralelo. Em projetos de baixa complexidade, o SHIELD foca mais em checklists rápidos; em projetos maiores, já monta suíte de testes. A decisão de escopo do SHIELD fica com o mini-plano que o CRONOS entregou.

**Resultado:** Banco pronto, autenticação funcionando, infraestrutura configurado. NENHUM agente de funcionalidade começa antes disso estar concluído.

---

### FASE 3.5 — RITMO TEMPORAL (Dia 4 — Os Astros) — v6.0 NOVA

**Quem:** CRONOS (orquestrando) + Engenheiro de DevOps/SRE + Líder Técnico da Fundação
**Janelas:** 1

**Por que esta fase existe (v6.0):** Antes do v6.0, o sistema ia DIRETO da Fundação (Fase 3) para o Desenvolvimento de Funcionalidade (Fase 4), pulando completamente o Dia 4 da Metodologia Gênesis (Astros = Ritmo Temporal). Isso é a **inversão herética** literal que a Metodologia adverte: "fazer os peixes antes de haver águas e antes de haver ritmo temporal para governar essa vida". A Fase 3.5 existe para **construir o ritmo do sistema ANTES dos habitantes** (Dia 5).

**Cross-reference conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4 (Os Astros — o Ritmo Temporal do Sistema). Texto hebraico chave: *yehi meorot bi-rekia ha-shamayim le-havdil bein ha-yom u-vein ha-laila* — "haja luminares no firmamento para separar entre dia e noite".

**O que é construído nesta fase (10 artefatos do Dia 4):**

1. **Sistema de eventos declarado** — quais eventos existem, quem produz, quem consome (catálogo de eventos, não implementação ainda)
2. **Sistema de mensageria e filas configurado** — RabbitMQ, Kafka, SQS, Redis Streams, ou Inngest. Qual, por quê, contratos
3. **Jobs agendados mapeados** — cron tasks, scheduled jobs, periodic workers. Listados com frequência e dono
4. **Estratégia de cache com TTL por tipo de dado** — qual cache, quais TTLs, política de invalidação
5. **Timeouts declarados por tipo de operação** — HTTP, RPC, DB, fila. Cada um com valor numérico
6. **Retries com backoff exponencial configurados** — padrão: 3 tentativas, 1s/2s/4s. Retry policy documentada por dependência externa
7. **Circuit breakers para dependências externas críticas** — 5 falhas/60s pause para cada dependência externa crítica
8. **CI/CD funcionando de ponta a ponta em staging** — pipeline real executando testes, build, deploy em staging. **Não pode ser placeholder**
9. **Observabilidade configurada** — logs estruturados, métricas (latência, erro, saturação), traces distribuídos, dashboards visíveis
10. **Sub-contraposição declarada** — processos dominantes ativos (schedulers, dispatchers) contra processos testemunhas passivos (loggers, métricas, health checks)

**Resultado:** os 10 artefatos acima existem como arquivos `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<N>.md` (um por artefato), cada um com pelo menos: descrição, escolha tecnológica, justificativa, referência à documentação. **Nenhum agente de funcionalidade começa antes dos 10 artefatos estarem presentes.**

**Quem sella:** Líder técnico da Fundação + Comandante. Selo provisório permite iniciar Fase 4.

**Templates relacionados:**
- `.delta-11/templates/fase-ritmo-template.md` (Etapa 5 do v6.0) — template dos 10 artefatos
- `.delta-11/protocolos/fase-ritmo.md` (Etapa 5 do v6.0) — protocolo detalhado
- Hook bloqueante: `fase-ritmo-checker.py` (Etapa 5 do v6.0)

**Sobre o roadmap dos 7 ciclos:** o "Ciclo 4 — Tempo" do roadmap (definido em `ATLAS.md:415`) pode **continuar** marcando entregas temporais. A Fase 3.5 é a camada de RITMO que sustenta todos os 7 ciclos, não substitui nenhum.

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
1. **Varredura preventiva (OBRIGATÓRIO):** SCOUT é ativado automaticamente para varredura completa de todo o código antes da Fase 5. Busca: inicializações perigosas, bypass de contratos, validações ausentes, links quebrados, condições de corrida, falhas de segurança.
2. **Auditoria arquitetural (OBRIGATÓRIO):** CRONOS dispara o sub-agente `code-architect` para comparar código real vs arquitetura planejada no `project-core.md`. Se score for C ou menor, CRONOS cria tarefas de correção no kanban antes de avançar. Se detectar problema estrutural que exige mudança de contrato, CRONOS escala para o comandante reativar o ATLAS.

**Resultado:** Todas as funcionalidades implementadas, testadas individualmente pelo SHIELD, varridas pelo SCOUT, e auditadas arquiteturalmente. Problemas encontrados são corrigidos antes de avançar.

---

### FASE 4.5 — CONSCIÊNCIA DOMINANTE (Dia 6 — A Consciência Que Domina) — v6.0 NOVA

**Quem:** CRONOS (orquestrando) + VAULT (auth + RLS) + SHIELD (auditoria + rate limiting) + Líder de Produto (regras de negócio) + Especialista de Compliance/LGPD
**Janelas:** 1 a 2

**Por que esta fase existe (v6.0):** Antes do v6.0, o VAULT na Fase 3 entregava apenas autenticação básica + RLS. O Dia 6 da Metodologia Gênesis (a Consciência Dominante — única camada declarada *muito bom* no texto bíblico) exige que **após o código de funcionalidade existir** (Dia 5), a camada de governança consciente seja construída em cima dele: autenticação + autorização conscientes, motor de regras de negócio, auditoria imutável, rate limiting, LGPD, fluxos de aprovação. Esta fase é o único dia com a expressão *tov meod* (muito bom) — o sistema não apenas funciona, funciona de forma responsável e auditável.

**Cross-references:**
- `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6
- Skills globais v5.4 instaladas em `~/.claude/skills/`:
  - `owasp-top10` (7.374 linhas, 5 CVEs incluindo CVE-2024-34351 e CVE-2025-29927) — referência obrigatória do SHIELD
  - `supabase-rls` (6.676 linhas, P6 multi-tenancy, P7 Custom Hook) — referência obrigatória do VAULT
  - Bases curtas: `.delta-11/conhecimento/owasp-top10-overview.md`, `.delta-11/conhecimento/supabase-rls-patterns.md`
- **Texto hebraico chave:** *naaseh adam be-tzalmenu ki-dmutenu* (façamos o homem em nossa imagem) · *zachar u-nekevá bara otam* (masculino e feminino criou-os) · *tov meod* (muito bom — único dia com esta expressão)

**Os 5 entregáveis do Dia 6 (todos verificados):**

1. **Auditoria imutável de ações** — sistema que registra *quem fez o quê e quando* com logs append-only (não editáveis). Diferente do Sentry (que captura erros) — aqui é auditoria de ações do usuário (CRUD em entidades críticas). Para cada tabela com dados sensíveis, existe trigger ou middleware que registra a operação.

2. **Rate limiting obrigatório por endpoint crítico** — login, registro, recuperação de senha, APIs que consomem crédito/enviam email/SMS. Implementado como Chain of Responsibility após auth (padrão documentado em `conhecimento/design-patterns-praticos.md`).

3. **Motor de regras de negócio central** — regras de negócio que estão espalhadas pelo código são extraídas para um módulo central (`src/lib/regra-negocio/` ou equivalente) OU há justificativa explícita de por que determinada regra é distribuída. Sem motor central, auditoria fica cara.

4. **Sistema de consentimento LGPD/GDPR** — banner de cookies opt-in, registro de consentimento, fluxo de exportação de dados pessoais do usuário (direito de acesso), fluxo de exclusão de dados (direito ao esquecimento), DPO designado.

5. **Fluxos de aprovação para operações críticas** — delete em massa, transações financeiras, mudança de role, alteração de dados de outro usuário. Cada operação crítica tem um workflow de aprovação explícito (single-step, multi-step, ou automated via regra).

**Quem sella:** SHIELD (auditoria + rate limiting) + Comandante (LGPD + aprovações). Selo permite iniciar Fase 5.

**Resultado:** os 5 entregáveis verificados com evidência (arquivos em `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<N>.md`). Auth + Authz testadas com casos positivos e negativos. Logs de auditoria verificados como imutáveis. Rate limiting ativo em todos endpoints críticos. Fluxo LGPD testado com pessoa real.

**Templates e hooks relacionados (Etapa 6 do v6.0):**
- `.delta-11/templates/fase-consciencia-template.md` — template dos 5 entregáveis
- `.delta-11/protocolos/fase-consciencia.md` — protocolo detalhado
- Hook bloqueante: `fase-consciencia-checker.py`

**Sobre as skills globais:** o conteúdo das skills `owasp-top10` e `supabase-rls` NÃO é duplicado aqui — apenas garante-se que os agentes que executam esta fase **consultam** as skills via CLAUDE.md (description auto-ativa) ou via menção explícita no mini-plano.

---

### FASE 5 — TESTES DE INTEGRAÇÃO

**Quem:** SHIELD + SCOUT (se houver erros) + CRONOS (orquestrando — sempre)
**Janelas:** 1 a 2

O SHIELD executa testes de ponta a ponta: cada fluxo completo (usuário se cadastra → faz login → executa ação → vê resultado). Verifica coerência total entre interface, servidor, e banco.

**Resultado:** Todos os fluxos passando nos testes. Todos os erros encontrados corrigidos.

---

### FASE 6 — PREPARAÇÃO PARA LANÇAMENTO

**Quem:** SHIELD + Comandante
**Janelas:** 1

O SHIELD configura o ambiente de produção, executa auditoria de segurança, e apresenta relatório final ao comandante.

**Antes do deploy final, o SHIELD dispara 2 sub-agentes em sequência:**
1. `build-validator` — validação completa (typecheck, lint, build, testes, audit, secrets)
2. `verify-app` — teste real no browser (navegação, fluxos críticos, console errors)

**E verifica o monitoramento de erros:** Sentry configurado + erro proposital de teste capturado no painel. Deploy de produção sem Sentry ativo = REPROVADO (ver checklist de deploy no SHIELD.md).

Somente se AMBOS os sub-agentes retornarem PASS e o Sentry estiverem ativo, o deploy é apresentado ao comandante para aprovação.

**Resultado:** Sistema em produção.

---

### FASE 7 — DESCANSO CONSAGRADO (Dia 7 — vayechulu, vayishbot) — v6.0 NOVA

**Quem:** CRONOS (orquestrando) + SHIELD (deploy, runbooks, monitoramento) + Comandante (teste supremo de operação autônoma) + líder técnico
**Janelas:** 1 (mas com janela de observação de 2 semanas antes do selo final)

**Por que esta fase existe (v6.0):** Antes do v6.0, o sistema TERMINAVA na Fase 6 com "Sistema em produção". Mas o Dia 7 da Metodologia Gênesis não é "terminar" — é **consagrar**. Os verbos hebraicos *vayechulu* (foram consumados) e *vayishbot* (cessou intencionalmente) descrevem o momento em que o sistema atinge operação autônoma. Sem a Fase 7, o criador vira refém: cada bug precisa dele, cada feature nova precisa dele, cada incidente 3h da manhã precisa dele. A Fase 7 existe para **selar** o sistema em estado de operação autônoma.

**Cross-reference conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 7. Texto hebraico chave: *vayechulu ha-shamayim ve-ha-arets* (foram consumados os céus e a terra) · *vayishbot ba-yom ha-shvii* (cessou no sétimo dia) · *vayvarech* (abençoou) · *kadash* (santificou).

**Os 10 entregáveis do Dia 7 (todos verificados com EVIDÊNCIA):**

1. **Documentação técnica consumada** — arquitetura, decisões (ADRs), diagramas atualizados, guias de contribuição. Estado: `docs/arquitetura/`, `.delta-11/memoria/decisoes/`
2. **Documentação de domínio consumada** — glossário do negócio, regras de negócio explicitadas, casos de uso descritos. Estado: `docs/dominio/` ou `docs/comandante/`
3. **Testes de aceitação E2E** — fluxos críticos cobertos com testes automatizados que rodam em CI. Pelo menos os 5 fluxos mais importantes do produto
4. **Pipeline de deploy automatizado** — de commit até produção, sem intervenção manual. Funciona em staging E produção
5. **Runbooks operacionais específicos do projeto** — instanciados da skill global `owasp-top10` (`~/.claude/skills/owasp-top10/references/07-incident-response.md`) ou criados especificamente. Cobrem os 5 incidentes mais prováveis do produto. Em `.delta-11/memoria/runbooks/`
6. **Monitoramento com dashboards + alertas ativos** — dashboards visíveis para SLOs do produto, alertas configurados COM dono (quem recebe notificação), níveis INFO/WARN/CRITICAL
7. **Tag de release** — git tag marcado, changelog de release publicado, binário/artefato arquivado
8. **Backup testado** — rotina de backup rodando, último restore executado evidenciado (não é teórico)
9. **DR testado** — disaster recovery executado em ambiente isolado, tempo de recuperação (RTO) medido
10. **Onboarding testado com pessoa nova** — pelo menos 1 pessoa nova leu a doc e conseguiu fazer deploy local + 1 alteração pequena em < 1 dia

**O TESTE SUPREMO (critério de selo diferenciador do Dia 7):**

> *"Se o criador tirar 2 semanas de férias sem tocar no sistema, ele continua funcionando?"*

Se SIM → Dia 7 selado. Se NÃO → o sistema **não consagra**. Voltar e consertar o que falta (geralmente: runbook ausente, alerta sem dono, backup não testado).

**Quem sella:** Comandante (teste supremo) + líder técnico (entregáveis). Selo **só é declarado** após pelo menos 2 semanas de operação estável em produção.

**Resultado:** os 10 entregáveis verificados com evidência; 2 semanas de operação estável sem intervenção; teste supremo respondido SIM; tag de release consolidada.

**Templates e hooks relacionados (Etapa 7 do v6.0):**
- `.delta-11/templates/fase-descanso-template.md` — template dos 10 entregáveis
- `.delta-11/protocolos/fase-descanso.md` — protocolo detalhado
- Hook bloqueante: `fase-descanso-checker.py`
- Atualização do `monitor-delta11.sh` para detectar "operação autônoma estável por X dias"

**Sobre a Fase 6 anterior:** a Fase 6 (Preparação para Lançamento) é o **selo provisório** que permite colocar em produção. A Fase 7 (Descanso) é o **selo definitivo** que fecha o ciclo. Entre as duas, o sistema precisa operar de verdade em produção pelo tempo mínimo (2 semanas).

---

## RESUMO DAS 13 FASES DO FLUXO v6.0

```
0    Descoberta e Design              (Dia 1 — Luz)
1    Recepção e Classificação         (Dia 1 — selagem auxiliar)
2    Arquitetura e Contratos          (Dia 2 — Container)
2.3  Pesquisa Técnica                 (subsidiária, sempre)
2.4  Provisionamento de Ferramentas   (subsidiária, sempre)
2.5  Sequenciamento e Mini-planos     (subsidiária, sempre)
3    Fundação                         (Dia 3 — Superfícies)
3.5  Ritmo Temporal                   (Dia 4 — Astros) ← NOVA v6.0
4    Desenvolvimento                  (Dia 5 — Habitantes)
4.5  Consciência Dominante            (Dia 6 — Consciência) ← NOVA v6.0
5    Testes de Integração             (Dia 5 — selagem final)
6    Preparação para Lançamento       (Dia 6 — selagem final)
7    Descanso Consagrado              (Dia 7 — Descanso) ← NOVA v6.0
```

**Princípio 1 (Ordem Inegociável):** respeitado. Cada Dia só começa após o anterior selado.

**Princípio 2 (Selagem por critérios):** cada Dia tem critério objetivo de selo. O Dia 2 tem selagem provisória com validação retroativa obrigatória pelo Dia 3.

**Princípio 3 (Contraposição Lateral):** verificado pelo hook `contraposicao-checker.py` (Etapa 3 do v6.0).
