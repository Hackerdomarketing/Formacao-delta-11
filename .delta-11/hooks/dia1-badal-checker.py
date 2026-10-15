#!/usr/bin/env python3
"""
Vigia "Dia 1 — teste do badal" — Delta-11 v6.3 (2026-10-14). Item C-025.

Dia 1 da Metodologia Genesis (Luz): o proposito do software precisa estar
respondido em 8 perguntas antes de seguir:
  1. Frase decisoria   2. Identidade assumida   3. Identidade fugida
  4. Teste do badal (nitidez entre as duas identidades)
  5. Inimigo unico     6. Trauma unico          7. Lago abandonado
  8. Nova categoria de solucao

Alvos (PreToolUse em Edit|Write):
  - `docs/prd.md` do projeto;
  - `.delta-11/memoria/project-core.md`.

O que confere (C-025 — so a secao VISAO, e so quando ela muda):
  - No project-core: a secao cujo titulo contem "VISAO" (ex.: "## VISÃO DO
    PRODUTO"). Edicoes em outras secoes (contratos, banco...) NAO sao conferidas,
    para nao travar a atualizacao de contratos que o vigia contratos-minimos exige.
  - No PRD: a secao VISAO, se existir; senao, o documento todo.
  - Precisa de pelo menos 6 dos 8 elementos PREENCHIDOS. Um rotulo com
    [preencher] ou {{X}} nao conta como resposta.
  - Se a secao VISAO nao mudou nesta edicao, libera.

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

HOOK = "dia1-badal-checker"
PRD_RE = re.compile(r"(?:^|/)docs/prd\.md$", re.IGNORECASE)
PROJECT_CORE_RE = re.compile(r"(?:^|/)\.delta-11/memoria/project-core\.md$", re.IGNORECASE)
TITULO_VISAO_RE = re.compile(r"vis[aã]o", re.IGNORECASE)
MIN_ELEMENTOS = 6

ELEMENTOS = [
    ("1. Frase decisoria", "Qual a frase que o usuario pronuncia ao decidir usar?",
     r"\bfrase\s+(?:intern[ae]\s+)?decis[oó]ri[ae]\b"),
    ("2. Identidade assumida", "Quem o usuario se torna ao usar?",
     r"\bidentidade\s+assumida\b|\bidentidade\s+que\s+(?:o\s+)?usu[áa]rio\s+assume\b"),
    ("3. Identidade fugida", "Quem ele foge de continuar sendo?",
     r"\bidentidade\s+fugida\b|\bidentidade\s+que\s+(?:ele\s+)?foge\b"),
    ("4. Teste do badal", "As duas identidades ficam nitidas entre si?",
     r"\bteste\s+(?:do\s+)?badal\b|\bnitidez\s+entre\s+as\s+(?:duas\s+)?identidades\b|\bvayavdel\b"),
    ("5. Inimigo unico", "Qual o UNICO inimigo que o software derrota?",
     r"\binimigo\s+[úu]nico\b|\b[úu]nico\s+inimigo\b"),
    ("6. Trauma unico", "Qual o UNICO trauma que o software cura?",
     r"\btrauma\s+[úu]nico\b|\b[úu]nico\s+trauma\b"),
    ("7. Lago abandonado", "De qual UNICO lago o usuario migra?",
     r"\blago\s+abandonado\b|\b[úu]nico\s+lago\b"),
    ("8. Nova categoria", "Que categoria nova o software estabelece no mercado?",
     r"\bnova\s+categoria\b|\bcategoria\s+de\s+solu[çc][ãa]o\b"),
]


def answered(texto: str, padrao: str) -> bool:
    """O elemento aparece E tem resposta (na mesma linha ou na linha seguinte)."""
    regex = re.compile(padrao, re.IGNORECASE)
    linhas = texto.splitlines()
    for indice, linha in enumerate(linhas):
        achado = regex.search(linha)
        if not achado:
            continue
        resto = (linha[:achado.start()] + " " + linha[achado.end():])
        if comum.has_real_text(resto):
            return True
        for seguinte in linhas[indice + 1:indice + 3]:
            if not seguinte.strip():
                continue
            if comum.TITULO_RE.match(seguinte.strip()) and not seguinte.strip().startswith("####"):
                break
            if any(re.search(p, seguinte, re.IGNORECASE) for _r, _q, p in ELEMENTOS):
                break  # a linha seguinte ja e outro rotulo, nao uma resposta
            if comum.has_real_text(seguinte):
                return True
            break
    return False


def missing(texto: str) -> list[tuple[str, str]]:
    return [(rotulo, pergunta) for rotulo, pergunta, padrao in ELEMENTOS if not answered(texto, padrao)]


def message(caminho: str, faltando: list[tuple[str, str]]) -> str:
    achados = len(ELEMENTOS) - len(faltando)
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Dia 1 da Metodologia Genesis (Luz)\n"
        f"\n"
        f"Arquivo: {caminho}\n"
        f"A secao VISAO tem {achados} de 8 respostas preenchidas (minimo {MIN_ELEMENTOS}).\n"
        f"\nFaltam:\n"
    )
    for rotulo, pergunta in faltando:
        texto += f"  {rotulo}\n    -> {pergunta}\n"
    texto += (
        "\nResponda na secao 'VISÃO DO PRODUTO' do project-core.md (ou no docs/prd.md).\n"
        "Rotulo com [preencher] ainda nao conta como resposta.\n"
        "Referencia: .delta-11/conhecimento/metodologia-genesis-camadas.md → Dia 1\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0
    caminho = comum.target_path_text(evento)
    normal = caminho.replace("\\", "/")
    eh_prd = bool(PRD_RE.search(normal))
    if not eh_prd and not PROJECT_CORE_RE.search(normal):
        return 0

    antes, depois = comum.before_and_after(evento)
    visao_antes = comum.section(antes, TITULO_VISAO_RE)
    visao_depois = comum.section(depois, TITULO_VISAO_RE)
    if visao_depois is None:
        if not eh_prd:
            return 0  # project-core sem secao VISAO: nada a conferir
        visao_antes, visao_depois = antes, depois
    if visao_antes is not None and visao_antes.strip() == visao_depois.strip():
        return 0  # a edicao nao mexeu na VISAO

    faltando = missing(visao_depois)
    if len(ELEMENTOS) - len(faltando) >= MIN_ELEMENTOS:
        comum.log(HOOK, f"OK: VISAO com {len(ELEMENTOS) - len(faltando)} de 8 respostas")
        return 0
    return comum.block(
        HOOK, message(caminho, faltando),
        f"VISAO com {len(ELEMENTOS) - len(faltando)} de 8 respostas em {os.path.basename(caminho)}",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
