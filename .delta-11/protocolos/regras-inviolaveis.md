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
Build Validator APÓS cada tarefa de código (Passo 3.5). Code Simplifier APÓS Build Validator passar e ANTES do SHIELD, em cada tarefa (Passo 3.6). Code Architect AO FINAL da Fase 4, antes de iniciar a Fase 5. Verify App ANTES de deploy. Sem exceção.

## 12. CRONOS COORDENA EM PROJETOS COMPLEXOS (SCORE ≥ 7)
Em projetos com pontuação de complexidade ≥ 7, o CRONOS é ativado na Fase 2 e coordena toda execução. Agentes reportam a ele, não trabalham isolados.

## 13. PHASE 2.5 É OBRIGATÓRIA EM PROJETOS SCORE ≥ 7
Antes de escrever código em projetos complexos, cada agente cria arquivo de plano detalhado. CRONOS revisa e aprova todos os planos. Execução só começa após todos os planos aprovados. Sem planejamento prévio = improviso durante execução = retrabalho.
