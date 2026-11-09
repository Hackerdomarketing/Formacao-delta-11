#!/usr/bin/env python3
"""Guarda no git o que foi escrito em .delta-11/ (gancho de fim do Documentador e do CRONOS: um pedido não chama o Documentador). Não bloqueia nada.

Junta só .delta-11/, nunca o código (que só entra pela esteira). O cofre, o teste guardado e o que o leitor leu ficam
fora: o .gitignore já os deixa de fora, e, se algum tiver entrado por engano, ele sai do commit aqui.
Com repositório remoto, antes de enviar traz o que entrou lá (alarmes, correções do SCOUT pela automação), para os dois
não se separarem: se os commits só daqui mexem só em .delta-11/, o remoto entra e o registro é juntado por cima, sem
tocar no trabalho pela metade de nenhum agente. Código daqui ainda não enviado, um choque, ou um arquivo que o remoto
mudou e que está mudado na pasta: não junta (a próxima entrega pela esteira cuida, como o contrato dela diz).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

FORA = [".delta-11/cofre", ".delta-11/teste-guardado", ".delta-11/leitor"]


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, timeout=60)


def juntar_o_remoto() -> bool:
    """Deixa a pasta com o remoto dentro. Devolve se dá para enviar."""
    git("fetch", "-q")
    if git("merge-base", "--is-ancestor", "@{u}", "HEAD").returncode == 0:
        return True  # nada novo lá
    antes = git("rev-parse", "HEAD").stdout.strip()
    if git("merge-base", "--is-ancestor", "HEAD", "@{u}").returncode == 0:
        junto = git("rev-parse", "@{u}").stdout.strip()  # só avanço
    else:
        base = git("merge-base", "HEAD", "@{u}").stdout.strip()
        daqui = git("diff", "--name-only", "-z", base, "HEAD").stdout.split("\0")
        if any(a and not a.startswith(".delta-11/") for a in daqui):
            return False  # código daqui que o remoto não tem: a esteira junta
        arvore = git("merge-tree", "--write-tree", "HEAD", "@{u}")
        if arvore.returncode != 0:
            return False  # choque
        junto = git("commit-tree", arvore.stdout.split()[0], "-p", "HEAD", "-p", "@{u}",
                    "-m", "registro do Delta-11: junta o repositório remoto").stdout.strip()
    mudados = [a for a in git("diff", "--name-only", "-z", "HEAD", junto).stdout.split("\0") if a]
    if mudados and git("status", "--porcelain", "-z", "--", *mudados).stdout.strip("\0"):
        return False  # um agente está mexendo num arquivo que o remoto mudou
    if git("update-ref", "HEAD", junto, antes).returncode != 0:
        return False  # a esteira entrou no meio
    git("reset", "-q")
    existem = set(git("ls-tree", "-r", "--name-only", "-z", "HEAD", "--", *mudados).stdout.split("\0")) if mudados else set()
    if existem - {""}:
        git("checkout", "-q", "HEAD", "--", *sorted(existem - {""}))
    for apagado in set(mudados) - existem:
        Path(apagado).unlink(missing_ok=True)
    return True


def guardar() -> None:
    """O commit de .delta-11/ é montado num índice à parte, a partir do último commit: o que estiver no índice de verdade
    (código de uma esteira interrompida no meio, por exemplo) não vai junto nem é desfeito."""
    antes = git("rev-parse", "-q", "--verify", "HEAD").stdout.strip()
    if not antes:
        return
    with tempfile.TemporaryDirectory() as pasta:
        ambiente = {**os.environ, "GIT_INDEX_FILE": str(Path(pasta) / "indice")}
        aqui = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, timeout=60, env=ambiente)
        aqui("read-tree", antes)
        if aqui("add", "-A", "--", ".delta-11").returncode != 0:
            return
        aqui("rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *FORA)  # se um segredo tinha entrado no git por engano, ele sai
        arvore = aqui("write-tree").stdout.strip()
        if not arvore or arvore == git("rev-parse", antes + "^{tree}").stdout.strip():
            return
        novo = aqui("commit-tree", arvore, "-p", antes, "-m", "registro do Delta-11").stdout.strip()
    if novo and git("update-ref", "HEAD", novo, antes).returncode == 0:  # a esteira entrou no meio: fica para a próxima vez
        git("reset", "-q", "--", ".delta-11")  # o índice de verdade fica com o registro (e sem os segredos); o resto, como estava


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import motor
    os.chdir(motor.raiz())  # a pasta do produto, pelo tradutor do programa dito no comando (sem ela, não guarda nada)
    guardar()
    if git("rev-parse", "--abbrev-ref", "@{u}").returncode == 0 and juntar_o_remoto():
        git("push", "-q")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
