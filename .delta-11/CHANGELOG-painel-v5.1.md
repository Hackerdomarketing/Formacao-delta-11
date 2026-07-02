# Painel de Comando v5.1 — Registro de Mudanças

**Data:** 2026-07-02
**Versão do sistema:** v5 → v5.1 (v5 propagada + Painel de Comando v5.1)
**Autor:** Comandante Rafa + Claude Code

---

## Por que essa mudança existe

O painel anterior (v4.x) era uma **cópia visual literal** do `kanban.md` que os agentes usam pra se coordenar entre si. Isso fez o painel ficar cheio de linguagem técnica que só faz sentido pra outros agentes: IDs de tarefa (`T-IMPC-04`), hashes (`worktree agent-aa356b6e560d2eac5`), timestamps ISO 8601 (`2026-07-01T23:15Z`), caminhos de arquivo (`src/lib/ia/passada1/definicoes-blocos.ts`), status de build (`tsc PASS`).

O comandante humano — que não programa — abria o painel e via **uma parede de código**. Ficava agoniado, sem saber:
- Se podia fechar o computador
- Quanto faltava terminar
- Se algo estava travado
- Quem estava vivo e quem tinha parado

A v5.1 reformula o painel a partir de uma pergunta única: **o painel é pra você OU pra os agentes?**

Resposta: é pra você. Os agentes já têm o `kanban.md` cru.

## O que mudou

### 1. Layout — de 4 colunas kanban → 1 coluna vertical
- Antes: kanban Trello-style (A_FAZER / FAZENDO / REVISÃO / CONCLUÍDO) — modo TIME
- Agora: uma coluna narrativa — modo PASSAGEIRO num avião

### 2. Selo binário no topo (grande, colorido, na cara)
- 🟢 **SEGURO FECHAR** — tudo indo bem, você pode ir tomar café
- 🟡 **PRECISA DE VOCÊ** / **AGENTE SEM SINAL** / **TAREFA DEMORANDO** — atenção requerida
- 🔴 **N TRAVADO(S)** — emergência real, algo bloqueou

### 3. Progresso honesto
- Antes: "90%" solto sem contexto
- Agora: "Ciclo COMMODITY · Onda 1 · 90% · 104 tarefas prontas de 116 · 2 em execução · 1 em revisão · 9 pendentes"

### 4. Voz do CRONOS — card grande com mensagem em português
- Antes: campo `ultima_atualizacao` com jargão técnico (ex: "2026-07-01T23:15Z (ENGINE: T-IMPC-04 concluida na worktree agent-aa356b6e560d2eac5. 7 DefinicaoAnalise categoria 10 declaradas...")
- Agora: `mensagem_cronos.texto` em português leigo (ex: "O VAULT confirmou que o banco está pronto. O ENGINE já terminou e mandou pra revisão. Preparando a próxima onda com PIXEL e SHIELD. Nada quebrou. Você pode ir tomar café.")

### 5. Cada tarefa em execução com resumo humano
- Antes: `[IMPACTO-MUDANCA] Adicionar blocos de extração em src/lib/ia/passada1/definicoes-blocos.ts (paletas, headlines literais...)`
- Agora: "Fazendo uma mudança de impacto no sistema" (VAULT · Banco · há 4 horas)

### 6. Batimento cardíaco — quem tá vivo, quem parou
- Se um agente tem tarefa em "fazendo" mas não gravou heartbeat nos últimos 5 min → painel mostra "sem sinal ⚠"
- Cor amarela no card + selo geral vira "AGENTE SEM SINAL"
- Elimina o pior tipo de bug: painel dizendo "tudo ok" enquanto agente travou silenciosamente

### 7. Tempo relativo
- Antes: `2026-07-01T23:15Z`
- Agora: "há 4 horas"

### 8. Histórico colapsado
- Antes: os 104 cards concluídos renderizados em coluna gigante (17.804 pixels de altura)
- Agora: só últimas 5 tarefas visíveis + link "Ver histórico completo (99 outras tarefas) →" que abre sob demanda

### 9. IDs de tarefa rebaixados
- Antes: `T-IMPC-04` como TÍTULO do card
- Agora: metadado minúsculo cinza no canto direito

### 10. Estética preservada mas ressemantizada
- Fundo escuro cinematográfico + imagem bg-delta11.png sutil: MANTIDOS
- Vermelho: reservado APENAS para emergência real (não mais cor de tudo)
- Verde: para "seguro" e tarefas concluídas
- Amarelo: para "precisa de você"
- Azul: para nome do agente (neutro, informativo)

### 11. Tradução automática de fallback
- Se um agente não gravou `resumo_humano` (retrocompatibilidade com kanban antigo), o painel usa dicionário de padrões (regex) pra traduzir automaticamente:
  - `[IMPACTO-MUDANCA]` → "Fazendo uma mudança de impacto no sistema"
  - `migration|migração` → "Mexendo na estrutura do banco de dados"
  - `webhook` → "Configurando integração externa"
  - E outros 10+ padrões
- Se nada bate, mostra os primeiros 80 caracteres da descrição limpa (sem tags, backticks e IDs)

### 12. Auto-refresh silencioso
- Antes: botão "↻ ATUALIZAR" precisava ser clicado
- Agora: refresh automático a cada 5s (busca dados novos) + re-render a cada 30s (atualiza "há 2 min" → "há 3 min" mesmo sem mudança de dados)
- Botão manual removido — se você precisa clicar pra atualizar, o painel já mentia

## Contratos novos no kanban-data.js (v5.1)

3 campos novos que os agentes DEVEM gravar (regra centralizada no `CLAUDE.md` → seção "Passo 3.1 — Painel de Comando (v5.1)"):

### `resumo_humano` (por tarefa — TODOS os agentes)
Frase em português leigo, sem jargão técnico, max 15 palavras. Grava em cada tarefa dentro de `fazendo`, `revisao`, `concluido`.

### `mensagem_cronos` (no topo do kanban — SOMENTE CRONOS)
Voz do gerente de projeto. Formato:
```javascript
mensagem_cronos: {
  texto: "O VAULT confirmou que o banco está pronto. O ENGINE já terminou e mandou pra revisão. Preparando a próxima onda com PIXEL e SHIELD. Você pode ir tomar café.",
  timestamp: "2026-07-02T00:35:00Z",
  precisa_comandante: null  // ou "descrição do que precisa" — quando não-null, painel mostra convocação amarela
}
```

### `heartbeats` (array no nível principal — TODOS os agentes ativos)
Batimento cardíaco. Cada agente ativo grava:
```javascript
heartbeats: [
  { agente: "CRONOS", ultima_atividade: "2026-07-02T00:35:00Z", tarefa_atual: "T-CRONOS-COMMODITY" },
  { agente: "ENGINE", ultima_atividade: "2026-07-02T00:33:12Z", tarefa_atual: "T-IMPC-05" }
]
```

Agentes que estão descansando (concluíram tudo) NÃO gravam heartbeat — ausência do array é o sinal "dormindo".

## Como reverter (se der ruim)

O painel v4 antigo está preservado em `painel-v4.html.backup` na pasta oficial. Para reverter:

```bash
cd /Users/alfa/projetos/Formacao-delta-11/.delta-11
mv painel.html painel-v5.1.html.backup
mv painel-v4.html.backup painel.html
./sincronizar.sh  # (se quiser propagar reversão para todos os projetos)
```

Também existe backup completo da v4.0.5 em:
`/Users/alfa/Downloads/Formacao-delta-11-v4.0.5-backup-20260701-212024/`

## Compatibilidade

- **Kanban antigo (sem os 3 campos novos):** funciona. Painel usa fallback automático de tradução por regex.
- **Kanban parcialmente atualizado (só `resumo_humano`, sem `mensagem_cronos`):** funciona. Painel mostra "Sem atualização recente do CRONOS" no lugar da voz.
- **Kanban completo v5.1:** experiência plena — cronos fala com o comandante em português, tarefas têm frase humana, heartbeat detecta agente travado.

## Impacto operacional

- **Agentes ATIVOS agora (em ciclo COMMODITY do scanner-de-desvantagens-v3):** os agentes vivos na memória continuam com regras v4.0.5. Só percebem os campos novos quando forem reativados. **Não quebra nada.**
- **Novos ciclos** (a partir de agora, em qualquer projeto): agentes ativados leem os operativos v5 + regra 3.1 do CLAUDE.md → gravam os 3 campos novos → painel mostra experiência completa.
- **Comandante:** vê painel novo imediatamente ao abrir. Enquanto agentes ainda não gravaram os campos novos, tradução automática cobre o gap.

## Backups criados nesta sessão

- `~/Downloads/Formacao-delta-11-v4.0.5-backup-20260701-212024/` — snapshot completo da v4.0.5 antes da v5 chegar
- `~/projetos/Formacao-delta-11/.delta-11/painel-v4.html.backup` — versão anterior do painel

---

**Fim do CHANGELOG-painel-v5.1.md**
