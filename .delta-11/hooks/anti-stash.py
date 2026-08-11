#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA Edits no kanban.md marcando
CONCLUIDO se ha entradas em `git stash list` (Furo 5 da auditoria).

Cenário: BACK implementa feature, roda tests (falhando), faz
`git stash` para "esconder" os testes vermelhos, marca CONCLUIDO
no kanban (hook validar-contratos passa porque o código sem o
stash está OK), depois faz `git stash pop` trazendo os testes
vermelhos de volta. Resultado: kanban diz CONCLUIDO mas tests
ainda estão vermelhos.

Materializa o Furo 5 da auditoria 2026-08-11 (D-scan completo).

ALVO: Edits no kanban.md com transicao CONCLUIDO.

LOGICA:
  1. Detecta edit em .delta-11/kanban.md
  2. Detecta transicao CONCLUIDO no novo conteudo
  3. Executa `git stash list` (cross-platform via subprocess)
  4. Se saida nao-vazia: BLOQUEIA (exit 2)
  5. Caso contrario: PASSA (exit 0)

EXIT CODES:
  0 = pode prosseguir (sem stash OU kanban sem CONCLUIDO)
  2 = BLOQUEAR (stash detectado)
  1 = erro interno (nao bloqueia)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
KANBAN_FILE = Path(".delta-11/kanban.md")

CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE
)


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [anti-stash] {mensagem}\n")
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
    # Aceita path absoluto OU relativo
    return (
        file_path.endswith("/.delta-11/kanban.md")
        or file_path.endswith("\\.delta-11\\kanban.md")
        or file_path == ".delta-11/kanban.md"
        or file_path.endswith("kanban.md")  # qualquer kanban.md (relativo)
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


def get_stash_list() -> list[str]:
    """Executa git stash list e retorna linhas. Cross-platform."""
    try:
        result = subprocess.run(
            ["git", "stash", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return []


def block_stash(stash_lines: list[str], file_path: str) -> int:
    msg = (
        f"[anti-stash] BLOQUEIO v6.2.0 — git stash list tem {len(stash_lines)} entrada(s)\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que BACK em Onda D\n"
        f"fez 'git stash' para esconder testes vermelhos, marcou CONCLUIDO\n"
        f"no kanban (hook validar-contratos passou porque o codigo sem o\n"
        f"stash estava OK), depois fez 'git stash pop' trazendo os testes\n"
        f"vermelhos de volta. Resultado: kanban verde + tests vermelhos.\n"
        f"\n"
        f"Stash detectado:\n"
    )
    for line in stash_lines[:5]:
        msg += f"  - {line}\n"
    if len(stash_lines) > 5:
        msg += f"  ... e mais {len(stash_lines) - 5}\n"
    msg += (
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. ANTES de marcar CONCLUIDO, resolva o stash:\n"
        f"     a) `git stash pop` para trazer as mudancas de volta\n"
        f"     b) `git stash drop` para descartar\n"
        f"  2. Se stash contem testes que falham: corrija-os primeiro\n"
        f"  3. Repita o CONCLUIDO no kanban. Hook passara.\n"
        f"\n"
        f"Referencia: Furo 5 da auditoria 2026-08-11 (D-scan completo).\n"
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

        stash_lines = get_stash_list()
        if stash_lines:
            log_activity(
                f"BLOQUEIO: CONCLUIDO com {len(stash_lines)} stash(es) ativos"
            )
            return block_stash(stash_lines, file_path)

        log_activity("OK: CONCLUIDO com stash vazio")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[anti-stash] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[anti-stash] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)