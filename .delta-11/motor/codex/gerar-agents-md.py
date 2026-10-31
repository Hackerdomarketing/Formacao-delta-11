#!/usr/bin/env python3
"""
GERADOR DO AGENTS.md (motor Codex) — Delta-11 v7 (motor multiempresa).

NO CODEX, QUEM LE AS INSTRUCOES AUTOMATICAMENTE E O `AGENTS.md`.

O `AGENTS.md` e lido pelo Codex em cada execucao, a partir da raiz do
projeto (e dos diretorios ancestrais). O `CLAUDE.md` e o equivalente no
Claude Code. Um projeto que roda nos dois precisa dos DOIS — o Codex nao
le `CLAUDE.md`, e o Claude Code nao le `AGENTS.md`.

Este gerador cria o `AGENTS.md` a partir do `CLAUDE.md` da Formacao, com o
BLOCO DO MOTOR trocado pelo do Codex. O resto e o mesmo (a metodologia e
identica; e o texto do motor Codex substitui as 12 secoes marcadas).

Para o Claude Code, o `CLAUDE.md` do projeto segue intacto. Para o Codex,
o `AGENTS.md` tem o texto do Codex. Nenhum dos dois perde nada.

O `AGENTS.md` NAO e instalado nos motores que nao o leem (Claude Code, Kilo)
— o sincronizador so o cria no motor Codex.

Uso:
  python3 .delta-11/motor/codex/gerar-agents-md.py SAIDA [--motor codex]
      gera o AGENTS.md em SAIDA.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MOTOR_DIR = AQUI.parent
DELTA_DIR = MOTOR_DIR.parent
FONTE_CLAUDE = DELTA_DIR.parent / "CLAUDE.md"


def _carregar(nome: str, caminho: Path):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("saida", help="Arquivo AGENTS.md a escrever.")
    parser.add_argument("--motor", default="codex")
    parser.add_argument("--fonte", help="CLAUDE.md de entrada. Padrao: a raiz da Formacao.")
    args = parser.parse_args()

    fonte = Path(args.fonte) if args.fonte else FONTE_CLAUDE
    if not fonte.is_file():
        print(f"ERRO: CLAUDE.md nao encontrado em {fonte}", file=sys.stderr)
        return 1

    gerador = _carregar("delta11_gerar_claude", MOTOR_DIR / "gerar-claude-por-motor.py")
    texto = gerador.gerar(fonte.read_text(encoding="utf-8"), args.motor)

    # O AGENTS.md do Codex nao deve ter os marcadores internos (sao ruido
    # para o agente do Codex, que nao os usa).
    texto = texto.replace("<!-- MOTOR:CODIGO-INICIO -->\n", "").replace("<!-- MOTOR:CODIGO-FIM -->\n", "")

    destino = Path(args.saida)
    destino.write_text(texto, encoding="utf-8")
    print(f"AGENTS.md escrito em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
