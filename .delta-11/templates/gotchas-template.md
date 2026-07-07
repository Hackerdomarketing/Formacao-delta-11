# TEMPLATE — Gotchas do Projeto (memória viva de armadilhas)

**O que é:** o registro acumulado de armadilhas REAIS que já morderam este projeto — cada uma com o que evitar, por que, e o que fazer no lugar. É a diferença entre time que repete o erro e time que aprende: a base de conhecimento é curada e estática; o gotchas.md cresce sozinho a cada erro resolvido.

**Onde vive a instância:** `.delta-11/memoria/gotchas.md` (um por projeto, compartilhado — path absoluto do repo principal)

**Quem ESCREVE:**
- **SCOUT** — após TODA correção concluída (passo 6 do fluxo de correção): o bug que ele acabou de matar vira gotcha
- **SHIELD** — ao reprovar pelo MESMO padrão de erro pela 2ª vez
- **Qualquer agente** — que perdeu mais de 30 minutos numa armadilha não documentada

**Quem LÊ:** **CRONOS** — antes de despachar cada mini-plano, copia os gotchas relevantes à zona do agente (formato resumido: `EVITE: [padrão] — [motivo] — [alternativa]`). Agentes NÃO precisam ler o arquivo inteiro — recebem o recorte no mini-plano.

**Manutenção:** máximo ~50 gotchas por projeto. Gotcha repetido → incrementar `Ocorrências` (não duplicar). Gotcha que virou regra permanente do sistema → promover para a base de conhecimento do domínio (via comandante) e remover daqui.

---

```markdown
# Gotchas do Projeto — [nome do projeto]

> Mais novo no topo. CRONOS: injete os da zona relevante em cada mini-plano.

## G-002: [padrão que deu errado, em 1 linha]
- **Data:** AAAA-MM-DD · **Registrado por:** [agente] · **Zona:** BANCO | API | UI-PÁGINAS | UI-FORMS | UI-LAYOUT | CONFIG | TESTES
- **EVITE:** [o que não fazer — específico, com nome de função/arquivo se houver]
- **PORQUE:** [o que aconteceu de verdade — o erro real, 1-2 linhas]
- **FAÇA:** [a alternativa correta que funcionou]
- **Ocorrências:** 1

## G-001: Supabase retorna lista vazia sem erro quando RLS bloqueia
- **Data:** 2026-07-07 · **Registrado por:** exemplo · **Zona:** API
- **EVITE:** tratar `data: []` como "não existem registros" sem verificar política RLS
- **PORQUE:** query com RLS ativo e política ausente retorna vazio SILENCIOSAMENTE — parece bug de dados, é permissão
- **FAÇA:** ao receber vazio inesperado, rodar a mesma query com service role em ambiente dev; se retornar dados, o problema é política RLS
- **Ocorrências:** 1
```
