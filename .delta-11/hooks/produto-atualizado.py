#!/usr/bin/env python3
"""
Vigia "produto atualizado" — Delta-11 v6.3 (2026-10-14). Itens C-006, C-015, C-036.

Furo 3 da auditoria 2026-08-11: agentes concluiam tarefas sem atualizar o
`[AGENTE]-produto.md` (o retrato do que existe agora, D8). O CRONOS perdia o fio.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`):
  - So para tarefas que PASSAM a ficar concluidas nesta edicao (compara antes e
    depois; reescrever o kanban inteiro nao reconta tarefas antigas — C-036).
  - Dono da tarefa: "Por: X", "Agente: X", "[X]" ou "| X |" na linha.
  - Para executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SHIELD, SCOUT):
    exige `.delta-11/memoria/[AGENTE]-produto.md` da PASTA PRINCIPAL (C-006)
    alterado dentro da janela (`janela_horas`, padrao 4 h).
  - ATLAS e CRONOS sao isentos.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "produto-atualizado"


def product_age(agente: str) -> float | None:
    caminho = comum.delta_dir() / "memoria" / f"{agente}-produto.md"
    try:
        return comum.now_utc().timestamp() - caminho.stat().st_mtime
    except OSError:
        return None


def message(agente: str, linha: str, idade: float | None) -> str:
    horas = comum.limits()["janela_horas"]
    limite = comum.limits()["produto_max_tokens"]
    motivo = (
        f"{agente}-produto.md NAO EXISTE em .delta-11/memoria/"
        if idade is None
        else f"{agente}-produto.md foi alterado pela ultima vez ha {idade / 3600:.1f} h (limite {horas} h)"
    )
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — produto.md desatualizado\n"
        f"\n"
        f"Tarefa: {linha[:160]}\n"
        f"Dono: {agente}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"O que fazer:\n"
        f"  1. {agente} atualiza .delta-11/memoria/{agente}-produto.md (pasta principal) com o\n"
        f"     que existe agora (ate {limite} tokens; inclua a linha `autocritica: <caminho>`)\n"
        f"     e .delta-11/memoria/{agente}-historia.md com o diario da tarefa.\n"
        f"  2. Depois disso a conclusao pode ser marcada de novo.\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    _antes, _depois, novas = comum.kanban_change(evento)
    janela = comum.window_seconds()
    for linha in novas:
        agente = comum.line_agent(linha)
        if agente not in comum.EXECUTORES_COM_SHIELD:
            continue
        idade = product_age(agente)
        if idade is None or idade > janela:
            return comum.block(
                HOOK, message(agente, linha, idade),
                f"{agente} concluiu {comum.task_id(linha) or 'tarefa'} sem produto.md recente",
            )
        comum.log(HOOK, f"OK: {agente}-produto.md alterado ha {idade / 3600:.1f} h")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
