# TEMPLATE — Fase 7: Artefato de Descanso (Dia 7 da Metodologia Gênesis)

> **O que é:** este template preenche CADA UM dos 10 entregáveis do Dia 7 (Descanso Consagrado). Um entregável = um arquivo `.delta-11/memoria/decisoes/AAAA-MM-DD-descanso-<N>-<slug>.md`.
>
> **Diferença dos entregáveis do Dia 4 e Dia 6:** o Dia 7 exige **EVIDÊNCIA** — não basta declarar. O entregável só conta quando há prova de execução (link para log, screenshot, hash, ou teste executado).
>
> **Quem escreve:** SHIELD + Líder técnico + Comandante.
>
> **Quem sella:** Comandante (teste supremo) + Líder técnico (entregáveis).
>
> **Quando NÃO aplicar:** sistemas de playground, MVP descartável, demo didática. Ver protocolo para exceções.
>
> **Referência conceitual:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 7.
> **Protocolo formal:** `.delta-11/protocolos/fase-descanso.md`.

---

## Cabeçalho do artefato (preencher uma vez)

```markdown
# Entregável {{NUMERO}} de 10 — {{NOME_ENTREGAVEL}} (Dia 7 / Fase 7)

- **Projeto:** {{NOME_PROJETO}}
- **Data:** {{AAAA-MM-DD}}
- **Autor:** {{NOME_AUTOR}} (SHIELD / Líder técnico / Comandante)
- **Status:** proposta | aceita | concluída-com-evidência
- **Cross-reference Metodologia:** `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 7

## Descrição

O QUE é este entregável. Por que o sistema precisa dele para operar autonomamente.

Máximo 200 palavras.

## Escolha

A tecnologia / padrão / formato escolhido. Em uma frase.

## Justificativa

Por que ESSA escolha e não outras.

Máximo 150 palavras.

## Como executar (este é o passo-chave do Dia 7)

Comandos exatos, em ordem, com saída esperada em cada um:

1. [Ação concreta — verbo no infinitivo]
   ```bash
   {{COMANDO}}
   ```
   **Saída esperada:** {{DESCRICAO_DA_SAIDA_OU_VALOR}}

2. [Ação concreta]
   ...

## Evidência de execução

**SEM EVIDÊNCIA, O ENTREGÁVEL NÃO CONTA.** Cada entregável do Dia 7 precisa de UMA das formas abaixo:

- **Link para log:** `[link para arquivo .delta-11/logs/...]` mostrando a saída real
- **Screenshot:** caminho `.delta-11/evidencias/screenshots/AAAA-MM-DD/HHMM-contexto.png`
- **Hash / checksum:** assinatura de artefato ou tag
- **Registro de teste:** "Executado em AAAA-MM-DD por {{NOME}}, durou {{TEMPO}}, resultado: {{RESULTADO}}"
- **Link para dashboard:** URL do dashboard mostrando o estado atual

Para o Dia 7, **evidência fraca é não-evidência**. Errar para o lado de fornecer mais evidência.

## Operador(es) humano(s)

Quem é o **dono da operação** deste entregável. Se algo quebrar em produção às 3h da manhã, quem é chamado.

- **Dono primário:** {{NOME}}, contato: {{EMAIL/TELEFONE}}
- **Dono backup:** {{NOME}}, contato: {{EMAIL/TELEFONE}}

## Critério de consagração

Como verificar que este entregável continua valido daqui em diante:

- [Verificação periódica: a cada X tempo]
- [Quem é responsável por essa verificação]
- [O que fazer se a verificação falhar]

## Cross-references (skills globais)

Quais skills globais e patterns este entregável consulta:

- Skill `owasp-top10` — referência `~/.claude/skills/owasp-top10/references/07-incident-response.md` (10 runbooks genéricos de IR)
- Pattern: {{nome pattern se aplicável}}

---
*Preenchido em {{DATA_PREENCHIMENTO}} | Evidência anexada em {{DATA_EVIDENCIA}} | Selado: [ ] Comandante | [ ] Líder técnico*
```

---

## Como preencher os 10 entregáveis (+ o teste supremo)

| # | Entregável | Slug sugerido | Nome do arquivo | Endereço |
|---|-----------|---------------|------------------|----------|
| 1 | Documentação técnica | `docs-tecnica` | `{{DATA}}-descanso-01-docs-tecnica.md` | `docs/arquitetura/` |
| 2 | Documentação de domínio | `docs-dominio` | `{{DATA}}-descanso-02-docs-dominio.md` | `docs/dominio/` |
| 3 | Testes E2E | `e2e` | `{{DATA}}-descanso-03-e2e.md` | `tests/e2e/` |
| 4 | Deploy automatizado | `deploy-auto` | `{{DATA}}-descanso-04-deploy-auto.md` | `.github/workflows/` |
| 5 | Runbooks específicos | `runbooks` | `{{DATA}}-descanso-05-runbooks.md` | `memoria/runbooks/` |
| 6 | Monitoramento + alertas | `monitoramento` | `{{DATA}}-descanso-06-monitoramento.md` | `src/lib/observabilidade/` |
| 7 | Tag de release | `tag-release` | `{{DATA}}-descanso-07-tag-release.md` | tag git |
| 8 | Backup testado | `backup` | `{{DATA}}-descanso-08-backup-testado.md` | logs + restore |
| 9 | DR testado | `dr` | `{{DATA}}-descanso-09-dr-testado.md` | runbook + log |
| 10 | Onboarding testado | `onboarding` | `{{DATA}}-descanso-10-onboarding.md` | log da pessoa nova |
| EXTRA | Teste supremo | `teste-supremo` | `{{DATA}}-descanso-EXTRA-teste-supremo.md` | declaração do Comandante |

Substitua `{{DATA}}` por `date +%Y-%m-%d`.

Para entregáveis 5-10, copie o **template de runbook** (em `.delta-11/templates/descanso-runbook-template.md` se existir, ou use o cabeçalho acima) para CADA runbook específico.

---

## ⚠️ IMPORTANTE — Descanso exige evidência, não declaração

O Dia 7 é **operação autônoma comprovada**. Declaração sem evidência não consagra.

Exemplos:
- "Backup testado" não é "rotina configurada" — é **log de restore executado**
- "Runbook X existe" não é "runbook escrito" — é **runbook testado por pessoa real**
- "Onboarding feito" não é "doc escrita" — é **pessoa nova conseguiu subir local**
- "Teste supremo" não é "achamos que ia funcionar" — é **2+ semanas sem intervenção**

Se você está preenchendo o template sem ter evidência, **volte e execute primeiro**. Não declare.

---

## Template Simplificado para os 10 entregáveis (versão rápida)

Para quem já viveu o projeto e quer preencher mais rápido, eis versão reduzida do cabeçalho:

```markdown
# {{NUMERO}}. {{NOME_ENTREGAVEL}}

**Data:** {{AAAA-MM-DD}}
**Autor:** {{NOME}}
**Status:** {{STATUS}}

## O que é

1 frase.

## Como executar

[comandos]

## Evidência

[link ou descrição]

## Dono

{{NOME + CONTATO}}
```

Use a versão reduzida quando a evidência é forte (ex: log gigante) e o longo seria repetir info.

---

## Especial: Template de Runbook (Entregável 5)

```markdown
# Runbook — {{NOME_DO_INCIDENTE}} do Projeto {{NOME_PROJETO}}

**Quando aplicar:** {{SINTOMAS_OBSERVADOS}}
**Severidade:** INFO | WARN | CRITICAL
**Dono primário:** {{NOME}} | Contato: {{EMAIL/TELEFONE}}
**Dono backup:** {{NOME}} | Contato: {{EMAIL/TELEFONE}}

## Sintomas (o que dispara este runbook)

- Métrica X caiu abaixo de Y por mais de Z minutos
- Alerta Slack chegou dizendo "..."
- Dashboard mostra: [screenshot]

## Causa provável (em ordem de probabilidade)

1. [Causa A] — ocorrências observadas: N (última: AAAA-MM-DD)
2. [Causa B] — ocorrências observadas: N
3. [Causa C] — ocorrências observadas: N (rara mas aconteceu)

## Diagnóstico

```bash
# Comando 1: confirmar sintoma
curl https://api.servico.com/health
# Saída esperada: 200 OK

# Comando 2: identificar causa
grep -i "ERROR" /var/log/servico.log | tail -20
# Saída esperada: lista de erros

# Comando 3: log específico
journalctl -u servico --since "10 min ago"
```

## Mitigação imediata (5 min)

1. [Ação A] — comando: `[comando exato]`
2. [Ação B] — `curl ...`
3. Se não resolveu em 5 min, escalar

## Escalonamento

- **5 min sem resolver:** acionar Dono Primário (telefone)
- **15 min sem resolver:** acionar Dono Backup
- **30 min sem resolver:** Postar aviso no status público [link]
- **1 hora sem resolver:** Considerar rollback (ver runbook de rollback)

## Prevenção

[O que mudou após o último incidente desse tipo para evitar recorrência]

---
**Testado pela última vez:** {{DATA_TESTE}}, por {{PESSOA}}, durou {{TEMPO}}
**Resultado do teste:** {{RESULTADO}}
**Próxima revisão:** {{PROXIMA_DATA}}
```

---

**Versão do template:** v6.0.0 (2026-07-12)
**Local canônico:** `.delta-11/templates/fase-descanso-template.md`
**Proveniência:** criado na Etapa 7B do plano Nível 3 Profundo (auditoria 2026-07-10)