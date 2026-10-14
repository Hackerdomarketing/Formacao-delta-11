# Protocolo do Ciclo Interno de 7 Sub-Etapas

> **Protocolo replicável que toda fase do D-11 (0 a 7) deve executar internamente.**
> **Esta é a materialização da fractalidade da Criação: cada fase contém as 7 sub-etapas.**
>
> **Cross-references:**
> - Base conceitual: `.delta-11/conhecimento/metodologia-genesis-camadas.md` → seção "O Ciclo Interno de 7 Sub-Etapas"
> - Template parametrizado: `.delta-11/templates/ciclo-interno-template.md`
> - Operativo do ATLAS menciona a estrutura fractal (Fases ↔ Sub-etapas) na seção sobre as fases internas
> - Mini-plano que carrega o checklist: `.delta-11/templates/mini-plano-agente-template.md` → `planos/[AGENTE]-plan.md`

## Por que este protocolo existe

A Metodologia Gênesis afirma que cada um dos 7 dias "segue o mesmo ciclo interno de sete sub-etapas" (do documento da Metodologia). Isso significa: não basta fazer a Fase 3 — a Fase 3 TEM que internamente passar por planejamento → delegação → execução → comunicação → revisão → teste → selo.

**Problema que resolve:** agentes tendem a pular sub-etapas. Em vez de fazer revisão cruzada (sub-etapa 5), eles auto-aprovam o próprio trabalho. Em vez de fazer teste adversarial (sub-etapa 6), eles pulam direto pro selo (sub-etapa 7). O resultado é trabalho sem selagem real.

**Como este protocolo se aplica:** cada agente (ATLAS, CRONOS, SHIELD, executor) verifica que as 7 sub-etapas foram seguidas. **Não existe hook (vigia automático) específico do ciclo interno.** A verificação é feita pelos próprios agentes, usando o checklist das 7 sub-etapas que o CRONOS coloca em todo mini-plano (`planos/[AGENTE]-plan.md`): o CRONOS confere as sub-etapas 1 e 2 ao montar o mini-plano, e o SHIELD confere as sub-etapas 5, 6 e 7 na revisão de cada tarefa e no selo da fase (ver "Quem verifica" no fim deste arquivo). Os hooks que existem cobram só pedaços: `pre-leitura.py` (sub-etapa 2) e `pre-selo.py`, `validar-contratos-fim-fase.py` e os checkers de fase (sub-etapa 7).

## As 7 sub-etapas em detalhe

### Sub-etapa 1 — Planejamento baseado na fase anterior selada

**O que:** olhar explicitamente o `Selo` da fase anterior antes de começar. Sem isso, a fase nasce **cega** — não sabe o que já existe.

**Pergunta concreta:** "O que a fase anterior deixou pronto que eu construo em cima?"

**Local da evidência:** o mini-plano do agente (gerado pelo CRONOS) cita o `[AGENTE-ANTERIOR]-produto.md` na seção 2 ("Recorte da fase anterior").

**Erro comum:** começar do zero sem ler o estado anterior. Gera retrabalho.

### Sub-etapa 2 — Delegação com contexto isolado

**O que:** o especialista que vai executar recebe apenas o **recorte necessário** para a fase — não o contexto inteiro do projeto. Sem isso, contexto polui e a fase perde foco.

**Mecanismo no D-11:** o hook `pre-leitura.py` (PreToolUse Read) BLOQUEIA leituras que escapam do escopo do agente — executores leem só as fatias do project-core do seu papel (`memoria/project-core/banco.md`, `contratos.md`, `visual.md`, `decisoes-tecnicas.md`), nunca o arquivo inteiro. Mas isso é só o lado técnico — conceitualmente, o mini-plano deve citar fontes com etiqueta `[Fonte: arquivo#seção]` e omitir contexto desnecessário (seção 5, Limites de escopo).

**Pergunta concreta:** "O que eu NÃO preciso saber para executar esta tarefa?"

**Erro comum:** copiar o project-core inteiro para o mini-plano. Dilui foco, aumenta tokens.

### Sub-etapa 3 — Execução paralela dos especialistas

**O que:** quando há múltiplos especialistas a executar a fase, eles rodam **em paralelo**, não em fila. Sem isso, fases viram gargalo sequencial.

**Mecanismo no D-11:** o CRONOS dispara os executores via `Agent tool` com `run_in_background: true` e `isolation: "worktree"`. Até 3 agentes simultâneos (`paralelo_max` em `.delta-11/.config-limites.json`). Cada agente recebe seu mini-plano independente.

**Atenção:** paralelismo não é anarquia. Cada agente ainda segue seu mini-plano com escopo bem definido (seção 5, Limites de escopo).

**Erro comum:** executar agentes em série "para evitar confusão". Mata velocidade.

### Sub-etapa 4 — Comunicação entre executores dentro do escopo da fase

**O que:** descobrir dependências cruzadas entre os trabalhos dos agentes, **sem sair do escopo da fase**. Sem isso, agentes paralelos pisam uns nos outros ou deixam gaps.

**Mecanismo no D-11:** `SendMessage` passando pelo CRONOS. O executor que descobre a dependência avisa o CRONOS (ex.: "a tabela X precisa do campo Y para a minha rota"); o CRONOS repassa ao agente afetado pelo `name` dele, ou dispara o ATLAS se a descoberta mexe no contrato. A mensagem é aviso; o registro fica no `-produto.md` de quem descobriu (e, se for o caso, na seção `PROPOSTAS PARA O PROJECT-CORE`).

**Pergunta concreta:** "Minha execução descobriu algo que afeta o trabalho de outro agente paralelo?"

**Atenção:** coordenação entre fases distintas NÃO é sub-etapa 4 — é a abertura de fase do CRONOS (`memoria/CRONOS-abertura-fase-N.md`).

**Erro comum:** cada agente termina o seu sem avisar ninguém, e o merge na branch principal entra em conflito.

### Sub-etapa 5 — Revisão cruzada externa

**O que:** alguém **de fora** (sem contexto de construção) verifica se o resultado faz sentido para quem chega de fora. Sem isso, auto-aprovação e contaminações passam.

**Mecanismo no D-11:** o `SHIELD` revisa cada tarefa concluída (linha `[SHIELD] APROVADO T-XXX [AGENTE]`). Ao fim de cada fase, o CRONOS dispara o `fresh-reviewer` (olhos virgens) e o `cold-start-tester`; ao final da Fase 4, também o `code-architect` (auditoria arquitetural).

**Pergunta concreta:** "Quem pode olhar isso sem ter construído e dizer se faz sentido?"

**Erro comum:** agente se auto-aprova porque "é óbvio que está certo". Raramente é óbvio de fora.

### Sub-etapa 6 — Teste adversarial

**O que:** alguém **encarregado de tentar quebrar** o resultado, sem alinhamento com o autor. Sem isso, bugs sutis passam.

**Mecanismo no D-11:** cada executor roda a cadeia obrigatória de sub-agentes por tarefa (`build-validator` no Passo 3.5 + `contract-tester` no Passo 3.7, que gera E roda os testes de contrato). Ao fim da Fase 4.5 (antes da Fase 5), o CRONOS dispara o `SCOUT` para a varredura completa de todo o código.

**Pergunta concreta:** "O que pode dar errado aqui que o autor não previu?"

**Atenção:** o teste adversarial não é "teste de aceitação do usuário final". É **destruição preventiva** — alguém cuja métrica de sucesso é encontrar bugs.

**Erro comum:** confundir com QA. QA testa se funciona; adversarial testa se quebra.

### Sub-etapa 7 — Selagem por critérios objetivos

**O que:** declarar a fase concluída **apenas** quando critérios verificáveis estão cumpridos. Sem isso, fase é "razoavelmente pronta" e vira drenagem de qualidade.

**Mecanismo no D-11:** cada fase tem seu critério de selo específico (definido no `fluxo-zero-ao-lancamento.md`, seção "Como uma fase é selada"). Hooks técnicos (`pre-selo.py`, `validar-contratos-fim-fase.py`, `contraposicao-checker.py`, checkers de fase) bloqueiam a transição se o critério não for cumprido. Em modo `automatico`, o CRONOS sela quando tudo está verde; em `modo manual`, o comandante digita `aprovar`.

**Pergunta concreta:** "Esta fase tem critérios objetivos de selagem cumpridos, verificáveis por máquina, sem depender de auto-declaração?"

**Erro comum:** agente ou líder declara "está pronto" sem que critérios formais tenham sido cumpridos.

## Aplicação por fase

Cada fase do D-11 executa as 7 sub-etapas. Como o protocolo é replicável:

| Fase | Sub-etapa 1 (Plano) | Sub-etapa 2 (Delegação) | Sub-etapa 3 (Paralelo) | Sub-etapa 4 (Comunicação) | Sub-etapa 5 (Revisão) | Sub-etapa 6 (Adversarial) | Sub-etapa 7 (Selo) |
|------|---|---|---|---|---|---|---|
| 0 — Descoberta | roteiro de perguntas do ATLAS (+ aprendizados entre projetos) | contexto da Fase 0 | descoberta + produto em paralelo | conversa entre ATLAS e comandante | releitura do documento de visão | comandante questiona superficialidade | comandante aprova a visão (decisão de negócio) |
| 1 — Classificação | régua de `classificacao.md` | só o PRD e a visão | (fase é 1 agente) | N/A | ATLAS confere cada critério | testar o score contra o caso mais exigente | classificação registrada no project-core |
| 2 — Arquitetura | plano + limites de contexto | ATLAS escreve as fatias do project-core | desenho em paralelo (componentes, esquemas) | retorno cruzado entre seções | SHIELD revisa contratos (disparado pelo CRONOS) | contract-tester (Passo 2.7) | selo provisório; confirmado no Dia 3 |
| 2.3 — Pesquisa Técnica | plano de pesquisa | brief dos sub-agentes | até 3 sub-agentes em paralelo | consolidação no `pesquisa-tecnica.md` | CRONOS revisa | busca por armadilhas e CVEs | CRONOS declara completa |
| 2.4 — Provisionamento | plano de ferramentas | brief do tool-provisioner | provisiona CADA ferramenta | relatório único | CRONOS revisa | testa falhas com chamada real | CRONOS sela; comandante só entrega credenciais |
| 2.5 — Sequenciamento | plano de ondas | mini-planos por agente | cronograma paralelo | dependências cruzadas | code-architect (opcional) | teste a seco do plano | CRONOS sela (`modo manual`: comandante aprova) |
| 3 — Fundação | mini-plano do VAULT | mini-plano VAULT (+ SHIELD em paralelo) | VAULT executa + SHIELD prepara | avisos pelo CRONOS | SHIELD revisa migrations | schema-validator + tentar quebrar o esquema | SHIELD APROVADO + SUSTENTA do Dia 2 |
| 3.5 — Ritmo | mini-planos da Fase 3.5 | BACK, ENGINE, VAULT, SHIELD com artefatos próprios | até 3 em paralelo | avisos pelo CRONOS | SHIELD revisa os 10 | SCOUT derruba uma dependência | **10 artefatos** + SUSTENTA do BACK |
| 4 — Desenvolvimento | mini-planos por agente | até 3 executores por vez, em ondas | execução paralela | avisos pelo CRONOS | SHIELD revisa cada tarefa + code-architect no fim | build-validator + contract-tester por tarefa | SHIELD APROVADO em todas + cadeia de selo |
| 4.5 — Consciência | mini-planos da Fase 4.5 | VAULT, ENGINE, FORM/PIXEL | até 3 em paralelo | alinham regras de negócio via CRONOS | SHIELD revisa segurança | varredura completa do SCOUT (tenta contornar) | **5 entregáveis** + selo do SHIELD |
| 5 — Testes Integração | plano de E2E | contextos isolados | (fase é 1 agente) | N/A | fresh-reviewer + qa-ui-tandem | tentar quebrar fluxos | E2E verdes |
| 6 — Preparação | plano de deploy | contexto de produção | (fase é 1 agente) | N/A | SHIELD audita segurança | verify-app pré-deploy | Sentry ativo + comandante aprova o deploy |
| 7 — Descanso | plano de consagração | 10 entregáveis distribuídos | até 3 em paralelo | avisos pelo CRONOS | fresh-reviewer + pessoa nova (onboarding) | SCOUT simula incidentes; monitor detecta autonomia | **10 entregáveis + teste supremo de 2 semanas** |

## O template `ciclo-interno-template.md` e o mini-plano

Para aplicar o protocolo, o CRONOS usa o template `.delta-11/templates/ciclo-interno-template.md` (uma seção por sub-etapa, com perguntas e entregáveis esperados).

O encaixe com o mini-plano está **integrado**: todo mini-plano gerado pelo CRONOS em `.delta-11/planos/[AGENTE]-plan.md` (um arquivo por agente, sobrescrito a cada onda; o anterior vai para `planos/arquivo/`) tem as 6 seções — 1 Objetivo da onda; 2 Recorte da fase anterior (sub-etapa 1); 3 Tarefas; 4 Critérios de aceite (sub-etapa 7); 5 Limites de escopo (sub-etapa 2); 6 Convenções — e termina com o **checklist das 7 sub-etapas** copiado do `ciclo-interno-template.md`. O agente marca o checklist; o CRONOS e o SHIELD conferem.

## Quando este protocolo pode ser simplificado

- **Projetos descartáveis:** pular sub-etapas 5 (revisão cruzada) e 6 (teste adversarial) é aceitável APENAS se o projeto for explicitamente declarado como descartável — o CRONOS registra isso no kanban e no mini-plano.
- **Tarefas triviais:** editar README, atualizar versão, corrigir typo — apenas sub-etapas 1, 3 e 7 são obrigatórias. As outras são implícitas.

Em QUALQUER outro caso, TODAS as 7 sub-etapas. Sem atalho.

## Quem verifica que as 7 sub-etapas foram seguidas

- **CRONOS** verifica na geração do mini-plano (sub-etapas 1, 2) e na cadeia de selo (sub-etapa 7)
- **SHIELD** verifica nas revisões, pelo checklist do mini-plano (sub-etapas 5, 6, 7)
- **Comandante** só valida a selagem (sub-etapa 7) com o comando `aprovar` quando o projeto está em `modo manual`
- **fresh-reviewer** e **code-architect** são disparados pelo CRONOS como revisores externos (sub-etapa 5)

Não há hook automático do ciclo interno: se um dia for criado, ele deve ler o checklist do mini-plano (proposta registrada no relatório da v6.3).

## Manutenção

Mudanças aqui passam por:
1. Proposta via issue
2. Discussão em equipe
3. Decisão via ADR (raro — protocolo raramente muda)
4. Atualização deste arquivo + template

**Versão do protocolo:** v6.3 (2026-10-14) — Correção Geral. Criado na v6.0.0 (2026-07-12).
**Manutenção:** manter sincronizado com `metodologia-genesis-camadas.md` (seção "O Ciclo Interno de 7 Sub-Etapas") e com `fluxo-zero-ao-lancamento.md` (que define selagem por fase).

---
*Mudanças neste protocolo são registradas no CHANGELOG (última: v6.3).*