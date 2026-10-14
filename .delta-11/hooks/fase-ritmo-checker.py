#!/usr/bin/env python3
"""
Vigia da Fase 3.5 (Ritmo Temporal, Dia 4) — Delta-11 v6.3 (2026-10-14). C-015, C-028.

Principio de Selagem: a Fase 3.5 so pode ser SELADA com os 10 artefatos do Dia 4
em `.delta-11/memoria/decisoes/` da pasta principal, um por numero:
  AAAA-MM-DD-ritmo-temporal-NN-<slug>.md   (NN = 01 a 10, arquivo nao vazio)

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`, caminho relativo
ou absoluto): so quando a edicao ACRESCENTA uma linha que declara o selo da fase,
por exemplo:
  "Fase 3.5 selada"   "[SELO 3.5]"   "Dia 4 selado"   "[RITMO] ... SELO"
Concluir tarefas individuais da fase (que produzem os artefatos um a um) nao e
bloqueado — o selo e que exige os 10 (protocolos/fase-ritmo.md, "Criterio
objetivo de selo").

A mensagem lista exatamente os numeros que FALTAM (C-028).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "fase-ritmo-checker"
FASE = "3.5"
PREFIXO = "ritmo-temporal"
ARTEFATOS = {
    1: "sistema-eventos", 2: "filas", 3: "jobs-agendados", 4: "cache-ttl",
    5: "timeouts", 6: "retries", 7: "circuit-breakers", 8: "ci-cd-staging",
    9: "observabilidade", 10: "sub-contraposicao",
}


def message(selo: list[str], faltando: list[int], nomes: list[str]) -> str:
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Selo da Fase 3.5 (Ritmo Temporal, Dia 4)\n"
        f"\n"
        f"Linha que declara o selo: {selo[0][:160]}\n"
        f"Presentes: {len(ARTEFATOS) - len(faltando)} de {len(ARTEFATOS)}. Faltam {len(faltando)}:\n"
    )
    texto += "".join(
        f"  {n:02d}. {ARTEFATOS[n]}  -> .delta-11/memoria/decisoes/AAAA-MM-DD-{PREFIXO}-{n:02d}-{ARTEFATOS[n]}.md\n"
        for n in faltando
    )
    if nomes:
        texto += "\nJa existem:\n" + "".join(f"  - {n}\n" for n in nomes)
    texto += (
        "\nCrie os que faltam com .delta-11/templates/fase-ritmo-template.md e declare o\n"
        "selo de novo. Protocolo: .delta-11/protocolos/fase-ritmo.md\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    antes, depois = comum.before_and_after(evento)
    selo = comum.declares_seal(comum.new_lines(antes, depois), FASE)
    if not selo:
        return 0
    _presentes, faltando, nomes = comum.phase_artifacts(PREFIXO, len(ARTEFATOS))
    if not faltando:
        comum.log(HOOK, "OK: selo da Fase 3.5 com os 10 artefatos")
        return 0
    return comum.block(HOOK, message(selo, faltando, nomes), f"selo da Fase 3.5 com {len(faltando)} artefato(s) faltando")


if __name__ == "__main__":
    comum.run(main, HOOK)
