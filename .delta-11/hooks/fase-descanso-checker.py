#!/usr/bin/env python3
"""
Vigia da Fase 7 (Descanso Consagrado, Dia 7) — Delta-11 v6.3 (2026-10-14). C-015, C-027.

Principio de Selagem: a Fase 7 so pode ser SELADA (consagrada) com DUAS condicoes:
  1. Os 10 entregaveis do Dia 7 em `.delta-11/memoria/decisoes/` da pasta
     principal, um por numero: AAAA-MM-DD-descanso-NN-<slug>.md (NN = 01 a 10).
  2. Registro explicito do TESTE SUPREMO no kanban (2 semanas de operacao
     autonoma), por exemplo: "**TESTE SUPREMO PASSOU** — 2 semanas sem intervencao".

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`): so quando a edicao
ACRESCENTA uma linha que declara o selo da fase, por exemplo:
  "Fase 7 consagrada"   "Fase 7 selada"   "[SELO 7]"   "[SELO FASE 7.0]"
  "Dia 7 consagrado"    "[CONSAGRAÇÃO] ... SELO"   "[DESCANSO] ... consagrado"
Um "[7]" solto no texto nao dispara mais (C-027) e a palavra CONSAGRACAO agora e
reconhecida com a grafia certa.

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

HOOK = "fase-descanso-checker"
FASE = "7"
PREFIXO = "descanso"
ENTREGAVEIS = {
    1: "docs-tecnica", 2: "docs-dominio", 3: "e2e", 4: "deploy-auto", 5: "runbooks",
    6: "monitoramento", 7: "tag-release", 8: "backup-testado", 9: "dr-testado",
    10: "onboarding-testado",
}
TESTE_SUPREMO_RE = re.compile(
    r"TESTE\s+SUPREMO\s*\**\s*(?:PASSOU|OK|SIM|APROVADO)\b"
    r"|opera[cç][ãa]o\s+aut[ôo]noma\s+(?:de\s+)?(?:2|duas)\s+semanas"
    r"|(?:2|duas)\s+semanas\s+sem\s+interven[cç][ãa]o",
    re.IGNORECASE,
)


def message(selo: list[str], faltando: list[int], nomes: list[str], sem_teste: bool) -> str:
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Selo da Fase 7 (Descanso Consagrado, Dia 7)\n"
        f"\n"
        f"Linha que declara o selo: {selo[0][:160]}\n"
    )
    if faltando:
        texto += f"\nEntregaveis presentes: {len(ENTREGAVEIS) - len(faltando)} de {len(ENTREGAVEIS)}. Faltam:\n"
        texto += "".join(
            f"  {n:02d}. {ENTREGAVEIS[n]}  -> .delta-11/memoria/decisoes/AAAA-MM-DD-{PREFIXO}-{n:02d}-{ENTREGAVEIS[n]}.md\n"
            for n in faltando
        )
        if nomes:
            texto += "Ja existem:\n" + "".join(f"  - {n}\n" for n in nomes)
    if sem_teste:
        texto += (
            "\nFalta o registro do TESTE SUPREMO no kanban (2 semanas de operacao\n"
            "autonoma), no formato:\n"
            "  **TESTE SUPREMO PASSOU** — 2 semanas sem intervencao\n"
        )
    texto += (
        "\nModelo: .delta-11/templates/fase-descanso-template.md\n"
        "Protocolo: .delta-11/protocolos/fase-descanso.md\n"
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
    _presentes, faltando, nomes = comum.phase_artifacts(PREFIXO, len(ENTREGAVEIS))
    sem_teste = not TESTE_SUPREMO_RE.search(depois)
    if not faltando and not sem_teste:
        comum.log(HOOK, "OK: selo da Fase 7 com 10 entregaveis + TESTE SUPREMO")
        return 0
    resumo = f"selo da Fase 7: {len(faltando)} entregavel(is) faltando" + ("; sem TESTE SUPREMO" if sem_teste else "")
    return comum.block(HOOK, message(selo, faltando, nomes, sem_teste), resumo)


if __name__ == "__main__":
    comum.run(main, HOOK)
