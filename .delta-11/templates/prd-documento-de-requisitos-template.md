# TEMPLATE — PRD (Documento de Requisitos do Produto)

**O que é:** o documento que diz o que o produto É, para QUEM, o que FAZ e — tão importante quanto — o que NÃO faz. É a visão do produto em formato que o comandante lê, aprova e pode compartilhar com qualquer pessoa.

**Onde salvar:** `docs/prd.md` (zoneamento: `docs/` é spec de produto)

**Quem escreve:** **ATLAS**, ao final da Fase 0 (Descoberta) — o PRD consolida as respostas das 7 camadas de perguntas. A aprovação do comandante na Fase 0 passa a ser SOBRE este documento.

**Limite:** máximo ~300 linhas. PRD é bússola, não enciclopédia — detalhe técnico vai para o project-core.md.

**Versão do modelo:** v6.3 (2026-10-14) — acrescenta a seção 0 com os 8 elementos do Dia 1 (Luz) que o vigia
`dia1-badal-checker.py` exige (pelo menos 6 de 8) ao editar `docs/prd.md`. Guia de como chegar em cada resposta:
`templates/fase-luz-template.md`. Os mesmos 8 elementos vão para a seção VISÃO DO PRODUTO do project-core.

---

```markdown
# PRD — [Nome do Produto]

- **Data:** AAAA-MM-DD · **Versão:** 1.0 · **Autor:** ATLAS + Comandante
- **Status:** rascunho | aprovado pelo comandante em AAAA-MM-DD

## 0. A Luz — o propósito nuclear (Dia 1 da Metodologia Gênesis)

> Responda cada item em 1-2 frases, nas palavras do usuário. Se um item não se aplica, escreva "não se aplica —
> [motivo]" (o vigia aceita até 2 ausentes, mas a ausência precisa de motivo).

1. **Frase decisória:** [a frase que o usuário diz por dentro quando decide usar — ex.: "chega de perder venda por demora no WhatsApp"]
2. **Identidade assumida:** [quem ele passa a ser ao usar — ex.: "o dono que responde na hora, mesmo dormindo"]
3. **Identidade fugida:** [quem ele está deixando de ser — ex.: "o dono escravo do celular"]
4. **Teste do badal:** [as duas identidades ficam nítidas e separadas, sem uma apagar a outra? SIM/NÃO + por quê]
5. **Único inimigo derrotado:** [o UM inimigo que o produto vence — ex.: "a demora na primeira resposta"]
6. **Único trauma curado:** [a UMA dor antiga que o produto cura — ex.: "o cliente que sumiu depois de esperar 2 horas"]
7. **Único lago abandonado:** [de qual UMA solução atual o usuário sai — ex.: "planilha + WhatsApp pessoal"]
8. **Nova categoria de solução:** [o nome da categoria nova que o produto estabelece — ex.: "atendente de vendas que nunca dorme"]

**Contraposição:** Tipo 1 — identidade assumida × identidade fugida (separação nítida, sem eliminação).

## 1. O problema (por que este produto existe)

[2-4 frases: a dor real, de quem, e o prejuízo de não resolver. Vem das camadas 1 da Fase 0 — GATE P8: se não há prejuízo real, o projeto não deveria existir.]

## 2. Para quem (avatar)

[3-5 frases: quem usa, contexto, nível técnico, o que essa pessoa valoriza.]

## 3. A solução em 1 parágrafo

[O que o produto faz, na frase que o comandante usaria para explicar a um amigo.]

## 4. O que o produto FAZ (funcionalidades do MVP)

1. [funcionalidade — 1 linha cada, em linguagem de resultado: "o usuário consegue X"]
2. …

## 5. O que o produto NÃO FAZ (anti-escopo — tão importante quanto o item 4)

- [o que foi deliberadamente deixado de fora e por quê — 1 linha cada]

## 6. Como saberemos que deu certo (métricas)

- [métrica de sucesso definida na camada 4 da Fase 0 — ex: "X usuários fazem Y na primeira semana"]

## 7. Restrições e premissas

- **Orçamento/ferramentas:** [limites definidos na camada 2]
- **Prazo:** [se houver]
- **Premissas:** [o que assumimos como verdade — se cair, o plano muda]

## 8. Riscos conhecidos

- [risco → mitigação em 1 linha]
```

## Auditoria de completude (ATLAS executa ANTES de pedir aprovação)

**Seção 0 (Dia 1):** os 8 elementos estão respondidos (ou com motivo de ausência)? Teste final: "se qualquer pessoa
da equipe for perguntada sobre o propósito nuclear, todas respondem essencialmente a mesma coisa?"

Pergunta-teste sobre cada funcionalidade do item 4: **"Um agente conseguiria implementar isto sem chutar nenhuma decisão?"**
- Se NÃO → falta resposta na descoberta; voltar à camada correspondente da Fase 0 e perguntar ao comandante
- Se SIM para todas → PRD pronto para aprovação
