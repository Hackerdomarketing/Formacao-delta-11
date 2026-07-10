# React + Next.js 15 — Referência Curta para Componentes

> **Esta é a base CURTA.** A versão COMPLETA (16 fontes, 44 claims, 45 armadilhas, 22 padrões, 32 anti-padrões, 5 árvores de debugging) vive em `~/.claude/skills/react-next/` (skill global instalada em v5.4 Estágio 6.1).
>
> **Quando consultar esta base vs a skill:**
> - Esta base: lembrar onde colocar 'use client'; checklist de 10 perguntas antes de commitar; anti-padrões comuns
> - Skill (`~/.claude/skills/react-next/`): dúvida sobre Server vs Client Components; debugging de hydration mismatch; Server Action; testing; performance
>
> **CROSS-REFERENCE com outras skills:**
> - **RLS, supabase admin, Edge Functions:** use `~/.claude/skills/supabase-rls/`
> - **Security (XSS, headers, A03 Injection):** use `~/.claude/skills/owasp-top10/`
> - **Setup inicial de projeto Next.js:** use a doc oficial (esta skill assume projeto já criado)

## 1. As 10 perguntas antes de commitar componente

1. **'use client' está no nível mais alto necessário?** (não no leaf)
2. **Não renderiza `Date.now()`, `Math.random()`, `window` na primeira render?** (hydration mismatch)
3. **useEffect com subscription/timer tem cleanup function?**
4. **ESLint `react-hooks/exhaustive-deps` passa?**
5. **useState é APENAS para UI state local?** (não para derivar de props)
6. **Server Action tem `revalidatePath` ou `revalidateTag`?**
7. **Server Action valida input com Zod?**
8. **useMemo/useCallback é APENAS onde precisa?**
9. **Bundle size < 100KB First Load JS?**
10. **Error Boundary + loading state?**

Se QUALQUER é "não", CONSERTE antes de `git commit`.

## 2. Os 8 mandamentos de React/Next

1. **Server Component é o default.** Adicione `'use client'` APENAS se precisar de state/effect/event.
2. **'use client' é BOUNDARY, não marker.** Marca onde "ilhas interativas" começam.
3. **`import 'server-only'` em módulos server.** Build quebra se Client importar.
4. **useEffect é o POLICIAL, não o jardineiro.** Chega DEPOIS do crime (após render).
5. **Hydration mismatch = diferença server vs client.** `Date.now()`, `Math.random()`, `window` quebram.
6. **Server Action = function async no server.** SEMPRE `revalidatePath` ao final.
7. **Memo é otimização prematura em Server Components.** RSC elimina 90% dos useMemo.
8. **Race condition em form = user clica 2x.** Use `useFormStatus` ou disable button.

## 3. Árvore de decisão: Server ou Client?

```
O componente precisa de state, effect, ou event handler?
├── NÃO → Server Component (default)
└── SIM → 'use client' no ancestral mais alto
         │
         ├── State global (theme, auth, locale)? → Context API
         ├── State local (input, toggle)? → useState
         ├── Subscription/Timer? → useEffect com cleanup
         ├── Cálculo pesado repetido? → useMemo (medir antes!)
         └── Function em dep de useEffect? → useCallback
```

## 4. Os 10 anti-padrões mais comuns

| # | Anti-padrão | Severidade | Onde cai |
|---|---|---|---|
| 1 | **'use client' sem necessidade** (ANTI-001) | ALTO | Aumenta bundle, hydrata sem necessidade |
| 2 | **'use client' no leaf** (ANTI-002) | ALTO | JS boundary no meio da tree |
| 3 | **Renderiza `Date.now()` na primeira render** (ANTI-005) | CRÍTICO | Hydration mismatch |
| 4 | **Server Action sem revalidate** (ANTI-017) | CRÍTICO | UI não atualiza após mutation |
| 5 | **Server Action sem Zod** (ANTI-018) | CRÍTICO | Input não validado = vetor de exploit |
| 6 | **useEffect sem cleanup** (ANTI-011) | ALTO | Memory leak |
| 7 | **useMemo em tudo** (ANTI-013) | MÉDIO | Overhead sem ganho |
| 8 | **useState para derivar de props** (ANTI-009) | ALTO | State stale quando props mudam |
| 9 | **Importar server-only de Client** (ANTI-003) | CRÍTICO | Service_role key vaza |
| 10 | **Lista sem virtualização** (ANTI-022) | MÉDIO | 10k+ items = travamento |

## 5. Quando aprofundar na skill completa

| Situação | Vá para |
|---|---|
| Criar primeiro Server Component vs Client | skill `01-fundamentos.md` §Server Components |
| "useEffect com deps erradas" | skill `08-debugging-reativo.md` §Infinite loop |
| "Hydration mismatch" | skill `08-debugging-reativo.md` §Hydration |
| Implementar form com Server Action | skill `05-server-actions.md` (sessão 6.2) |
| "Bundle está grande" | skill `06-performance.md` (sessão 6.2) |
| Code review rápido de PR | skill `10-heuristicas-bolso.md` (sessão 6.4) |
| 22 padrões de implementação | skill `03-patterns-corretos.md` |
| 32 anti-padrões com casos reais | skill `04-anti-patterns.md` |
| Testar Server Components | skill `07-testing.md` (sessão 6.3) |
| Onboarding (entender o "por que") | skill `references/_mental-model.md` (sessão 6.4) |

## 6. Quem cuida de UI/React no projeto

| Quem | Quando |
|---|---|
| **FRONT** | Layout raiz, design system, navegação, design tokens |
| **PIXEL** | Páginas com identidade visual própria, animações, polimento |
| **FORM** | Forms multi-step, validação complexa, upload |
| **ENGINE** | Server Actions que fazem mutations, lógica de negócio |
| **SHIELD** | Code review de PR com componente novo (checagem dos 10 anti-padrões) |
| **Comandante** | Reporta "tela branca" / "componente quebrou" para o time |

---

**Proveniência:** Esta base é a versão resumida (gate) da skill completa `~/.claude/skills/react-next/` construída via Skill Forge v3 (Deep Path, Estágio 6.1 do plano de execução v5.4). A skill é o lugar de verdade; esta base existe para o time ter o essencial de React/Next em 5 minutos de leitura.