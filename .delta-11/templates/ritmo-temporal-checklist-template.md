# TEMPLATE — Checklist de 1 página do Ritmo Temporal (Fase 3.5 / Dia 4 — Ciclo 2 em diante)

> **O que é (v6.4 — ciclo leve):** no **Ciclo 1** a Fase 3.5 entrega os 10 documentos completos
> (`templates/fase-ritmo-template.md`). Do **Ciclo 2 em diante**, ela entrega UMA página: este checklist, com os
> 10 itens do Dia 4, cada um com "sem mudança" ou a mudança em até 3 linhas.
>
> **Onde salvar:** `.delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-checklist-ciclo-N.md`
> (`N` = número do ciclo, o mesmo do `**Ciclo atual:**` do kanban). Exemplo: `2026-11-03-ritmo-temporal-checklist-ciclo-2.md`.
>
> **Quando o ciclo MEXE na área** (cria filas novas, troca o cache, muda o CI/CD...): o item afetado ganha o
> **documento completo** (`AAAA-MM-DD-ritmo-temporal-<NN>-<slug>.md`, modelo `fase-ritmo-template.md`); a linha
> dele aqui escreve `mudou: <resumo>` e o nome do arquivo na coluna "Documento completo". O resto continua no checklist.
>
> **Quem escreve:** o BACK (líder técnico da fase), com a parte de ENGINE, VAULT e SHIELD. **Quem confere:** o
> SHIELD. **Quem sela:** como no Ciclo 1 (SUSTENTA do BACK + cadeia de selo do CRONOS).
>
> **O vigia `fase-ritmo-checker.py` confere sozinho:** que o arquivo do ciclo atual existe; que os 10 itens estão
> nas linhas numeradas; que cada um diz `sem mudança` (ou `não se aplica`) ou `mudou: ...`; que o documento
> completo citado existe. **O vigia NÃO julga** se uma mudança era grande o bastante para exigir documento
> completo: isso é o SHIELD que confere.
>
> **Protocolo formal:** `.delta-11/protocolos/fase-ritmo.md` → "Ciclo leve". **Metodologia:**
> `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 4 (Os Astros).

---

## Copie daqui para baixo

```markdown
# Checklist do Ritmo Temporal — Ciclo {{N}} ({{AAAA-MM-DD}})

- **Projeto:** {{NOME_PROJETO}}
- **Entrega do ciclo (1 frase, do roadmap dos 7 ciclos):** {{ENTREGA_DO_CICLO}}
- **Autor:** {{AGENTE}} · **Conferido pelo SHIELD:** [ ]

| Nº | Item | Neste ciclo | Documento completo |
|---|---|---|---|
| 01 | sistema-eventos | [sem mudança — ou "mudou: ..." em até 3 linhas] | [— ou nome do arquivo] |
| 02 | filas | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 03 | jobs-agendados | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 04 | cache-ttl | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 05 | timeouts | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 06 | retries | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 07 | circuit-breakers | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 08 | ci-cd-staging | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 09 | observabilidade | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 10 | sub-contraposicao | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
```

## Como preencher (regras curtas)

1. Uma linha por item, sempre com o número (`01` a `10`). Não apague linha: item sem novidade é `sem mudança`.
2. Mudança pequena: `mudou: <o que mudou e por quê>` na própria linha, em até 3 linhas.
3. Mudança que mexe na área: `mudou: <resumo>` e, na coluna "Documento completo", o nome
   `AAAA-MM-DD-ritmo-temporal-NN-<slug>.md`. O documento completo é escrito com `fase-ritmo-template.md`.
4. Tecnologia nova no ciclo (fila nova, cache novo): a Fase 2.3 já pesquisou; cite a pesquisa na linha.

## Exemplo preenchido (Ciclo 3 — "Sementes")

```markdown
| Nº | Item | Neste ciclo | Documento completo |
|---|---|---|---|
| 01 | sistema-eventos | mudou: eventos novos `order.shipped` e `order.returned` (produtor ENGINE, consumidor e-mail) | — |
| 02 | filas | mudou: fila nova de devoluções no Inngest | 2026-11-20-ritmo-temporal-02-filas-devolucoes.md |
| 03 | jobs-agendados | sem mudança | — |
| 04 | cache-ttl | sem mudança | — |
| 05 | timeouts | sem mudança | — |
| 06 | retries | sem mudança | — |
| 07 | circuit-breakers | mudou: breaker na API da transportadora (5 falhas / 60 s) | — |
| 08 | ci-cd-staging | sem mudança | — |
| 09 | observabilidade | mudou: painel de devoluções (tempo médio, erro) | — |
| 10 | sub-contraposicao | sem mudança | — |
```
