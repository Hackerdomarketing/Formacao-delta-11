# Scratch — Arquivos Temporários (v5.2 — Regra Inviolável 16)

Pasta canônica para TODO arquivo efêmero gerado durante o trabalho:
previews HTML, JSON de debug, outputs de cURL, resultados intermediários.

**NUNCA use o `/tmp` do sistema** — fica fora do projeto, fora do git, e some sem aviso
(caso real: previews de e-mail em `/tmp/email-previews/` referenciados num roteiro de selo).

**Formato do nome:** `[AAAA-MM-DD]-[descricao-curta]/` ou `[AAAA-MM-DD]-[descricao].ext`

**Retenção:** o GC de sessão (`gc-locks.py`) apaga tudo com mais de 7 dias.
Se algo daqui precisa sobreviver, promova para o endereço canônico do seu tipo
(ver CLAUDE.md, seção "PARA IA EXTERNA" — mapa de zoneamento).
