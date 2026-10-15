#!/usr/bin/env python3
"""
Vigia "anti-stash" — Delta-11 v6.3 (2026-10-14). Itens C-020, C-036.

Golpe que impede (Furo 5 da auditoria 2026-08-11): esconder testes vermelhos com
`git stash` [gaveta temporaria de mudancas do git], marcar a tarefa como concluida
no kanban e depois trazer o stash de volta.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`):
  - So olha tarefas que PASSAM a ficar concluidas nesta edicao (compara o kanban
    antes e depois — reescrever o kanban inteiro nao reconta tarefas antigas).
  - So bloqueia por stash RECENTE: criado dentro da janela (`janela_horas`, padrao
    4 h, em .config-limites.json). Stash antigo, sem relacao com o trabalho atual,
    nao bloqueia mais (C-020). O stash e compartilhado por todas as worktrees do
    repositorio, por isso vale para qualquer agente.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "anti-stash"


def recent_stashes() -> list[str]:
    """Stashes criados dentro da janela: ['stash@{0} (ha 0.5 h): On main: msg']."""
    try:
        resultado = subprocess.run(
            ["git", "stash", "list", "--format=%gd|%ct|%gs"],
            cwd=str(comum.main_project_dir()), capture_output=True, text=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if resultado.returncode != 0:
        return []
    agora = comum.now_utc().timestamp()
    janela = comum.window_seconds()
    recentes = []
    for linha in resultado.stdout.splitlines():
        partes = linha.split("|", 2)
        if len(partes) != 3:
            continue
        try:
            idade = agora - int(partes[1])
        except ValueError:
            continue
        if idade <= janela:
            recentes.append(f"{partes[0]} (ha {idade / 3600:.1f} h): {partes[2]}")
    return recentes


def message(stashes: list[str], tarefas: list[str]) -> str:
    horas = comum.limits()["janela_horas"]
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — ha {len(stashes)} stash(es) criados nas ultimas {horas} h\n"
        f"\n"
        f"Tarefa(s) sendo marcadas como concluidas:\n"
    )
    texto += "".join(f"  - {t[:160]}\n" for t in tarefas[:5])
    texto += "\nStash recente:\n" + "".join(f"  - {s}\n" for s in stashes[:5])
    texto += (
        f"\n"
        f"Por que: um stash recente pode estar escondendo testes vermelhos. Concluir\n"
        f"a tarefa assim deixa o kanban verde com o codigo quebrado.\n"
        f"\n"
        f"O que fazer:\n"
        f"  1. Resolva o stash: `git stash pop` (traz de volta e corrige) ou\n"
        f"     `git stash drop` (se for lixo).\n"
        f"  2. Rode os testes de novo.\n"
        f"  3. Marque a conclusao outra vez.\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    _antes, _depois, novas = comum.kanban_change(evento)
    if not novas:
        return 0
    stashes = recent_stashes()
    if not stashes:
        return 0
    return comum.block(HOOK, message(stashes, novas), f"conclusao com {len(stashes)} stash(es) recente(s)")


if __name__ == "__main__":
    comum.run(main, HOOK)
