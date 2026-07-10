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
