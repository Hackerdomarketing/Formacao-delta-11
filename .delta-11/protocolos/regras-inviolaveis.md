# REGRAS INVIOLÁVEIS — FORMAÇÃO Δ-11

Estas 10 regras não podem ser quebradas por nenhum agente sob nenhuma circunstância.

## 1. NUNCA CODIFICAR ANTES DE PLANEJAR
Nenhum agente escreve código antes do ATLAS ter completado a classificação, definido a arquitetura, e o comandante ter aprovado o plano.

## 2. BANCO DE DADOS E INFRAESTRUTURA ANTES DE TUDO
O VAULT completa a fundação (banco, autenticação, políticas de segurança) antes de qualquer agente de funcionalidade começar. Sem exceção.

## 3. CONTRATO DE INTERFACE DE PROGRAMAÇÃO DE APLICAÇÕES É LEI
O que está no `project-core.md` é a verdade absoluta. Interface e servidor seguem EXATAMENTE o contrato. Mudanças passam obrigatoriamente pelo ATLAS.

## 4. REGRA DAS TRÊS TENTATIVAS
Se o SCOUT não corrigiu um erro em 3 tentativas, para obrigatoriamente. O comandante reinicia a janela com contexto limpo.

## 5. TESTES NÃO SÃO OPCIONAIS
Nenhuma funcionalidade está concluída sem aprovação do SHIELD. Sem testes, sem conclusão.

## 6. CADA AGENTE ATUALIZA SUA MEMÓRIA E O KANBAN
Ao terminar qualquer tarefa, o agente OBRIGATORIAMENTE atualiza seu arquivo de estado e o kanban. Sem exceção.

## 7. NENHUM AGENTE ALTERA ESTRUTURA SEM ATLAS
Mudanças em banco, autenticação, contratos, ou módulos fundamentais requerem aprovação do ATLAS.

## 8. SEMPRE LEIA SEU ARQUIVO DE ESTADO ANTES DE TRABALHAR
Antes de iniciar qualquer tarefa, leia seu arquivo de estado para não repetir trabalho feito ou desfazer algo já completado.

## 9. COMUNICAÇÃO ENTRE INTERFACE E SERVIDOR SEMPRE VIA CONTRATO
Nenhum agente de interface combina informalmente com agente de servidor sobre formato de dados. Tudo passa pelo contrato formal no `project-core.md`.

## 10. LANÇAMENTO SOMENTE COM APROVAÇÃO DO COMANDANTE
O deploy para produção nunca acontece automaticamente. O comandante dá o aval final.

## 11. SUB-AGENTES OBRIGATÓRIOS NÃO SÃO OPCIONAIS
Build Validator APÓS cada tarefa de código (Passo 3.5). Code Architect AO FINAL da Fase 4, antes de iniciar a Fase 5. Verify App ANTES de deploy. Sem exceção.

## 12. CRONOS COORDENA EM PROJETOS COMPLEXOS (SCORE ≥ 7)
Em projetos com pontuação de complexidade ≥ 7, o CRONOS é ativado na Fase 2 e coordena toda execução. Agentes reportam a ele, não trabalham isolados.

## 13. PHASE 2.5 É OBRIGATÓRIA EM PROJETOS SCORE ≥ 7
Antes de escrever código em projetos complexos, cada agente cria arquivo de plano detalhado. CRONOS revisa e aprova todos os planos. Execução só começa após todos os planos aprovados. Sem planejamento prévio = improviso durante execução = retrabalho.

## 14. FERRAMENTAS EXTERNAS SÃO REGISTRADAS ANTES DE SEREM INSTALADAS (v5.2 — formaliza regra que existia só no template)
Antes de instalar um SDK de serviço externo, adicionar uma chave de API ao `.env`, ou configurar um novo MCP — PARE. Atualize `.delta-11/memoria/ferramentas-do-projeto.md` PRIMEIRO (template em `.delta-11/templates/ferramentas-do-projeto-template.md`). Só depois faça a instalação. Vale para agentes Δ-11 E para qualquer IA externa trabalhando no projeto.

## 15. DOCUMENTAÇÃO DE INTEGRAÇÃO EXTERNA VIVE AO LADO DO CÓDIGO (v5.2)
Toda documentação de integração externa (configuração de API, chave, vendor, modelo de IA) vive em `src/lib/[dominio]/[etapa]/README.md` — AO LADO do código que a consome — usando o template `.delta-11/templates/config-integracao-externa-template.md`. O nome é pela FUNÇÃO no produto ("ia-da-analise-competitiva"), NUNCA pelo vendor ("kimi-moonshot"). NUNCA em `docs/` (que é para spec de produto) nem na raiz. O hook `pre-criacao-arquivo.py` bloqueia violações. Origem: caso real de 2026-07-03 (`docs/configuracao-kimi-moonshot.md` criado por IA externa).

## 16. ZONEAMENTO DOCUMENTAL DO PROJETO (v5.2)
Cada tipo de arquivo tem endereço canônico — o mapa completo está no CLAUDE.md, seção "PARA IA EXTERNA":
- Raiz do projeto: SÓ código/config de framework + `CLAUDE.md` + `README.md`. Nada mais.
- Documentos pessoais do comandante (planejamentos, reflexões, guias): `docs/comandante/`
- Conhecimento para agentes: `.delta-11/conhecimento/` (a pasta `skills/` na raiz é LEGADA — não criar nada lá)
- Arquivos temporários (previews, debug): `.delta-11/scratch/` — NUNCA no `/tmp` do sistema (some sem aviso). Expiram em 7 dias (GC automático).
- Screenshots de evidência: `.delta-11/evidencias/screenshots/AAAA-MM-DD/`
- Logs completos de sub-agentes: `.delta-11/logs/sub-agentes/` (Regra 17)
Arquivos EXISTENTES fora do zoneamento NÃO são movidos automaticamente — mencionar ao comandante e perguntar (regra global de organização).

## 17. RELATÓRIOS DE SUB-AGENTES SÃO PERSISTIDOS (v5.2)
Todo relatório de sub-agente (build-validator, contract-tester, code-architect, fresh-reviewer, cold-start-tester, schema-validator, verify-app, tool-provisioner) é salvo em `.delta-11/logs/sub-agentes/[AAAA-MM-DD]-[sub-agente]-[AGENTE-que-disparou]-[T-XXX].md` ANTES de ser resumido. O `[AGENTE]-produto.md` continua com a linha-resumo (formato v5) + o path do log completo. Sem o log persistido, auditoria pós-morte é impossível — a linha-resumo não diz POR QUE passou.
