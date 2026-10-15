# 🔍 SELO EXPERIENCIAL — Fase [N] (v6.4 — executado pelo sub-agente qa-ui-tandem)

> **Template v6.4 (2026-10-15).** O selo é EXECUTADO pelo sub-agente `qa-ui-tandem`
> (`.delta-11/sub-agentes/qa-ui-tandem.md`), que opera o produto num navegador real — o Tandem Browser, pela API
> HTTP em `http://localhost:8765` — e devolve PASS / FAIL / BLOQUEADO com screenshots. Se o Tandem não estiver
> rodando, o sub-agente usa o Playwright e avisa no relatório.
>
> **Onde este arquivo vive depois de preenchido:** o CRONOS copia este modelo para
> `.delta-11/planos/selo-experiencial-fase-[N].md` e preenche a seção "Fluxos críticos".
>
> **Modo do selo** (`.delta-11/.modo-selo`): `automatico` é o PADRÃO (D1). O comandante troca com os comandos
> `modo manual` / `modo automatico` — ninguém precisa editar arquivo à mão.

---

## Quem executa este selo

**Sub-agente `qa-ui-tandem`** — disparado pelo CRONOS via `Agent tool`, sem worktree, depois que todas as
tarefas da fase têm `[SHIELD] APROVADO`. Ele sai JUNTO com os outros revisores de fase (v6.4), na mesma mensagem e
em segundo plano; o CRONOS espera todos e consolida:

```
SHIELD APROVADO em todas → [ Fresh Reviewer + Cold Start Tester (um por -produto.md) + qa-ui-tandem ] → selo
                             (todos juntos, run_in_background: true)
```

```
Agent(
  description: "qa-ui-tandem — Selo Fase [N]",
  subagent_type: "general-purpose",
  model: "sonnet",
  run_in_background: true,
  prompt: "[conteúdo de .delta-11/sub-agentes/qa-ui-tandem.md]
Projeto em: [caminho absoluto da pasta principal]. Fase: [N].
Roteiro: .delta-11/planos/selo-experiencial-fase-[N].md. URL base: [http://localhost:3000].
Execute agora. NÃO pergunte ao humano — devolva PASS, FAIL ou BLOQUEADO."
)
```

---

## Fluxos críticos (o CRONOS preenche a partir do project-core e do PRD)

Escreva cada fluxo do jeito que um usuário faria, com o resultado que ele deveria ver. Máximo de 7 fluxos por
fase; priorize o que a fase acabou de entregar.

- **[Fluxo 1 — nome curto]:** [URL inicial] → [ação 1] → [ação 2] → **resultado esperado:** [o que aparece na tela]
- **[Fluxo 2]:** ...
- **[Fluxo N]:** ...

**Conta de teste (se algum fluxo exigir login):** as variáveis `TEST_USER_EMAIL` e `TEST_USER_PASSWORD` no
`.env.local` (só os NOMES aparecem aqui — nunca os valores).

**O que NÃO testar neste selo:** [fluxos com pagamento real, envio real de e-mail/SMS, publicação externa — o
sub-agente marca BLOQUEADO se encontrar].

---

## Como o sub-agente testa cada fluxo (resumo — detalhes no sub-agente)

1. **Abre uma aba própria** em segundo plano: `POST /tabs/open` com `{"url": "...", "focus": false, "source": "wingman"}`
2. **Lê a tela** pela árvore de acessibilidade: `GET /snapshot?interactive=true&compact=true` com `X-Tab-Id`
3. **Age** com eventos reais de teclado e mouse: `POST /snapshot/click` (`{"ref":"@eN"}`) e `POST /snapshot/fill`
4. **Confere** o resultado esperado num snapshot novo (e os erros do console)
5. **Guarda a evidência:** `GET /screenshot` com `X-Tab-Id`, gravado em
   `.delta-11/evidencias/screenshots/AAAA-MM-DD/HHMM-selo-fase-[N]-fluxo-[K]-passo-[P]-QA-UI-TANDEM.png`

Relatório completo: `.delta-11/logs/sub-agentes/AAAA-MM-DD-qa-ui-tandem-CRONOS-fase-[N].md`.

---

## O que o CRONOS faz com o veredito

### PASS
- Modo `automatico`: a fase é selada e a próxima abre sozinha. O painel mostra "Selo verde ✓".
- Modo `manual`: o CRONOS mostra ao comandante o relatório (com os screenshots) e um roteiro curto para ele
  conferir com os próprios olhos, se quiser; o comandante digita `aprovar`.

### FAIL
1. Fix trivial (um campo, um texto, uma rota): o CRONOS dispara o executor responsável com o diagnóstico
   (1 tentativa) e roda o qa-ui-tandem de novo.
2. Fix não trivial: o CRONOS cria no kanban a tarefa `[SELO-FAIL] [fluxo] — [problema]` para o executor
   responsável e bloqueia o avanço da fase.
3. O painel mostra: "Selo vermelho: [problema]. Tarefa criada no kanban." — é um aviso, não uma pergunta.
4. O CRONOS continua trabalhando no que não depende da fase bloqueada.

Quem corrige é sempre o agente executor, despachado pelo CRONOS — nunca o comandante.

### BLOQUEADO
O sub-agente precisou de algo que só um humano tem (conta, CAPTCHA, código de acesso, ação externa real). O
CRONOS só fala com o comandante se for uma das 3 situações permitidas (D4) — credencial/conta, risco de dano
ou decisão de negócio — e pede a MENOR ação possível (ex.: "crie uma conta de teste e coloque
`TEST_USER_EMAIL`/`TEST_USER_PASSWORD` no `.env.local`").

---

## O que mudou em relação ao template v5.2

- ❌ Removido: roteiro de "Passo 1 — abra a URL tal" para o humano executar
- ✅ Adicionado: sub-agente `qa-ui-tandem` que opera o produto pelo Tandem Browser e grava evidências
- ❌ Removido: modo manual como padrão
- ✅ Adicionado: modo `automatico` como padrão; `modo manual` só por escolha do comandante
- ✅ v6.3: endpoints reais da API HTTP do Tandem, alternativa com Playwright, veredito BLOQUEADO, caminho do
  roteiro preenchido e das evidências
- ✅ v6.4: o qa-ui-tandem sai JUNTO com o fresh-reviewer e os cold-start-tester, em segundo plano
  (`run_in_background: true`) — não espera mais os outros revisores terminarem
