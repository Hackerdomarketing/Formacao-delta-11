#!/usr/bin/env python3
"""Instala o motor do Delta-11 v7 numa pasta de produto, ou atualiza uma pasta que já tem o v7.

Uso: python3 instalar.py <pasta-do-produto>               (produto novo, ou produto que já existe sem o v7)
     python3 instalar.py --atualizar <pasta-do-produto>   (troca agentes, travas, esteira, modelos e configuração; mantém o modelo de IA que o projeto escolheu para cada agente)
     python3 instalar.py --passar-do-v6 <pasta> [--ensaio] [--criar-git] [--guardar-copias]   (projeto que já tem o Delta-11 antigo (v6): passa para o v7
                          sem perder nada e com volta atrás; --ensaio só mostra o que faria, sem mudar nada; detalhes em passagem_do_v6.py)
     --motor <programa>   o programa de agentes que roda o produto: claude-code (o padrão; na atualização, o que a pasta já tem).
                          Fica gravado em .delta-11/motor/VERSAO e no fim do comando de cada gancho: o motor nunca o adivinha.
     --ia <perfil>        a IA (o "cérebro") do produto: claude (o padrão), deepseek, minimax, kimi ou gateway (agentes/perfis-de-ia.json).
                          Escreve a IA em .claude/settings.local.json (fora do git; a chave vem do cofre na hora, nunca vai para arquivo) e o
                          perfil em .delta-11/motor/VERSAO (campo ia). Na atualização, sem --ia, a pasta mantém a IA que já tem.
                          O gateway pede também --endereco, --modelo-forte, --modelo-medio e --modelo-leve (e, se quiser, --entrada-do-cofre).
                          Para trocar a IA de um produto já instalado, sem atualizar o motor: ferramentas/trocar-ia.py.

Nunca toca na fonte da v6.4.1, na fonte do v7, nem numa subpasta de outro repositório. Junta a configuração que a
pasta já tiver (guardando uma cópia), em vez de mantê-la sem a trava. Só instala agentes, trava e esteira que passaram
na conferência e no pulso. A esteira é do motor: vai para a raiz do produto no commit da instalação; os comandos do
produto (esteira-comandos.txt, do BACK) nunca são trocados.
"""
from __future__ import annotations

import datetime
import fnmatch
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
V7 = MOTOR.parent
REGRAS = V7 / "02-regras"
FONTE_V7 = V7.parent
FONTE_V6 = Path.home() / "Documents" / "VSCODE" / "Formacao-delta-11"  # onde o dono guarda a fonte da v6.4.1; no computador de um aluno, quem diz é fontes_da_v6()
MARCA_CLAUDE_MD = "<!-- delta-11 v7"
TRAVA_NA_CONFIGURACAO = "/.claude/hooks/delta-11/"
VAI_PARA_AS_COPIAS = [".env", ".env.local"]
# Fora do git: as cópias das candidatas, a configuração de quem usa o computador, o registro de CRONOS, os segredos
# (os lugares que o terminal não lê, do mapa da trava) e o .env.
IGNORAR_NO_GIT = [".claude/worktrees/", ".claude/settings.local.json", ".claude/settings.json.antes-do-delta-11", ".claude/hooks/delta-11/vivos/",
                  *(l + "/" for l in json.loads((MOTOR / "agentes" / "lugares.json").read_text(encoding="utf-8"))["lugares_que_o_terminal_nao_le"]
                    if not l.startswith("~")), ".delta-11/esteira/", ".rascunho/", "test-results/", "playwright-report/", "coverage/", *VAI_PARA_AS_COPIAS]
# Chaves que, na configuração local (que vale mais que a do projeto), desligariam a trava, a caixa de areia ou o ATLAS.
LOCAL_QUE_DESLIGA = ["disableAllHooks", "agent", "outputStyle", "worktree"]
PASTAS_PESSOAIS = {"documents", "desktop", "downloads", "pictures", "movies", "music", "library", "public", "applications",
                   "documentos", "mesa", "transferências", "imagens", "filmes", "músicas"}
ESTEIRA = MOTOR / "esteira" / "esteira"
COMANDOS_DA_ESTEIRA = "esteira-comandos.txt"
MODELO_DOS_COMANDOS = """# Os comandos do produto para a esteira do motor (do BACK; o formato: .delta-11/motor/modelos/esteira.md).
# Enquanto não houver as linhas `testar:` e `testes:`, a esteira recusa toda entrega. Um exemplo, para um site em Node:
# instalar: npm ci
# montar: npm run build
# testar: npm test
# testes: tests/ *.test.js
# publicar: npx wrangler pages deploy dist
# fluxo-principal: node tests/fluxo-principal.mjs
"""
# O pulso do instalador roda o pulso da esteira uma vez e deixa esta marca (com a impressão digital da esteira e do
# pulso dela) para as instalações dele não o repetirem; a variável sozinha não pula nada.
MARCA_DO_PULSO_DA_ESTEIRA = ".pulso-da-esteira-passou"
# Igual para a trava, a tela do app (sem janela) e os agentes: o pulso da passagem do v6 roda os três uma vez e deixa esta marca, com a
# impressão digital de TODO o v7 (regras e motor) que provou; a variável sozinha não pula nada. Só o pulso a usa.
MARCA_DO_PULSO_DO_MOTOR = ".pulso-do-motor-passou"
# A esteira que o produto tinha construído (sem o cabeçalho da do motor) foi trocada: o aviso de abertura o conta ao ATLAS.
CABECALHO_DA_ESTEIRA_DO_MOTOR = b"# A esteira do Delta-11 v7: o programa do MOTOR"
ESTEIRA_PROPRIA_TROCADA = Path(".delta-11") / "motor" / "esteira-propria-trocada.md"
PELA_METADE = Path(".delta-11") / "motor" / "atualizado-com-camada-aberta.md"
PROGRAMA_PADRAO = "claude-code"
OPCOES_COM_VALOR = ["--motor", "--ia", "--endereco", "--modelo-forte", "--modelo-medio", "--modelo-leve", "--entrada-do-cofre"]
avisos: list[str] = []


def erro(motivo: str) -> None:
    print(f"ERRO: {motivo}\nNada foi instalado.")
    sys.exit(1)


def rodar(*args: str, pasta: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=pasta, capture_output=True, text=True)


def resolver(pasta: str) -> Path:
    """Caminho absoluto de verdade, mesmo para pasta que ainda não existe (resolve o pedaço que existe)."""
    p = Path(pasta).expanduser().absolute()
    existe, resto = p, []
    while not existe.exists():
        resto.insert(0, existe.name)
        existe = existe.parent
    return existe.resolve().joinpath(*resto)


def fontes_da_v6() -> list[Path]:
    """Onde pode estar a fonte da v6.4.1 neste computador. Na pasta publicada para os alunos, a v6.4.1 e o v7 moram no
    mesmo repositório (a pasta v7/ fica dentro dele), mas o aluno pode ter outro clone da v6.4.1 em outro lugar:
    o registro do sincronizador antigo (campo "source") diz qual. O caminho do dono fica na lista (só protege)."""
    fontes = [FONTE_V6]
    registro = Path(os.environ.get("DELTA11_REGISTRY") or (Path.home() / ".delta-11-registry.json")).expanduser()
    try:
        fonte = json.loads(registro.read_text(encoding="utf-8")).get("source")
        if isinstance(fonte, str) and fonte.strip():
            fontes.append(Path(fonte).expanduser())
    except (OSError, ValueError, AttributeError):
        pass
    return fontes


def dentro(caminho: Path, pasta: Path) -> bool:
    try:
        caminho.relative_to(pasta.resolve() if pasta.exists() else pasta)
        return True
    except ValueError:
        return False


def recusar_lugares_proibidos(destino: Path, dentro_de_git_maior_ok: bool = False) -> None:
    if destino in (Path.home(), Path("/")) or len(destino.parts) <= 3:
        erro(f"{destino} é uma pasta do sistema ou a pasta pessoal; o produto precisa de uma pasta só dele.")
    icloud = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    if destino.name.lower() in PASTAS_PESSOAIS or destino == icloud:
        erro(f"{destino} é uma pasta pessoal (Documentos, Mesa, Downloads...); crie dentro dela uma pasta só para o produto.")
    for fonte_v6 in fontes_da_v6():
        if dentro(destino, fonte_v6):
            erro(f"{destino} fica dentro da fonte da v6.4.1 ({fonte_v6}); o v7 não entra lá.")
    if dentro(destino, FONTE_V7):
        erro(f"{destino} fica dentro da fonte do v7 ({FONTE_V7}); instale numa pasta de produto.")
    if destino.is_dir() and not (destino / ".git").exists():  # um produto com repositórios dentro (submódulos, dependências) é um produto só
        outros = sorted({g.parent.relative_to(destino).as_posix() for g in list(destino.glob("*/.git")) + list(destino.glob("*/*/.git"))})
        if outros:
            erro(f"{destino} guarda outros projetos ({', '.join(outros[:3])}); o produto precisa de uma pasta só dele.")
    existe = destino
    while not existe.exists():
        existe = existe.parent
    topo = rodar("git", "-C", str(existe), "rev-parse", "--show-toplevel")
    # O nome com acento chega de dois jeitos (o "é" junto, ou o "e" mais o acento): o git devolve um, o caminho dito pode ser o outro.
    forma = lambda caminho: unicodedata.normalize("NFC", str(caminho))
    if topo.returncode == 0 and forma(Path(topo.stdout.strip()).resolve()) != forma(destino) and not dentro_de_git_maior_ok:  # a passagem do v6 decide isso sozinha, com --criar-git
        erro(f"{destino} fica dentro de outro repositório git ({topo.stdout.strip()}); instale na raiz dele ou numa pasta nova.")


def caminho_de_busca_do_terminal() -> str:
    """O caminho de busca que o terminal do dono usa (com o Homebrew e afins), para os agentes acharem o Node."""
    feito = subprocess.run(["/bin/zsh", "-lc", 'printf %s "$PATH"'], capture_output=True, text=True, timeout=30) \
        if Path("/bin/zsh").exists() else None
    partes = (feito.stdout.split(":") if feito and feito.returncode == 0 else []) + os.environ.get("PATH", "").split(":")
    vistas: list[str] = []
    for parte in partes + ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]:
        if parte and parte not in vistas:
            vistas.append(parte)
    return ":".join(vistas)


def conferir_dependencias(caminho: str) -> None:
    if not shutil.which("git"):
        erro("o git não está instalado; sem ele não há esteira nem volta atrás.")
    if not (shutil.which("claude", path=caminho) or (Path.home() / ".local" / "bin" / "claude").exists()):
        avisos.append("Não achei o Claude Code neste computador; instale-o antes de abrir a pasta.")
    if not shutil.which("node", path=caminho):
        avisos.append("Não achei o Node neste computador: produtos de site e app precisam dele (o BACK avisa na Camada 2).")


def programas_do_motor() -> dict:
    """Os programas de agentes que o motor sabe traduzir (a lista mora no tradutor, ganchos/motor.py)."""
    especificacao = importlib.util.spec_from_file_location("motor_do_delta11", MOTOR / "ganchos" / "motor.py")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo.PROGRAMAS


def programa_instalado(destino: Path) -> str:
    """O programa de agentes que a VERSAO da pasta diz (vazio numa instalação de antes do tradutor)."""
    try:
        return str(json.loads((destino / ".delta-11" / "motor" / "VERSAO").read_text(encoding="utf-8")).get("motor") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def perfil_de_ia():
    """O módulo dos perfis de IA (ferramentas/perfil_de_ia.py), carregado pelo caminho: o mesmo código do trocar-ia.py."""
    especificacao = importlib.util.spec_from_file_location("perfil_de_ia", MOTOR / "ferramentas" / "perfil_de_ia.py")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def digital_da_esteira() -> str:
    return hashlib.sha256(ESTEIRA.read_bytes() + (MOTOR / "ferramentas" / "testar-esteira.py").read_bytes()).hexdigest()


def esteira_ja_provada() -> bool:
    marca = Path(os.environ.get("DELTA11_PULSO_DA_ESTEIRA_FEITO") or "/nenhuma")
    return marca.name == MARCA_DO_PULSO_DA_ESTEIRA and marca.is_file() and marca.read_text(encoding="utf-8").strip() == digital_da_esteira()


def digital_do_motor() -> str:
    """A impressão digital do v7 inteiro (regras e motor, sem os caches): qualquer arquivo mudado depois de provado invalida a marca."""
    h = hashlib.sha256()
    for raiz in (REGRAS, MOTOR):
        for arquivo in sorted(raiz.rglob("*")):
            if arquivo.is_file() and "__pycache__" not in arquivo.parts and arquivo.suffix != ".pyc" and arquivo.name != ".DS_Store":
                h.update(arquivo.relative_to(V7).as_posix().encode() + b"\0" + arquivo.read_bytes() + b"\0")
    return h.hexdigest()


def motor_ja_provado() -> bool:
    marca = Path(os.environ.get("DELTA11_PULSO_DO_MOTOR_FEITO") or "/nenhuma")
    return marca.name == MARCA_DO_PULSO_DO_MOTOR and marca.is_file() and marca.read_text(encoding="utf-8").strip() == digital_do_motor()


def conferir_motor() -> None:
    for script, motivo in [("montar-agentes.py", "os agentes não batem com as páginas das regras"),
                           ("testar-trava.py", "a trava não passou no pulso"),
                           ("testar-tela-do-app.py", "a tela do app não passou no pulso"),
                           ("testar-esteira.py", "a esteira não passou no pulso")]:
        if script == "testar-esteira.py" and esteira_ja_provada():
            continue
        if script != "testar-esteira.py" and motor_ja_provado():
            continue
        opcao = {"montar-agentes.py": ["--conferir"], "testar-tela-do-app.py": ["--sem-janela"]}.get(script, [])  # sem abrir janela no Mac do dono
        feito = rodar(sys.executable, "-B", str(MOTOR / "ferramentas" / script), *opcao)
        if feito.returncode != 0:
            erro(f"{motivo}. Saída: {feito.stdout.strip()[-400:]}")


def ler_json(arquivo: Path) -> dict:
    if not arquivo.exists():
        return {}
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except ValueError:
        erro(f"{arquivo} existe mas não é JSON válido; conserte ou mova esse arquivo antes de instalar.")
    if not isinstance(dados, dict):
        erro(f"{arquivo} não é uma configuração do Claude Code.")
    return dados


def juntar_configuracao(destino: Path) -> None:
    arquivo = destino / ".claude" / "settings.json"
    base = json.loads((MOTOR / "porta-de-entrada" / "settings.json").read_text(encoding="utf-8"))
    atual = ler_json(arquivo)
    copia = destino / ".claude" / "settings.json.antes-do-delta-11"
    if arquivo.exists() and not copia.exists() and TRAVA_NA_CONFIGURACAO not in arquivo.read_text(encoding="utf-8"):
        shutil.copy2(arquivo, copia)
        avisos.append(f"A pasta já tinha configuração do Claude Code; juntei a do Delta-11 a ela e guardei a antiga em {copia.name}.")
    if atual.get("agent") not in (None, "atlas"):
        avisos.append(f"A configuração dizia que o agente principal era '{atual['agent']}'; agora é o ATLAS.")
    if atual.pop("disableAllHooks", None):
        avisos.append("A configuração desligava todos os ganchos (disableAllHooks); religuei, porque a trava é um gancho.")
    novo = dict(atual)
    for chave in ("agent", "outputStyle", "autoMemoryEnabled", "worktree"):
        novo[chave] = base[chave]
    novo["env"] = {**(atual.get("env") or {}), **base["env"]}
    tirar_o_que_fura_a_caixa(novo, "do projeto")
    caixa = dict(atual.get("sandbox") or {})
    for chave in ("enabled", "allowUnsandboxedCommands", "failIfUnavailable"):
        caixa[chave] = base["sandbox"][chave]
    arquivos = dict(caixa.get("filesystem") or {})
    arquivos.pop("disabled", None)
    arquivos["allowWrite"] = list(base["sandbox"]["filesystem"]["allowWrite"])
    mapa = json.loads((MOTOR / "agentes" / "lugares.json").read_text(encoding="utf-8"))
    arquivos["denyWrite"] = sorted(set(arquivos.get("denyWrite") or []) | set(mapa["lugares_que_o_terminal_nao_grava"]))
    arquivos["denyRead"] = sorted(set(arquivos.get("denyRead") or []) | set(mapa["lugares_que_o_terminal_nao_le"]))
    caixa["filesystem"] = arquivos
    rede = dict(caixa.get("network") or {})
    rede["allowedDomains"] = sorted(set(rede.get("allowedDomains") or []) | set(base["sandbox"]["network"]["allowedDomains"]))
    rede["allowLocalBinding"] = base["sandbox"]["network"]["allowLocalBinding"]  # servidor de teste local
    caixa["excludedCommands"] = list(base["sandbox"]["excludedCommands"])  # só a esteira (que grava em .git/), a caixa do produto (presa pela caixa do Mac) e a tela do app (só o app declarado) rodam fora
    permissoes = dict(novo.get("permissions") or {})
    permissoes["allow"] = sorted(set(permissoes.get("allow") or []) | set(base["permissions"]["allow"]))
    novo["permissions"] = permissoes
    caixa["network"] = rede
    novo["sandbox"] = caixa
    ganchos, alheios = {}, 0
    for evento, grupos in (atual.get("hooks") or {}).items():
        mantidos = [g for g in grupos if TRAVA_NA_CONFIGURACAO not in json.dumps(g)]
        alheios += len(mantidos)
        if mantidos:
            ganchos[evento] = mantidos
    for evento, grupos in base["hooks"].items():
        ganchos[evento] = ganchos.get(evento, []) + grupos
    novo["hooks"] = ganchos
    if alheios:
        avisos.append(f"A configuração tem {alheios} gancho(s) de outro sistema; continuam ligados ao lado da trava. Confira se combinam.")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tirar_o_que_fura_a_caixa(config: dict, qual: str) -> None:
    """Comandos postos fora da caixa de areia e pastas extras de escrita furariam a trava pelo terminal."""
    base = json.loads((MOTOR / "porta-de-entrada" / "settings.json").read_text(encoding="utf-8"))["sandbox"]
    caixa = config.get("sandbox")
    if isinstance(caixa, dict):
        if set(caixa.pop("excludedCommands", None) or []) - set(base["excludedCommands"]):
            avisos.append(f"A configuração {qual} tirava comandos da caixa de areia (excludedCommands); tirei.")
        rede, arquivos = caixa.get("network"), caixa.get("filesystem")
        fracos = [c for c in ("allowAllUnixSockets", "enableWeakerNestedSandbox", "ignoreViolations") if caixa.pop(c, None) is not None]
        if isinstance(rede, dict):
            fracos += [c for c in ("allowUnixSockets", "allowAllUnixSockets", "httpProxyPort", "socksProxyPort") if rede.pop(c, None) is not None]
        if isinstance(arquivos, dict) and set(arquivos.pop("allowWrite", None) or []) - set(base["filesystem"]["allowWrite"]):
            fracos.append("allowWrite")
        if fracos:
            avisos.append(f"A configuração {qual} afrouxava a caixa de areia ({', '.join(fracos)}); tirei.")
    permissoes = config.get("permissions")
    if isinstance(permissoes, dict):
        if permissoes.pop("additionalDirectories", None):
            avisos.append(f"A configuração {qual} abria pastas extras para os agentes (additionalDirectories); tirei.")
        if permissoes.pop("defaultMode", None):
            avisos.append(f"A configuração {qual} fixava um modo de permissão; tirei (o modo é de quem usa o computador).")
        def desliga_o_motor(regra_de_permissao: str) -> bool:
            """Chamar agente, mensagem, esteira e escrever são do motor (a trava os confere); ler um segredo com caminho é proteção e fica."""
            nome = regra_de_permissao.split("(")[0]
            geral = "(" not in regra_de_permissao or regra_de_permissao.endswith(("(*)", "(**)"))
            return nome in ("Agent", "SendMessage", "TaskStop", "Write", "Edit", "NotebookEdit") or regra_de_permissao.startswith(
                ("Bash(sh esteira", "Bash(python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py", "Bash(python3 -I -B .claude/hooks/delta-11/tela-do-app.py")) \
                or (nome in ("Read", "Grep", "Glob", "Bash", "WebFetch") and geral)
        for regra in ("deny", "ask"):
            antes = permissoes.get(regra) or []
            depois = [x for x in antes if not desliga_o_motor(str(x))]
            if len(depois) != len(antes):
                permissoes[regra] = depois
                avisos.append(f"A configuração {qual} barrava ou perguntava por ferramentas do motor ({regra}); tirei essas regras.")
    ambiente = config.get("env")
    if isinstance(ambiente, dict) and ambiente.pop("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", None) is not None:
        avisos.append(f"A configuração {qual} limitava quantos agentes chamam agentes; tirei.")


def pastas_extras_pessoais() -> list[str]:
    """As pastas extras da configuração pessoal entram na área em que o terminal grava: a pasta do produto as barra."""
    extras = (configuracao_pessoal().get("permissions") or {}).get("additionalDirectories") or []
    return [str(Path(x).expanduser()) for x in extras if isinstance(x, str)]


def configuracao_pessoal() -> dict:
    # O pulso do instalador aponta uma configuração pessoal de mentira (a de verdade fica intocada).
    arquivo = os.environ.get("DELTA11_PULSO_CONFIGURACAO_PESSOAL") or str(Path.home() / ".claude" / "settings.json")
    try:
        return json.loads(Path(arquivo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def neutralizar_afrouxamentos_pessoais(local: dict) -> None:
    """A configuração pessoal soma as listas da caixa de areia às do projeto: o que ela afrouxa, a local desta pasta desfaz
    (comando posto fora da caixa vira comando barrado; pasta extra de escrita vira pasta proibida; afrouxamento ligado, desligado)."""
    caixa_pessoal = configuracao_pessoal().get("sandbox") or {}
    if not isinstance(caixa_pessoal, dict):
        return
    caixa = local.setdefault("sandbox", {})
    do_motor = ["sh esteira x", "python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py x", "python3 -I -B .claude/hooks/delta-11/tela-do-app.py x"]
    pessoais = [c for c in caixa_pessoal.get("excludedCommands") or [] if isinstance(c, str)]
    fora = [c for c in pessoais if not any(fnmatch.fnmatchcase(m, c) for m in do_motor)]  # barrar estes barraria o motor
    if fora:
        permissoes = local.setdefault("permissions", {})
        permissoes["deny"] = sorted(set(permissoes.get("deny") or []) | {f"Bash({c})" for c in fora})
        avisos.append(f"A configuração pessoal deste computador põe {len(fora)} comando(s) fora da caixa de areia; nesta pasta eles são barrados (rode-os pela caixa do produto).")
    extras = [str(Path(x).expanduser()) for x in (caixa_pessoal.get("filesystem") or {}).get("allowWrite") or [] if isinstance(x, str)]
    if extras:
        arquivos = caixa.setdefault("filesystem", {})
        arquivos["denyWrite"] = sorted(set(arquivos.get("denyWrite") or []) | set(extras))
        avisos.append(f"A configuração pessoal deste computador deixa o terminal gravar em {len(extras)} pasta(s) a mais; nesta pasta, não.")
    ligados = [c for c in ("enableWeakerNestedSandbox", "enableWeakerNetworkIsolation") if caixa_pessoal.get(c)]
    for chave in ligados:
        caixa[chave] = False
    rede_pessoal = caixa_pessoal.get("network") or {}
    if rede_pessoal.get("allowAllUnixSockets"):
        caixa.setdefault("network", {})["allowAllUnixSockets"] = False
        ligados.append("allowAllUnixSockets")
    if ligados:
        avisos.append(f"A configuração pessoal deste computador afrouxa a caixa de areia ({', '.join(ligados)}); nesta pasta, desligado.")
    sem_volta = [c for c in pessoais if c not in fora] + [c for c in ("allowAppleEvents", "ignoreViolations") if caixa_pessoal.get(c)] + [c for c in ("allowUnixSockets", "allowMachLookup", "httpProxyPort", "socksProxyPort") if rede_pessoal.get(c)]
    if sem_volta:
        avisos.append(f"A configuração pessoal deste computador afrouxa a caixa de areia de um jeito que a pasta não desfaz ({', '.join(sem_volta)}): tire de ~/.claude/settings.json.")


def juntar_configuracao_local(destino: Path, caminho: str) -> None:
    """Deixa de fora as instruções pessoais de quem usa o computador e dá aos agentes o caminho de busca do terminal."""
    arquivo = destino / ".claude" / "settings.local.json"
    atual = ler_json(arquivo)
    for chave in LOCAL_QUE_DESLIGA:
        if chave in atual:
            atual.pop(chave)
            avisos.append(f"A configuração local tinha '{chave}', que passaria por cima da do Delta-11; tirei.")
    caixa = atual.get("sandbox")
    if isinstance(caixa, dict):
        for chave, valor_ruim in (("enabled", False), ("allowUnsandboxedCommands", True), ("failIfUnavailable", False)):
            if caixa.get(chave) == valor_ruim:
                caixa.pop(chave)
                avisos.append(f"A configuração local mexia na caixa de areia ({chave}); tirei.")
        if isinstance(caixa.get("filesystem"), dict) and caixa["filesystem"].pop("disabled", None):
            avisos.append("A configuração local desligava a proteção de arquivos da caixa de areia; tirei.")
    if isinstance(atual.get("permissions"), dict) and atual["permissions"].pop("defaultMode", None):
        avisos.append("A configuração local trocava o modo de permissão dos agentes; tirei.")
    for variavel, nome in (("CLAUDE_CODE_FORK_SUBAGENT", "o modo fork"), ("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "as equipes experimentais")):
        if isinstance(atual.get("env"), dict) and atual["env"].pop(variavel, None) is not None:
            avisos.append(f"A configuração local mexia n{'o' if 'modo' in nome else 'as'} {nome}; tirei.")
    tirar_o_que_fura_a_caixa(atual, "local")
    neutralizar_afrouxamentos_pessoais(atual)
    extras = pastas_extras_pessoais()
    if extras:
        caixa = atual.setdefault("sandbox", {})
        arquivos = caixa.setdefault("filesystem", {})
        arquivos["denyWrite"] = sorted(set(arquivos.get("denyWrite") or []) | set(extras))
        avisos.append(f"A configuração pessoal deste computador abre {len(extras)} pasta(s) extra(s) aos agentes; nesta pasta o terminal deles não grava nelas.")
    casa = Path.home()
    fora = {str(casa / ".claude" / "CLAUDE.md"), str(casa / ".claude" / "rules" / "**")}
    for acima in destino.parents:
        for nome in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".claude/CLAUDE.md", ".claude/rules/**"):
            fora.add(str(acima / nome))
    fora |= {str(destino / "AGENTS.md"), str(destino / ".claude" / "AGENTS.md")}  # instruções de outro sistema na raiz
    if (destino / "AGENTS.md").exists() or (destino / ".mcp.json").exists():
        avisos.append("A pasta tem AGENTS.md ou .mcp.json de outro sistema; o AGENTS.md fica fora da conversa, e as ferramentas do .mcp.json não estão na lista de nenhum agente.")
    atual["claudeMdExcludes"] = sorted(set(atual.get("claudeMdExcludes") or []) | fora)
    ambiente = dict(atual.get("env") or {})
    ambiente["PATH"] = caminho
    atual["env"] = ambiente
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def guardar_instrucoes_antigas(destino: Path) -> None:
    """Instruções de outro sistema na pasta brigariam com o ATLAS: vão inteiras para `.delta-11/motor/instrucoes-anteriores/`, onde o ATLAS as lê."""
    guarda = destino / ".delta-11" / "motor" / "instrucoes-anteriores"  # o ATLAS as lê para escrever a Luz de um produto que já existe
    for nome in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md", ".claude/rules"):
        alvo = destino / nome
        if not alvo.exists() or (alvo.is_file() and alvo.read_text(encoding="utf-8", errors="replace").startswith(MARCA_CLAUDE_MD)):
            continue
        guarda.mkdir(parents=True, exist_ok=True)
        novo = guarda / nome.replace("/", "_").lstrip(".")
        while novo.exists():
            novo = novo.with_name("outra-" + novo.name)
        shutil.move(str(alvo), str(novo))
        avisos.append(f"A pasta tinha instruções de outro sistema ({nome}); guardei-as em {novo.relative_to(destino)}.")


def conferir_antes_de_mexer(destino: Path, atualizar: bool, ignorar_mudancas_sem_commit: bool = False) -> None:
    """Tudo o que pode recusar a instalação é conferido aqui, antes de qualquer mudança na pasta."""
    pasta = destino / ".claude" / "agents"
    manifesto = destino / ".claude" / "hooks" / "delta-11" / "agentes-instalados.txt"
    antigos = set(manifesto.read_text(encoding="utf-8").split()) if manifesto.exists() else set()
    novos = sorted(p.name for p in (MOTOR / "agentes").glob("*.md"))
    conflitos = [n for n in novos if (pasta / n).exists() and n not in antigos]
    if conflitos:
        erro(f"a pasta já tem agentes de outro sistema com os nomes do Delta-11: {', '.join(conflitos)}. Renomeie ou mova esses arquivos.")
    for configuracao in (destino / ".claude" / "settings.json", destino / ".claude" / "settings.local.json"):
        ler_json(configuracao)
    if not atualizar and not ignorar_mudancas_sem_commit and (destino / ".git").exists():  # a passagem do v6 guarda essas mudanças num commit antes
        soltos = rodar("git", "status", "--porcelain", pasta=destino).stdout.splitlines()
        if soltos:
            erro(f"a pasta tem {len(soltos)} mudança(s) sem commit (por exemplo {soltos[0].strip()}); guarde-as num commit, ou descarte-as, "
                 "antes de instalar: depois ninguém seria dono delas.")


def instalar_agentes(destino: Path, atualizar: bool) -> int:
    pasta = destino / ".claude" / "agents"
    manifesto = destino / ".claude" / "hooks" / "delta-11" / "agentes-instalados.txt"
    antigos = set(manifesto.read_text(encoding="utf-8").split()) if manifesto.exists() else set()
    novos = sorted(p.name for p in (MOTOR / "agentes").glob("*.md"))
    outros = sorted(p.name for p in pasta.glob("*.md") if p.name not in antigos | set(novos)) if pasta.is_dir() else []
    if outros:
        avisos.append(f"A pasta tem outros agentes ({', '.join(outros)}); nenhum agente do Delta-11 consegue chamá-los.")
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in sorted(antigos - set(novos)):
        (pasta / velho).unlink(missing_ok=True)
        avisos.append(f"Tirei o agente {velho}, que saiu do Delta-11.")
    for nome in novos:
        texto = (MOTOR / "agentes" / nome).read_text(encoding="utf-8")
        alvo = pasta / nome
        if atualizar and alvo.exists():
            escolhido = next((l for l in alvo.read_text(encoding="utf-8").splitlines() if l.startswith("model: ")), None)
            if escolhido:
                texto = "\n".join(escolhido if l.startswith("model: ") else l for l in texto.split("\n"))
        alvo.write_text(texto, encoding="utf-8")
    manifesto.parent.mkdir(parents=True, exist_ok=True)
    manifesto.write_text("\n".join(novos) + "\n", encoding="utf-8")
    return len(novos)


def instalar_ganchos_e_modelos(destino: Path) -> None:
    ganchos = destino / ".claude" / "hooks" / "delta-11"
    ganchos.mkdir(parents=True, exist_ok=True)
    do_motor = {o.name for o in (MOTOR / "ganchos").iterdir() if o.is_file()} | {"lugares.json", "agentes-instalados.txt"}
    for velho in ganchos.iterdir():
        if velho.is_file() and velho.name not in do_motor:
            velho.unlink()  # gancho de uma versão anterior do motor (por exemplo guardar-registro.sh)
    for origem in [*(MOTOR / "ganchos").iterdir(), MOTOR / "agentes" / "lugares.json"]:
        if origem.is_file():
            shutil.copy2(origem, ganchos / origem.name)
            (ganchos / origem.name).chmod(0o755 if origem.suffix in (".py", ".sh") else 0o644)
    tradutores = ganchos / "motores"  # um por programa de agentes; o motor.py escolhe pelo nome dito no comando
    if tradutores.is_dir():
        shutil.rmtree(tradutores)
    shutil.copytree(MOTOR / "ganchos" / "motores", tradutores, ignore=shutil.ignore_patterns("__pycache__"))
    for tradutor in tradutores.iterdir():
        tradutor.chmod(0o644)
    modelos = destino / ".delta-11" / "motor" / "modelos"
    if modelos.is_dir():
        shutil.rmtree(modelos)
    modelos.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location("gerar", REGRAS / "ferramentas" / "gerar-paginas.py")
    gerar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gerar)
    # A tabela de territórios vai junto: o ARQUITETO e o CRONOS a carregam pelos modelos (a fonte continua uma só).
    for origem in [*(MOTOR / "modelos").glob("*.md"), *(REGRAS / "modelos").glob("*.md"), REGRAS / "fontes" / "territorios.md", REGRAS / "fontes" / "camadas.md"]:
        (modelos / origem.name).write_text(gerar.com_valores(origem.read_text(encoding="utf-8")), encoding="utf-8")
    shutil.copy2(MOTOR / "esteira" / "esteira-automacao.yml", modelos / "esteira-automacao.yml")  # o BACK o copia para .github/workflows/
    for pasta in ("quadro", "estado", "registro/para-o-delta-11", "cofre"):
        (destino / ".delta-11" / pasta).mkdir(parents=True, exist_ok=True)
    referencias = destino / "referencias"  # o dono solta aqui o que quer mostrar ao ATLAS; a Luz cita o que ele escolheu vendo
    if not referencias.exists():
        referencias.mkdir()
        (referencias / "COMO-USAR.md").write_text(
            "# Referências do dono\n\nSolte aqui prints, PDFs, planilhas e fotos de outros sistemas que você quer mostrar ao ATLAS. "
            "Ele lê tudo o que está aqui (diga a ele o nome do arquivo). Você também pode colar ou arrastar uma imagem direto na conversa.\n",
            encoding="utf-8")
    como = destino / ".delta-11" / "registro" / "para-o-delta-11" / "00-como-usar.md"
    if not como.exists():
        como.write_text("# Lições e defeitos do próprio Delta-11: um arquivo novo por achado (quem mantém o Delta-11 recolhe; o dono não é avisado)\n", encoding="utf-8")
    claude_md = destino / "CLAUDE.md"
    novo_claude = (MOTOR / "porta-de-entrada" / "CLAUDE.md").read_text(encoding="utf-8")
    if claude_md.exists() and claude_md.read_text(encoding="utf-8") != novo_claude:
        avisos.append("Troquei o CLAUDE.md do Delta-11 pela versão nova do motor.")
    claude_md.write_text(novo_claude, encoding="utf-8")
    copias = destino / ".worktreeinclude"
    if not copias.exists():
        copias.write_text("# Delta-11 v7: o que vai para as cópias das candidatas (só o que o git ignora)\n" + "\n".join(VAI_PARA_AS_COPIAS) + "\n", encoding="utf-8")


def instalar_esteira(destino: Path) -> list[str]:
    """A esteira do motor vai para a raiz; os comandos do produto, só o modelo e só se ainda não existem. Devolve o que entra no commit."""
    alvo = destino / "esteira"
    nova = ESTEIRA.read_bytes()
    if alvo.exists() and alvo.read_bytes() != nova:
        avisos.append("Troquei o programa `esteira` da pasta pela esteira do motor (a antiga fica no histórico do git); os comandos do produto ficam em esteira-comandos.txt.")
        if CABECALHO_DA_ESTEIRA_DO_MOTOR not in alvo.read_bytes()[:400]:
            marca = destino / ESTEIRA_PROPRIA_TROCADA
            marca.parent.mkdir(parents=True, exist_ok=True)
            marca.write_text(f"# A esteira própria do produto foi trocada pela do motor em {datetime.date.today().isoformat()}\n\n"
                             "Os testes e os pulsos que ela rodava continuam no código; um pedido do dono os tira, ou o `testar:` os chama.\n", encoding="utf-8")
            avisos.append("A esteira antiga era do próprio produto: os testes e pulsos dela continuam no código (um pedido os tira).")
    alvo.write_bytes(nova)
    alvo.chmod(0o755)
    comandos = destino / COMANDOS_DA_ESTEIRA
    if comandos.exists():
        return ["esteira"]
    comandos.write_text(MODELO_DOS_COMANDOS, encoding="utf-8")
    avisos.append("Pus o modelo de esteira-comandos.txt na raiz: o BACK escreve nele os comandos de instalar, montar, testar e publicar o produto.")
    return ["esteira", COMANDOS_DA_ESTEIRA]


def o_que_esta_pela_metade(destino: Path) -> list[str]:
    """Antes de trocar o motor: as camadas abertas, as mudanças do produto sem commit (o que nenhuma entrega juntou) e as
    entregas sem fim (o relato da esteira sem ENTROU nem RECUSOU). Vazio: nada aberto."""
    quadro = destino / ".delta-11" / "quadro"
    abertas = []
    for pasta in sorted(p for p in quadro.iterdir() if p.is_dir()) if quadro.is_dir() else []:
        if not ((pasta / "abertura.md").is_file() or (pasta / "quadro.md").is_file()):
            continue
        texto = (pasta / "quadro.md").read_text(encoding="utf-8", errors="replace") if (pasta / "quadro.md").is_file() else ""
        achado = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", texto, re.IGNORECASE)
        valor = achado.group(1).strip().strip("*_ ").lower() if achado else ""
        if not (valor.startswith(("selad", "encerrad", "feit")) or re.match(r"parada\b", valor)):
            abertas.append(f"{pasta.name} ({valor or 'aberta'})")
    soltos = [l[3:] for l in rodar("git", "status", "--porcelain", "--untracked-files=all", pasta=destino).stdout.splitlines()
              if not l[3:].startswith((".delta-11/", ".claude/"))]
    sem_fim = []
    for relato in sorted((destino / ".delta-11" / "esteira").glob("*.log"), key=lambda r: r.stat().st_mtime):  # a mais nova por último
        linhas = [l for l in relato.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        if linhas and not linhas[-1].startswith(("ENTROU", "RECUSOU")):
            sem_fim.append(relato.name)
    if not (abertas or soltos or sem_fim):
        return []
    return (([f"Camadas abertas: {', '.join(abertas)}."] if abertas else ["Nenhuma camada aberta."])
            + ([f"Mudanças do produto que nenhuma entrega juntou ({len(soltos)}): {', '.join(soltos[:12])}{' e mais' if len(soltos) > 12 else ''}."] if soltos else [])
            + ([f"Entregas sem fim (o relato não diz ENTROU nem RECUSOU): {', '.join(sem_fim[-6:])}."] if sem_fim else []))


def registrar_o_que_esta_pela_metade(destino: Path, achados: list[str]) -> None:
    """Guarda a lista para o aviso de abertura (o ATLAS a leva ao ARQUITETO, que decide pelo modelo do tamanho)."""
    marca = destino / PELA_METADE
    if not achados:
        marca.unlink(missing_ok=True)
        return
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(f"# O motor foi atualizado com trabalho pela metade em {datetime.datetime.now().isoformat(timespec='minutes')}\n\n"
                     + "\n".join(f"- {a}" for a in achados) + "\n", encoding="utf-8")
    avisos.append("A atualização pegou trabalho pela metade (o ATLAS o leva ao ARQUITETO): " + " ".join(achados))


def marcar_versao(destino: Path, atualizar: bool, programa: str, ia: str) -> None:
    commit = rodar("git", "-C", str(FONTE_V7), "rev-parse", "--short", "HEAD").stdout.strip() or "sem-git"
    sujo = bool(rodar("git", "-C", str(FONTE_V7), "status", "--porcelain", "--", "v7").stdout.strip())
    if sujo:
        avisos.append("O motor tinha mudança não guardada no git quando instalei; a marca da versão diz isso.")
    marca = {"delta11": "v7", "motor": programa, "ia": ia, "motor_commit": commit, "motor_com_mudanca_nao_guardada": sujo, "fonte": str(FONTE_V7),
             "instalado_em": datetime.datetime.now().isoformat(timespec="seconds"), "atualizacao": atualizar}
    (destino / ".delta-11" / "motor" / "VERSAO").write_text(json.dumps(marca, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def preparar_git(destino: Path) -> None:
    if not (destino / ".git").exists():
        rodar("git", "init", "-q", "-b", "main", pasta=destino)
    if not rodar("git", "config", "user.email", pasta=destino).stdout.strip():
        rodar("git", "config", "user.name", "Dono do produto", pasta=destino)
        rodar("git", "config", "user.email", "dono@produto.invalid", pasta=destino)
        avisos.append("O git deste computador não tem nome e e-mail; usei 'Dono do produto' só nesta pasta.")
    ignorar = destino / ".gitignore"
    atuais = ignorar.read_text(encoding="utf-8").splitlines() if ignorar.exists() else []
    # Pasta que já ignorava .delta-11/ ou .claude/: o motor e o registro precisam entrar no git (as exceções vêm antes do bloco do Delta-11).
    ignorados = [p for p in (".delta-11/motor/VERSAO", ".delta-11/luz.md", ".claude/agents/atlas.md", "CLAUDE.md")
                 if rodar("git", "check-ignore", "-q", "--no-index", p, pasta=destino).returncode == 0]
    if ignorados and "!.delta-11/" not in atuais:
        with ignorar.open("a", encoding="utf-8") as f:
            f.write(("\n" if atuais and atuais[-1] else "") + "# Delta-11 v7: o motor e o registro entram no git\n!.delta-11/\n!.delta-11/**\n!.claude/\n!.claude/**\n!CLAUDE.md\n")
        avisos.append("O .gitignore desta pasta ignorava .delta-11/ ou .claude/; acrescentei as exceções para o motor entrar no git.")
        atuais = ignorar.read_text(encoding="utf-8").splitlines()
    # Depois de uma exceção (`!.delta-11/**`), o bloco do Delta-11 vem de novo inteiro: no .gitignore vale a última linha que bate.
    depois_da_excecao = atuais[max(i for i, l in enumerate(atuais) if l.startswith("!.delta-11")) + 1:] if any(l.startswith("!.delta-11") for l in atuais) else atuais
    faltam = [l for l in IGNORAR_NO_GIT if l not in depois_da_excecao]
    if faltam:
        with ignorar.open("a", encoding="utf-8") as f:
            f.write(("\n" if atuais and atuais[-1] else "") + "# Delta-11 v7: fora do git\n" + "\n".join(faltam) + "\n")


def guardar_no_git(destino: Path, atualizar: bool, da_esteira: list[str]) -> None:
    # Na atualização, só o motor: o trabalho em andamento no quadro não entra com a mensagem da instalação.
    caminhos = [".gitignore", "CLAUDE.md", ".worktreeinclude", ".claude/agents", ".claude/hooks/delta-11", ".claude/settings.json",
                *da_esteira, ".delta-11/motor" if atualizar else ".delta-11"]
    for nome in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md", ".claude/rules"):
        if rodar("git", "ls-files", "--error-unmatch", nome, pasta=destino).returncode == 0:
            caminhos.append(nome)  # instrução antiga que saiu do lugar: o commit registra a mudança
    if (destino / "referencias" / "COMO-USAR.md").is_file():
        caminhos.append("referencias/COMO-USAR.md")  # só o que o instalador põe; o que o dono solta ali, ele mesmo guarda
    # -f: o motor entra mesmo numa pasta que já ignorava .claude/ (o que é de fora do git continua fora pelo .gitignore do Delta-11).
    adicionado = rodar("git", "add", "-A", "-f", "--", *[c for c in caminhos if c != ".delta-11" and c != ".delta-11/motor"], pasta=destino)
    rodar("git", "reset", "-q", "--", ".claude/hooks/delta-11/vivos", ".claude/hooks/delta-11/__pycache__", ".claude/hooks/delta-11/motores/__pycache__",
          pasta=destino)  # nunca entram
    if adicionado.returncode == 0:
        adicionado = rodar("git", "add", "-A", "--", ".delta-11/motor" if atualizar else ".delta-11", pasta=destino)
    if adicionado.returncode != 0:
        erro(f"o git não aceitou os arquivos instalados: {adicionado.stderr.strip()}")
    if rodar("git", "diff", "--cached", "--quiet", "--", *caminhos, pasta=destino).returncode != 0:
        feito = rodar("git", "commit", "-q", "-m", ("Delta-11 v7 atualizado" if atualizar else "Delta-11 v7 instalado") + "\n\nDelta-11: instalado", "--", *caminhos, pasta=destino)
        if feito.returncode != 0:
            erro(f"o git não guardou a instalação: {feito.stderr.strip()}")


def recusar_sistema_sem_caixa() -> None:
    """O v7 exige a caixa de areia do Claude Code, que só existe no Mac e no Linux (e no WSL2): no Windows, com ela
    obrigatória, o Claude Code fecha ao abrir a pasta. Recusa antes de mexer em qualquer coisa."""
    if platform.system() not in ("Darwin", "Linux"):
        erro("o v7 ainda não roda no Windows: lá a caixa de areia do Claude Code não existe, e sem ela o Claude Code fecha ao abrir a "
             "pasta. Neste computador, continue no Delta-11 v6.4.1 (`bash novo-projeto.sh <pasta>`, na pasta da Formação).")


def main() -> int:
    args = sys.argv[1:]
    recusar_sistema_sem_caixa()
    if "--passar-do-v6" in args or "--ensaio" in args or "--criar-git" in args or "--guardar-copias" in args:
        # A passagem de um projeto do v6 para o v7 mora em passagem_do_v6.py; só ela entende estas opções.
        if "--passar-do-v6" not in args or "--atualizar" in args:
            print(__doc__)
            return 2
        especificacao = importlib.util.spec_from_file_location("passagem_do_v6", Path(__file__).resolve().parent / "passagem_do_v6.py")
        passagem = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(passagem)
        return passagem.executar(args, sys.modules[__name__])
    atualizar = "--atualizar" in args
    args = [a for a in args if a != "--atualizar"]
    pedidos: dict[str, str] = {}
    for opcao in OPCOES_COM_VALOR:
        if opcao in args:
            posicao = args.index(opcao)
            if posicao + 1 >= len(args) or args[posicao + 1].startswith("-"):
                print(__doc__)
                return 2
            pedidos[opcao] = args[posicao + 1]
            del args[posicao:posicao + 2]
    pedido_de_programa = pedidos.get("--motor", "")
    if len(args) != 1 or args[0].startswith("-"):
        print(__doc__)
        return 2
    destino = resolver(args[0])
    recusar_lugares_proibidos(destino)
    marca = destino / ".delta-11" / "motor" / "VERSAO"
    tem_v7 = marca.is_file() and '"delta11": "v7"' in marca.read_text(encoding="utf-8", errors="replace") \
        and (destino / ".claude" / "hooks" / "delta-11" / "agentes-instalados.txt").is_file()
    if atualizar and not tem_v7:
        erro("--atualizar só vale para pasta que já tem o v7 instalado.")
    if not atualizar and tem_v7:
        erro("esta pasta já tem o v7; para trocar pela versão nova, use --atualizar.")
    if not atualizar and (destino / ".delta-11").exists():
        erro("a pasta já tem .delta-11/ de outra versão do Delta-11 (v6 ou anterior); instale o v7 numa pasta nova.")
    # O programa de agentes é dito aqui, nunca adivinhado: o pedido, ou (na atualização) o que a pasta já tem, ou o padrão.
    programa = pedido_de_programa or (programa_instalado(destino) if atualizar else "") or PROGRAMA_PADRAO
    conhecidos = programas_do_motor()
    if programa not in conhecidos:
        erro(f"o motor ainda não sabe falar com o programa de agentes '{programa}' (os que ele conhece: {', '.join(conhecidos)}).")
    # A IA do produto: a pedida, ou (na atualização) a que a pasta já tem, ou o Claude. O pedido é conferido aqui (perfil conhecido, o que o
    # gateway pede, a chave no cofre), antes de qualquer mudança na pasta.
    modulo_de_ia = perfil_de_ia()
    ia_pedida = pedidos.get("--ia", "")
    ia_da_pasta = modulo_de_ia.ia_instalada(destino) if atualizar else ""
    ia = ia_pedida or ia_da_pasta or modulo_de_ia.PERFIL_PADRAO
    argumentos_da_ia = (pedidos.get("--endereco", ""), pedidos.get("--modelo-forte", ""), pedidos.get("--modelo-medio", ""),
                        pedidos.get("--modelo-leve", ""), pedidos.get("--entrada-do-cofre", ""))
    if ia_pedida or any(argumentos_da_ia):
        try:
            modulo_de_ia.preparar_perfil(ia, *argumentos_da_ia)
        except modulo_de_ia.RecusaDePerfil as recusa:
            erro(str(recusa))
    caminho = caminho_de_busca_do_terminal()
    conferir_dependencias(caminho)
    conferir_motor()
    if destino.exists():
        conferir_antes_de_mexer(destino, atualizar)
    if atualizar:
        rodando = destino / ".delta-11" / "esteira" / "rodando"
        vivas = []
        for sinal in rodando.glob("*") if rodando.is_dir() else []:
            pid = sinal.name.rsplit("-", 1)[-1]
            linhas = sinal.read_text(encoding="utf-8", errors="replace").splitlines()
            comeco = rodar("ps", "-o", "lstart=", "-p", pid).stdout.strip() if pid.isdigit() else ""
            if comeco and len(linhas) > 1 and linhas[1].strip() == comeco:
                vivas.append(sinal.name)
        if vivas:
            erro(f"uma entrega está rodando agora ({', '.join(vivas)}): espere a esteira terminar antes de atualizar o motor.")
    pela_metade = o_que_esta_pela_metade(destino) if atualizar else []
    destino.mkdir(parents=True, exist_ok=True)
    preparar_git(destino)
    guardar_instrucoes_antigas(destino)
    quantos = instalar_agentes(destino, atualizar)
    instalar_ganchos_e_modelos(destino)
    da_esteira = instalar_esteira(destino)
    if atualizar:
        registrar_o_que_esta_pela_metade(destino, pela_metade)
    juntar_configuracao(destino)
    juntar_configuracao_local(destino, caminho)
    # O perfil claude é a instalação de sempre (não escreve nada). Outra IA, ou a volta ao Claude numa pasta que tinha outra, escreve (ou tira)
    # as variáveis e o comando da chave; sem --ia, a atualização deixa a IA da pasta como está (a configuração local sobrevive à junção acima).
    if ia_pedida and (ia_pedida != modulo_de_ia.PERFIL_PADRAO or ia_da_pasta not in ("", modulo_de_ia.PERFIL_PADRAO)):
        try:
            resumo_da_ia = modulo_de_ia.aplicar_perfil_de_ia(destino, ia, *argumentos_da_ia)
        except modulo_de_ia.RecusaDePerfil as recusa:
            erro(f"{recusa} (a pasta já tinha sido mexida; rode de novo)")
        avisos.extend(resumo_da_ia["avisos"])
        if ia != modulo_de_ia.PERFIL_PADRAO:
            avisos.append(f"A IA deste produto é {resumo_da_ia['nome']}: a chave vem do cofre na hora (entrada {resumo_da_ia['entrada_do_cofre']}) e nada foi gravado em arquivo. "
                          + modulo_de_ia.LEMBRETE_DO_LIMITE)
    marcar_versao(destino, atualizar, programa, ia)
    guardar_no_git(destino, atualizar, da_esteira)
    print(f"OK — Delta-11 v7 {'atualizado' if atualizar else 'instalado'} em {destino} ({quantos} agentes, trava, esteira e aviso de abertura ligados;"
          f" programa de agentes: {programa}; ia: {ia}).")
    for aviso in avisos:
        print(f"  Aviso: {aviso}")
    print("Próximo passo do dono: abrir esta pasta no VSCode, abrir o painel do Claude e aceitar a pergunta de confiança na pasta"
          " (só na primeira vez). Quem responde é o ATLAS. Deixe o computador ligado e a conversa aberta enquanto uma camada anda.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
