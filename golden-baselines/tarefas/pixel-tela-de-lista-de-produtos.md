# Tarefa Canônica — PIXEL — Tela de lista de produtos

**Agente-alvo:** PIXEL · **Duração esperada:** 1 janela · **Criada em:** 2026-07-07 (não alterar — ver README)
**Última atualização:** 2026-07-07 (v5.3 baseline) — se a tarefa precisar mudar, versione (crie v2 em arquivo novo, mantendo a v1 para histórico)

## Bloco de ativação

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é PIXEL. Leia seu operativo e sua base de conhecimento normalmente.

# Mini-plano — PIXEL | Golden | ONDA G-1
Tipo de tarefa: funcionalidade

## 1. O que esta tarefa precisa produzir
Página /products que lista produtos de uma loja de cafés especiais.

## 2. Recorte relevante da fase anterior
- Rota GET /api/products retorna { products: [{ id, name, price_cents, image_url, roast_level }] } [Fonte: esta tarefa canônica]
- Identidade visual: marca premium de café, tom quente e artesanal, SEM cara de template [Fonte: esta tarefa canônica]

## 3. Critérios de sucesso
- Página com os 3 estados visuais completos: skeleton, erro com retry, sucesso
- Responsiva (celular e desktop) e acessível (alt, foco, contraste)
- Identidade visual conforme marca: café premium, tom quente e artesanal, SEM cara de template (criterios ESPECÍFICOS no gabarito abaixo — Corretude)

## 4. Dependências — nenhuma (pode mockar a rota com fixture local)

## 5. LIMITES DE ESCOPO
- NÃO criar a rota de API real (mock permitido)
- NÃO criar página de detalhe, carrinho ou checkout
- NÃO instalar biblioteca de UI pronta (shadcn ok se já existir no projeto; nada novo)

## 6. CONVENÇÕES — as fixas do template (limites §8 + idioma §9)
```

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
