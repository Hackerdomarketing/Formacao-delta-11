# Base de Conhecimento: Backend e Integracao — BACK

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Rota ≤ 150 linhas · lógica de negócio extraída para src/lib/ · ao revisar ENGINE/VAULT, violação de limite = reprovação.


Referencia pratica para lideranca tecnica de servidor em projetos web.
Foco: Next.js API Routes + Supabase. Otimizacao, autenticacao, integracao.

> **v6.3 (2026-10-14):** login conferido no servidor com `@supabase/ssr` + `getUser()` (o pacote
> `@supabase/auth-helpers-nextjs` e `getSession()` no servidor estao proibidos). Formato de erro: o unico do sistema
> (D13), definido em `nextjs-api-patterns.md` seção 3. Tempos-limite: tabela unica de `protocolos/regras-codigo.md`
> (D19). Esta base e a FONTE UNICA de: N+1 (seção 2) e inicializacao sob demanda / `getStripe` (seção 5).

---

## 1. Arquitetura de Rotas Modulares

### Estrutura padrao de API Route (Next.js App Router)

```typescript
// src/app/api/orders/route.ts

import { NextResponse } from 'next/server'
import { createSupabaseClient } from '@/lib/supabase/server' // @supabase/ssr (ver nextjs-api-patterns.md seção 7)
import { errorResponse } from '@/lib/api/error-response'      // formato unico D13

export async function GET(request: Request) {
  const supabase = await createSupabaseClient()

  // 1. Autenticacao — getUser() confere o token com o Supabase (NUNCA getSession() no servidor)
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return errorResponse('UNAUTHORIZED', 'Nao autenticado')
  }

  // 2. Validacao de entrada
  const { searchParams } = new URL(request.url)
  const page = Math.max(1, parseInt(searchParams.get('page') || '1'))

  // 3. Query ao banco (sempre filtrar por user_id)
  const { data, error } = await supabase
    .from('orders')
    .select('id, status, total_cents, created_at')
    .eq('user_id', user.id)
    .range((page - 1) * 20, page * 20 - 1)

  // 4. Tratamento de erro
  if (error) {
    console.error('[API /orders GET]', error.message)
    return errorResponse('INTERNAL_ERROR', 'Erro interno')
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

### N+1 — O problema mais comum (fonte unica desta licao)

**O que e:** Para cada item de uma lista, fazer uma query extra ao banco.

```typescript
// ERRADO — N+1: 1 query para pedidos + N queries para itens
const orders = await supabase.from('orders').select('*')
for (const order of orders.data ?? []) {
  const items = await supabase.from('order_items').select('*').eq('order_id', order.id)
}

// CERTO — 1 query com join
const ordersWithItems = await supabase
  .from('orders')
  .select('*, order_items(*)')
  .eq('user_id', user.id)
```

### Indices

Todo campo usado em WHERE, ORDER BY ou JOIN DEVE ter indice:

```sql
-- Campos obrigatorios para indice
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Indice composto para queries frequentes
CREATE INDEX idx_orders_user_id_status ON orders(user_id, status);
```

### Paginacao

NUNCA retorne todos os registros. Sempre pagine:

```typescript
// Padrao: 20 itens por pagina
const PAGE_SIZE = 20
const from = (page - 1) * PAGE_SIZE
const to = from + PAGE_SIZE - 1

const { data, count } = await supabase
  .from('orders')
  .select('id, status, created_at', { count: 'exact' })
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
2. Sessao: cookie httpOnly gerenciado pelo @supabase/ssr (createServerClient / createBrowserClient)
3. Verificacao: getUser() no servidor em toda rota protegida (getSession() so no navegador, para estado de tela)
4. Refresh: automatico pelo Supabase (access token expira em 1h)
5. Logout: supabase.auth.signOut()
```

### Middleware de protecao (Next.js)

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request })
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options))
        },
      },
    }
  )

  // getUser() confere o token com o Supabase e renova o cookie se preciso
  const { data: { user } } = await supabase.auth.getUser()

  // Rotas protegidas
  if (request.nextUrl.pathname.startsWith('/app') && !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Rotas de admin
  if (request.nextUrl.pathname.startsWith('/admin')) {
    if (!user) return NextResponse.redirect(new URL('/login', request.url))
    // Verificar role (coluna na tabela profiles)
    const { data: profile } = await supabase
      .from('profiles')
      .select('role')
      .eq('id', user.id)
      .single()
    if (profile?.role !== 'admin') {
      return NextResponse.redirect(new URL('/app', request.url))
    }
  }

  return response
}

export const config = {
  matcher: ['/app/:path*', '/admin/:path*']
}
```

Middleware NAO e a unica defesa (CVE-2025-29927): toda rota e todo layout protegido confere `getUser()` de novo.

### Regras inviolaveis de autenticacao

- TODA rota de API que retorna dados do usuario confere o usuario com `getUser()` no servidor
- NUNCA confie em dados do cliente para autorizar (sempre re-verificar no servidor)
- Tokens e chaves NUNCA no frontend (`NEXT_PUBLIC_` so para dados publicos)
- RLS no Supabase e a segunda camada — middleware e a primeira

---

## 4. Tratamento de Erros HTTP

### Tabela de status codes

| Status | `error.code` | Quando usar |
|--------|-------------|------------|
| 200 | — | Sucesso em leitura: `{ data: [...] }` |
| 201 | — | Sucesso em criacao: `{ data: { id: "..." } }` |
| 400 | `VALIDATION_ERROR` | Entrada invalida, campo faltando, valor fora do permitido (inclui o que antes era 422) |
| 401 | `UNAUTHORIZED` | Nao autenticado |
| 403 | `FORBIDDEN` | Sem permissao |
| 404 | `NOT_FOUND` | Nao encontrado |
| 409 | `CONFLICT` | Conflito (ex: email ja cadastrado) |
| 429 | `RATE_LIMITED` | Limite de requisicoes |
| 500 | `INTERNAL_ERROR` | Erro interno |

### Formato de resposta (unico do sistema — D13)

```typescript
// Sucesso
{ data: { ... } }

// Erro (qualquer status 4xx/5xx)
{ error: { code: "VALIDATION_ERROR", message: "mensagem legivel para o usuario", details: [{ field: "email", message: "formato invalido" }] } }
```

A funcao `errorResponse(code, message, details)` esta em `nextjs-api-patterns.md` seção 3 — use a mesma.

### Logging de erros

```typescript
// Sempre logue com contexto suficiente para diagnostico
console.error(`[API /orders ${method}]`, {
  error: error.message,
  userId: user?.id,
  input: { status, page } // NUNCA logue senhas ou tokens
})
```

---

## 5. Integracao com Servicos Externos

### Inicializacao sob demanda (fonte unica do padrao `getStripe`)

```typescript
// ERRADO — executa no import; crash se a variavel estiver ausente, mesmo em rotas que nao usam Stripe
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// CERTO — inicializacao sob demanda dentro da funcao, com cache da instancia
// (o mesmo codigo aparece em design-patterns-praticos.md como exemplo de Factory)
let stripeInstance: Stripe | null = null

function getStripe(): Stripe {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error('Configuracao de pagamento ausente')
  }
  stripeInstance ??= new Stripe(process.env.STRIPE_SECRET_KEY)
  return stripeInstance
}

export async function POST(request: Request) {
  const stripe = getStripe()
  // usar stripe aqui
}
```

### Timeout + Retry

Valores da tabela unica de `protocolos/regras-codigo.md` (D19): API externa 10 s, banco 5 s, chamada interna 3 s,
3 novas tentativas com espera crescente (1 s, 2 s, 4 s), circuit breaker abre apos 5 falhas e fecha apos 60 s.
Codigo pronto: `fetchWithTimeout` / `fetchWithRetry` em `nextjs-api-patterns.md` seção 8 — nao copie outra versao.

### Graceful degradation

Quando servico externo falha, o sistema DEVE continuar funcionando com funcionalidade parcial:

```typescript
// Exemplo: envio de email falha, mas pedido e criado
try {
  await sendOrderConfirmationEmail(order)
} catch (error) {
  console.error('[Email] Falha ao enviar confirmacao', error)
  // NAO retorne erro 500 — o pedido foi criado com sucesso
  // Registre para reenvio posterior
  await supabase.from('email_queue').insert({
    kind: 'order_confirmation',
    order_id: order.id,
    attempts: 0
  })
}
```

---

## 6. Revisao de Codigo Backend

### O que verificar ao revisar rotas do ENGINE

- [ ] Toda rota confere o usuario com `getUser()` antes de retornar dados (nenhum `getSession()` no servidor, nenhum `@supabase/auth-helpers-nextjs`)?
- [ ] Queries filtram por `user_id` (nao retorna dados de outros usuarios)?
- [ ] Todos os campos string tem `.max()` na validacao?
- [ ] Paginacao implementada (nao retorna tudo)?
- [ ] Erros retornam status HTTP correto (nao tudo 500) no formato unico `{ error: { code, message, details } }`?
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

- [ ] Rota segue o contrato da fatia `memoria/project-core/contratos.md`?
- [ ] Todos os campos do contrato estao implementados (entrada E saida)?
- [ ] Todos os cenarios de erro listados no contrato retornam o status correto?
- [ ] Build Validator passou sem blockers?
- [ ] Contract Tester gerou E rodou os testes de contrato das rotas tocadas, com PASS (Passo 3.7)?

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
**Certo:** Toda rota protegida comeca com `getUser()` e retorna 401 (`UNAUTHORIZED`) se nao houver usuario.

### Confiar no cliente para validacao

**Errado:** Frontend valida, backend aceita sem re-validar.
**Certo:** Validacao SEMPRE duplicada no servidor (Zod schema compartilhado ajuda).

### Inicializar servico externo no topo do modulo

**Errado:** `const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)` — crash no import se variavel ausente.
**Certo:** Funcao `getStripe()` que valida e retorna instancia on-demand.

### Retornar todos os campos do banco na resposta

**Errado:** `supabase.from('users').select('*')` — inclui campos internos.
**Certo:** `supabase.from('users').select('id, name, email, avatar_url')` — so o necessario.

### Ignorar o contrato ao implementar

**Errado:** Implementar rota "do jeito que faz sentido" sem consultar `project-core.md`.
**Certo:** Abrir a fatia `memoria/project-core/contratos.md` (executores nao leem o project-core inteiro — D6), ler o contrato da rota, implementar EXATAMENTE o que esta definido. Divergencia → `PROPOSTAS PARA O PROJECT-CORE` no seu `-produto.md`.
