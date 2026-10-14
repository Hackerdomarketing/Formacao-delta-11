# TEMPLATE — Fase 0: A Luz, o Propósito Nuclear (Dia 1 da Metodologia Gênesis)

> **O que é:** o roteiro que o ATLAS segue na Fase 0 (Descoberta e Design) para chegar às **8 respostas do Dia 1**
> e registrá-las nos dois lugares que o sistema confere:
> - `docs/prd.md` → seção **0. A Luz** (modelo `templates/prd-documento-de-requisitos-template.md`)
> - `.delta-11/memoria/project-core.md` → seção **VISÃO DO PRODUTO — Dia 1, a Luz**
>
> **Vigia que confere:** `hooks/dia1-badal-checker.py` — ao editar o PRD ou o project-core, ele procura os 8
> elementos pelos nomes abaixo e **bloqueia se houver menos de 6**. Use os nomes exatamente como estão (ex.:
> "Frase decisória", "Teste do badal", "Único lago abandonado"), senão o vigia não os encontra.
>
> **Quem faz:** ATLAS (facilitador) + Comandante, na conversa da Fase 0. O ATLAS pergunta; o comandante responde.
> **Quem sela:** o Comandante (o propósito do produto é decisão de negócio — uma das 3 situações em que o
> sistema fala com ele, D4).
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 1 (A Luz).
> **Versão do template:** v6.3 (2026-10-14) — criado na correção C-112.

---

## Como conduzir (ritmo da conversa)

1. **Uma pergunta por vez**, em linguagem do dia a dia. Nada de "qual é a sua proposta de valor?".
2. **Devolva com as palavras dele:** "Então, se eu entendi, quem usa diz por dentro: '...'. É isso?"
3. **Só avance quando ele confirmar.** Resposta vaga ("ajudar as pessoas") volta com um exemplo concreto.
4. **Um de cada:** inimigo, trauma e lago são ÚNICOS. Se vierem três, peça para escolher o principal — os outros
   vão para o anti-escopo ou para depois.
5. Os 8 elementos podem ser preenchidos junto com o AVATAR, o DIFERENCIAL, a EXPERIÊNCIA e a IDENTIDADE VISUAL
   que o protocolo da Fase 0 já pede — eles se completam.

---

## As 8 perguntas (o que perguntar e o que registrar)

| # | Elemento (nome exato) | Pergunta ao comandante | Resposta boa (exemplo) | Resposta fraca (refazer) |
|---|---|---|---|---|
| 1 | **Frase decisória** | "Qual é a frase que o seu cliente diz por dentro no minuto em que decide usar isso?" | "Chega de perder venda porque demorei no WhatsApp." | "Quero mais eficiência." |
| 2 | **Identidade assumida** | "Quem ele passa a ser quando usa o produto?" | "O dono que responde na hora, mesmo dormindo." | "Um usuário satisfeito." |
| 3 | **Identidade fugida** | "Quem ele está cansado de ser e quer deixar para trás?" | "O dono escravo do celular." | "Alguém sem o produto." |
| 4 | **Teste do badal** | "Dá para ver a diferença entre esses dois sem confusão? E ele continua sendo ele mesmo, só que melhor?" | "Sim: antes ele vivia preso ao celular; agora o celular trabalha por ele. Ele não deixou de ser dono." | "Mais ou menos." |
| 5 | **Único inimigo derrotado** | "Se o produto pudesse vencer UMA coisa só, qual seria?" | "A demora na primeira resposta." | "A concorrência, o preço e a falta de tempo." |
| 6 | **Único trauma curado** | "Qual é a lembrança ruim que ele não quer viver de novo?" | "O cliente que sumiu depois de esperar 2 horas." | "Problemas em geral." |
| 7 | **Único lago abandonado** | "O que ele usa hoje e vai largar quando tiver o produto?" | "Planilha + WhatsApp pessoal." | "Nada." |
| 8 | **Nova categoria de solução** | "Como você chamaria essa coisa, se não pudesse usar o nome de nenhum produto que já existe?" | "Atendente de vendas que nunca dorme." | "Um app de chat." |

**Contraposição:** Tipo 1 (existencial-identitária) — identidade assumida × identidade fugida. A separação é
nítida (*vayavdel*, separar com nitidez), **sem eliminação**: o produto não apaga quem o usuário era; separa as
duas versões com clareza.

---

## Bloco para copiar (vai igual no PRD e no project-core)

```markdown
1. **Frase decisória:** [...]
2. **Identidade assumida:** [...]
3. **Identidade fugida:** [...]
4. **Teste do badal:** [SIM/NÃO — por quê, em 1 frase]
5. **Único inimigo derrotado:** [...]
6. **Único trauma curado:** [...]
7. **Único lago abandonado:** [...]
8. **Nova categoria de solução:** [...]

**Contraposição:** Tipo 1 — [identidade assumida] × [identidade fugida], sem eliminação.
```

Se um elemento realmente não se aplica, escreva o nome dele e "não se aplica — [motivo]". O vigia aceita até 2
ausentes; mais que isso significa que a Fase 0 não terminou.

---

## Selo do Dia 1 (critérios objetivos)

- [ ] Os 8 elementos estão no `docs/prd.md` (seção 0) **e** no `project-core.md` (VISÃO DO PRODUTO), com o mesmo texto
- [ ] A contraposição Tipo 1 está declarada nos dois arquivos (linha `**Contraposição:**`)
- [ ] Teste final: o ATLAS escreve, sem olhar o PRD, o propósito do produto em 1 frase — e ela bate com a frase decisória e a nova categoria
- [ ] O comandante confirmou o PRD (status "aprovado pelo comandante em AAAA-MM-DD")

Selado o Dia 1, o ATLAS segue para a Fase 1 (classificação) e depois para a Fase 2 (Dia 2 — Container).
