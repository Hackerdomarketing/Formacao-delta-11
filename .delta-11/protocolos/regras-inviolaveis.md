# REGRAS INVIOLÁVEIS — FORMAÇÃO Δ-11 (v6.4)

Esta é a **lista oficial**: 17 regras, com esta numeração. "Violar a Regra N" sempre se refere a este arquivo. O CLAUDE.md mostra as mesmas 17, uma linha cada, ou remete para cá. Nenhum agente pode quebrá-las sob nenhuma circunstância.

## 1. NUNCA CODIFICAR ANTES DE PLANEJAR
Nenhum agente escreve código antes de o ATLAS ter fechado a visão com o comandante (Fase 0), feito a classificação (Fase 1) e definido a arquitetura e os contratos (Fase 2), e de o CRONOS ter montado os mini-planos (Fase 2.5). Em `modo manual`, cada uma dessas fronteiras também espera o `aprovar` do comandante.

## 2. BANCO DE DADOS E INFRAESTRUTURA ANTES DE TUDO
O VAULT completa a fundação (banco, autenticação, políticas de segurança) antes de qualquer agente de funcionalidade começar. Sem exceção.

## 3. CONTRATO DE INTERFACE DE PROGRAMAÇÃO DE APLICAÇÕES É LEI
O project-core (`memoria/project-core.md` e as fatias em `memoria/project-core/`) é a verdade do CONTRATO: o que deve ser. Interface e servidor seguem EXATAMENTE o contrato. Mudanças passam obrigatoriamente pelo ATLAS — só ele escreve o project-core. As migrations são a verdade do banco IMPLEMENTADO: o que é. Se as duas divergirem, é um bug: o CRONOS dispara o ATLAS para decidir.

## 4. REGRA DAS TRÊS TENTATIVAS
Todo agente tenta no máximo 3 vezes antes de escalar ao CRONOS. Se o SCOUT não corrigiu um erro em 3 tentativas, ele para obrigatoriamente e avisa o CRONOS. O CRONOS dispara um NOVO SCOUT com contexto limpo (só o resumo do problema). Depois de 6 falhas no total, o CRONOS dispara o ATLAS e, se preciso, avisa o comandante. SCOUT nunca dispara SCOUT. Detalhes em `correcao-de-erros.md`.

## 5. TESTES NÃO SÃO OPCIONAIS
Nenhuma funcionalidade está concluída sem aprovação do SHIELD. Todos os executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT) passam pela revisão, que é feita por onda, com veredito por tarefa. A aprovação é a linha `[SHIELD] APROVADO T-XXX [AGENTE]` no activity-log; reprovação é `[SHIELD] REPROVADO T-XXX [AGENTE] motivo`. O SHIELD reprova código e contrato (o que é falso, contradiz o contrato ou deixa risco técnico), nunca a redação de um documento. Sem testes, sem conclusão.

## 6. CADA AGENTE ATUALIZA SUA MEMÓRIA; SÓ O CRONOS ATUALIZA O KANBAN
Ao terminar qualquer tarefa, o agente OBRIGATORIAMENTE atualiza `memoria/[NOME]-produto.md` (o que existe agora; até 500 tokens para executores) e acrescenta ao `memoria/[NOME]-historia.md` (diário). Depois avisa o CRONOS por `SendMessage`. Só o CRONOS escreve `kanban.md` e `kanban-data.js`. O antigo `[NOME]-estado.md` é legado: pode ser lido, nunca escrito.

## 7. NENHUM AGENTE ALTERA ESTRUTURA SEM ATLAS
Mudanças em banco, autenticação, contratos, ou módulos fundamentais requerem aprovação do ATLAS. Quem precisa de uma mudança escreve na seção `PROPOSTAS PARA O PROJECT-CORE` do seu `-produto.md`; o CRONOS encaminha ao ATLAS.

## 8. SEMPRE LEIA SUA MEMÓRIA ANTES DE TRABALHAR
Antes de iniciar qualquer tarefa, leia o seu `-produto.md` (e o `-estado.md` legado, se existir), o seu mini-plano (`planos/[NOME]-plan.md`) e as fatias do project-core permitidas para o seu papel, para não repetir trabalho feito nem desfazer algo já completado.

## 9. COMUNICAÇÃO ENTRE INTERFACE E SERVIDOR SEMPRE VIA CONTRATO
Nenhum agente de interface combina informalmente com agente de servidor sobre formato de dados. Tudo passa pelo contrato formal no project-core (fatia `contratos.md`). O formato de erro é único: HTTP 400 com `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }`.

## 10. LANÇAMENTO SOMENTE COM APROVAÇÃO DO COMANDANTE
O deploy para produção nunca acontece automaticamente: é publicação externa, uma das 3 situações em que o comandante é chamado. O comandante dá o aval final.

## 11. SUB-AGENTES OBRIGATÓRIOS NÃO SÃO OPCIONAIS
- `build-validator` APÓS cada tarefa de código (Passo 3.5).
- `contract-tester` JUNTO com o build-validator, em cada tarefa de código (Passo 3.7; os dois em segundo plano, e o executor espera os dois): gera E roda os testes de contrato do que mudou.
- `code-architect` AO FINAL da Fase 4, antes de avançar.
- `verify-app` ANTES de deploy (Fase 6).
- Revisores de selo ao fim de cada fase, disparados JUNTOS e em segundo plano: `fresh-reviewer` + `cold-start-tester` (um por `-produto.md`) + `qa-ui-tandem` (quando há interface navegável).
- `tool-provisioner` na Fase 2.4.

Sem exceção. A lista completa e quem dispara cada um está em `sub-agentes.md`.

## 12. CRONOS COORDENA TODO PROJETO
O CRONOS é ativado ao final da Fase 2 em TODO projeto, independente da pontuação de complexidade. O ATLAS dispara SOMENTE o CRONOS. O CRONOS dispara todos os outros — executores, SHIELD, SCOUT, sub-agentes e o próprio ATLAS quando há bloqueio de contrato ou replanejamento. Executores nunca disparam outros agentes: avisam o CRONOS por `SendMessage`. O score define apenas QUANTOS agentes entram (se FRONT acumula PIXEL+FORM e BACK acumula ENGINE+VAULT), nunca SE o CRONOS entra.

## 13. FASE 2.5 É OBRIGATÓRIA EM TODO PROJETO
Antes de qualquer código, o CRONOS monta o mini-plano de cada agente executor (`.delta-11/planos/[AGENTE]-plan.md`, um por agente, sobrescrito a cada onda; o anterior vai para `planos/arquivo/`) — os agentes NÃO criam os próprios planos. O mini-plano tem 6 seções (objetivo da onda; recorte da fase anterior; tarefas; critérios de aceite; limites de escopo; convenções) e o checklist do ciclo interno de 7 sub-etapas. Execução só começa após os mini-planos prontos. Sem planejamento prévio = improviso durante execução = retrabalho.

## 14. FERRAMENTAS EXTERNAS SÃO REGISTRADAS ANTES DE SEREM INSTALADAS
Antes de instalar um SDK de serviço externo, adicionar uma chave de API ao `.env`, ou configurar um novo MCP — PARE. Atualize `.delta-11/memoria/ferramentas-do-projeto.md` PRIMEIRO (modelo em `.delta-11/templates/ferramentas-do-projeto-template.md`). Só depois faça a instalação. Vale para agentes Δ-11 E para qualquer IA externa trabalhando no projeto.

## 15. DOCUMENTAÇÃO DE INTEGRAÇÃO EXTERNA VIVE AO LADO DO CÓDIGO
Toda documentação de integração externa (configuração de API, chave, vendor, modelo de IA) vive em `src/lib/[dominio]/[etapa]/README.md` — AO LADO do código que a consome — usando o modelo `.delta-11/templates/config-integracao-externa-template.md`. As pastas têm nome em inglês, pela FUNÇÃO no produto (ex.: `src/lib/ai/competitive-analysis/README.md`), NUNCA pelo vendor ("kimi-moonshot"). NUNCA em `docs/` (que é para spec de produto) nem na raiz. O hook `pre-criacao-arquivo.py` bloqueia violações. Origem: caso real de 2026-07-03 (`docs/configuracao-kimi-moonshot.md` criado por IA externa).

## 16. ZONEAMENTO DOCUMENTAL DO PROJETO
Cada tipo de arquivo tem endereço canônico — o mapa completo está no CLAUDE.md, seção "PARA IA EXTERNA":
- Raiz do projeto: SÓ código/config de framework + `CLAUDE.md` + `README.md`. Nada mais.
- Documentos pessoais do comandante (planejamentos, reflexões, guias): `docs/comandante/`
- Conhecimento para agentes: `.delta-11/conhecimento/` (a pasta `skills/` na raiz é LEGADA — não criar nada lá)
- Arquivos temporários (previews, depuração, conflitos de merge): `.delta-11/scratch/` — NUNCA na pasta temporária do sistema (some sem aviso e mistura projetos). Expiram em 7 dias (limpeza automática).
- Screenshots de evidência: `.delta-11/evidencias/screenshots/AAAA-MM-DD/`
- Logs completos de sub-agentes: `.delta-11/logs/sub-agentes/` (Regra 17)
- Decisões arquiteturais (ADR) e entregáveis das Fases 3.5, 4.5 e 7: `.delta-11/memoria/decisoes/AAAA-MM-DD-titulo.md` (modelo `adr-registro-de-decisao-arquitetural-template.md`; entregáveis de fase no padrão `AAAA-MM-DD-<fase>-<NN>-<slug>.md`)
- Bug reports: `.delta-11/bugs/BUG-NNN-titulo.md` (modelo `bug-report-template.md`)
- PRD (documento de requisitos): `docs/prd.md` (modelo `prd-documento-de-requisitos-template.md`)
- Lições que valem para todos os projetos: `~/.delta-11/aprendizados-entre-projetos.md` (fora do projeto; quem escreve é o CRONOS)

Arquivos EXISTENTES fora do zoneamento NÃO são movidos automaticamente: mexer em arquivo do comandante é risco de perda de dados, então o agente registra o caso e o CRONOS avisa o comandante (regra global de organização).

## 17. RELATÓRIOS DE SUB-AGENTES SÃO PERSISTIDOS
Todo relatório de sub-agente (build-validator, contract-tester, code-architect, verify-app, schema-validator, impact-mapper (que só roda a pedido do CRONOS e nunca cria tarefas no kanban sem a aprovação dele), fresh-reviewer, cold-start-tester, tool-provisioner, qa-ui-tandem) é salvo em `.delta-11/logs/sub-agentes/[AAAA-MM-DD]-[sub-agente]-[AGENTE-que-disparou]-[T-XXX].md` ANTES de ser resumido. O `[AGENTE]-produto.md` continua com a linha-resumo + o caminho do log completo. Além disso, o hook do evento `SubagentStop` grava sozinho `logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log` (com o identificador do sub-agente e a última mensagem) — é a prova de que o sub-agente rodou. Sem o relatório persistido, auditoria pós-morte é impossível — a linha-resumo não diz POR QUE passou.
