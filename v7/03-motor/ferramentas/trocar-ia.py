#!/usr/bin/env python3
"""Troca a IA (o "cérebro") de um produto que já tem o Delta-11 v7 instalado: claude, deepseek, minimax, kimi ou gateway.

Uso: python3 trocar-ia.py <pasta-do-produto> <perfil>
     python3 trocar-ia.py <pasta-do-produto> gateway --endereco <URL> --modelo-forte <nome> --modelo-medio <nome> --modelo-leve <nome> [--entrada-do-cofre <NOME>]

Escreve a IA em `.claude/settings.local.json` do produto (que fica fora do git) com o mesmo código do `instalar.py --ia`, e diz o perfil
na `.delta-11/motor/VERSAO` (um commit só com esse arquivo). A chave não vai para arquivo: vem do cofre na hora, pelo `apiKeyHelper`.
Os perfis, os endereços, os nomes de modelo e a fonte oficial de cada um estão em agentes/perfis-de-ia.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

FERRAMENTAS = Path(__file__).resolve().parent


def carregar_perfil_de_ia():
    especificacao = importlib.util.spec_from_file_location("perfil_de_ia", FERRAMENTAS / "perfil_de_ia.py")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def recusar(motivo: str) -> int:
    print(f"ERRO: {motivo}\nNada foi mudado.")
    return 1


def guardar_a_versao_no_git(destino: Path, perfil: str) -> None:
    """Só a VERSAO entra no commit (a configuração local fica fora do git); sem git ou sem mudança, não faz nada."""
    versao = ".delta-11/motor/VERSAO"
    if subprocess.run(["git", "-C", str(destino), "ls-files", "--error-unmatch", versao], capture_output=True).returncode != 0:
        return
    if subprocess.run(["git", "-C", str(destino), "diff", "--quiet", "--", versao], capture_output=True).returncode == 0:
        return
    subprocess.run(["git", "-C", str(destino), "add", "--", versao], capture_output=True)
    subprocess.run(["git", "-C", str(destino), "commit", "-q", "-m", f"Delta-11 v7: a IA do produto agora é {perfil}", "--", versao], capture_output=True)


def main() -> int:
    leitor = argparse.ArgumentParser(add_help=False)
    leitor.add_argument("pasta", nargs="?")
    leitor.add_argument("perfil", nargs="?")
    leitor.add_argument("--endereco", default="")
    leitor.add_argument("--modelo-forte", default="")
    leitor.add_argument("--modelo-medio", default="")
    leitor.add_argument("--modelo-leve", default="")
    leitor.add_argument("--entrada-do-cofre", default="")
    pedido, sobrou = leitor.parse_known_args()
    if not pedido.pasta or not pedido.perfil or sobrou:
        print(__doc__)
        return 2
    modulo = carregar_perfil_de_ia()
    destino = Path(pedido.pasta).expanduser().resolve()
    try:
        marca = modulo.arquivo_da_versao(destino)
        if not (marca.is_file() and '"delta11": "v7"' in marca.read_text(encoding="utf-8", errors="replace")):
            return recusar(f"{destino} não tem o v7 instalado (não achei .delta-11/motor/VERSAO); instale com instalar.py antes de escolher a IA.")
        resumo = modulo.aplicar_perfil_de_ia(destino, pedido.perfil, pedido.endereco, pedido.modelo_forte, pedido.modelo_medio, pedido.modelo_leve,
                                             pedido.entrada_do_cofre)
    except modulo.RecusaDePerfil as recusa:
        return recusar(str(recusa))
    modulo.gravar_ia_na_versao(destino, pedido.perfil)
    guardar_a_versao_no_git(destino, pedido.perfil)
    if pedido.perfil == "claude":
        print("OK — a IA deste produto agora é o Claude (o login normal do Claude Code); tirei da configuração local as variáveis e o comando de chave de outra IA.")
    else:
        fonte = f"fonte lida em {resumo['lido_em']}" if resumo["lido_em"] else "fonte não conferida"
        print(f"OK — a IA deste produto agora é {resumo['nome']} (modelo forte: {resumo['modelo_forte']}, médio: {resumo['modelo_medio']}, "
              f"leve: {resumo['modelo_leve']}; {fonte}).")
        print(f"  A chave vem do cofre na hora (entrada {resumo['entrada_do_cofre']}); nada foi gravado em arquivo.")
    for aviso in resumo["avisos"]:
        print(f"  AVISO: {aviso}")
    print("  Feche e abra a conversa do Claude nesta pasta para valer.")
    print(f"  {modulo.LEMBRETE_DO_LIMITE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
