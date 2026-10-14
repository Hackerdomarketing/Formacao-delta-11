#!/usr/bin/env python3
"""
Vigia "contratos minimos" — Delta-11 v6.3 (2026-10-14). Item C-024.

Furo 7 da auditoria 2026-08-11: um ciclo novo foi aberto sem o ATLAS atualizar os
contratos [acordos de API e banco] no project-core. Os executores trabalharam com
contratos velhos e o trabalho foi refeito.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`):
  - So quando um ciclo NOVO e ABERTO nesta edicao: compara o kanban antes e
    depois e procura marcadores que nao existiam:
        [NOVO CICLO]   [CICLO 5]   [5º CICLO]   ## CICLO 5
    Reescrever um cabecalho ja existente ("[CICLO 2]") nao conta (C-024).
  - Exige que o project-core.md OU alguma fatia em `memoria/project-core/` tenha
    sido alterada dentro da janela (`janela_horas`, padrao 4 h).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "contratos-minimos"
CICLO_RE = re.compile(
    r"\[\s*(NOVO\s+CICLO|CICLO\s+\d+|\d+\s*[º°o]\s*CICLO)\s*\]|^#{1,6}\s*(CICLO\s+\d+)\b",
    re.IGNORECASE | re.MULTILINE,
)


def cycle_markers(texto: str) -> Counter:
    marcadores: Counter = Counter()
    for achado in CICLO_RE.finditer(texto):
        bruto = achado.group(1) or achado.group(2) or ""
        normal = " ".join(bruto.upper().split())
        normal = re.sub(r"(\d+)\s*[º°O]\s*CICLO", r"CICLO \1", normal)
        marcadores[normal] += 1
    return marcadores


def newest_core_age() -> tuple[float | None, str]:
    memoria = comum.delta_dir() / "memoria"
    candidatos = [memoria / "project-core.md"]
    fatias = memoria / "project-core"
    if fatias.is_dir():
        candidatos += sorted(fatias.glob("*.md"))
    agora = comum.now_utc().timestamp()
    melhor: tuple[float | None, str] = (None, "")
    for caminho in candidatos:
        try:
            idade = agora - caminho.stat().st_mtime
        except OSError:
            continue
        if melhor[0] is None or idade < melhor[0]:
            melhor = (idade, caminho.name)
    return melhor


def message(novos: list[str], idade: float | None) -> str:
    horas = comum.limits()["janela_horas"]
    motivo = (
        "project-core.md nao existe"
        if idade is None
        else f"project-core e fatias sem alteracao ha {idade / 3600:.1f} h (limite {horas} h)"
    )
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — ciclo novo aberto sem contratos atualizados\n"
        f"\n"
        f"Ciclo(s) aberto(s) nesta edicao: {', '.join(novos)}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"Antes de abrir um ciclo, o ATLAS atualiza os contratos (API, banco, decisoes)\n"
        f"em .delta-11/memoria/project-core.md ou nas fatias de memoria/project-core/.\n"
        f"So o ATLAS escreve o project-core (D7): CRONOS, peca a atualizacao ao ATLAS e\n"
        f"abra o ciclo depois.\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    antes, depois = comum.before_and_after(evento)
    novos = list((cycle_markers(depois) - cycle_markers(antes)).elements())
    if not novos:
        return 0
    idade, nome = newest_core_age()
    if idade is not None and idade <= comum.window_seconds():
        comum.log(HOOK, f"OK: ciclo novo ({', '.join(novos)}) com {nome} alterado ha {idade / 3600:.1f} h")
        return 0
    return comum.block(HOOK, message(novos, idade), f"ciclo novo {', '.join(novos)} sem project-core recente")


if __name__ == "__main__":
    comum.run(main, HOOK)
