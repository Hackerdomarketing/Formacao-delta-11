#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DELTA-11 v6.3 — Hook SubagentStop: um sub-agente terminou
# ═══════════════════════════════════════════════════════════════
# Registro (templates/settings-hooks.json):
#   SubagentStop  matcher ""  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/fim-subagente.sh"
#
# O que faz (D32, N-002, C-008):
#   1. Grava `.delta-11/logs/sub-agentes/AAAAMMDDTHHMMSSZ-[agent_type].log`
#      na PASTA PRINCIPAL, com agent_id, agent_type, o agente Delta-11
#      (se identificado), o sub-agente detectado na primeira mensagem
#      (ex.: build-validator) e a última mensagem do sub-agente.
#      O forca-despacho.py aceita esse arquivo como prova (até 4 h).
#   2. Identifica o agente Delta-11 que terminou: vínculo do agent_id
#      em `ativacoes/agentes-sessao.json`, `agent_type`, ou o operativo
#      citado na primeira mensagem da transcrição. Nunca adivinha pelo
#      "ACK mais recente" (apagaria o sinal de outro agente).
#   3. Apaga `ativacoes/ack-NOME.txt` e `ativacoes/pulso-NOME.json` do
#      agente que terminou e regenera `.delta-11/pulsos-data.js`.
#   4. Escreve uma linha no activity-log (formato D25).
# As travas desse sub-agente são liberadas pelo release-locks.js,
# registrado no mesmo evento.
#
# Sai sempre com 0: no SubagentStop o código 2 impediria o sub-agente
# de terminar. A lógica mora no motor de sinais (heartbeat.sh).
# ═══════════════════════════════════════════════════════════════

bash "$(dirname "$0")/heartbeat.sh" fim-subagente
exit 0
