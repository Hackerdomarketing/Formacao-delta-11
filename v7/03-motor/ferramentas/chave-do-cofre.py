#!/usr/bin/env python3
"""Tira uma chave do cofre do dono (secretctl) na hora de usar: é o comando que o `apiKeyHelper` do Claude Code roda.

Uso: python3 chave-do-cofre.py <ENTRADA>            imprime SÓ a chave (nada mais) e sai com 0; se não der, não imprime nada na saída e sai com erro
     python3 chave-do-cofre.py --existe <ENTRADA>   não imprime nada; sai com 0 (a entrada existe), 1 (não existe) ou 3 (o cofre não abriu)
     python3 chave-do-cofre.py --listar             imprime só os NOMES das entradas (nunca valores)

O secretctl só pergunta a senha mestra num terminal, então este programa abre um terminal de mentira, entrega a senha que está no
Chaveiro do Mac (o mesmo lugar de onde o servidor do cofre a tira) e lê a resposta. A senha e a chave nunca vão para arquivo, nem
para a linha de comando; a chave só passa pela saída deste programa, direto para o Claude Code.
Para os pulsos: com DELTA11_SECRETCTL apontando um `secretctl` de mentira, ele é chamado direto, sem Chaveiro nem terminal.
"""
from __future__ import annotations

import os
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

CONTA_DO_CHAVEIRO = "secretctl"
SERVICO_DO_CHAVEIRO = "secretctl-mcp"
PEDIDO_DA_SENHA = b"master password:"
LIMITE_EM_SEGUNDOS = 30
SAIDA_NAO_EXISTE, SAIDA_COFRE_FECHADO = 1, 3


def falhar(motivo: str, codigo: int = SAIDA_COFRE_FECHADO) -> None:
    print(f"chave-do-cofre: {motivo}", file=sys.stderr)
    sys.exit(codigo)


def localizar_secretctl() -> str:
    dito = os.environ.get("DELTA11_SECRETCTL")
    if dito:
        return dito
    achado = shutil.which("secretctl") or str(Path.home() / "bin" / "secretctl")
    if not Path(achado).exists():
        falhar("não achei o programa secretctl (esperado em ~/bin/secretctl)")
    return achado


def senha_do_chaveiro() -> str:
    feito = subprocess.run(["security", "find-generic-password", "-a", CONTA_DO_CHAVEIRO, "-s", SERVICO_DO_CHAVEIRO, "-w"],
                           capture_output=True, text=True)
    senha = feito.stdout.strip() if feito.returncode == 0 else ""
    if not senha:
        falhar(f"a senha do cofre não está no Chaveiro do Mac (conta {CONTA_DO_CHAVEIRO}, serviço {SERVICO_DO_CHAVEIRO})")
    return senha


def rodar_com_senha(programa: str, argumentos: list[str], senha: str) -> tuple[int, str]:
    """Roda o secretctl num terminal de mentira, entrega a senha quando ele a pede e devolve (código de saída, o que ele escreveu depois do pedido)."""
    pid, terminal = pty.fork()
    if pid == 0:  # o filho vira o secretctl
        os.execv(programa, [programa, *argumentos])
    recebido, enviada, prazo = b"", False, time.monotonic() + LIMITE_EM_SEGUNDOS
    while time.monotonic() < prazo:
        if not select.select([terminal], [], [], 0.2)[0]:
            continue
        try:
            pedaco = os.read(terminal, 4096)
        except OSError:  # o filho fechou o terminal: acabou
            break
        if not pedaco:
            break
        recebido += pedaco
        if not enviada and PEDIDO_DA_SENHA in recebido:
            os.write(terminal, senha.encode() + b"\n")
            enviada = True
    else:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        falhar(f"o cofre não respondeu em {LIMITE_EM_SEGUNDOS} segundos")
    _, estado = os.waitpid(pid, 0)
    texto = recebido.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "")
    if senha in texto:  # o terminal repetiu a senha de volta: nada disso pode sair
        falhar("o terminal do cofre repetiu a senha; recusei a resposta")
    depois = texto.rsplit("master password:", 1)[-1] if "master password:" in texto else texto
    return os.waitstatus_to_exitcode(estado), depois.lstrip("\n")


def rodar_secretctl(argumentos: list[str]) -> tuple[int, str]:
    programa = localizar_secretctl()
    if os.environ.get("DELTA11_SECRETCTL"):  # o secretctl de mentira dos pulsos: sem senha, sem terminal
        feito = subprocess.run([programa, *argumentos], capture_output=True, text=True)
        return feito.returncode, feito.stdout
    return rodar_com_senha(programa, argumentos, senha_do_chaveiro())


def nomes_das_entradas() -> set[str]:
    codigo, saida = rodar_secretctl(["list"])
    if codigo != 0:
        falhar("o cofre não abriu (a senha do Chaveiro pode estar velha)")
    return set(re.findall(r"[A-Za-z0-9_.\-/]+", saida))


def main() -> int:
    argumentos = sys.argv[1:]
    if argumentos == ["--listar"]:
        print("\n".join(sorted(nomes_das_entradas())))
        return 0
    if len(argumentos) == 2 and argumentos[0] == "--existe":
        return 0 if argumentos[1] in nomes_das_entradas() else SAIDA_NAO_EXISTE
    if len(argumentos) != 1 or argumentos[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    codigo, saida = rodar_secretctl(["get", argumentos[0]])
    chave = saida.strip()
    if codigo != 0 or not chave or "\n" in chave:  # com erro, ou sem nada, ou com mais de uma linha (um aviso junto): nunca imprime
        falhar(f"não consegui ler a entrada {argumentos[0]} do cofre", SAIDA_NAO_EXISTE)
    print(chave)
    return 0


if __name__ == "__main__":
    sys.exit(main())
