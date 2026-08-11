#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA Edits no kanban.md
marcando novo ciclo se project-core.md nao foi tocado (Furo 7).

Materializa o Furo 7 da auditoria 2026-08-11 (D-scan completo):
'ATLAS nao formalizou contratos M2 em project-core.md'. Quando
novo ciclo abre, contratos devem ser atualizados (M2 = matriz
de contratos de API/banco). Se project-core.md nao foi tocado
em 4h, agentes vao trabalhar com contratos desatualizados.

ALVO: Edits no kanban.md com mencao a "[CICLO X]" ou "[NOVO CICLO]".

LOGICA:
  1. Detecta edit em .delta-11/kanban.md
  2. Detecta mencao a novo ciclo no novo conteudo
  3. Verifica mtime do .delta-11/memoria/project-core.md
  4. Se project-core.md foi tocado em <=4h: PASSA (contratos OK)
  5. Se project-core.md NAO tocado em <=4h: BLOQUEIA
  6. Sem mencao a novo ciclo: PASSA (mudanca normal)

EXIT CODES:
  0 = pode prosseguir
  2 = BLOQUEAR (novo ciclo sem project-core.md atualizado)
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
KANBAN_FILE = Path(".delta-11/kanban.md")
PROJECT_CORE = Path(".delta-11/memoria/project-core.md")

# Janela: 4 horas
JANELA_SEGUNDOS = 4 * 60 * 60

# Marcadores de novo ciclo
NOVO_CICLO_RE = re.compile(
    r"\[(?:NOVO\s+CICLO|CICLO\s+\d+|\d+º\s+CICLO|\d+°\s+CICLO)\]|"
    r"\[?(?:Novo\s+Ciclo|Iniciar\s+Ciclo|Abrir\s+Ciclo)\]?",
    re.IGNORECASE,
)

CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE
)


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [contratos-minimos] {mensagem}\n")
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


def has_novo_ciclo(content: str) -> bool:
    return bool(NOVO_CICLO_RE.search(content))


def project_core_idade() -> float | None:
    if not PROJECT_CORE.exists():
        return None
    try:
        return time.time() - PROJECT_CORE.stat().st_mtime
    except OSError:
        return None


def block_stale_core(file_path: str, idade: float | None) -> int:
    if idade is None:
        motivo = "project-core.md NAO EXISTE"
    else:
        motivo = f"project-core.md nao tocado ha {idade/3600:.1f}h"

    msg = (
        f"[contratos-minimos] BLOQUEIO v6.2.0 — novo ciclo sem project-core.md atualizado\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que ATLAS em\n"
        f"alguns casos abriu novo ciclo sem formalizar contratos M2\n"
        f"no project-core.md. Agentes de execucao (BACK, FRONT, etc.)\n"
        f"comecaram a trabalhar com contratos desatualizados, gerando\n"
        f"trabalho que teve que ser refeito quando o ATLAS atualizou\n"
        f"os contratos depois.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. ANTES de abrir novo ciclo, ATLAS deve atualizar\n"
        f"     .delta-11/memoria/project-core.md com os novos\n"
        f"     contratos M2 (API endpoints, schemas de banco, ADRs).\n"
        f"  2. Salvar project-core.md (Edit/Write). mtime sera\n"
        f"     atualizado automaticamente.\n"
        f"  3. Repita a marcacao do novo ciclo no kanban.\n"
        f"     Hook passara.\n"
        f"\n"
        f"Janela permitida: 4h. Se passou mais que 4h desde o\n"
        f"ultimo update do project-core.md, hook BLOQUEIA novamente.\n"
        f"\n"
        f"Referencia: Furo 7 da auditoria 2026-08-11 (D-scan completo).\n"
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

        if not has_novo_ciclo(combined):
            return 0

        idade = project_core_idade()
        if idade is None or idade > JANELA_SEGUNDOS:
            log_activity(
                f"BLOQUEIO: novo ciclo sem project-core.md atualizado (idade: {idade})"
            )
            sys.exit(block_stale_core(file_path, idade))

        log_activity(
            f"OK: novo ciclo com project-core.md tocado em {idade/3600:.1f}h"
        )
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[contratos-minimos] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[contratos-minimos] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)