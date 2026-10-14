# PROTOCOLO DE CORREÇÃO DE ERROS — FORMAÇÃO Δ-11 (v6.3)

## FLUXO

```
Erro detectado (SHIELD, comandante, ou qualquer agente)
    ↓
O agente que detectou tenta resolver sozinho (máximo 3 tentativas)
    ↓
Não resolveu? Classifica o erro (A, B ou C) e avisa o CRONOS por SendMessage
    ↓
Categoria A (visual): CRONOS dispara o FRONT ou o PIXEL
Categoria B (dados):  CRONOS dispara o SCOUT
Categoria C (estrutural): CRONOS dispara o ATLAS
    ↓
O agente de diagnóstico lê: as fatias do project-core / o project-core (SCOUT e ATLAS podem ler o inteiro)
                            + o -produto.md dos agentes envolvidos
    ↓
Gera duas análises: conservadora e abrangente → executa a mais adequada
    ↓
Passa pela rotina de finalização (build-validator → contract-tester → SendMessage ao CRONOS)
    ↓
O CRONOS dispara o SHIELD para revisar a correção
    ↓
APROVADO? → o CRONOS atualiza o kanban. Fim.
REPROVADO? → nova tentativa (o SCOUT tem no máximo 3)
    ↓
3 falhas do SCOUT → o SCOUT PARA e avisa o CRONOS
    ↓
O CRONOS dispara um NOVO SCOUT com contexto limpo (só o resumo do problema e o que já foi tentado)
    ↓
6 falhas no total → o CRONOS dispara o ATLAS (o problema é estrutural)
    ↓
Se nem o ATLAS resolver, ou se a saída exigir decisão de negócio → o CRONOS avisa o comandante
```

## ESCALAÇÃO DE ERROS (sempre via CRONOS)

Nenhum agente dispara outro agente por conta própria. Quem dispara o agente de resgate é sempre o CRONOS.

**Resumo rápido para quem encontrou o erro:**
1. Tente resolver sozinho (máximo 3 tentativas).
2. Classifique o erro (A/B/C).
3. Envie `SendMessage` ao CRONOS com o erro, a categoria e o contexto completo.
4. Salve o mesmo contexto em `.delta-11/ativacoes/erro-[DESTINO].txt` (registro e retomada — o arquivo é a fonte de verdade; a mensagem é só o aviso).
5. O CRONOS decide quem disparar (FRONT/PIXEL, SCOUT ou ATLAS) e com qual prompt.
6. Continue trabalhando em outras tarefas enquanto o agente de diagnóstico resolve.

## CATEGORIAS DE ALTERAÇÃO

| Categoria | O que é | Quem resolve | Quem aprova |
|-----------|---------|--------------|-------------|
| A — Apenas visual | Muda interface sem afetar dados | O próprio agente ou FRONT/PIXEL | FRONT autoriza; SHIELD revisa |
| B — Envolve dados | Muda formato de dados entre interface e servidor | SCOUT diagnostica e corrige | ATLAS atualiza o contrato se necessário; SHIELD revisa |
| C — Estrutural | Muda banco, autenticação ou módulos | ATLAS obrigatoriamente | ATLAS; o comandante só se for decisão de negócio ou houver risco de perda de dados |

## REGRAS

- Máximo 3 tentativas por agente antes de escalar.
- **SCOUT nunca dispara SCOUT.** Depois de 3 falhas, ele para e avisa o CRONOS; é o CRONOS quem dispara um novo SCOUT com contexto limpo. Depois de 6 falhas no total, o CRONOS dispara o ATLAS.
- Erro no código que outro agente escreveu: NÃO altere sem antes ler o `-produto.md` daquele agente.
- Documente o erro e a correção no seu `-produto.md` (o que existe agora) e no seu `-historia.md` (o que foi tentado).
- O kanban é escrito só pelo CRONOS: você informa, ele registra.
