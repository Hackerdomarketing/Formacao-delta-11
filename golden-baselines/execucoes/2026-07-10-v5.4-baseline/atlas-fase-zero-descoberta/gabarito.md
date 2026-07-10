## Gabarito (checklist de Corretude — avaliador confere item a item)

### Discovery (Fase 0 — saída canônica)

1. [ ] Arquivo `docs/avatar.md` criado com persona primária (nome, idade, profissão, contexto de uso, dores, gains, jobs-to-be-done) E persona secundária (pelo menos 1, mesmo nível de detalhe)
2. [ ] Avatar cita FONTE dos dados (entrevista, suposição fundamentada, benchmark) — não inventar números sem dizer que são chutes
3. [ ] Arquivo `docs/prd.md` criado usando o template `prd-documento-de-requisitos-template.md`, preenchido com: problema, público-alvo (linkando avatar.md), métricas de sucesso, escopo MVP vs fora-de-escopo, restrições técnicas (Next.js + Supabase), restrições de prazo (2 semanas)
4. [ ] PRD tem pelo menos 5 requisitos funcionais numerados (RF-001 a RF-00N) com critério de aceite
5. [ ] PRD tem pelo menos 3 requisitos não-funcionais (RNF): performance, segurança, usabilidade
6. [ ] Riscos do MVP listados explicitamente (pelo menos 3, com mitigação)
7. [ ] Decisões NÃO tomadas explicitamente (ex: "não decidimos se terá push notification" → registrado como decisão pendente, não como esquecimento)
8. [ ] Avatar.md E prd.md não contêm jargão técnico desnecessário para o comandante (linguagem humana + termos técnicos com explicação entre colchetes, conforme CLAUDE.md)
9. [ ] Nenhum código foi escrito (Fase 0 é descoberta; respeitar regra "nunca codificar antes do plano do ATLAS estar aprovado")
10. [ ] Briefing com perguntas para o comandante se algo ficou ambíguo (lista de 1-3 perguntas no fim do PRD se houver lacunas reais)

### Convenções

- Limites estruturais do estado-produto não se aplicam (ATLAS está isento)
- Português em todo o conteúdo
- Nomes de campos/tabelas em português também (não estamos em código — doc do comandante)
- Paths canônicos respeitados (avatar/prd não viraram `.md` na raiz)

### Disciplina v5 — anti-tells do ATLAS

- Frases como "tudo certo para Fase 2" sem evidência específica no PRD = reprovável
- Lista de requisitos sem critério de aceite = reprovável
- Avatar sem dados-fontes = reprovável (chute tem que ser declarado como chute)
