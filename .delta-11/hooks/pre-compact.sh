#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DELTA-11 v6.3 — Hooks PreCompact + SessionStart(compact): contexto cheio
# ═══════════════════════════════════════════════════════════════
# Registro (templates/settings-hooks.json):
#   PreCompact    matcher ""         →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/pre-compact.sh"
#   SessionStart  matcher "compact"  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/pre-compact.sh"
#
# Por que dois eventos (C-033, conferido na documentação oficial de
# hooks em 2026-10-14):
#   - No PreCompact o Claude Code DESCARTA `systemMessage` e não aceita
#     `additionalContext`: nada que este hook imprime chega ao modelo.
#     Aqui ele só marca o pulso como "contexto_critico", mantendo os
#     outros campos (ultima_tool, session_id...).
#     Ele NUNCA sai com 2: no PreCompact o código 2 cancela a
#     compactação, e a conversa pode estourar o limite.
#   - Logo depois da compactação o Claude Code dispara SessionStart com
#     source "compact". Nesse evento `hookSpecificOutput.additionalContext`
#     ENTRA no contexto do modelo. É aí que o alerta é entregue:
#     reler o próprio -produto.md / -plan.md e atualizar
#     -produto.md / -historia.md (D8).
#
# A lógica mora no motor de sinais (heartbeat.sh): um fato, um lugar.
# ═══════════════════════════════════════════════════════════════

bash "$(dirname "$0")/heartbeat.sh" pre-compact
exit 0
