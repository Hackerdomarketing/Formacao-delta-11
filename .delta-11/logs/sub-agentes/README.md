# Logs de Sub-agentes (v5.2 — Regra Inviolável 17)

Todo relatório completo de sub-agente é salvo aqui ANTES de ser resumido no `[AGENTE]-produto.md`.

**Formato do nome:** `[AAAA-MM-DD]-[sub-agente]-[AGENTE-que-disparou]-[T-XXX].md`
Exemplo: `2026-07-03-build-validator-ENGINE-T-042.md`

**Por que existe:** a linha-resumo ("build-validator: PASS / 277 testes") não diz POR QUE passou.
Quando um bug aparece depois, este é o único lugar onde a auditoria encontra o log original.

**Retenção:** o GC de sessão (`gc-locks.py`) remove logs com mais de 30 dias.
Logs de decisões importantes devem ser citados no `[AGENTE]-historia.md` antes de expirar.
