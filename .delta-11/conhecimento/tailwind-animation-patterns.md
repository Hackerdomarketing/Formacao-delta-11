# Tailwind CSS e Animation Patterns — Base de Conhecimento PIXEL

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Componente ≤ 150 linhas e ≤ 5 props · textos visíveis ao usuário sempre em português.


Referencia pratica para o agente PIXEL da Formacao Delta-11.
Foco: design responsivo, animacoes, micro-interacoes, tipografia, dark mode.

---

## 1. Responsive Design com Tailwind

```tsx
// Mobile-first: classes sem prefixo = mobile, prefixos = breakpoints maiores
<div className="
  grid grid-cols-1        // mobile: 1 coluna
  sm:grid-cols-2          // 640px+: 2 colunas
  md:grid-cols-3          // 768px+: 3 colunas
  lg:grid-cols-4          // 1024px+: 4 colunas
  gap-4 p-4
">
  {produtos.map(p => <CardDeProduto key={p.id} produto={p} />)}
</div>

// Container com largura maxima centralizado
<div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
  {children}
</div>

// Esconder/mostrar por breakpoint
<nav className="hidden md:flex">Menu Desktop</nav>
<button className="md:hidden">Menu Mobile</button>

// Tipografia responsiva
<h1 className="text-2xl sm:text-3xl lg:text-5xl font-bold">
  Titulo Responsivo
</h1>
```

---

## 2. Transitions com Tailwind

```tsx
// Transicao basica (hover suave)
<button className="
  bg-blue-600 text-white px-6 py-3 rounded-lg
  transition-all duration-200 ease-in-out
  hover:bg-blue-700 hover:shadow-lg hover:scale-105
  active:scale-95
">
  Comprar Agora
</button>

// Transicao de cor e borda (input de formulario)
<input className="
  border-2 border-gray-300 rounded-lg px-4 py-2
  transition-colors duration-150
  focus:border-blue-500 focus:ring-2 focus:ring-blue-200
  focus:outline-none
" />

// Transicao de opacidade (aparecer/desaparecer)
<div className={`
  transition-opacity duration-300
  ${visivel ? "opacity-100" : "opacity-0 pointer-events-none"}
`}>
  Conteudo que aparece e desaparece
</div>

// Transicao de altura (accordion)
<div className={`
  overflow-hidden transition-all duration-300 ease-in-out
  ${aberto ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}
`}>
  Conteudo expansivel
</div>
```

---

## 3. Animate Classes do Tailwind

```tsx
// Spin (loading spinner)
<svg className="animate-spin h-5 w-5 text-blue-600" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"
    className="opacity-25" fill="none" />
  <path className="opacity-75" fill="currentColor"
    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
</svg>

// Pulse (skeleton loading)
<div className="animate-pulse space-y-3">
  <div className="h-4 bg-gray-200 rounded w-3/4" />
  <div className="h-4 bg-gray-200 rounded w-1/2" />
  <div className="h-10 bg-gray-200 rounded" />
</div>

// Bounce (chamar atencao)
<span className="animate-bounce inline-block">↓</span>

// Ping (notificacao)
<span className="relative flex h-3 w-3">
  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
</span>
```

---

## 4. Framer Motion — Page Transitions

```tsx
"use client"
import { motion, AnimatePresence } from "framer-motion"

// Wrapper de pagina com fade + slide
function TransicaoDePagina({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      {children}
    </motion.div>
  )
}

// Uso no layout
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AnimatePresence mode="wait">
      <TransicaoDePagina key={/* pathname */}>
        {children}
      </TransicaoDePagina>
    </AnimatePresence>
  )
}
```

### List Animations (itens que entram um por um)

```tsx
"use client"
import { motion } from "framer-motion"

const variantesDoContainer = {
  escondido: { opacity: 0 },
  visivel: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const variantesDoItem = {
  escondido: { opacity: 0, y: 20 },
  visivel: { opacity: 1, y: 0 },
}

function ListaAnimada({ itens }: { itens: Array<{ id: string; nome: string }> }) {
  return (
    <motion.ul
      variants={variantesDoContainer}
      initial="escondido"
      animate="visivel"
      className="space-y-2"
    >
      {itens.map((item) => (
        <motion.li key={item.id} variants={variantesDoItem} className="p-4 bg-white rounded shadow">
          {item.nome}
        </motion.li>
      ))}
    </motion.ul>
  )
}
```

### Gestures (arrastar, hover, tap)

```tsx
<motion.div
  whileHover={{ scale: 1.03, boxShadow: "0 10px 30px rgba(0,0,0,0.1)" }}
  whileTap={{ scale: 0.97 }}
  drag="x"
  dragConstraints={{ left: -100, right: 100 }}
  className="p-6 bg-white rounded-xl cursor-grab active:cursor-grabbing"
>
  Arraste horizontalmente
</motion.div>
```

---

## 5. Skeleton Loading Patterns

```tsx
// Card skeleton completo
function EsqueletoDeCard() {
  return (
    <div className="animate-pulse rounded-xl border p-4 space-y-4">
      {/* Imagem */}
      <div className="h-48 bg-gray-200 rounded-lg" />
      {/* Titulo */}
      <div className="h-5 bg-gray-200 rounded w-2/3" />
      {/* Descricao */}
      <div className="space-y-2">
        <div className="h-3 bg-gray-200 rounded w-full" />
        <div className="h-3 bg-gray-200 rounded w-4/5" />
      </div>
      {/* Botao */}
      <div className="h-10 bg-gray-200 rounded-lg w-1/3" />
    </div>
  )
}

// Grid de skeletons (enquanto a lista carrega)
function EsqueletoDeGrid({ quantidade = 6 }: { quantidade?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: quantidade }).map((_, i) => (
        <EsqueletoDeCard key={i} />
      ))}
    </div>
  )
}
```

---

## 6. Micro-Interactions

```tsx
// Botao com feedback visual completo
<button className="
  group relative overflow-hidden
  bg-blue-600 text-white font-medium px-6 py-3 rounded-lg
  transition-all duration-200
  hover:bg-blue-700 hover:shadow-lg
  active:scale-[0.98]
  focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2
  disabled:opacity-50 disabled:cursor-not-allowed
">
  <span className="relative z-10">Enviar</span>
  {/* Efeito ripple no hover */}
  <span className="absolute inset-0 bg-white/10 scale-0 group-hover:scale-100
    transition-transform duration-300 rounded-lg" />
</button>

// Icon button com tooltip
<button className="
  group relative p-2 rounded-full
  hover:bg-gray-100 transition-colors
" aria-label="Excluir item">
  <TrashIcon className="h-5 w-5 text-gray-500 group-hover:text-red-500 transition-colors" />
  <span className="
    absolute -top-8 left-1/2 -translate-x-1/2
    bg-gray-800 text-white text-xs px-2 py-1 rounded
    opacity-0 group-hover:opacity-100 transition-opacity
    pointer-events-none whitespace-nowrap
  ">
    Excluir
  </span>
</button>

// Link com underline animado
<a className="
  relative text-blue-600 font-medium
  after:absolute after:bottom-0 after:left-0
  after:h-0.5 after:w-0 after:bg-blue-600
  after:transition-all after:duration-300
  hover:after:w-full
">
  Saiba mais
</a>
```

---

## 7. Google Fonts com Next.js

```tsx
// src/app/layout.tsx
import { Inter, Playfair_Display } from "next/font/google"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  )
}
```

```js
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-playfair)", "Georgia", "serif"],
      },
    },
  },
}
```

```tsx
// Uso
<h1 className="font-display text-4xl">Titulo Elegante</h1>
<p className="font-sans text-base">Texto normal do corpo</p>
```

---

## 8. Dark Mode

```tsx
// tailwind.config.ts — habilitar dark mode por classe
module.exports = {
  darkMode: "class",
  // ...
}

// Componente com dark mode
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
  border border-gray-200 dark:border-gray-700 rounded-lg p-6">
  <h2 className="text-lg font-bold">Titulo</h2>
  <p className="text-gray-600 dark:text-gray-400">Descricao do conteudo</p>
</div>

// Toggle de dark mode
"use client"
import { useEffect, useState } from "react"

function BotaoDeDarkMode() {
  const [escuro, setEscuro] = useState(false)

  useEffect(() => {
    const salvo = localStorage.getItem("tema")
    const prefereEscuro = window.matchMedia("(prefers-color-scheme: dark)").matches
    setEscuro(salvo === "escuro" || (!salvo && prefereEscuro))
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle("dark", escuro)
    localStorage.setItem("tema", escuro ? "escuro" : "claro")
  }, [escuro])

  return (
    <button
      onClick={() => setEscuro(!escuro)}
      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      aria-label={escuro ? "Ativar modo claro" : "Ativar modo escuro"}
    >
      {escuro ? "☀️" : "🌙"}
    </button>
  )
}
```
