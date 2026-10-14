# React Component Patterns — Base de Conhecimento FRONT

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Componente ≤ 150 linhas e ≤ 5 props · 1 componente exportado por arquivo · ao revisar PIXEL/FORM, violação de limite = reprovação.


Referencia pratica para o agente FRONT da Formacao Delta-11 (base OFICIAL do FRONT — `perfis/FRONT.json`; complemento: `react-next-overview.md`). v6.3: identificadores dos exemplos em ingles (regra §9).
Foco: Next.js App Router, composicao de componentes, estado, navegacao.

---

## 1. Server Components vs Client Components

```tsx
// SERVER COMPONENT (padrao no App Router — roda no servidor)
// Pode acessar banco, filesystem, secrets. NAO usa hooks.
async function ProductList() {
  const products = await fetchProducts() // acesso direto ao banco
  return (
    <ul>
      {products.map(product => <li key={product.id}>{product.name}</li>)}
    </ul>
  )
}

// CLIENT COMPONENT — precisa do "use client" no topo
// Pode usar hooks (useState, useEffect, etc), eventos, browser APIs
"use client"
import { useState } from "react"

function ItemCounter() {
  const [count, setCount] = useState(0)
  return (
    <button onClick={() => setCount(previousCount => previousCount + 1)}>
      {count} itens
    </button>
  )
}
```

**Regra:** Use Server Components por padrao. So adicione `"use client"` quando precisar de interatividade (hooks, eventos de click, estado local).

---

## 2. State Management

### React Context (estado global simples)

```tsx
// user-context.tsx
"use client"
import { createContext, useContext, useState, ReactNode } from "react"

type User = { name: string; email: string } | null

const UserContext = createContext<{
  user: User
  setUser: (nextUser: User) => void
}>({ user: null, setUser: () => {} })

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null)
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
```

### Zustand (estado global com mais controle)

```tsx
import { create } from "zustand"

type CartState = {
  items: Array<{ id: string; name: string; price: number }>
  addItem: (item: { id: string; name: string; price: number }) => void
  removeItem: (id: string) => void
  getItemCount: () => number
}

export const useCart = create<CartState>((set, get) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  removeItem: (id) => set((state) => ({ items: state.items.filter(item => item.id !== id) })),
  getItemCount: () => get().items.length,
}))
```

### URL State (estado via query params — sobrevive a refresh)

```tsx
"use client"
import { useSearchParams, useRouter, usePathname } from "next/navigation"

function SearchFilters() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const currentFilter = searchParams.get("category") || "all"

  function applyFilter(category: string) {
    const nextSearchParams = new URLSearchParams(searchParams)
    nextSearchParams.set("category", category)
    router.push(`${pathname}?${nextSearchParams.toString()}`)
  }

  return (
    <select value={currentFilter} onChange={(event) => applyFilter(event.target.value)}>
      <option value="all">Todos</option>
      <option value="electronics">Eletronicos</option>
      <option value="clothing">Roupas</option>
    </select>
  )
}
```

---

## 3. Layout Patterns

### Nested Layouts (layouts que envolvem paginas)

```
src/app/layout.tsx              → Layout raiz (HTML, body, providers)
src/app/(app)/layout.tsx        → Layout da area logada (sidebar, navbar)
src/app/(app)/dashboard/page.tsx   → Pagina do dashboard (herda ambos layouts)
src/app/(admin)/layout.tsx      → Layout do admin (diferente do app)
```

```tsx
// src/app/(app)/layout.tsx
export default function AuthenticatedAreaLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
```

### Shared Layout com Route Groups

```
src/app/(marketing)/          → Paginas publicas (home, sobre, precos)
src/app/(app)/                → Area logada
src/app/(admin)/              → Area administrativa
```

Route groups `(nome)` NAO afetam a URL. Servem apenas para organizar layouts.

---

## 4. Navigation

```tsx
// Link estatico
import Link from "next/link"
<Link href="/products">Ver Produtos</Link>

// Link dinamico
<Link href={`/products/${product.id}`}>Detalhes</Link>

// Navegacao programatica (client component)
"use client"
import { useRouter } from "next/navigation"

function LogoutButton() {
  const router = useRouter()
  async function handleSignOut() {
    await signOut()
    router.push("/login")
  }
  return <button onClick={handleSignOut}>Sair</button>
}

// Redirect no servidor (server component ou middleware)
import { redirect } from "next/navigation"

async function ProtectedPage() {
  const supabase = await createSupabaseClient() // @supabase/ssr — ver nextjs-api-patterns.md seção 7
  const { data: { user } } = await supabase.auth.getUser() // getUser(), nunca getSession() no servidor
  if (!user) redirect("/login")
  return <div>Conteudo protegido</div>
}
```

---

## 5. Loading e Error Boundaries

```
src/app/(app)/dashboard/
├── page.tsx          → Conteudo da pagina
├── loading.tsx       → Mostrado enquanto page.tsx carrega
└── error.tsx         → Mostrado se page.tsx da erro
```

```tsx
// loading.tsx — skeleton automatico
export default function Loading() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/3" />
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-2/3" />
    </div>
  )
}

// error.tsx — DEVE ser client component
"use client"
export default function ErrorBoundaryPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="text-center p-8">
      <h2 className="text-xl font-bold text-red-600">Algo deu errado</h2>
      <p className="mt-2 text-gray-600">{error.message}</p>
      <button onClick={reset} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        Tentar novamente
      </button>
    </div>
  )
}
```

---

## 6. Data Fetching

### Server Component (recomendado — sem estado de loading manual)

```tsx
async function ProductsPage() {
  const products = await fetch("https://api.example.com/products", {
    next: { revalidate: 60 }, // revalida cache a cada 60 segundos
  }).then(response => response.json())

  return <ProductList products={products} />
}
```

### SWR (client-side com cache e revalidacao)

```tsx
"use client"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then(response => response.json())

function NotificationsPanel() {
  const { data, error, isLoading } = useSWR("/api/notifications", fetcher, {
    refreshInterval: 30000, // atualiza a cada 30 segundos
  })

  if (isLoading) return <Skeleton />
  if (error) return <ErrorMessage />
  return <List items={data} />
}
```

---

## 7. Component Composition

### Compound Components (componentes que trabalham juntos)

```tsx
function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border p-4 shadow-sm">{children}</div>
}

Card.Header = function Header({ children }: { children: React.ReactNode }) {
  return <div className="border-b pb-2 mb-3 font-semibold">{children}</div>
}

Card.Body = function Body({ children }: { children: React.ReactNode }) {
  return <div className="text-gray-600">{children}</div>
}

// Uso:
<Card>
  <Card.Header>Titulo do Card</Card.Header>
  <Card.Body>Conteudo aqui dentro</Card.Body>
</Card>
```

### Render Props / Children as Function

```tsx
function SearchableList<T extends { id: string }>({
  items,
  searchField,
  renderItem,
}: {
  items: T[]
  searchField: keyof T
  renderItem: (item: T) => React.ReactNode
}) {
  const [query, setQuery] = useState("")
  const filteredItems = items.filter(item =>
    String(item[searchField]).toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Buscar..."
        className="w-full p-2 border rounded mb-4"
      />
      <div className="space-y-2">{filteredItems.map(renderItem)}</div>
    </div>
  )
}
```
