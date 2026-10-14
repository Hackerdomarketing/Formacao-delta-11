# Base de Conhecimento: Coordenacao de Projetos Multi-Agente — CRONOS

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Todo mini-plano que você gerar leva a seção CONVENÇÕES apontando para as seções 8-9 do regras-codigo.md.


Referencia pratica para coordenar agentes paralelos em projetos de software.
Foco: dependencias, caminho critico, resolucao de bloqueios, sequenciamento.

---

## 1. Analise de Caminho Critico

O caminho critico e a sequencia mais longa de tarefas dependentes — qualquer atraso nela atrasa o projeto inteiro.

### Como identificar

1. Liste todas as tarefas e suas dependencias ("depende de")
2. Calcule a cadeia mais longa de tarefas sequenciais
3. Essa cadeia e o caminho critico — priorize-a acima de tudo

### Caminho critico tipico (Next.js + Supabase)

```
VAULT (banco) → ENGINE (rotas API) → FRONT (layout) → PIXEL (paginas) → SHIELD (revisao)
```

Essa cadeia e quase sempre o caminho critico. FORM pode rodar em paralelo com PIXEL (zonas diferentes), mas ambos dependem do FRONT.

### Regra pratica

- Se uma tarefa esta no caminho critico e outra nao: a do caminho critico tem prioridade absoluta
- Se duas tarefas estao no caminho critico: a que desbloqueia MAIS tarefas subsequentes vai primeiro
- Tarefas fora do caminho critico podem atrasar sem impactar o prazo total

---

## 2. Mapeamento de Dependencias

### Tipos de dependencia

| Tipo | Significado | Exemplo |
|------|------------|---------|
| **Bloqueante** | B nao pode comecar sem A terminar | ENGINE precisa que VAULT crie as tabelas |
| **Parcial** | B pode comecar com parte de A pronta | FRONT pode comecar layout enquanto ENGINE cria as primeiras rotas |
| **Informacional** | B precisa saber o que A decidiu, nao esperar terminar | PIXEL precisa saber quais paginas existem (definido pelo ATLAS) |

### Formato de registro no kanban

Toda tarefa com dependencia DEVE ter o campo:
```
Depende de: T-XXX (AGENTE)
```

### Grafo de dependencias por fase tipica

```
Fase 3 (Infraestrutura):
  VAULT cria banco → desbloqueia ENGINE e BACK

Fase 4 (Desenvolvimento):
  ENGINE (rotas) ──→ FRONT (layout) ──→ PIXEL (paginas)
                                    ──→ FORM (formularios)
  VAULT (queries) ──→ ENGINE (usa queries nas rotas)

Fase 5 (Qualidade):
  SHIELD revisa tudo → SCOUT faz scan preventivo
```

### Anti-padrao: dependencia circular

Se A depende de B e B depende de A, algo esta errado na arquitetura. Escale para ATLAS imediatamente.

---

## 3. Sequenciamento por Zona de Trabalho

Os agentes trabalham em zonas. A regra fundamental:

- **Zonas diferentes = podem rodar em PARALELO**
- **Mesma zona = devem rodar em SEQUENCIA**

### Tabela de zonas

| Zona | Arquivos | Agentes tipicos |
|------|---------|----------------|
| BANCO | Supabase: tabelas, RLS, functions, migrations | VAULT |
| API | `src/app/api/**` | ENGINE, BACK |
| UI-PAGINAS | `src/app/(app)/**`, `src/app/(admin)/**` | PIXEL |
| UI-FORMS | Componentes de formulario | FORM |
| UI-LAYOUT | `src/components/**`, layouts, navegacao | FRONT |
| CONFIG | `middleware.ts`, `src/lib/**`, `src/types/**` | Compartilhada |
| TESTES | `__tests__/**`, `*.test.*` | SHIELD |

### Decisoes de sequenciamento

```
SEGURO em paralelo:
  PIXEL (UI-PAGINAS) + ENGINE (API) + FORM (UI-FORMS)
  SHIELD (TESTES) + qualquer agente (SHIELD so le, nao edita)

PERIGOSO em paralelo:
  FRONT (UI-LAYOUT) + PIXEL (UI-PAGINAS) — ambos tocam UI
  ENGINE (API) + BACK (API) — mesma zona, risco de conflito

PROIBIDO em paralelo:
  Dois agentes editando o mesmo arquivo
```

---

## 4. Deteccao e Resolucao de Bloqueios

### Sinais de agente bloqueado

| Sinal | O que verificar |
|-------|----------------|
| Tarefa em FAZENDO por muito tempo sem atualizar kanban-data.js | Agente pode ter travado ou enchido contexto |
| Arquivo de lock antigo (>30 min) sem heartbeat recente | Agente morreu sem liberar locks |
| Tarefa marcada como "bloqueado" no kanban | Dependencia nao resolvida |
| ACK de ativacao ausente apos 10 min do dispatch | Agente nao iniciou |

### Playbook de desbloqueio

**Agente travado (sem heartbeat):**
1. Verifique `.delta-11/ativacoes/ack-[AGENTE].txt` — existe?
2. Se nao: o dispatch falhou. Re-dispare o agente
3. Se sim mas heartbeat antigo: contexto esgotou. Gere prompt de retomada e re-dispare

**Dependencia nao cumprida:**
1. Identifique qual tarefa esta bloqueando
2. Verifique se o agente responsavel esta ativo e trabalhando nela
3. Se nao: priorize essa tarefa (mova para o topo da fila do agente)
4. Se sim mas demorando: resequencie você mesmo (CRONOS) as tarefas que não dependem dela. O comandante só entra se a troca mudar escopo ou prazo combinado (D4)

**Dois agentes tentando editar o mesmo arquivo:**
1. Verifique `.delta-11/locks/` — ha conflito?
2. O agente que chegou segundo DEVE trabalhar em outra tarefa ate o lock ser liberado
3. NUNCA force a remocao de um lock ativo

---

## 5. Padroes de Falha em Projetos Multi-Agente

### Race condition de transicao de fase

**Problema:** Duas sessões tentam abrir a próxima fase ao mesmo tempo (ex.: o CRONOS original e uma retomada).
**Solucao:** Só o CRONOS abre fase (D5) e usa a trava atômica (`mkdir .trava-fase-N`) — só quem cria o diretório abre a fase; quem encontra a trava pronta para.

### Duplicacao de trabalho

**Problema:** Dois agentes criam o mesmo arquivo ou implementam a mesma funcionalidade.
**Solucao:** Verificar locks ANTES de iniciar. Cada agente declara quais arquivos vai tocar no Passo 0.3.

### Drift arquitetural

**Problema:** Agente implementa algo diferente do que o contrato no `project-core.md` especifica.
**Solucao:** Contract Tester (sub-agente) roda antes de marcar tarefa como concluida. Se desvio detectado, tarefa volta para correcao.

### Contexto esgotado no meio de tarefa critica

**Problema:** Agente do caminho critico enche o contexto e para. Outros agentes ficam esperando.
**Solucao:** O agente grava `memoria/[AGENTE]-produto.md` e `-historia.md` (onde parou) e avisa o CRONOS por SendMessage. O CRONOS dispara a retomada do agente (ele mesmo sem worktree, `name: "cronos"`; o executor retomado volta com `isolation: "worktree"`) e confirma pela ACK. Nenhum agente se auto-dispara.

### Efeito domino de erro

**Problema:** Erro no VAULT (banco) se propaga para ENGINE (rotas) e depois para FRONT (telas).
**Solucao:** Quando erro e detectado em camada base (banco, contrato), PARE os agentes das camadas acima. Corrija a base primeiro. Depois retome de cima para baixo.

---

## 6. Gatilhos de Replanejamento

CRONOS DEVE declarar replanejamento quando:

| Gatilho | Acao |
|---------|------|
| 3 falhas consecutivas na mesma tarefa | O SCOUT para e avisa o CRONOS; o CRONOS dispara um NOVO SCOUT com contexto limpo (resumo do problema). Após 6 falhas no total, o CRONOS dispara o ATLAS (D23) |
| Mudanca de contrato no `project-core.md` (aviso `ativacoes/contratos-desatualizados.txt`) | Esperar o ATLAS terminar, rodar o contract-tester UMA vez, apagar o aviso; se já há código, disparar o impact-mapper e decidir as tarefas propostas (D31) |
| Taxa de aprovacao do SHIELD < 50% | Algo estrutural esta errado — escalar para ATLAS |
| Dependencia fundamental impossivel de cumprir | Replanejar a ordem das tarefas |
| Agente do caminho critico morreu e nao retomou em 15 min | Re-disparar ou redistribuir tarefas |

### Processo de replanejamento

1. **Congele** o kanban — nenhum agente puxa nova tarefa
2. **Diagnostique** a causa raiz (nao o sintoma)
3. **Dispare o ATLAS** se a causa for de contrato ou arquitetura; consulte o comandante só se a mudança for de escopo/negócio (D4)
4. **Atualize** o kanban com a nova sequencia
5. **Descongele** e informe os agentes ativos

---

## 7. Checklist de Coordenacao

### Antes de cada transicao de fase

- [ ] Todas as tarefas da fase atual estao CONCLUIDO no kanban?
- [ ] Nenhum lock ativo em `.delta-11/locks/`?
- [ ] Nenhuma tarefa em REVISAO aguardando SHIELD?
- [ ] Trava de fase criada com sucesso (`mkdir .trava-fase-N`)?
- [ ] Mini-planos da próxima fase escritos em `planos/[AGENTE]-plan.md` (o anterior arquivado em `planos/arquivo/`) e despacho na ordem correta de prioridade?
- [ ] Primeiro VAULT, depois ENGINE/BACK, depois FRONT, depois PIXEL/FORM?

### Durante execucao de fase

- [ ] Caminho critico esta sendo priorizado?
- [ ] Agentes em zonas diferentes estao em paralelo (nao sequencial desnecessario)?
- [ ] Nenhum agente esta parado esperando quando poderia trabalhar em tarefa alternativa?
- [ ] kanban-data.js esta sendo atualizado (progresso visivel no painel)?
- [ ] ACKs de todos os agentes ativos existem em `.delta-11/ativacoes/`?

### Apos cada tarefa concluida

- [ ] Tarefa movida para CONCLUIDO (ou REVISAO se precisa SHIELD)?
- [ ] Dependencias desbloqueadas foram identificadas?
- [ ] Agente desbloqueado foi disparado automaticamente?
- [ ] `memoria/[AGENTE]-produto.md` e `-historia.md` atualizados (o antigo `-estado.md` é legado — D8)?

---

## 8. Erros Comuns do Coordenador

### Nao verificar dependencias antes de disparar

**Errado:** Disparar PIXEL antes do FRONT criar os layouts.
**Certo:** Verificar no kanban se as tarefas de FRONT que PIXEL depende estao CONCLUIDO.

### Disparar agentes na mesma zona em paralelo

**Errado:** ENGINE e BACK rodando ao mesmo tempo editando rotas de API.
**Certo:** ENGINE primeiro (cria rotas), BACK depois (revisa e otimiza).

### Ignorar agente morto

**Errado:** Esperar infinitamente um agente que encheu o contexto.
**Certo:** Verificar heartbeat/ACK. Se ausente apos 10 min, re-disparar com prompt de retomada.

### Levar ao comandante o que é decisão técnica (ou esconder dele o que é de negócio)

**Errado:** Perguntar "posso resequenciar?" ao comandante, ou mudar escopo/prazo combinado sem falar com ele.
**Certo:** Resequenciar é decisão do CRONOS — faça e registre no painel. Só leve ao comandante as 3 situações da D4: decisão de negócio/escopo que só ele pode tomar; credencial/conta/pagamento/CAPTCHA; risco de perda de dados ou publicação externa.

### Nao usar a trava de fase

**Errado:** Abrir a próxima fase sem verificar se outra sessão do CRONOS já está fazendo isso.
**Certo:** SEMPRE usar `mkdir .trava-fase-N` antes de abrir a fase. Se já existe, parar.
