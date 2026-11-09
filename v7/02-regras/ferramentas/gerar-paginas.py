#!/usr/bin/env python3
"""Monta a página de cada papel a partir das fontes (um fato, um lugar).

Cada página = fonte do papel + núcleo + as fontes que a primeira linha do papel pede
(<!-- inclui: a.md b.md -->). Cada valor citado (`nome`) ganha o número ao lado, tirado de valores.md.
Uso: python3 gerar-paginas.py   (escreve só em paginas/; não aceita pasta de destino)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "fontes"
PAPEIS = FONTES / "papeis"
CABECALHO = "<!-- GERADO por ferramentas/gerar-paginas.py a partir de fontes/. Não edite aqui: edite a fonte. -->\n\n"
INCLUI = re.compile(r"^<!-- inclui: (.*?) -->\s*$")


def inclusoes(texto_papel: str) -> list[str]:
    primeira = texto_papel.splitlines()[0] if texto_papel else ""
    m = INCLUI.match(primeira)
    return m.group(1).split() if m else []


def sem_inclusoes(texto_papel: str) -> str:
    linhas = texto_papel.splitlines()
    if linhas and INCLUI.match(linhas[0]):
        linhas = linhas[1:]
    return "\n".join(linhas).strip()


def com_valores(corpo: str) -> str:
    for linha in (FONTES / "valores.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- `([a-z_]+)`: (\d+ \S+) — ", linha)
        if m:
            corpo = corpo.replace(f"`{m.group(1)}`", f"`{m.group(1)}` ({m.group(2)})")
    return corpo


def montar(papel: str) -> str:
    texto_papel = (PAPEIS / f"{papel}.md").read_text(encoding="utf-8")
    partes = [sem_inclusoes(texto_papel), (FONTES / "nucleo.md").read_text(encoding="utf-8").strip()]
    partes += [(FONTES / extra).read_text(encoding="utf-8").strip() for extra in inclusoes(texto_papel)]
    return CABECALHO + com_valores("\n\n---\n\n".join(partes)) + "\n"


def gerar(destino: Path) -> dict[str, str]:
    destino.mkdir(parents=True, exist_ok=True)
    paginas = {}
    for arquivo in sorted(PAPEIS.glob("*.md")):
        texto = montar(arquivo.stem)
        (destino / arquivo.name).write_text(texto, encoding="utf-8")
        paginas[arquivo.name] = texto
    return paginas


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(__doc__)
        sys.exit(0 if sys.argv[1] in ("-h", "--help") else 2)
    for nome, texto in gerar(RAIZ / "paginas").items():
        palavras = len(texto.split())
        print(f"{nome:18s} {palavras:5d} palavras  ~{palavras / 500:.1f} páginas")
