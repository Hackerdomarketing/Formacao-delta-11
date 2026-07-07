# React Component Patterns — Base de Conhecimento FRONT

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Componente ≤ 150 linhas e ≤ 5 props · 1 componente exportado por arquivo · ao revisar PIXEL/FORM, violação de limite = reprovação.


Referencia pratica para o agente FRONT da Formacao Delta-11.
Foco: Next.js App Router, composicao de componentes, estado, navegacao.

---

## 1. Server Components vs Client Components

```tsx
// SERVER COMPONENT (padrao no App Router — roda no servidor)
// Pode acessar banco, filesystem, secrets. NAO usa hooks.
async function ListaDeProdutos() {
  const produtos = await buscarProdutos() // acesso direto ao banco
  return (
    <ul>
      {produtos.map(p => <li key={p.id}>{p.nome}</li>)}
    </ul>
  )
}

// CLIENT COMPONENT — precisa do "use client" no topo
// Pode usar hooks (useState, useEffect, etc), eventos, browser APIs
"use client"
import { useState } from "react"

function ContadorDeItens() {
  const [quantidade, setQuantidade] = useState(0)
  return (
    <button onClick={() => setQuantidade(q => q + 1)}>
      {quantidade} itens
    </button>
  )
}
```

**Regra:** Use Server Components por padrao. So adicione `"use client"` quando precisar de interatividade (hooks, eventos de click, estado local).

---

## 2. State Management

### React Context (estado global simples)

```tsx
// contexto-do-usuario.tsx
"use client"
import { createContext, useContext, useState, ReactNode } from "react"

type Usuario = { nome: string; email: string } | null

const ContextoUsuario = createContext<{
  usuario: Usuario
  definirUsuario: (u: Usuario) => void
}>({ usuario: null, definirUsuario: () => {} })

export function ProvedorDeUsuario({ children }: { children: ReactNode }) {
  const [usuario, definirUsuario] = useState<Usuario>(null)
  return (
    <ContextoUsuario.Provider value={{ usuario, definirUsuario }}>
      {children}
    </ContextoUsuario.Provider>
  )
}

export function useUser() {
  return useContext(ContextoUsuario)
}
```

### Zustand (estado global com mais controle)

```tsx
import { create } from "zustand"

type EstadoDoCarrinho = {
  itens: Array<{ id: string; nome: string; preco: number }>
  adicionarItem: (item: { id: string; nome: string; preco: number }) => void
  removerItem: (id: string) => void
  totalDeItens: () => number
}

export const useCarrinho = create<EstadoDoCarrinho>((set, get) => ({
  itens: [],
  adicionarItem: (item) => set((estado) => ({ itens: [...estado.itens, item] })),
  removerItem: (id) => set((estado) => ({ itens: estado.itens.filter(i => i.id !== id) })),
  totalDeItens: () => get().itens.length,
}))
```

### URL State (estado via query params — sobrevive a refresh)

```tsx
"use client"
import { useSearchParams, useRouter, usePathname } from "next/navigation"

function FiltrosDeBusca() {
  const parametros = useSearchParams()
  const roteador = useRouter()
  const caminho = usePathname()

  const filtroAtual = parametros.get("categoria") || "todos"

  function applyFilter(categoria: string) {
    const novosParametros = new URLSearchParams(parametros)
    novosParametros.set("categoria", categoria)
    roteador.push(`${caminho}?${novosParametros.toString()}`)
  }

  return (
    <select value={filtroAtual} onChange={(e) => applyFilter(e.target.value)}>
      <option value="todos">Todos</option>
      <option value="eletronicos">Eletronicos</option>
      <option value="roupas">Roupas</option>
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
src/app/(app)/painel/page.tsx   → Pagina do painel (herda ambos layouts)
src/app/(admin)/layout.tsx      → Layout do admin (diferente do app)
```

```tsx
// src/app/(app)/layout.tsx
export default function LayoutAreaLogada({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <BarraLateral />
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
<Link href="/produtos">Ver Produtos</Link>

// Link dinamico
<Link href={`/produtos/${produto.id}`}>Detalhes</Link>

// Navegacao programatica (client component)
"use client"
import { useRouter } from "next/navigation"

function BotaoDeLogout() {
  const roteador = useRouter()
  async function sair() {
    await fazerLogout()
    roteador.push("/login")
  }
  return <button onClick={sair}>Sair</button>
}

// Redirect no servidor (server component ou middleware)
import { redirect } from "next/navigation"

async function PaginaProtegida() {
  const sessao = await verificarSessao()
  if (!sessao) redirect("/login")
  return <div>Conteudo protegido</div>
}
```

---

## 5. Loading e Error Boundaries

```
src/app/(app)/painel/
├── page.tsx          → Conteudo da pagina
├── loading.tsx       → Mostrado enquanto page.tsx carrega
└── error.tsx         → Mostrado se page.tsx da erro
```

```tsx
// loading.tsx — skeleton automatico
export default function Carregando() {
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
export default function Erro({ error, reset }: { error: Error; reset: () => void }) {
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
async function PaginaDeProdutos() {
  const produtos = await fetch("https://api.exemplo.com/produtos", {
    next: { revalidate: 60 }, // revalida cache a cada 60 segundos
  }).then(r => r.json())

  return <ListaDeProdutos produtos={produtos} />
}
```

### SWR (client-side com cache e revalidacao)

```tsx
"use client"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then(r => r.json())

function PainelDeNotificacoes() {
  const { data, error, isLoading } = useSWR("/api/notificacoes", fetcher, {
    refreshInterval: 30000, // atualiza a cada 30 segundos
  })

  if (isLoading) return <Esqueleto />
  if (error) return <MensagemDeErro />
  return <Lista itens={data} />
}
```

---

## 7. Component Composition

### Compound Components (componentes que trabalham juntos)

```tsx
function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border p-4 shadow-sm">{children}</div>
}

Card.Cabecalho = function Cabecalho({ children }: { children: React.ReactNode }) {
  return <div className="border-b pb-2 mb-3 font-semibold">{children}</div>
}

Card.Corpo = function Corpo({ children }: { children: React.ReactNode }) {
  return <div className="text-gray-600">{children}</div>
}

// Uso:
<Card>
  <Card.Cabecalho>Titulo do Card</Card.Cabecalho>
  <Card.Corpo>Conteudo aqui dentro</Card.Corpo>
</Card>
```

### Render Props / Children as Function

```tsx
function ListaComBusca<T extends { id: string }>({
  itens,
  campoDeBusca,
  renderizarItem,
}: {
  itens: T[]
  campoDeBusca: keyof T
  renderizarItem: (item: T) => React.ReactNode
}) {
  const [busca, setBusca] = useState("")
  const filtrados = itens.filter(item =>
    String(item[campoDeBusca]).toLowerCase().includes(busca.toLowerCase())
  )

  return (
    <div>
      <input
        type="text"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
        placeholder="Buscar..."
        className="w-full p-2 border rounded mb-4"
      />
      <div className="space-y-2">{filtrados.map(renderizarItem)}</div>
    </div>
  )
}
```
