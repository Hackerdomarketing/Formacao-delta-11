# GUIA DO COMANDANTE — FORMAÇÃO Δ-11

Este documento é para VOCÊ, comandante. Aqui está tudo que você precisa para operar a Formação Δ-11 no VS Code com Claude Code.

---

## COMO TUDO FUNCIONA EM 30 SEGUNDOS

1. Rode o script de instalação no Terminal do macOS (uma única vez)
2. Abra o VS Code com o projeto
3. Abra UMA janela do Claude Code e digite `d11` seguido da descrição do projeto
4. O sistema planeja tudo e te entrega os prompts prontos para cada janela que você precisa abrir
5. Você copia e cola cada prompt em uma nova janela — sem decorar nada
6. Durante o trabalho, você só digita comandos simples como `avançar`, `status`, `aprovar`
7. Quando o contexto de uma janela enche, o próprio agente te entrega o prompt de continuação

**Você NUNCA precisa lembrar o nome de nenhum agente. Eles se identificam sozinhos.**

---

## INSTALAÇÃO (uma vez só)

Abra o Terminal do macOS e execute:

```bash
cd /caminho/para/pasta/dos/arquivos
chmod +x instalar.sh
./instalar.sh
```

O script faz tudo automaticamente:
- Verifica se você tem Git e GitHub CLI instalados (e te diz como instalar se não tiver)
- Cria um repositório privado no seu GitHub
- Faz o primeiro commit e push
- Instala a extensão Live Server no VS Code (para o painel visual)
- Abre o VS Code com o projeto
- Abre o painel visual no navegador

**Para projetos futuros**, use o script `novo-projeto.sh`:

```bash
./novo-projeto.sh ~/projetos/meu-novo-app
```

Isso copia os arquivos da Formação Δ-11 para uma pasta nova, limpa e pronta para um projeto diferente.

---

## PARA COMEÇAR UM PROJETO NOVO

Abra UMA janela do Claude Code e digite:

```
d11

[descreva seu projeto aqui com o máximo de detalhe possível]
```

É só isso. O sistema ativa automaticamente o agente de planejamento, que vai:
- Classificar a complexidade do seu projeto
- Apresentar o plano para você aprovar
- Definir toda a arquitetura técnica
- E no final, te entregar algo assim:

```
PRÓXIMAS JANELAS — Copie e cole cada bloco em uma nova janela:

═══ JANELA 2 ═══════════════════════════
[bloco de texto pronto para colar]
═════════════════════════════════════════

═══ JANELA 3 ═══════════════════════════
[bloco de texto pronto para colar]
═════════════════════════════════════════
```

Você abre as janelas, cola os blocos, e cada agente começa a trabalhar. Pronto.

**OU, ainda mais fácil:** rode o script de disparo automático no Terminal:

```bash
./disparar.sh
```

O script lê os prompts que o ATLAS salvou em `.delta-11/ativacoes/` e abre uma aba do Terminal para cada agente, com o Claude Code já rodando e trabalhando. Todos ao mesmo tempo, sem você copiar e colar nada.

---

## COMANDOS DO DIA A DIA

Depois que os agentes estão trabalhando, você só precisa destes comandos curtos:

| Você digita | O que acontece |
|-------------|---------------|
| `status` | O agente diz o que está fazendo e o que falta |
| `avançar` | Finaliza a tarefa atual e puxa a próxima |
| `pausar` | Salva tudo e para (para quando você precisa sair) |
| `retomar` | Lê onde parou e continua |
| `aprovar` | Você aprova o que o agente apresentou |

Esses comandos funcionam em qualquer janela, com qualquer agente. Você não precisa saber quem é quem.

---

## QUANDO O CONTEXTO DE UMA JANELA ENCHE

Você percebe porque o agente fica lento, se repete, ou esquece coisas. Quando isso acontecer, o próprio agente já sabe o que fazer. Ele vai te entregar algo assim:

```
ATENÇÃO COMANDANTE: meu contexto está quase cheio.
Abra uma nova janela do Claude Code e cole o texto abaixo:
═══════════════════════════════════════════════════

[bloco completo de retomada — você só copia e cola]

═══════════════════════════════════════════════════
```

Você:
1. Copia o bloco
2. Fecha a janela antiga
3. Abre uma nova janela
4. Cola

O agente novo lê onde o anterior parou e continua como se nada tivesse acontecido.

**Se o agente não te entregar o bloco sozinho** (porque travou antes), digite `pausar` — isso força ele a salvar tudo e gerar o bloco de retomada.

**Se a janela travou completamente** e você não consegue nem digitar `pausar`: feche a janela, abra uma nova, e cole isto:

```
Formação Δ-11. Uma janela anterior travou sem gerar prompt de retomada.
Leia o kanban em .delta-11/kanban.md para identificar qual agente estava trabalhando.
Leia o arquivo de estado desse agente em .delta-11/memoria/ para saber onde parou.
Continue o trabalho pendente.
```

---

## O FLUXO COMPLETO

### FASE 1 e 2 — PLANEJAMENTO (1 janela)

```
d11

Quero construir um aplicativo que faz [descrição do projeto]
```

O agente de planejamento classifica, arquiteta, define tudo, e te pede aprovação. Você lê e digita `aprovar`. Ele então te entrega os prompts das próximas janelas.

### FASE 3 — FUNDAÇÃO (1 a 2 janelas)

Você cola os prompts que recebeu na fase anterior. Os agentes criam o banco de dados e a infraestrutura. Quando terminam, te avisam e entregam os prompts da próxima fase.

### FASE 4 — DESENVOLVIMENTO (2 a 7 janelas)

Você cola os prompts. Cada agente trabalha nas suas tarefas. Você acompanha pelo kanban. Digita `avançar` quando quer que um agente pule para a próxima tarefa. Digita `status` quando quer saber como está.

### FASE 5 — TESTES (1 a 2 janelas)

O agente de testes valida tudo. Se houver erros, te avisa e entrega o prompt para ativar o agente de correção.

### FASE 6 — LANÇAMENTO (1 janela)

O agente de testes prepara tudo e te pede aprovação final. Você digita `aprovar` e o deploy acontece.

---

## ACOMPANHAMENTO — O KANBAN

Você tem DUAS formas de acompanhar o progresso:

### OPÇÃO 1 — Preview do VS Code (simples)

1. No VS Code, abra `.delta-11/kanban.md`
2. Pressione `Ctrl+Shift+V` (preview de markdown)
3. Posicione ao lado das janelas do Claude Code
4. A preview atualiza automaticamente quando qualquer agente salva

### OPÇÃO 2 — Painel visual no navegador (recomendado)

1. Instale a extensão "Live Server" no VS Code (se ainda não tem)
2. Clique com botão direito no arquivo `.delta-11/painel.html`
3. Selecione "Open with Live Server"
4. O painel abre no navegador com visual de centro de comando
5. Atualiza automaticamente a cada 10 segundos
6. Você também pode clicar "ATUALIZAR" a qualquer momento

O painel mostra:
- Uma coluna para cada agente ativo com suas tarefas pendentes
- Coluna "FAZENDO" com o que está sendo executado agora
- Coluna "REVISÃO" com tarefas aguardando validação
- Coluna "CONCLUÍDO" com tarefas aprovadas
- Coluna "BLOQUEADO" quando algo trava (com o motivo)
- Barra de progresso geral do projeto
- Cores diferentes para cada agente

---

## QUANTAS JANELAS SIMULTÂNEAS

Você não precisa decidir isso. O agente de planejamento analisa o projeto e te diz exatamente quantas janelas abrir e te entrega cada prompt pronto. A referência geral:

| Complexidade do projeto | Janelas na fase de desenvolvimento |
|------------------------|-----------------------------------|
| Baixa (projeto simples) | 2 a 3 |
| Média | 4 a 5 |
| Alta (projeto complexo) | 5 a 7 |

---

## RESUMO VISUAL DO SEU SETUP

```
╔═══════════════════════════════════════════════════╗
║                    VS CODE                        ║
║                                                   ║
║  ┌──────────┐  ┌──────────┐  ┌──────────────────┐║
║  │ Claude   │  │ Claude   │  │                  │║
║  │ Code     │  │ Code     │  │   kanban.md      │║
║  │          │  │          │  │   (preview)      │║
║  │ Agente 1 │  │ Agente 2 │  │                  │║
║  │ (você    │  │ (você    │  │   Você vê tudo   │║
║  │ colou o  │  │ colou o  │  │   aqui           │║
║  │ prompt)  │  │ prompt)  │  │                  │║
║  └──────────┘  └──────────┘  └──────────────────┘║
║  ┌──────────┐  ┌──────────┐                      ║
║  │ Claude   │  │ Claude   │   Explorador de      ║
║  │ Code     │  │ Code     │   Arquivos           ║
║  │          │  │          │   (código sendo      ║
║  │ Agente 3 │  │ Agente 4 │   gerado)           ║
║  └──────────┘  └──────────┘                      ║
╚═══════════════════════════════════════════════════╝
```

---

## DICAS

- **Tudo começa com `d11` e a descrição do projeto.** A partir daí, o sistema te guia.
- **Você nunca precisa decorar nomes de agentes.** Os prompts são sempre entregues prontos para copiar e colar.
- **Se está confuso**, digite `status` em qualquer janela.
- **Se quer ver o panorama geral**, abra o kanban.md.
- **Se uma janela travou**, feche e abra uma nova. Se o agente não te deu o prompt de retomada antes de travar, cole na nova janela: "Formação Δ-11. Uma janela travou. Leia o kanban e continue o trabalho pendente."
