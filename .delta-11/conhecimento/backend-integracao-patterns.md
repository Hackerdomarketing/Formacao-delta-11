# Base de Conhecimento: Backend e Integracao — BACK

Referencia pratica para lideranca tecnica de servidor em projetos web.
Foco: Next.js API Routes + Supabase. Otimizacao, autenticacao, integracao.

---

## 1. Arquitetura de Rotas Modulares

### Estrutura padrao de API Route (Next.js App Router)

```typescript
// src/app/api/[recurso]/route.ts

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const supabase = createRouteHandlerClient({ cookies })

  // 1. Autenticacao
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    return NextResponse.json({ error: 'nao autenticado' }, { status: 401 })
  }

  // 2. Validacao de entrada
  const { searchParams } = new URL(request.url)
  const page = Math.max(1, parseInt(searchParams.get('page') || '1'))

  // 3. Query ao banco (sempre filtrar por user_id)
  const { data, error } = await supabase
    .from('recurso')
    .select('*')
    .eq('user_id', session.user.id)
    .range((page - 1) * 20, page * 20 - 1)

  // 4. Tratamento de erro
  if (error) {
    console.error('[API /recurso GET]', error.message)
    return NextResponse.json({ error: 'erro interno' }, { status: 500 })
  }

  // 5. Resposta
  return NextResponse.json({ data })
}
```

### Principios de organizacao

- Uma pasta por recurso: `/api/users/`, `/api/orders/`, `/api/products/`
- Rotas aninhadas para sub-recursos: `/api/orders/[id]/items/`
- Logica de negocio em funcoes separadas (nao inline na route handler)
- Servicos externos inicializados DENTRO da funcao (nunca no topo do modulo)

---

## 2. Otimizacao de Queries

### N+1 — O problema mais comum

**O que e:** Para cada item de uma lista, fazer uma query extra ao banco.

```typescript
// ERRADO — N+1: 1 query para pedidos + N queries para itens
const pedidos = await supabase.from('pedidos').select('*')
for (const pedido of pedidos.data) {
  const itens = await supabase.from('itens').select('*').eq('pedido_id', pedido.id)
}

// CERTO — 1 query com join
const pedidos = await supabase
  .from('pedidos')
  .select('*, itens(*)')
  .eq('user_id', session.user.id)
```

### Indices

Todo campo usado em WHERE, ORDER BY ou JOIN DEVE ter indice:

```sql
-- Campos obrigatorios para indice
CREATE INDEX idx_pedidos_user_id ON pedidos(user_id);
CREATE INDEX idx_pedidos_created_at ON pedidos(created_at);
CREATE INDEX idx_itens_pedido_id ON itens(pedido_id);

-- Indice composto para queries frequentes
CREATE INDEX idx_pedidos_user_status ON pedidos(user_id, status);
```

### Paginacao

NUNCA retorne todos os registros. Sempre pagine:

```typescript
// Padrao: 20 itens por pagina
const PAGE_SIZE = 20
const from = (page - 1) * PAGE_SIZE
const to = from + PAGE_SIZE - 1

const { data, count } = await supabase
  .from('recurso')
  .select('*', { count: 'exact' })
  .range(from, to)
  .order('created_at', { ascending: false })
```

### Quando usar cache

| Condicao | Estrategia |
|----------|-----------|
| Dados lidos >10x/min e mudam raramente | Cache com TTL de 5-15 min |
| Dados do usuario atual, mudam sempre | Sem cache (query direto) |
| Dados publicos (categorias, config) | Cache longo (1 hora+) |
| Contadores e agregacoes | Cache curto (1-5 min) |

---

## 3. Padroes de Autenticacao

### Fluxo padrao (Supabase Auth)

```
1. Login: supabase.auth.signInWithPassword()
2. Sessao: cookie httpOnly gerenciado pelo Supabase Auth Helpers
3. Verificacao: getSession() em toda rota protegida
4. Refresh: automatico pelo Supabase (access token expira em 1h)
5. Logout: supabase.auth.signOut()
```

### Middleware de protecao (Next.js)

```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })
  const { data: { session } } = await supabase.auth.getSession()

  // Rotas protegidas
  if (req.nextUrl.pathname.startsWith('/app') && !session) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // Rotas de admin
  if (req.nextUrl.pathname.startsWith('/admin')) {
    if (!session) return NextResponse.redirect(new URL('/login', req.url))
    // Verificar role (coluna na tabela profiles)
    const { data: profile } = await supabase
      .from('profiles')
      .select('role')
      .eq('id', session.user.id)
      .single()
    if (profile?.role !== 'admin') {
      return NextResponse.redirect(new URL('/app', req.url))
    }
  }

  return res
}

export const config = {
  matcher: ['/app/:path*', '/admin/:path*']
}
```

### Regras inviolaveis de autenticacao

- TODA rota de API que retorna dados do usuario verifica `session`
- NUNCA confie em dados do cliente para autorizar (sempre re-verificar no servidor)
- Tokens e chaves NUNCA no frontend (`NEXT_PUBLIC_` so para dados publicos)
- RLS no Supabase e a segunda camada — middleware e a primeira

---

## 4. Tratamento de Erros HTTP

### Tabela de status codes

| Status | Quando usar | Exemplo de resposta |
|--------|------------|-------------------|
| 200 | Sucesso em leitura | `{ data: [...] }` |
| 201 | Sucesso em criacao | `{ data: { id: "..." } }` |
| 400 | Entrada invalida | `{ error: "campo X obrigatorio" }` |
| 401 | Nao autenticado | `{ error: "sessao expirada" }` |
| 403 | Sem permissao | `{ error: "sem acesso a este recurso" }` |
| 404 | Nao encontrado | `{ error: "recurso nao encontrado" }` |
| 409 | Conflito (ex: duplicata) | `{ error: "email ja cadastrado" }` |
| 422 | Validacao semantica | `{ error: "valor fora do range permitido" }` |
| 429 | Limite de requisicoes | `{ error: "muitas requisicoes, aguarde" }` |
| 500 | Erro interno | `{ error: "erro interno" }` |

### Formato padrao de resposta de erro

```typescript
// Sucesso
{ data: { ... } }

// Erro
{ error: "mensagem legivel para o usuario" }

// Erro com detalhes (validacao)
{ error: "validacao falhou", details: { campo: "mensagem" } }
```

### Logging de erros

```typescript
// Sempre logue com contexto suficiente para diagnostico
console.error(`[API /recurso ${method}]`, {
  error: error.message,
  userId: session?.user?.id,
  input: { campo1, campo2 } // NUNCA logue senhas ou tokens
})
```

---

## 5. Integracao com Servicos Externos

### Padrao de inicializacao segura

```typescript
// ERRADO — crash se variavel ausente
const stripe = new Stripe(process.env.STRIPE_KEY!)

// CERTO — inicializacao on-demand dentro da funcao
function getStripe() {
  if (!process.env.STRIPE_KEY) {
    throw new Error('STRIPE_KEY nao configurada')
  }
  return new Stripe(process.env.STRIPE_KEY)
}

export async function POST(request: Request) {
  const stripe = getStripe()
  // usar stripe aqui
}
```

### Timeout + Retry

```typescript
async function chamarServicoExterno(url: string, tentativas = 3) {
  for (let i = 0; i < tentativas; i++) {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000) // 5s

      const response = await fetch(url, { signal: controller.signal })
      clearTimeout(timeout)

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    } catch (error) {
      if (i === tentativas - 1) throw error
      // Backoff exponencial: 1s, 2s, 4s
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000))
    }
  }
}
```

### Graceful degradation

Quando servico externo falha, o sistema DEVE continuar funcionando com funcionalidade parcial:

```typescript
// Exemplo: envio de email falha, mas pedido e criado
try {
  await enviarEmailConfirmacao(pedido)
} catch (error) {
  console.error('[Email] Falha ao enviar confirmacao', error)
  // NAO retorne erro 500 — o pedido foi criado com sucesso
  // Registre para reenvio posterior
  await supabase.from('email_queue').insert({
    tipo: 'confirmacao_pedido',
    pedido_id: pedido.id,
    tentativas: 0
  })
}
```

---

## 6. Revisao de Codigo Backend

### O que verificar ao revisar rotas do ENGINE

- [ ] Toda rota verifica sessao antes de retornar dados?
- [ ] Queries filtram por `user_id` (nao retorna dados de outros usuarios)?
- [ ] Todos os campos string tem `.max()` na validacao?
- [ ] Paginacao implementada (nao retorna tudo)?
- [ ] Erros retornam status HTTP correto (nao tudo 500)?
- [ ] Servicos externos inicializados dentro da funcao?
- [ ] Sem N+1 (usa joins em vez de loops)?

### O que verificar ao revisar queries do VAULT

- [ ] Indices existem para campos em WHERE/ORDER BY?
- [ ] RLS ativado na tabela com policies corretas?
- [ ] Foreign keys tem ON DELETE definido?
- [ ] Campos NOT NULL tem DEFAULT ou sao obrigatorios na validacao?
- [ ] Migrations estao na ordem correta (dependencias primeiro)?
- [ ] Seeds nao contem dados sensiveis?

### O que verificar em performance

- [ ] Response time aceitavel (<500ms para operacoes simples)?
- [ ] Payload nao retorna dados desnecessarios (use .select('campo1, campo2'))?
- [ ] Queries complexas usam indices compostos?
- [ ] Cache aplicado onde faz sentido (tabela na secao 2)?

---

## 7. Checklist de Qualidade Backend

### Antes de marcar tarefa como concluida

- [ ] Rota segue o contrato definido no `project-core.md`?
- [ ] Todos os campos do contrato estao implementados (entrada E saida)?
- [ ] Todos os cenarios de erro listados no contrato retornam o status correto?
- [ ] Build Validator passou sem blockers?
- [ ] Contract Tester verificou conformidade com `project-core.md`?

### Antes de aprovar tarefa do ENGINE ou VAULT

- [ ] Codigo segue os padroes desta base de conhecimento?
- [ ] Nao ha queries N+1?
- [ ] Autenticacao e verificada em toda rota protegida?
- [ ] Servicos externos usam timeout + retry?
- [ ] Erros sao logados com contexto suficiente?
- [ ] Nenhum dado sensivel exposto em logs ou respostas?

---

## 8. Erros Comuns de Backend

### Esquecer de verificar sessao em rota de API

**Errado:** Rota retorna dados sem verificar autenticacao.
**Certo:** Toda rota protegida comeca com `getSession()` e retorna 401 se ausente.

### Confiar no cliente para validacao

**Errado:** Frontend valida, backend aceita sem re-validar.
**Certo:** Validacao SEMPRE duplicada no servidor (Zod schema compartilhado ajuda).

### Inicializar servico externo no topo do modulo

**Errado:** `const stripe = new Stripe(process.env.STRIPE_KEY!)` — crash no import se variavel ausente.
**Certo:** Funcao `getStripe()` que valida e retorna instancia on-demand.

### Retornar todos os campos do banco na resposta

**Errado:** `supabase.from('users').select('*')` — inclui campos internos.
**Certo:** `supabase.from('users').select('id, name, email, avatar_url')` — so o necessario.

### Ignorar o contrato ao implementar

**Errado:** Implementar rota "do jeito que faz sentido" sem consultar `project-core.md`.
**Certo:** Abrir `project-core.md`, ler o contrato da rota, implementar EXATAMENTE o que esta definido.
