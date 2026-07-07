# TEMPLATE — PRD (Documento de Requisitos do Produto)

**O que é:** o documento que diz o que o produto É, para QUEM, o que FAZ e — tão importante quanto — o que NÃO faz. É a visão do produto em formato que o comandante lê, aprova e pode compartilhar com qualquer pessoa.

**Onde salvar:** `docs/prd.md` (zoneamento: `docs/` é spec de produto)

**Quem escreve:** **ATLAS**, ao final da Fase 0 (Descoberta) — o PRD consolida as respostas das 7 camadas de perguntas. A aprovação do comandante na Fase 0 passa a ser SOBRE este documento.

**Limite:** máximo ~300 linhas. PRD é bússola, não enciclopédia — detalhe técnico vai para o project-core.md.

---

```markdown
# PRD — [Nome do Produto]

- **Data:** AAAA-MM-DD · **Versão:** 1.0 · **Autor:** ATLAS + Comandante
- **Status:** rascunho | aprovado pelo comandante em AAAA-MM-DD

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

Pergunta-teste sobre cada funcionalidade do item 4: **"Um agente conseguiria implementar isto sem chutar nenhuma decisão?"**
- Se NÃO → falta resposta na descoberta; voltar à camada correspondente da Fase 0 e perguntar ao comandante
- Se SIM para todas → PRD pronto para aprovação
