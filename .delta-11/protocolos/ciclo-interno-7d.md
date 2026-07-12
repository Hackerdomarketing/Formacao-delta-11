# Protocolo do Ciclo Interno de 7 Sub-Etapas

> **Protocolo replicável que toda fase do D-11 (0 a 7) deve executar internamente.**
> **Esta é a materialização da fractalidade da Criação: cada fase contém as 7 sub-etapas.**
>
> **Cross-references:**
> - Base conceitual: `.delta-11/conhecimento/metodologia-genesis-camadas.md` → seção "O Ciclo Interno de 7 Sub-Etapas"
> - Template parametrizado: `.delta-11/templates/ciclo-interno-template.md`
> - Operativo do ATLAS menciona estrutura fractal (Fases ↔ Sub-etapas) em `operativos/ATLAS.md:386-403`

## Por que este protocolo existe

A Metodologia Gênesis afirma que cada um dos 7 dias "segue o mesmo ciclo interno de sete sub-etapas" (do documento da Metodologia). Isso significa: não basta fazer a Fase 3 — a Fase 3 TEM que internamente passar por planejamento → delegação → execução → comunicação → revisão → teste → selo.

**Problema que resolve:** agentes tendem a pular sub-etapas. Em vez de fazer revisão cruzada (sub-etapa 5), eles auto-aprovam o próprio trabalho. Em vez de fazer teste adversarial (sub-etapa 6), eles pulam direto pro selo (sub-etapa 7). O resultado é trabalho sem selagem real.

**Como este protocolo se aplica:** cada agente/gate (ATLAS, CRONOS, SHIELD, executor) é instado a verificar que as 7 sub-etapas foram seguidas. Não há hook técnico automático (esta etapa é mais leve), mas o **template `ciclo-interno-template.md`** é obrigatório em cada mini-plano gerado pelo CRONOS.

## As 7 sub-etapas em detalhe

### Sub-etapa 1 — Planejamento baseado na fase anterior selada

**O que:** olhar explicitamente o `Selo` da fase anterior antes de começar. Sem isso, a fase nasce **cega** — não sabe o que já existe.

**Pergunta concreta:** "O que a fase anterior deixou pronto que eu construo em cima?"

**Local da evidência:** o mini-plano do agente (gerado pelo CRONOS) deve citar o `[AGENTE-ANTERIOR]-produto.md` na seção 2 ("Recorte relevante da fase anterior").

**Erro comum:** começar do zero sem ler o estado anterior. Gera retrabalho.

### Sub-etapa 2 — Delegação com contexto isolado

**O que:** o especialista que vai executar recebe apenas o **recorte necessário** para a fase — não o contexto inteiro do projeto. Sem isso, contexto polui e a fase perde foco.

**Mecanismo no D-11:** o hook `pre-leitura.py` (PreToolUse Read) BLOQUEIA leituras que escapam do escopo do agente. Mas isso é só o lado técnico — conceitualmente, o mini-plano deve citar fontes com etiqueta `[Fonte: arquivo#seção]` (regra v5.3) e omitir contexto desnecessário.

**Pergunta concreta:** "O que eu NÃO preciso saber para executar esta tarefa?"

**Erro comum:** copiar o `project-core.md` inteiro para o mini-plano. Dilui foco, aumenta tokens.

### Sub-etapa 3 — Execução paralela dos especialistas

**O que:** quando há múltiplos especialistas a executar a fase, eles rodam **em paralelo**, não em fila. Sem isso, fases viram gargalo sequencial.

**Mecanismo no D-11:** o CRONOS dispara via `Agent tool` com `run_in_background: true` e `isolation: worktree`. Até 3 agentes simultâneos. Cada agente recebe seu mini-plano independente.

**Atenção:** paralelismo não é anarquia. Cada agente ainda segue seu mini-plano com escopo bem definido (Limits of Scope, seção 5 do template mini-plano-agente).

**Erro comum:** executar agentes em série "para evitar confusão". Mata velocidade.

### Sub-etapa 4 — Comunicação entre executores dentro do escopo da fase

**O que:** descobrir dependências cruzadas entre os trabalhos dos agentes, **sem sair do escopo da fase**. Sem isso, agentes paralelos pisam uns nos outros ou deixam gaps.

**Mecanismo no D-11:** `SendMessage` entre agentes da mesma fase. Os 3 da onda, por exemplo, podem trocar mensagens sobre "a tabela X está com campo Y a mais que precisamos, ou esperem a próxima onda atualizar".

**Pergunta concreta:** "Minha execução descobriu algo que afeta o trabalho de outro agente paralelo?"

**Atenção:** mensagens entre fases distintas NÃO são sub-etapa 4 — é coordenação CRONOS, diferente.

**Erro comum:** agentes não falam entre si, terminam各自的各自 (cada um seu), e o merge na branch principal entra em conflito.

### Sub-etapa 5 — Revisão cruzada externa

**O que:** alguém **de fora** (sem contexto de construção) verifica se o resultado faz sentido para quem chega de fora. Sem isso, auto-aprovação e contaminações passam.

**Mecanismo no D-11:** o `code-architect` é disparado ao final da Fase 4 (auditoria arquitetural). O `SHIELD` faz revisão contínua na Fase 4 (por cada tarefa concluída).

**Pergunta concreta:** "Quem pode olhar isso sem ter construído e dizer se faz sentido?"

**Erro comum:** agente se auto-aprova porque "é óbvio que está certo". Raramente é óbvio de fora.

### Sub-etapa 6 — Teste adversarial

**O que:** alguém **encarregado de tentar quebrar** o resultado, sem alinhamento com o autor. Sem isso, bugs sutis passam.

**Mecanismo no D-11:** o `SCOUT` faz varredura completa de todo o código antes da Fase 5 (final da Fase 4). O SHIELD tem cadeia obrigatória de sub-agentes (`build-validator` + `contract-tester`) por tarefa.

**Pergunta concreta:** "O que pode dar errado aqui que o autor não previu?"

**Atenção:** o teste adversarial não é "teste de aceitação do usuário final". É **destruição preventiva** — alguém cuja métrica de sucesso é encontrar bugs.

**Erro comum:** confundir com QA. QA testa se funciona; adversarial testa se quebra.

### Sub-etapa 7 — Selagem por critérios objetivos

**O que:** declarar a fase concluída **apenas** quando critérios verificáveis estão cumpridos. Sem isso, fase é "razoavelmente pronta" e vira drenagem de qualidade.

**Mecanismo no D-11:** cada fase tem seu critério de selo específico (definido no `fluxo-zero-ao-lancamento.md`). Hooks técnicos (`pre-selo.py`, `validar-contratos-fim-fase.py`, `contraposicao-checker.py`, hooks de fase) bloqueiam transição se critério não cumprido.

**Pergunta concreta:** "Esta fase tem critérios objetivos de selagem cumpridos, verificáveis por máquina, sem depender de auto-declaração?"

**Erro comum:** agente ou líder declara "está pronto" sem que critérios formais tenham sido cumpridos.

## Aplicação por fase

Cada fase do D-11 executa as 7 sub-etapas. Como o protocolo é replicável:

| Fase | Sub-etapa 1 (Plan) | Sub-etapa 2 (Deleg) | Sub-etapa 3 (Par) | Sub-etapa 4 (Com) | Sub-etapa 5 (Rev) | Sub-etapa 6 (Adv) | Sub-etapa 7 (Selo) |
|------|---|---|---|---|---|---|---|
| 0 — Descoberta | mini-plano do ATLAS | contexto da Fase 0 | descoberta + produto em paralelo | conversa entre ATLAS e Comandante | releitura do documento de visão | commander questiona superficialidade | Comandante aprova |
| 2 — Arquitetura | plano + ctx limites | mini-plano do ATLAS | design em paralelo (componentes, schemas) | feedback cruzado entre seções | code-architect valida plano | (não aplicável nesta fase) | SHIELD revisa contratos |
| 2.3 — Pesq Técnica | plano de pesquisa | brief dos sub-agentes | 3 sub-agentes em paralelo | consolidação no pesquisa-tecnica.md | CRONOS revisa | busca por armadilhas | CRONOS declara completa |
| 2.4 — Provisionamento | plano de tools | tool-provisioner brief | provisiona CADA tool | relatório único | CRONOS revisa | testa falhas | Commander aprova ou refaz |
| 2.5 — Sequenciamento | plano de ondas | mini-planos por agente | cronograma paralelo | dependências cruzadas | revision de mini-planos | smoke-test do plan | CRONOS pede aprovação |
| 3 — Fundação | plano do VAULT | mini-plano VAULT (e.SHIELD paralelo) | VAULT executa + SHIELD prepara | alinhamento em kanban | SHIELD valida migrations | tentar quebrar schema | VAULT + SHIELD selam |
| 3.5 — Ritmo | plano da Fase 3.5 | DevOps/SRE executa | (fase é 1 agente) | N/A | líder técnico revisa | tentar invadir dashboards | **10 artefatos** + selo |
| 4 — Desenvolvimento | mini-planos por agente | 8 agentes em paralelo (3 ondas) | execução paralela | SendMessage entre agentes | SHIELD revisa contínua | SCOUT varredura | build-validator + contract-tester |
| 4.5 — Consciência | plano da Fase 4.5 | SHIELD + Compliance + Produto | 3 em paralelo | alinham regras de negócio | SHIELD revisa segurança | SCOUT tenta bypass | **5 entregáveis** + selo |
| 5 — Testes Integração | plano de E2E | contextos isolados | (fase é 1 agente) | N/A | Commander valida UX | tentar quebrar fluxos | E2E verdes |
| 6 — Preparação | plano de deploy | contexto de produção | (fase é 1 agente) | N/A | SHIELD security audit | try-to-break pré-deploy | Sentry ativo + Commander aprova |
| 7 — Descanso | plano de consagração | 10 entregáveis | (fase é 1 agente) | N/A | Commander valida UX | monitor-delta11 detecta autonomia | **10 entregáveis + teste supremo** |

## O template `ciclo-interno-template.md`

Para aplicar o protocolo, **cada agente de execução usa o template** `.delta-11/templates/ciclo-interno-template.md`. O template tem 7 seções (uma por sub-etapa) com perguntas e entregáveis esperados.

O mini-plano gerado pelo CRONOS (em `.delta-11/planos/[AGENTE]-plan.md`) DEVE copiar/integrar o conteúdo do ciclo-interno-template. O template mini-plano-agente já tem seção 2 (sub-etapa 2 - Delegação com contexto isolado) e seção 5 (Limites de Escopo, relacionada à sub-etapa 2). Falta generalizar.

## Quando este protocolo pode ser simplificado

- **Projetos descartáveis:** pular sub-etapas 5 (revisão cruzada) e 6 (teste adversarial) é aceitável APENAS se for explicitamente declarado como descartável no kanban. Documentar.
- **Tarefas triviais:** editar README, atualizar versão, corrigir typo — apenas sub-etapas 1, 3 e 7 são obrigatórias. As outras são implícitas.

Em QUALQUER outro caso, TODAS as 7 sub-etapas. Sem atalho.

## Quem verifica que as 7 sub-etapas foram seguidas

- **CRONOS** verifica na geração do mini-plano (sub-etapas 1, 2)
- **SHIELD** verifica nas revisões (sub-etapas 5, 6, 7)
- **Comandante** valida a selagem (sub-etapa 7) via Comando `aprovar`
- **code-architect** é disparado em pontos críticos como revisor externo (sub-etapa 5)

## Manutenção

Mudanças aqui passam por:
1. Proposta via issue
2. Discussão em equipe
3. Decisão via ADR (raro — protocolo raramente muda)
4. Atualização deste arquivo + template

**Versão do protocolo:** v6.0.0 (2026-07-12)
**Manutenção:** manter sincronizado com `metodologia-genesis-camadas.md` (seção "O Ciclo Interno de 7 Sub-Etapas") e com `fluxo-zero-ao-lancamento.md` (que define selagem por fase).

---
*Este documento é IMUTÁVEL após publicação. Correções em ADIÇÕES POSTERIORES no CHANGELOG.*