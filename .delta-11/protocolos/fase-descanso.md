# Protocolo da Fase 7 — Descanso Consagrado (Dia 7 da Metodologia Gênesis)

> **Protocolo formal da Fase 7 que existe APÓS a Fase 6 (Preparação para Lançamento).**
> **Esta fase foi adicionada no v6.0.0 para corrigir o achado #7 da auditoria (Furo Grave).**
>
> **Cross-references:**
> - Fluxo principal: `.delta-11/protocolos/fluxo-zero-ao-lancamento.md` → seção "FASE 7 — DESCANSO CONSAGRADO"
> - Base conceitual: `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 7
> - Template dos 10 entregáveis: `.delta-11/templates/fase-descanso-template.md`
> - Hook bloqueante: `.delta-11/hooks/fase-descanso-checker.py`
> - Quem faz cada entregável: `fluxo-zero-ao-lancamento.md` → tabela "PAPEL DE CADA AGENTE NAS FASES 3.5, 4.5 E 7"
> - Skill global de runbooks IR: `~/.claude/skills/owasp-top10/references/07-incident-response.md`

## O que é o Dia 7 — em linguagem da Metodologia Gênesis

Texto hebraico chave (Gênesis 2:1-3):

> *vayechulu ha-shamayim ve-ha-arets ve-chol tzevaam* — "foram consumados os céus e a terra e todo o exército deles"
> *vayishbot ba-yom ha-shvii mi-kol melachtô* — "cessou no sétimo dia de toda sua obra"
> *vayvarech Elohim et yom ha-shvii vayekadesh otô* — "abençoou Deus o dia sétimo e o santificou"

Verbos hebraicos:
- **kalá** (consumar, terminar completamente)
- **shabat** (cessar intencionalmente, parar por escolha soberana — não por cansaço)
- **barach** (abençoar, consagrar com poder)
- **kadash** (santificar, separar do comum para o sagrado)

Significado: depois de criar todas as camadas, Deus **consagra o sistema** — declara que está terminado, sagrado, operável sozinho. No software, isso é quando o sistema atinge **operação autônoma**: o criador pode tirar férias e o sistema continua funcionando.

**Por que esta fase é DEPOIS da Fase 6 (Preparação) e não integrada:** Fase 6 é o **selo provisório** que permite colocar em produção. Fase 7 é o **selo definitivo** que fecha o ciclo. Entre as duas, o sistema precisa operar de verdade em produção pelo tempo mínimo. Lançar ≠ consagrar.

## A Diferença Crítica: Selo Provisório vs Definitivo

| Fase 6 (Provisório) | Fase 7 (Definitivo) |
|----------------------|----------------------|
| Deploy em produção | Operação autônoma comprovada |
| Sentry + verify-app funcionando | 2 semanas de operação estável |
| Funcionalidades entregues | Runbooks específicos do projeto |
| Acessos monitorados | Alertas com donos designados |
| Cada alerta tratado manualmente | Alertas resolvem-se sozinhos |
| Criador disponível 100% do tempo | Criador pode tirar férias |

Fase 6 = **terminou de construir**. Fase 7 = **consagrado como sistema autônomo**.

## O TESTE SUPREMO (critério diferenciador do Dia 7)

> *"Se o criador tirar 2 semanas de férias sem tocar no sistema, ele continua funcionando?"*

Se SIM → Dia 7 selado. **Operação autônoma comprovada.**

Se NÃO → o sistema **não consagra**. Voltar e consertar o que falta. Em ordem de probabilidade:
1. Falta runbook operacional (alguém precisa acordar de madrugada)
2. Alerta sem dono (ninguém recebe notificação)
3. Backup não testado (incidente expõe fragilidade)
4. Deploy manual (saiu cedo do trabalho pra deploy)
5. Onboarding quebrado (novo dev não consegue mexer no sistema sem o criador explicar)

O prazo é **2 semanas**, o mesmo em todo o sistema (fluxo, metodologia, monitor e hook). Um projeto crítico (saúde, financeiro) pode continuar sendo observado depois do selo, mas o selo do Dia 7 sai com 2 semanas.

## Os 10 entregáveis do Dia 7 — declaração completa

Cada entregável vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-descanso-<NN>-<slug>.md` (`<NN>` de 01 a 10; modelo em `fase-descanso-template.md`). Cada um tem: descrição, escolha, justificativa, link, **evidência de execução**.

### Entregável 1 — Documentação técnica consumada

**O que:** arquitetura, decisões (ADRs), diagramas atualizados, guias de contribuição. Estado: `docs/arquitetura/`, `.delta-11/memoria/decisoes/`.

**Critério de consagração:**
- README.md na raiz do projeto cobre: o que é, como rodar local, como deployar, troubleshooting básico
- ADRs das decisões significativas (pelo menos as 5 mais importantes documentadas)
- Diagrama de módulos e seus fluxos (atualizado, não desatualizado há 6 meses)

**Verificação prática:** pessoa nova segue só a documentação e consegue subir o projeto local em < 1 hora.

### Entregável 2 — Documentação de domínio consumada

**O que:** glossário do negócio, regras de negócio explicitadas, casos de uso descritos. Estado: `docs/dominio/` ou `docs/comandante/`.

**Critério de consagração:**
- Glossário com os 15-30 termos mais importantes do domínio
- Regras de negócio escritas em prosa (não enterradas em código)
- Casos de uso principais (5-10) com diagrama de fluxo

**Verificação prática:** Comandante (não-técnico) consegue ler a documentação de domínio e responder "como o sistema funciona pra X?" corretamente.

### Entregável 3 — Testes de aceitação E2E

**O que:** fluxos críticos cobertos com testes automatizados que rodam em CI. **Pelo menos os 5 fluxos mais importantes do produto.**

**Critério de consagração:**
- Cada teste E2E roda em CI (GitHub Actions, GitLab CI, etc.)
- Cada teste cobre um fluxo de usuário completo (cadastro → ação → resultado visível)
- Falha de teste E2E = pipeline falha = NÃO vai pra produção

**Verificação prática:** deletar o banco de staging, rodar CI, ver a app voltando do zero com seed automático.

### Entregável 4 — Pipeline de deploy automatizado

**O que:** de commit até produção, sem intervenção manual. Funciona em staging E produção.

**Critério de consagração:**
- CI roda lint + typecheck + testes + build + deploy em staging
- O deploy em produção só sai com o aval do comandante (é publicação externa — Regra 10); depois do aval, o pipeline faz o resto sozinho
- Rollback automático em caso de falha de smoke test pós-deploy

**Verificação prática:** pegar um PR, mergear, ver staging atualizar em < 30 min sem ninguém fazer nada.

### Entregável 5 — Runbooks operacionais específicos do projeto

**O que:** instanciados da skill global `owasp-top10` (`~/.claude/skills/owasp-top10/references/07-incident-response.md`) ou criados especificamente. Cobrem os **5 incidentes mais prováveis do produto**. Em `.delta-11/memoria/runbooks/`.

**Critério de consagração:**
- 5 runbooks no mínimo
- Cada runbook tem: sintoma, causa provável, comando de diagnóstico, ação de mitigação, escalonamento
- Cada runbook é **testado** (teste de mesa: o SCOUT simula o incidente e o dono segue o runbook)
- Cada runbook tem **dono** claro (quem é chamado se acontecer)

**Onde pegar material:** a skill global `owasp-top10` tem 10 runbooks genéricos de Incident Response (A01 a A10). Para cada runbook do projeto, comece do genérico e adapte ao domínio do seu produto.

**Exemplo de runbook "API externa X caiu":**
1. **Sintoma:** dashboard mostra success rate < 50%
2. **Causa provável:** X está fora do ar (ver status page)
3. **Diagnóstico:** `curl -I https://api.x.com/health`
4. **Mitigação:** ativar modo degradado (retornar cache), postar aviso no status público
5. **Escalonamento:** se > 1 hora, ligar para contato comercial X (telefone no runbook)

**Diferença entre runbook genérico e runbook específico:** runbook genérico é "se você ver X, faça Y". Runbook específico é "se a métrica M cair abaixo de T, faça Y, em até 30 min, e avise P". **Específico = operacional**.

### Entregável 6 — Monitoramento com dashboards + alertas ativos

**O que:** dashboards visíveis para SLOs do produto, alertas configurados COM dono (quem recebe notificação), níveis INFO/WARN/CRITICAL.

**Critério de consagração:**
- 1 dashboard principal com golden signals (latência, tráfego, erros, saturação)
- 1 dashboard por serviço crítico
- Cada alerta tem: sintoma (o que dispara), severidade, ação de mitigação, canal (Slack/email/SMS), dono

**Verificação prática:** simular um pico de erro 5x, ver alerta chegando ao dono em < 2 minutos.

### Entregável 7 — Tag de release

**O que:** git tag marcado, changelog de release publicado, binário/artefato arquivado.

**Critério de consagração:**
- Cada release consolidado tem tag git (ex: `v1.2.3`)
- Cada tag tem changelog gerado (Conventional Commits → CHANGELOG.md)
- Binário/artefato arquivado (S3, GitHub Releases, ou similar)
- Tag tem checksum / assinatura (proteção contra tampering)

**Verificação prática:** pegar uma tag antiga, tentar deployar a partir dela, ver que tudo funciona idêntico ao release.

### Entregável 8 — Backup testado

**O que:** rotina de backup rodando, último restore executado **evidenciado** (não é teórico — foi feito de verdade).

**Critério de consagração:**
- Backup automático configurado (cron ou gerenciado)
- Frequência documentada (diário / hora, conforme criticidade)
- Retenção documentada (30 dias / 1 ano / permanente)
- **Restore TESTADO pelo menos uma vez por trimestre**: backup → banco novo → app funcionando
- Evidência: log do teste, screenshot do banco novo funcionando, ou relatório automatizado

**Verificação prática:** deletar banco de produção (em staging), restaurar do backup de ontem, ver tudo voltando.

### Entregável 9 — DR testado (Disaster Recovery)

**O que:** disaster recovery **executado em ambiente isolado**, tempo de recuperação (RTO) medido.

**Critério de consagração:**
- Plano DR documentado (o que conta como "desastre", como recuperar)
- Runbook de DR executado pelo menos 1x (em staging isolado)
- RTO medido e documentado (ex: "se região A cai, região B assume em 30 min")
- RPO documentado (quantos minutos de dados posso perder — ex: "máx 5 min por replicação assíncrona")
- Failover testado também (voltar pra região A depois)

**Verificação prática:** desligar a região A em staging (simulado), ver app respondendo pela região B em < RTO documentado.

### Entregável 10 — Onboarding testado com pessoa nova

**O que:** pelo menos 1 pessoa nova leu a doc e conseguiu fazer deploy local + 1 alteração pequena em < 1 dia.

**Critério de consagração:**
- Pessoa nova (não envolvida no desenvolvimento) escolhida
- Lê a documentação (Entregáveis 1 e 2)
- Faz deploy local sem pedir ajuda ao criador
- Faz 1 alteração pequena em < 1 hora (ex: muda copy de botão, troca cor)
- Reporta o que foi difícil → documentação atualizada

**Verificação prática:** trazer dev novo, cronometrar, capturar onde travou.

## O TESTE SUPREMO como entregável de selo

Os 10 entregáveis acima são os **pré-requisitos** para o teste supremo rodar. Mas o teste supremo em si é **um entregável também**:

- 2 semanas de operação estável em produção sem intervenção do criador (o período de observação começa quando o CRONOS confirma os 10 entregáveis)
- O comandante registra: "Resultado do teste supremo: [SIM / NÃO]" (o CRONOS faz a pergunta, em linguagem simples, ao fim das 2 semanas)
- Se SIM → Dia 7 selado
- Se NÃO → volta para Fases anteriores conforme o que falhou

## Incidente durante o período de observação

Não existe "Fase 7.5". Incidente é um **acontecimento**, não uma camada da Criação: ele pode surgir a qualquer momento das 2 semanas (e depois delas), por isso é tratado DENTRO da Fase 7, assim:

1. **Quem detecta** (alerta do entregável 6, Sentry, monitor ou o comandante) avisa o CRONOS.
2. **O runbook manda.** O dono segue o runbook específico daquele sintoma (entregável 5). Correção de código passa pelo fluxo normal de `correcao-de-erros.md` (o CRONOS dispara SCOUT/ATLAS; o SHIELD revisa; deploy só com o aval do comandante).
3. **Sem runbook para o sintoma?** Isso é falha do entregável 5: o CRONOS cria a tarefa para escrever o runbook que faltou.
4. **O incidente exigiu o criador?** Se o comandante precisou intervir, o teste supremo falhou nesse ciclo: o período de observação de 2 semanas **recomeça do zero** depois da correção.
5. **Registro:** o CRONOS registra o incidente e a lição em `.delta-11/memoria/decisoes/AAAA-MM-DD-descanso-incidente-<slug>.md` e acrescenta a lição em `~/.delta-11/aprendizados-entre-projetos.md` se ela valer para outros projetos.

## Quem faz e quem sela

- **SHIELD** — entregáveis 3 (E2E em CI), 4 (pipeline com volta atrás), 5 (runbooks), 6 (painéis e alertas) e 7 (tag de release); confere os 10
- **VAULT** — entregáveis 8 (backup com restauração testada) e 9 (recuperação de desastre do banco)
- **BACK/ENGINE** — documentação técnica do servidor (parte do 1) e runbooks das integrações externas (parte do 5)
- **FRONT** (com PIXEL e FORM) — documentação da interface (parte do 1) e o roteiro de onboarding (10)
- **ATLAS** — documentação de domínio (2), disparado pelo CRONOS
- **SCOUT** — simula os incidentes para testar os runbooks
- **CRONOS** — orquestra, abre e fecha o período de observação, registra as lições entre projetos
- **Comandante** — responde ao teste supremo e escolhe a pessoa nova do onboarding (só ele conhece as pessoas)

A Fase 7 consagra com: os 10 entregáveis conferidos pelo SHIELD + o SIM do comandante no teste supremo. Sem os dois, a Fase 7 NÃO consagra.

## Memória entre projetos

Ao selar a Fase 7, o CRONOS acrescenta de 3 a 5 lições do projeto a `~/.delta-11/aprendizados-entre-projetos.md`, com o nome do projeto e a data (formato em `sub-agentes.md`, caso de uso 10 do code-architect). O ATLAS lê esse arquivo nas Fases 0 e 2 do próximo projeto.

## Relação com Skills Globais

A skill `owasp-top10` (referência `07-incident-response.md`, 449 linhas, v5.4 Estágio 5) tem 10 runbooks genéricos de IR. **Use-os como ponto de partida**, mas **crie runbooks específicos do seu produto** — runbook genérico é exemplo, não produto.

**NÃO duplique** o conteúdo da skill no projeto. Em vez disso:
- Adicione 1 linha em `.delta-11/memoria/runbooks/README.md`: "Esta pasta herda runbooks genéricos de `~/.claude/skills/owasp-top10/references/07-incident-response.md` e os especializa para este produto"
- Cada runbook específico herda do genérico e adiciona: dados concretos do produto, telefones de vendors, comandos exatos

## Integração com monitor-delta11.sh

O script `monitor-delta11.sh` detecta agentes travados. Para a Fase 7, ele é **estendido** com detecção de operação autônoma:
- A cada verificação (5 min), comparar timestamp da última intervenção humana no projeto
- Se for > 2 semanas → sinal `OPERACAO_AUTONOMA_DETECTADA`
- O comando `vigilante` e o painel mostram esse sinal
- Atenção: silêncio por abandono (agente órfão, alerta aberto sem dono) não é consagração — o CRONOS confere isso antes de aceitar o sinal

## Endereço canônico dos entregáveis

Cada um dos 10 entregáveis + o teste supremo vira um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-descanso-<NN>-<slug>.md` (`<NN>` com dois dígitos; o hook `fase-descanso-checker.py` conta os arquivos por esse nome). Runbooks específicos vão em `.delta-11/memoria/runbooks/`.

## Manutenção

Este protocolo evolui conforme o sistema amadurece. Mudanças aqui passam por:
1. Proposta via issue
2. Discussão em equipe
3. Decisão via ADR
4. Atualização deste arquivo + template + hook + monitor-delta11.sh

**Versão do protocolo:** v6.3 (2026-10-14) — Correção Geral. Criado na v6.0.0 (2026-07-12).
**Manutenção:** manter sincronizado com `metodologia-genesis-camadas.md` (Dia 7) e `fase-descanso-template.md`.

---
*Mudanças neste protocolo são registradas no CHANGELOG (última: v6.3).*