#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DELTA-11 v6.3 — Hooks Stop + SessionEnd: fim de resposta / fim de sessão
# ═══════════════════════════════════════════════════════════════
# Registro (templates/settings-hooks.json):
#   Stop        matcher ""  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/on-stop.sh"
#   SessionEnd  matcher ""  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/on-stop.sh"
#
# ATENÇÃO (C-007): o evento Stop acontece no fim de CADA resposta do
# agente, não no fim da sessão. Por isso:
#   - Stop       → SÓ renova o pulso (status "aguardando"). Não apaga
#                  ACK, não grava "morte".
#   - SessionEnd → a sessão acabou de verdade: grava
#                  `ativacoes/morte-NOME.json` (motivo = campo `reason`
#                  do evento, que só existe no SessionEnd), apaga ACK e
#                  pulso dos agentes DESTA sessão (vínculos em
#                  `ativacoes/agentes-sessao.json`) e regenera
#                  `pulsos-data.js`. Agentes de outras sessões não são
#                  tocados.
# As travas de arquivo são liberadas pelo release-locks.js, registrado
# no mesmo SessionEnd (e no SubagentStop).
#
# A lógica mora no motor de sinais (heartbeat.sh): um fato, um lugar.
# Sai sempre com 0 — no Stop, o código 2 impediria o agente de parar.
# ═══════════════════════════════════════════════════════════════

bash "$(dirname "$0")/heartbeat.sh" on-stop
exit 0
