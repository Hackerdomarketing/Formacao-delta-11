# TEMPLATE — ADR (Registro de Decisão Arquitetural)

**O que é:** o registro de UMA decisão de arquitetura — contexto, decisão, consequências. Um arquivo por decisão, imutável (decisão nova que muda uma antiga = ADR novo apontando para o antigo). É o que responde "por que isso é assim?" meses depois, quando ninguém lembra.

**Onde salvar:** `.delta-11/memoria/decisoes/AAAA-MM-DD-titulo-curto-da-decisao.md` (ex: `2026-07-07-supabase-em-vez-de-firebase.md`)

**Quem escreve:**
- **ATLAS** — ao tomar decisão de arquitetura na Fase 2 e ao aprovar mudança de contrato/esquema em qualquer fase
- **CRONOS** — ao registrar decisão emergente no Protocolo de Abertura de Fase (drift aprovado, mudança de rota)

**Quando NÃO escrever ADR:** decisão trivial ou reversível em minutos (escolha de nome de variável, ordem de tarefas). ADR é para decisões que CUSTAM caro para reverter.

---

```markdown
# ADR: [título da decisão em 1 linha]

- **Data:** AAAA-MM-DD
- **Autor:** [ATLAS ou CRONOS]
- **Status:** aceita | substituída por [link do ADR novo]
- **Fase/Ciclo:** [onde o projeto estava]

## Contexto

[2-5 frases: qual problema ou escolha estava na mesa. O que forçou a decisão AGORA.
Em português de gente — o comandante lê isto.]

## Decisão

[1-3 frases: O QUE foi decidido, afirmativo. "Vamos usar X para Y."]

## Alternativas consideradas

- **[Alternativa A]:** descartada porque [motivo em 1 linha]
- **[Alternativa B]:** descartada porque [motivo em 1 linha]

## Consequências

- **Ganhamos:** [o que fica melhor]
- **Pagamos:** [o custo/limitação aceita — TODA decisão tem um]
- **Reverter custa:** [barato | caro | quase impossível — e por quê em 1 linha]

## Fontes

[Se a decisão veio de pesquisa-tecnica.md, documentação oficial, ou regra do sistema — citar: `[Fonte: arquivo#seção]`]
```
