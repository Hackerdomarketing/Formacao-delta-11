# Tarefa Canônica — FRONT — Layout base e design system para dashboard

**Agente-alvo:** FRONT · **Duração esperada:** 1 janela · **Criada em:** 2026-07-10 (não alterar — ver README)
**Última atualização:** 2026-07-10 (v5.4 baseline) — se a tarefa precisar mudar, versione (crie v2 em arquivo novo, mantendo a v1 para histórico)

## Bloco de ativação (colar na janela do FRONT)

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é FRONT. Leia seu operativo e as bases react-component-patterns.md + design-patterns-praticos.md normalmente.

# Mini-plano — FRONT | Golden | ONDA G-2
Tipo de tarefa: fundação de UI

## 1. O que esta tarefa precisa produzir
Layout raiz + design system mínimo para uma dashboard autenticada
de app B2B (SaaS interno). Outros agentes (PIXEL, FORM) vão
preencher páginas e formulários EM CIMA do que você criar aqui.

## 2. Recorte relevante
- App B2B desktop-first (tablet funciona, mobile é nice-to-have)
- Identidade: tons neutros (cinza/azul), sem cara de startup flashy
- Tipografia do sistema (system-ui) — fonte custom é decisão de PIXEL, não sua
- Modo escuro OBRIGATÓRIO (cliente corporativo usa)
- Acessibilidade alvo: WCAG AA

## 3. Entregas específicas
- src/app/layout.tsx: layout raiz com sidebar + header
- src/app/(authed)/layout.tsx: grupo de rotas autenticadas com guard
- src/components/layout/sidebar.tsx
- src/components/layout/header.tsx
- src/components/layout/user-menu.tsx (com logout)
- src/lib/design-system/tokens.ts: cores, espaçamentos, raios
- src/lib/design-system/theme-provider.tsx: alternância light/dark
- src/app/globals.css: import das variáveis CSS do design system

## 4. Limites de escopo
- NÃO criar páginas de feature (PIXEL faz isso)
- NÃO criar formulários complexos (FORM faz isso)
- NÃO mexer em auth/RLS (isso é do ENGINE)
- NÃO instalar biblioteca de UI pronta (shadcn/radix: só se JÁ existir no projeto)
```

## Gabarito (checklist de Corretude — avaliador confere item a item)

### Design system (tokens)

1. [ ] `tokens.ts` define paleta com pelo menos 6 cores semânticas (background, foreground, primary, secondary, muted, destructive) CADA UMA com variante light E dark — não 12 cores literais
2. [ ] Espaçamentos seguem escala consistente (ex: 4, 8, 12, 16, 24, 32, 48) — não valores arbitrários
3. [ ] Raios de borda definidos como escala (sm, md, lg) — não 1 valor fixo
4. [ ] `globals.css` referencia os tokens via variáveis CSS (`var(--color-primary)`), NÃO valores hardcoded nos componentes
5. [ ] Modo escuro implementado via classe no `<html>` ou atributo `data-theme`, NÃO via prefers-color-scheme puro (senão o usuário não pode forçar)

### Layout

6. [ ] `layout.tsx` tem `<html lang="pt-BR">` e `<body>` com classe do theme provider
7. [ ] Sidebar colapsável (botão de toggle) E responsivo (em mobile vira drawer ou hamburger)
8. [ ] Header tem: logo, breadcrumb (placeholder OK), user-menu
9. [ ] User-menu mostra nome do usuário E email (vem do session, mock pode ser usado)
10. [ ] Navegação do sidebar pelo menos 3 itens placeholder ("Dashboard", "Configurações", "Ajuda") — mesmo que páginas não existam ainda (links âncora)

### Guard de rota autenticada

11. [ ] `(authed)/layout.tsx` verifica sessão (mock OK se auth ainda não implementado)
12. [ ] Redireciona para `/login` se não autenticado (NÃO renderiza nada)
13. [ ] Loading state visível durante verificação (não flash de conteúdo)

### Qualidade de código

14. [ ] Cada componente ≤ 150 linhas e ≤ 5 props (regra §8)
15. [ ] Nenhum `style={{}}` inline com valores literais — usa tokens via classes/variáveis
16. [ ] Sem dependências novas instaladas (só o que já tem no projeto)
17. [ ] Acessibilidade: foco visível (outline não removido), aria-label em botões só com ícone, contraste mínimo 4.5:1 (verificar com ferramenta ou comentário justificando)
18. [ ] Nenhum texto de UI em inglês (regra §9)

### Disciplina v5 — anti-tells

- Layout sem modo escuro = reprovável (B2B sem dark mode é caso de reprovação hoje)
- Tokens hardcoded em componentes (`bg-blue-500`) = reprovável (vaza design system)
- Sidebar que não colapsa em mobile = reprovável (UX B2B mínimo)
- Importar shadcn/radix sem o projeto ter = reprovável (escopo furado)