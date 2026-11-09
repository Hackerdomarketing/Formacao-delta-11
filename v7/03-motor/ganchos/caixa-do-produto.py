#!/usr/bin/env python3
"""Caixa do produto do Delta-11 v7: o jeito de rodar o produto (testes, navegador de teste, servidor, banco, as
ferramentas de linha de comando dos serviços) para todos os agentes e para a esteira.

A caixa de areia do Claude Code não deixa o navegador de teste abrir, nem o banco e as ferramentas em Go conectarem
(provado no ensaio de 2026-10-17). Por isso este programa roda fora dela (chamado com o texto exato da configuração)
e prende o comando com a caixa do próprio Mac: grava só na pasta em que roda, no temporário, nos caches das
ferramentas e, só com `--com-ambiente` (o publicar da esteira; a trava não deixa um agente pedir), no ambiente do dono
que `esteira-comandos.txt` dessa pasta declara (`ambiente: <caminho>`, só dentro de AMBIENTE_DO_DONO: o app em
~/Applications, os dados dele em ~/Library; sem a opção, o `ambiente:` é conferido, mas nada grava nele), e nunca em .git/, .delta-11/, .claude/, no
programa da esteira nem nos arquivos de controle da raiz; não
lê o cofre, o teste guardado, o leitor do teste, as conversas gravadas nem as chaves pessoais do computador. A rede é
livre (o banco e o navegador precisam): por isso o que é segredo fica onde ele não lê.

Uso, sozinho na linha, na pasta em que o agente trabalha (a raiz do produto, ou a da cópia da candidata):
    python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py <comando> [argumentos...]
Para rodar noutra cópia (a de uma candidata, da raiz; a temporária da esteira), o comando roda dentro dela:
    python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py --raiz <cópia> <comando> [argumentos...]
Quem tem o terminal vigiado (Destruidor, Revisor, Selador) põe `olhar` antes de tudo: a pasta fica só para ler (nem
mudar, nem apagar, nem renomear); grava só no que o git ignora (o que a montagem gera, as dependências, os resultados de
teste, o rascunho `.rascunho/`), nunca no `.env`, no temporário e nos caches; do ambiente do dono, só nos dados do app
(não troca o app instalado nem o que liga com o Mac).
Chamada de dentro da própria caixa (a esteira rodando um pulso que chama a caixa), roda direto: a caixa de fora já prende.
A cópia de ataque (o Destruidor ataca a esteira de ponta a ponta): `copia-de-ataque <nome>` monta no temporário, em
`delta11-ataque-<nome>/`, o último commit como um repositório novo, sem o que conta como foi feito (o quadro, o registro,
as lições, os estados, o teste guardado, o leitor, o cofre e os relatos), com uma camada aberta vazia (`quadro/ataque/`).
Numa cópia de ataque, a caixa deixa gravar a cópia inteira (o .git e o .delta-11 dela também), mesmo no modo de olhar:
ela é descartável, e a pasta principal continua proibida; o ambiente do dono (o app instalado, os dados dele, o que liga
com o Mac) fica fechado, e a esteira dali nunca publica (a cópia nasce com `.delta-11/esteira/ensaio`). O relato da
esteira na cópia se lê com `relato-da-copia <nome>` (só o da cópia, nunca o do produto).
"""
from __future__ import annotations

import importlib.util
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DENTRO = "DELTA11_DENTRO_DA_CAIXA_DO_PRODUTO"
COMANDOS = "esteira-comandos.txt"
# O ambiente do dono (um app de Mac instalado e os dados dele): (prefixo, só um arquivo .plist direto nele, vale no modo de olhar).
AMBIENTE_DO_DONO = (
    ("Applications", False, False),
    ("Library/Application Support", False, True),
    ("Library/Caches", False, True),
    ("Library/Logs", False, True),
    ("Library/Preferences", True, True),
    ("Library/LaunchAgents", True, False),
)
ENSINA_O_AMBIENTE = ("vale, uma linha por lugar, um caminho dentro (nunca a pasta inteira) de ~/Applications/ (o app: <App>.app), "
                     "~/Library/Application Support/, Caches/ ou Logs/ (<id>), ou ~/Library/Preferences/ ou LaunchAgents/ (<id>.plist, "
                     "para ligar com o Mac)")


def sair(motivo: str) -> None:
    print(f"caixa do produto: {motivo}", file=sys.stderr)
    sys.exit(2)


def pasta_principal(raiz_do_programa: Path) -> tuple[Path, Path | None]:
    """A pasta principal do produto e o .git dela (numa cópia de candidata, o .git é o da pasta principal)."""
    comum = subprocess.run(["git", "-C", str(raiz_do_programa), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                           capture_output=True, text=True, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
    if comum.returncode != 0 or not comum.stdout.strip():
        return raiz_do_programa, None
    git = Path(comum.stdout.strip()).resolve()
    return (git.parent if git.name == ".git" else raiz_do_programa), git


def temporarios() -> list[Path]:
    pastas = {Path(tempfile.gettempdir()).resolve(), Path("/private/tmp"), Path("/private/var/folders")}
    return sorted(p for p in pastas if p.exists())


def texto(p: Path | str) -> str:
    """O caminho entre aspas, como ele é (acentos inclusive): a caixa do Mac não entende o \\u00e7 do json."""
    return '"' + str(p).replace("\\", "\\\\").replace('"', '\\"') + '"'


def em_regex(caminho: Path | str) -> str:
    """O caminho como texto literal numa expressão da caixa do Mac."""
    return re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", str(caminho))


def ignorados(raiz: Path) -> tuple[list[str], list[str]]:
    """Onde o modo de olhar grava: o que as linhas simples do .gitignore nomeiam (já existindo ou não) e o arquivo
    temporário que a configuração da montagem cria ao lado dela. Devolve também o que volta a ser proibido dentro disso:
    as linhas com `!`, os .env e os arquivos que estão no git."""
    proibidos = (".env", ".git", ".delta-11", ".claude")
    livres, de_volta = [f"^{em_regex(raiz)}/(.*/)?[^/]*\\.timestamp-[^/]*\\.mjs$"], [f"^{em_regex(raiz)}/(.*/)?\\.env[^/]*$"]
    sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    listados = subprocess.run(["git", "-C", str(raiz), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                              capture_output=True, text=True, env=sem_git).stdout.split("\0")
    arquivos_de_ignorar = sorted({raiz / ".gitignore", *(raiz / a for a in listados if a == ".gitignore" or a.endswith("/.gitignore"))})
    for arquivo, linha in ((f, l) for f in arquivos_de_ignorar if f.is_file() for l in f.read_text(encoding="utf-8").splitlines()):
        base = arquivo.parent  # o .gitignore de uma subpasta vale a partir dela
        molde = linha.strip()
        negado = molde.startswith("!")
        molde = molde.lstrip("!")
        partes = [x.lstrip("*") for x in molde.strip("/").split("/")]
        if not molde or molde.startswith("#") or "[" in molde or (not negado and any(x.startswith(proibidos) for x in partes)):
            continue
        if molde.startswith("**/"):
            molde = molde[3:]  # "**/x" vale também na raiz
        ancorado = molde.startswith("/") or "/" in molde.strip("/")
        corpo = em_regex(molde.strip("/")).replace("\\*\\*", ".*").replace("\\*", "[^/]*").replace("\\?", "[^/]")
        (de_volta if negado else livres).append(f"^{em_regex(base)}/{'' if ancorado else '(.*/)?'}{corpo}(/.*)?$")
    do_git = subprocess.run(["git", "-C", str(raiz), "ls-files", "-z"], capture_output=True, text=True, env=sem_git).stdout.split("\0")
    ja_no_git = [str(raiz / a) for a in do_git if a and any(re.search(e, str(raiz / a)) for e in livres)]
    return livres, de_volta + [f"^{em_regex(a)}$" for a in ja_no_git]


def ambiente_do_dono(raiz: Path, olhar: bool, criar: bool = True) -> list[Path]:
    """Os lugares do ambiente do dono que esteira-comandos.txt da pasta declara (`ambiente: <caminho>`). Um caminho fora de
    AMBIENTE_DO_DONO recusa a caixa inteira, ensinando. No modo de olhar, só os dados do app."""
    arquivo = raiz / COMANDOS
    if not arquivo.is_file():
        return []
    casa = Path.home()
    achados = []
    for linha in arquivo.read_text(encoding="utf-8", errors="replace").splitlines():
        declarado = re.match(r"\s*ambiente\s*:(.*)$", linha)
        if not declarado:
            continue
        pedido = declarado.group(1).strip().strip("'\"")
        caminho = Path(os.path.expanduser(pedido)) if pedido.startswith("~/") else Path(pedido)
        lugar = None
        if caminho.is_absolute() and ".." not in caminho.parts:
            for prefixo, so_plist, no_olhar in AMBIENTE_DO_DONO:
                base = casa / prefixo
                dentro = (caminho.parent == base and caminho.suffix == ".plist") if so_plist else base in caminho.parents
                if dentro and Path(os.path.realpath(base)) in Path(os.path.realpath(caminho)).parents:  # um atalho não leva para fora
                    lugar = (base, no_olhar)
                    break
        if lugar is None:
            sair(f"`ambiente: {pedido}` ({COMANDOS}) fica fora do ambiente do dono; {ENSINA_O_AMBIENTE}.")
        if olhar and not lugar[1]:
            continue
        if criar:  # só quando vai gravar: conferir não deixa pasta vazia na pasta pessoal do dono
            caminho.parent.mkdir(parents=True, exist_ok=True)  # ~/Applications pode ainda não existir; a caixa a cria, fora da caixa do Mac
        achados.append(caminho)
    return achados


FORA_DA_COPIA_DE_ATAQUE = (".delta-11/quadro", ".delta-11/registro", ".delta-11/licoes.md", ".delta-11/estado", ".delta-11/teste-guardado",
                           ".delta-11/leitor", ".delta-11/cofre", ".delta-11/esteira", ".env", ".env.local")


def e_copia_de_ataque(raiz: Path) -> bool:
    return raiz.name.startswith("delta11-ataque-") and any(t in raiz.parents for t in temporarios())


def copia_de_ataque(principal: Path, nome: str) -> None:
    """Monta a cópia de ataque do último commit e diz onde ela ficou."""
    if not re.fullmatch(r"[a-z0-9-]{1,40}", nome or ""):
        sair("o nome da cópia de ataque é curto, em minúsculas, números e hífen (ex.: destruidor-3).")
    destino = Path(tempfile.gettempdir()).resolve() / f"delta11-ataque-{nome}"
    shutil.rmtree(destino, ignore_errors=True)
    destino.mkdir(parents=True)
    sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    pacote = subprocess.run(["git", "-C", str(principal), "archive", "--format=tar", "HEAD"], capture_output=True, env=sem_git)
    if pacote.returncode != 0 or subprocess.run(["tar", "-x", "-C", str(destino)], input=pacote.stdout, capture_output=True).returncode != 0:
        sair("não consegui montar a cópia de ataque do último commit.")
    for fora in FORA_DA_COPIA_DE_ATAQUE:
        alvo = destino / fora
        shutil.rmtree(alvo, ignore_errors=True) if alvo.is_dir() else alvo.unlink(missing_ok=True)
    camada = destino / ".delta-11" / "quadro" / "ataque"
    (camada / "linhas").mkdir(parents=True)
    (camada / "abertura.md").write_text("# Abertura da cópia de ataque\n", encoding="utf-8")
    (camada / "quadro.md").write_text("# Quadro da cópia de ataque\n\nSituação: aberto\n", encoding="utf-8")
    (destino / ".delta-11" / "esteira").mkdir(parents=True, exist_ok=True)
    (destino / ".delta-11" / "esteira" / "ensaio").write_text("a cópia de ataque nunca envia nem publica\n", encoding="utf-8")
    for passo in (["init", "-q", "-b", "main"], ["config", "user.name", "Ataque do Delta-11"], ["config", "user.email", "ataque@delta-11.invalid"],
                  ["config", "core.hooksPath", "/dev/null"], ["add", "-A"], ["commit", "-q", "-m", "cópia de ataque\n\nDelta-11: instalado"]):
        subprocess.run(["git", "-C", str(destino), *passo], capture_output=True, env=sem_git)
    print(f"cópia de ataque pronta: {destino} (rode nela pela caixa: `python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py olhar --raiz {destino} <comando>`)")


def relato_da_copia(nome: str) -> None:
    """O último relato da esteira na cópia de ataque `nome` (o Destruidor não lê o .delta-11 de nenhuma outra pasta)."""
    if not re.fullmatch(r"[a-z0-9-]{1,40}", nome or ""):
        sair("diga o nome da cópia de ataque (o mesmo de `copia-de-ataque <nome>`).")
    copia = (Path(tempfile.gettempdir()).resolve() / f"delta11-ataque-{nome}").resolve()
    pasta = copia / ".delta-11" / "esteira"
    if not e_copia_de_ataque(copia) or pasta.is_symlink() or not pasta.is_dir():
        sair(f"não há relato na cópia de ataque {nome}.")
    relatos = sorted((r for r in pasta.glob("*.log") if r.is_file() and not r.is_symlink() and r.resolve().parent == pasta.resolve()),
                     key=lambda r: r.stat().st_mtime)
    if not relatos:
        sair(f"não há relato na cópia de ataque {nome}.")
    print(f"relato {relatos[-1].name}:")
    print(relatos[-1].read_text(encoding="utf-8", errors="replace")[-20000:])


def dentro_de(caminho: Path, pastas: set[Path]) -> bool:
    return any(caminho == p or p in caminho.parents for p in pastas)


def caches_liberados(principal: Path) -> list[Path]:
    """As pastas de cache das ferramentas (npm, pip...) em que o comando grava: quem diz é o tradutor do programa de agentes
    da instalação (o motor.py da pasta principal, que ninguém altera; nunca o de uma cópia de candidata). Sem o tradutor
    ali, nenhuma: a caixa só aperta."""
    arquivo = principal / ".claude" / "hooks" / "delta-11" / "motor.py"
    if not arquivo.is_file():
        return []
    especificacao = importlib.util.spec_from_file_location("motor_da_pasta_principal", arquivo)
    motor = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(motor)
    return motor.caches_liberados(principal)


def perfil(raiz: Path, principal: Path, git: Path | None, olhar: bool, sem_ambiente: bool = False) -> str:
    """Na caixa do Mac vale a última regra que bate: libera, depois proíbe a pasta principal (quando roda noutra pasta),
    libera de novo a pasta em que roda, e por fim proíbe os lugares de controle das duas (e, no modo de olhar, o que já existe)."""
    mapa = json.loads((principal / ".claude" / "hooks" / "delta-11" / "lugares.json").read_text(encoding="utf-8"))
    caches = caches_liberados(principal)
    controle = {git} if git else set()
    for base in {raiz, principal}:
        controle |= {base / ".git", base / ".delta-11"} | {base / lugar for lugar in mapa["lugares_que_o_terminal_nao_grava"] if "*" not in lugar}
    controle |= {principal / ".claude"} if raiz == principal else {raiz / ".claude"}
    ataque = e_copia_de_ataque(raiz)
    if ataque:  # descartável: a cópia inteira é dela, o .git e o .delta-11 dela também; a pasta principal segue proibida
        controle = {c for c in controle if raiz not in c.parents and c != raiz}
    nao_le = set()
    for lugar in mapa["lugares_que_o_terminal_nao_le"]:
        nao_le |= {Path(lugar).expanduser()} if lugar.startswith("~") else {raiz / lugar, principal / lugar}
    regras = lambda acao, pastas: f"({acao} file-write* " + " ".join(f"(subpath {texto(p)})" for p in sorted(pastas)) + ")"
    # A tela, o teclado e os programas são do dono: pela caixa, nada abre app, manda ordem a outro programa nem simula tecla
    # (isso só pela tela do app, na hora que ele libera).
    linhas = ["(version 1)", "(allow default)", "(deny lsopen)", "(deny appleevent-send)", "(deny hid-control)",
              '(deny mach-lookup (global-name "com.apple.windowserver.active"))',  # sem sessão de tela: nenhuma janela, nenhum evento
              '(deny process-exec (literal "/bin/launchctl") (literal "/usr/bin/open") (literal "/usr/bin/osascript"))',
              "(deny file-write*)", regras("allow", [*temporarios(), *caches, Path("/dev")])]
    ambiente = ambiente_do_dono(raiz, olhar, criar=not (ataque or sem_ambiente))  # confere o `ambiente:` sempre (o errado recusa, ensinando)
    if ataque or sem_ambiente:
        ambiente = []  # da cópia de ataque, e fora do publicar, nada no ambiente do dono
    if ambiente:
        linhas.append(regras("allow", ambiente))
    if raiz != principal:
        linhas.append(regras("deny", [principal]))  # a pasta principal, e as cópias das outras candidatas
    linhas.append(regras("allow", [raiz]))
    if olhar and not ataque:  # a pasta só para ler; de volta, só o que o git ignora (a cópia de ataque é toda dele)
        livres, de_volta = ignorados(raiz)
        linhas += [regras("deny", [raiz]), "(allow file-write* " + " ".join(f'(regex #"{e}")' for e in livres) + ")",
                   "(deny file-write* " + " ".join(f'(regex #"{e}")' for e in de_volta) + ")"]
    linhas.append(regras("deny", controle))
    pessoais = sorted(p for p in nao_le if not dentro_de(p, {raiz, principal}))
    if pessoais:
        linhas.append("(deny file-read* " + " ".join(f"(subpath {texto(p)})" for p in pessoais) + ")")
    # Os segredos da pasta: o conteúdo dos arquivos, não a pasta (quem varre a raiz, como uma ferramenta de teste, passa por ela).
    for pasta in sorted(set(nao_le) - set(pessoais)):
        linhas.append(f'(deny file-read-data (require-all (regex #"^{em_regex(pasta)}/") (vnode-type REGULAR-FILE)))')
    return "\n".join(linhas) + "\n"


def main() -> None:
    args = sys.argv[1:]
    olhar = args[:1] == ["olhar"]
    args = args[1:] if olhar else args
    raiz_pedida, sem_ambiente = None, True
    while args[:1] in (["--raiz"], ["--com-ambiente"]):
        if args[0] == "--com-ambiente":  # só o publicar da esteira: grava no ambiente do dono (a trava não deixa um agente pedir)
            sem_ambiente, args = False, args[1:]
            continue
        if len(args) < 2:
            sair("falta a pasta depois de --raiz.")
        raiz_pedida, args = Path(args[1]).resolve(), args[2:]
    if not args:
        sair("falta o comando. Uso: python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py <comando> [argumentos...]")
    preso = shutil.which("sandbox-exec") and subprocess.run(["sandbox-exec", "-p", "(version 1)(allow default)", "/usr/bin/true"],
                                                            capture_output=True).returncode != 0
    if os.environ.get(DENTRO) == "1" and preso:
        if raiz_pedida:
            os.chdir(raiz_pedida)
        os.execvp(args[0], args)  # já dentro da caixa (a marca e a prova de estar preso): ela continua prendendo este comando
    raiz_do_programa = AQUI.parent.parent.parent
    principal, git = pasta_principal(raiz_do_programa)
    copias = principal / ".claude" / "worktrees"
    if raiz_do_programa != principal and raiz_do_programa.parent != copias:
        sair("esta caixa não está na pasta do produto nem numa cópia de candidata dele.")
    raiz = raiz_do_programa
    if args[:1] == ["copia-de-ataque"]:
        copia_de_ataque(principal, args[1] if len(args) > 1 else "")
        return
    if args[:1] == ["relato-da-copia"]:
        relato_da_copia(args[1] if len(args) > 1 else "")
        return
    if args[:1] == ["apagar-copia-de-ataque"]:
        nome = args[1] if len(args) > 1 else ""
        if not re.fullmatch(r"[a-z0-9-]{1,40}", nome):
            sair("diga o nome da cópia de ataque (o mesmo de `copia-de-ataque <nome>`).")
        copia = Path(tempfile.gettempdir()).resolve() / f"delta11-ataque-{nome}"
        if e_copia_de_ataque(copia) and not copia.is_symlink():
            shutil.rmtree(copia, ignore_errors=True)
        print(f"cópia de ataque {nome} apagada.")
        return
    if raiz_pedida:
        no_temporario = any(t in raiz_pedida.parents for t in temporarios())
        if not (no_temporario or (raiz_pedida.parent == copias and raiz_pedida.is_dir())):
            sair(f"--raiz só aceita a cópia de uma candidata (`.claude/worktrees/<cópia>`) ou uma cópia no temporário (a da esteira); recebeu {raiz_pedida}.")
        raiz = raiz_pedida
    if not shutil.which("sandbox-exec"):
        # Fora do Mac (a automação do repositório): a máquina da automação é descartável e não guarda cofre nem conversas.
        print("caixa do produto: sem sandbox-exec nesta máquina; rodando sem a caixa (só vale fora do computador do dono).", file=sys.stderr)
        os.chdir(raiz)
        os.execvp(args[0], args)
    if preso:
        sair("rodou dentro da caixa de areia do Claude Code, onde ela não abre. Rode sozinha na linha, exatamente "
             "`python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py <comando>` (sem `&&`, `;`, `|`, `cd`, redirecionamento "
             "nem `$(...)`; para encadear, passe `sh -c '<comandos>'` como o comando, sem opção com hífen logo antes do `sh`).")
    regras_da_caixa = perfil(raiz, principal, git, olhar, sem_ambiente)
    with tempfile.NamedTemporaryFile("w", suffix=".sb", prefix="caixa-do-produto-", delete=False, encoding="utf-8") as arquivo:
        arquivo.write(regras_da_caixa)
    try:
        sys.exit(subprocess.run(["sandbox-exec", "-f", arquivo.name, *args], cwd=raiz if raiz_pedida else os.getcwd(),
                                env={**os.environ, DENTRO: "1"}).returncode)
    finally:
        os.remove(arquivo.name)


if __name__ == "__main__":
    main()
