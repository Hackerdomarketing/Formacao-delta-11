# Metodologia Gênesis para Construção de Software — Camadas Canônicas

> **Esta é a referência canônica da Metodologia Gênesis (Rafa Marks, v1.0) traduzida para o Sistema Δ-11 v6.0.**
> Se você é um agente Δ-11 e não sabe qual é a próxima camada a construir, comece aqui.
> **Cross-references:**
> - 3 skills globais instaladas em v5.4: `~/.claude/skills/supabase-rls/`, `~/.claude/skills/owasp-top10/`, `~/.claude/skills/react-next/`. Índice: `.delta-11/conhecimento/skills-globais-v5-4.md`.
> - Auditoria que fundamentou este documento: `.delta-11/memoria/decisoes/2026-07-10-auditoria-delta-11-vs-metodologia-genesis.md`.
> - Fonte original (Gênesis 1-2, Texto Massorético hebraico) preservada em cada Dia.

## TL;DR — A Geometria em 1 página

Software alcança o **Descanso Consagrado do Dia 7** (operação autônoma) **somente** se as 7 camadas forem construídas em ordem, cada uma **selada por critérios objetivos**, e cada uma declarar sua **contraposição lateral** do tipo específico correto. Sem ordem, sem selagem ou sem contraposição, o software vira refém do criador.

---

## Os 3 Princípios Fundamentais

### Princípio 1 — Ordem Inegociável

Da luz ao descanso, do externo ao interno. Cada camada só pode existir depois que a camada externa que a envolve foi criada e nomeada com nitidez. **Peixes não foram criados antes das águas. Código não é escrito antes do ritmo temporal.**

**Aplicação no D-11:** as 13 fases do fluxo (0, 1, 2, 2.3, 2.4, 2.5, 2.7, 3, 3.5, 4, 4.5, 5, 6, 7) são executadas em ordem. Os 7 Dias correspondem a 7 delas — Dia 1 = Fase 0, Dia 2 = Fase 2, Dia 3 = Fase 3, Dia 4 = Fase 3.5, Dia 5 = Fase 4, Dia 6 = Fase 4.5, Dia 7 = Fase 7; as Fases 1, 2.x, 5 e 6 são fases de apoio, fora dos Dias. Nenhuma fase pode ser pulada (Regra Inviolável 1 + hooks técnicos `pre-selo.py` e `validar-contratos-fim-fase.py`).

### Princípio 2 — Selagem Antes da Próxima Camada

"Selado" = a camada tem **capacidade estrutural completa** de sustentar o peso de tudo que virá dentro dela. Não é "razoavelmente pronto". É "qualquer camada interna pode ser construída em cima sem risco de rachar".

**Aplicação no D-11:** cada fase termina com critério de selo explícito. v6.0 adiciona o **Critério de Selo Específico por Dia da Metodologia** (ver Seção "Critérios Objetivos de Selo" abaixo). O Dia 2 (Container) tem selagem **provisória** com validação retroativa obrigatória pelo Dia 3 — alinhado com o fato bíblico de que Gênesis não declara o Dia 2 "bom" isoladamente.

### Princípio 3 — Contraposição Lateral Obrigatória

Cada camada tem uma contraposição lateral **do tipo específico** daquela camada (existem 7 tipos). Sem declaração explícita da contraposição, a camada não está selada. **Este é o princípio mais ausente do D-11 pré-v6.0** — zero matches no `.delta-11/` antes desta versão. v6.0 corrige com hook `contraposicao-checker.py` (Etapa 3).

**Aplicação no D-11:** hook `contraposicao-checker.py` (PreToolUse, Edit/Write em `project-core.md`) bloqueia avanço se a contraposição lateral do tipo correto não estiver declarada.

---

## Os 7 Dias — Mapeamento Camada a Camada

### Dia 1 — A Luz (o Propósito Nuclear Encarnado)

**Texto hebraico chave:** *yehi or* (haja luz) · *vayavdel Elohim bein ha-or u-vein ha-choshech* (separou Deus entre luz e trevas) · *badal* (separar com nitidez absoluta)

**Camada no software:** propósito nuclear, frase interna decisória do usuário, identidade assumida vs identidade fugida (sem eliminação), único inimigo derrotado, único trauma curado, único lago abandonado, Nova Categoria de Solução estabelecida.

**Contraposição lateral — Tipo 1 (existencial-identitária):** identidade assumida contra identidade fugida. Teste do *vayavdel*: as duas identidades ficam nítidas entre si? **Sem eliminação**: o software faz separação com nitidez, não destrói a identidade antiga.

**Critério objetivo de selo:** as 8 perguntas obrigatórias (frase decisória, identidade assumida, identidade fugida, teste do badal, inimigo único, trauma único, lago abandonado, Nova Categoria) estão todas respondidas no PRD. Teste final: "se qualquer pessoa da equipe for perguntada sobre o propósito nuclear, todas respondem essencialmente a mesma coisa".

**Quem faz:** ATLAS (Facilitador) + Comandante. Janela única. Selado pelo Comandante.

**Referência no D-11:** Fase 0 do fluxo + `templates/fase-luz-template.md` (roteiro das 8 perguntas, v6.3) + seção 0 de `templates/prd-documento-de-requisitos-template.md` + seção VISÃO DO PRODUTO de `memoria/project-core.md` + hook `dia1-badal-checker.py` (exige 6 de 8 no PRD ou no project-core).

---

### Dia 2 — O Container (a Arquitetura Macro)

**Texto hebraico chave:** *yehi rakia be-toch ha-mayim* (haja firmamento no meio das águas) · *vayikra Elohim la-rakia shamayim* (chamou Deus ao firmamento Céus)

**Camada no software:** paradigma arquitetural escolhido (monolito modular, microsserviços, hexagonal, DDD, event-driven, camadas, serverless), fronteiras entre regiões do sistema, stack tecnológica fundacional, protocolos de comunicação, estrutura de repositório.

**Contraposição lateral — Tipo 2 (estrutural tripla com três elementos):** arquitetura sustentadora (firmamento) contra mundo externo (águas de cima: usuários, integrações, chamadas externas) contra mundo interno (águas de baixo: regras de negócio, dados persistentes, estado). Três elementos nomeados explicitamente.

**Critério objetivo de selo:** ADR principal escrito e revisado; mapa de bounded contexts desenhado; diagrama de fronteiras completo; protocolos de comunicação declarados; stack com justificativa; **selo provisório com nota explícita de validação retroativa**.

**Quem faz:** ATLAS (Arquiteto) + SHIELD (revisão) + líderes técnicos. Janela 1-2. Selo provisório do arquiteto, selo definitivo confirmado retroativamente no Dia 3.

**Referência no D-11 v6.0:** Fase 2 do fluxo + ADR template + hook `validar-arquitetura-vs-modelos.py` (Etapa 4) que força validação retroativa.

---

### Dia 3 — As Superfícies e a Vegetação (Schema, Modelos, Contratos)

**Texto hebraico chave:** *yikavu ha-mayim mi-tachat ha-shamayim el makom echad ve-tereh ha-yabashá* (congreguem-se as águas debaixo dos céus para um lugar e apareça a porção seca) · *essev mazria zera* (erva com semente exposta) vs *etz peri asher zarô-bo* (árvore com semente encapsulada)

**Camada no software:** schema de banco de dados completo, modelos de domínio (entidades, agregados, value objects, eventos), contratos de API (endpoints, payloads, responses), estrutura de pastas, tipos e interfaces, padrões reutilizáveis (componentes, funções puras, factories).

**Contraposição lateral — Tipo 3 (dupla, em duas dimensões):**
- Substância: estruturas sólidas persistentes (schema, entidades, tipos imutáveis) contra estruturas fluidas transientes (payloads em memória, filas, cache, sessão).
- Estrutural-reprodutiva: padrões de semente exposta (funções puras copy-pastáveis) contra padrões de semente encapsulada (fábricas, geradores, DSLs que viajam dentro do padrão).

**Critério objetivo de selo:** schema completo migrado em dev; modelos codificados; contratos formalizados (OpenAPI/proto/GraphQL); estrutura de pastas executada; dupla contraposição declarada. **E a verificação retroativa crítica:** o Dia 2 é retroativamente declarado "bom" junto com o Dia 3, OU refazer arquitetura antes de continuar.

**Quem faz:** VAULT + ENGINE/BACK + FRONT (em paralelo). Janela 2-3. Selo do VAULT + validação retroativa do Dia 2.

**Referência no D-11 v6.0:** Fase 3 do fluxo + `esquema-banco-template.md` + `contratos-api-template.md` + hook `validar-arquitetura-vs-modelos.py`.

---

### Dia 4 — Os Astros (o Ritmo Temporal do Sistema)

**Texto hebraico chave:** *yehi meorot bi-rekia ha-shamayim le-havdil bein ha-yom u-vein ha-laila* (haja luminares no firmamento para separar entre dia e noite) · *le-memshelet ha-yom u-le-memshelet ha-laila* (para governança do dia e para governança da noite)

**Camada no software:** sistema de eventos declarado, sistema de mensageria e filas, jobs agendados, estratégia de cache com TTL, timeouts, retries com backoff, circuit breakers, **CI/CD funcionando de ponta a ponta em staging**, observabilidade (logs estruturados, métricas, traces, dashboards), plano de resposta a incidentes.

**Contraposição lateral — Tipo 4 (funcional-temporal + sub-contraposição hierárquica):**
- Funcional-temporal: processos síncronos que governam tempo do usuário (HTTP, RPC, renderização) contra processos assíncronos que governam tempo do sistema (background jobs, workers, filas, scheduled tasks).
- Hierárquica: processos dominantes ativos (schedulers, dispatchers, orchestrators) contra processos testemunhas passivos (loggers, métricas, health checks, dashboards).

**Critério objetivo de selo:** os 10 artefatos obrigatórios declarados e verificados (eventos, filas, jobs, cache, timeouts, retries, circuit breakers, CI/CD em staging, observabilidade, sub-contraposição declarada).

**Quem faz:** CRONOS dispara; Engenheiro de DevOps/SRE + Líder Técnico. Janela 1. Selo do líder técnico (no `modo manual`, também o `aprovar` do Comandante).

**Referência no D-11 v6.0:** **Fase 3.5 (NOVA no v6.0)** + `protocolos/fase-ritmo.md` + `templates/fase-ritmo-template.md`. Esta fase **NÃO EXISTIA antes do v6.0** — é a correção do achado #4 (furo principal da auditoria).

---

### Dia 5 — Os Habitantes das Águas e do Ar (Serviços, Endpoints, Componentes)

**Texto hebraico chave:** *yishretzu ha-mayim sheretz nefesh chayá* (enxameiem as águas com enxames de alma vivente) · *ve-et kol of kanaf le-minehu* (e toda ave alada conforme sua espécie)

**Camada no software:** serviços de backend, endpoints, componentes de interface, integrações externas, workers, event listeners, código funcional efetivo.

**Contraposição lateral — Tipo 5 (territorial pura + escalar):**
- Territorial pura: habitantes de backend (território servidor) contra habitantes de frontend (território cliente).
- Escalar: componentes principais dominantes (páginas, agregados de domínio, endpoints críticos) contra componentes secundários (utilitários, helpers, formatadores).

**Critério objetivo de selo:** todos os habitantes principais implementados e testados; cobertura de testes acima do limiar; endpoints funcionando em staging com dados reais; componentes renderizando; integrações com credenciais de staging; contraposições declaradas.

**Quem faz:** CRONOS dispara; ENGINE/BACK + FRONT/PIXEL/FORM + SCOUT (em ondas paralelas, isolamento: worktree). Janela 2-7. Selo do SHIELD após revisão contínua.

**Referência no D-11 v6.0:** Fase 4 do fluxo + Zonas BANCO/API/UI + ondas + mini-planos + build-validator + autocrítica.

---

### Dia 6 — A Consciência Dominante (Autenticação, Autorização, Regras Conscientes)

**Texto hebraico chave:** *naaseh adam be-tzalmenu ki-dmutenu* (façamos o homem em nossa imagem conforme nossa semelhança) · *zachar u-nekevá bara otam* (masculino e feminino criou-os) · *tov meod* (muito bom — único dia com esta expressão)

**Camada no software:** sistema de autenticação (login, tokens, sessão, refresh, revogação), sistema de autorização (papéis, permissões, políticas, RBAC/ABAC), motor de regras de negócio central, sistema de auditoria com logs imutáveis, rate limiting, guardrails contra abuso, isolamento multi-tenant, validação profunda, fluxos de aprovação, sistema de consentimento LGPD/GDPR.

**Contraposição lateral — Tipo 6 (complementar + hierárquica):**
- Complementar: autenticação (verifica QUEM É — natureza de identificação) contra autorização (verifica O QUE PODE FAZER — natureza de permissão). Duas naturezas complementares; nenhuma sozinha é suficiente.
- Hierárquica: governança consciente (dominadores) sobre serviços e endpoints do Dia 5 (dominados).

**Critério objetivo de selo:** os 5 entregáveis verificados (auditoria imutável, rate limiting por endpoint crítico, motor de regras central, LGPD, fluxos de aprovação); auth e authz testadas positiva e negativamente; regras de negócio testadas com casos de borda; auditoria funcionando com logs imutáveis; rate limiting ativo; isolamento multi-tenant verificado; validação profunda passando.

**Quem faz:** CRONOS dispara; VAULT (auth + RLS) + SHIELD (auditoria) + Líder de produto (regras de negócio) + Especialista de compliance. Janela 1-2. Selo do SHIELD (no `modo manual`, também o `aprovar` do Comandante; regras de negócio que só ele pode decidir sobem para ele em qualquer modo — D4).

**Referência no D-11 v6.0:** **Fase 4.5 (NOVA no v6.0)** + `protocolos/fase-consciencia.md` + `templates/fase-consciencia-template.md` + integração com skills globais `owasp-top10` (5 CVEs, 47 testes) e `supabase-rls` (P6 multi-tenancy, P7 Custom Hook).

---

### Dia 7 — O Descanso Consagrado (Documentação Consumada, Operação Autônoma)

**Texto hebraico chave:** *vayechulu* (foram consumados) · *vayishbot* (cessou intencionalmente) · *vayvarech* (abençoou) · *kadash* (santificou)

**Camada no software:** documentação técnica + de domínio consumada, testes de aceitação E2E, pipeline de deploy automatizado, **runbooks operacionais específicos do projeto** (instanciados da base global), monitoramento com dashboards + alertas ativos, versionamento com tag de release, backups configurados e testados, plano de DR testado, onboarding de novos devs testado, **teste supremo** ("se o criador tirar 2 semanas de férias, o sistema continua?").

**Contraposição lateral — Tipo 7 (de estado):** sistema no estado de obra consumada (selada, versionada, documentada, testada, em operação estável) contra sistema no estado de trabalho em curso (em desenvolvimento ativo, sem consagração final). Ambos coexistiram dentro da história do software — houve um momento em que estava em curso, houve um momento em que ficou consumado.

**Critério objetivo de selo:** os 10 entregáveis verificados com evidência; **operação estável por pelo menos 2 semanas** sem intervenção do criador; tag de release consolidada; backup testado evidenciado; DR testado evidenciado; onboarding testado com pessoa nova; alertas configurados E ativos.

**Quem faz:** CRONOS orquestra; SHIELD (deploy + runbooks + monitoramento); Comandante (teste supremo de operação autônoma). Janela 1. Selo do Comandante + do líder técnico juntos.

**Referência no D-11 v6.0:** **Fase 7 (NOVA no v6.0)** + `protocolos/fase-descanso.md` + `templates/fase-descanso-template.md` + hook `fase-descanso-checker.py` + atualização do `monitor-delta11.sh` para detectar operação autônoma.

---

## O Ciclo Interno de 7 Sub-Etapas (replicável por fase)

Toda fase (não importa qual) executa internamente o mesmo ciclo de 7 sub-etapas. Inspirado na Geometria da Criação e em processos de engenharia verificados.

1. **Planejamento baseado na fase anterior selada** — olhar o Selo anterior antes de começar. Sem isso, a fase nasce cega.
2. **Delegação com contexto isolado** — o especialista recebe apenas o recorte necessário para o dia. Sem isso, contexto polui e a fase perde foco.
3. **Execução paralela dos especialistas** — backend, frontend, devops, dados em paralelo onde for possível. Sem isso, fases viram gargalo sequencial.
4. **Comunicação entre executores dentro da fase** — descobrir dependências cruzadas sem sair do escopo da fase.
5. **Revisão cruzada externa** — alguém de fora (sem contexto de construção) verifica se faz sentido para quem chega.
6. **Teste adversarial** — alguém encarregado de tentar quebrar o resultado.
7. **Selagem por critérios objetivos** — só então avançar. Ver Seção abaixo.

**Aplicação no D-11:** `protocolos/ciclo-interno-7d.md` + `templates/ciclo-interno-template.md` + seção "Checklist do ciclo interno" do `templates/mini-plano-agente-template.md`. A verificação do ciclo interno é feita pelo CRONOS (sub-etapas 1 e 2) e pelo SHIELD (5 a 7) pelo checklist do mini-plano; não há hook específico.

---

## Critérios Objetivos de Selo — Resumo por Dia

| Dia | Selo principal | Selo secundário | Quem sella | Quem valida retroativamente |
|-----|----------------|-----------------|------------|---------------------------|
| 1 — Luz | 8 perguntas obrigatórias respondidas | Teste "equipe responde igual sobre o propósito" | Comandante | — |
| 2 — Container | ADR + fronteiras + protocolos | **Selo provisório** com nota retroativa | Arquiteto | Dia 3 |
| 3 — Superfícies | Schema + modelos + contratos | **Retrovalidação do Dia 2** | VAULT + líder técnico | Dia 2 |
| 4 — Astros | 10 artefatos do Ritmo | Sub-contraposição declarada | Líder técnico (+ Comandante no `modo manual`) | — |
| 5 — Habitantes | Cobertura de testes + endpoints em staging | Sub-contraposição escalar | SHIELD | — |
| 6 — Consciência | 5 entregáveis verificados | Auth + Authz testadas (casos positivos e negativos) | SHIELD (+ Comandante no `modo manual`) | — |
| 7 — Descanso | 10 entregáveis + 2 semanas operação autônoma | Tag + backup testado + DR testado | Comandante + líder técnico | — |

### Ciclo 1 completo, Ciclos 2 a 7 leves (v6.4)

O projeto atravessa os 7 Dias **7 vezes** — uma por ciclo de entrega (Regra dos 7 Ciclos). A Ordem Inegociável vale dentro de cada ciclo, mas o que um Dia já construiu não precisa ser reconstruído do zero no ciclo seguinte:

- **Ciclo 1:** todos os Dias com os entregáveis completos (os 10 artefatos do Dia 4, os 5 do Dia 6...).
- **Ciclos 2 a 7:** o Dia 4 (Fase 3.5) e o Dia 6 (Fase 4.5) entregam UM checklist de 1 página cada (`templates/ritmo-temporal-checklist-template.md` e `templates/consciencia-checklist-template.md`): cada item diz "sem mudança" ou a mudança em até 3 linhas. Item cuja área o ciclo MEXE ganha o documento completo. As fases de apoio 2.3 e 2.4 só rodam para tecnologia ou ferramenta NOVA.
- **Dia 7 entre ciclos:** as 2 semanas de observação de um ciclo correm junto com o começo do ciclo seguinte; o selo final do Dia 7 vem quando elas terminam.
- **Selagem continua por critério objetivo:** os vigias aceitam o checklist do ciclo atual (a partir do Ciclo 2) como equivalente aos documentos; o SHIELD confere o que o vigia não consegue julgar (se a mudança exigia o documento completo).

Detalhes: `protocolos/fluxo-zero-ao-lancamento.md` (seção "Ciclos"), `protocolos/fase-ritmo.md` e `protocolos/fase-consciencia.md` (seção "Ciclo leve"), `protocolos/fase-descanso.md` ("A Fase 7 não trava o ciclo seguinte").

---

## Os 4 Sinais de "Fazendo Certo"

São testes VIVOS, executados a cada semana de projeto. Se algum falhar, voltar e consertar a camada correspondente.

**Sinal 1 — Energia diminuindo, não aumentando.** A cada dia consagrado, a energia necessária para consagrar o próximo dia DIMINUI. Se você sente que cada dia fica mais pesado, algum dia anterior foi selado com rachadura.

**Sinal 2 — Novos membros entendem sem você.** Se você é a única pessoa capaz de explicar o sistema, algum Selo anterior está frágil. Teste: peça para um dev novo ler a documentação e explicar o sistema de volta.

**Sinal 3 — Bug no dia N é resolvido no dia N.** Se um bug no Dia 5 exige mexer no Dia 2, o Dia 2 estava impreciso. Volte e refaça.

**Sinal 4 — Duas semanas sem você e o sistema continua.** O teste supremo do Dia 7. Se o sistema exige sua presença, o Dia 7 não foi alcançado. Volte e consagre.

---

## Mapeamento para o D-11 v6.0 (visão executiva)

| Dia | Fase no D-11 v6.0 | Novo no v6.0? | Hook bloqueante | Template |
|-----|-------------------|---------------|-----------------|----------|
| 1 — Luz | Fase 0 | Não (existente) | `dia1-badal-checker.py` (NOVO) | `fase-luz-template.md` (criado na v6.3) + PRD seção 0 |
| 2 — Container | Fase 2 | Não (existente) | `validar-arquitetura-vs-modelos.py` (NOVO, Etapa 4) | ADR (existente) |
| 3 — Superfícies | Fase 3 | Não (existente) | `validar-arquitetura-vs-modelos.py` (retroativa) | `esquema-banco-template.md` (existente) |
| 4 — Astros | **Fase 3.5 (NOVA)** | **SIM** | `fase-ritmo-checker.py` (NOVO, Etapa 5) | `fase-ritmo-template.md` (NOVO) |
| 5 — Habitantes | Fase 4 | Não (existente) | `pre-selo.py` + `validar-contratos-fim-fase.py` (existentes) | (existente) |
| 6 — Consciência | **Fase 4.5 (NOVA)** | **SIM** | `fase-consciencia-checker.py` (NOVO, Etapa 6) | `fase-consciencia-template.md` (NOVO) |
| 7 — Descanso | **Fase 7 (NOVA)** | **SIM** | `fase-descanso-checker.py` (NOVO, Etapa 7) | `fase-descanso-template.md` (NOVO) |
| Princípio 3 | (transversal) | **SIM** | `contraposicao-checker.py` (NOVO, Etapa 3) | (seção em cada Dia) |
| Sub-etapas | (transversal) | **SIM** | — (sem hook: CRONOS e SHIELD conferem) | `ciclo-interno-template.md` + checklist do mini-plano |

---

## Integração com Skills Globais v5.4

As 3 skills globais instaladas em v5.4 cobrem parcialmente 3 dos 7 dias:

- **`supabase-rls`** → Dia 6 (multi-tenancy, RLS, isolamento por linha). v6.0 **integra** a skill como referência obrigatória do VAULT, sem duplicar conteúdo.
- **`owasp-top10`** → Dia 6 (segurança, CVE-2024-34351, CVE-2025-29927, incident response). v6.0 **integra** a skill como referência obrigatória do SHIELD + inclui **10 runbooks de IR** disponíveis como base para instanciar runbooks específicos do projeto no Dia 7.
- **`react-next`** → Dia 5 (componentes, Server Actions, debugging). v6.0 **integra** a skill como referência do FRONT/PIXEL.

**Importante:** as skills globais NÃO substituem a necessidade de Fase 3.5 (Ritmo Temporal) e Fase 7 (Descanso). Cobrem **conteúdo de habilidades**, não **camadas estruturais**.

---

## Referências e Proveniência

- **Fonte primária:** Metodologia Gênesis para Construção de Software v1.0 (Rafa Marks, julho de 2026), recebida em sessão autônoma de auditoria em 2026-07-10.
- **Auditoria que fundamenta este documento:** `.delta-11/memoria/decisoes/2026-07-10-auditoria-delta-11-vs-metodologia-genesis.md`. Achados #1, #2, #3, #4, #5, #6, #7, #8 com evidência arquivo-linha-citação.
- **Plano de execução do v6.0:** registrado no `CHANGELOG.md` institucional como entrada **v6.0 — Alinhamento com Metodologia Gênesis**.
- **Infraestrutura de teste v5.4:** `.delta-11/tests/` — cada correção do v6.0 tem teste em `tests/` que falha antes e passa depois (TDD).

---

**Versão do documento:** v6.4 (2026-10-15) — ciclo leve do Ciclo 2 em diante; Dia 7 em paralelo com o ciclo seguinte. Antes: v6.3 (2026-10-14) — 13 fases, teste supremo de 2 semanas, `fase-luz-template.md` criado, sem hook de ciclo interno; v6.0.0 (2026-07-10)
**Manutenção:** Este documento é a referência canônica da Metodologia Gênesis dentro do D-11. Mudanças aqui devem ser propostas via ADR com aprovação do Comandante.
**Próxima revisão programada:** após 90 dias de uso em produção em pelo menos 1 projeto real.