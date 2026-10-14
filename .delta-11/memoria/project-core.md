# MEMÓRIA CENTRAL DO PROJETO — FORMAÇÃO Δ-11

> **Modelo v6.3 (2026-10-14).** Regras de leitura e escrita deste arquivo:
>
> - **ESCREVE (D7):** SOMENTE o ATLAS — neste arquivo e nas fatias em `memoria/project-core/`. Qualquer outro
>   agente que tenha algo para cá escreve na seção `PROPOSTAS PARA O PROJECT-CORE` do próprio
>   `memoria/[AGENTE]-produto.md`; o CRONOS encaminha ao ATLAS. A abertura de fase do CRONOS vai em
>   `memoria/CRONOS-abertura-fase-N.md`, nunca aqui.
> - **LÊ INTEIRO (D6):** ATLAS, CRONOS, SHIELD, SCOUT e os sub-agentes.
> - **EXECUTORES (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM) NÃO leem este arquivo inteiro.** Leem só as FATIAS do
>   seu papel, que o ATLAS mantém em `memoria/project-core/` (mapa abaixo), mais o próprio
>   `planos/[AGENTE]-plan.md`, a própria coluna do kanban, `pesquisa-tecnica.md` e a própria base de conhecimento.
> - **DUAS VERDADES (D24):** este arquivo é a verdade do CONTRATO (o que o sistema DEVE ser). As migrations em
>   `supabase/migrations/` são a verdade do banco IMPLEMENTADO (o que o banco É). Se divergirem, é bug para o
>   ATLAS decidir: corrigir este arquivo (o contrato estava errado) ou pedir nova migration (o banco está errado).
>
> **Mapa das fatias** (o ATLAS atualiza a fatia no mesmo momento em que atualiza a seção correspondente):
>
> | Fatia | Seções deste arquivo | Quem lê |
> |---|---|---|
> | `memoria/project-core/banco.md` | ESQUEMA DO BANCO DE DADOS + REGRAS DE NEGÓCIO | VAULT, BACK, ENGINE |
> | `memoria/project-core/contratos.md` | CONTRATOS DE API | ENGINE, BACK, FRONT, FORM |
> | `memoria/project-core/visual.md` | VISÃO DO PRODUTO → Telas e experiências + IDENTIDADE VISUAL | FRONT, PIXEL, FORM |
> | `memoria/project-core/decisoes-tecnicas.md` | STACK + ARQUITETURA + DECISÕES TÉCNICAS CRÍTICAS + PADRÕES DE IMPLEMENTAÇÃO | todos os executores |

---

## PROJETO

**Nome:** [preenchido pelo ATLAS]
**Descrição:** [o que o sistema faz, em 2-3 frases]
**Usuários-alvo:** [para quem é]
**Problema que resolve:** [qual dor resolve]
**PRD:** `docs/prd.md` (modelo `templates/prd-documento-de-requisitos-template.md`)

---

## VISÃO DO PRODUTO — Dia 1, a Luz (preenchido pelo ATLAS na Fase 0)

> Modelo de preenchimento: `templates/fase-luz-template.md`. O vigia `dia1-badal-checker.py` exige pelo menos 6 dos
> 8 elementos abaixo ao editar este arquivo ou o `docs/prd.md`. Escreva cada um em 1-2 frases, nas palavras do
> usuário — não em jargão.

1. **Frase decisória:** [a frase que o usuário diz por dentro no momento em que decide usar o produto]
2. **Identidade assumida:** [quem o usuário passa a ser ao usar]
3. **Identidade fugida:** [quem ele está deixando de ser]
4. **Teste do badal:** [as duas identidades ficam nítidas e separadas, sem uma apagar a outra? SIM/NÃO + por quê]
5. **Único inimigo derrotado:** [o UM inimigo que o produto vence]
6. **Único trauma curado:** [a UMA dor antiga que o produto cura]
7. **Único lago abandonado:** [de qual UMA solução atual o usuário sai]
8. **Nova categoria de solução:** [o nome da categoria nova que o produto estabelece]

**Contraposição:** Tipo 1 (existencial-identitária) — identidade assumida × identidade fugida, sem eliminação.

**Avatar (usuário final):**
[Quem é essa pessoa, o que ela está passando, o que já tentou, o que a frustra nas soluções atuais]

**Diferencial competitivo:**
[O que torna este produto diferente e superior ao que existe no mercado. O que faria o usuário abandonar o que usa hoje.]

**Telas e experiências:**
[Para cada tela do projeto:]
```
TELA: [nome]
EXPERIÊNCIA: [o que o usuário vê, faz, e sente]
PROMPT DE DESIGN: [prompt aprovado para geração visual]
REFERÊNCIAS: [links ou descrições de inspiração]
```

---

## CONTRAPOSIÇÃO LATERAL (por dia — Princípio 3 da Metodologia Gênesis)

> O vigia `contraposicao-checker.py` exige a contraposição declarada ao editar este arquivo. O ATLAS preenche a
> linha de cada Dia quando a fase correspondente começa; dias futuros ficam com "[a declarar na Fase N]".
> Referência dos 7 tipos: `conhecimento/metodologia-genesis-camadas.md`.

| Dia | Fase | Contraposição lateral declarada |
|---|---|---|
| 1 — Luz | 0 | **Contraposição:** Tipo 1 — [identidade assumida] × [identidade fugida] |
| 2 — Container | 2 | **Contraposição:** Tipo 2 — [arquitetura sustentadora] × [mundo externo: usuários, integrações] × [mundo interno: regras, dados, estado] |
| 3 — Superfícies | 3 | **Contraposição:** Tipo 3 — [sólido persistente] × [fluido transiente]; [semente exposta] × [semente encapsulada] |
| 4 — Astros | 3.5 | **Contraposição:** Tipo 4 — [síncrono] × [assíncrono]; [dominante] × [testemunha] |
| 5 — Habitantes | 4 | **Contraposição:** Tipo 5 — [backend] × [frontend]; [principal] × [secundário] |
| 6 — Consciência | 4.5 | **Contraposição:** Tipo 6 — [autenticação] × [autorização]; [governança] × [serviços] |
| 7 — Descanso | 7 | **Contraposição:** Tipo 7 — [obra consumada] × [trabalho em curso] |

---

## CLASSIFICAÇÃO

**Complexidade:** [BAIXA (5–8) / MÉDIA (9–12) / ALTA (13–15)]
**Pontuação detalhada (5 critérios, 1 a 3 pontos cada — D14):**
- Telas e rotas: [1-3] pontos — [justificativa]
- Integrações externas: [1-3] pontos — [justificativa]
- Modelo de dados: [1-3] pontos — [justificativa]
- Tempo real: [1-3] pontos — [justificativa]
- Segurança: [1-3] pontos — [justificativa]
- **Total: [5-15] pontos**

**Agentes ativados:** [lista — em BAIXA, os líderes acumulam papéis]

## STACK TECNOLÓGICA

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Interface de Usuário | | |
| Estilização | | |
| Servidor | | |
| Banco de Dados | | |
| Autenticação | | |
| Hospedagem | | |

## ARQUITETURA — Dia 2, o Container (preenchido pelo ATLAS na Fase 2)

[Paradigma escolhido, diagrama de módulos e suas fronteiras, protocolos de comunicação. ADR principal em
`memoria/decisoes/AAAA-MM-DD-titulo.md`. Selo provisório — confirmado retroativamente no Dia 3 (Fase 3).]

---

## DECISÕES TÉCNICAS CRÍTICAS (preenchido pelo ATLAS na Fase 2)

**Autenticação:**
- Login e registro são feitos pelo: [navegador (código do lado do cliente) / servidor (rotas de API)]
- Conferência do usuário no servidor: `@supabase/ssr` + `supabase.auth.getUser()` (nunca `getSession()` no servidor — ele confia no cookie sem conferir com o Supabase)
- Gestão de cookies de sessão: [quem gerencia e como]
- Confirmação de email: [habilitada/desabilitada, página de destino do link]
- Fallback se perfil ainda não existe no primeiro login: [como tratar]

**Serviços externos:**
- Padrão de inicialização: [sob demanda dentro de funções, NUNCA no nível do módulo]
- Comportamento com variáveis de ambiente ausentes: [como tratar]
- Fluxo completo de webhooks: [descrição de cada etapa e tratamento de falha]

**Framework:**
- Rotas do servidor e cookies: [repassam automaticamente ou precisam de configuração]
- Renderização: [quais páginas no servidor, quais no navegador]
- Middleware: [o que protege, e quais defesas existem se ele falhar]

**Armadilhas conhecidas das tecnologias escolhidas:**
1. [Tecnologia]: [armadilha e como evitar]
2. [Tecnologia]: [armadilha e como evitar]
3. [Tecnologia]: [armadilha e como evitar]

---

## PADRÕES DE IMPLEMENTAÇÃO (preenchido pelo ATLAS na Fase 2, obrigatório para TODOS os agentes)

- Serviços externos: inicialização sob demanda, nunca no nível do módulo
- Defesa em profundidade: layouts protegidos devem verificar autenticação independente do middleware
- Tratamento de erros: toda chamada ao banco deve verificar o campo de erro antes de usar os dados
- Tratamento de erros: toda chamada de API no frontend deve ter catch com feedback visível ao usuário (nunca catch vazio)
- Erro de API (D13): validação falhou ou campo faltando = HTTP 400 com `{ "error": { "code": "VALIDATION_ERROR", "message": "texto para humano", "details": [...] } }`
- Tempos-limite (D19): banco 5 s · API externa 10 s · chamada interna 3 s · 3 novas tentativas com espera crescente · circuit breaker abre após 5 falhas e fecha após 60 s
- Validação: toda string deve ter .max() definido
- Validação: toda URL deve rejeitar protocolos perigosos (javascript:, data:, file:, ftp:)
- Componentes: todo componente que recebe dados do servidor deve tratar null e undefined
- Atomicidade: operações que envolvem mais de uma escrita no banco devem ser atômicas
- Nomes em código (D20): inglês, sem abreviação (`/api/users`, `createdAt`, `calculateCartTotal`); textos para humanos em português
- [Adicionar regras específicas do projeto aqui]

---

## IDENTIDADE VISUAL

**Tom visual:** [minimalista refinado / futurista ousado / editorial sofisticado / etc. — preenchido pelo ATLAS]

**Paleta de cores** (nomes das variáveis em inglês — são código):
```css
--color-primary: ;
--color-accent: ;
--color-background: ;
--color-card-background: ;
--color-text-primary: ;
--color-text-secondary: ;
--color-border: ;
--color-success: ;
--color-error: ;
--color-warning: ;
```

**Tipografia:**
- Fonte de títulos: [nome — importar com `next/font`]
- Fonte de corpo: [nome — importar com `next/font`]
- Fonte de código (se aplicável): [nome]

**Estilo de componentes:**
- Bordas: [arredondadas / retas / mistas]
- Sombras: [suaves / dramáticas / nenhuma]
- Espaçamento: [generoso / compacto]
- Animações: [tipo de revelação, transições, micro-interações]

## CONTRATOS DE API

[Cada rota no formato padrão — preenchido pelo ATLAS. Modelo completo: `templates/contratos-api-template.md`.
Nomes de rota e de campo em inglês (D20).]

<!--
ROTA: [MÉTODO] [/api/resource]
DESCRIÇÃO: [o que faz]
AUTENTICAÇÃO: [público / requer token / apenas administrador]

ENTRADA:
{
  fieldName: tipo (obrigatório/opcional) — descrição
}

SAÍDA SUCESSO (código [número]):
{
  fieldName: tipo — descrição
}

SAÍDA ERRO (código 400 — validação, formato único D13):
{
  "error": { "code": "VALIDATION_ERROR", "message": "texto para humano", "details": [...] }
}

SAÍDA ERRO (código [401/403/404/409] — erro de domínio):
{
  "error": { "code": "[UNAUTHORIZED|FORBIDDEN|NOT_FOUND|CONFLICT|...]", "message": "quando acontece" }
}
-->

## ESQUEMA DO BANCO DE DADOS

[Cada tabela com colunas, tipos, relacionamentos — preenchido pelo ATLAS. Modelo completo:
`templates/esquema-banco-template.md`. Este é o CONTRATO do banco; o que está implementado vive em
`supabase/migrations/` (D24).]

<!--
TABELA: [table_name]
| Coluna | Tipo | Restrições | Descrição |
|--------|------|-----------|-----------|
| id | uuid | PK, default gen_random_uuid() | |
| created_at | timestamptz | NOT NULL, default now() | |
-->

## REGRAS DE NEGÓCIO

[Regras fundamentais que nunca podem ser violadas — preenchido pelo ATLAS]

---

## RITMO, CONSCIÊNCIA E DESCANSO (Fases 3.5, 4.5 e 7)

[O ATLAS registra aqui uma linha por entregável quando a fase for selada — o conteúdo completo fica nos arquivos.]

- **Fase 3.5 — Ritmo (Dia 4):** 10 artefatos em `memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<N>-<slug>.md` — [selada em AAAA-MM-DD / pendente]
- **Fase 4.5 — Consciência (Dia 6):** 5 entregáveis em `memoria/decisoes/AAAA-MM-DD-consciencia-<N>-<slug>.md` — [selada em AAAA-MM-DD / pendente]
- **Fase 7 — Descanso (Dia 7):** 10 entregáveis em `memoria/decisoes/AAAA-MM-DD-descanso-<N>-<slug>.md` + runbooks em `memoria/runbooks/` + teste supremo de 2 semanas — [selada em AAAA-MM-DD / pendente]

## DECISÕES ARQUITETURAIS

| Data | Decisão | Justificativa | Impacto |
|------|---------|---------------|---------|
