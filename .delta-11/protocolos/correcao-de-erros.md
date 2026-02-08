# PROTOCOLO DE CORREÇÃO DE ERROS — FORMAÇÃO Δ-11

## FLUXO

```
Erro detectado (SHIELD, comandante, ou qualquer agente)
    ↓
O agente que detectou classifica o erro (A, B ou C)
    ↓
Categoria A (visual): o próprio agente tenta corrigir (max 3 tentativas)
Categoria B (dados): auto-dispara SCOUT com contexto do erro
Categoria C (estrutural): auto-dispara ATLAS com contexto do erro
    ↓
SCOUT/ATLAS lê: project-core.md + estados dos agentes envolvidos
    ↓
SCOUT/ATLAS gera duas análises: conservadora e abrangente
    ↓
SCOUT/ATLAS executa a correção mais adequada
    ↓
SHIELD testa a correção (se SHIELD não está ativo, o próprio agente testa)
    ↓
Passou? → Concluído. SCOUT/ATLAS atualiza kanban e estado.
Falhou? → Segunda tentativa (máximo 3)
    ↓
3 falhas do SCOUT? → Comandante reinicia janela do SCOUT
    ↓
Mais 3 falhas (6 total)? → Escalar para ATLAS
```

## AUTO-DISPATCH DE ERROS

Qualquer agente que encontrar um erro que NÃO consegue resolver sozinho pode auto-disparar o agente de diagnóstico. O procedimento completo está no CLAUDE.md, seção "AUTO-DISPATCH DE ERROS" dentro do PROTOCOLO DE AUTO-DISPATCH.

**Resumo rápido:**
1. Tente resolver sozinho (máximo 3 tentativas)
2. Classifique o erro (A/B/C)
3. Crie arquivo em `.delta-11/ativacoes/erro-[DESTINO].txt` com contexto completo
4. Auto-dispare usando o mecanismo AppleScript do VS Code
5. Continue trabalhando em outras tarefas enquanto o agente de diagnóstico resolve

## CATEGORIAS DE ALTERAÇÃO

| Categoria | O que é | Quem resolve | Quem aprova |
|-----------|---------|--------------|-------------|
| A — Apenas visual | Muda interface sem afetar dados | O próprio agente ou FRONT/PIXEL | FRONT autoriza |
| B — Envolve dados | Muda formato de dados entre interface e servidor | SCOUT diagnostica e corrige | ATLAS atualiza contrato se necessário |
| C — Estrutural | Muda banco, autenticação ou módulos | ATLAS obrigatoriamente | ATLAS + Comandante |

## REGRAS

- Máximo 3 tentativas por agente antes de escalar
- SCOUT nunca escala para SCOUT (informa o comandante)
- Erros em código que outro agente escreveu: NÃO altere sem antes ler o estado daquele agente
- Sempre documente o erro e a correção no arquivo de estado
