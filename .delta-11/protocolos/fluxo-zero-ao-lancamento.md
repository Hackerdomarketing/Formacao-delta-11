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

**Quem:** ATLAS + SHIELD (revisão) + CRONOS (se Score ≥ 7)
**Janelas:** 1 a 2

O ATLAS define tudo: contratos de interface de programação de aplicações com regras de validação detalhadas, esquema de banco, decisões técnicas críticas, padrões de implementação obrigatórios, armadilhas conhecidas das tecnologias escolhidas, fluxos completos de ponta a ponta, regras de autenticação e autorização, e popula o kanban com todas as tarefas.

**Antes de finalizar:** O ATLAS ativa o SHIELD para uma revisão de segurança dos contratos. O SHIELD verifica se as validações estão completas, se os fluxos estão mapeados, se as decisões técnicas cobrem as armadilhas, e se existe defesa em profundidade. O ATLAS corrige o que o SHIELD apontar.

**Ativação do CRONOS:** Se a pontuação de complexidade for ≥ 7 (projetos médios ou altos), o ATLAS ativa o CRONOS ao final desta fase. O CRONOS passa a monitorar o kanban, coordenar agentes, e ser o ponto de contato do comandante durante as próximas fases.

**Resultado:** `project-core.md` completo com contratos detalhados, decisões técnicas, padrões de implementação, e armadilhas documentadas. `kanban.md` populado. Contratos revisados pelo SHIELD. CRONOS ativado (se aplicável). Comandante sabe quantas janelas abrir.

---

### FASE 2.5 — PLANEJAMENTO DETALHADO (OBRIGATÓRIA EM PROJETOS SCORE ≥ 7)

**Quem:** Todos os agentes da próxima fase + CRONOS (coordenador)
**Janelas:** 2 a 8 (depende de quantos agentes vão trabalhar na Fase 3 e 4)

**Quando executar:** Somente em projetos com Score ≥ 7 (complexidade média ou alta). Em projetos baixa complexidade (Score < 7), pular esta fase e ir direto para Fase 3.

Esta fase existe para evitar que agentes "pensem enquanto fazem". Antes de escrever qualquer código, cada agente PLANEJA o que vai fazer, e o CRONOS revisa todos os planos para detectar conflitos ANTES da execução começar.

**Processo:**

1. **CRONOS dispara todos os agentes da Fase 3 e 4** em paralelo (respeitando zonas e dependências)
2. **Cada agente cria seu arquivo de plano:** `.delta-11/planos/[AGENTE]-plan.md` contendo:
   - Quais arquivos vai criar/modificar
   - Quais dependências precisa (de outros agentes ou bibliotecas)
   - Decisões técnicas específicas (padrões, estruturas, validações)
   - Checklist de tarefas detalhado
   - Estimativa de complexidade de cada tarefa
3. **CRONOS lê todos os planos** e identifica:
   - Conflitos (dois agentes planejando mexer no mesmo arquivo)
   - Dependências circulares (A depende de B que depende de A)
   - Decisões técnicas inconsistentes (FRONT quer usar lib X, PIXEL quer usar lib Y)
   - Tarefas faltando (algo que ninguém planejou mas precisa ser feito)
4. **CRONOS pode disparar Code Architect** para validar se os planos propostos seguem a arquitetura do `project-core.md`
5. **Se conflitos encontrados:** CRONOS devolve os planos aos agentes com instruções de replanejamento. Loop até todos os planos estarem consistentes.
6. **Quando todos os planos aprovados:** CRONOS marca no kanban que a Fase 2.5 foi concluída, e os agentes podem avançar para execução (Fase 3 e 4) **seguindo exatamente os planos aprovados**.

**Resultado:** Todos os agentes sabem EXATAMENTE o que vão fazer antes de escrever código. Zero improviso durante execução. Conflitos resolvidos ANTES de acontecerem.

---

### FASE 3 — FUNDAÇÃO

**Quem:** VAULT (obrigatório) + SHIELD (se média ou alta complexidade)
**Janelas:** 1 a 2

O VAULT cria o banco de dados, autenticação, e políticas de segurança. O SHIELD prepara infraestrutura e estratégia de testes.

**Resultado:** Banco pronto, autenticação funcionando, infraestrutura configurada. NENHUM agente de funcionalidade começa antes disso estar concluído.

---

### FASE 4 — DESENVOLVIMENTO

**Quem:** Depende da complexidade (o ATLAS já definiu quem) + CRONOS (se Score ≥ 7)
**Janelas:** 2 a 7

**Se Fase 2.5 foi executada:** Cada agente já tem seu plano aprovado em `.delta-11/planos/[AGENTE]-plan.md` e **DEVE seguir exatamente o plano**. Qualquer desvio precisa ser aprovado pelo CRONOS (que pode disparar Code Architect para avaliar impacto).

**Se Fase 2.5 foi pulada (Score < 7):** Cada agente lê o kanban, vê suas tarefas, e começa a trabalhar diretamente.

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

**Monitoramento de drift arquitetural (CRONOS em projetos Score ≥ 7):**
Se CRONOS percebe que um agente está demorando muito ou fazendo muitos commits, pode disparar Code Architect para verificar se o agente está seguindo o plano ou improvisando. Se detectar drift significativo, CRONOS pode parar o agente e forçar replanejamento.

**Ao final da Fase 4 (quando todos os agentes de desenvolvimento terminam):**
1. **Code Simplifier (OBRIGATÓRIO):** O último agente a terminar dispara o sub-agente `code-simplifier` para simplificar todo o código escrito na fase. Após simplificação, dispara `build-validator` para confirmar que nada quebrou.
2. **Varredura preventiva (OBRIGATÓRIO):** SCOUT é ativado automaticamente para varredura completa de todo o código antes da Fase 5. Busca: inicializações perigosas, bypass de contratos, validações ausentes, links quebrados, condições de corrida, falhas de segurança.
3. **Auditoria arquitetural (OBRIGATÓRIO):** ATLAS ou CRONOS (se ativo) dispara o sub-agente `code-architect` para comparar código real vs arquitetura planejada no `project-core.md`. Se score for C ou menor, tarefas de correção são criadas no kanban antes de avançar.

**Resultado:** Todas as funcionalidades implementadas, código simplificado, testadas individualmente pelo SHIELD, varridas pelo SCOUT, e auditadas arquiteturalmente. Problemas encontrados são corrigidos antes de avançar.

---

### FASE 5 — TESTES DE INTEGRAÇÃO

**Quem:** SHIELD + SCOUT (se houver erros) + CRONOS (se Score ≥ 7)
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
