# Mini-plano — [AGENTE] | Fase [N] | Onda [N]
Tipo de tarefa: funcionalidade | correção-de-bug | performance | segurança | refatoração
(o SHIELD usa o tipo para exigir a evidência mínima correspondente)

> **Template v6.3 (2026-10-14) — Mini-plano de agente executor (Mecanismo M1, D17).**
> - **Arquivo:** `.delta-11/planos/[AGENTE]-plan.md` — UM por agente, sobrescrito a cada onda.
> - **Histórico:** antes de sobrescrever, o CRONOS move a versão anterior para
>   `.delta-11/planos/arquivo/[AGENTE]-plan-fase-[N]-onda-[N].md`. Nenhum outro nome de plano existe.
> - **Quem escreve:** só o CRONOS (Fase 2.5 ou replanejamento). O agente executor lê e segue; não edita.
> - **LIMITE:** o brief de despacho derivado deste plano não passa de 2.000 tokens (`brief_max_tokens` em
>   `.delta-11/.config-limites.json`; o hook `pre-despacho.py` bloqueia).
> - **Ciclo interno:** a seção final "Checklist do ciclo interno" é obrigatória (protocolo
>   `protocolos/ciclo-interno-7d.md`, guia por sub-etapa em `templates/ciclo-interno-template.md`).
> - **Rastreabilidade:** toda afirmação técnica carrega `[Fonte: arquivo#seção]`. Informação que não está em
>   documento nenhum → "sem orientação na documentação — decisão em aberto". PROIBIDO inventar. O executor
>   DEVOLVE (por SendMessage ao CRONOS) mini-plano com afirmação técnica sem fonte.

## 1. Objetivo da onda

[2-4 frases: o que DEVE existir ao final desta onda — o QUE, não o COMO — e por que esta onda existe.
Se este plano substitui um anterior: qual, por quê, e o caminho da versão arquivada em `planos/arquivo/`.]

## 2. Recorte da fase anterior

**Produto que você recebe:** `[Fonte: memoria/[AGENTE-ANTERIOR]-produto.md#o-que-existe-agora]` — [1-3 frases do que
está pronto para você construir em cima].

**Fatias do project-core que você lê (D6 — executores NÃO leem o `project-core.md` inteiro):**
- [ ] `memoria/project-core/contratos.md` — [rotas que você implementa ou consome]
- [ ] `memoria/project-core/banco.md` — [tabelas que você usa]
- [ ] `memoria/project-core/visual.md` — [telas/componentes]
- [ ] `memoria/project-core/decisoes-tecnicas.md` — [decisões que te limitam]
(marque só as que o papel exige; mais `pesquisa-tecnica.md`, sua coluna do kanban e sua base de conhecimento)

**Recorte técnico (só o que te afeta, cada item com fonte):**
- [contrato que consome] `[Fonte: project-core/contratos.md#post-api-orders]`
- [tabela que usa] `[Fonte: project-core/banco.md#orders]`

**Gotchas da sua zona** (copiados de `memoria/gotchas.md`):
- EVITE: [padrão] — [motivo] — [alternativa]

## 3. Tarefas

| ID | O que fazer | Arquivos (paths exatos quando conhecidos) | Depende de | Desbloqueia |
|---|---|---|---|---|
| T-[NNN] | [ação] | `src/...` | [T-NNN de AGENTE + como verificar que está pronta] | [T-NNN de AGENTE] |

**Paralelismo:** [quem roda junto com você nesta onda — ou "sozinho nesta onda"].
**Avise por SendMessage ao CRONOS se descobrir:** [ex.: divergência de schema, contrato ambíguo, mudança de escopo].

## 4. Critérios de aceite

[Verificáveis por máquina ou por evidência. Máximo 6 — se precisar de mais, a onda é grande demais: o CRONOS
quebra em mais ondas.]

- [ ] [critério 1 — mensurável] — verificável por: [comando, teste ou evidência]
- [ ] `tsc --noEmit` 0 erros · build PASS · `npm run test:contracts` sem regressão (adaptar ao stack)
- [ ] contract-tester (Passo 3.7) PASS para as rotas tocadas

## 5. Limites de escopo (OBRIGATÓRIO — Mecanismo M3)

**O que está EXPLICITAMENTE FORA do escopo desta onda:**

- [item 1 — o que este agente NÃO deve fazer, mesmo que pareça útil]
- [item 2 — decisão que não é deste agente]
- [item 3 — preocupação de fase futura que não deve ser antecipada]

**Regra para o agente:** se algo não está nos critérios de aceite MAS parece útil → verifique se viola os
limites. Se violar, PARE e envie SendMessage ao CRONOS.
**Regra para o SHIELD:** output que viola limites = REPROVAÇÃO IMEDIATA, independente de qualidade técnica.

## 6. Convenções (fixo — o CRONOS copia esta seção em todo mini-plano de código)

- **Limites estruturais:** função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 ·
  componente React ≤ 150 linhas e ≤ 5 props · rota ≤ 150 linhas (`regras-codigo.md` seção 8 — o
  build-validator bloqueia).
- **Idioma (D20):** nomes de variáveis/funções/tabelas/rotas/campos JSON em INGLÊS, sem abreviação
  (`/api/users`, `createdAt`, `calculateCartTotal`); comentários, textos de UI, mensagens ao usuário e
  descrições de teste em PORTUGUÊS (`regras-codigo.md` seção 9).
- **Erro de API (D13):** validação falhou ou campo faltando = HTTP **400** com
  `{ "error": { "code": "VALIDATION_ERROR", "message": "texto para humano", "details": [...] } }`.
- **Tempos-limite (D19):** banco 5 s · API externa 10 s · chamada interna 3 s · 3 novas tentativas com espera
  crescente · circuit breaker abre após 5 falhas e fecha após 60 s.
- **Temporários (D21):** `.delta-11/scratch/` — nunca `/tmp`.
- **Memória (D7, D8, D10):** você NÃO escreve no project-core (proposta vai na seção
  `PROPOSTAS PARA O PROJECT-CORE` do seu `-produto.md`), NÃO escreve no kanban (avise o CRONOS) e NÃO cria
  `[AGENTE]-estado.md` (legado).

## Checklist do ciclo interno (7 sub-etapas — protocolo `ciclo-interno-7d.md`)

| # | Sub-etapa | Onde está neste plano / quem cumpre | OK |
|---|---|---|---|
| 1 | Planejamento sobre a fase anterior selada | Seção 2 cita o `-produto.md` anterior | [ ] |
| 2 | Delegação com contexto isolado | Seção 2 (fatias permitidas) + Seção 5 (limites) | [ ] |
| 3 | Execução paralela | Seção 3 (paralelismo) — o CRONOS despacha com `isolation: "worktree"` | [ ] |
| 4 | Comunicação entre executores | Seção 3 ("avise o CRONOS se descobrir") — SendMessage | [ ] |
| 5 | Revisão cruzada externa | SHIELD revisa (Passo 3.8, pedido pelo CRONOS) | [ ] |
| 6 | Teste adversarial | build-validator (3.5) + contract-tester gera E roda (3.7) | [ ] |
| 7 | Selagem por critérios objetivos | Seção 4 — cada critério com evidência | [ ] |

## Finalização (ordem única — D9)

**Início:** Passo 0 ACK (`ativacoes/ack-[AGENTE].txt`) → 0.VW (conferir se nasceu na worktree) → 0.3 travas
(`mkdir .delta-11/locks/...lock`) → 0.5 ler SÓ as fatias marcadas na seção 2.

**Fim:**
1. **1a** `memoria/[AGENTE]-produto.md` (≤ 500 tokens, com a linha `autocritica: <caminho>`) e **1b**
   `memoria/[AGENTE]-historia.md` — sempre na pasta PRINCIPAL do projeto (caminho absoluto)
2. **3.4** autocrítica em 2 paradas → `logs/autocritica/`
3. **3.5** build-validator · **3.7** contract-tester (gera E roda os testes de contrato do que mudou) —
   relatórios em `logs/sub-agentes/`
4. Commit na branch da worktree
5. **3.8** SendMessage ao CRONOS pedindo a revisão do SHIELD (sem criar `.txt`, sem editar o kanban)
6. **3.9** liberar as travas que você criou
