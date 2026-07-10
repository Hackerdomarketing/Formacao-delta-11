## Gabarito (checklist de Corretude)

1. [ ] Página em `src/app/products/page.tsx`; componente(s) ≤ 150 linhas e ≤ 5 props cada
2. [ ] Skeleton que IMITA o layout real dos cards (não spinner centralizado)
3. [ ] Estado de erro com mensagem em português + botão "Tentar de novo" funcional
4. [ ] Dados renderizados com fallback (`?.` / `??`) — nenhum acesso direto a campo que pode faltar
5. [ ] `next/image` com `alt` descritivo e `width`/`height` (sem layout shift)
6. [ ] Preço formatado de centavos para R$ (Intl.NumberFormat pt-BR)
7. [ ] Fonte via `next/font` que NÃO seja Inter/Roboto/Arial; paleta coerente com café artesanal via variáveis CSS
8. [ ] Animação de entrada com atraso sequencial nos cards + hover com micro-interação
9. [ ] Responsivo mobile-first (grid 1 coluna → 2-3 colunas) e navegável por teclado
10. [ ] Zero texto de interface em inglês; zero nome de variável em português
