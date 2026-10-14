#!/usr/bin/env python3
"""
Vigia SessionStart "limpeza de worktrees" — Delta-11 v6.3 (2026-10-14). Itens C-045, C-002.

Furo 11 da auditoria 2026-08-11: worktrees [copias isoladas do projeto] orfas se
acumulavam. No inicio da sessao, este vigia roda `git worktree prune` na PASTA
PRINCIPAL do projeto, que remove apenas os REGISTROS de worktrees cuja pasta ja
nao existe (nao apaga nenhuma pasta com trabalho).

v6.3: corrigido o erro de digitacao no nome da variavel `depois` (C-045), que fazia o relatorio cair
sempre no tratamento de erro. O diario agora mostra antes/depois de verdade.

Registro: SessionStart (matcher ""). Nao escreve nada no stdout (no SessionStart o
stdout vira contexto do agente). Sempre sai com 0: limpeza nunca bloqueia. Erro
interno: registra ERRO-INTERNO no activity-log e avisa no stderr (exit 1, nao
bloqueia) — ver _comum.run.
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "worktree-prune"


def git(argumentos: list[str], tempo: int) -> tuple[bool, str]:
    try:
        resultado = subprocess.run(
            ["git"] + argumentos, cwd=str(comum.main_project_dir()),
            capture_output=True, text=True, timeout=tempo,
        )
    except (OSError, subprocess.SubprocessError) as erro:
        return False, str(erro)
    return resultado.returncode == 0, ((resultado.stdout or "") + (resultado.stderr or "")).strip()


def list_worktrees() -> list[str] | None:
    ok, saida = git(["worktree", "list", "--porcelain"], 2)
    if not ok:
        return None
    return [l[len("worktree "):] for l in saida.splitlines() if l.startswith("worktree ")]


def main() -> int:
    comum.read_event()
    if not comum.delta_dir().is_dir():
        return 0
    antes = list_worktrees()
    if antes is None:
        return 0  # fora de repositorio git
    sucesso, saida = git(["worktree", "prune", "-v"], 3)
    depois = list_worktrees() or []
    removidas = max(len(antes) - len(depois), 0)
    if not sucesso:
        comum.log(HOOK, f"AVISO: git worktree prune falhou: {saida[:200]}", "SISTEMA")
    elif removidas:
        comum.log(HOOK, f"{removidas} registro(s) de worktree orfa removido(s); antes {len(antes)}, depois {len(depois)}", "SISTEMA")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
