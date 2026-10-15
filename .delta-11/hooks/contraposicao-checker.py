#!/usr/bin/env python3
"""
Vigia "contraposicao lateral" — Delta-11 v6.3 (2026-10-14). Item C-023.

Principio 3 da Metodologia Genesis: cada camada (Dia) declara a sua
contraposicao lateral — o lado DOMINANTE e o lado TESTEMUNHA — do tipo certo do
dia. Sem isso o Selo da camada fica incompleto.

Alvo: Edit/Write em `.delta-11/memoria/project-core.md` (PreToolUse).

O que confere (C-023 — estrutura, nao so a palavra):
  - A secao cujo titulo contem "Contraposicao" (ex.: "## CONTRAPOSIÇÃO LATERAL
    (por dia)").
  - Cada linha preenchida dessa secao que fala de um Dia precisa ter os DOIS lados
    separados por "×", " x ", " vs " ou "↔":
        - **Dia 1 — Tipo 1 (existencial-identitaria):** identidade assumida × identidade fugida
    Linhas so com marcadores ([preencher], {{X}}, <...>) contam como "ainda vazias"
    e nao bloqueiam.

Quando bloqueia (exit 2):
  - a secao foi ALTERADA nesta edicao e tem linha de Dia preenchida sem os dois
    lados, ou nao sobrou nenhuma declaracao valida apesar de haver texto;
  - a secao EXISTIA e a edicao a apaga.
Quando NAO bloqueia:
  - edicoes em outras partes do project-core (contratos, banco, visual...) —
    a secao de contraposicao nao mudou;
  - project-core antigo sem a secao (so registra AVISO no diario).

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

HOOK = "contraposicao-checker"
PROJECT_CORE_RE = re.compile(r"(?:^|/)\.delta-11/memoria/project-core\.md$", re.IGNORECASE)
TITULO_CONTRAPOSICAO_RE = re.compile(r"contraposi[cç][aã]o", re.IGNORECASE)
DIA_RE = re.compile(r"\bDia\s*[1-7]\b", re.IGNORECASE)
SEPARADOR_RE = re.compile(r"\s(?:×|x|X|vs\.?|versus|↔)\s|×|↔")

EXEMPLOS = [
    "- **Dia 1 — Tipo 1 (existencial-identitaria):** identidade assumida × identidade fugida",
    "- **Dia 2 — Tipo 2 (estrutural tripla):** arquitetura × mundo externo",
    "- **Dia 3 — Tipo 3 (substancia + estrutural):** schema × contratos",
    "- **Dia 4 — Tipo 4 (funcional-temporal):** dominante (sincrono) × testemunha (assincrono)",
    "- **Dia 5 — Tipo 5 (territorial + escalar):** backend × frontend",
    "- **Dia 6 — Tipo 6 (complementar + hierarquica):** autenticacao × autorizacao",
    "- **Dia 7 — Tipo 7 (de estado):** obra consumada × em curso",
]


def problems(secao: str) -> list[str]:
    """Linhas de Dia preenchidas sem os dois lados. Lista vazia = ok."""
    ruins = []
    linhas_de_dia = 0
    texto_real = False
    for linha in secao.splitlines():
        # tira o rotulo "Dia N — Tipo N (...):" e confere os dois lados no corpo
        corpo = re.split(r":\*{0,2}", linha, maxsplit=1)[-1] if ":" in linha else linha
        if not DIA_RE.search(linha):
            if comum.has_real_text(linha) and not linha.lstrip().startswith(">"):
                texto_real = True
            continue
        linhas_de_dia += 1
        if not comum.has_real_text(corpo):
            continue  # Dia ainda nao preenchido ([preencher])
        partes = SEPARADOR_RE.split(corpo)
        lados = [p for p in partes if comum.has_real_text(p, 2)]
        if len(partes) < 2 or len(lados) < 2:
            ruins.append(linha.strip())
    if texto_real and linhas_de_dia == 0:
        ruins.append("(a secao tem texto, mas nenhuma linha 'Dia N ... lado A × lado B')")
    return ruins


def message(caminho: str, motivo: str, ruins: list[str]) -> str:
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Principio 3 da Metodologia Genesis\n"
        f"\n"
        f"Arquivo: {caminho}\n"
        f"Motivo: {motivo}\n"
    )
    if ruins:
        texto += "\nLinhas sem os dois lados (dominante × testemunha):\n"
        texto += "".join(f"  - {l[:160]}\n" for l in ruins[:7])
    texto += (
        "\nCada Dia declara a contraposicao com os DOIS lados, assim:\n"
        + "".join(f"  {e}\n" for e in EXEMPLOS)
        + "\nLinhas ainda nao preenchidas podem ficar com [preencher].\n"
        "Referencia: .delta-11/conhecimento/metodologia-genesis-camadas.md\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0
    caminho = comum.target_path_text(evento)
    if not PROJECT_CORE_RE.search(caminho.replace("\\", "/")):
        return 0

    antes, depois = comum.before_and_after(evento)
    secao_antes = comum.section(antes, TITULO_CONTRAPOSICAO_RE)
    secao_depois = comum.section(depois, TITULO_CONTRAPOSICAO_RE)

    if secao_depois is None:
        if secao_antes is not None:
            return comum.block(
                HOOK, message(caminho, "a edicao APAGA a secao de contraposicao lateral", []),
                "secao de contraposicao apagada do project-core",
            )
        comum.log(HOOK, "AVISO: project-core sem secao de contraposicao lateral (nao bloqueado)")
        return 0

    if secao_antes is not None and secao_antes.strip() == secao_depois.strip():
        return 0  # a edicao mexeu em outra parte do project-core

    ruins = problems(secao_depois)
    if not ruins:
        comum.log(HOOK, "OK: contraposicao lateral declarada com os dois lados")
        return 0
    return comum.block(
        HOOK, message(caminho, "declaracao de contraposicao incompleta", ruins),
        f"contraposicao incompleta ({len(ruins)} linha(s))",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
