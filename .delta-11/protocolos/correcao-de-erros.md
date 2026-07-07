# PROTOCOLO DE CORREÇÃO DE ERROS — FORMAÇÃO Δ-11

## FLUXO

```
Erro detectado (SHIELD, comandante, ou qualquer agente)
    ↓
O agente que detectou classifica o erro (A, B ou C)
    ↓
Categoria A (visual): o próprio agente tenta corrigir (max 3 tentativas)
Categoria B (dados): escala SCOUT via SendMessage ao CRONOS
Categoria C (estrutural): escala ATLAS via SendMessage ao CRONOS
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

## ESCALAÇÃO DE ERROS (v4.0 — via CRONOS)

Qualquer agente que encontrar um erro que NÃO consegue resolver sozinho escala para o CRONOS — nenhum agente dispara outro agente por conta própria. O procedimento completo está no CLAUDE.md, seção "DISPATCH DE ERROS" dentro do PROTOCOLO DE DISPATCH DE AGENTES.

**Resumo rápido:**
1. Tente resolver sozinho (máximo 3 tentativas)
2. Classifique o erro (A/B/C)
3. Envie `SendMessage` ao CRONOS descrevendo o erro, a categoria e o contexto completo
4. Salve o contexto em `.delta-11/ativacoes/erro-[DESTINO].txt` (registro histórico e retomada)
5. O CRONOS decide quem disparar (SCOUT, ATLAS ou FRONT/PIXEL) via Agent tool nativo
6. Continue trabalhando em outras tarefas enquanto o agente de diagnóstico resolve

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
