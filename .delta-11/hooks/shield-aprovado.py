#!/usr/bin/env python3
"""
Vigia "SHIELD aprovou" — Delta-11 v6.3 (2026-10-14). Itens C-039, C-036, D11, D33.

Nenhuma tarefa de executor fica concluida sem a APROVACAO do SHIELD.

Quem precisa (D11): VAULT, BACK, ENGINE, FRONT, PIXEL, FORM e SCOUT.
Isentos: SHIELD (nao revisa a si mesmo), ATLAS e CRONOS.

Prova aceita (D33): no `.delta-11/activity-log.md` da pasta principal, uma linha
com horario gravada pelo SHIELD:
    - [AAAA-MM-DDTHH:MM:SSZ] [SHIELD] APROVADO T-XXX [AGENTE]
    - [AAAA-MM-DDTHH:MM:SSZ] [SHIELD] REPROVADO T-XXX [AGENTE] motivo
  - So "APROVADO" libera; "REPROVADO" nunca conta como aprovacao (C-039).
  - Vale a ULTIMA decisao do SHIELD para aquela tarefa e agente: se depois da
    aprovacao veio uma reprovacao, bloqueia.
  - A decisao precisa estar dentro da janela (`janela_horas`, padrao 4 h) pelo
    HORARIO DA LINHA (nao pela data do arquivo, que todo vigia renova).
  - Se a linha concluida nao tem ID de tarefa, basta uma APROVACAO recente
    do SHIELD para aquele agente (sem reprovacao depois).

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`): so para tarefas
que PASSAM a ficar concluidas nesta edicao (compara antes e depois — C-036).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "shield-aprovado"
EXIGEM_SHIELD = set(comum.EXECUTORES)  # D11 — sem o proprio SHIELD
DECISAO_RE = re.compile(
    r"\[SHIELD\]\s+(APROVADO|REPROVADO)\s+([A-Za-z][\w.]*-[\w.-]+)\s+\[([A-Z]+)\]",
    re.IGNORECASE,
)


def shield_decisions() -> list[tuple]:
    """[(quando, decisao, tarefa, agente)] dentro da janela, em ordem do arquivo."""
    texto = comum.read_text(comum.delta_dir() / "activity-log.md")
    agora = comum.now_utc()
    janela = comum.window_seconds()
    decisoes = []
    for linha in texto.splitlines():
        achado = DECISAO_RE.search(linha)
        if not achado:
            continue
        quando = comum.line_timestamp(linha)
        if quando is None or (agora - quando).total_seconds() > janela:
            continue
        decisoes.append((quando, achado.group(1).upper(), achado.group(2).upper(), achado.group(3).upper()))
    decisoes.sort(key=lambda d: d[0])
    return decisoes


def latest_decision(decisoes: list[tuple], agente: str, tarefa: str | None) -> str | None:
    escolhidas = [d for d in decisoes if d[3] == agente and (tarefa is None or d[2] == tarefa)]
    return escolhidas[-1][1] if escolhidas else None


def message(agente: str, linha: str, tarefa: str | None, decisao: str | None) -> str:
    horas = comum.limits()["janela_horas"]
    id_texto = tarefa or "T-XXX"
    motivo = (
        f"o SHIELD REPROVOU {id_texto} de {agente} (ultima decisao)"
        if decisao == "REPROVADO"
        else f"nenhuma aprovacao do SHIELD para {id_texto} de {agente} nas ultimas {horas} h"
    )
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — falta a aprovacao do SHIELD\n"
        f"\n"
        f"Tarefa: {linha[:160]}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"O que fazer:\n"
        f"  1. O executor avisa o CRONOS por SendMessage pedindo a revisao do SHIELD (D9, 3.8).\n"
        f"  2. O CRONOS dispara o SHIELD; o SHIELD grava no activity-log:\n"
        f"       - [AAAA-MM-DDTHH:MM:SSZ] [SHIELD] APROVADO {id_texto} [{agente}]\n"
        f"     ou  - [AAAA-MM-DDTHH:MM:SSZ] [SHIELD] REPROVADO {id_texto} [{agente}] motivo\n"
        f"  3. Com APROVADO gravado, a conclusao pode ser marcada de novo.\n"
        f"  4. Se REPROVADO: nao conclua; corrija ou mova para BLOQUEADO.\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    _antes, _depois, novas = comum.kanban_change(evento)
    decisoes = None
    for linha in novas:
        agente = comum.line_agent(linha)
        if agente not in EXIGEM_SHIELD:
            continue
        if decisoes is None:
            decisoes = shield_decisions()
        tarefa = comum.task_id(linha)
        decisao = latest_decision(decisoes, agente, tarefa)
        if decisao != "APROVADO":
            return comum.block(
                HOOK, message(agente, linha, tarefa, decisao),
                f"{agente} concluiu {tarefa or 'tarefa'} sem APROVADO do SHIELD",
            )
        comum.log(HOOK, f"OK: {tarefa or 'tarefa'} de {agente} aprovada pelo SHIELD")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
