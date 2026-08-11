#!/usr/bin/env python3
"""
Hook SessionStart do Delta-11 v6.2: executa `git worktree prune`
para limpar worktrees orfas.

Materializa o Furo 11 da auditoria 2026-08-11 (D-scan completo):
'8 worktrees orfas sem limpeza'. gc-locks.py limpa locks/scratch/
logs mas NAO worktrees (que ficam em .delta-11/wt-*). Hook
expande o gc-locks para incluir worktree cleanup.

ALVO: SessionStart. Roda automaticamente quando Claude Code
inicia sessao.

LOGICA:
  1. Executa `git worktree list --porcelain` para listar worktrees
  2. Executa `git worktree prune` para remover worktrees orfas
     (referencias em .git/worktrees que nao tem mais diretorio)
  3. Loga quantas foram removidas em activity-log.md
  4. Sempre exit 0 (cleanup nao bloqueia)
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [worktree-prune] {mensagem}\n")
    except OSError:
        pass


def list_worktrees() -> list[str]:
    """Lista worktrees do repo git atual."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return []


def run_worktree_prune() -> tuple[bool, str]:
    """Executa git worktree prune. Retorna (sucesso, saida)."""
    try:
        result = subprocess.run(
            ["git", "worktree", "prune", "-v"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False, "git nao encontrado"


def main() -> int:
    try:
        antes = list_worktrees()
        sucesso, saida = run_worktree_prune()
        depois = list_worktrees()

        removidas_count = (len(antes) - len(depoor)) if antes and depois else 0

        if removidas_count > 0:
            log_activity(
                f"OK: {removidas_count} worktree(s) orfa(s) removida(s). "
                f"Antes: {len(antes)} worktree(s). Depois: {len(depoor)} worktree(s)."
            )
        else:
            log_activity(
                f"INFO: nenhuma worktree orfa para remover. "
                f"Total: {len(depoor)} worktree(s) ativas."
            )

        if not sucesso:
            log_activity(f"AVISO: git worktree prune retornou falha: {saida}")

        # Sempre exit 0: cleanup nao bloqueia
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[worktree-prune] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO nao-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())