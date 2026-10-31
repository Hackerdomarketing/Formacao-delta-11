#!/usr/bin/env python3
"""
PORTAO UNIVERSAL DO DELTA-11 — v7 (motor multiempresa).

O PROBLEMA QUE ELE RESOLVE
-------------------------
O Claude Code e o Codex disparam os 37 vigias do Delta-11 sozinhos: o
orquestrador chama o vigia antes de cada acao (evento `PreToolUse`). O Kilo
NAO tem hooks — o schema oficial dele (`app.kilo.ai/config.json`) nao tem a
chave "hooks" e nao existe "PreToolUse" no pacote. Entao, num motor sem
hooks, o vigia so roda se ALGUEM o chamar.

Este e o Portao: um programa que o agente consulta antes de agir. Ele tem
um contrato de CLI ESTAVEL, igual em todo motor:

    porteiro <vigia> < payload.json
    exit 0  = liberado
    exit 2  = BLOQUEADO (o motivo vai no stderr)
    exit 1  = erro interno do vigia (a acao foi liberada sem conferencia)

O payload e o mesmo evento JSON que o Claude Code entrega no stdin dos
hooks. Entao o MESMO vigia roda nos tres motores:

    Claude Code / Codex:  o orquestrador chama o vigia direto (hook)
    Kilo / qualquer outro: o agente chama o porteiro, que chama o vigia

POR QUE UM PORTAO E NAO "RODAR OS VIGIAS NA MAO"
-------------------------------------------------
A Formacao tem uma regra dura sobre isso: "protecao que depende de agente
obedecer prompt NAO e protecao; toda regra critica precisa de hook tecnico".
O portao nao elimina essa regra — ele a torna MECANICA:

  - o agente tem UM comando para rodar (o porteiro), que cabe numa linha;
  - o porteiro roda o vigia de verdade, com o payload de verdade;
  - o codigo de saida e o mesmo (2 bloqueia), entao o agente nao pode
    "decidir" que o bloqueio nao vale;
  - o portao tem um MODO AUDITORIA, que roda TODOS os vigias de bloqueio e
    devolve um relatorio, sem bloquear — para quando se quer conferir o
    estado da protecao sem o risco de travar o trabalho.

O MODO AUDITORIA e o que permite usar o Delta-11 em qualquer motor com
seguranca: em vez de depender de cada agente lembrar, o portao varre tudo.

COMO O AGENTE DESCUBRE O PORTAO
-------------------------------
O `AGENTS.md` / `CLAUDE.md` do projeto (o bloco do motor) diz o caminho. No
Kilo, o caminho e:

    python3 .delta-11/motor/porteiro/porteiro.py <vigia>

e a forma completa de auditar tudo:

    python3 .delta-11/motor/porteiro/porteiro.py --auditar

Requer Python 3.8+. Usa so a biblioteca padrao.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MOTOR_DIR = AQUI.parent
HOOKS_DIR = MOTOR_DIR.parent / "hooks"

# Os vigias que BLOQUEIAM (os que o Claude Code registra em PreToolUse e
# UserPromptSubmit). Esta e a lista que o modo --auditar percorre.
# Fonte: `.delta-11/templates/settings-hooks.json`.
def _vigias_de_bloqueio() -> list[tuple[str, str]]:
    """[(nome-do-arquivo, evento)] de todos os vigias que bloqueiam."""
    import re

    template = MOTOR_DIR.parent / "templates" / "settings-hooks.json"
    if not template.is_file():
        return []
    try:
        dados = json.loads(template.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    vistos: list[tuple[str, str]] = []
    for evento in ("PreToolUse", "UserPromptSubmit"):
        for grupo in (dados.get("hooks") or {}).get(evento, []):
            for handler in grupo.get("hooks", []):
                comando = handler.get("command", "")
                achado = re.search(r"/hooks/([^\"/]+)\"$", comando)
                if not achado:
                    continue
                par = (achado.group(1), evento)
                if par not in vistos:
                    vistos.append(par)
    return vistos


def _rodar_vigia(nome: str, payload: bytes) -> tuple[int, str, str]:
    """Roda um vigia com o payload no stdin. Devolve (codigo, stdout, stderr)."""
    caminho = HOOKS_DIR / nome
    if not caminho.is_file():
        return 127, "", f"vigia nao encontrado: {caminho}"
    if nome.endswith(".js"):
        comando = ["node", str(caminho)]
    elif nome.endswith(".sh"):
        comando = ["bash", str(caminho)]
    else:
        comando = ["python3", str(caminho)]
    try:
        resultado = subprocess.run(
            comando,
            input=payload,
            capture_output=True,
            timeout=120,
            cwd=os.getcwd(),
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"[{nome}] vigia estourou o tempo limite (120 s)"
    except OSError as exc:
        return 127, "", f"[{nome}] nao deu para rodar: {exc}"
    return resultado.returncode, resultado.stdout.decode("utf-8", "replace"), resultado.stderr.decode("utf-8", "replace")


def porta(vigia: str, payload: bytes) -> int:
    """Chama um vigia e devolve o codigo de saida dele (0 libera, 2 bloqueia)."""
    codigo, _stdout, stderr = _rodar_vigia(vigia, payload)
    if stderr:
        sys.stderr.write(stderr)
    return codigo


def auditar(payload: bytes) -> int:
    """
    Roda TODOS os vigias de bloqueio em modo auditoria: nenhum bloqueia, mas
    todos dizem o que bloqueariam. Devolve 0 se nada bloqueia, 2 se algo
    bloqueia (para o agente poder decidir).
    """
    print("PORTAO DO DELTA-11 — auditoria completa")
    print("=" * 60)
    bloqueios: list[tuple[str, str]] = []
    erros: list[tuple[str, str]] = []

    for nome, evento in _vigias_de_bloqueio():
        codigo, _stdout, stderr = _rodar_vigia(nome, payload)
        if codigo == 2:
            bloqueios.append((nome, stderr.strip()))
            print(f"  [BLOQUEARIA] {nome}")
        elif codigo not in (0, 1):
            erros.append((nome, stderr.strip() or f"exit {codigo}"))
            print(f"  [ERRO]       {nome} (exit {codigo})")
        else:
            print(f"  [ok]         {nome}")

    print("=" * 60)
    if bloqueios:
        print(f"\n{len(bloqueios)} vigia(s) BLOQUEARIA(M) esta acao:\n")
        for nome, motivo in bloqueios:
            print(f"--- {nome} ---")
            print(motivo or "(sem motivo)")
            print()
        return 2
    if erros:
        print(f"\n{len(erros)} vigia(s) falharam (a acao foi liberada sem conferencia):")
        for nome, motivo in erros:
            print(f"  {nome}: {motivo}")
        return 1
    print("\nNenhum vigia bloqueia esta acao.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="porteiro",
        description="Portao universal do Delta-11: chama um vigia (ou todos) "
                    "com o payload da acao e devolve o codigo de bloqueio.",
    )
    parser.add_argument(
        "vigia",
        nargs="?",
        help="Nome do vigia (ex.: pre-criacao-arquivo.py). Omitir = auditar tudo.",
    )
    parser.add_argument(
        "--auditar",
        action="store_true",
        help="Roda todos os vigias de bloqueio em modo relatorio (nao bloqueia).",
    )
    parser.add_argument(
        "--payload",
        help="Caminho de um arquivo JSON com o evento. Sem isso, le do stdin.",
    )
    args = parser.parse_args()

    if args.payload:
        try:
            payload = Path(args.payload).read_bytes()
        except OSError as exc:
            print(f"ERRO: nao deu para ler o payload: {exc}", file=sys.stderr)
            return 1
    else:
        payload = sys.stdin.buffer.read()

    if not payload.strip():
        print(
            "PORTAO: payload vazio. Mande o evento JSON da acao no stdin, "
            "ou use --payload ARQUIVO.",
            file=sys.stderr,
        )
        return 1

    # O payload precisa ser um JSON valido: um evento malformado nao deve
    # passar em silencio (seria a mesma falha que o vigia teria).
    try:
        evento = json.loads(payload)
    except ValueError as exc:
        print(f"PORTAO: payload nao e JSON valido: {exc}", file=sys.stderr)
        return 1
    if not isinstance(evento, dict):
        print("PORTAO: o payload precisa ser um objeto JSON", file=sys.stderr)
        return 1

    if args.auditar or not args.vigia:
        return auditar(payload)

    return porta(args.vigia, payload)


if __name__ == "__main__":
    sys.exit(main())
