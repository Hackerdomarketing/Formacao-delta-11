# KANBAN — FORMAÇÃO Δ-11

> **Quem escreve:** SOMENTE o CRONOS (D10, v6.3). Ele atualiza este arquivo e o `kanban-data.js` juntos.
> **Quem lê:** todos os agentes leem a própria coluna para saber o que fazer.
> **Executores não editam este arquivo:** ao começar, terminar ou travar uma tarefa, avisam o CRONOS por
> SendMessage e registram no próprio `memoria/[NOME]-produto.md`. Assim uma edição nunca apaga a outra.
> **Horários:** sempre data e hora completas (ISO), ex.: `2026-10-14T13:05:00-03:00`.
> O comandante acompanha o progresso pelo `painel.html` (abre sozinho no navegador quando o Delta-11 começa).

**Projeto:** [nome do projeto — o CRONOS copia do plano do ATLAS]
**Complexidade:** [BAIXA 5–8 / MÉDIA 9–12 / ALTA 13–15 pontos]
**Fase atual:** [fase e onda, ex.: Fase 3 · onda 2 de 4]
**Última atualização:** [data e hora ISO] — CRONOS

---

## 📋 BACKLOG (tarefas não atribuídas)

<!-- Tarefas identificadas mas ainda não distribuídas -->

---

## 🏗️ ATLAS — A FAZER

<!-- Tarefas de planejamento e arquitetura -->

---

## 📊 CRONOS — A FAZER

<!-- Tarefas de gestão e coordenação -->

---

## 🖥️ FRONT — A FAZER

<!-- Tarefas de liderança e revisão de interface -->

---

## 🎨 PIXEL — A FAZER

<!-- Tarefas de componentes visuais e páginas -->

---

## 📝 FORM — A FAZER

<!-- Tarefas de formulários e validações -->

---

## ⚙️ BACK — A FAZER

<!-- Tarefas de liderança e revisão de servidor -->

---

## 🔧 ENGINE — A FAZER

<!-- Tarefas de rotas e lógica de negócio -->

---

## 🔐 VAULT — A FAZER

<!-- Tarefas de banco de dados e autenticação -->

---

## 🛡️ SHIELD — A FAZER

<!-- Tarefas de testes, segurança e infraestrutura -->

---

## 🔍 SCOUT — A FAZER

<!-- Erros para diagnosticar e corrigir -->

---

## ⚡ FAZENDO

<!-- Formato: **[ID]** — [Descrição] | Agente: [NOME] | Início: [AAAA-MM-DDTHH:MM:SS-03:00] -->

---

## 👁️ REVISÃO

<!-- Formato: **[ID]** — [Descrição] | Por: [agente] | Revisor: [SHIELD ou líder] -->

---

## ✅ CONCLUÍDO

<!-- Formato: **[ID]** — [Descrição] | Por: [agente] | Aprovado: [SHIELD] | Data: [AAAA-MM-DDTHH:MM:SS-03:00] -->

---

## 🚫 BLOQUEADO

<!-- Formato: **[ID]** — [Descrição] | Agente: [nome] | Motivo: [detalhe] | Precisa de: [ATLAS/comandante] -->

---

## ☑️ CHECKLIST POR SQUAD (onda atual)

<!-- O CRONOS marca [x] quando o item da onda estiver cumprido. Zera a lista ao abrir uma onda nova.
     Item que não se aplica à onda: escreva "(não se aplica)" no fim da linha, não apague. -->

### Squad Interface — FRONT · PIXEL · FORM
- [ ] Telas e componentes da onda prontos (PIXEL)
- [ ] Formulários com validação e mensagens de erro em português (FORM)
- [ ] Interface ligada aos contratos de API da fatia `contratos.md` (FRONT)
- [ ] Revisão do líder FRONT feita
- [ ] Autocrítica, build-validator e contract-tester rodados por cada um
- [ ] SHIELD aprovou cada tarefa (linha APROVADO no activity-log)

### Squad Servidor — BACK · ENGINE · VAULT
- [ ] Banco, migrations e regras de acesso da onda prontos (VAULT)
- [ ] Rotas e lógica de negócio prontas, erros no formato único (400 `VALIDATION_ERROR`) (ENGINE)
- [ ] Contratos implementados iguais à fatia `contratos.md` (BACK)
- [ ] Revisão do líder BACK feita
- [ ] Autocrítica, build-validator e contract-tester rodados por cada um
- [ ] SHIELD aprovou cada tarefa (linha APROVADO no activity-log)

### Squad Qualidade — SHIELD · SCOUT
- [ ] Toda tarefa entregue na onda revisada pelo SHIELD (aprovada ou reprovada com motivo)
- [ ] Testes e verificação de segurança da onda rodados (SHIELD)
- [ ] Erros abertos diagnosticados ou encaminhados (SCOUT; após 3 falhas, avisa o CRONOS)
- [ ] Nenhuma tarefa da onda em BLOQUEADO sem dono
