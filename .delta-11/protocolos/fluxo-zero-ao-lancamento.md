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

**Quem:** ATLAS + SHIELD (revisão)
**Janelas:** 1 (ATLAS trabalha, depois ativa SHIELD para revisar)

O ATLAS define tudo: contratos de interface de programação de aplicações com regras de validação detalhadas, esquema de banco, decisões técnicas críticas, padrões de implementação obrigatórios, armadilhas conhecidas das tecnologias escolhidas, fluxos completos de ponta a ponta, regras de autenticação e autorização, e popula o kanban com todas as tarefas.

**Antes de finalizar:** O ATLAS ativa o SHIELD para uma revisão de segurança dos contratos. O SHIELD verifica se as validações estão completas, se os fluxos estão mapeados, se as decisões técnicas cobrem as armadilhas, e se existe defesa em profundidade. O ATLAS corrige o que o SHIELD apontar.

**Resultado:** `project-core.md` completo com contratos detalhados, decisões técnicas, padrões de implementação, e armadilhas documentadas. `kanban.md` populado. Contratos revisados pelo SHIELD. Comandante sabe quantas janelas abrir.

---

### FASE 3 — FUNDAÇÃO

**Quem:** VAULT (obrigatório) + SHIELD (se média ou alta complexidade)
**Janelas:** 1 a 2

O VAULT cria o banco de dados, autenticação, e políticas de segurança. O SHIELD prepara infraestrutura e estratégia de testes.

**Resultado:** Banco pronto, autenticação funcionando, infraestrutura configurada. NENHUM agente de funcionalidade começa antes disso estar concluído.

---

### FASE 4 — DESENVOLVIMENTO

**Quem:** Depende da complexidade (o ATLAS já definiu quem)
**Janelas:** 2 a 7

Cada agente lê o kanban, vê suas tarefas, e começa a trabalhar. Ao concluir cada tarefa, atualiza seu estado e o kanban. O SHIELD testa CONTINUAMENTE conforme as funcionalidades são entregues (não espera o final).

**Ciclo de cada tarefa:**
```
Agente puxa tarefa do kanban → Executa → Atualiza estado e kanban → SHIELD verifica contra contrato → Aprovado? → Próxima tarefa
```

**Ao final da Fase 4 (quando todos os agentes de desenvolvimento terminam):**
O SCOUT é ativado automaticamente para uma varredura preventiva completa de todo o código antes da Fase 5. Ele busca problemas que o SHIELD pode não ter pego nas verificações individuais: inicializações perigosas, bypass de contratos, validações ausentes, links quebrados, condições de corrida, e falhas de segurança.

**Resultado:** Todas as funcionalidades implementadas, testadas individualmente pelo SHIELD, e varridas pelo SCOUT. Problemas encontrados pelo SCOUT são corrigidos antes de avançar.

---

### FASE 5 — TESTES DE INTEGRAÇÃO

**Quem:** SHIELD + SCOUT (se houver erros)
**Janelas:** 1 a 2

O SHIELD executa testes de ponta a ponta: cada fluxo completo (usuário se cadastra → faz login → executa ação → vê resultado). Verifica coerência total entre interface, servidor, e banco.

**Resultado:** Todos os fluxos passando nos testes. Todos os erros encontrados corrigidos.

---

### FASE 6 — PREPARAÇÃO PARA LANÇAMENTO

**Quem:** SHIELD + Comandante
**Janelas:** 1

O SHIELD configura o ambiente de produção, executa auditoria de segurança, e apresenta relatório final ao comandante. O comandante aprova o deploy.

**Resultado:** Sistema em produção.
