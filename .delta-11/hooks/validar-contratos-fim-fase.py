#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11: valida testes de contrato antes de permitir que
uma tarefa seja movida para CONCLUIDO em transição de fase no kanban.md.

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.

Invocação:
  Configurado em .claude/settings.json em hooks.PreToolUse com matcher "Edit|Write"
  apontando para este script. Recebe evento JSON via stdin.

Lógica:
  1. Verifica se o Edit/Write atinge .delta-11/kanban.md
  2. Se sim, checa se o diff contém transição "para CONCLUIDO" em tarefa de Fase N
     (heurística: linha editada contém "CONCLUIDO" ou "✅")
  3. Se houver transição relevante, roda a suíte de contract tests do projeto
     detectando o framework via package.json / pytest / etc.
  4. Se passar, exit 0 (permite o Edit); se falhar, exit 2 (bloqueia Edit e
     injeta mensagem — conforme protocolo PreToolUse do Claude Code).

Exit codes:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention do Claude Code)
  1 = erro interno (não bloqueia por default — loga e deixa passar)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


KANBAN_FILE = Path(".delta-11/kanban.md")
ACTIVITY_LOG = Path(".delta-11/activity-log.md")
PACKAGE_JSON = Path("package.json")
PYTEST_INI = Path("pytest.ini")
PYPROJECT = Path("pyproject.toml")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
        f.write(f"- [{timestamp_utc()}] [validar-contratos-fim-fase] {message}\n")


def read_hook_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def is_kanban_edit(event: dict) -> bool:
    """Detecta se o Edit/Write alvo é kanban.md do Delta-11."""
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return file_path.endswith("/.delta-11/kanban.md") or file_path.endswith(
        "\\.delta-11\\kanban.md"
    )


def touches_conclusion(event: dict) -> bool:
    """
    Heurística: o novo conteúdo do Edit/Write inclui marcador de conclusão.
    Evita rodar testes pesados em cada edit pequeno do kanban.
    """
    tool_input = event.get("tool_input") or {}
    # Edit tool fields
    new_string = tool_input.get("new_string") or ""
    # Write tool field
    content = tool_input.get("content") or ""
    combined = f"{new_string}\n{content}"
    markers = ("CONCLUIDO", "CONCLUÍDO", "CONCLUIDA", "✅", "## CONCLU")
    return any(m in combined for m in markers)


def detect_test_command() -> list[str] | None:
    """
    Detecta o comando correto para rodar os testes de contrato no projeto.
    Retorna lista de argv (para subprocess.run) ou None se não conseguiu detectar.

    Estratégia cross-platform:
      - Node: npm run test:contracts (via `npm` se no PATH)
      - Python: pytest tests/contracts/ (via `pytest` ou `python -m pytest`)
    """
    # Node projects
    if PACKAGE_JSON.exists():
        try:
            pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts") or {}
            if "test:contracts" in scripts:
                npm = shutil.which("npm")
                if npm:
                    return [npm, "run", "test:contracts"]
        except (json.JSONDecodeError, OSError):
            pass

    # Python projects
    if PYTEST_INI.exists() or PYPROJECT.exists():
        pytest_bin = shutil.which("pytest")
        if pytest_bin:
            return [pytest_bin, "tests/contracts/"]
        # fallback: python -m pytest
        py = shutil.which("python3") or shutil.which("python")
        if py:
            return [py, "-m", "pytest", "tests/contracts/"]

    return None


def run_contract_tests(cmd: list[str]) -> tuple[bool, str]:
    """Roda a suíte de contract tests. Retorna (passou, saída resumida)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min máximo
        )
        passed = result.returncode == 0
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        # resume output para caber no log
        summary = output.strip()[-2000:]
        return (passed, summary)
    except subprocess.TimeoutExpired:
        return (False, "timeout após 5 minutos")
    except OSError as e:
        return (False, f"falha ao executar: {e}")


def block_edit(reason: str) -> int:
    """
    Convenção PreToolUse do Claude Code: exit 2 bloqueia a ferramenta e o stderr
    é injetado como mensagem. Formato: escrever explicação no stderr.
    """
    print(
        "[validar-contratos-fim-fase] BLOQUEIO: testes de contrato falharam antes "
        "de permitir transição de fase.\n"
        f"Motivo: {reason}\n\n"
        "Ação requerida: corrija a implementação OU atualize os contratos em "
        "project-core.md (o hook PostToolUse vai regenerar os testes "
        "automaticamente) antes de tentar mover a tarefa para CONCLUIDO.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = read_hook_event()

    if not is_kanban_edit(event):
        return 0
    if not touches_conclusion(event):
        return 0

    cmd = detect_test_command()
    if cmd is None:
        # Projeto não tem framework de testes reconhecível — deixa passar mas loga
        log_activity(
            "aviso: nenhum framework de testes detectado (sem package.json com "
            "test:contracts, pytest.ini ou pyproject.toml) — transição permitida "
            "sem validação automática"
        )
        return 0

    log_activity(f"rodando contract tests: {' '.join(cmd)}")
    passed, output = run_contract_tests(cmd)

    if passed:
        log_activity("contract tests PASSOU — transição permitida")
        return 0

    log_activity("contract tests FALHOU — transição bloqueada")
    return block_edit(
        output.splitlines()[-1] if output.strip() else "saída vazia (ver activity-log.md)"
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        # Em caso de erro interno do hook, NÃO bloquear — apenas logar
        print(f"[validar-contratos-fim-fase] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO não-fatal: {exc}")
        except Exception:
            pass
        sys.exit(0)
