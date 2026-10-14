# FLUXO DO ZERO AO LANÇAMENTO — FORMAÇÃO Δ-11 (v6.3)

## AS 13 FASES OBRIGATÓRIAS

São 13 fases: **0, 1, 2, 2.3, 2.4, 2.5, 3, 3.5, 4, 4.5, 5, 6 e 7**. Elas são executadas nesta ordem. Nenhuma fase pode ser pulada (as únicas exceções declaradas estão nos protocolos das Fases 3.5 e 4.5, sempre registradas no kanban pelo CRONOS).

Sete delas são os **7 Dias** da Metodologia Gênesis (`.delta-11/conhecimento/metodologia-genesis-camadas.md`):

| Dia | Fase |
|---|---|
| Dia 1 — Luz | Fase 0 |
| Dia 2 — Container | Fase 2 |
| Dia 3 — Superfícies | Fase 3 |
| Dia 4 — Astros | Fase 3.5 |
| Dia 5 — Habitantes | Fase 4 |
| Dia 6 — Consciência | Fase 4.5 |
| Dia 7 — Descanso | Fase 7 |

As outras seis (1, 2.3, 2.4, 2.5, 5 e 6) são **fases de apoio**: ficam fora dos Dias, preparam ou conferem o Dia vizinho e não mudam a ordem dos Dias. O **Passo 2.7** (SHIELD gera os testes de contrato) é um passo dentro da Fase 2, não uma fase própria.

**Como os agentes rodam (v6.3):** ninguém abre sessão, janela ou terminal à mão. O ATLAS dispara SOMENTE o CRONOS. O CRONOS dispara todos os outros (executores, SHIELD, SCOUT, sub-agentes e, quando preciso, o próprio ATLAS) com o Agent tool. Executores rodam com `isolation: "worktree"`; CRONOS e SHIELD revisor rodam sem worktree. Detalhes em `.delta-11/protocolos/comunicacao.md`.

**Quando o comandante é chamado:** só nas 3 situações de sempre — (1) decisão de negócio ou de escopo que só ele pode tomar; (2) credencial, conta, pagamento ou CAPTCHA; (3) risco de perda de dados ou publicação externa (deploy). E, se o projeto estiver em `modo manual` (`.delta-11/.modo-selo`), na fronteira entre fases, com o comando `aprovar`. O padrão é `automatico`.

---

### FASE 0 — DESCOBERTA E DESIGN (Dia 1 — Luz)

**Quem:** ATLAS (como facilitador) + Comandante
**Disparo:** o ATLAS é o primeiro agente ativado no projeto.

Esta é a fase mais importante do projeto. Antes de classificar, arquitetar, ou escrever uma única linha de código, o ATLAS trabalha JUNTO com o comandante para entender profundamente:

1. **O AVATAR** — Quem é o usuário final? O que ele está passando? O que ele já tentou? O que o frustra nos produtos atuais? O que faria ele dizer "uau, isso é exatamente o que eu precisava"?

2. **O DIFERENCIAL** — O que vai tornar este projeto diferente e superior a TUDO que existe no mercado? Como isso pode ser uma nova categoria de produto, não apenas mais uma cópia do que já existe?

3. **A EXPERIÊNCIA** — Como cada tela deve fazer o usuário se sentir? Qual é o fluxo ideal da perspectiva do usuário (não do programador)?

4. **A IDENTIDADE VISUAL** — Se o comandante forneceu referências visuais, marca, ou estilo: absorver. Se não: construir junto, perguntando, mostrando opções, iterando.

Esta fase é, por natureza, decisão de negócio (situação 1): por isso o comandante participa dela inteira.

**Antes de começar**, o ATLAS lê `~/.delta-11/aprendizados-entre-projetos.md` (lições que o CRONOS registrou em projetos anteriores). Se o arquivo não existir, segue sem ele.

O ATLAS conduz essa fase fazendo PERGUNTAS, não apresentando documentos. Ele extrai informações do comandante em blocos curtos, validando cada parte antes de avançar. No final, gera um documento de visão de produto que guia todas as decisões técnicas que vêm depois.

**Sobre geração de interfaces visuais:**
O ATLAS pode gerar prompts detalhados para ferramentas de design por inteligência artificial (como o Google Stitch ou similar) para que o comandante visualize cada tela antes de qualquer código ser escrito. O processo é:
- Discutir a tela com o comandante
- Gerar um prompt descritivo e detalhado da tela
- O comandante usa o prompt na ferramenta de design e mostra o resultado
- Iterar até o comandante aprovar o visual
- Repetir para cada tela do projeto
- Salvar os prompts aprovados e as referências visuais no project-core (fatia `memoria/project-core/visual.md`)

**Resultado:** Documento de visão de produto aprovado pelo comandante (`docs/prd.md`). Identidade visual definida. Prompts de design para cada tela gerados e aprovados. Somente após esta fase o ATLAS avança para a classificação (Fase 1).

---

### FASE 1 — RECEPÇÃO E CLASSIFICAÇÃO (apoio)

**Quem:** ATLAS
**Disparo:** mesma sessão do ATLAS.

O ATLAS classifica e pontua o projeto pela régua única de `.delta-11/protocolos/classificacao.md` (5 critérios, soma 5–15; BAIXA 5–8, MÉDIA 9–12, ALTA 13–15) e registra o resultado no project-core. A pontuação decide QUANTOS agentes entram (se FRONT acumula PIXEL+FORM e BACK acumula ENGINE+VAULT); o CRONOS entra sempre.

O comandante só é consultado se a classificação depender de uma decisão de escopo que só ele pode tomar (ex.: "o MVP terá pagamento ou não?"). Em `modo manual`, ele aprova na fronteira da fase.

**Resultado:** Classificação registrada no project-core.

---

### FASE 2 — ARQUITETURA E CONTRATOS (Dia 2 — Container)

**Quem:** ATLAS (escreve) + SHIELD (revisa, disparado pelo CRONOS) + CRONOS (disparado pelo ATLAS — sempre, em todo projeto)

O ATLAS relê `~/.delta-11/aprendizados-entre-projetos.md` antes de escolher tecnologias e padrões.

O ATLAS define tudo: contratos de interface de programação de aplicações com regras de validação detalhadas, esquema de banco, decisões técnicas críticas, padrões de implementação obrigatórios, armadilhas conhecidas das tecnologias escolhidas, fluxos completos de ponta a ponta, regras de autenticação e autorização, a contraposição do Dia 2, e a lista completa de tarefas. Só o ATLAS escreve o project-core e as suas fatias (`memoria/project-core/banco.md`, `contratos.md`, `visual.md`, `decisoes-tecnicas.md`). A lista de tarefas vai na seção `TAREFAS PARA O KANBAN` do `memoria/ATLAS-produto.md` — quem escreve o `kanban.md` é o CRONOS.

**Revisão dos contratos pelo SHIELD (sem o ATLAS disparar ninguém além do CRONOS):**
1. O ATLAS registra o pedido de revisão no `ATLAS-produto.md` (seção `PEDIDO DE REVISÃO DO SHIELD`) e dispara o CRONOS.
2. O CRONOS popula o kanban com a lista do ATLAS e dispara o SHIELD (sem worktree) para revisar os contratos: validações completas, fluxos mapeados, armadilhas cobertas, defesa em profundidade.
3. Se o SHIELD apontar correções, o CRONOS dispara o ATLAS de novo com a lista; o ATLAS corrige o project-core.
4. **Passo 2.7 (SHIELD):** com os contratos finais, o SHIELD dispara o `contract-tester`, que gera os testes de contrato em `tests/contracts/` e os roda uma vez.

**Selo:** provisório. O Dia 2 só é declarado "bom" de forma definitiva junto com o Dia 3 (validação retroativa na Fase 3).

**Resultado:** project-core completo (contratos detalhados, decisões técnicas, padrões, armadilhas, contraposição). Contratos revisados pelo SHIELD e testes de contrato gerados. Kanban populado pelo CRONOS. O ATLAS sai da linha de frente; o CRONOS conduz o projeto a partir daqui.

---

### FASE 2.3 — PESQUISA TÉCNICA (apoio — obrigatória em todo projeto)

**Quem:** CRONOS + até 3 sub-agentes de pesquisa disparados por ele (Agent tool, `subagent_type: "general-purpose"`)

Antes de montar mini-planos ou disparar qualquer agente de execução, o CRONOS pesquisa documentação oficial atualizada das tecnologias escolhidas pelo ATLAS.

**Por que existe:** o ATLAS escolheu tecnologias na Fase 2 baseado em conhecimento de treinamento, que pode ter meses de defasagem. Bibliotecas mudam versões, APIs mudam, boas práticas mudam, aparecem descontinuações e falhas de segurança publicadas (CVEs). Esta fase garante que a execução comece com informação fresca.

**Processo:**

1. CRONOS extrai do project-core a lista completa de tecnologias (Next.js, Supabase, Stripe, React Hook Form, Zod, etc.)
2. CRONOS dispara sub-agentes de pesquisa em paralelo (até 3 simultâneos) usando o MCP Context7 se disponível, senão WebSearch + WebFetch
3. Cada sub-agente retorna: versão estável mais recente, mudanças incompatíveis das últimas 3 versões, descontinuações ativas, armadilhas conhecidas, padrões atuais vs antigos, links para docs oficiais
4. CRONOS consolida tudo em `.delta-11/memoria/pesquisa-tecnica.md`
5. Se a pesquisa revelar problema crítico (biblioteca descontinuada, CVE ativo, padrão substituído), o CRONOS PARA o sequenciamento e dispara o ATLAS para reavaliar a escolha técnica. O comandante só é avisado se a troca exigir decisão de negócio (ex.: trocar por um serviço pago)
6. Os achados da pesquisa alimentam obrigatoriamente os mini-planos da Fase 2.5

**Resultado:** `.delta-11/memoria/pesquisa-tecnica.md` com documentação atualizada de cada tecnologia. Problemas críticos resolvidos com o ATLAS. Base sólida para os mini-planos.

---

### FASE 2.4 — PROVISIONAMENTO DE FERRAMENTAS (apoio — obrigatória em todo projeto)

**Quem:** CRONOS + sub-agente `tool-provisioner` (disparado pelo CRONOS)

Depois da pesquisa técnica e ANTES dos mini-planos, o CRONOS dispara o `tool-provisioner`, que transforma a lista de ferramentas do projeto em capacidade VERIFICADA:

1. Inventário completo: MCPs, chaves de API, contas, variáveis de ambiente, CLIs
2. Classificação: AUTO-CLI (instala sozinho) · AUTO-BROWSER (configura via navegador automatizado) · CREDENCIAL (pede ao comandante, tudo de uma vez — situação 2) · HUMANO (pagamento/telefone — checklist em linguagem leiga)
3. Verificação de CADA ferramenta com chamada real — não só "a chave existe"
4. Relatório em `.delta-11/memoria/tool-verification.md` + log completo em `.delta-11/logs/sub-agentes/`

**Por que existe:** configurar ferramentas à mão era a maior fricção do comandante — tarefas de configuração ficavam penduradas no kanban por dias.

**Resultado:** todas as ferramentas verificadas OU pendências explícitas com dono claro (comandante) e instruções passo a passo. FAIL que bloqueia a Fase 3 é resolvido ANTES dos mini-planos.

---

### FASE 2.5 — SEQUENCIAMENTO E MINI-PLANOS (apoio — obrigatória em todo projeto)

**Quem:** CRONOS (executa sozinho — agentes de execução NÃO criam planos próprios)

Esta fase existe para evitar que agentes "pensem enquanto fazem". O CRONOS monta os mini-planos de cada agente, usando como insumo os contratos do ATLAS + a pesquisa técnica da Fase 2.3.

**Processo:**

1. **CRONOS lê as seções relevantes do project-core** (rotas, banco, decisões técnicas, padrões) + `.delta-11/memoria/pesquisa-tecnica.md`
2. **CRONOS constrói o mapa de dependências** entre as tarefas do kanban (veja operativo CRONOS PASSO 2)
3. **CRONOS identifica o caminho crítico** (qual agente bloqueia os outros)
4. **CRONOS cria um mini-plano para cada agente de execução** em `.delta-11/planos/[AGENTE]-plan.md` — um arquivo por agente, sobrescrito a cada onda (o anterior vai para `.delta-11/planos/arquivo/`). O mini-plano tem 6 seções:
   1. Objetivo da onda
   2. Recorte da fase anterior (cita o `[AGENTE]-produto.md` anterior)
   3. Tarefas (checklist ordenado, arquivos a criar/modificar, dependências de outros agentes)
   4. Critérios de aceite
   5. Limites de escopo (o que o agente NÃO faz; quais fatias do project-core ele lê)
   6. Convenções (decisões técnicas e armadilhas aplicáveis, achados da pesquisa)

   e inclui o checklist do ciclo interno de 7 sub-etapas (`.delta-11/protocolos/ciclo-interno-7d.md`).
5. **CRONOS monta as ondas de ativação** (ONDA 1, ONDA 2, ONDA 3) e documenta em `.delta-11/planos/CRONOS-sequenciamento.md`
6. **CRONOS pode disparar o `code-architect`** para validar se os mini-planos seguem a arquitetura do project-core (opcional, útil em projetos grandes)
7. **CRONOS sela a fase e dispara a ONDA 1.** Em `modo manual`, apresenta o sequenciamento ao comandante na fronteira da fase e espera `aprovar`.

**Resultado:** Cada agente tem um mini-plano específico pronto, alinhado com contratos e docs atualizadas. CRONOS tem ondas de ativação documentadas. Zero improviso durante execução.

---

### FASE 3 — FUNDAÇÃO (Dia 3 — Superfícies)

**Quem:** VAULT (obrigatório, com worktree) + SHIELD (prepara testes) + CRONOS (orquestrando)

**Boilerplate PRIMEIRO (projetos web Next.js):** antes de construir do zero, o agente da fundação cria o projeto com `npx create-next-app@latest` e aplica o overlay padrão do sistema, a partir da fonte oficial do Δ-11:

```bash
# A fonte oficial é o campo "source" de ~/.delta-11-registry.json
# (padrão: ~/Documents/VSCODE/Formacao-delta-11)
D11_SOURCE="$(python3 -c "import json,os;print(os.path.expanduser(json.load(open(os.path.expanduser('~/.delta-11-registry.json')))['source']))" 2>/dev/null || echo "$HOME/Documents/VSCODE/Formacao-delta-11")"
"$D11_SOURCE/boilerplate-delta-11-nextjs/aplicar-boilerplate.sh" /caminho/do/projeto
```

Isso entrega pronto: limites de código no linter, formato único de erro, validação de ambiente, endereço do monitoramento de erros e pasta de testes de contrato (detalhes no README do boilerplate). Só depois o VAULT constrói o que é específico do projeto.

O VAULT cria o banco de dados, autenticação, e políticas de segurança. O SHIELD prepara infraestrutura e estratégia de testes em paralelo. Em projetos de baixa complexidade, o SHIELD foca mais em checklists rápidos; em projetos maiores, já monta suíte de testes. A decisão de escopo do SHIELD fica com o mini-plano que o CRONOS entregou.

**Duas verdades, sem confusão:** o project-core é a verdade do CONTRATO (o que deve ser); as migrations são a verdade do banco IMPLEMENTADO (o que é). Se divergirem, é um bug: o CRONOS dispara o ATLAS para decidir.

**Validação retroativa do Dia 2:** antes de selar a Fase 3, a tarefa "Validação Retroativa Dia 2 ← Dia 3" precisa estar concluída no kanban com a resposta **SUSTENTA** (a arquitetura aguentou a fundação) ou **REFAZER** (o CRONOS dispara o ATLAS para refazer a arquitetura). O hook `validar-arquitetura-vs-modelos.py` cobra isso.

**Resultado:** Banco pronto, autenticação funcionando, infraestrutura configurada, Dia 2 confirmado. NENHUM agente de funcionalidade começa antes disso estar concluído.

---

### FASE 3.5 — RITMO TEMPORAL (Dia 4 — Os Astros)

**Quem:** BACK (líder técnico da fase) + ENGINE + VAULT + SHIELD, orquestrados pelo CRONOS. Em projetos de BAIXA complexidade, o BACK acumula ENGINE e VAULT. Papel de cada um: ver a tabela "PAPEL DE CADA AGENTE NAS FASES 3.5, 4.5 E 7" abaixo.

**Por que esta fase existe (v6.0):** antes da v6.0, o sistema ia DIRETO da Fundação (Fase 3) para o Desenvolvimento de Funcionalidade (Fase 4), pulando completamente o Dia 4 da Metodologia Gênesis (Astros = Ritmo Temporal). Isso é a **inversão herética** literal que a Metodologia adverte: "fazer os peixes antes de haver águas e antes de haver ritmo temporal para governar essa vida". A Fase 3.5 existe para **construir o ritmo do sistema ANTES dos habitantes** (Dia 5).

**Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4 (Os Astros — o Ritmo Temporal do Sistema). Texto hebraico chave: *yehi meorot bi-rekia ha-shamayim le-havdil bein ha-yom u-vein ha-laila* — "haja luminares no firmamento para separar entre dia e noite".

**O que é construído nesta fase (10 artefatos do Dia 4):**

1. **Sistema de eventos declarado** — quais eventos existem, quem produz, quem consome (catálogo de eventos, não implementação ainda)
2. **Sistema de mensageria e filas configurado** — RabbitMQ, Kafka, SQS, Redis Streams, ou Inngest. Qual, por quê, contratos
3. **Jobs agendados mapeados** — tarefas agendadas (cron) e trabalhadores periódicos. Listados com frequência e dono
4. **Estratégia de cache com TTL por tipo de dado** — qual cache, quais tempos de validade, política de invalidação
5. **Tempos-limite declarados por tipo de operação** — valores da tabela única em `.delta-11/protocolos/regras-codigo.md` §3 (banco 5 s; API externa 10 s; chamada interna 3 s)
6. **Novas tentativas com espera crescente** — 3 tentativas (1 s, 2 s, 4 s), política documentada por dependência externa
7. **Circuit breakers para dependências externas críticas** — abre após 5 falhas, fecha após 60 s
8. **CI/CD funcionando de ponta a ponta em staging** — pipeline real executando testes, build, deploy em staging. **Não pode ser de mentira**
9. **Observabilidade configurada** — logs estruturados, métricas (latência, erro, saturação), traces distribuídos, painéis visíveis
10. **Sub-contraposição declarada** — processos dominantes ativos (agendadores, despachantes) contra processos testemunhas passivos (logs, métricas, verificações de saúde)

**Resultado:** os 10 artefatos acima existem como arquivos `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<NN>-<slug>.md` (um por artefato, `<NN>` de 01 a 10), cada um com pelo menos: descrição, escolha tecnológica, justificativa, referência à documentação. **Nenhum agente de funcionalidade começa antes dos 10 artefatos estarem presentes.**

**Quem sela:** o BACK (líder técnico) declara **SUSTENTA** no kanban (via CRONOS); o SHIELD revisa; o CRONOS roda a cadeia de selo. Em `modo manual`, o comandante digita `aprovar`. Selo provisório permite iniciar a Fase 4.

**Arquivos relacionados:**
- `.delta-11/templates/fase-ritmo-template.md` — modelo dos 10 artefatos
- `.delta-11/protocolos/fase-ritmo.md` — protocolo detalhado
- Hook bloqueante: `fase-ritmo-checker.py`

**Sobre o roadmap dos 7 ciclos:** o "Ciclo 4 — Tempo" do roadmap (definido no `ATLAS.md`) pode **continuar** marcando entregas temporais. A Fase 3.5 é a camada de RITMO que sustenta todos os 7 ciclos, não substitui nenhum.

---

### FASE 4 — DESENVOLVIMENTO (Dia 5 — Habitantes)

**Quem:** agentes de execução definidos pela complexidade (com worktree, até 3 por vez, em ondas) + CRONOS (sempre, orquestrando) + SHIELD (revisão contínua)

Cada agente já tem seu mini-plano em `.delta-11/planos/[AGENTE]-plan.md` (criado pelo CRONOS na Fase 2.5) e **DEVE seguir exatamente o mini-plano**. Qualquer desvio precisa ser aprovado pelo CRONOS (que pode disparar o `code-architect` para avaliar impacto).

O SHIELD testa CONTINUAMENTE conforme as funcionalidades são entregues (não espera o final).

**Ciclo de cada tarefa (ordem única para todos os executores):**
```
INÍCIO
  Passo 0    ACK em .delta-11/ativacoes/ack-[NOME].txt
  Passo 0.VW conferir se nasceu na worktree
  Passo 0.3  travas: mkdir .delta-11/locks/[caminho--do--arquivo].lock
  Passo 0.5  ler as fatias permitidas do project-core + mini-plano + própria coluna do kanban
             + pesquisa-tecnica.md + própria base de conhecimento
EXECUÇÃO     seguir o mini-plano
FINALIZAÇÃO
  Passo 1a   atualizar memoria/[NOME]-produto.md (com a linha "autocritica: <caminho>")
  Passo 1b   acrescentar ao memoria/[NOME]-historia.md
  Passo 3.4  autocrítica (2 paradas) em .delta-11/logs/autocritica/
  Passo 3.5  build-validator
  Passo 3.7  contract-tester (gera E roda os testes de contrato do que mudou)
  Passo 3.8  SendMessage ao CRONOS pedindo a revisão do SHIELD
  Passo 3.9  liberar as travas
DEPOIS (CRONOS)
  dispara o SHIELD → SHIELD grava "[SHIELD] APROVADO T-XXX [AGENTE]" ou
  "[SHIELD] REPROVADO T-XXX [AGENTE] motivo" no activity-log → CRONOS atualiza o kanban
```

O executor NÃO escreve no `kanban.md` nem no `kanban-data.js`: só o CRONOS escreve neles.

**Validação contínua de build (REGRA OBRIGATÓRIA):**
Todo agente que escreve código (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT) **DEVE** disparar o sub-agente `build-validator` ANTES de dar a tarefa por concluída. Isso garante que erros de build são pegos na origem, não acumulados para o SHIELD descobrir depois.

- Se **PASS**: continua normalmente
- Se **FAIL com bloqueios**: corrige ANTES de concluir
- Se **FAIL só com avisos**: pode concluir, mas registra os avisos no `-produto.md`

**Monitoramento de desvio arquitetural (CRONOS — em todo projeto):**
Se o CRONOS percebe que um agente está demorando muito ou fazendo muitos commits, pode disparar o `code-architect` para verificar se o agente está seguindo o mini-plano ou improvisando. Se detectar desvio significativo, o CRONOS pode parar o agente e forçar replanejamento. Em projetos de BAIXA complexidade (5–8) o desvio costuma ser mais raro — mas a regra é a mesma.

**Ao final da Fase 4 (quando todos os agentes de desenvolvimento terminam):**
1. **Varredura preventiva (OBRIGATÓRIO):** o CRONOS dispara o SCOUT para varredura completa de todo o código antes da Fase 4.5. Busca: inicializações perigosas, contratos contornados, validações ausentes, links quebrados, condições de corrida, falhas de segurança.
2. **Auditoria arquitetural (OBRIGATÓRIO):** o CRONOS dispara o sub-agente `code-architect` para comparar código real vs arquitetura planejada no project-core. Se a nota for C ou pior, o CRONOS cria tarefas de correção no kanban antes de avançar. Se detectar problema estrutural que exige mudança de contrato, o CRONOS dispara o ATLAS.

**Resultado:** Todas as funcionalidades implementadas, aprovadas uma a uma pelo SHIELD, varridas pelo SCOUT, e auditadas arquiteturalmente. Problemas encontrados são corrigidos antes de avançar.

---

### FASE 4.5 — CONSCIÊNCIA DOMINANTE (Dia 6 — A Consciência Que Domina)

**Quem:** VAULT (auditoria imutável + parte de banco da LGPD) + ENGINE (limite de requisições, motor de regras, fluxos de aprovação) + FORM/PIXEL (telas de consentimento e aprovação) + BACK e FRONT (líderes que revisam) + SHIELD (revisa e sela), orquestrados pelo CRONOS. Decisões de negócio desta fase (quem é o encarregado de dados, quais operações exigem aprovação, texto da política de privacidade) são do comandante (situação 1). Papel de cada um: ver a tabela "PAPEL DE CADA AGENTE NAS FASES 3.5, 4.5 E 7" abaixo.

**Por que esta fase existe (v6.0):** antes da v6.0, o VAULT na Fase 3 entregava apenas autenticação básica + RLS. O Dia 6 da Metodologia Gênesis (a Consciência Dominante — única camada declarada *muito bom* no texto bíblico) exige que **depois que o código de funcionalidade existe** (Dia 5), a camada de governança consciente seja construída em cima dele: autenticação + autorização conscientes, motor de regras de negócio, auditoria imutável, limite de requisições, LGPD, fluxos de aprovação. Esta fase é o único dia com a expressão *tov meod* (muito bom) — o sistema não apenas funciona, funciona de forma responsável e auditável.

**Referências:**
- `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6
- Skills globais instaladas em `~/.claude/skills/`:
  - `owasp-top10` (5 CVEs incluindo CVE-2024-34351 e CVE-2025-29927) — referência obrigatória do SHIELD
  - `supabase-rls` (P6 multi-tenancy, P7 Custom Hook) — referência obrigatória do VAULT
  - Bases curtas: `.delta-11/conhecimento/owasp-top10-overview.md`, `.delta-11/conhecimento/supabase-rls-patterns.md`
- **Texto hebraico chave:** *naaseh adam be-tzalmenu ki-dmutenu* (façamos o homem em nossa imagem) · *zachar u-nekevá bara otam* (masculino e feminino criou-os) · *tov meod* (muito bom — único dia com esta expressão)

**Os 5 entregáveis do Dia 6 (todos verificados):**

1. **Auditoria imutável de ações** — sistema que registra *quem fez o quê e quando* com logs que só aceitam acréscimo (não editáveis). Diferente do Sentry (que captura erros) — aqui é auditoria de ações do usuário (criar, ler, alterar, apagar em entidades críticas). Para cada tabela com dados sensíveis, existe trigger ou middleware que registra a operação.

2. **Limite de requisições obrigatório por endpoint crítico** — login, registro, recuperação de senha, APIs que consomem crédito/enviam e-mail/SMS. Implementado como Chain of Responsibility após a autenticação (padrão documentado em `conhecimento/design-patterns-praticos.md`).

3. **Motor de regras de negócio central** — regras de negócio que estão espalhadas pelo código são extraídas para um módulo central (`src/lib/business-rules/`) OU há justificativa explícita de por que determinada regra é distribuída. Sem motor central, auditoria fica cara.

4. **Sistema de consentimento LGPD/GDPR** — banner de cookies opt-in, registro de consentimento, fluxo de exportação de dados pessoais do usuário (direito de acesso), fluxo de exclusão de dados (direito ao esquecimento), encarregado de dados (DPO) designado.

5. **Fluxos de aprovação para operações críticas** — apagar em massa, transações financeiras, mudança de papel/permissão, alteração de dados de outro usuário. Cada operação crítica tem um fluxo de aprovação explícito (um passo, vários passos, ou automático por regra).

**Quem sela:** SHIELD (auditoria + limite de requisições + teste cruzado). O CRONOS roda a cadeia de selo. Em `modo manual`, o comandante digita `aprovar`. Selo permite iniciar a Fase 5.

**Resultado:** os 5 entregáveis verificados com evidência (arquivos `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<NN>-<slug>.md`, `<NN>` de 01 a 05). Autenticação e autorização testadas com casos positivos e negativos. Logs de auditoria verificados como imutáveis. Limite de requisições ativo em todos os endpoints críticos. Fluxo LGPD testado de ponta a ponta.

**Arquivos relacionados:**
- `.delta-11/templates/fase-consciencia-template.md` — modelo dos 5 entregáveis
- `.delta-11/protocolos/fase-consciencia.md` — protocolo detalhado
- Hook bloqueante: `fase-consciencia-checker.py`

**Sobre as skills globais:** o conteúdo das skills `owasp-top10` e `supabase-rls` NÃO é duplicado aqui — o mini-plano de cada agente da fase cita a skill que ele deve consultar.

---

### FASE 5 — TESTES DE INTEGRAÇÃO (apoio)

**Quem:** SHIELD + SCOUT (se houver erros, disparado pelo CRONOS) + CRONOS (orquestrando — sempre)

O SHIELD executa testes de ponta a ponta: cada fluxo completo (usuário se cadastra → faz login → executa ação → vê resultado). Verifica coerência total entre interface, servidor, e banco — inclusive as camadas do Dia 6 (auditoria grava, limite de requisições recusa).

**Resultado:** Todos os fluxos passando nos testes. Todos os erros encontrados corrigidos.

---

### FASE 6 — PREPARAÇÃO PARA LANÇAMENTO (apoio — selo provisório de produção)

**Quem:** SHIELD + Comandante (o deploy é publicação externa — situação 3)

O SHIELD configura o ambiente de produção, executa auditoria de segurança, e prepara o relatório final.

**Antes do deploy final, o SHIELD dispara 2 sub-agentes em sequência:**
1. `build-validator` — validação completa (typecheck, lint, build, testes, audit, segredos)
2. `verify-app` — teste real no navegador (navegação, fluxos críticos, erros no console)

**E verifica o monitoramento de erros:** Sentry configurado + erro proposital de teste capturado no painel. Deploy de produção sem Sentry ativo = REPROVADO (ver checklist de deploy no SHIELD.md).

Somente se AMBOS os sub-agentes retornarem PASS e o Sentry estiver ativo, o deploy é apresentado ao comandante para aprovação (Regra 10).

**Resultado:** Sistema em produção. Começa o período de observação da Fase 7.

---

### FASE 7 — DESCANSO CONSAGRADO (Dia 7 — vayechulu, vayishbot)

**Quem:** SHIELD (pipeline, runbooks, monitoramento, release) + VAULT (backup e recuperação do banco) + BACK/ENGINE e FRONT (documentação técnica e onboarding) + ATLAS (documentação de domínio, disparado pelo CRONOS) + SCOUT (simulação de incidentes), orquestrados pelo CRONOS + Comandante (responde ao teste supremo). Papel de cada um: ver a tabela "PAPEL DE CADA AGENTE NAS FASES 3.5, 4.5 E 7" abaixo.
**Duração:** período de observação de 2 semanas em produção antes do selo final.

**Por que esta fase existe (v6.0):** antes da v6.0, o sistema TERMINAVA na Fase 6 com "Sistema em produção". Mas o Dia 7 da Metodologia Gênesis não é "terminar" — é **consagrar**. Os verbos hebraicos *vayechulu* (foram consumados) e *vayishbot* (cessou intencionalmente) descrevem o momento em que o sistema atinge operação autônoma. Sem a Fase 7, o criador vira refém: cada bug precisa dele, cada funcionalidade nova precisa dele, cada incidente às 3h da manhã precisa dele. A Fase 7 existe para **selar** o sistema em estado de operação autônoma.

**Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 7. Texto hebraico chave: *vayechulu ha-shamayim ve-ha-arets* (foram consumados os céus e a terra) · *vayishbot ba-yom ha-shvii* (cessou no sétimo dia) · *vayvarech* (abençoou) · *kadash* (santificou).

**Os 10 entregáveis do Dia 7 (todos verificados com EVIDÊNCIA):**

1. **Documentação técnica consumada** — arquitetura, decisões (ADRs), diagramas atualizados, guias de contribuição. Endereço: `docs/arquitetura/`, `.delta-11/memoria/decisoes/`
2. **Documentação de domínio consumada** — glossário do negócio, regras de negócio explicitadas, casos de uso descritos. Endereço: `docs/dominio/` ou `docs/comandante/`
3. **Testes de aceitação E2E** — fluxos críticos cobertos com testes automatizados que rodam em CI. Pelo menos os 5 fluxos mais importantes do produto
4. **Pipeline de deploy automatizado** — de commit até produção, sem intervenção manual. Funciona em staging E produção
5. **Runbooks operacionais específicos do projeto** — instanciados da skill global `owasp-top10` (`~/.claude/skills/owasp-top10/references/07-incident-response.md`) ou criados especificamente. Cobrem os 5 incidentes mais prováveis do produto. Em `.delta-11/memoria/runbooks/`
6. **Monitoramento com painéis + alertas ativos** — painéis visíveis para as metas de serviço do produto, alertas configurados COM dono (quem recebe notificação), níveis INFO/WARN/CRITICAL
7. **Tag de release** — git tag marcado, changelog de release publicado, binário/artefato arquivado
8. **Backup testado** — rotina de backup rodando, última restauração executada e evidenciada (não é teórica)
9. **Recuperação de desastre testada** — executada em ambiente isolado, tempo de recuperação (RTO) medido
10. **Onboarding testado com pessoa nova** — pelo menos 1 pessoa nova leu a doc e conseguiu subir o projeto local + 1 alteração pequena em menos de 1 dia

**O TESTE SUPREMO (critério de selo diferenciador do Dia 7):**

> *"Se o criador tirar 2 semanas de férias sem tocar no sistema, ele continua funcionando?"*

O prazo é **2 semanas** — o mesmo em todo o sistema. Se SIM → Dia 7 selado. Se NÃO → o sistema **não consagra**. Voltar e consertar o que falta (geralmente: runbook ausente, alerta sem dono, backup não testado).

**Incidente durante o período de observação:** é tratado DENTRO da Fase 7 (não existe "Fase 7.5"). Ver a seção "Incidente durante o período de observação" em `.delta-11/protocolos/fase-descanso.md`.

**Quem sela:** o comandante responde ao teste supremo (ele é o "criador" que se afasta) e o SHIELD confere os 10 entregáveis. O selo **só é declarado** após 2 semanas de operação estável em produção.

**Memória entre projetos:** ao fechar a Fase 7 (e ao fim de cada ciclo), o CRONOS acrescenta de 3 a 5 lições ao arquivo `~/.delta-11/aprendizados-entre-projetos.md`, com o nome do projeto e a data. É esse arquivo que o ATLAS lê nas Fases 0 e 2 do próximo projeto.

**Resultado:** os 10 entregáveis verificados com evidência; 2 semanas de operação estável sem intervenção; teste supremo respondido SIM; tag de release consolidada; lições registradas.

**Arquivos relacionados:**
- `.delta-11/templates/fase-descanso-template.md` — modelo dos 10 entregáveis
- `.delta-11/protocolos/fase-descanso.md` — protocolo detalhado
- Hook bloqueante: `fase-descanso-checker.py`
- `monitor-delta11.sh` sinaliza "operação autônoma estável" depois de 2 semanas

**Sobre a Fase 6 anterior:** a Fase 6 (Preparação para Lançamento) é o **selo provisório** que permite colocar em produção. A Fase 7 (Descanso) é o **selo definitivo** que fecha o ciclo. Entre as duas, o sistema precisa operar de verdade em produção por 2 semanas.

---

## PAPEL DE CADA AGENTE NAS FASES 3.5, 4.5 E 7

Todo executor sabe que estas três fases existem e o que entrega nelas. O CRONOS escreve essas tarefas no mini-plano de cada um; o nome do arquivo de cada entregável segue o padrão `AAAA-MM-DD-<fase>-<NN>-<slug>.md` em `.delta-11/memoria/decisoes/` (os hooks de fase contam os arquivos por esse nome).

| Agente | Fase 3.5 — Ritmo (10 artefatos `ritmo-temporal-NN`) | Fase 4.5 — Consciência (5 entregáveis `consciencia-NN`) | Fase 7 — Descanso (10 entregáveis `descanso-NN`) |
|---|---|---|---|
| **BACK** | Líder técnico da fase. Escreve 01 (eventos), 02 (filas) e 10 (sub-contraposição); revisa ENGINE e VAULT; declara SUSTENTA | Revisa o trabalho de ENGINE e VAULT; decide o que é "regra distribuída por design" no 03 | 01 (documentação técnica do servidor: README, ADRs) |
| **ENGINE** | 03 (jobs agendados), 05 (tempos-limite), 06 (novas tentativas), 07 (circuit breakers) | 02 (limite de requisições), 03 (motor de regras em `src/lib/business-rules/`), 05 (fluxos de aprovação no servidor), rotas de exportação/exclusão do 04 | Runbooks das integrações externas (parte do 05) |
| **VAULT** | 04 (cache e invalidação ligada aos dados) e a parte de banco do 03 e do 05 | 01 (auditoria imutável: `audit_log` só-acréscimo, gatilhos, RLS) e a parte de banco do 04 (exportar/apagar dados) | 08 (backup com restauração testada) e 09 (recuperação de desastre do banco, RTO/RPO) |
| **FRONT** | Não escreve artefato; lê 01, 04 e 05 para os estados de carregando/erro da interface | Revisa PIXEL e FORM | 01 (documentação da interface) e 10 (onboarding: "como mudar um texto de botão") |
| **PIXEL** | Não escreve artefato; aplica os estados de carregando/erro | Banner de cookies e telas de aprovação/histórico (04 e 05) | Apoia o 10 (alteração pequena de interface documentada) |
| **FORM** | Não escreve artefato; aplica tempos-limite e novas tentativas nos envios | Telas de consentimento, pedido de exportação/exclusão e pedido de aprovação (04 e 05) | Apoia o 10 |
| **SHIELD** | 08 (CI/CD em staging) e 09 (observabilidade); revisa os 10 | Sela 01 e 02; teste cruzado (o `audit_log` grava; a 6ª tentativa de login é recusada) | 03 (E2E em CI), 04 (deploy automatizado com volta atrás), 05 (runbooks), 06 (painéis e alertas), 07 (tag de release); confere os 10 |
| **SCOUT** | Teste adversarial: derruba uma dependência e confere se o circuit breaker abre | Tenta contornar autorização, limite de requisições e aprovação | Simula os incidentes dos runbooks (teste de mesa) |
| **ATLAS** | — | Só se faltar regra de negócio no project-core (o CRONOS o dispara) | 02 (documentação de domínio: glossário e regras em prosa), disparado pelo CRONOS |
| **CRONOS** | Orquestra, roda a cadeia de selo | Orquestra, roda a cadeia de selo | Orquestra, abre o período de observação de 2 semanas, registra as lições entre projetos |

Em projetos de BAIXA complexidade, o BACK faz também o papel de ENGINE e VAULT, e o FRONT o de PIXEL e FORM.

---

## COMO UMA FASE É SELADA (todas)

1. Todas as tarefas da fase com `[SHIELD] APROVADO` no activity-log.
2. O CRONOS dispara o `fresh-reviewer` (olhos virgens).
3. O CRONOS dispara o `cold-start-tester`, uma vez para cada `[AGENTE]-produto.md` da fase.
4. Se a fase tem interface navegável, o CRONOS dispara o `qa-ui-tandem` (selo experiencial pelo Tandem Browser).
5. Os hooks de fase conferem os critérios objetivos (`pre-selo.py`, `validar-contratos-fim-fase.py`, `contraposicao-checker.py` e o checker da fase, quando houver).
6. Modo `automatico` (padrão): tudo verde → o CRONOS escreve `memoria/CRONOS-abertura-fase-N.md` e abre a próxima fase sozinho. Qualquer sinal vermelho → o CRONOS cria tarefas de correção e a fase volta para execução. Modo `manual`: o CRONOS mostra o relatório ao comandante e espera `aprovar`.

---

## RESUMO DAS 13 FASES DO FLUXO (v6.3)

```
Fase  Nome                              Dia da Criação
0     Descoberta e Design               Dia 1 — Luz
1     Recepção e Classificação          apoio (fora dos Dias)
2     Arquitetura e Contratos           Dia 2 — Container (selo provisório; inclui o Passo 2.7 do SHIELD)
2.3   Pesquisa Técnica                  apoio
2.4   Provisionamento de Ferramentas    apoio
2.5   Sequenciamento e Mini-planos      apoio
3     Fundação                          Dia 3 — Superfícies (+ validação retroativa do Dia 2)
3.5   Ritmo Temporal                    Dia 4 — Astros
4     Desenvolvimento                   Dia 5 — Habitantes
4.5   Consciência Dominante             Dia 6 — Consciência
5     Testes de Integração              apoio (confere os Dias 5 e 6 juntos)
6     Preparação para Lançamento        apoio (selo provisório de produção)
7     Descanso Consagrado               Dia 7 — Descanso (teste supremo de 2 semanas)
```

**Princípio 1 (Ordem Inegociável):** respeitado. Cada Dia só começa após o anterior selado; as fases de apoio ficam entre os Dias sem trocar a ordem deles.

**Princípio 2 (Selagem por critérios):** cada Dia tem critério objetivo de selo. O Dia 2 tem selagem provisória com validação retroativa obrigatória pelo Dia 3.

**Princípio 3 (Contraposição Lateral):** verificado pelo hook `contraposicao-checker.py`.
