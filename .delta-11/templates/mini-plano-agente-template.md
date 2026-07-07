# Mini-plano — [AGENTE] | [Ciclo/Fase] | ONDA [N]

> **Template v5.2 — Mini-plano de agente executor.**
> Gerado pelo CRONOS na Fase 2.5 (ou em replanejamento). Salvo em `.delta-11/planos/[AGENTE]-plan-[ciclo]-onda-[N].md`.
> Convenção de nome: `[AGENTE]-plan-[nome-do-ciclo]-onda-[N][-subtopico].md` (ex: `ENGINE-plan-ciclo-robustez-onda-4-email.md`).
> LIMITE: o brief de despacho derivado deste plano não pode passar de 2.000 tokens (hook `pre-despacho.py` bloqueia).
> Se este plano SUBSTITUI versão anterior, declare no bloco de contexto abaixo e preserve a anterior para auditoria.

## Contexto

[2-4 frases: por que esta onda existe, o que veio antes, decisões do comandante/ATLAS que autorizam.
Se substitui plano anterior: qual, por quê, e onde a versão descartada está preservada.]

## 1. O que esta tarefa precisa produzir

[Descrição funcional do entregável — o que DEVE existir ao final. Não como fazer, o QUE.
Liste arquivos a criar/modificar com paths exatos quando conhecidos.]

## 2. Recorte relevante da fase anterior

[APENAS o que do produto da fase/onda anterior afeta diretamente este agente. NÃO o arquivo inteiro.
Cite: contratos que consome (com linha do contratos-api.md), tabelas que usa, decisões que o limitam.]

## 3. Critérios de sucesso desta tarefa

[Derivados dos critérios da fase; específicos e verificáveis. Máximo 6 itens — se precisar de mais,
a tarefa é grande demais: quebre em mais ondas (princípio da granularização v5).]

- [ ] [critério 1 — mensurável]
- [ ] `tsc --noEmit` 0 erros / `npm run test:contracts` sem regressão / build PASS (adaptar ao stack)

## 4. Dependências

- **Depende de:** [tarefa/agente + o que precisa estar pronto + como verificar que está]
- **Desbloqueia:** [tarefa/agente que espera este trabalho]

## 5. LIMITES DE ESCOPO (OBRIGATÓRIO — v4.0.3)

**O que está EXPLICITAMENTE FORA do escopo desta tarefa:**

- [item 1 — o que este agente NÃO deve fazer, mesmo que pareça útil]
- [item 2 — decisão que não é deste agente]
- [item 3 — preocupação de fase futura que não deve ser antecipada]

**Regra para o agente:** se algo não está nos critérios de sucesso MAS parece útil → verifique se
viola os limites. Se violar, PARE e envie SendMessage ao CRONOS.
**Regra para o SHIELD:** output que viola limites = REPROVAÇÃO IMEDIATA, independente de qualidade técnica.

## 6. CONVENÇÕES (fixo — CRONOS copia esta seção em todo mini-plano de código)

- **Limites estruturais:** função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · componente React ≤ 150 linhas e ≤ 5 props · rota ≤ 150 linhas (`regras-codigo.md` seção 8 — build-validator bloqueia).
- **Idioma:** nomes de variáveis/funções/tabelas/campos JSON em INGLÊS, sem abreviação; comentários, textos de UI, mensagens ao usuário e descrições de teste em PORTUGUÊS (`regras-codigo.md` seção 9).

## Formato de output (ao concluir)

1. Cadeia de sub-agentes obrigatória (build-validator → contract-tester),
   relatórios persistidos em `.delta-11/logs/sub-agentes/` (v5.2 — M-12)
2. Atualizar kanban.md + kanban-data.js + [AGENTE]-produto.md (path absoluto do repo principal)
3. Commit na branch da worktree
4. SendMessage ao CRONOS com payload JSON estruturado
5. Remover ACK se última tarefa
