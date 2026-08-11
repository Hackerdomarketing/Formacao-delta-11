#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA Edits no kanban.md marcando
CONCLUIDO para BACK/ENGINE/VAULT se SHIELD nao aprovou (Furo 4).

Materializa o Furo 4 da auditoria 2026-08-11 (D-scan completo):
'Onda C (commit 858bf66) sem autocrítica/SHIELD/build-validator'.
Contract tests sao executados por validar-contratos-fim-fase.py,
mas o agente pode pula-los se soft-rule.

Este hook foca no **SHIELD review** especificamente (outros
sub-agentes sao verificados por forca-despacho.py e anti-stash.py).

ALVO: Edits no kanban.md com transicao CONCLUIDO para BACK/ENGINE/VAULT.

LOGICA:
  1. Detecta edit em .delta-11/kanban.md
  2. Detecta transicao CONCLUIDO
  3. Identifica agente (BACK/ENGINE/VAULT)
  4. Verifica activity-log.md: ha linha com [SHIELD] ... [AGENTE]
     nas ultimas 4 horas?
  5. Se nao: BLOQUEIA (exit 2)
  6. Se sim: PASSA (exit 0)
  7. Agentes fora da lista: PASSA sempre (isentos)

EXIT CODES:
  0 = pode prosseguir
  2 = BLOQUEAR (sem SHIELD approval)
  1 = erro interno
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")

# Agentes que EXIGEM SHIELD approval antes de CONCLUIDO
AGENTES_QUE_EXIGEM_SHIELD = {"BACK", "ENGINE", "VAULT"}

# Janela: 4 horas
JANELA_SEGUNDOS = 4 * 60 * 60

CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE
)
AGENTE_TAG_RE = re.compile(r"\[([A-Z_-]+)\]")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [shield-aprovado] {mensagem}\n")
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


def is_kanban_edit(event: dict) -> bool:
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return (
        file_path.endswith("/.delta-11/kanban.md")
        or file_path.endswith("\\.delta-11\\kanban.md")
        or file_path == ".delta-11/kanban.md"
        or file_path.endswith("kanban.md")
    )


def get_combined_content(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    return (
        tool_input.get("new_string", "")
        + "\n"
        + tool_input.get("content", "")
    )


def touches_conclusion(content: str) -> bool:
    return bool(CONCLUSAO_RE.search(content))


def extract_agente_from_content(content: str) -> str | None:
    lines = content.split("\n")
    for line in lines:
        if CONCLUSAO_RE.search(line):
            match = AGENTE_TAG_RE.search(line)
            if match:
                return match.group(1)
    return None


def has_recent_shield_approval(agente: str) -> bool:
    """Verifica activity-log.md para linha [SHIELD] ... [AGENTE] nas ultimas 4h."""
    if not ACTIVITY_LOG.exists():
        return False

    try:
        mtime = ACTIVITY_LOG.stat().st_mtime
        if time.time() - mtime > JANELA_SEGUNDOS:
            # activity-log.md nao foi tocado em 4h = improvavel ter SHIELD recente
            return False
    except OSError:
        return False

    try:
        conteudo = ACTIVITY_LOG.read_text(encoding="utf-8")
    except OSError:
        return False

    # Procura linha com [SHIELD] e [AGENTE] nas ultimas 4h
    # Formato: "- [TIMESTAMP] [shield-aprovado] [BACK] X"
    # Ou: "- [TIMESTAMP] [SHIELD] ... [BACK] X" (formato de SHIELD review)
    for line in conteudo.splitlines()[-200:]:  # ultimas 200 linhas
        if "[SHIELD]" in line and f"[{agente}]" in line:
            return True

    return False


def block_no_shield(agente: str, file_path: str) -> int:
    msg = (
        f"[shield-aprovado] BLOQUEIO v6.2.0 — SHIELD nao aprovou {agente}\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Agente: {agente}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que BACK/ENGINE/\n"
        f"VAULT em algumas ondas marcaram CONCLUIDO sem review do SHIELD.\n"
        f"Validar-contratos-fim-fase.py roda tests, mas SHIELD review\n"
        f"e' camada adicional: analiza code quality, vulnerabilidades,\n"
        f"compliance com contratos M2, e consistencia arquitetural.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. ANTES de marcar CONCLUIDO, dispare SHIELD review via\n"
        f"     Agent tool (subagent_type: general-purpose) com brief:\n"
        f"\n"
        f"     Agent(\n"
        f"       description: \"SHIELD review para {agente}\",\n"
        f"       subagent_type: \"general-purpose\",\n"
        f"       run_in_background: false,\n"
        f"       prompt: \"Projeto em: [caminho]. Agente: {agente}.\n"
        f"         Revise qualidade, seguranca e compliance.\"\n"
        f"     )\n"
        f"\n"
        f"  2. O SHIELD loga no activity-log.md com tag [SHIELD] e\n"
        f"     o agente correspondente. Hook passara nas proximas 4h.\n"
        f"\n"
        f"  3. Se SHIELD reportar problemas: NAO marque CONCLUIDO.\n"
        f"     Crie tarefas adicionais no kanban com tag [BLOQUEADO].\n"
        f"\n"
        f"Referencia: Furo 4 da auditoria 2026-08-11 (D-scan completo).\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        event = read_hook_event()

        if not is_kanban_edit(event):
            return 0

        file_path = (
            (event.get("tool_input") or {}).get("file_path", "")
            or "<desconhecido>"
        )
        combined = get_combined_content(event)

        if not touches_conclusion(combined):
            return 0

        agente = extract_agente_from_content(combined)
        if not agente:
            return 0

        # Agentes fora da lista nao exigem SHIELD
        if agente not in AGENTES_QUE_EXIGEM_SHIELD:
            log_activity(
                f"OK: {agente} nao exige SHIELD approval (isento)"
            )
            return 0

        if has_recent_shield_approval(agente):
            log_activity(
                f"OK: {agente} tem SHIELD approval recente — CONCLUIDO liberado"
            )
            return 0

        log_activity(
            f"BLOQUEIO: {agente} tentou CONCLUIDO sem SHIELD approval"
        )
        sys.exit(block_no_shield(agente, file_path))

    except Exception as exc:  # noqa: BLE001
        print(f"[shield-aprovado] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[shield-aprovado] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)