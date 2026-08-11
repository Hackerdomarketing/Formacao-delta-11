#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA execucao quando o contexto
do agente esta' proximo do limite (autocompact iminente).

Materializa o Furo #1 da auditoria 2026-08-11: 'Autocompact matou 5
agentes'. Quando o Claude Code atinge ~85% do context window, ele
dispara autocompact automaticamente, o que pode perder estado
crucial de agents de longa duracao.

ALVO: PreToolUse em qualquer tool. Recebe evento JSON via stdin.

LOGICA:
  1. Le evento JSON via stdin
  2. Extrai o prompt/brief do tool_input (campo 'prompt' ou 'content'
     ou 'new_string')
  3. Estima tokens (1 token ~ 4 chars, padrao D-11)
  4. Se tokens estimados > 170.000 (85% de 200.000 default):
     - BLOQUEIA (exit 2)
     - Sugere ao agente: persistir estado em .delta-11/memoria/
       e/ou retomar em nova sessao via Agent tool
  5. Caso contrario, exit 0 (passa)

EXIT CODES:
  0 = pode prosseguir
  2 = BLOQUEAR (contexto proximo do limite — previne autocompact)
  1 = erro interno (nao bloqueia)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")

# Limite: Claude Code default context window = 200K tokens.
# 85% disso = 170K tokens = 680K chars (4 chars/token).
# Aciona BLOQUEIO antes do autocompact automatico.
LIMITE_TOKENS_AUTOCOMPACT = 170_000
APROXIMACAO_CHARS_POR_TOKEN = 4


def timestamp_utc() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"- [{timestamp_utc()}] [anti-autocompact] {mensagem}\n")
    except OSError:
        pass


def read_hook_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def estimate_tokens(event: dict) -> int:
    """
    Estima o numero de tokens do evento, combinando:
    - 'prompt' (campo especifico do Agent/Task tool)
    - 'content' (Write tool)
    - 'new_string' (Edit tool)
    - 'command' (Bash tool)
    Fallback: se nenhum campo existir, retorna 0.
    """
    tool_input = event.get("tool_input") or {}
    tool_name = event.get("tool_name", "")

    # Tenta campos comuns de prompt
    candidates = []
    candidates.append(tool_input.get("prompt", "") or "")
    candidates.append(tool_input.get("content", "") or "")
    candidates.append(tool_input.get("new_string", "") or "")
    candidates.append(tool_input.get("command", "") or "")

    # Em eventos PreToolUse do Agent tool (Task), o prompt vem em
    # tool_input.prompt ou no campo raiz 'prompt'
    if event.get("prompt"):
        candidates.append(event["prompt"])

    # Pega o maior (e' onde esta o conteudo principal)
    total_chars = max((len(c) for c in candidates), default=0)

    if total_chars == 0:
        return 0

    return total_chars // APROXIMACAO_CHARS_POR_TOKEN


def block_autocompact(tokens_estimados: int, file_path: str) -> int:
    msg = (
        f"[anti-autocompact] BLOQUEIO v6.2.0 — Contexto > 85% do limite\n"
        f"\n"
        f"Arquivo/acao: {file_path}\n"
        f"Tokens estimados: {tokens_estimados:,} (limite: {LIMITE_TOKENS_AUTOCOMPACT:,})\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"Claude Code dispara autocompact automatico quando o context\n"
        f"window atinge ~85% da capacidade. Em agentes de longa duracao\n"
        f"(ex: BACK implementando feature grande), autocompact pode\n"
        f"perder estado crucial do agente. A auditoria de 2026-08-11\n"
        f"documentou 5 agentes que morreram por autocompact.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. ANTES de continuar: persista o estado em arquivo canonico:\n"
        f"     - .delta-11/memoria/[SEU-AGENTE]-produto.md (estado do produto)\n"
        f"     - .delta-11/memoria/[SEU-AGENTE]-historia.md (historico de tarefas)\n"
        f"     - .delta-11/activity-log.md (ja e' automatico)\n"
        f"  2. Em vez de continuar com a mesma sessao: dispare uma NOVA\n"
        f"     sessao sua via Agent tool (subagent_type: general-purpose)\n"
        f"     passando o estado persistido como brief:\n"
        f"\n"
        f"     Agent(\n"
        f"       description: \"Continuidade [AGENTE] - projeto [NOME]\",\n"
        f"       subagent_type: \"general-purpose\",\n"
        f"       run_in_background: true,\n"
        f"       isolation: \"worktree\",\n"
        f"       prompt: \"[ESTADO PERSISTIDO] Continue de onde parei.\"\n"
        f"     )\n"
        f"\n"
        f"  3. Ou use o comando 'retomar' do CRONOS para nova sessao\n"
        f"     com estado preservado.\n"
        f"\n"
        f"Referencia: Furo 1 da auditoria 2026-08-11 (D-scan completo).\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        event = read_hook_event()

        tool_input = event.get("tool_input") or {}
        file_path = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("command")
            or "<desconhecido>"
        )

        tokens = estimate_tokens(event)

        if tokens > LIMITE_TOKENS_AUTOCOMPACT:
            log_activity(
                f"BLOQUEIO: tokens={tokens:,} > limite={LIMITE_TOKENS_AUTOCOMPACT:,} "
                f"(autocompact iminente)"
            )
            return block_autocompact(tokens, file_path)

        return 0

    except Exception as exc:  # noqa: BLE001
        # Erro interno NAO bloqueia (padrao D-11) — apenas loga
        print(f"[anti-autocompact] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO nao-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[anti-autocompact] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)  # Nunca bloquear por erro interno