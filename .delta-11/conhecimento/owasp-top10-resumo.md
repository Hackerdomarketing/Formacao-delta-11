# Base de Conhecimento de Seguranca — SHIELD Agent

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Você REPROVA código que viola estes limites — inclua a checagem em toda revisão.


Referencia pratica para auditoria de seguranca em aplicacoes web.
Foco: Next.js + Supabase. Verificacoes executaveis por leitura de codigo.

---

## 1. OWASP Top 10 (2021) — Resumo Acionavel

### A01: Broken Access Control

**O que e:** Usuario acessa recursos ou acoes que nao deveria (ver dados de outro usuario, acessar painel admin sem permissao).

**Como detectar no codigo:**
- Rotas de API sem verificacao de `session` ou `user.id` antes de retornar dados
- Queries ao banco sem filtro por `user_id` (ex: `SELECT * FROM pedidos` sem `WHERE user_id = ?`)
- Paginas admin sem middleware de autenticacao/autorizacao
- IDs sequenciais expostos em URLs sem validacao de propriedade (IDOR)
- Falta de RLS no Supabase (tabelas com `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` ausente)

**Como corrigir:**
- Toda rota de API valida sessao: `const { data: { session } } = await supabase.auth.getSession()`
- Toda query filtra por `user_id` do usuario autenticado
- RLS ativado em TODAS as tabelas do Supabase com policies explicitas
- Middleware Next.js protege rotas privadas (`middleware.ts`)

---

### A02: Cryptographic Failures

**O que e:** Dados sensiveis expostos por falta de criptografia ou criptografia fraca.

**Como detectar no codigo:**
- Senhas armazenadas em texto puro (sem hash)
- Tokens ou chaves em codigo-fonte, logs ou respostas de API
- `NEXT_PUBLIC_` prefixo em variaveis que contem segredos (expoe no browser)
- Comunicacao HTTP em vez de HTTPS
- Algoritmos fracos: MD5, SHA1 para hashing de senhas

**Como corrigir:**
- Supabase Auth cuida do hashing de senhas (bcrypt) — nao reinventar
- Segredos APENAS em `.env.local` sem prefixo `NEXT_PUBLIC_`
- Verificar que `SUPABASE_SERVICE_ROLE_KEY` NUNCA aparece no frontend
- Forcar HTTPS em producao

---

### A03: Injection

**O que e:** Dados do usuario executados como codigo (SQL, JavaScript, comandos do sistema).

**Como detectar no codigo:**
- Concatenacao de strings em queries SQL: `` `SELECT * FROM users WHERE id = ${input}` ``
- `dangerouslySetInnerHTML` com dados nao sanitizados
- `eval()`, `Function()`, `setTimeout(string)` com input do usuario
- Supabase RPC com parametros nao validados
- Template literals em queries sem parameterizacao

**Como corrigir:**
- Supabase client usa queries parametrizadas por padrao — manter esse padrao
- Para RPC: `supabase.rpc('funcao', { param: valorValidado })`
- NUNCA usar `dangerouslySetInnerHTML` com dados de usuario
- Usar bibliotecas de sanitizacao (DOMPurify) se HTML dinamico for necessario

---

### A04: Insecure Design

**O que e:** Falhas de arquitetura que nenhuma implementacao correta consegue resolver.

**Como detectar no codigo:**
- Ausencia de rate limiting em endpoints sensiveis (login, registro, reset senha)
- Logica de negocio no frontend que deveria estar no servidor
- Falta de validacao server-side (confiando apenas no frontend)
- Fluxo de pagamento sem verificacao server-side do valor

**Como corrigir:**
- Rate limiting via middleware ou Supabase Edge Functions
- TODA logica de negocio critica no servidor (API routes ou Supabase Functions)
- Validacao duplicada: frontend (UX) + servidor (seguranca)

---

### A05: Security Misconfiguration

**O que e:** Configuracoes padrao inseguras ou configuracoes esquecidas.

**Como detectar no codigo:**
- `next.config.js` com headers de seguranca ausentes
- CORS configurado como `*` (aceita qualquer origem)
- `.env` ou `.env.local` no repositorio Git (verificar `.gitignore`)
- `DEBUG=true` ou modo verbose em producao
- Supabase anon key usada para operacoes que deveriam usar service role (e vice-versa)
- Headers faltando: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`

**Como corrigir:**
- Adicionar security headers em `next.config.js` ou `middleware.ts`
- CORS restrito ao dominio da aplicacao
- `.env*` listado no `.gitignore`
- Separar anon key (frontend) de service role key (servidor apenas)

---

### A06: Vulnerable and Outdated Components

**O que e:** Dependencias com vulnerabilidades conhecidas.

**Como detectar no codigo:**
- `npm audit` reporta vulnerabilidades altas ou criticas
- `package.json` com versoes fixas muito antigas (sem `^` ou `~`)
- Dependencias abandonadas (sem commit no repo ha mais de 1 ano)

**Como corrigir:**
- Rodar `npm audit fix` regularmente
- Manter dependencias atualizadas, especialmente `next`, `@supabase/supabase-js`

---

### A07: Identification and Authentication Failures

**O que e:** Falhas no sistema de login, sessao ou identidade do usuario.

**Como detectar no codigo:**
- Sessao que nunca expira (sem `maxAge` em cookies)
- Token JWT armazenado em `localStorage` (vulneravel a XSS)
- Falta de verificacao de email no registro
- Reset de senha sem token de uso unico ou com token que nao expira
- Ausencia de protecao contra brute force no login

**Como corrigir:**
- Usar Supabase Auth (gerencia sessoes, tokens, refresh automatico)
- Cookies HttpOnly para tokens (Supabase SSR faz isso)
- Ativar verificacao de email no Supabase Dashboard
- Rate limiting no endpoint de login

---

### A08: Software and Data Integrity Failures

**O que e:** Codigo ou dados modificados sem verificacao de integridade.

**Como detectar no codigo:**
- CI/CD sem verificacao de integridade de pacotes
- `npm install` sem `package-lock.json` (versoes podem mudar)
- Webhooks recebidos sem validacao de assinatura
- Updates de banco sem validacao de schema

**Como corrigir:**
- Manter `package-lock.json` no repositorio
- Validar assinatura de webhooks (Stripe, Supabase, etc.)

---

### A09: Security Logging and Monitoring Failures

**O que e:** Falta de registros de eventos de seguranca.

**Como detectar no codigo:**
- Login falho sem log
- Mudancas de permissao sem auditoria
- Erros de autorizacao silenciados (catch vazio)
- Ausencia de monitoramento de erros (sem Sentry, LogRocket, etc.)

**Como corrigir:**
- Logar tentativas de login (sucesso e falha)
- Logar acessos negados com detalhes (IP, user agent, endpoint)
- Nunca usar `catch(e) {}` vazio — pelo menos logar o erro

---

### A10: Server-Side Request Forgery (SSRF)

**O que e:** Servidor faz requisicoes para URLs controladas pelo atacante.

**Como detectar no codigo:**
- `fetch(userInput)` ou `axios.get(userInput)` no servidor
- Funcoes que aceitam URLs externas sem validacao (upload por URL, preview de link)

**Como corrigir:**
- Validar e restringir URLs aceitas (whitelist de dominios)
- Bloquear IPs internos (127.0.0.1, 10.x.x.x, 192.168.x.x)
- Nao permitir redirecionamentos automaticos em requisicoes do servidor

---

## 2. Padroes de Seguranca Next.js + Supabase

### Checklist de Verificacao Rapida

```
[ ] middleware.ts protege rotas autenticadas (redireciona para login se sem sessao)
[ ] Supabase client do servidor usa createServerClient (nao createBrowserClient)
[ ] Service role key usada APENAS em API routes ou Server Actions, NUNCA no frontend
[ ] Todas as tabelas com RLS ativado
[ ] Server Actions validam input antes de processar
[ ] API routes retornam 401/403 para requests nao autorizados (nao 200 com erro no body)
[ ] next.config.js define security headers
[ ] Imagens externas restritas em next.config.js (remotePatterns)
```

### Padroes Perigosos Especificos

| Padrao perigoso | Onde procurar | Alternativa segura |
|---|---|---|
| `createBrowserClient` no servidor | API routes, Server Components | `createServerClient` |
| `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY` | `.env*` | Remover `NEXT_PUBLIC_` — nunca expor no browser |
| `supabase.auth.getUser()` sem validar retorno | API routes | Verificar `error` e `data.user` antes de prosseguir |
| `headers()` / `cookies()` em Client Component | Componentes com `"use client"` | Mover logica para Server Component ou API route |
| Fetch sem `cache: 'no-store'` para dados sensiveis | Server Components | Adicionar `cache: 'no-store'` ou `revalidate: 0` |

---

## 3. Checklist de Autenticacao

```
[ ] Tokens JWT armazenados em cookies HttpOnly (nao localStorage)
[ ] Cookies com flags: HttpOnly, Secure, SameSite=Lax (minimo)
[ ] Refresh token rotacionado apos cada uso
[ ] Sessao expira apos periodo de inatividade (maxAge definido)
[ ] Logout invalida sessao no servidor (nao apenas apaga cookie local)
[ ] Verificacao de email obrigatoria no registro
[ ] Rate limiting em: login, registro, reset de senha, verificacao de email
[ ] Senhas com requisito minimo (8+ caracteres)
[ ] CSRF protection em forms que mutam dados (POST/PUT/DELETE)
[ ] Supabase Auth configurado com autoRefreshToken e persistSession
```

---

## 4. Validacao de Input

### Regras de Verificacao no Codigo

**Server-side (OBRIGATORIO):**
```
[ ] Todo endpoint de API valida tipo, formato e tamanho dos parametros
[ ] Usar Zod, Yup ou similar para schema validation no servidor
[ ] Rejeitar requests com campos extras nao esperados
[ ] Limitar tamanho de uploads (next.config.js: api.bodyParser.sizeLimit)
[ ] Escapar output HTML (React faz por padrao, MAS cuidado com dangerouslySetInnerHTML)
```

**Prevencao de XSS:**
```
[ ] Zero uso de dangerouslySetInnerHTML com dados de usuario
[ ] Content-Security-Policy header definido
[ ] Nenhum eval(), Function(), document.write() com input externo
[ ] URLs validadas antes de usar em href (prevenir javascript: protocol)
[ ] Dados de usuario nunca inseridos diretamente em atributos HTML de evento (onclick, etc.)
```

**Prevencao de SQL Injection:**
```
[ ] Zero concatenacao de strings em queries (nem em Supabase RPC raw SQL)
[ ] Supabase client methods usados (select, insert, update) — estes parametrizam automaticamente
[ ] Supabase Functions (Edge Functions) com parametros tipados
[ ] Se usar SQL raw em migrations: parametros via $1, $2 (nunca interpolacao)
```

---

## 5. Row Level Security (RLS) — Erros Comuns

### Erros que o SHIELD deve detectar

| Erro | Como detectar | Impacto |
|---|---|---|
| RLS desativado na tabela | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` ausente | Qualquer usuario acessa tudo |
| Policy com `USING (true)` | Grep por `USING (true)` nas policies | Equivale a nao ter RLS |
| SELECT sem policy mas INSERT com | Verificar que todas as operacoes (SELECT, INSERT, UPDATE, DELETE) tem policy | Dados vazam via SELECT |
| Policy referencia `auth.uid()` mas tabela nao tem coluna `user_id` | Comparar schema com policies | Policy nao filtra nada |
| Service role usado no frontend | `SUPABASE_SERVICE_ROLE_KEY` acessivel no browser | Bypass total do RLS |
| Policy permite UPDATE sem restringir colunas | UPDATE policy sem `WITH CHECK` | Usuario altera campos proibidos |
| Falta de policy para DELETE | Tabela com RLS mas sem policy de DELETE | DELETE falha silenciosamente ou permite tudo |
| Junction tables sem RLS | Tabelas de relacao N:N esquecidas | Relacoes expostas entre usuarios |

### Padrao Correto de RLS

```sql
-- Ativar RLS
ALTER TABLE tabela ENABLE ROW LEVEL SECURITY;

-- SELECT: usuario ve apenas seus dados
CREATE POLICY "usuario_ve_seus_dados" ON tabela
  FOR SELECT USING (auth.uid() = user_id);

-- INSERT: usuario insere apenas com seu id
CREATE POLICY "usuario_insere_seus_dados" ON tabela
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- UPDATE: usuario atualiza apenas seus dados
CREATE POLICY "usuario_atualiza_seus_dados" ON tabela
  FOR UPDATE USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- DELETE: usuario deleta apenas seus dados
CREATE POLICY "usuario_deleta_seus_dados" ON tabela
  FOR DELETE USING (auth.uid() = user_id);
```

---

## 6. Seguranca de Variaveis de Ambiente

### Verificacoes Obrigatorias

```
[ ] .env e .env.local listados no .gitignore
[ ] .env NAO aparece no git status (nao rastreado)
[ ] .env.example existe com APENAS nomes de variaveis (sem valores reais)
[ ] Nenhum segredo tem prefixo NEXT_PUBLIC_ (expoe no browser)
[ ] SUPABASE_SERVICE_ROLE_KEY existe APENAS em .env.local (nunca .env commitado)
[ ] Variaveis de producao configuradas no provedor de deploy (Vercel, etc.), nao em arquivo
[ ] Nenhuma chave de API, token ou senha hardcoded no codigo-fonte
[ ] Nenhum console.log() imprime variaveis de ambiente ou tokens
```

### Mapa de Variaveis Supabase

| Variavel | Prefixo NEXT_PUBLIC_ | Onde usar |
|---|---|---|
| `SUPABASE_URL` | Sim (seguro) | Frontend e servidor |
| `SUPABASE_ANON_KEY` | Sim (seguro — RLS protege) | Frontend e servidor |
| `SUPABASE_SERVICE_ROLE_KEY` | NUNCA | Apenas servidor (API routes, Server Actions) |
| `DATABASE_URL` | NUNCA | Apenas servidor ou migrations |
| `JWT_SECRET` | NUNCA | Apenas configuracao do Supabase |

---

## Protocolo de Auditoria do SHIELD

Ao revisar codigo de outro agente, seguir esta ordem:

1. **Variaveis de ambiente** — Verificar exposicao de segredos (secao 6)
2. **Autenticacao** — Verificar fluxo de login e protecao de rotas (secao 3)
3. **Controle de acesso** — Verificar RLS e filtros por user_id (secoes 1-A01 e 5)
4. **Validacao de input** — Verificar sanitizacao server-side (secao 4)
5. **Padroes Next.js/Supabase** — Verificar erros especificos do stack (secao 2)
6. **Injecao** — Verificar concatenacao de strings em queries (secao 1-A03)
7. **Headers de seguranca** — Verificar next.config.js e middleware (secao 1-A05)
