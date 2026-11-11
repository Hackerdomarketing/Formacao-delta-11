#!/usr/bin/env python3
"""Tela do app do Delta-11 v7: ver e usar a janela de um app de Mac (para quem o mapa deixa, em `usam_a_tela`: hoje, o Revisor).

Dentro da caixa de areia do Claude Code, e da caixa do produto, o macOS não deixa um programa ver nem clicar a janela de
outro (o System Events dá erro de privilégio). Por isso este programa roda fora delas (chamado com o texto exato da
configuração) e age só sobre o app declarado em `esteira-comandos.txt` da pasta em que roda (`app: <nome do processo ou
do pacote .app>`; o atalho global dele em `atalho: <combinação>`). Fala com o Mac só por modelos fixos de JavaScript para
Automação: nenhum texto de quem chama vira código (vai como argumento, e é conferido antes). Só digita com o app na frente,
conferindo a cada letra, para nunca digitar em outro programa.

Uso, sozinho na linha, na raiz do produto (ou na da cópia da candidata):
    python3 -I -B .claude/hooks/delta-11/tela-do-app.py <ação> [argumento]
Ações:
    abrir                 abre o app (o de `ambiente:`, senão o da montagem, senão o que o Mac conhece) e o traz para a frente
    ver                   escreve a árvore das janelas do app, em texto: papel, rótulo e valor de cada parte
    foto                  captura só a janela do app em `.rascunho/tela-<n>.png` (abra-a com a ferramenta de ler)
    clicar "<rótulo>"     aperta a parte da janela com esse rótulo (veja os rótulos com `ver`)
    digitar "<texto>"     digita no app (só com ele na frente)
    tecla "<combinação>"  aperta uma tecla, com ou sem modificadores (`enter`, `esc`, `cmd+s`, `cmd+shift+n`), no app da frente
    atalho                manda a combinação global declarada em `atalho:` (prova o atalho global do app)
    fechar                fecha o app
Sai com 0 (feito), 1 (não deu: o app não abriu, o rótulo não existe), 2 (pedido recusado) ou 3 (o macOS negou uma permissão).
A tela, o teclado e os programas são do dono: nada roda (nem `fechar`, que fecharia o app com o que ele digitava) sem a
hora que ele liberou, que o ATLAS escreve em `.delta-11/tela-liberada.md` (`até: <AAAA-MM-DD HH:MM>`, no máximo
`tela_liberada_max` adiante); passada a hora, recusa.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent.parent
CHAMADA = "python3 -I -B .claude/hooks/delta-11/tela-do-app.py"
COMANDOS = "esteira-comandos.txt"
ACOES = {"abrir": 0, "ver": 0, "foto": 0, "clicar": 1, "digitar": 1, "tecla": 1, "atalho": 0, "fechar": 0}
TEXTO_MAX = 1000  # letras de um `digitar` (cada uma conferida com o app na frente)
ROTULO_MAX = 200
VER_MAX = 400  # partes da janela que `ver` escreve
NAO_ENTRA_NA_BUSCA = {".git", ".delta-11", ".claude", "node_modules", ".rascunho", "checkouts", "repositories", "artifacts", "Pods"}
MODIFICADORES = {"cmd": "command down", "command": "command down", "comando": "command down", "⌘": "command down",
                 "shift": "shift down", "⇧": "shift down",
                 "option": "option down", "opt": "option down", "alt": "option down", "opção": "option down", "⌥": "option down",
                 "ctrl": "control down", "control": "control down", "controle": "control down", "⌃": "control down"}
TECLAS = {"enter": 36, "return": 36, "retorno": 36, "tab": 48, "space": 49, "espaço": 49, "delete": 51, "backspace": 51, "apagar": 51,
          "esc": 53, "escape": 53, "forwarddelete": 117, "home": 115, "end": 119, "pageup": 116, "pagedown": 121,
          "left": 123, "esquerda": 123, "right": 124, "direita": 124, "down": 125, "baixo": 125, "up": 126, "cima": 126,
          **{f"f{n}": c for n, c in zip(range(1, 13), (122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111))}}
NOMES_DAS_TECLAS = ", ".join(sorted(k for k in TECLAS if k.isascii() and not re.fullmatch(r"f\d+", k))) + ", f1 a f12"
AJUSTES = "Ajustes do Sistema > Privacidade e Segurança"
QUEM_LIGAR = "ligando o programa em que o Claude Code roda (o Visual Studio Code ou o Terminal)"
NEGADO = {
    "acessibilidade": f"o macOS negou: falta a permissão de Acessibilidade. O dono libera em {AJUSTES} > Acessibilidade, {QUEM_LIGAR}.",
    "automacao": f"o macOS negou: falta a permissão de Automação. O dono libera em {AJUSTES} > Automação, {QUEM_LIGAR} e, embaixo dele, o System Events.",
    "gravacao": f"o macOS negou a foto: falta a permissão de Gravação de Tela. O dono libera em {AJUSTES} > Gravação de Tela e Áudio do Sistema, {QUEM_LIGAR}.",
    "esperando": f"o macOS não respondeu a tempo: talvez espere o dono responder a um pedido de permissão na tela ({AJUSTES}).",
    "bloqueada": "a tela do Mac está bloqueada: o macOS não mostra janela nem traz app para a frente. O dono desbloqueia o Mac (e o deixa assim enquanto o time testa).",
}

# Os modelos fixos (JavaScript para Automação). Os valores chegam em argv, nunca no texto do modelo.
COMUM = """
function processo(se, nome) {
  let achados = se.processes.whose({name: nome});
  if (achados.length === 0) achados = se.processes.whose({displayedName: nome});
  return achados.length === 0 ? null : achados[0];
}
function daFrente(se) {
  const f = se.processes.whose({frontmost: true});
  return f.length ? f[0].name() : "";
}
function texto(f) { try { const v = f(); return (v === null || v === undefined) ? "" : String(v); } catch (e) { return ""; } }
"""
MODELOS = {
    "estado": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const p = processo(se, argv[0]);
  if (!p) return JSON.stringify({aberto: false, frente: false, da_frente: daFrente(se), pid: 0, janelas: 0});
  return JSON.stringify({aberto: true, frente: p.frontmost(), da_frente: daFrente(se), pid: p.unixId(), janelas: p.windows().length});
}""",
    "ativar": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const p = processo(se, argv[0]);
  if (!p) return "FECHADO";
  p.frontmost = true;
  return "OK";
}""",
    "ver": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const p = processo(se, argv[0]);
  const maximo = parseInt(argv[1], 10);
  if (!p) return "FECHADO";
  const linhas = [];
  function andar(el, nivel) {
    if (linhas.length >= maximo || nivel > 30) return;
    const papel = texto(() => el.role()).replace(/^AX/, "");
    const rotulo = texto(() => el.title()) || texto(() => el.description()) || texto(() => el.name());
    let valor = texto(() => el.value()).replace(/\\s+/g, " ");
    if (valor.length > 200) valor = valor.slice(0, 200) + "...";
    linhas.push("  ".repeat(nivel) + papel + (rotulo ? ' "' + rotulo + '"' : "") + (valor ? " = " + valor : ""));
    let filhos = [];
    try { filhos = el.uiElements(); } catch (e) {}
    for (const filho of filhos) andar(filho, nivel + 1);
  }
  for (const janela of p.windows()) andar(janela, 0);
  if (linhas.length >= maximo) linhas.push("(parei em " + maximo + " partes)");
  return linhas.join("\\n");
}""",
    "bloqueada": """
ObjC.import("CoreGraphics");
function run(argv) {
  const sessao = ObjC.deepUnwrap(ObjC.castRefToObject($.CGSessionCopyCurrentDictionary())) || {};
  return sessao.CGSSessionScreenIsLocked ? "SIM" : "NAO";
}""",
    "janelas": """
ObjC.import("CoreGraphics");
function run(argv) {
  const pid = parseInt(argv[0], 10);
  const lista = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo($.kCGWindowListOptionOnScreenOnly | $.kCGWindowListExcludeDesktopElements, $.kCGNullWindowID)));
  return JSON.stringify(lista.filter(j => j.kCGWindowOwnerPID === pid && j.kCGWindowLayer === 0).map(j => j.kCGWindowNumber));
}""",
    "clicar": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const p = processo(se, argv[0]);
  const procurado = argv[1];
  if (!p) return "FECHADO";
  const fila = p.windows().slice();
  let vistos = 0;
  while (fila.length && vistos < 5000) {
    const el = fila.shift();
    vistos += 1;
    const rotulos = [texto(() => el.title()), texto(() => el.description()), texto(() => el.name())];
    if (rotulos.indexOf(procurado) >= 0) {
      try { el.click(); } catch (e) { el.actions.byName("AXPress").perform(); }
      return "CLICOU " + texto(() => el.role()).replace(/^AX/, "");
    }
    try { for (const filho of el.uiElements()) fila.push(filho); } catch (e) {}
  }
  return "NAO ACHEI";
}""",
    "digitar": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const nome = argv[0];
  for (const letra of Array.from(argv[1])) {
    const p = processo(se, nome);
    if (!p || !p.frontmost()) return "OUTRO NA FRENTE: " + daFrente(se);
    se.keystroke(letra);
  }
  return "DIGITOU";
}""",
    "tecla": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const usando = argv[3] ? argv[3].split(",") : [];
  if (argv[0]) {
    const p = processo(se, argv[0]);
    if (!p || !p.frontmost()) return "OUTRO NA FRENTE: " + daFrente(se);
  }
  if (argv[1] === "codigo") se.keyCode(parseInt(argv[2], 10), {using: usando});
  else se.keystroke(argv[2], {using: usando});
  return "APERTOU";
}""",
    "fechar": COMUM + """
function run(argv) {
  const se = Application("System Events");
  const p = processo(se, argv[0]);
  if (!p) return "FECHADO";
  const pid = p.unixId();
  const id = texto(() => p.bundleIdentifier());
  if (id) { try { Application(id).quit(); return "PEDIU " + pid; } catch (e) {} }
  return "PID " + pid;
}""",
}


class Recusa(Exception):
    """O pedido não vale (sai com 2)."""


class NaoDeu(Exception):
    """O pedido vale, mas não deu (sai com 1)."""


class Negado(Exception):
    """O macOS negou uma permissão (sai com 3)."""


class Mac:
    """O que o programa pede ao Mac. O pulso troca por um de mentira, para provar as recusas sem janela de verdade."""

    def preso(self) -> bool:
        return bool(shutil.which("sandbox-exec")) and subprocess.run(["sandbox-exec", "-p", "(version 1)(allow default)", "/usr/bin/true"],
                                                                     capture_output=True).returncode != 0

    def jxa(self, modelo: str, *valores: str) -> str:
        try:
            feito = subprocess.run(["osascript", "-l", "JavaScript", "-e", MODELOS[modelo], "--", *valores], capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired:
            raise Negado(NEGADO["esperando"])
        if feito.returncode != 0:
            erro = feito.stderr.strip()
            raise Negado(NEGADO[permissao_negada(erro)]) if permissao_negada(erro) else NaoDeu(f"o Mac respondeu com erro: {erro[-300:]}")
        return feito.stdout.strip()

    def abrir(self, comando: list[str]) -> tuple[int, str]:
        feito = subprocess.run(comando, capture_output=True, text=True, timeout=60)
        return feito.returncode, (feito.stdout + feito.stderr).strip()

    def soltar(self, programa: Path, relato: Path) -> None:
        relato.parent.mkdir(exist_ok=True)
        with relato.open("a", encoding="utf-8") as saida:
            subprocess.Popen([str(programa)], cwd=str(RAIZ), stdout=saida, stderr=saida, stdin=subprocess.DEVNULL, start_new_session=True)

    def capturar(self, janela: int, arquivo: Path) -> tuple[int, str]:
        feito = subprocess.run(["screencapture", "-x", "-o", "-l", str(janela), str(arquivo)], capture_output=True, text=True, timeout=60)
        return feito.returncode, (feito.stdout + feito.stderr).strip()

    def matar(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    def esperar(self, segundos: float) -> None:
        time.sleep(segundos)


def permissao_negada(erro: str) -> str:
    """Qual permissão o macOS negou, pela mensagem do osascript (vazio: não foi permissão)."""
    baixo = erro.lower()
    if "-1743" in baixo or "not authorized to send apple events" in baixo or "não está autorizad" in baixo:
        return "automacao"
    if "-1719" in baixo or "-25211" in baixo or "-10004" in baixo or "assistive" in baixo or "acessibilidade" in baixo or "privilege violation" in baixo:
        return "acessibilidade"
    if "-1712" in baixo:
        return "esperando"
    return ""


def sem_controle(texto: str, o_que: str, maximo: int) -> str:
    if not texto or len(texto) > maximo or any(ord(c) < 32 or ord(c) == 127 for c in texto):
        raise Recusa(f"{o_que} vazio, maior que {maximo} letras, ou com quebra de linha ou caractere de controle (para Enter, use `tecla \"enter\"`).")
    return texto


def declarado(raiz: Path) -> dict[str, str]:
    """O app e o atalho que esteira-comandos.txt da pasta declara."""
    arquivo = raiz / COMANDOS
    achados: dict[str, str] = {}
    if arquivo.is_file():
        for linha in arquivo.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*(app|atalho)\s*:(.*)$", linha)
            if m and m.group(1) not in achados:
                achados[m.group(1)] = m.group(2).strip().strip("'\"")
    nome = achados.get("app", "")
    if not nome:
        raise Recusa(f"{COMANDOS} não declara o app: escreva uma linha `app: <nome do processo ou do pacote .app>` (quem faz os comandos do produto a escreve).")
    if len(nome) > 80 or re.search(r"[/:\\\"`$\x00-\x1f\x7f]", nome):
        raise Recusa(f"`app: {nome}` fora do formato: só o nome do app (sem caminho, aspas, barra ou dois-pontos).")
    achados["app"] = nome[:-4] if nome.endswith(".app") else nome
    return achados


def combinacao(texto: str, global_: bool = False) -> tuple[str, str, list[str]]:
    """`cmd+shift+n` vira ("letra", "n", ["command down", "shift down"]); `enter` vira ("codigo", "36", [])."""
    sem_controle(texto, "a combinação", 40)
    partes = [p.strip().lower() for p in texto.split("+")]
    if texto.endswith("+") and len(partes) > 1:  # `cmd++`: a tecla é o +
        partes = partes[:-2] + ["+"]
    *mods, tecla = partes
    if any(m not in MODIFICADORES for m in mods) or not tecla:
        raise Recusa(f"combinação fora do formato ('{texto}'): modificadores ({', '.join(sorted({'cmd', 'shift', 'option', 'ctrl'}))}) e uma tecla, "
                     f"com +, como `cmd+shift+n`, ou uma tecla com nome ({NOMES_DAS_TECLAS}).")
    usando = sorted({MODIFICADORES[m] for m in mods})
    if global_ and not set(usando) & {"command down", "option down", "control down"}:
        raise Recusa(f"o atalho global ('{texto}') precisa de cmd, option ou ctrl: sem eles, a tecla iria para o programa da frente.")
    if tecla in TECLAS:
        return "codigo", str(TECLAS[tecla]), usando
    if len(tecla) != 1:
        raise Recusa(f"tecla desconhecida '{tecla}': uma letra, um número ou um sinal, ou um nome ({NOMES_DAS_TECLAS}).")
    return "letra", tecla, usando


def estado(mac: Mac, nome: str) -> dict:
    return json.loads(mac.jxa("estado", nome))


def pela_frente(mac: Mac, nome: str) -> None:
    """Traz o app para a frente e confere: com outro programa na frente, nada é digitado."""
    agora = estado(mac, nome)
    if not agora["aberto"]:
        raise NaoDeu(f"o app {nome} está fechado: rode `{CHAMADA} abrir` antes.")
    if not agora["frente"]:
        mac.jxa("ativar", nome)
        mac.esperar(0.5)
        agora = estado(mac, nome)
    if not agora["frente"]:
        raise Recusa(f"o app {nome} não está na frente (na frente: {agora['da_frente'] or 'nenhum'}): não digito em outro programa. "
                     f"Peça ao dono para não usar o Mac enquanto você testa, e tente de novo.")


def achar_na_montagem(raiz: Path, nome: str) -> tuple[Path | None, Path | None]:
    """O pacote `<nome>.app` mais novo da pasta e, sem ele, o programa `<nome>` mais novo (o executável que a montagem gera)."""
    pacotes, programas = [], []
    for pasta, subpastas, arquivos in os.walk(raiz):
        atual = Path(pasta)
        if len(atual.relative_to(raiz).parts) > 7:
            subpastas[:] = []
            continue
        for sub in list(subpastas):
            if sub in NAO_ENTRA_NA_BUSCA or sub.endswith(".app") or sub.endswith(".dSYM"):
                subpastas.remove(sub)
            if sub == f"{nome}.app":
                pacotes.append(atual / sub)
        programas += [atual / a for a in arquivos if a == nome and os.access(atual / a, os.X_OK) and (atual / a).is_file()]
    mais_novo = lambda lista: max(lista, key=lambda c: c.stat().st_mtime) if lista else None
    return mais_novo(pacotes), mais_novo(programas)


def abrir(mac: Mac, raiz: Path, nome: str) -> str:
    if estado(mac, nome)["aberto"]:
        mac.jxa("ativar", nome)
        return f"o app {nome} já estava aberto; trouxe-o para a frente."
    instalados = []
    arquivo = raiz / COMANDOS
    for linha in arquivo.read_text(encoding="utf-8", errors="replace").splitlines() if arquivo.is_file() else []:
        m = re.match(r"\s*ambiente\s*:(.*)$", linha)
        caminho = Path(os.path.expanduser(m.group(1).strip().strip("'\""))) if m else None
        if caminho and caminho.suffix == ".app" and caminho.is_dir() and caminho.stem == nome:
            instalados.append(caminho)
    pacote, programa = achar_na_montagem(raiz, nome)
    if instalados:
        origem, (codigo, saida) = f"o instalado, {instalados[0]}", mac.abrir(["open", str(instalados[0])])
    elif pacote:
        origem, (codigo, saida) = f"o da montagem, {pacote.relative_to(raiz)}", mac.abrir(["open", str(pacote)])
    elif programa:
        relato = raiz / ".rascunho" / "tela-do-app.log"
        mac.soltar(programa, relato)
        origem, codigo, saida = f"o programa da montagem, {programa.relative_to(raiz)} (a saída dele vai para .rascunho/tela-do-app.log)", 0, ""
    else:
        origem, (codigo, saida) = "o que o Mac conhece por esse nome", mac.abrir(["open", "-a", nome])
    if codigo != 0:
        raise NaoDeu(f"não achei o app {nome}: nem em `ambiente:`, nem na montagem (`{nome}.app` ou o programa `{nome}`), nem no Mac ({saida[-200:]}).")
    for _ in range(40):
        agora = estado(mac, nome)
        if agora["aberto"] and (agora["janelas"] or _ >= 30):  # a janela aparece um pouco depois do processo
            mac.jxa("ativar", nome)
            mac.esperar(0.5)
            agora = estado(mac, nome)
            return f"abri {origem}: janelas {agora['janelas']}, na frente {'sim' if agora['frente'] else 'não (na frente: ' + agora['da_frente'] + ')'}."
        mac.esperar(0.5)
    raise NaoDeu(f"abri {origem}, mas o processo {nome} não apareceu em 20 segundos (o nome em `app:` é o do processo? Veja no Monitor de Atividade).")


def foto(mac: Mac, raiz: Path, nome: str) -> str:
    agora = estado(mac, nome)
    if not agora["aberto"]:
        raise NaoDeu(f"o app {nome} está fechado: rode `{CHAMADA} abrir` antes.")
    janelas = json.loads(mac.jxa("janelas", str(agora["pid"])) or "[]")
    if not janelas:
        raise NaoDeu(f"o app {nome} não tem janela na tela (minimizada, noutra mesa ou sem janela).")
    pasta = raiz / ".rascunho"
    pasta.mkdir(exist_ok=True)
    numeros = [int(m.group(1)) for a in pasta.glob("tela-*.png") if (m := re.fullmatch(r"tela-(\d+)\.png", a.name))]
    arquivo = pasta / f"tela-{max(numeros, default=0) + 1}.png"
    codigo, saida = mac.capturar(int(janelas[0]), arquivo)
    if codigo != 0 or not arquivo.is_file() or arquivo.stat().st_size == 0:
        raise Negado(NEGADO["gravacao"] + (f" ({saida[-160:]})" if saida else ""))
    return f"foto da janela de {nome}: {arquivo.relative_to(raiz)} (abra-a com a ferramenta de ler)."


def fechar(mac: Mac, nome: str) -> str:
    resposta = mac.jxa("fechar", nome)
    if resposta == "FECHADO":
        return f"o app {nome} já estava fechado."
    pid = int(resposta.split()[-1])
    for tentativa in range(20):
        if not estado(mac, nome)["aberto"]:
            return f"fechei o app {nome}."
        if tentativa == 10 or resposta.startswith("PID"):
            mac.matar(pid)
        mac.esperar(0.5)
    raise NaoDeu(f"pedi para o app {nome} fechar e ele seguiu aberto (talvez espere uma resposta na janela: veja com `ver`).")


def liberada_ate(raiz: Path) -> str:
    """A hora até a qual o dono liberou a tela (o arquivo é da pasta principal, também numa cópia de candidata); sem ela, recusa."""
    principal = raiz.parent.parent.parent if raiz.parent.name == "worktrees" and raiz.parent.parent.name == ".claude" else raiz
    arquivo = principal / ".delta-11" / "tela-liberada.md"
    texto = arquivo.read_text(encoding="utf-8", errors="replace") if arquivo.is_file() else ""
    achado = re.search(r"^\W*at[ée]\s*:\s*(\d{4}-\d{2}-\d{2})[ t]+(\d{1,2}:\d{2})", texto, re.IGNORECASE | re.MULTILINE)
    pedir = ("peça na sua linha `PARA CRONOS:` a tela do Mac, com o tempo do seu passo (o CRONOS faz a chamada 2 ao dono; com o sim, o "
             "ATLAS escreve `.delta-11/tela-liberada.md` com `até: <AAAA-MM-DD HH:MM>`)")
    if not achado:
        raise Recusa("a tela, o teclado e os programas do Mac são do dono: só se usam numa hora que ele libera. " + pedir + ".")
    fim = time.mktime(time.strptime(f"{achado.group(1)} {achado.group(2)}", "%Y-%m-%d %H:%M"))
    teto = float(json.loads((AQUI / "lugares.json").read_text(encoding="utf-8")).get("tela_liberada_max_horas", 4)) if (AQUI / "lugares.json").is_file() else 4.0
    if fim - arquivo.stat().st_mtime > teto * 3600 + 60:
        raise Recusa(f"a hora liberada ({achado.group(1)} {achado.group(2)}) passa de `tela_liberada_max` ({teto:g} h) depois de escrita: " + pedir + " de novo.")
    if time.time() >= fim:
        raise Recusa(f"a hora que o dono liberou para a tela acabou ({achado.group(1)} {achado.group(2)}): " + pedir + " de novo.")
    return f"{achado.group(1)} {achado.group(2)}"


def executar(argumentos: list[str], mac: Mac, raiz: Path = RAIZ, cwd: Path | None = None) -> str:
    """Confere o pedido e faz a ação; devolve o que dizer na tela. Erros: Recusa, NaoDeu, Negado."""
    if not argumentos or argumentos[0] not in ACOES:
        raise Recusa(f"diga a ação: {', '.join(ACOES)} (uso: `{CHAMADA} <ação> [argumento]`).")
    acao, resto = argumentos[0], argumentos[1:]
    if len(resto) != ACOES[acao]:
        raise Recusa(f"`{acao}` leva {'um argumento, entre aspas' if ACOES[acao] else 'nenhum argumento'}; a tela age só sobre o app declarado em "
                     f"`app:` de {COMANDOS}, e o nome dele nunca vem na linha.")
    if Path(cwd or os.getcwd()).resolve() != raiz.resolve():
        raise Recusa(f"rode na raiz da pasta do produto (ou na da cópia da candidata), exatamente `{CHAMADA} {acao}`.")
    if mac.preso():
        raise Recusa(f"rodou dentro de uma caixa de areia, onde o macOS não deixa ver nem clicar outra janela. Rode sozinha na linha, exatamente "
                     f"`{CHAMADA} <ação>` (sem `&&`, `;`, `|`, `cd`, redirecionamento nem `$(...)`, e nunca pela caixa do produto).")
    do_app = declarado(raiz)
    nome = do_app["app"]
    # Tudo o que o pedido traz é conferido antes de qualquer pergunta ao Mac.
    texto = sem_controle(resto[0], "o texto", TEXTO_MAX) if acao == "digitar" else ""
    rotulo = sem_controle(resto[0], "o rótulo", ROTULO_MAX) if acao == "clicar" else ""
    tecla_pedida = combinacao(resto[0]) if acao == "tecla" else None
    if acao == "atalho" and not do_app.get("atalho"):
        raise Recusa(f"{COMANDOS} não declara o atalho global: escreva uma linha `atalho: <combinação>` (como `ctrl+option+g`).")
    atalho = combinacao(do_app["atalho"], global_=True) if acao == "atalho" else None
    liberada_ate(raiz)
    if acao != "fechar" and mac.jxa("bloqueada") == "SIM":
        raise Negado(NEGADO["bloqueada"])
    if acao == "digitar":
        pela_frente(mac, nome)
        resposta = mac.jxa("digitar", nome, texto)
        if resposta != "DIGITOU":
            raise NaoDeu(f"parei de digitar: {resposta.lower()} (o que veio antes foi digitado no app).")
        return f"digitei {len(texto)} letra(s) no app {nome}."
    if acao == "tecla":
        tipo, tecla, usando = tecla_pedida
        pela_frente(mac, nome)
        resposta = mac.jxa("tecla", nome, tipo, tecla, ",".join(usando))
        if resposta != "APERTOU":
            raise NaoDeu(f"não apertei: {resposta.lower()}.")
        return f"apertei {resto[0]} no app {nome}."
    if acao == "atalho":
        tipo, tecla, usando = atalho
        mac.jxa("tecla", "", tipo, tecla, ",".join(usando))
        mac.esperar(1)
        agora = estado(mac, nome)
        return (f"mandei o atalho global {do_app['atalho']}; agora: app {nome} {'aberto' if agora['aberto'] else 'fechado'}, "
                f"janelas {agora['janelas']}, na frente {agora['da_frente'] or 'nenhum'}.")
    if acao == "clicar":
        resposta = mac.jxa("clicar", nome, rotulo)
        if resposta == "FECHADO":
            raise NaoDeu(f"o app {nome} está fechado: rode `{CHAMADA} abrir` antes.")
        if not resposta.startswith("CLICOU"):
            raise NaoDeu(f"não achei nada com o rótulo \"{rotulo}\" nas janelas do app {nome} (veja os rótulos com `{CHAMADA} ver`).")
        return f"cliquei em \"{rotulo}\" ({resposta.split(' ', 1)[1]}) no app {nome}."
    if acao == "ver":
        agora = estado(mac, nome)
        if not agora["aberto"]:
            raise NaoDeu(f"o app {nome} está fechado: rode `{CHAMADA} abrir` antes.")
        arvore = mac.jxa("ver", nome, str(VER_MAX))
        cabeca = f"App {nome}: janelas {agora['janelas']}, na frente {'sim' if agora['frente'] else 'não (na frente: ' + agora['da_frente'] + ')'}."
        return cabeca + ("\n" + arvore if arvore and arvore != "FECHADO" else "\n(nenhuma janela)")
    if acao == "foto":
        return foto(mac, raiz, nome)
    if acao == "abrir":
        return abrir(mac, raiz, nome)
    return fechar(mac, nome)


def main() -> int:
    try:
        print(executar(sys.argv[1:], Mac()))
        return 0
    except Recusa as recusa:
        print(f"tela do app: RECUSOU: {recusa}", file=sys.stderr)
        return 2
    except NaoDeu as erro:
        print(f"tela do app: NÃO DEU: {erro}", file=sys.stderr)
        return 1
    except Negado as negado:
        print(f"tela do app: {negado}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
