# PROTOCOLO DE COMUNICAÇÃO — FORMAÇÃO Δ-11

## COMO OS AGENTES SE COMUNICAM

Os agentes são instâncias separadas do Claude Code em janelas diferentes. Eles NÃO se comunicam diretamente. Toda coordenação acontece por TRÊS mecanismos de arquivos compartilhados:

### 1. KANBAN (`.delta-11/kanban.md`)
Fonte de verdade sobre tarefas. Cada agente lê, puxa tarefas, e atualiza ao concluir.

### 2. ARQUIVOS DE ESTADO (`.delta-11/memoria/[AGENTE]-estado.md`)
Cada agente registra o que fez e onde parou. Outros agentes podem ler quando precisam de contexto.

### 3. PROJETO CENTRAL (`.delta-11/memoria/project-core.md`)
Contratos, esquema de banco, decisões arquiteturais. Todos leem. Somente ATLAS atualiza.

### 4. MODO DE DISPATCH (`.delta-11/.dispatch-mode`)
Configura como os agentes abrem novas janelas automaticamente. Três modos possíveis:
- **terminal-app** — Cada agente roda como processo `claude` CLI em aba separada do Terminal.app (recomendado — zero conflito de lock file)
- **vscode-tab** — Via extensão Claude Code do VS Code (comando "Open in New Tab" — pode travar com muitos agentes)
- **manual** — O comandante cola os prompts manualmente

O ATLAS configura este arquivo na primeira ativação. Qualquer agente pode ler o arquivo para saber qual mecanismo usar ao auto-disparar.

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

## 5. RASTREAMENTO EM TEMPO REAL

Dois mecanismos automáticos garantem visibilidade total quando agentes trabalham em paralelo:

### ACTIVITY LOG (`.delta-11/activity-log.md`)
- **Gerado automaticamente** por hooks do sistema (PostToolUse)
- Toda escrita de arquivo (Write, Edit) é registrada com: agente, tarefa, arquivo, horário
- **Consultar obrigatoriamente no Passo 0.1** antes de iniciar qualquer tarefa
- Nenhum agente precisa "lembrar" de escrever — o hook faz automaticamente

### SISTEMA DE LOCKS (`.delta-11/locks/`)
- Antes de editar qualquer arquivo: criar `.delta-11/locks/[caminho--do--arquivo].lock`
- O hook PreToolUse verifica locks automaticamente antes de cada Write/Edit
- Se o arquivo está travado por outro agente → operação é BLOQUEADA com mensagem clara
- Ao finalizar tarefa: deletar seus locks (Passo 3.8)
- Fallback automático: hook Stop libera todos os locks quando a sessão encerra
- Locks com mais de 2 horas são removidos automaticamente (proteção contra sessões abandonadas)

### HOOKS DO SISTEMA (`.claude/settings.json`)
- **PreToolUse** → Verifica lock antes de cada Write/Edit
- **PostToolUse** → Registra atividade automaticamente no activity-log.md
- **Stop** → Libera locks quando agente para
- Hooks são configurados pelo `sincronizar.sh` e não dependem de cooperação do agente

## ESQUEMA DE BANCO CONGELADO

Durante um sprint, o esquema de banco NÃO MUDA. Agentes podem confiar na estabilidade. Mudanças seguem o mesmo processo do contrato (via ATLAS).
