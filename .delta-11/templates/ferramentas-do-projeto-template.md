# Ferramentas e Serviços Externos deste Projeto

**Projeto:** [PREENCHER — nome do projeto]
**Pasta do projeto:** [PREENCHER — caminho absoluto da pasta, ex: /Users/seunome/Documents/VSCODE/meu-projeto]
**Última atualização:** [PREENCHER — data no formato AAAA-MM-DD]
**Atualizado por:** [PREENCHER — nome do agente que atualizou, ex: ATLAS, ou "comandante" se foi o operador humano]

---

## Como ler este arquivo

Este arquivo é uma lista de TODAS as ferramentas externas que este projeto usa para funcionar. Por "ferramenta externa" entenda: todo serviço online com login, conta paga, ou chave de acesso. Inclui banco de dados, hospedagem, pagamento, envio de e-mail, autenticação, IAs externas, e qualquer plataforma onde foi preciso criar uma conta.

**Não entram aqui** bibliotecas de código abertas (React, Tailwind, Next.js, Zod e similares) — essas estão listadas no `package.json` do projeto e não precisam ser anotadas aqui porque não têm conta, não têm preço, e não exigem login.

**Quem lê este arquivo:**
- O comandante (dono do projeto), para saber em tempo real o que está sendo pago, com qual e-mail cada conta foi criada, qual o link de cada painel administrativo, e como acessar cada serviço quando precisar.
- Qualquer IA trabalhando no projeto — seja Claude Code, Codex, Cursor, Aider, ou agentes Δ-11 (ATLAS, CRONOS, BACK, ENGINE, VAULT, etc.) — para saber o que JÁ está em uso ANTES de sugerir adicionar uma ferramenta nova, e para saber exatamente como ela acessa cada serviço.

**Regra de ouro:** se você é uma IA e está prestes a instalar um SDK de serviço externo (`@supabase/supabase-js`, `stripe`, `resend`, `@upstash/redis`, qualquer coisa parecida), adicionar uma chave de API ao `.env`, ou configurar um novo MCP — PARE. Atualize este arquivo PRIMEIRO. Só depois faça a instalação. Esta é uma Regra Inviolável do Delta-11 (Regra 14).

---

## 1. [NOME DA FERRAMENTA, ex: Supabase]

**O que é:**
[1-2 frases em linguagem leiga, para quem nunca ouviu falar. Ex: "É um banco de dados online onde a gente guarda todas as informações do sistema — cadastros de usuários, produtos, vendas. Ele já vem com sistema de login pronto e regras de segurança que controlam quem pode ver o quê."]

**Por que estamos usando neste projeto:**
[Função específica que essa ferramenta tem no contexto deste projeto. Ex: "Guarda os cadastros dos clientes do salão, controla o login deles, e garante que cada dono de salão só veja os agendamentos do próprio negócio."]

**Requisitos que precisamos para a ferramenta funcionar:**
[Variáveis de ambiente que precisam estar configuradas, configurações mínimas no painel da ferramenta, tabelas/recursos que precisam existir. Ex: "Precisamos das variáveis SUPABASE_URL e SUPABASE_ANON_KEY no arquivo .env do projeto. A tabela 'usuarios' precisa estar criada e com a regra de segurança ativa antes da primeira tela de cadastro funcionar."]

**Plano contratado:**
[Nome do plano. Ex: "Free", "Pro", "Business", "Pay-as-you-go"]

**Preço:**
[Valor com moeda e período. Ex: "R$ 125 por mês", "US$ 25 por mês", "Grátis até 50.000 usuários", "~R$ 0,02 por chamada de API"]

**Data de contratação:**
[Quando a conta foi criada, no formato AAAA-MM-DD. Ex: 2026-06-15]

**E-mail da conta usada para criar:**
[O e-mail que foi usado no cadastro da ferramenta. Ex: rafa@exemplo.com]

**Link para acessar o painel da ferramenta:**
[URL do painel administrativo. Ex: https://supabase.com/dashboard/project/abc123]

**Link da documentação oficial:**
[URL da documentação da ferramenta. Ex: https://supabase.com/docs]

**Como a IA acessa este serviço quando precisa trabalhar com ele:**

Marque com [X] o que se aplica. Pode ser mais de uma forma de acesso.

- [ ] **Pelo operador humano** — a IA NÃO acessa o serviço diretamente; quando precisa de algo (criar uma tabela, ver um relatório), pede ao comandante para fazer pelo painel.
- [ ] **Por CLI** — existe uma ferramenta de linha de comando local (ex: o comando `supabase` no terminal); a IA executa comandos via Bash.
- [ ] **Por MCP** — existe um servidor MCP já configurado neste computador; a IA usa direto pelo Claude Code chamando ferramentas com nomes tipo `mcp__nomeDaFerramenta__*`.
- [ ] **Por API** — existe uma chave de API guardada no arquivo .env do projeto; a IA faz chamadas HTTP (via `fetch`, `curl`, ou SDK do próprio serviço).

**Status:** [Ativa / Em teste / Cancelada / Migrando]
[Use "Ativa" quando está em uso real. "Em teste" quando ainda está sendo avaliada e pode ser descartada. "Cancelada" quando a conta foi encerrada (mantenha a entrada no arquivo para histórico). "Migrando" quando está sendo trocada por outra ferramenta.]

**Observações:**
[Notas livres — limite do plano, data de renovação, contato do suporte, problemas conhecidos, qualquer detalhe relevante. Ex: "Plano Pro renova automaticamente todo dia 15. Limite de 8GB de banco e 250GB de transferência por mês. Acima disso cobra extra. Se passar de 80%, recebo email."]

---

## 2. [PRÓXIMA FERRAMENTA]

[Repita a mesma estrutura para cada ferramenta nova. Mantenha a numeração crescente — 1, 2, 3, 4...]

---

## Histórico de Mudanças

Cada vez que alguma ferramenta é adicionada, removida, troca de plano, ou troca de status, registre uma linha aqui. Formato:

`AAAA-MM-DD — [tipo de mudança] — [agente ou comandante] — [descrição curta]`

**Exemplos:**

- 2026-06-15 — Adicionada — ATLAS — Supabase (plano Free) registrada na Fase 0 do projeto
- 2026-06-18 — Adicionada — ENGINE — Stripe (Pay-as-you-go) registrada antes de implementar a tela de checkout
- 2026-07-02 — Upgrade — comandante — Supabase migrado de Free para Pro (R$ 125/mês) por aproximação do limite de armazenamento
- 2026-08-10 — Cancelada — comandante — Mailgun cancelado e substituído por Resend (registrado na entrada de Resend acima)
