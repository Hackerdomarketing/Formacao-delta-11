#!/usr/bin/env python3
"""Aviso de abertura da conversa (gancho de início de sessão do Delta-11 v7; roda ao abrir e ao retomar a conversa).

Conta ao ATLAS em que pé o produto está: cada camada ou pedido do quadro (uma pasta com `abertura.md` ou `quadro.md`)
com a situação escrita na primeira linha do quadro, há quantos minutos ele mudou, até quando espera (Camada 7), se um
CRONOS trabalha nele agora em outra conversa aberta, os avisos do alarme do produto e, enquanto `esteira-comandos.txt`
não tem `testar:` e `testes:`, que a esteira recusa tudo (e se a esteira própria do produto foi trocada). O que fazer com isso está nas
rotas do ATLAS. Nunca muda nada além de tirar do registro de CRONOS os de conversas que já fecharam.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import registro_de_cronos as reg  # noqa: E402
import motor  # noqa: E402

FECHADAS = ("selad", "encerrad", "feit")


def situacao_de(pasta: Path) -> str:
    quadro = pasta / "quadro.md"
    texto = quadro.read_text(encoding="utf-8") if quadro.is_file() else ""
    m = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", texto, re.IGNORECASE)
    return m.group(1).strip().strip("*_ ").lower() if m else "aberto (o quadro ainda não diz a situação)"


def de_fora(raiz: Path) -> tuple[list[str], set[str], list[str]]:
    """O que as leis que rodam fora deste computador deixaram no repositório remoto: correções (do SCOUT) e alarmes
    (devolve também os nomes dos alarmes de lá, com os resolvidos)."""
    import subprocess
    git = lambda *a: subprocess.run(["git", "-C", str(raiz), *a], capture_output=True, text=True, timeout=15)
    try:
        if git("rev-parse", "--abbrev-ref", "@{u}").returncode != 0:
            return [], set(), []
        git("fetch", "-q")
        novos = git("rev-list", "--count", "HEAD..@{u}").stdout.strip()
        remotos = {a.split("/")[-1] for a in git("ls-tree", "--name-only", "@{u}", ".delta-11/alarmes/").stdout.split()}
        mudados_la = {a.split("/")[-1] for a in git("diff", "--name-only", "HEAD...@{u}", "--", ".delta-11/alarmes/").stdout.split()}
        pedidos_la = {a.split("/")[-1] for a in git("ls-tree", "--name-only", "@{u}", ".delta-11/pedidos-das-leis/").stdout.split()}
        pedidos_aqui = {a.name for a in (raiz / ".delta-11" / "pedidos-das-leis").glob("*")} if (raiz / ".delta-11" / "pedidos-das-leis").is_dir() else set()
        locais = {a.name for a in (raiz / ".delta-11" / "alarmes").glob("*")} if (raiz / ".delta-11" / "alarmes").is_dir() else set()
    except (OSError, subprocess.SubprocessError):
        return ["- Não deu para olhar o repositório remoto agora."], set(), []
    saida = []
    if novos and novos != "0":
        saida.append(f"- O repositório remoto tem {novos} mudança(s) que ainda não estão aqui (por exemplo correções do SCOUT); a próxima entrega pela esteira as traz.")
    # Do remoto: o aviso novo lá, ou reescrito lá depois de resolvido (o alarme voltou); o SCOUT o lê com git show @{u}:<caminho>.
    def quando_la(nome: str) -> int:  # a hora do último commit do remoto que mexeu nesse alarme
        saida_git = git("log", "-1", "--format=%ct", "@{u}", "--", f".delta-11/alarmes/{nome}").stdout.strip()
        return int(saida_git) if saida_git.isdigit() else 0

    def resolvido_depois(nome: str) -> bool:  # o .resolvido (lá ou aqui) é mais novo que a última vez que o alarme escreveu
        marca_aqui = raiz / ".delta-11" / "alarmes" / f"{nome}.resolvido"
        hora_da_marca = max(quando_la(f"{nome}.resolvido"), int(marca_aqui.stat().st_mtime) if marca_aqui.is_file() else 0)
        return hora_da_marca >= quando_la(nome) and (f"{nome}.resolvido" in remotos or marca_aqui.is_file())
    pendentes = sorted(a for a in (remotos - locais) | mudados_la if not a.endswith(".resolvido") and not resolvido_depois(a))
    novos_pedidos = sorted(a for a in pedidos_la - pedidos_aqui if not a.endswith(".tratado") and f"{a}.tratado" not in pedidos_la | pedidos_aqui)
    for pedido in novos_pedidos:  # o ATLAS não tem terminal: o conteúdo vem aqui (ao encaminhar, ele escreve `<pedido>.tratado`)
        conteudo = git("show", f"@{{u}}:.delta-11/pedidos-das-leis/{pedido}").stdout.strip().splitlines()[:20]
        saida.append(f"- Pedido que uma lei do produto abriu no repositório remoto, {pedido}: " + " / ".join(conteudo))
    return saida, remotos, pendentes


def main() -> None:
    try:
        pedido = motor.ler(aceita_vazio=True)  # pelo tradutor do programa dito no comando
    except motor.SemPrograma as erro:
        print(f"Situação do produto: o motor do Delta-11 não pode contá-la, e a trava barra tudo: {erro}")
        return
    reg.anotar_sono()
    origem, sessao = pedido["origem"] or "startup", pedido["sessao"]
    raiz = motor.raiz(obrigatoria=False) or Path(os.getcwd())
    mapa = json.loads((AQUI / "lugares.json").read_text(encoding="utf-8"))
    silencio = mapa["silencio_max_minutos"]
    # O registro de um CRONOS cuja conversa fechou fica: ele diz quem conduziu cada quadro por último (a trava não deixa
    # acordar um CRONOS de quadro velho). Quem trabalha agora é conferido pela conversa viva.
    quadro = raiz / ".delta-11" / "quadro"
    desta = [r for r in reg.registros() if r.get("sessao") == sessao and r.get("trabalhando") and reg.roda(r.get("pid", 0)) and reg.ativo(r)]
    if origem in ("clear", "compact"):
        cabeca = "Situação do produto, contada pelo motor do Delta-11 depois de a conversa ser limpa ou resumida:"
    elif origem == "resume":
        cabeca = "Situação do produto, contada pelo motor do Delta-11 ao retomar esta conversa (os CRONOS da conversa anterior não valem mais: para seguir uma camada, ligue um novo):"
    else:
        cabeca = "Situação do produto, contada pelo motor do Delta-11 ao abrir esta conversa (nenhum CRONOS desta conversa está vivo):"
    linhas = [cabeca]
    for vivo in desta:
        linhas.append(f"- O CRONOS de {vivo.get('quadro')} trabalha nesta conversa: agentId {vivo.get('agente')} (fale com ele por mensagem).")
    if origem in ("clear", "compact"):  # a mesma conversa: o CRONOS que terminou nela ainda acorda por mensagem
        for parado in (r for r in reg.registros() if r.get("sessao") == sessao and r.get("agente") and not r.get("trabalhando") and not reg.velho(r)):
            linhas.append(f"- O CRONOS de {parado.get('quadro')} terminou nesta conversa: agentId {parado.get('agente')} (para seguir, mande mensagem a ele).")
    abertos = 0
    for pasta in sorted(p for p in quadro.iterdir() if p.is_dir()) if quadro.is_dir() else []:
        if not ((pasta / "abertura.md").is_file() or (pasta / "quadro.md").is_file()):
            continue  # só linhas (Destruidor da Luz, SCOUT): não é camada nem pedido
        situacao = situacao_de(pasta)
        if situacao.startswith(FECHADAS) or re.match(r"parada\b", situacao):
            continue
        abertos += 1
        arquivos = [a for a in pasta.rglob("*") if a.is_file()]
        minutos = int((time.time() - max(a.stat().st_mtime for a in arquivos)) / 60) if arquivos else None
        quem = reg.trabalhando_em(pasta.name.lower())
        if any(v.get("sessao") == sessao for v in quem) or any(pasta.name.lower() in (v.get("quadro"), *v.get("quadros", [])) for v in desta):
            cronos = "o CRONOS desta conversa trabalha nele"
        elif quem:
            cronos = "um CRONOS trabalha nele agora, em outra conversa aberta"
        else:
            cronos = "nenhum CRONOS trabalhando"
        quando = "quadro vazio" if minutos is None else f"o quadro mudou há {minutos} minutos"
        linhas.append(f"- {pasta.name}: {situacao}; {quando}; {cronos}.")
        abertura = (pasta / "abertura.md").read_text(encoding="utf-8") if (pasta / "abertura.md").is_file() else ""
        chamada = re.search(r"^chamada ao dono\W*:\s*(.+)$", abertura, re.IGNORECASE | re.MULTILINE)
        if chamada and situacao.startswith("esperando o dono"):
            linhas.append(f"  Chamada ao dono que o ARQUITETO deixou na abertura: {chamada.group(1).strip()}")
    if not abertos:
        linhas.append("- Nenhuma camada ou pedido aberto no quadro.")
    for frase in reg.parados_no_meio(raiz):  # a conversa fechou com agentes trabalhando: "esperando o dono" não esconde isso
        linhas.append(f"- Trabalho parado no meio em {frase}: ligue um CRONOS do quadro, que segue por ele.")
    atualizado = raiz / ".delta-11" / "motor" / "atualizado-com-camada-aberta.md"
    aberturas = [a.stat().st_mtime for a in quadro.glob("*/abertura.md")] if quadro.is_dir() else []
    tratada = any(a.stat().st_mtime > atualizado.stat().st_mtime and "motor atualizado: tratado" in a.read_text(encoding="utf-8", errors="replace").lower()
                  for a in quadro.glob("*/abertura.md")) if atualizado.is_file() and quadro.is_dir() else False
    if atualizado.is_file() and not tratada:
        resumo = " / ".join(l.strip("- ").strip() for l in atualizado.read_text(encoding="utf-8").splitlines()[1:8] if l.strip())
        linhas.append("- O motor foi atualizado com trabalho pela metade; leve ao ARQUITETO o que ficou pela metade (ele decide pelo modelo do tamanho "
                      f"e abre a camada no caminho novo): {resumo}")
    if (raiz / ".delta-11" / "anterior-v6" / "PONTO-DE-PARTIDA.md").is_file() and not (raiz / ".delta-11" / "luz.md").is_file():
        linhas.append("Este produto veio do Delta-11 antigo. Antes de começar a Luz, leia `.delta-11/anterior-v6/PONTO-DE-PARTIDA.md` e comece a conversa da Luz "
                      "pelo meio: mostre ao dono, em poucas linhas, o que o produto é e onde parou, e peça que ele confirme ou corrija.")
    comandos = raiz / "esteira-comandos.txt"
    dos_comandos = comandos.read_text(encoding="utf-8", errors="replace").splitlines() if comandos.is_file() else []
    if not all(any(re.match(rf"\s*{chave}\s*:\s*\S", l) for l in dos_comandos) for chave in ("testar", "testes")):
        linhas.append("- esteira-comandos.txt ainda não tem as linhas `testar:` e `testes:`: a esteira recusa tudo até os comandos serem escritos "
                      "(quem os escreve: o BACK, ou o Construtor único do caminho pequeno).")
        if (raiz / ".delta-11" / "motor" / "esteira-propria-trocada.md").is_file():
            linhas.append("- A esteira que o produto tinha construído foi trocada pela do motor: os testes e pulsos antigos dela continuam no código "
                          "(um pedido os tira, ou o `testar:` os chama).")
    de_la, remotos, do_remoto = de_fora(raiz)
    linhas += de_la
    alarmes = raiz / ".delta-11" / "alarmes"
    todos = ({a.name for a in alarmes.iterdir() if a.is_file()} if alarmes.is_dir() else set())
    def resolvido(aviso: str) -> bool:  # o SCOUT marca o resolvido; o alarme que volta reescreve o aviso depois dele
        marca = alarmes / f"{aviso}.resolvido"
        if marca.is_file():
            return (alarmes / aviso).stat().st_mtime <= marca.stat().st_mtime
        return f"{aviso}.resolvido" in remotos
    avisos = sorted(a for a in todos if not a.endswith(".resolvido") and not resolvido(a))
    pedidos_das_leis = raiz / ".delta-11" / "pedidos-das-leis"
    nomes_pedidos = {a.name for a in pedidos_das_leis.iterdir() if a.is_file()} if pedidos_das_leis.is_dir() else set()
    abertos_pelas_leis = sorted(a for a in nomes_pedidos if not a.endswith(".tratado") and f"{a}.tratado" not in nomes_pedidos)
    if abertos_pelas_leis:
        linhas.append("- Pedidos que uma lei do produto abriu (trate como pedido do dono; depois escreva `<pedido>.tratado`): " + ", ".join(abertos_pelas_leis) + ".")
    todos_os_avisos = avisos + [f"{a} (no repositório remoto)" for a in do_remoto if a not in avisos]
    linhas.append(f"- Avisos do alarme do produto: {', '.join(todos_os_avisos)}." if todos_os_avisos else "- Nenhum aviso do alarme, aqui nem no repositório remoto.")
    linhas.append(f"Hora agora: {time.strftime('%Y-%m-%d %H:%M %z')}. (silencio_max = {silencio} minutos)")
    print("\n".join(linhas))


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print(f"Situação do produto: o motor não conseguiu ler o quadro ({type(erro).__name__}: {erro}).")
    sys.exit(0)
