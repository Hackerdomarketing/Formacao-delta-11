#!/usr/bin/env python3
"""Pulso da tela do app (ganchos/tela-do-app.py): prova as recusas e o que ela pede ao Mac, sem depender de janela.

Troca o Mac por um de mentira (que diz qual app está na frente, se a tela está bloqueada, se o macOS nega) e confere, caso
a caso, o que a tela do app recusa (ação, argumentos, app não declarado, digitar com outro programa na frente, atalho sem
modificador) e o que ela pede (só modelos fixos, com o texto como argumento). Depois, se este Mac deixa, um ensaio de
verdade com a Calculadora (abrir, ver, foto, digitar, fechar), pulado com aviso se o macOS negar, se a tela estiver
bloqueada ou se a Calculadora já estiver aberta (a do dono não se fecha).
Uso: python3 testar-tela-do-app.py [--sem-janela]   (sai com 1 se algum caso der o resultado errado)
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
PROGRAMA = MOTOR / "ganchos" / "tela-do-app.py"
_spec = importlib.util.spec_from_file_location("tela_do_app", PROGRAMA)
tela = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tela)


class MacDeMentira(tela.Mac):
    """Responde como o Mac responderia; guarda cada pedido para o caso conferir."""

    def __init__(self, frente: str = "Gastos", obedece: bool = True, aberto: bool = True, bloqueada: bool = False, preso: bool = False):
        self.frente, self.obedece, self.aberto, self.bloqueada, self._preso = frente, obedece, aberto, bloqueada, preso
        self.pedidos: list[tuple] = []

    def preso(self) -> bool:
        return self._preso

    def jxa(self, modelo: str, *valores: str) -> str:
        assert modelo in tela.MODELOS, modelo  # só modelos fixos
        self.pedidos.append((modelo, valores))
        if modelo == "bloqueada":
            return "SIM" if self.bloqueada else "NAO"
        if modelo == "estado":
            return json.dumps({"aberto": self.aberto, "frente": self.aberto and self.frente == valores[0], "da_frente": self.frente, "pid": 42, "janelas": 1})
        if modelo == "ativar":
            if self.obedece:
                self.frente = valores[0]
            return "OK"
        if modelo == "ver":
            return 'Window "Gastos"\n  Button "Salvar"\n  TextField "Valor" = 12'
        if modelo == "janelas":
            return "[7]"
        if modelo == "clicar":
            return "CLICOU Button" if valores[1] == "Salvar" else "NAO ACHEI"
        if modelo == "fechar":
            self.aberto = False
            return "PEDIU 42"
        return {"digitar": "DIGITOU", "tecla": "APERTOU"}[modelo]

    def abrir(self, comando: list[str]) -> tuple[int, str]:
        self.pedidos.append(("open", tuple(comando)))
        self.aberto = True
        return 0, ""

    def soltar(self, programa: Path, relato: Path) -> None:
        self.pedidos.append(("soltar", (str(programa),)))
        self.aberto = True

    def capturar(self, janela: int, arquivo: Path) -> tuple[int, str]:
        self.pedidos.append(("capturar", (janela, str(arquivo))))
        arquivo.write_bytes(b"\x89PNG")
        return 0, ""

    def matar(self, pid: int) -> None:
        self.pedidos.append(("matar", (pid,)))

    def esperar(self, segundos: float) -> None:
        pass


def produto(base: Path, nome: str, comandos: str, liberada: float | None = 3600) -> Path:
    """O produto de mentira; `liberada`: segundos até o fim da hora que o dono liberou a tela (None: sem o arquivo)."""
    p = base / nome
    (p / ".claude/hooks/delta-11").mkdir(parents=True)
    (p / ".claude/hooks/delta-11/tela-do-app.py").write_bytes(PROGRAMA.read_bytes())
    (p / "esteira-comandos.txt").write_text(comandos, encoding="utf-8")
    if liberada is not None:
        (p / ".delta-11").mkdir()
        fim = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + liberada))
        (p / ".delta-11/tela-liberada.md").write_text(f"# A tela do Mac do dono\n\nAté: {fim}\n", encoding="utf-8")
    return p


def pedir(p: Path, mac: MacDeMentira, *argumentos: str, cwd: Path | None = None) -> tuple[str, str]:
    """(tipo do resultado, texto): feito, recusa, nao-deu ou negado."""
    try:
        return "feito", tela.executar(list(argumentos), mac, raiz=p, cwd=cwd or p)
    except tela.Recusa as recusa:
        return "recusa", str(recusa)
    except tela.NaoDeu as erro:
        return "nao-deu", str(erro)
    except tela.Negado as negado:
        return "negado", str(negado)


def pedidos_de(mac: MacDeMentira, modelo: str) -> list[tuple]:
    return [v for m, v in mac.pedidos if m == modelo]


def casos_simulados(base: Path) -> list[tuple[str, bool]]:
    comandos = "testar: sh testes.sh\ntestes: testes/\napp: Gastos.app\natalho: ctrl+option+g\n"
    p = produto(base, "produto", comandos)
    resultados = []

    def caso(nome: str, certo: bool) -> None:
        resultados.append((nome, certo))

    tipo, texto = pedir(p, MacDeMentira())
    caso("sem ação: RECUSA, ensinando as ações", tipo == "recusa" and "abrir, ver, foto" in texto)
    tipo, texto = pedir(p, MacDeMentira(), "apagar")
    caso("ação desconhecida: RECUSA", tipo == "recusa" and "diga a ação" in texto)
    mac = MacDeMentira()
    tipo, texto = pedir(p, mac, "abrir", "Outro App")
    caso("app não declarado na linha (`abrir Outro App`): RECUSA, sem pedir nada ao Mac", tipo == "recusa" and "nunca vem na linha" in texto and not mac.pedidos)
    tipo, texto = pedir(p, MacDeMentira(), "digitar")
    caso("`digitar` sem o texto: RECUSA", tipo == "recusa" and "um argumento" in texto)
    tipo, texto = pedir(p, MacDeMentira(), "digitar", "linha 1\nlinha 2")
    caso("`digitar` com quebra de linha: RECUSA (Enter é `tecla`)", tipo == "recusa" and "quebra de linha" in texto)
    tipo, texto = pedir(p, MacDeMentira(), "digitar", "x" * (tela.TEXTO_MAX + 1))
    caso("`digitar` com texto grande demais: RECUSA", tipo == "recusa" and str(tela.TEXTO_MAX) in texto)
    mac = MacDeMentira(bloqueada=True)
    tipo, texto = pedir(p, mac, "tecla", "cmd+banana")
    caso("`tecla` desconhecida: RECUSA antes de perguntar ao Mac", tipo == "recusa" and "tecla desconhecida" in texto and not mac.pedidos)
    tipo, texto = pedir(p, MacDeMentira(), "tecla", "hyper+a")
    caso("modificador desconhecido: RECUSA", tipo == "recusa" and "fora do formato" in texto)
    tipo, texto = pedir(p, MacDeMentira(), "ver", cwd=p / ".claude")
    caso("fora da raiz da pasta: RECUSA", tipo == "recusa" and "raiz da pasta" in texto)
    tipo, texto = pedir(p, MacDeMentira(preso=True), "ver")
    caso("dentro de uma caixa de areia: RECUSA, ensinando a linha certa", tipo == "recusa" and "caixa de areia" in texto and tela.CHAMADA in texto)
    for nome_do_caso, liberada in (("sem-hora", None), ("hora-acabou", -120)):
        q = produto(base, nome_do_caso, comandos, liberada=liberada)
        mac = MacDeMentira()
        tipo, texto = pedir(q, mac, "abrir")
        caso(f"tela sem a hora liberada pelo dono ({nome_do_caso}): RECUSA, sem pedir nada ao Mac, ensinando a pedir pelo ATLAS",
             tipo == "recusa" and "tela-liberada.md" in texto and "PARA CRONOS" in texto and not mac.pedidos)
    q = produto(base, "fechar-sem-hora", comandos, liberada=None)
    mac = MacDeMentira()
    tipo, texto = pedir(q, mac, "fechar")
    caso("`fechar` também precisa da hora liberada (fecharia o app com o que o dono digitava)", tipo == "recusa" and not mac.pedidos)
    q = produto(base, "hora-longe-demais", comandos, liberada=30 * 3600)
    mac = MacDeMentira()
    tipo, texto = pedir(q, mac, "ver")
    caso("hora liberada além de `tela_liberada_max`: RECUSA", tipo == "recusa" and "tela_liberada_max" in texto and not mac.pedidos)
    sem_app = produto(base, "sem-app", "testar: sh testes.sh\ntestes: testes/\n")
    tipo, texto = pedir(sem_app, MacDeMentira(), "ver")
    caso("sem `app:` em esteira-comandos.txt: RECUSA, ensinando", tipo == "recusa" and "não declara o app" in texto)
    for errado in ("../Gastos", 'Gas"tos', "Gastos:x"):
        q = produto(base, f"app-errado-{len(resultados)}", f"app: {errado}\n")
        tipo, texto = pedir(q, MacDeMentira(), "ver")
        caso(f"`app: {errado}`: RECUSA (só o nome)", tipo == "recusa" and "fora do formato" in texto)
    mac = MacDeMentira(frente="Finder", obedece=False)
    tipo, texto = pedir(p, mac, "digitar", "café 12,50")
    caso("`digitar` com outro programa na frente: RECUSA e nada é digitado", tipo == "recusa" and "não está na frente" in texto and "Finder" in texto
         and not pedidos_de(mac, "digitar") and pedidos_de(mac, "ativar"))
    mac = MacDeMentira(frente="Finder", obedece=False)
    tipo, texto = pedir(p, mac, "tecla", "cmd+s")
    caso("`tecla` com outro programa na frente: RECUSA e nada é apertado", tipo == "recusa" and not pedidos_de(mac, "tecla"))
    mac = MacDeMentira(frente="Finder", obedece=True)
    tipo, texto = pedir(p, mac, "digitar", "'; do shell script \"rm -rf ~\" --")
    digitado = pedidos_de(mac, "digitar")
    caso("`digitar` traz o app para a frente e manda o texto como argumento do modelo fixo, nunca como código",
         tipo == "feito" and digitado == [("Gastos", "'; do shell script \"rm -rf ~\" --")] and "rm -rf" not in tela.MODELOS["digitar"])
    mac = MacDeMentira()
    tipo, texto = pedir(p, mac, "tecla", "cmd+shift+n")
    caso("`tecla cmd+shift+n` com o app na frente: aperta, com os modificadores", tipo == "feito"
         and pedidos_de(mac, "tecla") == [("Gastos", "letra", "n", "command down,shift down")])
    mac = MacDeMentira()
    tipo, texto = pedir(p, mac, "tecla", "enter")
    caso("`tecla enter`: aperta pelo código da tecla", tipo == "feito" and pedidos_de(mac, "tecla") == [("Gastos", "codigo", "36", "")])
    sem_atalho = produto(base, "sem-atalho", "app: Gastos\n")
    tipo, texto = pedir(sem_atalho, MacDeMentira(), "atalho")
    caso("`atalho` sem `atalho:` declarado: RECUSA", tipo == "recusa" and "não declara o atalho" in texto)
    fraco = produto(base, "atalho-fraco", "app: Gastos\natalho: shift+a\n")
    tipo, texto = pedir(fraco, MacDeMentira(), "atalho")
    caso("`atalho: shift+a` (sem cmd, option ou ctrl): RECUSA, a tecla iria para o programa da frente", tipo == "recusa" and "precisa de cmd" in texto)
    mac = MacDeMentira(frente="Finder", obedece=False)
    tipo, texto = pedir(p, mac, "atalho")
    caso("`atalho`: manda a combinação global declarada, com qualquer programa na frente", tipo == "feito"
         and pedidos_de(mac, "tecla") == [("", "letra", "g", "control down,option down")])
    mac = MacDeMentira()
    tipo, texto = pedir(p, mac, "clicar", "Salvar")
    tipo2, texto2 = pedir(p, MacDeMentira(), "clicar", "Nada disso")
    caso("`clicar` aperta o rótulo que existe; o que não existe: NÃO DEU, ensinando o `ver`", tipo == "feito" and tipo2 == "nao-deu" and "ver" in texto2)
    tipo, texto = pedir(p, MacDeMentira(), "ver")
    caso("`ver` escreve a árvore das janelas: papel, rótulo e valor", tipo == "feito" and 'Button "Salvar"' in texto and "= 12" in texto and "na frente sim" in texto)
    tipo, texto = pedir(p, MacDeMentira(aberto=False), "ver")
    caso("`ver` com o app fechado: NÃO DEU, ensinando o `abrir`", tipo == "nao-deu" and "abrir" in texto)
    mac = MacDeMentira()
    primeira, segunda = pedir(p, mac, "foto"), pedir(p, mac, "foto")
    caso("`foto` só da janela do app, em .rascunho/tela-<n>.png, sem repetir o nome", primeira[0] == segunda[0] == "feito"
         and (p / ".rascunho/tela-1.png").is_file() and (p / ".rascunho/tela-2.png").is_file() and pedidos_de(mac, "capturar")[0][0] == 7)
    tipo, texto = pedir(p, MacDeMentira(bloqueada=True), "ver")
    caso("tela do Mac bloqueada: diz numa linha o que o dono faz", tipo == "negado" and "bloqueada" in texto)
    instalado = base / "Applications" / "Gastos.app"
    instalado.mkdir(parents=True)
    com_ambiente = produto(base, "com-ambiente", f"app: Gastos\nambiente: {instalado}\n")
    (com_ambiente / "build" / "Gastos.app").mkdir(parents=True)
    mac = MacDeMentira(aberto=False)
    tipo, texto = pedir(com_ambiente, mac, "abrir")
    caso("`abrir` abre o app instalado no ambiente do dono (`ambiente:`) e o traz para a frente", tipo == "feito"
         and pedidos_de(mac, "open") == [("open", str(instalado))] and pedidos_de(mac, "ativar"))
    da_montagem = produto(base, "da-montagem", "app: Gastos\n")
    (da_montagem / "build" / "Gastos.app").mkdir(parents=True)
    mac = MacDeMentira(aberto=False)
    pedir(da_montagem, mac, "abrir")
    caso("`abrir` sem `ambiente:`: o pacote Gastos.app da montagem", pedidos_de(mac, "open") == [("open", str(da_montagem / "build" / "Gastos.app"))])
    programa = produto(base, "programa", "app: Gastos\n")
    (programa / ".build" / "debug").mkdir(parents=True)
    (programa / ".build" / "debug" / "Gastos").write_text("#!/bin/sh\n")
    (programa / ".build" / "debug" / "Gastos").chmod(0o755)
    mac = MacDeMentira(aberto=False)
    pedir(programa, mac, "abrir")
    caso("`abrir` sem pacote: o programa Gastos que a montagem gerou", pedidos_de(mac, "soltar") == [(str(programa / ".build" / "debug" / "Gastos"),)])
    mac = MacDeMentira(aberto=False)
    pedir(sem_atalho, mac, "abrir")
    caso("`abrir` sem nada na pasta: o app que o Mac conhece pelo nome", pedidos_de(mac, "open") == [("open", "-a", "Gastos")])
    mac = MacDeMentira()
    tipo, texto = pedir(p, mac, "fechar")
    caso("`fechar` fecha o app declarado", tipo == "feito" and "fechei" in texto and pedidos_de(mac, "fechar") == [("Gastos",)])
    # O macOS negando: a mensagem do osascript vira uma linha que diz ao dono o que liberar, e onde.
    rodar_de_verdade = tela.subprocess.run
    respostas = {"automacao": "execution error: Not authorized to send Apple events to System Events. (-1743)",
                 "acessibilidade": "execution error: System Events got an error: osascript is not allowed assistive access. (-1719)"}
    for qual, erro in respostas.items():
        tela.subprocess.run = lambda *a, erro=erro, **k: subprocess.CompletedProcess(a[0], 1, "", erro)
        try:
            tela.Mac().jxa("estado", "Gastos")
            texto = ""
        except tela.Negado as negado:
            texto = str(negado)
        finally:
            tela.subprocess.run = rodar_de_verdade
        caso(f"o macOS nega ({qual}): uma linha com a permissão e onde o dono a libera", "Ajustes do Sistema > Privacidade e Segurança" in texto
             and {"automacao": "Automação", "acessibilidade": "Acessibilidade"}[qual] in texto)
    caso("os modelos fixos não montam código com texto de fora (sem eval nem do shell script)", not any(
        "eval(" in m or "do shell script" in m or "doShellScript" in m for m in tela.MODELOS.values()))
    feito = subprocess.run([sys.executable, "-I", "-B", ".claude/hooks/delta-11/tela-do-app.py"], cwd=p, capture_output=True, text=True)
    caso("o programa, sem ação, sai com 2 e diz RECUSOU", feito.returncode == 2 and "RECUSOU" in feito.stderr)
    return resultados


def ensaio_de_verdade(base: Path) -> tuple[bool | None, str]:
    """Abrir, ver, foto, digitar e fechar a Calculadora. None: pulado (com o motivo)."""
    if subprocess.run(["pgrep", "-x", "Calculator"], capture_output=True).returncode == 0:
        return None, "a Calculadora já está aberta (a do dono não se fecha)"
    p = produto(base, "ensaio", "app: Calculator\n")
    passos = []

    def rodar(*argumentos: str) -> subprocess.CompletedProcess:
        feito = subprocess.run([sys.executable, "-I", "-B", ".claude/hooks/delta-11/tela-do-app.py", *argumentos], cwd=p, capture_output=True, text=True, timeout=180)
        passos.append(f"{' '.join(argumentos)} -> {feito.returncode}: {(feito.stdout + feito.stderr).strip()[:160]}")
        return feito
    try:
        aberto = rodar("abrir")
        if aberto.returncode == 3:
            return None, aberto.stderr.strip()
        visto, foto, digitado = rodar("ver"), rodar("foto"), rodar("digitar", "12")
        if 3 in (visto.returncode, foto.returncode, digitado.returncode):
            return None, " / ".join(passos)
        certo = aberto.returncode == 0 and visto.returncode == 0 and "Window" in visto.stdout and foto.returncode == 0 \
            and any(a.stat().st_size > 1000 for a in (p / ".rascunho").glob("tela-*.png")) and digitado.returncode == 0
    finally:
        fechado = rodar("fechar")
    return certo and fechado.returncode == 0 and subprocess.run(["pgrep", "-x", "Calculator"], capture_output=True).returncode != 0, " / ".join(passos)


def main() -> int:
    falhas = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp).resolve()
        resultados = casos_simulados(base)
        for nome, certo in resultados:
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}")
            if not certo:
                falhas.append(nome)
        total = len(resultados)
        if "--sem-janela" in sys.argv:
            print("  (sem o ensaio de verdade: --sem-janela)")
        elif sys.platform != "darwin":
            print("  pulado — o ensaio de verdade: só no Mac")
        else:
            certo, como = ensaio_de_verdade(base)
            if certo is None:
                print(f"  pulado — o ensaio de verdade com a Calculadora: {como}")
            else:
                total += 1
                print(f"  {'ok' if certo else 'ERRADO'} — ensaio de verdade: abrir, ver, foto, digitar e fechar a Calculadora" + ("" if certo else f" ({como})"))
                if not certo:
                    falhas.append("ensaio de verdade")
    if falhas:
        print(f"PULSO DA TELA DO APP FALHOU — {len(falhas)} de {total} casos: " + "; ".join(falhas))
        return 1
    print(f"PULSO DA TELA DO APP OK — {total} casos: as recusas recusam e o Mac só recebe modelos fixos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
