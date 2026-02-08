# PROTOCOLO DE COMUNICAÇÃO — FORMAÇÃO Δ-11

## COMO OS AGENTES SE COMUNICAM

Os agentes são instâncias separadas do Claude Code em janelas diferentes. Eles NÃO se comunicam diretamente. Toda coordenação acontece por TRÊS mecanismos de arquivos compartilhados:

### 1. KANBAN (`.delta-11/kanban.md`)
Fonte de verdade sobre tarefas. Cada agente lê, puxa tarefas, e atualiza ao concluir.

### 2. ARQUIVOS DE ESTADO (`.delta-11/memoria/[AGENTE]-estado.md`)
Cada agente registra o que fez e onde parou. Outros agentes podem ler quando precisam de contexto.

### 3. PROJETO CENTRAL (`.delta-11/memoria/project-core.md`)
Contratos, esquema de banco, decisões arquiteturais. Todos leem. Somente ATLAS atualiza.

## FORMATO DE CONTRATO DE INTERFACE DE PROGRAMAÇÃO DE APLICAÇÕES

```
ROTA: [MÉTODO] [/caminho]
DESCRIÇÃO: [o que faz]
AUTENTICAÇÃO: [público / requer token / apenas administrador]

ENTRADA:
{
  campo: tipo (obrigatório/opcional) — descrição
}

SAÍDA SUCESSO (código [número]):
{
  campo: tipo — descrição
}

SAÍDA ERRO (código [número]):
{
  error: texto — quando acontece
}
```

## QUANDO O CONTRATO PODE MUDAR

1. Qualquer agente identifica necessidade de mudança
2. Registra no kanban como BLOQUEIO com justificativa
3. Comandante consulta ATLAS
4. ATLAS avalia, aprova ou rejeita
5. Se aprovado: ATLAS atualiza `project-core.md`
6. Todos os agentes veem a mudança na próxima leitura

## ESQUEMA DE BANCO CONGELADO

Durante um sprint, o esquema de banco NÃO MUDA. Agentes podem confiar na estabilidade. Mudanças seguem o mesmo processo do contrato (via ATLAS).
