#!/usr/bin/env python3
"""
MARCADOR DE SECOES DO MOTOR — Delta-11 v7 (motor multiempresa).

O CLAUDE.md da Formacao tem ~66 mil caracteres que descrevem o motor
ORIGINAL (Claude Code): como ativar, como disparar, como os hooks disparam,
como o Agent tool cria worktree, como o SendMessage funciona.

Essas secoes nao valem para outro motor. Mas nao podem ser APAGADAS: tem
conhecimento duro (os 37 vigias com seus gatilhos e timeouts, a estrutura
do prompt de ativacao, o formato do payload de hook). A solucao e:

  1. MARCAR cada secao do motor com marcadores proprios:
         <!-- MOTOR:CODIGO-INICIO --> ... <!-- MOTOR:CODIGO-FIM -->
     Entre os marcadores, a secao e do motor e pode ser SUBSTITUIDA.
  2. O conteudo original fica guardado em
     `.delta-11/motor/CLAUDE-original.md` (a referencia, consultavel).
  3. O gerador (`gerar-bloco-motor.py`) troca o que esta entre os marcadores
     pela versao do motor pedido.

O que fica FORA dos marcadores e a METODOLOGIA (as 7 camadas, as 17 regras
inviolaveis, o protocolo de codigo, o painel, as correcoes aprendidas) —
que e a mesma em todo motor e nunca e tocada.

O QUE ESTE SCRIPT FAZ (uma vez, na fonte):
  - le o CLAUDE.md
  - envolve cada secao do motor nos marcadores
  - NAO apaga nada: o texto original continua la, agora marcado

O QUE ELE NAO FA: nao decide o que o motor novo escreve no lugar. Isso e do
gerador.

Uso:
  python3 .delta-11/motor/marcar-secoes-motor.py [--desmarcar]
      marca (ou desmarca) as secoes do motor no CLAUDE.md da fonte.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DELTA_DIR = AQUI.parent
INICIO = "<!-- MOTOR:CODIGO-INICIO -->"
FIM = "<!-- MOTOR:CODIGO-FIM -->"

# As secoes que descrevem o MOTOR (Claude Code). A METODOLOGIA fica de fora
# e nunca e marcada — ela e igual em todo motor.
SECOES_DO_MOTOR = [
    "## ⚡ ATIVAÇÃO DELTA-11",
    "## 🚧 VOCÊ NÃO É UM AGENTE Δ-11?",
    "## 🤖 DISPATCH AUTÔNOMO",
    "## 🛡️ VIGIAS AUTOMÁTICOS",
    "## PROTOCOLO DE ATIVAÇÃO",
    "## MUDANÇA ESTRUTURAL v4.0 —",
    "## MUDANÇA ESTRUTURAL v4.0 Onda 2",
    "## PROTOCOLO DE INÍCIO DE TAREFA",
    "## PROTOCOLO DE FINALIZAÇÃO DE TAREFA",
    "## PROTOCOLO DE FASE CONCLUÍDA",
    "## PROTOCOLO DE CONTEXTO ESGOTADO",
    "## PROTOCOLO DE DISPATCH DE AGENTES",
]


def _eh_secao_do_motor(titulo: str) -> bool:
    return any(titulo.startswith(p) for p in SECOES_DO_MOTOR)


def marcar(texto: str) -> tuple[str, int]:
    """Envolve cada secao do motor nos marcadores. Devolve (texto, n_secoes)."""
    if INICIO in texto:
        return texto, 0  # ja marcado

    linhas = texto.splitlines(keepends=True)
    saida: list[str] = []
    marcadas = 0
    dentro = False

    # Primeiro passo: descobrir os indices das secoes de nivel 2.
    indices_n2 = [i for i, l in enumerate(linhas) if l.startswith("## ")]

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if linha.startswith("## ") and _eh_secao_do_motor(linha):
            if dentro:
                # A secao anterior era do motor e esta tambem: fecha a
                # anterior e abre esta (uma secao por bloco).
                saida.append(f"{FIM}\n")
            saida.append(f"{INICIO}\n")
            dentro = True
            marcadas += 1
        saida.append(linha)

        # Fecha a marcacao na proxima secao de nivel 2 que NAO e do motor.
        if dentro:
            proxima = None
            for j in indices_n2:
                if j > i:
                    proxima = j
                    break
            if proxima is not None and not _eh_secao_do_motor(linhas[proxima]):
                saida.append(f"{FIM}\n")
                dentro = False
        i += 1

    if dentro:
        saida.append(f"{FIM}\n")

    return "".join(saida), marcadas


def desmarcar(texto: str) -> tuple[str, int]:
    """Remove os marcadores (o texto fica como estava)."""
    if INICIO not in texto:
        return texto, 0
    n = texto.count(INICIO)
    saida = []
    for linha in texto.splitlines(keepends=True):
        if linha.strip() in (INICIO, FIM):
            continue
        saida.append(linha)
    return "".join(saida), n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--desmarcar", action="store_true")
    parser.add_argument("--fonte", help="CLAUDE.md de entrada. Padrao: a raiz da Formacao.")
    parser.add_argument("--saida", help="Arquivo de saida. Padrao: edita a entrada.")
    args = parser.parse_args()

    fonte = Path(args.fonte) if args.fonte else DELTA_DIR.parent / "CLAUDE.md"
    if not fonte.is_file():
        print(f"ERRO: CLAUDE.md nao encontrado em {fonte}", file=sys.stderr)
        return 1

    texto = fonte.read_text(encoding="utf-8")
    if args.desmarcar:
        resultado, n = desmarcar(texto)
        acao = "desmarcadas"
    else:
        resultado, n = marcar(texto)
        acao = "marcadas"

    if args.saida:
        Path(args.saida).write_text(resultado, encoding="utf-8")
        print(f"{n} secao(oes) {acao} em {args.saida}")
    else:
        fonte.write_text(resultado, encoding="utf-8")
        print(f"{n} secao(oes) {acao} em {fonte}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
