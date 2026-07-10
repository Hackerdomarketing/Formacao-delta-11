# Tarefa Canônica — FORM — Formulário multi-step com upload e validação servidor

**Agente-alvo:** FORM · **Duração esperada:** 1 janela · **Criada em:** 2026-07-10 (não alterar — ver README)
**Última atualização:** 2026-07-10 (v5.4 baseline) — se a tarefa precisar mudar, versione (crie v2 em arquivo novo, mantendo a v1 para histórico)

## Bloco de ativação (colar na janela do FORM)

```
Formação Δ-11 — Tarefa canônica de avaliação (golden baseline).
Você é FORM. Leia seu operativo e as bases react-form-patterns.md + react-component-patterns.md normalmente.

# Mini-plano — FORM | Golden | ONDA G-2
Tipo de tarefa: formulário complexo

## 1. O que esta tarefa precisa produzir
Formulário multi-step (3 etapas) para um wizard de "Cadastrar
minha empresa" no app B2B. Última etapa inclui UPLOAD de logo
e documento CNPJ (PDF). Submissão POSTa para /api/onboarding
(já existe — só consumir).

## 2. As 3 etapas
1. Dados básicos: nome fantasia, razão social, CNPJ (com máscara)
2. Endereço: CEP (com busca ViaCEP), logradouro, número, complemento, cidade, UF
3. Documentos: upload de LOGO (PNG/JPG até 2MB) e CARTÃO CNPJ (PDF até 5MB)

## 3. Validações no cliente (Zod + react-hook-form)
- CNPJ: 14 dígitos, com dígitos verificadores válidos
- CEP: 8 dígitos, deve existir na busca ViaCEP antes de avançar
- Logo: tipo MIME image/*, tamanho ≤ 2MB
- PDF: tipo MIME application/pdf, tamanho ≤ 5MB

## 4. Validações no servidor (re-check OBRIGATÓRIO)
- Mesmas validações do cliente (cliente é descômodo, servidor é lei)
- Rate limit: máx 5 submissões por usuário por hora
- Storage: upload vai para Supabase Storage com path
  `onboarding/{user_id}/{timestamp}-{filename}`

## 5. Limites de escopo
- NÃO implementar a API /api/onboarding (já existe)
- NÃO mexer em auth/RLS (ENGINE)
- NÃO instalar biblioteca de UI (FRONT decide; usar só o que tem)
- Formato do arquivo: arquivos individuais por etapa, em
  src/components/onboarding/step-1-dados-basicos.tsx etc.
```

## Gabarito (checklist de Corretude — avaliador confere item a item)

### Estrutura e UX

1. [ ] Componente wizard com state machine claro (passo 1 → 2 → 3 → submit), usando o que o projeto já tem (useReducer, zustand, ou estado local — não inventar biblioteca)
2. [ ] Botão "Voltar" funcional em todas as etapas após a primeira
3. [ ] Barra de progresso visível (qual etapa está, quantas faltam)
4. [ ] Estado de loading global ao submeter (não por campo)
5. [ ] Mensagens de erro do servidor mostradas em português e vinculadas ao campo certo (não "Erro genérico" no topo)

### Validação cliente

6. [ ] Schema Zod único compartilhado entre as 3 etapas (src/lib/validation/onboarding.ts) — não 3 schemas duplicados
7. [ ] Validação por etapa (não valida tudo junto no fim) — UX melhor
8. [ ] CNPJ: usa algoritmo de dígitos verificadores (não só `length === 14`)
9. [ ] CEP: busca ViaCEP antes de permitir avançar (não só valida formato)
10. [ ] Upload: tipo MIME E tamanho validados NO CLIENTE antes de subir (evita upload gigante que vai falhar)

### Validação servidor (re-check)

11. [ ] API /api/onboarding (ou o que o agente EXAMINAR do código existente) tem re-validação Zod — cita o trecho ou patch proposto
12. [ ] Rate limit presente (in-memory OK para MVP, mas presente) — cita onde fica
13. [ ] Storage path é `onboarding/{user_id}/...` (não usa filename do usuário direto — risco de path traversal)
14. [ ] Storage NÃO é público (bucket privado; URL assinada retornada só após aprovação)

### Limites e convenções

15. [ ] Cada componente ≤ 150 linhas (regra §8)
16. [ ] Cada componente ≤ 5 props
17. [ ] Nenhum `useState` para mais de 3 valores correlacionados (usar reducer/zustand)
18. [ ] TypeScript strict — sem `any`
19. [ ] Mensagens de UI em português, nomes de código em inglês (regra §9)
20. [ ] Sem `console.log` de debug deixado
21. [ ] Sem código comentado órfão

### Disciplina v5 — anti-tells

- Validação só no cliente = reprovável (cliente é descômodo, servidor é lei — Cláusula §8 de regras-codigo)
- Schema Zod duplicado por etapa = reprovável (manutenção impossível)
- Upload sem validar MIME antes = reprovável (UX ruim — usuário espera 30s pra descobrir)
- Path de storage usando filename do usuário = reprovável (vulnerabilidade de path traversal)