# Next.js API Patterns — Referencia ENGINE (base oficial)

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Rota ≤ 150 linhas · lógica de negócio em src/lib/ · nomes de campos JSON em inglês, mensagens ao usuário em português.
>
> **v6.3 (2026-10-14):** esta base é a FONTE ÚNICA do formato de erro de API (seção 3, D13). Validação falhou ou
> campo faltando = **400** (nunca 422). Tempos-limite e novas tentativas seguem a tabela única de
> `protocolos/regras-codigo.md` (D19). Rate limit com armazenamento compartilhado (nunca `Map` em memória).

Base de conhecimento pratica para implementacao de rotas API no App Router.

---

## 1. Estrutura de Rotas (App Router)

Cada rota e um arquivo `route.ts` dentro de `src/app/api/`:

```
src/app/api/
  users/
    route.ts          → GET /api/users, POST /api/users
    [id]/
      route.ts        → GET /api/users/:id, PATCH, DELETE
  auth/
    login/
      route.ts        → POST /api/auth/login
```

Metodos exportados = verbos HTTP aceitos. Metodo nao exportado = 405 automatico.

```ts
// src/app/api/users/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  return NextResponse.json({ users: [] });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return NextResponse.json({ created: true }, { status: 201 });
}
```

Rotas dinamicas recebem params como segundo argumento (no Next.js 15, `params` e uma Promise):

```ts
// src/app/api/users/[id]/route.ts
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return NextResponse.json({ id });
}
```

---

## 2. Request/Response

```ts
// Ler query params
const url = new URL(request.url);
const page = Number(url.searchParams.get("page") ?? "1");

// Ler body JSON
const body = await request.json();

// Ler headers
const authorizationHeader = request.headers.get("authorization");

// Resposta com status e headers customizados
return NextResponse.json(
  { data: result },
  {
    status: 200,
    headers: { "X-Total-Count": String(total) },
  }
);
```

---

## 3. Formato único de erro (D13 — fonte única do sistema)

Todas as rotas DEVEM retornar erros neste formato (o mesmo do `templates/contratos-api-template.md` e o que o
`contract-tester` confere):

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "texto para humano", "details": [] } }
```

```ts
// src/lib/api/error-response.ts
import { NextResponse } from "next/server";

type ErrorCode =
  | "VALIDATION_ERROR" | "UNAUTHORIZED" | "FORBIDDEN" | "NOT_FOUND"
  | "CONFLICT" | "RATE_LIMITED" | "INTERNAL_ERROR";

const STATUS_BY_CODE: Record<ErrorCode, number> = {
  VALIDATION_ERROR: 400, UNAUTHORIZED: 401, FORBIDDEN: 403, NOT_FOUND: 404,
  CONFLICT: 409, RATE_LIMITED: 429, INTERNAL_ERROR: 500,
};

export function errorResponse(code: ErrorCode, message: string, details: unknown[] = []) {
  return NextResponse.json(
    { error: { code, message, details } },
    { status: STATUS_BY_CODE[code] }
  );
}
```

Codigos HTTP usados:

| Codigo | `error.code` | Quando usar |
|--------|-------------|-------------|
| 400 | `VALIDATION_ERROR` | Body invalido, campo obrigatorio faltando, formato errado, Zod falhou |
| 401 | `UNAUTHORIZED` | Token ausente ou expirado |
| 403 | `FORBIDDEN` | Token valido mas sem permissao para o recurso |
| 404 | `NOT_FOUND` | Recurso nao encontrado |
| 409 | `CONFLICT` | Conflito (ex: email ja cadastrado) |
| 429 | `RATE_LIMITED` | Rate limit excedido |
| 500 | `INTERNAL_ERROR` | Erro interno inesperado (sem stack trace na resposta) |

**Nao use 422.** Validacao do Zod tambem e 400 — um codigo so para "a entrada esta errada" evita que testes de
contrato e implementacao discordem.

---

## 4. Autenticacao (`@supabase/ssr` + `getUser()`)

```ts
import { NextRequest } from "next/server";
import { createSupabaseClient } from "@/lib/supabase/server";
import { errorResponse } from "@/lib/api/error-response";

async function verifyAuthentication(request: NextRequest) {
  const supabase = await createSupabaseClient();

  // getUser() confere o token com o Supabase. NUNCA use getSession() no servidor:
  // ele so le o cookie e confia nele sem conferir.
  const { data: { user }, error } = await supabase.auth.getUser();

  if (error || !user) {
    return { user: null, supabase, failure: errorResponse("UNAUTHORIZED", "Nao autenticado") };
  }

  return { user, supabase, failure: null };
}

// Uso em qualquer rota:
export async function GET(request: NextRequest) {
  const { user, supabase, failure } = await verifyAuthentication(request);
  if (failure) return failure;

  // user.id disponivel, supabase com contexto do usuario (RLS ativo)
}
```

---

## 5. Validacao de Input (Zod)

```ts
import { z } from "zod";

const createUserSchema = z.object({
  name: z.string().trim().min(2).max(100),
  email: z.string().trim().toLowerCase().email().max(254),
  role: z.enum(["admin", "member"]).default("member"),
});

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return errorResponse("VALIDATION_ERROR", "Body nao e JSON valido");
  }

  const parsed = createUserSchema.safeParse(body);
  if (!parsed.success) {
    const details = parsed.error.issues.map((issue) => ({
      field: issue.path.join("."),
      message: issue.message,
    }));
    return errorResponse("VALIDATION_ERROR", "Dados invalidos", details);
  }

  const input = parsed.data; // tipado automaticamente
  // ... criar usuario com input.name, input.email, input.role
}
```

---

## 6. Rate Limiting (armazenamento compartilhado)

Em servidor serverless (Vercel) cada requisicao pode cair numa instancia nova: contador em memoria (`new Map()`)
zera e o limite NAO funciona em producao. Use um armazenamento compartilhado — padrao do sistema:
`@upstash/ratelimit` + `@upstash/redis` (registrar em `memoria/ferramentas-do-projeto.md` antes de instalar —
Regra 14).

```ts
// src/lib/api/rate-limit.ts
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { NextRequest, NextResponse } from "next/server";
import { errorResponse } from "@/lib/api/error-response";

let loginRateLimit: Ratelimit | null = null;

function getLoginRateLimit() {
  // inicializacao sob demanda (nunca no topo do modulo)
  loginRateLimit ??= new Ratelimit({
    redis: Redis.fromEnv(), // UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN
    limiter: Ratelimit.slidingWindow(10, "60 s"), // 10 req/min
    prefix: "rate-limit:login",
  });
  return loginRateLimit;
}

export async function checkLoginRateLimit(request: NextRequest): Promise<NextResponse | null> {
  const clientIp = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  const { success } = await getLoginRateLimit().limit(clientIp);
  return success ? null : errorResponse("RATE_LIMITED", "Muitas requisicoes. Tente novamente em breve.");
}

// Uso:
export async function POST(request: NextRequest) {
  const blocked = await checkLoginRateLimit(request);
  if (blocked) return blocked;
  // ... continuar
}
```

---

## 7. Integracao Supabase

### Cliente com contexto do usuario (RLS ativo)

Usar `createServerClient` de `@supabase/ssr` com cookies — respeita Row Level Security. (O pacote
`@supabase/auth-helpers-nextjs` e legado: nao usar.)

```ts
// src/lib/supabase/server.ts
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createSupabaseClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        },
      },
    }
  );
}
```

### Cliente admin (service role — ignora RLS)

Usar APENAS para operacoes administrativas (criar usuario, limpar dados, jobs):

```ts
// src/lib/supabase/admin.ts
import { createClient } from "@supabase/supabase-js";

export function createAdminClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}
```

NUNCA expor service role no frontend. NUNCA usar service role para operacoes do usuario.

---

## 8. Servicos Externos (APIs de terceiros)

- **Inicializacao sob demanda** (ex.: `getStripe()`): o padrao e a fonte unica estao em
  `backend-integracao-patterns.md`, seção "Inicializacao sob demanda".
- **Tempos-limite e novas tentativas:** valores da tabela unica em `protocolos/regras-codigo.md` (D19) — API externa
  10 s, banco 5 s, chamada interna 3 s, 3 novas tentativas com espera crescente, circuit breaker abre apos 5 falhas e
  fecha apos 60 s.

```ts
// src/lib/http/fetch-with-timeout.ts
const EXTERNAL_API_TIMEOUT_MS = 10_000; // D19

export async function fetchWithTimeout(url: string, options?: RequestInit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), EXTERNAL_API_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

const MAX_RETRIES = 3; // D19: 3 novas tentativas depois da primeira

export async function fetchWithRetry(url: string, options?: RequestInit) {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options);
      if (response.ok || response.status < 500) return response;
    } catch (error) {
      if (attempt === MAX_RETRIES) throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, 2 ** attempt * 1000)); // 1 s, 2 s, 4 s
  }
  throw new Error(`Falha apos ${MAX_RETRIES} novas tentativas: ${url}`);
}
```

---

## 9. Erros Comuns a Evitar

| Erro | Correto |
|------|---------|
| `export default function handler` | Exportar funcoes nomeadas: `export async function GET` |
| Nao tratar `await request.json()` com try/catch | Sempre envolver em try/catch — body pode ser invalido |
| Retornar `new Response(JSON.stringify(x))` | Usar `NextResponse.json(x)` — mais limpo e seta Content-Type |
| Usar `process.env.X` sem `!` ou checagem | Validar variaveis no startup ou usar assertion |
| Fazer `console.log(error)` e retornar 200 | Retornar o status HTTP correto (4xx/5xx) no formato unico de erro |
| Responder 422 para Zod | 400 `VALIDATION_ERROR` (D13) |
| `getSession()` no servidor | `getUser()` |
| Rate limit em `new Map()` | `@upstash/ratelimit` |
| Inicializar SDK externo no topo do modulo | Inicializar dentro da funcao ou com factory |
| Usar service role para queries do usuario | Usar cliente com cookies (RLS ativo) |
| Esquecer de `await params` em rotas dinamicas | Params e Promise no App Router — sempre await |
| Nao validar input antes de usar | Sempre validar com Zod antes de processar |
| Capturar erro generico e esconder detalhes | Logar o erro real no servidor, retornar mensagem segura ao cliente |
