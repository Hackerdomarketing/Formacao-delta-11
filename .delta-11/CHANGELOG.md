# CHANGELOG — Formação Δ-11

**O que é:** documento único que conta a história das versões do Sistema Δ-11 em formato narrativo (por que, o que, como testar). Complementa o git log — **não substitui**. Git é fonte da verdade de mudanças atômicas; este arquivo é fonte da verdade de ARQUITETURA e DECISÃO.

**Onde vive:** `.delta-11/CHANGELOG.md` — sincronizado para os 18 projetos via `./sincronizar.sh`.

**Quem lê:**
- O **comandante humano** (Rafa) — para entender o que mudou entre versões sem ler 50 commits.
- Um **novo agente** que acabou de ser ativado — para entender o estado atual do sistema sem ler 50 commits.
- O **próximo mantenedor** (qualquer pessoa que herdar o sistema) — para entender por que decisões foram tomadas.

**Quem escreve:**
- O **CRONOS** ao final de cada onda/bloco concluído (cria a entrada).
- O **ATLAS** ao final de cada Fase do fluxo (revisa entradas técnicas).

**Regra de manutenção:**
- Cada entrada vira IMUTÁVEL depois de publicada (estilo ADR). Correções vão em "ADIÇÕES POSTERIORES" no fim.
- Formato padronizado: **Por que existe** → **O que mudou** → **Como testar** → **Commits desta versão**.

---

## v5.4 (2026-07-10) — Estágios 0-3 do plano de execução

**Versão anterior:** v5.3 (2026-07-07) — Onda 4 fechou com golden baselines + boilerplate.
**Autor:** Comandante Rafa + Claude Code (sequência de Estágios 0-3).
**Status:** Em produção nos 18 projetos.

### Por que essa versão existe

O sistema estava funcional, mas dois sintomas expunham doença estrutural:

1. **Regressões invisíveis** — o hook `pre-criacao-arquivo.py` tinha um bug silencioso (CASO D/E engolidos pelo B por ordem de checagem) que passou despercebido por 2 meses. O syncronizar.sh também tinha um bug crítico de self-sync que sobrescrevia o repo de distribuição com versão antiga de outro clone.

2. **Medição inexistente** — mudanças no sistema (operativos, bases de conhecimento, CLAUDE.md) eram avaliadas "no olhômetro". Não havia régua fixa para comparar versão A vs versão B.

A v5.4 inverte a lógica: **medir antes de crescer**. Estágio 0 criou a infra de teste automatizada; Estágios 1-2 fecharam furos; Estágio 3 documenta tudo.

### O que mudou

#### Estágio 0 (2026-07-10) — Infraestrutura de teste e medição

**O que:** Criação do `.delta-11/tests/` (pastas `hooks/`, `templates/`, `scripts/`) com orquestrador `rodar-todos.sh`. Migrados os 9 casos validados do F2 para `tests/hooks/pre-criacao-arquivo.test.py`. Adicionado `.delta-11/tests/**` ao loop de sincronização. Criado `golden-baselines/rodar-comparacao.sh` (prepara execuções datadas). Allowlist `Read(~/.claude/skills/**)` no settings-hooks.json. `novo-projeto.sh` agora cria `.delta-11/memoria/gotchas.md` no dia 1 (F5).

**Por que:** Antes desta versão, "qual versão do Δ-11 é melhor" era respondido por impressão. Agora há régua: 3/3 OK (E0) → 7/7 OK (E1) → 7/7 OK + 10 goldens (E2).

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

**O que:** 7 tarefas canônicas novas (ATLAS, CRONOS, BACK, FRONT, FORM, SHIELD, SCOUT) totalizando 10 tarefas cobrindo TODOS os agentes. Baseline v5.4 gerada em `golden-baselines/execucoes/2026-07-10-v5.4-baseline/` com 10 prompts + gabaritos. `rodar-comparacao.sh` reescrito com extração Python (cross-platform — sed do macOS não suporta `/I`).

**Por que:** A régua de comparação antes cobria só 3 agentes (ENGINE, PIXEL, VAULT). Era como medir a qualidade de um time testando só 3 dos 10 jogadores.

**Bug crítico resolvido durante E2:** SELF-SYNC GUARD adicionado em `sincronizar.sh`. O registry global apontava para um clone desatualizado em `~/projetos/Formacao-delta-11`, e o `sincronizar.sh` propagava arquivos DAQUELE clone PARA o repo real em `~/Documents/VSCODE/Formacao-delta-11`, sobrescrevendo correções com versões antigas. O guard compara `proj_dir` com `SCRIPT_DIR` e pula com aviso amarelo se forem iguais (self-sync). Registry atualizado para o path real.

#### Estágio 3 (2026-07-10) — Este CHANGELOG

**O que:** Este documento. Conta a história v5.2 → v5.4 em formato narrativo.

### Como testar

```bash
# Suite completa automatizada
bash .delta-11/tests/rodar-todos.sh

# Esperado: 7/7 OK (3 do E0 + 4 do E1/E2)

# Fail-fast se hook de segurança regrediu
bash .delta-11/tests/rodar-todos.sh --hooks pre-criacao-arquivo

# Re-rodar comparação de goldens
bash golden-baselines/rodar-comparacao.sh v5.4.1   # cria nova rodada para comparar com v5.4-baseline
```

### Commits desta versão

- `2b16664` feat(v5.4 E2): 7 tarefas canônicas novas + baseline v5.4 + self-sync guard
- `fa5bcf0` feat(v5.4 E1): fechar 10 furos restantes do Bloco A (G1-G4) + 4 novos testes + baseline v5.3
- `9a7c477` fix(v5.4 E0): reordenação dos casos D/E/F antes de B + path absoluto do hook no teste
- `512b35b` feat(v5.4 E0): infra de teste automatizada + allowlist skills + bootstrap gotchas

---

## v5.3 (2026-07-07) — Onda 4 + Bloco A (5 furos críticos)

**Versão anterior:** v5.2 (2026-07-03) — Ciclo de Zoneamento Documental.
**Autor:** Comandante Rafa + Claude Code (Onda 1-4 + auditoria).
**Status:** Versão base usada pela v5.4 como comparação.

### O que mudou

#### Onda 1 (2026-07-07) — Limites estruturais de código

**O que:** Implementação das regras da seção 8 de `regras-codigo.md` (limites estruturais: função ≤ 50 linhas, arquivo ≤ 400 linhas, aninhamento ≤ 3, complexidade ciclomática ≤ 10). Convenção de idioma (inglês em código, português em conteúdo). Sentry obrigatório pré-deploy.

**Por que:** As regras existiam no papel mas não havia enforcement. Esta onda implementou.

#### Onda 2 (2026-07-07) — Design patterns + ADR + bug report + PRD

**O que:** Base de conhecimento `design-patterns-praticos.md` (10 padrões GoF filtrados pelos mais úteis no Δ-11). Templates: `adr-registro-de-decisao-arquitetural-template.md`, `bug-report-template.md`, `prd-documento-de-requisitos-template.md`. Função de auditoria de completude.

**Por que:** O sistema não tinha templates canônicos para os 3 tipos de documentos mais importantes (decisão, bug, requisitos). Cada agente inventava formato.

#### Onda 3 (2026-07-07) — Mecanismos de qualidade

**O que:** Sub-agentes `build-validator`, `code-simplifier` (removido em 2026-07-05), `contract-tester` padronizados em todos os agentes de execução. Cadeia obrigatória ao final de cada tarefa.

**Por que:** Sem quality gate automático, a revisão do SHIELD era inconsistente.

**Nota histórica:** o `code-simplifier` foi removido em 2026-07-05 por decisão do comandante. Era otimizador terminal — ninguém consumia seu output para decisão. Responsabilidade por legibilidade passou aos executores durante a escrita + revisão do SHIELD. Mudança documentada em 5 lugares (CLAUDE.md + 4 sub-agentes).

#### Onda 4 (2026-07-07) — Golden baselines + boilerplate

**O que:** Pasta `golden-baselines/` com 3 tarefas canônicas (ENGINE, PIXEL, VAULT) + rubrica de avaliação. Boilerplate Next.js (`boilerplate-delta-11-nextjs/`) com `aplicar-boilerplate.sh` + overlay (env, error-response, monitoramento-de-erros, eslint).

**Por que:** Antes desta onda, não havia como medir regressão de qualidade entre versões do Δ-11. Também não havia scaffold testado para começar um projeto Next.js sem repetir 30 decisões tediosas.

#### Bloco A da auditoria (2026-07-07) — 5 furos críticos

**O que:** Correção de F1 (paths canônicos), F2 (hook zoneamento documental), F3 (Golden Path de tarefa), F8 (autocrítica no produto.md), F13 (interface billing).

**Por que:** Auditoria da v5.2 identificou 23 deficiências; este Bloco fechou as 5 mais urgentes (cirúrgicas, sem mudança de arquitetura).

### Como testar (goldens)

```bash
bash golden-baselines/rodar-comparacao.sh v5.3-baseline   # já gerada
# Esperado: MANIFESTO + 3 subdirs com prompt-de-ativacao + gabarito
```

### Commits desta versão

- `fa9ee08` fix: Bloco A da auditoria — os 5 furos mais urgentes da v5.3
- `43b5fd5` feat: Onda 4 — golden baselines + boilerplate overlay Next.js
- `c6de931` feat: Onda 3 — mecanismos de qualidade importados dos squads de programação
- `68e6f4a` feat: Onda 2 — design patterns, ADR, bug report, PRD e auditoria de completude
- `7f1b1ef` feat: Onda 1 — limites estruturais de código, convenção de idioma, Sentry obrigatório

---

## v5.2 (2026-07-03) — Ciclo de Zoneamento Documental (23 mudanças em 4 pilares)

**Versão anterior:** v5.1 (2026-07-02) — Painel de Comando redesenhado para comandante humano.
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
python3 .delta-11/hooks/pre-criacao-arquivo.py < /tmp/test-event.json
echo $?   # 2 = bloqueou, 0 = liberou

# Suite automatizada desta versao (v5.2)
bash .delta-11/tests/rodar-todos.sh
```

### Commits desta versão

- `83e1293` feat: v5.2 — Ciclo de Zoneamento Documental (23 mudanças em 4 pilares)
- `a2d98f3` fix: guarda técnica contra bug #39886 + hooks v5 finalmente ativados nos projetos
- `84d7b95` fix: sincronizar.sh reescreve projects[] do registry a cada sync

---

## v5.1 (2026-07-02) — Painel de Comando redesenhado

**Versão anterior:** v5 (2026-06-30) — granularização + hooks Python + modo-selo configurável.
**Autor:** Comandante Rafa + Claude Code.
**Documentação:** `.delta-11/CHANGELOG-painel-v5.1.md` (detalhes completos).

### Resumo

Painel de Comando (`painel.html`) redesenhado para o **comandante humano** (não para os agentes). Antes: 4 colunas kanban com IDs de tarefa e timestamps ISO. Depois: coluna vertical com selo binário grande (verde/amarelo/vermelho), voz do CRONOS em português leigo, e `resumo_humano` em cada tarefa.

### Commits desta versão

- `7ef0396` feat: v5.1 — Painel de Comando redesenhado para comandante humano
- `4fa10cc` fix: restaura identidade visual Δ-11 no painel v5.1

---

## v5.4 (2026-07-10) — Estágios 0-7 do plano de execução (3 skills globais)

**Versão anterior:** v5.3 (2026-07-07) — Onda 4 fechou com golden baselines + boilerplate.
**Autor:** Comandante Rafa + Claude Code (14 estágios sequenciais, 7 sessões de skills).
**Status:** Em produção nos 18 projetos. 3 skills globais instaladas em `~/.claude/skills/`.

### Por que essa versão existe

O sistema estava funcional, mas faltava **medição** (regressões invisíveis), **cobertura de RLS** (vazamentos silenciosos), **segurança** (CVEs do stack sem defesa), e **conhecimento de debugging React/Next** (tela branca frequente). v5.4 inverteu a lógica: "medir antes de crescer" → "infra de teste + furos fechados" → "skills globais" → "consolidação".

### O que mudou

#### Estágio 0 — Infraestrutura de teste automatizada
- **`.delta-11/tests/`** criado com `rodar-todos.sh` orquestrando 8 testes
- Suite pega bug real: hook `pre-criacao-arquivo` tinha CASO D/E engolidos por CASO B
- Fail-fast em `pre-criacao-arquivo.test.py` (se hook regredir, suite para)
- `novo-projeto.sh` agora cria `.delta-11/memoria/gotchas.md` (F5 fechado)
- Allowlist `Read(~/.claude/skills/**)` em `settings-hooks.json`

#### Estágio 1 — Bloco A: 10 furos fechados
- **F4:** exemplo preenchido em `estado-produto-template.md` (~470 tokens, dentro do orçamento)
- **F6 + F11 + F12:** `env.example` cita Regra 15; `aplicar-boilerplate.sh` recusa projeto sem `src/`; backup datado
- **F15:** seção Adapter cita Regra 14 → Regra 15 → Adapter (sequência completa)
- **F9 + F10 + F14:** `Última atualização` em 3 tarefas; critério subjetivo removido; `execucoes/.gitignore`

#### Estágio 2 — 10 tarefas canônicas (todos os agentes cobertos)
- 7 novas tarefas: ATLAS, CRONOS, BACK, FRONT, FORM, SHIELD, SCOUT
- 4 existentes atualizadas (ENGINE, PIXEL, VAULT)
- **Baseline v5.3** + **v5.4** em `golden-baselines/execucoes/` (comparativos obrigatórios)

#### Estágio 3 — CHANGELOG do sistema
- Este arquivo. Narrativa por versão (v5.4 → v5.3 → v5.2 → v5.1 → v5.0 → v4.0.4 → v4.0)
- Regra de imutabilidade: entradas publicadas viram ADR-like; correções vão em ADIÇÕES POSTERIORES

#### Estágio 4 — Skill `supabase-rls` (Skill Forge v3 Deep Path)
- **Pipeline:** Stage A (16 fontes, 35 claims, 32 armadilhas) → Stage B (14 princípios, 26 heurísticas, 32 testes) → Stage C (12 arquivos)
- **6.676 linhas** em `~/.claude/skills/supabase-rls/`: SKILL.md (172) + 10 references (4.459) + evals.json (221)
- **Empacotada** em `/tmp/supabase-rls.skill` (83.9 KB)
- Cobre: 7 padrões canônicos (P1-P7), multi-tenancy (3 estratégias), 32 testes, 26 heurísticas, 4 analogias, 8 invariantes + 7 anti-invariantes
- CVEs específicos: nenhum específico de RLS, mas cobre RLS bypass silencioso (G-001 canônico)
- Base curta D-11: 149 linhas (gate para skill completa)

#### Estágio 5 — Skill `owasp-top10` (Skill Forge v3 Deep Path)
- **Pipeline:** Stage A (16 fontes, 53 claims, 51 armadilhas, 5 CVEs) → Stage B (36 princípios, 32 heurísticas, 47 testes, 10 diagnostic flows) → Stage C (12 arquivos)
- **7.374 linhas** em `~/.claude/skills/owasp-top10/`: SKILL.md (192) + 10 references (6.961) + evals.json (221)
- **Empacotada** em `/tmp/owasp-top10.skill` (90.2 KB)
- Cobre: **10/10 categorias OWASP 2021** (A01-A10), 25 padrões canônicos (PAT-001 a PAT-025), 44 anti-padrões (ANTI-001 a ANTI-044) com CVEs
- **CVEs principais:** CVE-2024-34351 (SSRF Server Actions) + CVE-2025-29927 (Middleware bypass CRITICAL) + 3 adicionais
- 5 configs canônicas (headers, CORS, cookies, JWT, env vars)
- 47 testes executáveis (20 CRITICAL + 21 HIGH + 6 MEDIUM)
- Base curta D-11: 118 linhas (gate)

#### Estágio 6 — Skill `react-next` (Skill Forge v3 Deep Path)
- **Pipeline:** Stage A (16 fontes, 44 claims, 45 armadilhas) → Stage B (20 princípios, 31 heurísticas, 35 testes, 6 debugging flows) → Stage C (12 arquivos)
- **5.466 linhas** em `~/.claude/skills/react-next/`: SKILL.md (167) + 10 references (5.113) + evals.json (186)
- **Empacotada** em `/tmp/react-next.skill` (59.5 KB)
- Cobre: Server vs Client Components, hooks React 19, Server Actions, performance, testing, debugging reativo (5 árvores: hydration/infinite loop/memory/race/RSC), stack-specific Next.js 15
- **22 padrões canônicos** (PAT-01 a PAT-22) + **32 anti-padrões** (ANTI-001 a ANTI-032)
- 10 perguntas antes de commitar componente
- BUG #1 documentado: **Esquecer `revalidatePath` em Server Action = UI não atualiza**
- Base curta D-11: 102 linhas (gate)

#### Estágio 7 — Consolidação final
- CHANGELOG atualizado (este arquivo)
- 3 skills globais instaladas e testadas
- Suite D-11: **8/8 OK** (nada regrediu)
- 18 projetos sincronizados

### Estatísticas v5.4

| Métrica | Valor |
|---|---|
| **Estágios completados** | 14/14 (E0-E7) |
| **Custo total** | ~17h45 |
| **Skills globais criadas** | 3 (supabase-rls, owasp-top10, react-next) |
| **Linhas de skill autorais** | 19.516 (6.676 + 7.374 + 5.466) |
| **Arquivos em skills** | 36 (12 + 12 + 12) |
| **CVEs cobertos** | 2 CRITICAL + 3 HIGH |
| **Anti-padrões catalogados** | 145 (32 RLS + 44 OWASP + 32 React + 37 deduzidos) |
| **Padrões canônicos** | 54 (7 RLS + 25 OWASP + 22 React) |
| **Bases curtas do D-11** | 3 (uma por skill) |
| **Testes automatizados** | 8 (D-11) + 111 (skills) |
| **Projetos sincronizados** | 18 |

### Como testar

```bash
# 1. Suite automatizada do D-11 (deve passar 8/8)
bash .delta-11/tests/rodar-todos.sh

# 2. Validar cada skill
for skill in supabase-rls owasp-top10 react-next; do
  cd ~/.claude/skills/skill-forge
  /opt/homebrew/bin/python3.12 scripts/forge_validate.py /Users/alfa/.claude/skills/$skill
done

# 3. Sincronizar para os 18 projetos
cd ~/Documents/VSCODE/Formacao-delta-11
./sincronizar.sh --nota "Verificar v5.4 instalado: 3 skills globais"

# 4. Empacotado em /tmp/
ls -la /tmp/*.skill
# /tmp/supabase-rls.skill (83.9 KB)
# /tmp/owasp-top10.skill (90.2 KB)
# /tmp/react-next.skill (59.5 KB)
```

### Commits desta versão (v5.4)

(commits principais — a lista completa está em `git log --oneline`)

- `512b35b` feat(v5.4 E0): infra de teste automatizada + allowlist skills + bootstrap gotchas
- `fa5bcf0` feat(v5.4 E1): fechar 10 furos restantes do Bloco A (G1-G4) + 4 novos testes + baseline v5.3
- `2b16664` feat(v5.4 E2): 7 tarefas canônicas novas + baseline v5.4 + self-sync guard
- `c80bff3` feat(v5.4 E3): CHANGELOG.md do sistema + loop de sync + teste de regressão
- `a323120` feat(v5.4 E5.1): skill owasp-top10 — 5 novos references adicionados
- `eda8b21` feat(v5.4 E5.4): skill owasp-top10 — monitoring, IR, mental model, testes, heurísticas, evals
- `d496865` feat(v5.4 E6.1): skill react-next (sessão 6.1) + base curta do D-11

---

## v5.0 (2026-06-30) — Granularização + hooks Python

### Resumo

Granularização dos agentes (perfis, ferramentas, conhecimento, modelos separados por papel). Hooks Python cross-platform (substituindo AppleScript). Modo-selo configurável (manual vs automático).

### Commits principais

- `b070b2f` feat: v5 — granularização + hooks Python + modo-selo configurável
- `bd210fc` feat: v4.0.4 — isenção do limite de 500 tokens para ATLAS e CRONOS

---

## v4.0.4 (2026-06-XX) — Mudanças 1-17 da Criação

### Resumo

Adição das 17 mudanças estruturais baseadas na Geometria da Criação (M4 do framework). Inclui: fatias de domínio do project-core, abertura de fase, fresh reviewer, visão, viu que era bom, locks atômicos via mkdir, push-based task notifications, verificação proativa de worktree (Passo 0.VW).

### Commits principais

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

## v4.0 (2026-06-XX) — CRONOS orquestrador + hooks Python + worktrees

### Resumo

CRONOS entra em TODO projeto como orquestrador (independente de complexidade). Agent tool nativo com `run_in_background: true` e `isolation: worktree`. SendMessage para comunicação peer-to-peer. Arquitetura dupla (worktree isola código, kanban permanece compartilhado). Merge guiado por testes de contrato.

### Commits principais

- `17c16ad` feat: Alavanca 3 (lembrete inline BC) em 7 operativos
- `f47841d` sync: atualizar .last-update v4.0 e sincronizar.sh com *.py hooks
- `1938e3e` feat: v4.0 — CRONOS orquestrador + hooks Python cross-platform + worktrees + merge guiado
- `d31b1c3` feat: ferramentas especializadas CRONOS + BACK, expandir conhecimento ATLAS
- `421ce39` feat: completar capacitação — bases de conhecimento para CRONOS, BACK e SCOUT
- `8c1a1e6` feat: especialização real por agente — perfis, ferramentas, conhecimento e modelos
- `210bc5e` feat: padronizar sub-agentes — Build Validator + Code Simplifier + Contract Tester

---

## Versões anteriores (resumo)

- **v3.x** (2026-05) — AppleScript dispatch, sem worktrees, sem CRONOS. Sistema single-agent.
- **v2.x** (2026-04) — 10 agentes definidos, sem hooks, sem isolamento.
- **v1.x** (2026-03) — Fundação: 7 fases, regras invioláveis 1-13, kanban compartilhado.

Para detalhes anteriores a v4, consultar git log (formato: `git log --before="2026-06-01" --oneline`).

---

## ADIÇÕES POSTERIORES

_Nenhuma ainda._ Quando alguém quiser retificar ou complementar uma entrada publicada, adiciona aqui com timestamp + referência ao commit. Não edita entradas antigas.