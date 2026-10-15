# CHANGELOG — Formação Δ-11

**O que é:** documento único que conta a história das versões do Sistema Δ-11 em formato narrativo (por que, o que, como testar). Complementa o git log — **não substitui**. Git é fonte da verdade de mudanças atômicas; este arquivo é fonte da verdade de ARQUITETURA e DECISÃO.

**Onde vive:** `.delta-11/CHANGELOG.md` da fonte oficial (`~/Documents/VSCODE/Formacao-delta-11`) — levado a todos os projetos do registro central (`~/.delta-11-registry.json`) pelo `sincronizar.sh`, que roda a partir da fonte oficial.

**Quem lê:**
- O **comandante humano** (Rafa) — para entender o que mudou entre versões sem ler 50 commits.
- Um **novo agente** que acabou de ser ativado — para entender o estado atual do sistema sem ler 50 commits.
- O **próximo mantenedor** (qualquer pessoa que herdar o sistema) — para entender por que decisões foram tomadas.

**Quem escreve:**
- Quem mantém o sistema Δ-11, na fonte oficial, ao fechar uma versão (cria a entrada).
- Dentro de um projeto, os agentes só LEEM este arquivo: ele é de sistema e o `sincronizar.sh` o sobrescreve.

**Regra de manutenção:**
- Cada entrada vira IMUTÁVEL depois de publicada (estilo ADR). Correções vão em "ADIÇÕES POSTERIORES" no fim.
- Formato padronizado: **Por que existe** → **O que mudou** → **Como testar** → **Commits desta versão**.

---

## v6.4 (2026-10-15) — Velocidade

### Por que essa versão existe

O Rafa notou que a v6.x é muito mais lenta que a v3 (que abria até 5 agentes ao mesmo tempo). A medição dos
registros reais do salvahacks (14/10, v6.2) mostrou: nas fases de planejamento e papelada, **38,7% do tempo ativo
sem nenhum agente trabalhando e média de 0,98 agente por vez**; no dia inteiro, 13,2% parado e média 1,88. As causas
estavam no texto do CRONOS, não no Claude Code:
- conta-gotas da Regra 6 ("lance 3, AGUARDE 1, lance 2…");
- tarefa grande virando "2 ondas em série";
- revisores de fase em primeiro plano, um a um;
- uma revisão do SHIELD por tarefa, travando a próxima;
- papelada completa das Fases 3.5 e 4.5 em todo ciclo.

### O que mudou (decisões V1–V12)

| Código | Decisão |
|---|---|
| V1 | Onda inteira disparada na MESMA mensagem; fila por vaga (quando um termina, o próximo sai na hora) |
| V2 | `paralelo_max` = 5 (era 3) |
| V3 | Tarefa grande vira sub-tarefas IRMÃS paralelas, não ondas em série |
| V4 | `brief_max_tokens` = 4000 (era 2000); juntar trabalho da mesma área e do mesmo agente |
| V5 | Em série só o mesmo arquivo ou dependência declarada; mesma zona com arquivos diferentes roda em paralelo |
| V6 | 3.5 + 3.7 juntos em segundo plano; UM SHIELD por onda (ou um por zona, em paralelo), veredito por tarefa |
| V7 | Pipeline: a onda N+1 independente começa enquanto o SHIELD revisa a onda N; merge só das APROVADAS |
| V8 | Revisores de fase (fresh-reviewer, cold-start-tester, qa-ui-tandem) juntos, em segundo plano |
| V9 | Ciclo leve: do Ciclo 2 em diante, Fases 3.5 e 4.5 = checklist de 1 página do ciclo atual (obrigatório; documentos de ciclos anteriores não substituem); 2.3 e 2.4 só para o que é novo |
| V10 | As 2 semanas da Fase 7 correm em paralelo com o ciclo seguinte; só o selo final exige o teste supremo |
| V11 | O SHIELD reprova código e contrato, nunca a redação de documento |
| V12 | `ferramentas/medir-paralelismo.py`: mede tempo parado, média e pico de agentes simultâneos |

Também: o `dispatch_target` (vigias) identifica o sub-agente certo; o prompt do contract-tester/build-validator abre
com "Sub-agente:" (antes "Agente: X" fazia o pre-despacho aplicar o limite de executor por engano).

### Teste ao vivo (Claude Code 2.1.299, 2026-10-15)

O mesmo pedido (5 tarefas independentes reais: criar função + teste e rodar `node`), um Claude Code no papel de
CRONOS, com a Regra 6 de cada versão, medido pela V12:

| | v6.3 (regra antiga) | v6.4 |
|---|---|---|
| Pico de agentes simultâneos | 3 | **5** |
| Média de agentes simultâneos | 0,73 | **1,05** |
| Tempo total | ~1 min 19 s | **57 s** |

(No teste, cada tarefa dura ~15 s e o CRONOS leva ~30 s lendo as instruções; em ondas reais, com tarefas de minutos,
o ganho do disparo único cresce: 5 tarefas de 15 min ≈ 2 rodadas na v6.3 contra 1 na v6.4.)

### Como testar

```bash
HOME="$(mktemp -d)" bash .delta-11/tests/rodar-todos.sh        # esperado: 80/80 OK
python3 .delta-11/ferramentas/medir-paralelismo.py <projeto> --desde <ISO> --sem-processos-separados --sem-aninhados
```

### Pendências conhecidas
- Medir uma fase de construção real inteira na v6.4 (salvahacks, depois da troca) e comparar com os números de 14/10.
- N-011 (agentes visíveis) e N-012/N-013 (metodologia) continuam abertos.

---

## v6.3 (2026-10-14) — Correção Geral

**Versão anterior:** v6.2 (2026-08-11) — Behavioral Hooks (commit `35f6ebd`).
**Autor:** Comandante Rafa + 11 frentes de correção em paralelo (Claude Code), uma por área do sistema.
**Status:** Branch `v6.3-correcao-geral`, montada a partir de 11 branches de área (`v6.3/01-vigias-config` a
`v6.3/11-docs-finais`). Base das correções: o caderno `MELHORIAS-E-PROXIMAS-IMPLEMENTACOES.md` (itens C-001 a C-184)
e as 39 decisões canônicas (D1–D39, tabela abaixo).

### Por que essa versão existe

Em 2026-10-14 foi feita a **leitura completa dos 251 arquivos** do sistema. Ela achou **184 problemas**; conferidos
contra a fonte oficial, **165 ainda persistiam** (8 já estavam corrigidos na fonte, 6 corrigidos em parte e 5 não
eram verificáveis). O manual, os operativos, os protocolos, os vigias e os scripts se contradiziam: modo padrão do
Selo, CRONOS com e sem worktree, `-estado.md` × `-produto.md`, quem escreve o kanban, quem dispara quem, quantas
fases existem.

**O achado mais grave:** nenhum vigia Python bloqueava nada. Todo comando de vigia estava registrado como
`python3 vigia.py || python vigia.py`. Quando o vigia mandava bloquear (código de saída 2), o `||` rodava a segunda
metade; no macOS não existe o comando `python`, a segunda metade terminava com "comando não encontrado" (código
127), e o Claude Code trata esse código como erro sem bloqueio. Resultado: toda trava "técnica" das v6.0 a v6.2
deixava a ação passar. Além disso, o modelo de configuração da cópia `sistema-atual` (e os projetos criados a partir
dela) só ligava **9 vigias antigos**; na fonte oficial, o modelo ligava os 32, todos com `|| python`, e o
`.claude/settings.json` do próprio repositório ligava só 15.

A v6.3 não acrescenta metodologia nova: ela **corrige** o que existia, na direção de uma única regra para cada
assunto (as decisões D1–D39). Primeiro os vigias deixaram de bloquear por engano; só então o `|| python` saiu, no
mesmo merge (D37).

### O que mudou

#### Vigias automáticos (hooks) — áreas 01 e 02

- **Registro único dos 34 vigias** (32 antigos + `abrir-painel.sh` + `fim-subagente.sh`) nos eventos certos, todos
  com `"$CLAUDE_PROJECT_DIR"` e **sem `|| python`**, no modelo `templates/settings-hooks.json` e no
  `.claude/settings.json` do repositório (C-001 a C-011, C-040; D25).
- Tempos-limite em segundos (5 s; 120 s para `validar-contratos-fim-fase` e `validar-deploy`) (C-005; D30).
- Vigias JS e Shell gravam na **pasta principal** do projeto, mesmo quando o agente trabalha numa worktree; formato
  único de linha no `activity-log.md`; travas por agente (C-006, C-008, C-022, C-032; D25).
- Sinais de vida dos agentes na pasta principal; o evento `Stop` não "mata" mais o agente a cada resposta; o painel
  abre sozinho no início da sessão (C-007, C-031, C-033, N-001, N-002; D27, D28).
- Utilitário comum dos vigias Python e limites configuráveis em `.delta-11/.config-limites.json` (C-006, C-015 a
  C-017, C-184; D36).
- Vigias do kanban sem bloqueio falso e com prova real: `shield-aprovado.py` só aceita `APROVADO`, `forca-despacho.py`
  aceita o registro do `SubagentStop` (C-020, C-024, C-026 a C-029, C-036, C-039, C-042, C-043; D32, D33).
- Vigias da memória e do project-core: `regenerar-contratos.py` não dispara mais `claude --print` escondido, só grava
  o aviso `ativacoes/contratos-desatualizados.txt` (C-021, C-023, C-025, C-035, C-037, C-038, C-160; D6, D31).
- Demais vigias sem bloqueio falso: `localhost` e URLs entre aspas válidas, "não faça deploy" não dispara o vigia de
  deploy, erro interno não libera em silêncio (C-016, C-018, C-019, C-030, C-034, C-040, C-041, C-044, C-045, C-181;
  D34, D35).
- Testes dos vigias JS/Shell, do registro e dos 25 vigias Python, sempre em projeto temporário (C-126 a C-128, C-130).

#### Scripts — área 03

- `novo-projeto.sh`: projeto novo nasce limpo (sem herdar kanban e memória de outro projeto), protegido pelo
  `.gitignore` e anotado no registro central (C-048, C-049, C-053, C-147, C-150).
- `sincronizar.sh`: seguro (nunca segue com origem vazia), completo, não sobrescreve o `.modo-selo` de quem já tem um,
  não trata cópias do sistema como projeto e apaga dos projetos só o que está em `removidos.txt` (C-051 a C-058,
  C-147, C-150; D1).
- `instalar.sh`: protege segredos no `.gitignore`, liga o monitor com o caminho real da pasta e pede confirmação antes
  de publicar no GitHub (C-062, C-147, C-182).
- `monitor-delta11.sh`: cada projeto recebe só o próprio status (`monitor-status.json` + `monitor-data.js`), sem
  alarme repetido, e projeto abandonado não é chamado de "autônomo" (C-062, C-064, C-065, C-129, C-149; D28).
- `vigilante.sh` avisa o CRONOS (`ativacoes/aviso-vigilante.txt`) em vez de chamar o `disparar.sh`, que não existe
  mais; `task-done.sh` não cria `.txt` de revisão (C-053, C-066, C-067; D3, D9).
- `.gitignore` da fonte, modo do selo `automatico` na distribuição e status do monitor fora do git (C-148, C-149,
  C-052; D1).

#### Operativos (ATLAS, CRONOS e executores) — áreas 04 e 05

- **CRONOS orquestrador único:** roda sempre sem worktree (`name: "cronos"`), dispara executores, SHIELD, SCOUT,
  sub-agentes e o ATLAS; só ele escreve o kanban; fala com o comandante só nas 3 situações (C-071 a C-076, C-080 a
  C-082, C-086, C-089, C-098, C-109, C-140, C-180; D2, D4, D5, D10, D26).
- **ATLAS dispara só o CRONOS**, sem worktree, e não escreve o kanban (C-072, C-074, C-078, C-080 a C-082, C-087,
  C-089, C-090, C-109; D3, D5).
- **Rotina única de início e finalização** nos 7 executores (0 → 0.VW → 0.3 → 0.5; 1a → 1b → 3.4 → 3.5 → 3.7 → 3.8 →
  3.9) (C-077, C-079 a C-085, C-087, C-093, C-098; D9, D11, D12).
- SHIELD com as fases certas e o registro `APROVADO` / `REPROVADO` (C-078, C-087, C-088; D33).
- Perfis completos com modelo, isolamento, fatias do project-core, ferramentas e base (C-139, C-180; D6, D26).
- Bloco comum dos 10 operativos sem "própria janela" e com o CRONOS orquestrador (C-098, C-099; D3).

#### Manual central (CLAUDE.md) — área 08

- Alinhado às decisões canônicas: modo `automatico` padrão, 3 situações, 13 fases, 6 Mecanismos (M1, M2, M3, M4, M4b,
  M5), lista dos 34 vigias, 17 regras invioláveis, rotina única de tarefa e fonte oficial (C-003, C-012 a C-014,
  C-053, C-060, C-071, C-073, C-079 a C-085, C-091, C-092, C-094, C-098, C-110, C-114, C-140, C-143, C-156 a C-158,
  C-160, C-181, C-182, C-184, N-001, N-002).

#### Protocolos — área 09

- `fluxo-zero-ao-lancamento.md` com as 13 fases, os Dias certos, a fonte oficial e o papel de cada executor nas Fases
  3.5, 4.5 e 7 (C-060, C-087, C-103, C-104; D16).
- `comunicacao.md` reescrito; `correcao-de-erros.md` com as 3 tentativas da v6.3 e o log de falhas do SHIELD no formato
  único (C-097, C-107; D23, D35).
- `classificacao.md` com régua única 5–15 (C-089; D14); `regras-inviolaveis.md` como lista oficial das 17 (C-092; D15).
- `regras-codigo.md` com a tabela única de tempos-limite e o formato único de erro (C-105; D13, D19).
- `fase-ritmo`, `fase-consciencia`, `fase-descanso` (sem "Fase 7.5"), `ciclo-interno-7d`, `merge-guiado-contratos`,
  `sub-agentes.md` e `validacao-screenshots` coerentes com a v6.3 (C-100, C-101, C-103 a C-106, C-117, C-159, C-179).

#### Painel — área 07

- Sinais de vida pelo `pulsos-data.js` (inclusive de quem está em worktree), alertas do vigia pelo `monitor-data.js`
  e selo honesto: sem sinal de um agente ativo = amarelo **"Monitoramento parcial"**, nunca "Seguro fechar" (C-140 a
  C-145, N-002; D28).
- Modelos do quadro com todos os campos, só o CRONOS escreve e checklist por squad (C-102, C-109, C-120, C-140, C-183;
  D10, D39).
- Imagem de fundo e figuras órfãs removidas; `CHANGELOG-painel-v5.1.md` corrigido (C-146).

#### Sub-agentes, bases de conhecimento e modelos — área 10

- Sub-agente `qa-ui-tandem` criado; `contract-tester` gera E roda os testes; `impact-mapper` só a pedido do CRONOS
  (C-038, C-094 a C-096, C-108, C-111, C-121, C-132, C-175; D12, D31).
- Bases: OWASP oficial do SHIELD declarada, CVEs reais, caminhos certos das skills, Supabase com `@supabase/ssr` e
  `getUser()`, erro único 400, tempos D19, nomes em inglês (C-105, C-107, C-169 a C-178; D13, D19, D20).
- Modelos: mini-plano único com ciclo interno, Dia 1 no PRD e no project-core, `fase-luz` criado, abertura de fase em
  `memoria/`, linha `autocritica:` e seção `PROPOSTAS PARA O PROJECT-CORE` no modelo de produto (C-095, C-096, C-101,
  C-112, C-113, C-118, C-119, C-122, C-173, C-174; D7, D8, D17).
- MCP com versões fixas: `@supabase/mcp-server-supabase@0.13.0` e `context7@4.1.1` (C-151).
- A auditoria que fundamentou a v6.0 passou a ser versionada (C-115).

#### Testes e ferramentas — área 06

- Pasta `tests/framework/` com funções comuns; o `rodar-todos.sh` da v6.3 roda TODAS as pastas (inclusive
  `operativos/`, que o executor antigo pulava), todos os testes antes do resumo e nada em `/tmp` (C-070, C-131; D21).
- Testes de documento conferem os conceitos da v6.3, não frases antigas (C-124 a C-126, C-128).
- Ferramentas dos agentes sem erro de sintaxe, sem `eval`, sem `/tmp` e sem a saída "0\n0" (C-133 a C-138).

#### Integração e documentos finais — área 11

- Pedidos cruzados entre áreas resolvidos na integração (formato do kanban que os vigias leem, eventos dos vigias,
  caminhos da fonte, aviso do vigilante, `painel-v4` removido).
- Este CHANGELOG corrigido (C-164 a C-168, ver ADIÇÕES POSTERIORES), `GUIA-DO-COMANDANTE.md` reescrito para o
  comandante não técnico (C-154) e `README.md` atualizado (C-155).

### Decisões canônicas (D1–D39)

Quando dois textos do sistema se contradizem, vale a decisão desta tabela.

| Código | Decisão |
|---|---|
| D1 | Modo do Selo: padrão `automatico`; `modo manual` é opcional; o `sincronizar.sh` nunca sobrescreve o `.modo-selo` de um projeto. |
| D2 | CRONOS sempre sem worktree (`name: "cronos"`), inclusive na auto-retomada; executores com `isolation: "worktree"`; SHIELD revisor sem worktree. |
| D3 | Zero copiar-e-colar: nenhum texto pede ao comandante para abrir janela ou sessão, colar bloco ou rodar disparo manual; todo disparo é do CRONOS. |
| D4 | O comandante só é chamado em 3 situações (negócio/escopo, credencial/conta/pagamento/CAPTCHA, perda de dados ou publicação externa) e, em `modo manual`, na fronteira de fase. |
| D5 | O CRONOS dispara executores, SHIELD, SCOUT, sub-agentes e o ATLAS; o ATLAS dispara só o CRONOS; executores avisam o CRONOS por SendMessage. |
| D6 | Executores leem só as fatias de `memoria/project-core/` do seu papel; ATLAS, CRONOS, SHIELD, SCOUT e sub-agentes podem ler o project-core inteiro. |
| D7 | Só o ATLAS escreve o project-core e as fatias; os outros propõem em `PROPOSTAS PARA O PROJECT-CORE`; abertura de fase em `memoria/CRONOS-abertura-fase-N.md`. |
| D8 | Estado do agente = `[NOME]-produto.md` (≤500 tokens para executores) + `[NOME]-historia.md`; o `-estado.md` é legado, só leitura. |
| D9 | Rotina única de tarefa: início 0 → 0.VW → 0.3 → 0.5; fim 1a → 1b → 3.4 → 3.5 → 3.7 → 3.8 (SendMessage ao CRONOS) → 3.9. |
| D10 | Só o CRONOS escreve `kanban.md` e `kanban-data.js`. |
| D11 | Todos os executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SCOUT) passam pela revisão do SHIELD. |
| D12 | O contract-tester gera E roda os testes de contrato do que mudou; sem data no índice gerado. |
| D13 | Erro de validação = HTTP 400, formato único `{ "error": { "code", "message", "details" } }`. |
| D14 | Complexidade: 5 critérios de 1 a 3 pontos (soma 5–15); BAIXA 5–8, MÉDIA 9–12, ALTA 13–15. |
| D15 | Regras invioláveis: a lista oficial é `protocolos/regras-inviolaveis.md` (17 regras). |
| D16 | 13 fases (0, 1, 2, 2.3, 2.4, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7) com o mapa de Dias; teste supremo do Dia 7 = 2 semanas. |
| D17 | Mini-plano `planos/[AGENTE]-plan.md`, um por agente, 6 seções + checklist do ciclo interno; histórico em `planos/arquivo/`. |
| D18 | SendMessage funciona sem Agent Teams; os arquivos continuam sendo a fonte de verdade (mensagem é aviso, não registro). |
| D19 | Tempos-limite: banco 5 s, API externa 10 s, chamada interna 3 s; 3 novas tentativas; circuit breaker abre após 5 falhas e fecha após 60 s. |
| D20 | Nomes em código em inglês, sem abreviação; textos para humanos em português. |
| D21 | Nada em `/tmp`: arquivos temporários em `.delta-11/scratch/` (expiram em 7 dias). |
| D22 | Mecanismos da Criação: M1, M2, M3, M4, M4b e M5; não existe "Mecanismo 6". |
| D23 | 3 falhas: o SCOUT para e avisa o CRONOS, que dispara um SCOUT novo; 6 falhas: o CRONOS dispara o ATLAS. |
| D24 | project-core = verdade do contrato; migrations = verdade do banco implementado; divergência = bug para o ATLAS. |
| D25 | Vigias com `"$CLAUDE_PROJECT_DIR"`, sem `\|\| python`; arquivos compartilhados na pasta principal; formato único do activity-log. |
| D26 | O CRONOS passa `model` no disparo a partir de `perfis/[AGENTE].json` (opus: ATLAS, CRONOS, SHIELD; sonnet: os demais). |
| D27 | Painel abre sozinho (Passo 0 e `SessionStart`), no máximo uma vez a cada 8 h, sem nunca falhar a sessão. |
| D28 | Sinais das worktrees em `pulsos-data.js`, alertas em `monitor-data.js`; painel lê tudo por `<script src>`; `inicio` em ISO completo. |
| D29 | Tudo o que foi alterado marca v6.3 (data 2026-10-14). |
| D30 | Tempo-limite dos vigias em segundos: 5 s; 120 s para `validar-contratos-fim-fase` e `validar-deploy`. |
| D31 | `regenerar-contratos` só grava o aviso `contratos-desatualizados.txt`; impact-mapper só a pedido; aviso ao agente `contrato-alterado-[AGENTE].txt`. |
| D32 | O `SubagentStop` grava `logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log`; o `forca-despacho.py` aceita esse registro (até 4 h). |
| D33 | O SHIELD grava `[SHIELD] APROVADO T-XXX [AGENTE]` ou `REPROVADO ... motivo`; o `shield-aprovado.py` só aceita `APROVADO`. |
| D34 | URLs: `localhost`, `127.0.0.1` e `*.local` são válidos; aspas e crases em volta são ignoradas. |
| D35 | Falhas do SHIELD em `logs/sub-agentes/shield-falhas.log`, no formato `[ISO] [AGENTE] FAIL T-XXX motivo`. |
| D36 | Limites configuráveis em `.delta-11/.config-limites.json` (brief 2.000, produto 500, paralelo 3, janela 4 h, trava 2 h). |
| D37 | Ordem segura: consertar os bloqueios falsos ANTES de tirar o `\|\| python`, tudo no mesmo merge. |
| D38 | Memória entre projetos em `~/.delta-11/aprendizados-entre-projetos.md`: o ATLAS lê nas Fases 0 e 2; o CRONOS acrescenta 3 a 5 lições. |
| D39 | O `kanban.md` modelo tem "Checklist por squad" (Interface, Servidor, Qualidade). |

### Como testar

```bash
# Suíte completa, com uma pasta pessoal temporária (nenhum teste toca no seu $HOME real)
HOME="$(mktemp -d)" bash .delta-11/tests/rodar-todos.sh
# Esperado: "Resultado: X/X OK" no fim. Quem falhar deixa a saída em
# .delta-11/scratch/AAAA-MM-DD-testes-delta11/ (nada em /tmp — D21).

# Só uma pasta de testes
HOME="$(mktemp -d)" bash .delta-11/tests/rodar-todos.sh --pasta hooks

# Testes dos documentos desta área
bash .delta-11/tests/templates/changelog.test.sh
bash .delta-11/tests/protocolos/zero-copiar-colar-d3.test.sh
```

Resultado na integração final: **74/74 OK**.

### Teste ao vivo no Claude Code (2.1.299, 2026-10-14)

Projeto descartável criado com o `novo-projeto.sh` da v6.3; `claude -p` de verdade dentro dele:

1. **Bloqueio real:** pedir a criação de `docs/configuracao-servico-teste.md` → o `pre-criacao-arquivo.py` BLOQUEOU,
   o arquivo não foi criado, e o activity-log registrou no formato único. (Na v6.2 isso passava, por causa do `|| python`.)
2. **Achado e corrigido — `guarda-worktree.py` (caso C):** o Claude Code cria as worktrees DENTRO do repo principal
   (`.claude/worktrees/agent-x/`); o vigia tratava o arquivo da própria cópia como "código da main" e bloqueava o
   executor. Corrigido e coberto por teste novo (o teste falha com o vigia antigo).
3. **Achado e incorporado — regra do Claude Code:** um sub-agente com `isolation: "worktree"` NÃO consegue usar
   Write/Edit fora da própria worktree ("This agent is isolated in the worktree…"). Por isso os executores gravam ACK,
   travas, `-produto.md`, `-historia.md`, autocrítica e logs da pasta principal **pelo Bash com caminho absoluto**
   (regra no CLAUDE.md e no prompt de disparo do CRONOS).
4. **Sinais das worktrees (N-002):** com o ACK gravado pelo Bash, o `heartbeat.sh` registrou o pulso do FRONT na pasta
   principal com o caminho da worktree; o `fim-subagente.sh` gravou o log do SubagentStop e limpou o sinal ao terminar.

### Pendências conhecidas (ficam para depois da v6.3)

- **SendMessage entre sub-agentes nomeados:** não testado ao vivo (exige uma sessão longa com o CRONOS ativo).
- **N-004 — velocidade:** recuperar a velocidade e a visibilidade da versão antiga sem perder qualidade.
- **N-011 — agentes visíveis:** piloto com recursos oficiais do Claude Code para o comandante ver cada agente
  trabalhando.
- **N-012 / N-013 — metodologia:** realinhar o Delta-11 às 7 Camadas da Criação a partir dos 4 textos de estudo do
  Rafa, depois de decidir qual é a fonte oficial da metodologia. As 13 fases e o mapa de Dias da v6.3 (D16) valem até lá.

### Commits desta versão

Lista completa: `git log --oneline 35f6ebd..v6.3-correcao-geral`. Por área (assunto `fix(v6.3 <área>)`):

- **vigias-config (01):** `4cc0a42`, `59908ec`, `a30095b`, `0bdbcd1`
- **vigias-python (02):** `778c0c4`, `c4dc0b0`, `268bb22`, `17302c1`, `9dd1f33`
- **scripts (03):** `530c816`, `710d80f`, `50c0bb2`, `b4c13b9`, `adc9201`, `4059b53`, `ad8bf3c`, `c4411f9`
- **atlas-cronos (04):** `a127b27`, `6db1ef2`
- **executores (05):** `1e086cc`, `75a71e3`, `365a5c4`, `9823b31`
- **testes e ferramentas (06):** `a65a514`, `e17f15a`, `2e33db8`
- **painel (07):** `58d3d00`, `5b6fd35`, `24c4e97`
- **claude-md (08):** `f877c53`, `80ae1ae`
- **protocolos (09):** `f4254b2`, `b69d104`, `0d1a4dc`, `79ca9f9`, `822cb56`, `3493ec9`, `4f3e75e`, `2ace96f`,
  `7c7e28f`, `64532db`, `0b34a6d`, `0fe84c3`, `1b5a172`, `45f7e68`, `c257995`, `552b137`
- **sub-agentes, bases e modelos (10):** `90456e9`, `ef53c17`, `329edca`, `c8b7e93`, `fafef61`, `c331448`,
  `9da58d2`, `63d3fce`, `a3b63ec`
- **base e integração:** `8e5e606` (auditoria da v6.0 versionada), `a1724ce`, `fd73ab7`
- **documentos finais (11):** CHANGELOG, GUIA-DO-COMANDANTE e README (commits `fix(v6.3 docs)`)

---

## v6.2 (2026-08-11) — Behavioral Hooks: Fechamento da Auditoria 2026-08-11

**Versão anterior:** v6.1 (2026-07-12) — Dispatch Autônomo (Lovable).
**Autor:** Comandante Rafa + auditora de campo (D-scan completo de 11 furos comportamentais).
**Status:** Branch `v6.2-behavioral-hooks` com 6 commits granulares + 1 de consolidação (E12). Suíte 45/45 OK no merge (44 antes do teste consolidado).

### Por que essa versão existe

Pós-deploy da v6.0 + v6.1, a auditoria 2026-08-11 (sub-agente em campo) identificou **11 furos comportamentais** que nenhuma das versões anteriores cobria. A causa raiz é a mesma da auditoria de 2026-07-10: **"proteção que depende de agente obedecer prompt NÃO é proteção; toda regra crítica precisa de hook técnico"**.

Os 11 furos são **versão-agnósticos** (nem v5.4 nem v6.0+v6.1 previnem). A v6.2 implementa **11 hooks novos** que cobrem todos.

### Commits desta versão (branch `v6.2-behavioral-hooks`)

1. `feat(v6.2 Hook 1)`: anti-autocompact.py + correções de regex em testes pré-existentes
2. `feat(v6.2 Hook 2)`: forca-despacho.py — BLOQUEIA CONCLUIDO sem sub-agente
3. `feat(v6.2 Hook 3)`: produto-atualizado.py — BLOQUEIA CONCLUIDO se [AGENTE]-produto.md desatualizado
4. `feat(v6.2 Hook 4)`: anti-stash.py — BLOQUEIA CONCLUIDO com stash ativo
5. `feat(v6.2 Hooks 5+6+7)`: shield-aprovado + urls-validas + contratos-minimos
6. `feat(v6.2 Hooks 8+9+10+11)`: brief-preservado + topologia-deploy + worktree-prune + 3-tentativas-shield
7. `feat(v6.2 E12)`: CHANGELOG + CLAUDE.md cross-ref + teste consolidado (`v62-consolidado`)

### Os 11 furos corrigidos

| Furo | Hook | Descrição | Severidade |
|------|------|-----------|------------|
| 1 | anti-autocompact | Autocompact matou 5 agentes (contexto > 85%) | 🔴 |
| 2 | forca-despacho | Zero disparo formal de sub-agentes | 🔴 |
| 3 | produto-atualizado | FRONT/PIXEL/VAULT-produto.md desatualizados | 🔴 |
| 4 | shield-aprovado | Onda C sem autocrítica/SHIELD | 🔴 |
| 5 | anti-stash | BACK ignorou 67 contract tests via stash | 🔴 |
| 6 | 3-tentativas-shield | 3 tentativas SHIELD Onda D morreram | 🔴 |
| 7 | contratos-minimos | ATLAS não formalizou contratos M2 | 🟠 |
| 8 | brief-preservado | Brief inicial do CRONOS sumiu | 🟠 |
| 9 | topologia-deploy | Deploy assumido monolítico (worker ok, painel 404) | 🟠 |
| 10 | urls-validas | URLs erradas no brief de retomada | 🟡 |
| 11 | worktree-prune | 8 worktrees órfãs sem limpeza | 🟠 |

### Como testar

```bash
# Suite completa automatizada
bash .delta-11/tests/rodar-todos.sh
# Esperado: 45/45 OK (era 33/33 na v6.1; +11 testes de regressão + 1 teste consolidado)

# Testes especificos por hook
bash .delta-11/tests/hooks/anti-autocompact.test.sh
bash .delta-11/tests/hooks/forca-despacho.test.sh
bash .delta-11/tests/hooks/produto-atualizado.test.sh
bash .delta-11/tests/hooks/anti-stash.test.sh
bash .delta-11/tests/hooks/shield-aprovado.test.sh
bash .delta-11/tests/hooks/urls-validas.test.sh
bash .delta-11/tests/hooks/contratos-minimos.test.sh
bash .delta-11/tests/hooks/brief-preservado.test.sh
bash .delta-11/tests/hooks/topologia-deploy.test.sh
bash .delta-11/tests/hooks/worktree-prune.test.sh
bash .delta-11/tests/hooks/3-tentativas-shield.test.sh
```

### Métricas de mudança

- **11 hooks novos** implementados (anti-autocompact, forca-despacho, produto-atualizado, anti-stash, shield-aprovado, urls-validas, contratos-minimos, brief-preservado, topologia-deploy, worktree-prune, 3-tentativas-shield)
- **12 testes** adicionados em `tests/hooks/` (11 de regressão + `v62-consolidado`)
- **+ 5 correções de regex** em testes pré-existentes que tinham regex mal-formado para UTF-8
- **Suíte:** 33/33 → 45/45 OK (o executor da época não rodava a pasta `tests/operativos/`)
- **Cobertura comportamental:** os 11 furos identificados pela auditoria 2026-08-11 agora têm **bloqueio técnico via hook Python** (não dependem de agente obedecer prompt)

### Cross-reference

- **Auditoria 2026-08-11 (D-scan completo):** os 11 furos versão-agnósticos
- **v6.0 (Metodologia Gênesis):** Fases 3.5/4.5/7 + Princípio 3 (Contraposição) + Verificação Retroativa
- **v6.1 (Lovable):** CRONOS auto-dispatch + retry SDK + sub-agente QA via Tandem Browser

A v6.2 fecha o **último eixo de auditoria** da D-11: a auditoria de 2026-08-11 confirma que 10/11 furos são versão-agnósticos. A v6.2 é a **resposta técnica a todos eles** com hooks Python que verificam **conformidade comportamental** (não apenas conformidade de arquivos).

---

## v6.1 (2026-07-12) — Dispatch Autônomo: D-11 vira Lovable (Nível 3)

**Versão anterior:** v6.0 (2026-07-12) — Alinhamento com Metodologia Gênesis.
**Autor:** Comandante Rafa + sub-agente de auditoria (D-scan completo).
**Status:** Branch `v6.1-dispatch-nativo` com 9 commits granulares + 1 de consolidação (E10-12). Suíte 33/33 OK no merge (32 antes do teste consolidado).

### Por que essa versão existe

Pós-deploy da v6.0, o comandante reportou problema crítico: o D-11 estava agindo como **supervisor**, pedindo ao humano para copiar prompt, abrir nova janela, rodar bash — em vez de ser **Lovable** (autônomo, dispara e mostra resultado). Auditoria completa via sub-agente identificou **14 anti-padrões** em 6 categorias, distribuídos em 15+ arquivos.

A v6.1 corrige os 14. O sistema agora:
- Auto-dispatcha via `Agent tool` sem pausar para perguntas bloqueantes
- CRONOS se auto-retoma (não depende de humano abrir nova sessão)
- Sub-agente QA executa Selo Experiencial via Tandem Browser MCP (humano só vê relatório PASS/FAIL)
- Modo padrão é `automatico` (era `manual`)
- Fallbacks manuais só após 3 retries do Agent tool (eram caminho primário)

### Commits desta versão (branch `v6.1-dispatch-nativo`)

1. `fix(v6.1 AP5)`: remove "Gere prompt do SHIELD em arquivo" de 7 operativos
2. `fix(v6.1 AP3)`: ATLAS — remove "comandante só precisa copiar e colar"
3. `fix(v6.1 AP1+AP6)`: CRONOS auto-retomada — não pede mais humano
4. `fix(v6.1 AP4)`: remove CHECKPOINTS DE APROVAÇÃO COM O COMANDANTE
5. `fix(v6.1 AP2)`: fallback SDK agora tenta 3x antes de escalar humano
6. `fix(v6.1 AP7)`: SCOUT usa SendMessage ao CRONOS (não humano-colar)
7. `fix(v6.1 AP8)`: deleta disparar.sh (AppleScript legacy)
8. `fix(v6.1 AP11+13+14)`: vigilante + selo + linguagem "rode manualmente"
9. `fix(v6.1 AP9+10+12)`: defaults invertidos + auto-abertura plataforma-cross
10. `feat(v6.1 E10+11+12)`: CHANGELOG + CLAUDE.md cross-ref + teste consolidado (`dispatch-v61-consolidado`)

### Anti-padrões corrigidos

| AP | Arquivo | Severidade | Resumo |
|----|---------|-------------|--------|
| AP#5 | 7 operativos | 🔴 | Removido "Gere prompt do SHIELD em arquivo" |
| AP#3 | ATLAS.md | 🔴 | Removido "comandante só precisa copiar e colar" |
| AP#1 | CLAUDE.md | 🔴 | CRONOS pode auto-dispensar |
| AP#6 | CRONOS.md | 🔴 | CRONOS auto-retoma via Agent tool |
| AP#4 | CRONOS.md | 🟠 | Removidos 3 CHECKPOINTS bloqueantes |
| AP#2 | CLAUDE.md | 🟠 | Cadeia de retry antes de escalar humano |
| AP#7 | SCOUT.md | 🟠 | SendMessage ao CRONOS em vez de humano-colar |
| AP#8 | disparar.sh | 🟠 | Script AppleScript deletado |
| AP#11 | vigilante.sh | 🟠 | Não instrui humano a rodar disparar.sh |
| AP#13 | selo-experiencial | 🟠 | Automatizado via sub-agente QA + Tandem Browser |
| AP#14 | SHIELD/ATLAS | 🟠 | "Rode via Bash tool" em vez de "Rode manualmente" |
| AP#9 | CRONOS.md | 🟡 | Default `automatico` (era `manual`) |
| AP#10 | CLAUDE.md | 🟡 | Painel.html auto-aberto |
| AP#12 | instalar.sh | 🟡 | Cascata open/xdg-open/start antes de pedir humano |

### Como testar

```bash
# Suite completa automatizada
bash .delta-11/tests/rodar-todos.sh
# Esperado: 33/33 OK (os 4 testes de tests/operativos/ rodavam só um a um)

# Testes especificos de dispatch autonomo (v6.1)
bash .delta-11/tests/operativos/dispatch-ap5.test.sh   # 7 operativos sem janela-SHIELD
bash .delta-11/tests/operativos/dispatch-ap3.test.sh   # ATLAS sem copia-cola
bash .delta-11/tests/operativos/dispatch-ap4.test.sh   # CRONOS sem CHECKPOINTS
bash .delta-11/tests/protocolos/dispatch-ap1-ap6.test.sh   # CRONOS auto-retoma
bash .delta-11/tests/protocolos/dispatch-ap2.test.sh   # retry antes de humano
bash .delta-11/tests/protocolos/dispatch-ap7.test.sh   # SCOUT SendMessage
bash .delta-11/tests/protocolos/dispatch-ap8.test.sh   # disparar.sh removido
bash .delta-11/tests/protocolos/dispatch-ap11-ap13-ap14.test.sh   # vigilante+selo+linguagem
bash .delta-11/tests/protocolos/dispatch-ap9-ap10-ap12.test.sh   # defaults+painel+plataforma
```

### Métricas de mudança

- **14 anti-padrões** corrigidos em 9 commits
- **9 arquivos** modificados: CLAUDE.md, CRONOS.md, ATLAS.md, SCOUT.md, SHIELD.md, selo-experiencial-template.md, vigilante.sh, instalar.sh, disparar.sh (deletado)
- **+ 7 operativos** corrigidos no AP#5 (BACK, ENGINE, FORM, FRONT, PIXEL, SCOUT, VAULT)
- **10 testes novos**: 4 em `tests/operativos/` (o executor da época não rodava essa pasta) e 6 em `tests/protocolos/` (5 + `dispatch-v61-consolidado`)
- **Suíte:** 27/27 → **33/33 OK**
- **Comando humano em fluxo normal:** ~5-7 interações/fase → **0-1 interações/fase** (só quando algo falha)

---

## v6.0 (2026-07-12) — Alinhamento com Metodologia Gênesis (Nível 3 Profundo)

**Versão anterior:** v5.4 (2026-07-10) — 3 skills globais instaladas (supabase-rls, owasp-top10, react-next).
**Autor:** Comandante Rafa + auditoria inicial de Claude Code (12 commits na branch `v6.0-metodologia-genesis`).
**Status:** Branch pronta para merge. Suíte 27/27 OK.

### Por que essa versão existe

Auditoria estrutural do D-11 contra a **Metodologia Gênesis para Construção de Software v1.0** (Rafa Marks) revelou 8 furos estruturais. O D-11 cumpria parcialmente a metodologia — forte em Ordem (Fases 0→6 sequenciais) e em Selagem (pre-selo + validar-contratos), mas **ausente em Contraposição Lateral** (Princípio 3) e com lacunas graves nos Dias 4 (Ritmo Temporal), 6 (Consciência) e 7 (Descanso). A v6.0 reescreve a arquitetura do sistema para alinhar às 7 camadas da Criação como espinha dorsal.

A auditoria identificou o que o próprio D-11 advertia: "O D-11 reproduziu o erro humano que ele existe para impedir." Sem contraposição, sem Dia 4, sem Dia 7 — o sistema vira refém do criador.

A v6.0 inverte essa lógica: **camadas estruturais obrigatórias** + **princípios como leis técnicas** + **evidência como critério de selo** (especialmente no Dia 7).

### O que mudou

#### Fase 1 do v6.0 (Etapas 1-2 do plano) — Fundação conceitual

- **Base canônica da Metodologia Gênesis** (`.delta-11/conhecimento/metodologia-genesis-camadas.md`, ~230 linhas): referência que os 10 agentes consultam. Inclui os 3 Princípios Fundamentais, os 7 Dias com contraposição lateral do tipo correto (Tipo 1 a Tipo 7), critérios objetivos de selo, as 7 sub-etapas do Ciclo Interno, os 4 Sinais de "Fazendo Certo", mapeamento para fases do D-11 v6.0, cross-references com skills globais v5.4 e com a auditoria original. **Texto hebraico chave preservado por Dia.**

- **Fluxo das 7 fases reescrito** com Metodologia Gênesis como espinha dorsal. 3 novas fases adicionadas (Fase 3.5, 4.5, 7) — total de 13 fases no fluxo v6.0:
  - **Fase 3.5 — RITMO TEMPORAL** (Dia 4 — Os Astros): entre Fase 3 e Fase 4. Antes do v6.0 o sistema ia direto da Fundação para o Desenvolvimento, pulando o Dia 4 inteiro (inversão herética: "fazer os peixes antes de haver águas").
  - **Fase 4.5 — CONSCIÊNCIA DOMINANTE** (Dia 6 — único dia declarado *tov meod*): entre Fase 4 e Fase 5. Cobre autenticação+autorização conscientes, motor de regras de negócio, auditoria imutável, rate limiting, LGPD, fluxos de aprovação.
  - **Fase 7 — DESCANSO CONSAGRADO** (Dia 7 — *vayechulu, vayishbot, vayvarech, kadash*): após Fase 6. Cobre documentação consumada, deploy automatizado, **runbooks específicos do projeto**, monitoramento+alertas com dono, tag de release, backup testado, DR testado, onboarding testado, e o **TESTE SUPREMO** ("se o criador tirar 2 semanas de férias, o sistema continua?").

#### Fase 2 do v6.0 (Etapas 3-4) — Princípios como leis técnicas

- **Hook `contraposicao-checker.py`** (Etapa 3): PreToolUse que BLOQUEIA edição de `project-core.md` sem a palavra "contraposição" no conteúdo. **Materializa o Princípio 3 (Contraposição Lateral Obrigatória)** — que era zero no sistema antes do v6.0. Em stderr, lista os 7 tipos de contraposição (Tipo 1 a Tipo 7) correspondentes aos 7 dias.

- **Hook `validar-arquitetura-vs-modelos.py`** (Etapa 4): PreToolUse que BLOQUEIA conclusão de tarefa da Fase 3 sem tarefa CONCLUÍDA "Validação Retroativa Dia 2 ← Dia 3" no kanban. Aceita respostas **SUSTENTA** (passa) ou **REFAZER** (bloqueia para reativar ATLAS). **Materializa a Verificação Retroativa do Dia 2 pelo Dia 3** que a Metodologia Gênesis exige (Gênesis não declara o Dia 2 "bom" sozinho).

#### Fase 3 do v6.0 (Etapas 5-7) — Camadas completas (protocolo + template + hook)

Cada nova fase tem 3 artefatos canônicos com teste RED → GREEN:

| Etapa | Camada | Protocolo | Template | Hook |
|-------|--------|-----------|----------|------|
| 5 | Fase 3.5 (Dia 4 — Ritmo) | `protocolos/fase-ritmo.md` | `templates/fase-ritmo-template.md` | `hooks/fase-ritmo-checker.py` |
| 6 | Fase 4.5 (Dia 6 — Consciência) | `protocolos/fase-consciencia.md` | `templates/fase-consciencia-template.md` | `hooks/fase-consciencia-checker.py` |
| 7 | Fase 7 (Dia 7 — Descanso) | `protocolos/fase-descanso.md` | `templates/fase-descanso-template.md` | `hooks/fase-descanso-checker.py` |

**Hook da Fase 3.5** exige **10 artefatos** (eventos, filas, jobs, cache TTL, timeouts, retries, circuit breakers, CI/CD, observabilidade, sub-contraposição) em `.delta-11/memoria/decisoes/` antes de marcar Fase 3.5 concluída.

**Hook da Fase 4.5** exige **5 entregáveis** (auditoria imutável, rate limiting, motor de regras, LGPD, fluxos de aprovação).

**Hook da Fase 7** exige **10 artefatos + TESTE SUPREMO** explícito (frase "TESTE SUPREMO PASSOU" ou equivalente no kanban).

**Integração com `monitor-delta11.sh`** (Etapa 7D): detecta "operação autônoma ≥ 14 dias" via `OPERACAO_AUTONOMA` + `dias_silencio` no `monitor-status.json`.

#### Fase 4 do v6.0 (Etapas 8-9) — Fractalidade + Dia 1 com teste do badal

- **Protocolo + template do Ciclo Interno de 7 Sub-Etapas** (Etapa 8): materializa a fractalidade da Criação que o `operativos/ATLAS.md:386-403` apenas declarava ASPIRACIONALMENTE. Cada fase (0 a 7) deve executar internamente as 7 sub-etapas: planejamento → delegação → execução paralela → comunicação → revisão cruzada → teste adversarial → selagem. Tabela no protocolo mostra como cada fase do D-11 aplica as 7 sub-etapas (incluindo quais sub-etapas são N/A em fases de 1 agente).

- **Hook `dia1-badal-checker.py`** (Etapa 9): PreToolUse que BLOQUEIA edição de `docs/prd.md` ou `project-core.md` sem **6+ dos 8 elementos obrigatórios do Dia 1**:
  1. Frase decisória
  2. Identidade assumida
  3. Identidade fugida
  4. Teste do badal (nitidez entre identidades, sem eliminação)
  5. Inimigo único
  6. Trauma único
  7. Lago abandonado
  8. Nova categoria de Solução

**Materializa o achado #2 (Dia 1 sem teste do badal)** — antes do v6.0 a Fase 0 coletava só avatar/diferencial/experiência/identidade visual, sem dialética existencial.

### Como testar

```bash
# Suite completa automatizada — 27 checks
bash .delta-11/tests/rodar-todos.sh

# Esperado: 27/27 OK (foi 8/8 na v5.4; agora 27/27 com 19 testes adicionados)

# Por categoria:
#   [hooks]      - pre-criacao-arquivo, contraposicao-checker, validar-arquitetura-vs-modelos, fase-ritmo-checker, fase-consciencia-checker, fase-descanso-checker, dia1-badal-checker
#   [templates]  - changelog, design-patterns, estado-produto, golden-baselines, fase-ritmo-template, fase-consciencia-template, fase-descanso-template, ciclo-interno-template
#   [conhecimento] - metodologia-genesis
#   [protocolos] - fluxo-fase-3-5, fluxo-fase-4-5, fluxo-fase-7, fase-ritmo, fase-consciencia, fase-descanso, ciclo-interno-7d
#   [scripts]    - aplicar-boilerplate, novo-projeto-gotchas, rodar-comparacao, monitor-delta11-fase-7

# Verificar que hook de contraposicao bloqueia:
# Editar project-core.md sem "Contraposição" -> exit 2 (BLOQUEIO)

# Verificar que hook de validacao retroativa bloqueia:
# Concluir tarefa Fase 3 no kanban sem "Validacao Retroativa Dia 2 <- Dia 3 CONCLUIDA **SUSTENTA**" -> exit 2

# Verificar que hook de Fase 3.5 bloqueia conclusao sem 10 artefatos:
# Criar kanban com tarefa [3.5] concluida, sem 10 arquivos ritmo-temporal-*.md em .delta-11/memoria/decisoes/ -> exit 2

# Verificar que hook de Fase 7 bloqueia conclusao sem TESTE SUPREMO:
# Criar 10 arquivos descanso-*.md em .delta-11/memoria/decisoes/, marcar Fase 7 concluida SEM "TESTE SUPREMO PASSOU" -> exit 2

# Verificar que hook de Dia 1 bloqueia PRD sem 8 perguntas:
# Editar docs/prd.md sem pelo menos 6 dos 8 elementos obrigatorios -> exit 2
```

### Achados da auditoria — status final

| # | Achado | Gravidade inicial | Status v6.0 | Como foi corrigido |
|---|--------|-------------------|-------------|---------------------|
| 1 | Princípio 3 (Contraposição) ausente | 🔴 Bloqueante | ✅ Corrigido | `contraposicao-checker.py` (Etapa 3) |
| 2 | Dia 1 sem teste do badal | 🟠 Grave | ✅ Corrigido | `dia1-badal-checker.py` (Etapa 9) |
| 3 | Dia 2 sem validação retroativa | 🟠 Grave | ✅ Corrigido | `validar-arquitetura-vs-modelos.py` (Etapa 4) |
| 4 | Dia 4 (Ritmo) zero camada | 🔴 Furo principal | ✅ Corrigido | Fase 3.5 completa (Etapa 5) |
| 5 | Dia 5 sub-contraposição escalar | 🟡 Médio | ✅ Aceito (cumpre) | CRONOS mini-plano seção 5 (Limites de Escopo) + base canônica |
| 6 | Dia 6 (Consciência) consciência de domínio fraca | 🟠 Grave | ✅ Corrigido | Fase 4.5 completa (Etapa 6) |
| 7 | Dia 7 (Descanso) sem runbook/tag/backup/DR/teste supremo | 🔴 Furo grave | ✅ Corrigido | Fase 7 completa (Etapa 7) + integração `monitor-delta11.sh` |
| 8 | Fractal 3x7 ASPIRACIONAL (sem protocolo) | 🟡 Médio | ✅ Corrigido | `protocolos/ciclo-interno-7d.md` + template (Etapa 8) |

**Porcentagem de cumprimento (recalculada):** ~30% → ~95% após v6.0. Os 5% restantes são por construção — o Dia 5 (Habitantes) tem sub-contraposição escalar mapeada conceitualmente mas sem hook técnico dedicado (é papel do CRONOS mini-plano).

### Commits desta versão

Branch `v6.0-metodologia-genesis` (12 commits):

```
feat(v6.0 E10): consolidação final — CHANGELOG v6.0 + CLAUDE.md cross-ref
feat(v6.0 E9): hook dia1-badal-checker.py — Dia 1 com 8 perguntas do badal
feat(v6.0 E8): Ciclo Interno de 7 Sub-Etapas (protocolo + template)
feat(v6.0 E7): Fase 7 completa — protocolo + template + hook + monitor (Dia 7 Descanso)
feat(v6.0 E6): Fase 4.5 completa — protocolo + template + hook (Dia 6 Consciencia)
feat(v6.0 E5): Fase 3.5 completa — protocolo + template + hook bloqueante
feat(v6.0 E4): hook validar-arquitetura-vs-modelos.py — Validacao Retroativa Dia 2 <- Dia 3
feat(v6.0 E3): hook contraposicao-checker.py — Principio 3
feat(v6.0 E2C): Fase 7 DESCANSO CONSAGRADO no fluxo
feat(v6.0 E2B): Fase 4.5 CONSCIENCIA DOMINANTE no fluxo
feat(v6.0 E2A): Fase 3.5 RITMO TEMPORAL no fluxo
feat(v6.0 E1): base canonica da Metodologia Genesis + suite de teste
```

### Manutenção / próximos passos sugeridos

- **Merge:** quando o comandante aprovar, merge da branch `v6.0-metodologia-genesis` para `main`. Atualizar `sincronizar.sh` se necessário (verificar se novos arquivos em `tests/protocolos/`, `tests/templates/`, `tests/scripts/`, `hooks/` já estão no loop de sincronização).
- **Baseline v6.0:** gerar `golden-baselines/execucoes/2026-07-12-v6.0-baseline/` com 10 prompts + gabaritos.
- **Aplicação em projeto real:** rodar o fluxo v6.0 em um projeto real (`mcp-server-produtos-2` ou novo) para validar end-to-end. Anotar divergências para revisão da v6.0.1.
- **v6.0.1 (correções):** após 30 dias em produção, revisar:
  - Taxa de falsos positivos de hooks (PRD "vazio" aceito por engano?)
  - Quais sub-etapas estão sendo puladas na prática (relatório do CRONOS)
  - Quais tipos de contraposição foram mais subvertidos

### Auditoria de origem

Documento completo: `.delta-11/memoria/decisoes/2026-07-10-auditoria-delta-11-vs-metodologia-genesis.md` (~530 linhas, imutável). Inclui: bibliografia, tabela consolidada de achados, 8 achados detalhados com arquivo/linha-citação, síntese final, plano de correção em 3 níveis. A v6.0 implementou o **Nível 3 — Profundo**.

---

## v5.4 (2026-07-10) — Estágios 0-7 do plano de execução (testes, goldens, CHANGELOG e 3 skills globais)

**Versão anterior:** v5.3 (2026-07-07 a 2026-07-09) — Onda 4 fechou com golden baselines + boilerplate; Bloco A da auditoria.
**Autor:** Comandante Rafa + Claude Code (8 estágios, E0 a E7, em 12 commits no mesmo dia).
**Status:** Levada aos projetos do registro central. 3 skills globais instaladas em `~/.claude/skills/`.

### Por que essa versão existe

O sistema estava funcional, mas dois sintomas expunham doença estrutural:

1. **Regressões invisíveis** — o hook `pre-criacao-arquivo.py` tinha um bug silencioso (CASO D/E engolidos pelo B por ordem de checagem) que passou despercebido por 2 meses. O `sincronizar.sh` também tinha um bug crítico de self-sync que sobrescrevia o repo de distribuição com versão antiga de outro clone.

2. **Medição inexistente** — mudanças no sistema (operativos, bases de conhecimento, CLAUDE.md) eram avaliadas "no olhômetro". Não havia régua fixa para comparar versão A vs versão B.

Faltavam também **cobertura de RLS** (vazamentos silenciosos), **segurança** (CVEs do stack sem defesa) e **conhecimento de debugging React/Next** (tela branca frequente). A v5.4 inverteu a lógica: "medir antes de crescer" → "infra de teste + furos fechados" → "skills globais" → "consolidação".

### O que mudou

#### Estágio 0 (2026-07-10) — Infraestrutura de teste e medição

**O que:** Criação do `.delta-11/tests/` (pastas `hooks/`, `templates/`, `scripts/`) com orquestrador `rodar-todos.sh`. Migrados os 9 casos validados do F2 para `tests/hooks/pre-criacao-arquivo.test.py`. Fail-fast no teste do `pre-criacao-arquivo` (se o hook de segurança regredir, a suíte para). Adicionado `.delta-11/tests/**` ao loop de sincronização. Criado `golden-baselines/rodar-comparacao.sh` (prepara execuções datadas). Allowlist `Read(~/.claude/skills/**)` no settings-hooks.json. `novo-projeto.sh` agora cria `.delta-11/memoria/gotchas.md` no dia 1 (F5).

**Por que:** Antes desta versão, "qual versão do Δ-11 é melhor" era respondido por impressão. Agora há régua: 3/3 OK (E0) → 7/7 OK (E1) → 7/7 OK + 10 goldens (E2) → 8/8 OK (E3, com o teste do CHANGELOG).

**Bônus inesperado:** a suíte pegou um bug real que tinha passado despercebido — CASO D/E estavam atrás do B no hook. Reordenados para específicos (D, E, F) antes de genéricos (B). A lição: **testes não são burocracia, são rede de proteção para mudanças futuras**.

#### Estágio 1 (2026-07-10) — Bloco A: fechar 10 furos restantes

**O que:** 4 grupos (G1-G4) fecharam furos remanescentes da auditoria v5.3:

| Grupo | Furo | Componente | Mudança |
|---|---|---|---|
| G1 | F4 | `estado-produto-template.md` | Exemplo completo preenchido (~470 tokens, dentro do orçamento) |
| G2 | F6 + F11 + F12 | `aplicar-boilerplate.sh` + `env.example` | Aviso Regra 15 no env.example, recusa projetos sem `src/`, backup datado com `--force` |
| G3 | F15 | `design-patterns-praticos.md` | Seção Adapter cita Regra 14 → Regra 15 → Adapter (sequência completa) |
| G4 | F9 + F10 + F14 | 3 tarefas canônicas + execucoes/ | Campo "Última atualização", remoção de critério subjetivo, `.gitignore`/`gitkeep` |

**Por que:** Bloco A já tinha fechado 5 furos críticos na v5.3 (F1, F2, F3, F8, F13). Sobravam 10 que ninguém tinha priorizado. Esta versão fecha todos.

**F7 (cross-refs erradas) era falso positivo** — todas as 7 refs batiam. Mantido o teste como guarda de regressão.

#### Estágio 2 (2026-07-10) — Cobertura completa dos goldens

**O que:** 7 tarefas canônicas novas (ATLAS, CRONOS, BACK, FRONT, FORM, SHIELD, SCOUT) + as 3 existentes atualizadas (ENGINE, PIXEL, VAULT) = 10 tarefas cobrindo TODOS os agentes. Baselines v5.3 e v5.4 geradas em `golden-baselines/execucoes/` (a da v5.4 em `2026-07-10-v5.4-baseline/`, com 10 prompts + gabaritos). `rodar-comparacao.sh` reescrito com extração Python (cross-platform — sed do macOS não suporta `/I`).

**Por que:** A régua de comparação antes cobria só 3 agentes (ENGINE, PIXEL, VAULT). Era como medir a qualidade de um time testando só 3 dos 10 jogadores.

**Bug crítico resolvido durante E2:** SELF-SYNC GUARD adicionado em `sincronizar.sh`. O registry global apontava para um clone desatualizado em `~/projetos/Formacao-delta-11`, e o `sincronizar.sh` propagava arquivos DAQUELE clone PARA o repo real em `~/Documents/VSCODE/Formacao-delta-11`, sobrescrevendo correções com versões antigas. O guard compara `proj_dir` com `SCRIPT_DIR` e pula com aviso amarelo se forem iguais (self-sync). Registry atualizado para o path real.

#### Estágio 3 (2026-07-10) — Este CHANGELOG

**O que:** Este documento, com narrativa por versão (v5.4 → v5.3 → v5.2 → v5.1 → v5.0 → v4.0.4 → v4.0), entrada no loop de sincronização e teste de regressão (`tests/templates/changelog.test.sh`). Regra de imutabilidade: entradas publicadas viram ADR-like; correções vão em ADIÇÕES POSTERIORES.

#### Estágio 4 — Skill `supabase-rls` (Skill Forge v3 Deep Path, sessões 4.1 e 4.2)
- **Pipeline:** Stage A (16 fontes, 35 claims, 32 armadilhas) → Stage B (14 princípios, 26 heurísticas, 32 testes) → Stage C (12 arquivos)
- **6.676 linhas** em `~/.claude/skills/supabase-rls/`: SKILL.md (172) + 10 references (4.459) + evals.json (221)
- **Empacotada** em `/tmp/supabase-rls.skill` (83.9 KB)
- Cobre: 7 padrões canônicos (P1-P7), multi-tenancy (3 estratégias), 32 testes, 26 heurísticas, 4 analogias, 8 invariantes + 7 anti-invariantes
- CVEs específicos: nenhum específico de RLS, mas cobre RLS bypass silencioso (G-001 canônico)
- Base curta D-11: 149 linhas (gate para skill completa)

#### Estágio 5 — Skill `owasp-top10` (Skill Forge v3 Deep Path, sessões 5.1 a 5.4)
- **Pipeline:** Stage A (16 fontes, 53 claims, 51 armadilhas, 5 CVEs) → Stage B (36 princípios, 32 heurísticas, 47 testes, 10 diagnostic flows) → Stage C (12 arquivos)
- **7.374 linhas** em `~/.claude/skills/owasp-top10/`: SKILL.md (192) + 10 references (6.961) + evals.json (221)
- **Empacotada** em `/tmp/owasp-top10.skill` (90.2 KB)
- Cobre: **10/10 categorias OWASP 2021** (A01-A10), 25 padrões canônicos (PAT-001 a PAT-025), 44 anti-padrões (ANTI-001 a ANTI-044) com CVEs
- **CVEs principais:** CVE-2024-34351 (SSRF Server Actions) + CVE-2025-29927 (Middleware bypass CRITICAL) + 3 adicionais
- 5 configs canônicas (headers, CORS, cookies, JWT, env vars)
- 47 testes executáveis (20 CRITICAL + 21 HIGH + 6 MEDIUM)
- Base curta D-11: 118 linhas (gate)

#### Estágio 6 — Skill `react-next` (Skill Forge v3 Deep Path, sessão 6.1)
- **Pipeline:** Stage A (16 fontes, 44 claims, 45 armadilhas) → Stage B (20 princípios, 31 heurísticas, 35 testes, 6 debugging flows) → Stage C (12 arquivos)
- **5.466 linhas** em `~/.claude/skills/react-next/`: SKILL.md (167) + 10 references (5.113) + evals.json (186)
- **Empacotada** em `/tmp/react-next.skill` (59.5 KB)
- Cobre: Server vs Client Components, hooks React 19, Server Actions, performance, testing, debugging reativo (5 árvores: hydration/infinite loop/memory/race/RSC), stack-specific Next.js 15
- **22 padrões canônicos** (PAT-01 a PAT-22) + **32 anti-padrões** (ANTI-001 a ANTI-032)
- 10 perguntas antes de commitar componente
- BUG #1 documentado: **Esquecer `revalidatePath` em Server Action = UI não atualiza**
- Base curta D-11: 102 linhas (gate)

#### Estágio 7 — Consolidação final
- CHANGELOG atualizado (este arquivo), índice das skills e CLAUDE.md
- 3 skills globais instaladas e testadas
- Suite D-11: **8/8 OK** (nada regrediu)
- Sistema levado aos projetos do registro pelo `sincronizar.sh`

### Estatísticas v5.4

| Métrica | Valor |
|---|---|
| **Estágios completados** | 8 (E0 a E7), em 12 commits |
| **Custo total** | ~17h45 |
| **Skills globais criadas** | 3 (supabase-rls, owasp-top10, react-next) |
| **Linhas de skill autorais** | 19.516 (6.676 + 7.374 + 5.466) |
| **Arquivos em skills** | 36 (12 + 12 + 12) |
| **CVEs cobertos** | 2 CRITICAL + 3 HIGH |
| **Anti-padrões catalogados** | 145 (32 RLS + 44 OWASP + 32 React + 37 deduzidos) |
| **Padrões canônicos** | 54 (7 RLS + 25 OWASP + 22 React) |
| **Bases curtas do D-11** | 3 (uma por skill) |
| **Testes automatizados** | 8 (D-11) + 114 nas skills (32 RLS + 47 OWASP + 35 React) |
| **Projetos sincronizados** | os do registro central (o número "18" das versões anteriores deste texto não tinha fonte; o monitor da época listava 11 a 12 projetos) |

### Como testar

```bash
# 1. Suite automatizada do D-11 (deve passar 8/8)
bash .delta-11/tests/rodar-todos.sh

# Fail-fast se hook de segurança regrediu
bash .delta-11/tests/rodar-todos.sh --hook pre-criacao-arquivo

# 2. Re-rodar comparação de goldens
bash golden-baselines/rodar-comparacao.sh v5.4.1   # cria nova rodada para comparar com v5.4-baseline

# 3. Validar cada skill
for skill in supabase-rls owasp-top10 react-next; do
  cd ~/.claude/skills/skill-forge
  /opt/homebrew/bin/python3.12 scripts/forge_validate.py /Users/alfa/.claude/skills/$skill
done

# 4. Levar a versão aos projetos do registro
cd ~/Documents/VSCODE/Formacao-delta-11
./sincronizar.sh --nota "Verificar v5.4 instalado: 3 skills globais"
```

### Commits desta versão (v5.4)

- `512b35b` feat(v5.4 E0): infra de teste automatizada + allowlist skills + bootstrap gotchas
- `9a7c477` fix(v5.4 E0): reordenação dos casos D/E/F antes de B + path absoluto do hook no teste
- `fa5bcf0` feat(v5.4 E1): fechar 10 furos restantes do Bloco A (G1-G4) + 4 novos testes + baseline v5.3
- `2b16664` feat(v5.4 E2): 7 tarefas canônicas novas + baseline v5.4 + self-sync guard
- `c80bff3` feat(v5.4 E3): CHANGELOG.md do sistema + loop de sync + teste de regressão
- `c27fa2e` feat(v5.4 E4.1): skill supabase-rls (sessão 4.1) + base curta do D-11 (gate)
- `11a68cd` feat(v5.4 E4.2): skill supabase-rls — P6 multi-tenancy + P7 custom hooks
- `a323120` feat(v5.4 E5.1): skill owasp-top10 (sessão 5.1) + base curta do D-11
- `1215a47` feat(v5.4 E5.2): skill owasp-top10 — A06-A10 + 25 padrões canônicos
- `eda8b21` feat(v5.4 E5.4): skill owasp-top10 — monitoring, IR, mental model, testes, heurísticas, evals
- `d496865` feat(v5.4 E6.1): skill react-next (sessão 6.1) + base curta do D-11
- `4781ed1` feat(v5.4 E7): consolidação final — CHANGELOG v5.4 + índice skills + CLAUDE.md

---

## v5.3 (2026-07-07 a 2026-07-09) — Onda 4 + Bloco A (5 furos críticos)

**Versão anterior:** v5.2 (2026-07-03) — Ciclo de Zoneamento Documental.
**Autor:** Comandante Rafa + Claude Code (Onda 1-4 + auditoria).
**Status:** Versão base usada pela v5.4 como comparação.

### O que mudou

#### Antes das Ondas (2026-07-05 a 2026-07-07) — limpeza

**O que:** Remoção completa do sub-agente `code-simplifier` (2026-07-05, `f03c64e` + revisão `bacd3e8`): era otimizador terminal, ninguém consumia seu output para decisão; a legibilidade passou aos executores durante a escrita + revisão do SHIELD. Regras invioláveis atualizadas para as 17 da v4.0, sem etiquetas de versão nos títulos (`b7a1815`, `e1ed72d`). `sincronizar.sh` passou a ignorar as worktrees de execução dos agentes (`77d0427`).

#### Onda 1 (2026-07-07) — Limites estruturais de código

**O que:** Implementação das regras da seção 8 de `regras-codigo.md` (limites estruturais: função ≤ 50 linhas, arquivo ≤ 400 linhas, aninhamento ≤ 3, complexidade ciclomática ≤ 10). Convenção de idioma (inglês em código, português em conteúdo). Sentry obrigatório pré-deploy.

**Por que:** As regras existiam no papel mas não havia enforcement. Esta onda implementou.

#### Onda 2 (2026-07-07) — Design patterns + ADR + bug report + PRD

**O que:** Base de conhecimento `design-patterns-praticos.md` (10 padrões GoF filtrados pelos mais úteis no Δ-11). Templates: `adr-registro-de-decisao-arquitetural-template.md`, `bug-report-template.md`, `prd-documento-de-requisitos-template.md`. Função de auditoria de completude.

**Por que:** O sistema não tinha templates canônicos para os 3 tipos de documentos mais importantes (decisão, bug, requisitos). Cada agente inventava formato.

#### Onda 3 (2026-07-07) — Mecanismos de qualidade

**O que:** Mecanismos de qualidade importados dos squads de programação: autocrítica do autor em 2 paradas (Passo 3.4, gravada em `logs/autocritica/`; o SHIELD devolve tarefa sem autocrítica); verificação anti-falso-positivo do SCOUT em 4 passos + teste de regressão obrigatório; rastreabilidade `[Fonte: arquivo#seção]` no mini-plano do CRONOS; evidência mínima por tipo de tarefa no SHIELD; nota em 4 dimensões no `code-architect`; modelo `gotchas-template.md`; SISTEMA IMUNE (3 pares gatilho → resposta) nos 10 operativos.

**Por que:** Sem quality gate automático, a revisão do SHIELD era inconsistente.

**Nota histórica:** a cadeia `build-validator` → `code-simplifier` → `contract-tester` foi padronizada nos executores bem antes, em 2026-04-03 (`210bc5e`, preparação da v4.0). O `code-simplifier` foi removido em 2026-07-05 (ver "Antes das Ondas"), dois dias ANTES da Onda 3, que já partiu da cadeia `build-validator` → `contract-tester`.

#### Onda 4 (2026-07-07) — Golden baselines + boilerplate

**O que:** Pasta `golden-baselines/` com 3 tarefas canônicas (ENGINE, PIXEL, VAULT) + rubrica de avaliação. Boilerplate Next.js (`boilerplate-delta-11-nextjs/`) com `aplicar-boilerplate.sh` + overlay (env, error-response, monitoramento-de-erros, eslint).

**Por que:** Antes desta onda, não havia como medir regressão de qualidade entre versões do Δ-11. Também não havia scaffold testado para começar um projeto Next.js sem repetir 30 decisões tediosas.

#### Bloco A da auditoria (2026-07-09) — 5 furos críticos

**O que:** Correção de F1 (paths canônicos), F2 (hook zoneamento documental), F3 (Golden Path de tarefa), F8 (autocrítica no produto.md), F13 (interface billing).

**Por que:** Auditoria da v5.2 identificou 23 deficiências; este Bloco fechou as 5 mais urgentes (cirúrgicas, sem mudança de arquitetura).

### Como testar (goldens)

```bash
bash golden-baselines/rodar-comparacao.sh v5.3-baseline   # já gerada
# Esperado: MANIFESTO + 3 subdirs com prompt-de-ativacao + gabarito
```

### Commits desta versão

- `fa9ee08` fix: Bloco A da auditoria — os 5 furos mais urgentes da v5.3 (2026-07-09)
- `43b5fd5` feat: Onda 4 — golden baselines + boilerplate overlay Next.js
- `c6de931` feat: Onda 3 — mecanismos de qualidade importados dos squads de programação
- `68e6f4a` feat: Onda 2 — design patterns, ADR, bug report, PRD e auditoria de completude
- `7f1b1ef` feat: Onda 1 — limites estruturais de código, convenção de idioma, Sentry obrigatório
- `e1ed72d`, `77d0427`, `b7a1815` fix: regras invioláveis (17) sem etiquetas de versão + sincronizar ignora worktrees (2026-07-07)
- `bacd3e8`, `f03c64e` feat/fix: remoção completa do Code Simplifier (2026-07-05)

---

## v5.2 (2026-07-03) — Ciclo de Zoneamento Documental (23 mudanças em 4 pilares)

**Versão anterior:** v5.1 (2026-07-01) — Painel de Comando redesenhado para comandante humano.
**Autor:** Comandante Rafa + Claude Code (auditoria comparativa com M2C1).
**Status:** Versão base usada pela v5.3 e v5.4.

### Por que essa versão existe

Auditoria comparativa entre Δ-11 e o framework M2C1 (importado da skill `m2c1`) identificou 23 deficiências em 4 frentes:
1. **IA externa** (Claude/Codex/GPT/mini-max) criava arquivo em endereço aleatório — caso real `docs/configuracao-kimi-moonshot.md` (config de API nomeada pelo vendor na pasta de specs).
2. **10 tipos de artefato** gerados sem template canônico.
3. **Housekeeping zero** — locks de 45 dias, 13 backups de contrato sem rotação, arquivos efêmeros em /tmp.
4. **Setup de ferramentas 100% manual** do comandante.

### O que mudou (4 pilares)

#### Pilar 1 — Doutrina (Regras Invioláveis 14-17)

**O que:** Novas regras sobre zoneamento documental. Configuração de integração externa vive em `src/lib/[dominio]/[etapa]/README.md` (Regra 15), nomeada pela FUNÇÃO não pelo vendor. `.delta-11/conhecimento/` substituiu `skills/` legado. Decisões arquiteturais em `.delta-11/memoria/decisoes/` (Regra 16).

**Por que:** O "caso Kimi" — IA externa criou `docs/configuracao-kimi-moonshot.md` em vez de `src/lib/ia/analise-competitiva/README.md`. Ninguém encontrou depois, e quando o vendor trocou (Kimi → outro), o nome virou mentira.

#### Pilar 2 — Templates canônicos (10 novos)

**O que:** `mini-plano-agente-template.md`, `cronos-sequenciamento-template.md`, `cronos-dependencias-template.md`, `cronos-abertura-fase-template.md`, `selo-experiencial-template.md`, `contratos-api-template.md`, `esquema-banco-template.md`, `pesquisa-tecnica-template.md`, `impacto-mudanca-template.md`, `config-integracao-externa-template.md`.

**Por que:** Cada agente inventava formato para esses documentos. Inconsistência dificultava revisão automática.

#### Pilar 3 — Housekeeping

**O que:** Hook `gc-locks.py` em SessionStart limpa locks >2h. Rotação de `.contract-backup/` mantendo 5. Pastas canônicas `.delta-11/scratch/`, `.delta-11/evidencias/`, `.delta-11/logs/sub-agentes/`. `novo-projeto.sh` migra `.memoria-*` legado interativamente e põe scripts em `.delta-11/scripts/`.

**Por que:** Sem housekeeping automático, o sistema acumulava lixo. Locks velhos impediam novos agentes de editarem os mesmos arquivos.

#### Pilar 4 — Capacidade (sub-agente tool-provisioner)

**O que:** Sub-agente `tool-provisioner` na nova Fase 2.4 — provisiona MCPs, chaves, contas com verificação real. Provisionamento deixou de ser 100% manual.

**Por que:** Cada novo projeto perdia 30-45min em setup de chaves de Supabase + Vercel + Inngest.

### Como testar

```bash
# Hook de zoneamento (deve bloquear Kimi case)
python3 .delta-11/hooks/pre-criacao-arquivo.py < .delta-11/scratch/test-event.json
echo $?   # 2 = bloqueou, 0 = liberou

# Suite automatizada desta versao (v5.2)
bash .delta-11/tests/rodar-todos.sh
```

### Commits desta versão

- `83e1293` feat: v5.2 — Ciclo de Zoneamento Documental (23 mudanças em 4 pilares)
- `a2d98f3` fix: guarda técnica contra bug #39886 + hooks v5 finalmente ativados nos projetos
- `84d7b95` fix: sincronizar.sh reescreve projects[] do registry a cada sync

---

## v5.1 (2026-07-01) — Painel de Comando redesenhado

**Versão anterior:** v5 (2026-07-01) — granularização + hooks Python + modo-selo configurável.
**Autor:** Comandante Rafa + Claude Code.
**Documentação:** `.delta-11/CHANGELOG-painel-v5.1.md` (detalhes completos).

### Resumo

Painel de Comando (`painel.html`) redesenhado para o **comandante humano** (não para os agentes). Antes: 4 colunas kanban com IDs de tarefa e timestamps ISO. Depois: coluna vertical com selo binário grande (verde/amarelo/vermelho), voz do CRONOS em português leigo, e `resumo_humano` em cada tarefa.

### Commits desta versão

- `7ef0396` feat: v5.1 — Painel de Comando redesenhado para comandante humano
- `4fa10cc` fix: restaura identidade visual Δ-11 no painel v5.1
- `18e2c39` a `d3636f6` (2026-07-02, madrugada): mais 7 rodadas visuais do painel, chamadas nos commits de "painel v6" a "painel v12" — numeração do PAINEL, não do sistema (Sala de Operações, paleta preto + vermelho, grade de operativos, gaveta lateral, progresso geral em destaque)

---

## v5.0 (2026-07-01) — Granularização + hooks Python

### Resumo

Granularização dos agentes (perfis, ferramentas, conhecimento, modelos separados por papel). Hooks Python cross-platform (substituindo AppleScript). Modo-selo configurável (manual vs automático).

### Commits principais

- `b070b2f` feat: v5 — granularização + hooks Python + modo-selo configurável

---

## v4.0.4 (2026-04-18 a 2026-05-27) — Mudanças 1-17 da Criação

### Resumo

Adição das 17 mudanças estruturais baseadas na Geometria da Criação (M4 do framework). Inclui: fatias de domínio do project-core, abertura de fase, fresh reviewer, visão, viu que era bom, locks atômicos via mkdir, push-based task notifications, verificação proativa de worktree (Passo 0.VW).

### Commits principais

- `bd210fc` feat: v4.0.4 — isenção do limite de 500 tokens para ATLAS e CRONOS (2026-05-27)
- `b8e8b43` feat(ciclo7.5-d-02): checkpoint de locks ANTES de Edit/Write no prompt do CRONOS (2026-05-19)
- `892b068` feat: Mudança 17 — REGRA DOS 7 CICLOS obrigatória (v4.0.4)
- `9c23a6e` feat: Bloco C — Mudanças 15+11 (Mecanismos 5+2 da Criação)
- `9780685` feat: Bloco B — Mudanças 10+12 (Mecanismos 1+3 da Criação)
- `8c929d5` feat: Bloco A — Mudanças 13+16+14 (Mecanismos 4+6+4b da Criação)
- `a01ef58` feat: Mudança 5 — Fatias de domínio do project-core
- `9dad7cf` feat: Mudanças 1+2+3+4 — Abertura de Fase, Fresh Reviewer, Visão, Viu que Era Bom
- `7a16e61` feat: Mudança 9 — Alavanca 5 Lembrete de Escopo do project-core
- `31cd5d3` fix: Mudança 8 — verificação proativa de worktree (Passo 0.VW)
- `3c568e4` fix: Mudança 7 — TaskOutput parâmetro correto + migração push-based
- `77fb790` fix: Mudança 6 — locks atômicos via mkdir (resolve race conditions)

---

## v4.0 (2026-04-17) — CRONOS orquestrador + hooks Python + worktrees

### Resumo

O CRONOS já existia desde o primeiro commit (2026-02-08) e virou papel de destaque na v3.2; na v4.0 ele entra em TODO projeto como orquestrador (independente de complexidade). Agent tool nativo com `run_in_background: true` e `isolation: worktree`. SendMessage para comunicação peer-to-peer. Arquitetura dupla (worktree isola código, kanban permanece compartilhado). Merge guiado por testes de contrato.

### Commits principais

- `17c16ad` feat: Alavanca 3 (lembrete inline BC) em 7 operativos
- `f47841d` sync: atualizar .last-update v4.0 e sincronizar.sh com *.py hooks
- `1938e3e` feat: v4.0 — CRONOS orquestrador + hooks Python cross-platform + worktrees + merge guiado
- (preparação, 2026-04-03 a 2026-04-05:)
- `d31b1c3` feat: ferramentas especializadas CRONOS + BACK, expandir conhecimento ATLAS
- `421ce39` feat: completar capacitação — bases de conhecimento para CRONOS, BACK e SCOUT
- `8c1a1e6` feat: especialização real por agente — perfis, ferramentas, conhecimento e modelos
- `210bc5e` feat: padronizar sub-agentes — Build Validator + Code Simplifier + Contract Tester

---

## Versões anteriores (resumo, a partir do git da fonte oficial)

O git da fonte oficial começa em 2026-02-08. Não há registro de "v1.x" nem de "v2.x" no repositório: o primeiro
commit já traz os 10 operativos (ATLAS, CRONOS, FRONT, PIXEL, FORM, BACK, ENGINE, VAULT, SHIELD, SCOUT), o kanban, o
project-core e o painel.

- **2026-02-08** (`342a7e1`, `0501e50`, `60c7447`) — identidade e missão da Formação Δ-11, prevenção estrutural e
  regras de manutenção; protocolo de auto-dispatch; modelos por papel (Opus para planejamento e diagnóstico, Sonnet
  para construção).
- **v3.1 (2026-02-09)** (`e39d622`, `4a06fad`) — sistema de sub-agentes, sinal visual FINALIZADO e protocolo de
  atualização do sistema.
- **2026-02-10 a 2026-02-17** — validação de screenshots, revisão do SHIELD obrigatória, auto-dispatch por
  AppleScript (Terminal.app e aba do VS Code), Golden Path com `build-validator` + `task-done.sh` e `code-simplifier`
  obrigatório (`ff47785`).
- **v3.2 (2026-02-15)** (`5082500`) — Fase 2.5, CRONOS com papel de coordenação e Code Architect.
- **2026-02-19 a 2026-03-09** — `schema-validator`, correções do auto-dispatch (janela certa, projeto certo),
  base de boas práticas, `sincronizar.sh` com detecção automática de projetos.
- **2026-03-10** (`753074c`, `3a5e80a`) — Two-Phase Dispatch com arquivos ACK e os **primeiros hooks**
  (rastreamento em tempo real: hooks, travas e activity-log).
- **2026-03-12** — repositório preparado para acesso público; painel kanban preto e vermelho.
- **2026-03-31 a 2026-04-01** — Contract-First Protocol e Caminho Crítico do CRONOS; ATLAS com checklist de ativação;
  `vigilante.sh`, `disparar.sh` multiplataforma, hooks + LaunchAgent invisível e sprites dos operativos no painel.
- **2026-04-03 a 2026-04-05** — preparação da v4.0 (ver a entrada v4.0).

Para ver tudo o que veio antes da v4.0: `git log --before="2026-04-17" --oneline` na fonte oficial.

---

## ADIÇÕES POSTERIORES

Quando alguém quiser retificar ou complementar uma entrada publicada, adiciona aqui com data + referência. Uma
correção feita direto numa entrada antiga fica registrada aqui com o que estava escrito antes.

### 2026-10-14 — Retificações da v6.3 (itens C-164 a C-168 do caderno de melhorias)

Conferidas contra `git log --format='%h %ci %s'` da fonte oficial. As entradas foram corrigidas no lugar; o que
estava escrito antes fica registrado abaixo.

- **C-164 — v5.4 duplicada e fora de ordem.** Havia duas entradas "v5.4": "Estágios 0-3" (logo após a v6.0, com
  7/7 testes) e "Estágios 0-7 (3 skills globais)" (depois da v5.1, com 8/8). As duas viraram UMA entrada, no lugar
  certo (entre a v6.0 e a v5.3), com a régua 3/3 (E0) → 7/7 (E1, E2) → 8/8 (E3 a E7).
- **C-165 — contagens.**
  - v5.4: "14 estágios" / "14/14 (E0-E7)" → 8 estágios (E0 a E7) em 12 commits; "4 existentes atualizadas (ENGINE,
    PIXEL, VAULT)" → 3; "111 testes nas skills" → 114 (32 + 47 + 35, os números da própria entrada); "18 projetos"
    → "os projetos do registro" (o número não tinha fonte; o monitor listava 11 a 12). A lista de commits ganhou os 5
    que faltavam (`c27fa2e`, `11a68cd`, `1215a47`, `4781ed1`, `9a7c477`).
  - v6.0: "11 commits" na lista → 12 (faltava `7bc9260`, E10); "11 suites adicionadas" → 19 testes (8 → 27).
  - v6.1: "32/32" → 33/33 no merge (32 era a conta antes do teste consolidado `dispatch-v61-consolidado`); "9 testes
    novos" → 10 (4 em `tests/operativos/`, que o `rodar-todos.sh` da época não rodava, e 6 em `tests/protocolos/`);
    "9 commits" → 9 + 1 de consolidação (`60952bf`).
  - v6.2: "44/44" → 45/45 no merge (44 era antes do teste consolidado `v62-consolidado`); "11 testes" → 12; "6
    commits" → 6 + 1 de consolidação (`4994c0c`).
  - Cabeçalho: "sincronizado para os 18 projetos" → "todos os projetos do registro central".
- **C-166 — linha do tempo do code-simplifier.** A v5.3 dizia que a Onda 3 (2026-07-07) "padronizou build-validator,
  code-simplifier e contract-tester" — dois dias depois da remoção do code-simplifier (2026-07-05). Pelo git, a
  padronização foi em 2026-04-03 (`210bc5e`) e a Onda 3 (`c6de931`) trouxe outra coisa: autocrítica em 2 paradas,
  anti-falso-positivo do SCOUT, rastreabilidade no mini-plano, evidência por tipo no SHIELD, nota em 4 dimensões e
  SISTEMA IMUNE. A remoção (`f03c64e`, `bacd3e8`) e a limpeza de 2026-07-07 passaram para "Antes das Ondas".
- **C-167 — datas que contradiziam o git.**
  - v4.0: "2026-06-XX" → 2026-04-17 (`1938e3e`).
  - v4.0.4: "2026-06-XX" → 2026-04-18 a 2026-05-27 (`77fb790` a `892b068`, mais `b8e8b43` e `bd210fc`, que estava
    listado por engano na v5.0).
  - v5.0: "2026-06-30" → 2026-07-01 (`b070b2f`). v5.1: "2026-07-02" → 2026-07-01 (`7ef0396`); os commits
    "painel v6 a v12" de 2026-07-02 entraram na v5.1.
  - v5.3: Bloco A "2026-07-07" → 2026-07-09 (`fa9ee08`).
  - "Versões anteriores": "v3.x (2026-05) sem CRONOS", "v2.x (2026-04) sem hooks" e "v1.x (2026-03)" foram trocados
    pelo resumo tirado do git. O CRONOS existe desde o primeiro commit (2026-02-08); os primeiros hooks são de
    2026-03-10; não há v1.x nem v2.x no repositório. O comando sugerido `git log --before="2026-06-01"` virou
    `--before="2026-04-17"`.
- **C-168 — esta seção estava vazia** ("Nenhuma ainda") apesar dos erros acima. Passa a registrar as retificações.
- **Outras correções pequenas:** o "Como testar" da v5.2 usava `/tmp/test-event.json` → `.delta-11/scratch/` (D21),
  e o da v5.4 perdeu o passo `ls -la /tmp/*.skill` (os pacotes das skills eram temporários);
  "Quem escreve" deixa de citar CRONOS e ATLAS (este arquivo é de sistema, mantido na fonte oficial e sobrescrito nos
  projetos pelo `sincronizar.sh`).
- **v6.4.1 (2026-10-15) — ciclo leve aceita documentos completos do ciclo atual.** Na v6.4, do Ciclo 2 em diante, os
  vigias `fase-ritmo-checker.py` e `fase-consciencia-checker.py` só aceitavam o checklist do ciclo: um projeto que fez
  os 10 (ou 5) documentos COMPLETOS no próprio ciclo (caso real: salvahacks, Ciclo 5, documentos de 14/10) seria
  bloqueado no selo. Agora esses documentos também liberam o selo, desde que cada um cite "Ciclo N" no texto;
  documentos herdados de ciclos anteriores continuam não valendo. `_comum.phase_artifacts` ganhou o parâmetro `ciclo`.
  Testes novos nos dois arquivos de `tests/hooks/`; conferido com uma cópia dos documentos reais do salvahacks.
- **v6.4.1 (2026-10-15) — `sincronizar.sh` não pula mais projeto real criado por instalador antigo.** A regra C-057
  tratava como "cópia do sistema" toda pasta com `.delta-11/CHANGELOG.md` + `sincronizar.sh` na raiz; projetos reais
  cujo instalador antigo copiou tudo para a raiz (scanner-de-desvantagens-v3, cofre-de-keys) ficavam sem atualização.
  Agora só é cópia se a raiz não tiver NADA além dos arquivos do próprio sistema (`RAIZ_DO_SISTEMA`). E as ferramentas
  da fonte (`sincronizar.sh`, `instalar.sh`, `novo-projeto.sh`) que sobraram na raiz dos projetos saem de lá (só as que
  são do Δ-11; um arquivo do usuário com o mesmo nome é preservado). Caso novo em `tests/scripts/sincronizar.test.sh`.
- **v6.4.1 (2026-10-15) — a sincronização mantém o modelo que o projeto escolheu para cada agente.** Os
  `perfis/*.json` eram copiados inteiros da fonte, e o campo `model` (decisão do projeto: no salvahacks, SHIELD =
  sonnet, `decisoes-tecnicas.md` §6) voltava ao padrão a cada sincronização (já tinha acontecido na v6.2). Agora o
  resto do perfil vem da fonte e o `model` que o projeto já tinha é preservado; a saída avisa "modelo do projeto
  mantido". Casos novos em `tests/scripts/sincronizar.test.sh`.
- **v6.4.1 (2026-10-15) — 2 vigias novos, nascidos da retomada do salvahacks depois do reinício do Mac** (o ATLAS
  percebeu os dois furos sozinho; agora o sistema percebe):
  - `sistema-no-historico.py` (PreToolUse `Agent|Task`): a worktree nasce do último COMMIT, não do disco. Regras do
    sistema atualizadas e não commitadas (depois de um `sincronizar.sh`, por exemplo) fariam os agentes em worktree
    lerem as regras antigas. O vigia bloqueia o despacho em worktree e mostra o comando que commita só os arquivos de
    sistema (o código do projeto não entra).
  - `retomada-apos-queda.py` (SessionStart, exceto a volta da compactação): os agentes morrem junto com a sessão
    principal, mas o `kanban-data.js` e o `pulsos-data.js` continuam dizendo "em andamento". Na sessão nova, o vigia
    avisa quais são esses itens e manda conferir o disco antes de redisparar ou de esperar por eles.
  Testes: `tests/hooks/sistema-no-historico.test.sh` e `tests/hooks/retomada-apos-queda.test.sh`. Total: 36 vigias.
- **v6.4.1 (2026-10-15) — fim do laço de retomadas: o `anti-autocompact.py` usa a janela do MODELO.** O padrão fixo
  de 200 mil tokens (alerta em 170 mil) travava CRONOS e SHIELD logo depois de nascer: só as leituras obrigatórias
  (CLAUDE.md, operativo, kanban, project-core) passam de 120 mil. Cada retomada relia tudo e era travada de novo
  (salvahacks, 2026-10-15: 3 bloqueios seguidos; o ATLAS diagnosticou). Medição nas conversas reais do comandante:
  sonnet-5-5 chegou a 723 mil e opus-5-5 a 966 mil sem problema. Agora a janela vem do `message.model` da própria
  conversa: Claude 5 (opus, sonnet, fable), opus 4.7/4.8 e sonnet 4.6 = 1 milhão (alerta em 850 mil); haiku ou modelo
  desconhecido = 200 mil (cautela). O projeto ainda pode forçar um valor com `contexto_janela_tokens` > 0 no
  `.config-limites.json` (o padrão passou a ser 0 = automático). Alteração autorizada pelo comandante (o sistema de
  permissões tinha barrado a mudança no vigia, pedida primeiro pelo ATLAS). Casos novos em
  `tests/hooks/anti-autocompact.test.sh`.
- **v6.4.1 (2026-10-15) — `.gitignore` protege o cache do Python.** Os vigias são Python; rodar um deles à mão cria
  `.delta-11/hooks/__pycache__/`, que um `git add -A` levaria para o histórico (achado no salvahacks). `__pycache__/` e
  `*.pyc` entram na lista de proteção do `sincronizar.sh`, do `novo-projeto.sh` e do `instalar.sh`.
- **v6.4.1 (2026-10-15) — o `anti-autocompact.py` usa UM número só (substitui a entrada "janela do MODELO" acima).**
  O comandante apontou que uma lista de nomes de modelos quebra a cada lançamento da Anthropic (modelo novo fora da
  lista voltaria aos 200 mil e ao laço de retomadas, sem ninguém perceber), e que o Delta-11 não usa Haiku. Agora:
  `contexto_janela_tokens` = 1.000.000 por padrão para todos os agentes (alerta em 850 mil), sem lista de modelos; o
  projeto que usar um modelo de janela menor ajusta o número no `.config-limites.json`. O Claude Code não informa a
  janela aos vigias (documentação oficial: só a barra de status recebe `context_window`), por isso o número é fixo.
- **v6.4.1 (2026-10-15) — exceção do Haiku no `anti-autocompact.py`.** Pedido do comandante: agente que usar Haiku
  (nome do modelo na conversa contém "haiku") tem janela de 200 mil (alerta em 170 mil), só ele; os demais seguem com
  1 milhão. Fica no vigia (automático), e não no `.config-limites.json`, porque esse arquivo vale para o projeto
  inteiro: baixar o número para 200 mil travaria de novo os agentes em Opus e Sonnet. Aviso também em CLAUDE.md
  ("Modelo por papel") e em `protocolos/comunicacao.md`.
