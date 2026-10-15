# TEMPLATE — Checklist de 1 página da Consciência (Fase 4.5 / Dia 6 — Ciclo 2 em diante)

> **O que é (v6.4 — ciclo leve):** no **Ciclo 1** a Fase 4.5 entrega os 5 documentos completos
> (`templates/fase-consciencia-template.md`). Do **Ciclo 2 em diante**, ela entrega UMA página: este checklist,
> com os 5 itens do Dia 6, cada um com "sem mudança" ou a mudança em até 3 linhas.
>
> **Onde salvar:** `.delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-checklist-ciclo-N.md`
> (`N` = número do ciclo, o mesmo do `**Ciclo atual:**` do kanban). Exemplo: `2026-11-10-consciencia-checklist-ciclo-2.md`.
>
> **Quando o ciclo MEXE na área** (muda a autenticação, cria tabela com dado pessoal, cria operação crítica que
> pede aprovação, muda regra de negócio central...): o item afetado ganha o **documento completo**
> (`AAAA-MM-DD-consciencia-<NN>-<slug>.md`, modelo `fase-consciencia-template.md`); a linha dele aqui escreve
> `mudou: <resumo>` e o nome do arquivo na coluna "Documento completo". O resto continua no checklist.
>
> **Quem escreve:** VAULT, ENGINE e FORM/PIXEL, cada um na sua linha (BACK e FRONT revisam). **Quem confere e
> sela:** o SHIELD, como no Ciclo 1 (o teste cruzado continua: o `audit_log` grava; a 6ª tentativa de login é
> recusada).
>
> **O vigia `fase-consciencia-checker.py` confere sozinho:** que o arquivo do ciclo atual existe; que os 5 itens
> estão nas linhas numeradas; que cada um diz `sem mudança` (ou `não se aplica`) ou `mudou: ...`; que o
> documento completo citado existe. **O vigia NÃO julga** se uma mudança era grande o bastante para exigir
> documento completo: isso é o SHIELD que confere.
>
> **Protocolo formal:** `.delta-11/protocolos/fase-consciencia.md` → "Ciclo leve". **Metodologia:**
> `.delta-11/conhecimento/metodologia-genesis-camadas.md` → Dia 6.

---

## Copie daqui para baixo

```markdown
# Checklist da Consciência — Ciclo {{N}} ({{AAAA-MM-DD}})

- **Projeto:** {{NOME_PROJETO}}
- **Entrega do ciclo (1 frase, do roadmap dos 7 ciclos):** {{ENTREGA_DO_CICLO}}
- **Endpoints e tabelas novos deste ciclo:** {{LISTA_CURTA}}
- **Conferido pelo SHIELD:** [ ]

| Nº | Item | Neste ciclo | Documento completo |
|---|---|---|---|
| 01 | auditoria-imutavel | [sem mudança — ou "mudou: ..." em até 3 linhas] | [— ou nome do arquivo] |
| 02 | rate-limiting | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 03 | motor-regras | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 04 | lgpd | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
| 05 | fluxos-aprovacao | [sem mudança — ou "mudou: ..."] | [— ou nome do arquivo] |
```

## Como preencher (regras curtas)

1. Uma linha por item, sempre com o número (`01` a `05`). Item sem novidade é `sem mudança`.
2. Endpoint novo do ciclo SEMPRE aparece em algum item: rota pública nova → 02 (limite de requisições); tabela
   nova com dado sensível → 01 (auditoria) e 04 (LGPD); operação crítica nova → 05 (aprovação).
3. Mudança pequena: `mudou: <o que mudou>` na própria linha, em até 3 linhas.
4. Mudança que mexe na área: `mudou: <resumo>` e o nome do documento completo na última coluna.

## Exemplo preenchido (Ciclo 2 — "Espaço")

```markdown
| Nº | Item | Neste ciclo | Documento completo |
|---|---|---|---|
| 01 | auditoria-imutavel | mudou: gatilho de auditoria na tabela nova `team_invites` | — |
| 02 | rate-limiting | mudou: `/api/invites` com 10 convites / hora por usuário | — |
| 03 | motor-regras | sem mudança | — |
| 04 | lgpd | mudou: e-mail do convidado entra na exportação e na exclusão de dados | — |
| 05 | fluxos-aprovacao | sem mudança | — |
```
