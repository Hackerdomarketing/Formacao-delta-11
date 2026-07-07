# Next.js API Patterns — Referencia ENGINE

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Rota ≤ 150 linhas · lógica de negócio em src/lib/ · nomes de campos JSON em inglês, mensagens ao usuário em português.


Base de conhecimento pratica para implementacao de rotas API no App Router.

---

## 1. Estrutura de Rotas (App Router)

Cada rota e um arquivo `route.ts` dentro de `src/app/api/`:

```
src/app/api/
  usuarios/
    route.ts          → GET /api/usuarios, POST /api/usuarios
    [id]/
      route.ts        → GET /api/usuarios/:id, PATCH, DELETE
  auth/
    login/
      route.ts        → POST /api/auth/login
```

Metodos exportados = verbos HTTP aceitos. Metodo nao exportado = 405 automatico.

```ts
// src/app/api/usuarios/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  return NextResponse.json({ usuarios: [] });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return NextResponse.json({ criado: true }, { status: 201 });
}
```

Rotas dinamicas recebem params como segundo argumento:

```ts
// src/app/api/usuarios/[id]/route.ts
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
const pagina = Number(url.searchParams.get("pagina") ?? "1");

// Ler body JSON
const body = await request.json();

// Ler headers
const token = request.headers.get("authorization");

// Resposta com status e headers customizados
return NextResponse.json(
  { dados: resultado },
  {
    status: 200,
    headers: { "X-Total-Count": String(total) },
  }
);
```

---

## 3. Formato Padrao de Erro

Todas as rotas DEVEM retornar erros neste formato (definido no project-core.md):

```ts
function errorResponse(status: number, mensagem: string, detalhes?: unknown) {
  return NextResponse.json(
    { erro: true, mensagem, detalhes: detalhes ?? null },
    { status }
  );
}
```

Codigos HTTP mais usados:

| Codigo | Quando usar |
|--------|-------------|
| 400 | Body invalido, campo obrigatorio faltando, formato errado |
| 401 | Token ausente ou expirado |
| 403 | Token valido mas sem permissao para o recurso |
| 404 | Recurso nao encontrado |
| 409 | Conflito (ex: email ja cadastrado) |
| 422 | Validacao falhou (Zod errors) |
| 429 | Rate limit excedido |
| 500 | Erro interno inesperado |

---

## 4. Autenticacao (JWT / Session)

```ts
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

async function verifyAuthentication(request: NextRequest) {
  const cookieStore = await cookies();
  const supabase = createServerClient(
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

  const { data: { user }, error } = await supabase.auth.getUser();

  if (error || !user) {
    return { usuario: null, supabase, erro: errorResponse(401, "Nao autenticado") };
  }

  return { usuario: user, supabase, erro: null };
}

// Uso em qualquer rota:
export async function GET(request: NextRequest) {
  const { usuario, supabase, erro } = await verifyAuthentication(request);
  if (erro) return erro;

  // usuario.id disponivel, supabase com contexto do usuario (RLS ativo)
}
```

---

## 5. Validacao de Input (Zod)

```ts
import { z } from "zod";

const esquemaCriarUsuario = z.object({
  nome: z.string().min(2).max(100),
  email: z.string().email(),
  papel: z.enum(["admin", "membro"]).default("membro"),
});

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return errorResponse(400, "Body nao e JSON valido");
  }

  const resultado = esquemaCriarUsuario.safeParse(body);
  if (!resultado.success) {
    return errorResponse(422, "Validacao falhou", resultado.error.flatten());
  }

  const dados = resultado.data; // tipado automaticamente
  // ... criar usuario com dados.nome, dados.email, dados.papel
}
```

---

## 6. Rate Limiting

Implementacao simples com Map em memoria (suficiente para projetos pequenos/medios):

```ts
const contadorPorIP = new Map<string, { contagem: number; expira: number }>();

function checkRateLimit(
  request: NextRequest,
  limite: number = 60,
  janelaSegundos: number = 60
): NextResponse | null {
  const ip = request.headers.get("x-forwarded-for") ?? "desconhecido";
  const agora = Date.now();
  const registro = contadorPorIP.get(ip);

  if (!registro || agora > registro.expira) {
    contadorPorIP.set(ip, { contagem: 1, expira: agora + janelaSegundos * 1000 });
    return null;
  }

  registro.contagem++;
  if (registro.contagem > limite) {
    return errorResponse(429, "Muitas requisicoes. Tente novamente em breve.");
  }

  return null;
}

// Uso:
export async function POST(request: NextRequest) {
  const bloqueio = checkRateLimit(request, 10, 60); // 10 req/min
  if (bloqueio) return bloqueio;
  // ... continuar
}
```

---

## 7. Integracao Supabase

### Cliente com contexto do usuario (RLS ativo)

Usar `createServerClient` com cookies — respeita Row Level Security:

```ts
// src/lib/supabase/servidor.ts
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

Usar APENAS para operacoes administrativas (criar usuario, limpar dados, migracoes):

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

### Inicializacao sob demanda (NUNCA no topo do modulo)

```ts
// ERRADO — executa na importacao, mesmo em rotas que nao usam
const stripe = new Stripe(process.env.STRIPE_KEY!);

// CERTO — inicializa apenas quando a rota e chamada
function getStripe() {
  return new Stripe(process.env.STRIPE_KEY!);
}
```

### Timeout padrao de 5 segundos

```ts
async function fetchExternal(url: string, opcoes?: RequestInit) {
  const controlador = new AbortController();
  const timeout = setTimeout(() => controlador.abort(), 5000);

  try {
    const resposta = await fetch(url, {
      ...opcoes,
      signal: controlador.signal,
    });
    return resposta;
  } finally {
    clearTimeout(timeout);
  }
}
```

### Retry com backoff (maximo 3 tentativas)

```ts
async function fetchWithRetry(url: string, opcoes?: RequestInit, maxTentativas = 3) {
  for (let tentativa = 0; tentativa < maxTentativas; tentativa++) {
    try {
      const resposta = await fetchExternal(url, opcoes);
      if (resposta.ok || resposta.status < 500) return resposta;
    } catch (erro) {
      if (tentativa === maxTentativas - 1) throw erro;
    }
    await new Promise((r) => setTimeout(r, Math.pow(2, tentativa) * 1000));
  }
  throw new Error(`Falha apos ${maxTentativas} tentativas: ${url}`);
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
| Fazer `console.log(erro)` e retornar 200 | Retornar o status HTTP correto (4xx/5xx) |
| Inicializar SDK externo no topo do modulo | Inicializar dentro da funcao ou com factory |
| Usar service role para queries do usuario | Usar cliente com cookies (RLS ativo) |
| Esquecer de `await params` em rotas dinamicas | Params e Promise no App Router — sempre await |
| Nao validar input antes de usar | Sempre validar com Zod antes de processar |
| Capturar erro generico e esconder detalhes | Logar o erro real no servidor, retornar mensagem segura ao cliente |
