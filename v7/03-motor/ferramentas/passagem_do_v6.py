#!/usr/bin/env python3
"""A passagem de um projeto do Delta-11 v6 para o v7 (`instalar.py --passar-do-v6 <pasta>`).

Muda a "casa" de um projeto que tem o Delta-11 antigo sem perder um arquivo e com volta atrás. A ordem é sempre: recusar cedo
(antes de mudar qualquer coisa), guardar tudo, só então mudar, e deixar a volta escrita.

Uso (pelo instalador):
  instalar.py --passar-do-v6 <pasta> [--ensaio] [--criar-git] [--guardar-copias] [--motor claude-code]
    --ensaio           só mostra o que seria feito, com os números; não muda NENHUM arquivo (nem do projeto, nem do registro, nem a pasta de cópias)
    --criar-git        autoriza criar git próprio quando a pasta não tem (a raiz do git tem de ser a própria pasta)
    --guardar-copias   autoriza guardar o trabalho das cópias de agentes em ramos e levar as cópias para a gaveta

O que faz, nesta ordem (para na primeira recusa, antes de mudar qualquer coisa):
  1. Recusas: já é v7; sem o Delta-11 antigo; conversa aberta (3 sinais); cópias de agentes com trabalho sem --guardar-copias; sem git próprio sem --criar-git.
  2. Guarda: .tar.gz da pasta inteira (só sem git próprio); segredos para o .gitignore; git próprio (com --criar-git); commit "estado antes do v7";
     o trabalho das cópias de agentes em ramos; a marca `antes-do-v7`.
  3. Gaveta: a .delta-11/ antiga inteira vira .delta-11/anterior-v6/ (renomeada, nunca copiada e apagada), com o que era do sistema antigo na raiz
     (anterior-v6/raiz/); os ganchos do v6 saem das configurações; as cópias de agentes vão para anterior-v6/copias-de-agentes/ (git worktree move).
  4. Instala o v7 como numa pasta nova.  5. Escreve anterior-v6/PONTO-DE-PARTIDA.md.  6. (o aviso de abertura, em ganchos/situacao.py, o mostra ao ATLAS)
  7. Commit "passagem do Delta-11 v6 para o v7".  8. Tira a pasta do registro do sincronizador antigo.  9. Grava e imprime o relato.
Se algo falhar antes do commit, tudo o que mudou de lugar volta (a rede de segurança do git e o .tar.gz ficam). Nada é apagado pela passagem.

Variáveis de ambiente:
  DELTA11_REGISTRY                 o registro do sincronizador antigo (padrão ~/.delta-11-registry.json)
  DELTA11_COPIAS_ANTES_DO_V7       onde ficam os .tar.gz (padrão ~/Delta-11-copias-antes-do-v7/; fora de ~/Documents/VSCODE, ~/projetos e ~/Downloads)
Variáveis só do pulso (testar-passagem.py); mudar uma delas nunca enfraquece uma recusa:
  DELTA11_PULSO_LSOF_DE_MENTIRA    arquivo `saida-de-lsof-de-mentira.txt`, com a primeira linha MARCA_DO_LSOF_DE_MENTIRA, no lugar da saída do lsof
  DELTA11_PULSO_PASSAGEM_FALHAR_DEPOIS_DE   falha de propósito depois do passo dito (guardar, gaveta, instalar-o-v7, ponto-de-partida), para provar a volta
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import unicodedata
import time
from pathlib import Path

GAVETA = Path(".delta-11") / "anterior-v6"
NOME_TEMPORARIO = ".delta-11-antigo-do-v6"
GANCHO_DO_V6 = ".delta-11/hooks/"
MARCA_DO_LSOF_DE_MENTIRA = "# pulso da passagem do v6: saída de mentira do lsof"
NOME_DO_LSOF_DE_MENTIRA = "saida-de-lsof-de-mentira.txt"
PROGRAMAS_DE_CONVERSA = ("claude", "codex", "kilo", "kimi")
SO_PROTEGIDOS_DO_V6 = ("CLAUDE.md", "AGENTS.md")
SUFIXOS_DE_MODELO = (".example", ".sample", ".template", ".dist")
LINHAS_DE_SEGREDO = [".env", ".env.*", "!.env.example", "*.pem", "*.key", "credentials.json"]
LIMITE_ARQUIVO_SOLTO = 100 * 1024 * 1024
LIMITE_TOTAL_SOLTO = 1024 * 1024 * 1024
MINUTOS_DO_VINCULO = 30
MINUTOS_DO_QUADRO = 10
PALAVRAS_DO_PONTO_DE_PARTIDA = 1000
CONFIGURACOES_COM_GANCHOS = (".claude/settings.json", ".claude/settings.local.json", ".codex/hooks.json")
# Arquivos que a passagem muda no lugar: o original vai para anterior-v6/raiz/ antes (e a receita de volta o devolve por cima).
ORIGINAIS_GUARDADOS = (".gitignore", *CONFIGURACOES_COM_GANCHOS)
VARRIDOS_PELOS_MONITORES = ("Documents/VSCODE", "projetos", "Downloads")
CANDIDATOS_A_INSTRUCAO_ANTIGA = ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md", ".claude/rules")


class Recusada(Exception):
    """A passagem não pode acontecer; nada foi mudado."""


class Falhou(Exception):
    """Algo falhou no meio; o que mudou de lugar volta."""


# ───────────── pequenas ferramentas ─────────────

def git(destino: Path, *args: str) -> subprocess.CompletedProcess:
    """O git, sem as variáveis GIT_* de quem chamou (um gancho de commit apontaria para outro repositório) e sem gravar o índice só para olhar."""
    ambiente = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    ambiente.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    return subprocess.run(["git", "-C", str(destino), "-c", "core.quotepath=false", *args], capture_output=True, text=True, encoding="utf-8",
                          errors="surrogateescape", env=ambiente)


def git_que_grava(destino: Path, *args: str) -> subprocess.CompletedProcess:
    """O git que grava no repositório (commit, marca, ramo): sem os ganchos do projeto, sem assinatura e com uma identidade se o computador não tem."""
    identidade = [] if git(destino, "config", "user.email").stdout.strip() else ["-c", "user.name=Delta-11", "-c", "user.email=delta11@produto.invalid"]
    return git(destino, "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *identidade, *args)


def numero(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def tamanho(bytes_: int) -> str:
    if bytes_ >= 1024 ** 3:
        return f"{bytes_ / 1024 ** 3:.1f} GB".replace(".", ",")
    return f"{bytes_ / 1024 ** 2:.1f} MB".replace(".", ",")


def plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def hora(momento: float) -> str:
    return time.strftime("%H:%M", time.localtime(momento))


def data_e_hora(momento: float) -> str:
    return time.strftime("%d/%m %H:%M", time.localtime(momento))


def medir(pasta: Path) -> tuple[int, int]:
    """(bytes, arquivos) de uma pasta, sem seguir links."""
    total, quantos = 0, 0
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            try:
                total += os.lstat(os.path.join(raiz, nome)).st_size
                quantos += 1
            except OSError:
                pass
    return total, quantos


def e_segredo(caminho: str) -> bool:
    """`.env`, `.env.*` (menos os modelos sem valor), `*.pem`, `*.key` e `credentials.json`; o que está em node_modules é dependência, não segredo."""
    partes = caminho.split("/")
    if "node_modules" in partes[:-1]:
        return False
    nome = partes[-1].lower()
    if nome == ".env" or (nome.startswith(".env.") and not nome.endswith(SUFIXOS_DE_MODELO)):
        return True
    return nome.endswith((".pem", ".key")) or nome == "credentials.json"


def linha_de_ignorar(relativo: str) -> str:
    """O caminho de um arquivo como linha de .gitignore: ancorado na raiz, com os caracteres especiais protegidos."""
    protegido = re.sub(r"([*?\[\]\\])", r"\\\1", relativo)
    return "/" + (("\\" + protegido) if protegido[:1] in ("#", "!") else protegido)


def pegar_json(arquivo: Path) -> dict | None:
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


# ───────────── ganchos do v6 nas configurações ─────────────

def contar_ganchos(no) -> tuple[int, int]:
    """(ganchos do v6, ganchos de outros donos) num pedaço qualquer de configuração: todo objeto com `command`."""
    v6 = outros = 0
    if isinstance(no, dict):
        if isinstance(no.get("command"), str):
            return (1, 0) if GANCHO_DO_V6 in no["command"] else (0, 1)
        for valor in no.values():
            a, b = contar_ganchos(valor)
            v6, outros = v6 + a, outros + b
    elif isinstance(no, list):
        for item in no:
            a, b = contar_ganchos(item)
            v6, outros = v6 + a, outros + b
    return v6, outros


def tirar_ganchos_do_v6(no):
    """Devolve (o pedaço sem os ganchos cujo comando aponta para .delta-11/hooks/, quantos saíram). Grupo ou evento que fica vazio sai junto."""
    saiu = 0
    if isinstance(no, list):
        novos = []
        for item in no:
            if isinstance(item, dict) and isinstance(item.get("command"), str):
                if GANCHO_DO_V6 in item["command"]:
                    saiu += 1
                    continue
                novos.append(item)
            elif isinstance(item, dict) and isinstance(item.get("hooks"), list):
                interno, n = tirar_ganchos_do_v6(item["hooks"])
                saiu += n
                if item["hooks"] and not interno:
                    continue
                novos.append({**item, "hooks": interno})
            else:
                sub, n = tirar_ganchos_do_v6(item)
                saiu += n
                novos.append(sub)
        return novos, saiu
    if isinstance(no, dict):
        novo = {}
        for chave, valor in no.items():
            sub, n = tirar_ganchos_do_v6(valor)
            saiu += n
            if n and isinstance(valor, (list, dict)) and valor and not sub:
                continue
            novo[chave] = sub
        return novo, saiu
    return no, 0


# ───────────── a conversa aberta (três sinais; só leitura) ─────────────

def processos_do_lsof(destino: Path) -> list[tuple[str, str]]:
    """(hora de início, descrição) de cada processo claude, codex, kilo ou kimi com a pasta de trabalho dentro do projeto."""
    falso = os.environ.get("DELTA11_PULSO_LSOF_DE_MENTIRA")
    if falso:
        arquivo = Path(falso)
        linhas = arquivo.read_text(encoding="utf-8").splitlines() if arquivo.name == NOME_DO_LSOF_DE_MENTIRA and arquivo.is_file() else []
        if linhas and linhas[0] == MARCA_DO_LSOF_DE_MENTIRA:  # só o pulso, com o nome e a primeira linha certos
            inicio = next((l.split()[-1] for l in linhas if l.startswith("# inicio ")), "--:--")
            pid = next((l[1:] for l in linhas if l.startswith("p")), "?")
            return [(inicio, f"um processo (pid {pid}) tem a pasta de trabalho dentro do projeto")] \
                if any(l.startswith("n") and Path(l[1:]).resolve().is_relative_to(destino) for l in linhas) else []
    achados = []
    for programa in PROGRAMAS_DE_CONVERSA:
        feito = subprocess.run(["lsof", "-a", "-d", "cwd", "-c", programa, "-Fpn"], capture_output=True, text=True, errors="replace") if shutil.which("lsof") else None
        pid = ""
        for linha in (feito.stdout.splitlines() if feito else []):
            if linha.startswith("p"):
                pid = linha[1:]
            elif linha.startswith("n") and pid:
                try:
                    dentro_do_projeto = Path(linha[1:]).resolve().is_relative_to(destino)
                except OSError:
                    dentro_do_projeto = False
                if dentro_do_projeto:
                    inicio = subprocess.run(["ps", "-o", "lstart=", "-p", pid], capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"}).stdout.strip()
                    achado = re.search(r"\d\d:\d\d", inicio)
                    achados.append((achado.group(0) if achado else "--:--", f"um processo {programa} (pid {pid}) tem a pasta de trabalho dentro do projeto"))
    return achados


def vinculos_vivos(delta: Path) -> tuple[int, float] | None:
    """(quantos vínculos de agente sem `encerrado_em`, quando o arquivo mudou) se o arquivo mudou há menos de 30 minutos."""
    arquivo = delta / "ativacoes" / "agentes-sessao.json"
    dados = pegar_json(arquivo)
    if dados is None:
        return None
    chaves = dados.get("chaves") if isinstance(dados.get("chaves"), dict) else dados
    vivos = sum(1 for v in chaves.values() if isinstance(v, dict) and not v.get("encerrado_em"))
    mudou = arquivo.stat().st_mtime
    return (vivos, mudou) if vivos and time.time() - mudou < MINUTOS_DO_VINCULO * 60 else None


def sinais_do_trabalho(delta: Path) -> list[Path]:
    """O quadro e o diário do v6 (o histórico e o estado de cada agente, e o registro de atividade)."""
    memoria = delta / "memoria"
    return [p for p in [delta / "kanban.md", delta / "activity-log.md", *sorted(memoria.glob("*-historia.md")), *sorted(memoria.glob("*-estado.md"))] if p.is_file()]


def conversas_abertas(destino: Path) -> list[str]:
    delta = destino / ".delta-11"
    motivos = []
    for inicio, descricao in processos_do_lsof(destino):
        motivos.append(f"o projeto {destino.name} tem uma conversa aberta desde {inicio}; feche-a quando o trabalho dela terminar e rode de novo ({descricao}).")
    vivos = vinculos_vivos(delta)
    if vivos:
        motivos.append(f"o projeto {destino.name} tem uma conversa aberta desde {hora(vivos[1])}; feche-a quando o trabalho dela terminar e rode de novo "
                       f"(há {plural(vivos[0], 'vínculo de agente ainda aberto', 'vínculos de agente ainda abertos')} em .delta-11/ativacoes/agentes-sessao.json, mudado há menos de {MINUTOS_DO_VINCULO} minutos).")
    recentes = [p for p in sinais_do_trabalho(delta) if time.time() - p.stat().st_mtime < MINUTOS_DO_QUADRO * 60]
    if recentes:
        ultimo = max(recentes, key=lambda p: p.stat().st_mtime)
        minutos = int((time.time() - ultimo.stat().st_mtime) / 60)
        motivos.append(f"o projeto {destino.name} tem uma conversa aberta desde {hora(ultimo.stat().st_mtime)}; feche-a quando o trabalho dela terminar e rode de novo "
                       f"(o quadro mudou há {minutos} minuto(s): {ultimo.relative_to(delta).as_posix()}).")
    return motivos


# ───────────── o que o projeto tem (só leitura) ─────────────

def tem_o_v7(destino: Path) -> bool:
    versao = destino / ".delta-11" / "motor" / "VERSAO"
    return (versao.is_file() and '"delta11": "v7' in versao.read_text(encoding="utf-8", errors="replace")) or (destino / ".claude" / "hooks" / "delta-11").is_dir()


def tem_o_v6(destino: Path) -> bool:
    delta = destino / ".delta-11"
    return delta.is_dir() and any((delta / nome).exists() for nome in ("kanban.md", "operativos", "memoria", "protocolos", "hooks"))


def raiz_do_git(destino: Path) -> Path | None:
    topo = git(destino, "rev-parse", "--show-toplevel")
    return Path(topo.stdout.strip()).resolve() if topo.returncode == 0 and topo.stdout.strip() else None


def arquivos_soltos(destino: Path, com_git_proprio: bool) -> list[str]:
    """O que o `git add -A` levaria hoje: o que o git não conhece e não ignora (sem git próprio, tudo o que há na pasta)."""
    if com_git_proprio:
        return [a for a in git(destino, "ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0") if a]
    achados = []
    for raiz, subpastas, arquivos in os.walk(destino):
        subpastas[:] = [s for s in subpastas if s != ".git"]
        achados += [os.path.relpath(os.path.join(raiz, a), destino) for a in arquivos]
    return achados


def segredos_versionados(destino: Path) -> list[str]:
    return sorted(a for a in git(destino, "ls-files", "-z").stdout.split("\0") if a and e_segredo(a))


def copias_de_agentes(destino: Path) -> tuple[list[dict], list[str]]:
    """As cópias de agentes (git worktree) em .claude/worktrees/ e .kilo/worktrees/, e as pastas soltas ali que o git não conhece."""
    cadastradas, achadas = [], set()
    bloco: dict = {}
    saida = git(destino, "worktree", "list", "--porcelain").stdout + "\n\n"
    for linha in saida.splitlines():
        if not linha.strip():
            if bloco.get("worktree"):
                cadastradas.append(bloco)
            bloco = {}
            continue
        chave, _, valor = linha.partition(" ")
        bloco[chave] = valor or True
    copias = []
    for bloco in cadastradas:
        caminho = Path(bloco["worktree"])
        for familia in (".claude", ".kilo"):
            base = (destino / familia / "worktrees")
            try:
                caminho.resolve().relative_to(base.resolve())
            except ValueError:
                continue
            achadas.add(caminho.resolve())
            sumida = not caminho.exists()
            sujo = False if sumida else bool(git(caminho, "status", "--porcelain").stdout.strip())
            sha = bloco.get("HEAD") if isinstance(bloco.get("HEAD"), str) else ""
            ramo = bloco["branch"].removeprefix("refs/heads/") if isinstance(bloco.get("branch"), str) else None
            juntada = bool(sha) and git(destino, "merge-base", "--is-ancestor", sha, "HEAD").returncode == 0
            copias.append({"nome": caminho.name, "caminho": caminho, "familia": familia, "ramo": ramo, "sha": sha, "sumida": sumida, "suja": sujo,
                           "juntada": juntada, "travada": "locked" in bloco})
    soltas = []
    for familia in (".claude", ".kilo"):
        base = destino / familia / "worktrees"
        for pasta in sorted(base.iterdir()) if base.is_dir() else []:
            if pasta.is_dir() and pasta.resolve() not in achadas:
                soltas.append(f"{familia}/worktrees/{pasta.name}")
    return copias, soltas


def itens_da_raiz(destino: Path) -> list[tuple[str, str]]:
    """O que na raiz é do sistema antigo e vai para anterior-v6/raiz/ (caminho, descrição)."""
    itens = []
    claude = destino / "CLAUDE.md"
    if claude.is_file():
        texto = claude.read_text(encoding="utf-8", errors="replace")
        if "<!-- MOTOR:" in texto or "Δ-11" in texto or "DELTA-11" in texto:
            itens.append(("CLAUDE.md", "CLAUDE.md do v6"))
    agents = destino / "AGENTS.md"
    if agents.is_file() and re.search(r"ATIVAÇÃO DELTA-11|<!-- MOTOR:|operativo da Formação", agents.read_text(encoding="utf-8", errors="replace")[:4000]):
        itens.append(("AGENTS.md", "AGENTS.md do multiempresa"))
    if (destino / ".kilo" / "agent").is_dir():
        itens.append((".kilo/agent", f".kilo/agent/ ({plural(medir(destino / '.kilo' / 'agent')[1], 'arquivo', 'arquivos')})"))
    if (destino / ".kilo" / "permissoes.json").is_file():
        itens.append((".kilo/permissoes.json", ".kilo/permissoes.json"))
    if (destino / ".kimi-code").is_dir():
        itens.append((".kimi-code", ".kimi-code/"))
    return itens


def pasta_das_copias() -> Path:
    return Path(os.environ.get("DELTA11_COPIAS_ANTES_DO_V7") or (Path.home() / "Delta-11-copias-antes-do-v7")).expanduser().absolute()


def registro_do_sincronizador() -> Path:
    return Path(os.environ.get("DELTA11_REGISTRY") or (Path.home() / ".delta-11-registry.json")).expanduser()


def mesmo_caminho(entrada: str, destino: Path) -> bool:
    """O caminho do registro e a pasta, comparados com os acentos na mesma forma: o macOS pode guardar "é" como uma letra
    só (NFC) ou como "e" + acento (NFD), e as duas formas aparecem iguais na tela (o registro do sincronizador usa NFD)."""
    forma = lambda texto: unicodedata.normalize("NFC", texto)
    return forma(os.path.realpath(os.path.expanduser(entrada))) == forma(str(destino))


def esta_no_registro(destino: Path) -> bool:
    dados = pegar_json(registro_do_sincronizador())
    return bool(dados) and any(mesmo_caminho(entrada, destino) for entrada in entradas_do_registro(dados))


def entradas_do_registro(dados: dict) -> list[str]:
    return [e if isinstance(e, str) else e.get("path", "") for e in (dados.get("projects") or []) if isinstance(e, (str, dict))]


def nome_da_marca(destino: Path) -> str:
    existentes = set(git(destino, "tag").stdout.split()) if raiz_do_git(destino) == destino else set()
    nome, n = "antes-do-v7", 1
    while nome in existentes:
        n += 1
        nome = f"antes-do-v7-{n}"
    return nome


# ───────────── o ponto de partida (lido da .delta-11 antiga) ─────────────

def valor_do_campo(texto: str, campo: str) -> str:
    achado = re.search(rf"^\*\*{re.escape(campo)}:\*\*[ \t]*(.*)$", texto, re.MULTILINE)
    valor = achado.group(1).strip() if achado else ""
    return "" if (not valor or "[preenchido pelo ATLAS" in valor or re.fullmatch(r"\[[^\]]*\]", valor)) else valor


def curto(texto: str, palavras: int) -> str:
    partes = texto.split()
    return " ".join(partes[:palavras]) + (" …" if len(partes) > palavras else "")


def tarefas_do_quadro(texto: str) -> tuple[list[tuple[str, str]], int]:
    """(as tarefas abertas, na ordem FAZENDO, REVISÃO, A FAZER; quantas há no total)."""
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)
    secao, achadas = None, {"fazendo": [], "revisão": [], "a fazer": []}
    for linha in texto.splitlines():
        if linha.startswith("## "):
            titulo = linha.upper()
            secao = "fazendo" if "FAZENDO" in titulo else "revisão" if ("REVIS" in titulo) else "a fazer" if "A FAZER" in titulo else None
            continue
        if secao is None:
            continue
        item = None
        if linha.startswith("### "):
            item = linha[4:].strip()
        else:
            aberto = re.match(r"^\s*[-*]\s*\[[ ~?!]\]\s*(.+)$", linha)
            item = aberto.group(1).strip() if aberto else None
        if item and "CONCLU" not in item.upper() and "✅" not in item:
            achadas[secao].append(item)
    todas = [(s, i) for s in ("fazendo", "revisão", "a fazer") for i in achadas[s]]
    return todas, len(todas)


def decisoes_do_projeto(delta: Path) -> list[tuple[str, str]]:
    pasta = delta / "memoria" / "decisoes"
    itens = []
    for arquivo in sorted(pasta.rglob("*.md")) if pasta.is_dir() else []:
        if arquivo.name.lower() == "readme.md":
            continue
        titulo = next((l[2:].strip() for l in arquivo.read_text(encoding="utf-8", errors="replace").splitlines() if l.startswith("# ")), arquivo.stem)
        itens.append((arquivo.stem, re.sub(r"^ADR[-\w]*:\s*", "", titulo)))
    return itens


def avisos_do_time(delta: Path) -> tuple[list[tuple[str, str]], int]:
    """(os avisos próprios do projeto em gotchas.md, quantos eram só exemplo do modelo)."""
    arquivo = delta / "memoria" / "gotchas.md"
    if not arquivo.is_file():
        return [], 0
    blocos = re.split(r"^## ", arquivo.read_text(encoding="utf-8", errors="replace"), flags=re.MULTILINE)[1:]
    proprios, exemplos = [], 0
    for bloco in blocos:
        if "Semente do projeto" in bloco:
            exemplos += 1
            continue
        titulo = bloco.splitlines()[0].strip()
        evite = re.search(r"\*\*EVITE:\*\*\s*(.+)", bloco)
        proprios.append((re.sub(r"^G-\d+:\s*", "", titulo), evite.group(1).strip() if evite else ""))
    return proprios, exemplos


def montar_ponto_de_partida(delta: Path, data: str) -> tuple[str, dict]:
    """O PONTO-DE-PARTIDA.md (até 1.000 palavras) e os números dele, lidos da .delta-11 do v6 (onde ela estiver agora)."""
    core = (delta / "memoria" / "project-core.md")
    texto_core = core.read_text(encoding="utf-8", errors="replace") if core.is_file() else ""
    kanban = (delta / "kanban.md")
    texto_kanban = kanban.read_text(encoding="utf-8", errors="replace") if kanban.is_file() else ""
    campos = {c: valor_do_campo(texto_core, c) for c in ("Nome", "Descrição", "Usuários-alvo", "Problema que resolve")}
    fase = valor_do_campo(texto_kanban, "Fase atual")
    tarefas, total_tarefas = tarefas_do_quadro(texto_kanban)
    decisoes = decisoes_do_projeto(delta)
    avisos, exemplos = avisos_do_time(delta)
    numeros = {"fase_vazia": not fase, "descricao_vazia": not campos["Descrição"], "decisoes": len(decisoes), "avisos": len(avisos), "tarefas": total_tarefas}

    def escrever(limite_descricao: int, limite_tarefa: int, limite_decisao: int, maximo_decisoes: int) -> str:
        linhas = ["# Ponto de partida: o que o Delta-11 antigo deixou", "",
                  f"> Escrito pela passagem do v6 para o v7 em {data}, lendo a `.delta-11/` antiga (que está inteira nesta gaveta). Quem lê: o ATLAS, na primeira conversa, para começar a Luz pelo meio.", "",
                  "## O que o produto é", ""]
        for campo, rotulo in (("Nome", "Nome"), ("Descrição", "O que faz"), ("Usuários-alvo", "Para quem é"), ("Problema que resolve", "Problema que resolve")):
            valor = campos[campo]
            linhas.append(f"- {rotulo}: " + (curto(valor, limite_descricao) if valor else "o projeto antigo não tinha isto preenchido."))
        linhas += ["", "## Onde parou", "",
                   "Fase atual: " + (curto(fase, 30) if fase else "o quadro antigo não dizia a fase atual."), ""]
        if tarefas:
            linhas.append("Tarefas abertas no quadro antigo (em andamento, em revisão e a fazer):")
            for secao, item in tarefas[:15]:
                linhas.append(f"- ({secao}) {curto(item, limite_tarefa)}")
            if total_tarefas > 15:
                linhas.append(f"- (e mais {total_tarefas - 15} no quadro antigo, em `.delta-11/anterior-v6/kanban.md`)")
        else:
            linhas.append("O quadro antigo não tinha tarefas abertas.")
        linhas += ["", "## Decisões já tomadas", ""]
        if decisoes:
            for nome, titulo in decisoes[:maximo_decisoes]:
                linhas.append(f"- {nome}: {curto(titulo, limite_decisao)}")
            if len(decisoes) > maximo_decisoes:
                linhas.append(f"- (e mais {len(decisoes) - maximo_decisoes} em `.delta-11/anterior-v6/memoria/decisoes/`)")
        else:
            linhas.append("O projeto antigo não registrou decisões em `memoria/decisoes/`.")
        linhas += ["", "## Avisos que o time antigo deixou", ""]
        if avisos:
            for titulo, evite in avisos[:10]:
                linhas.append(f"- {curto(titulo, 14)}" + (f" (evite: {curto(evite, 18)})" if evite else ""))
            if len(avisos) > 10:
                linhas.append(f"- (e mais {len(avisos) - 10} em `.delta-11/anterior-v6/memoria/gotchas.md`)")
        else:
            linhas.append("O projeto antigo não deixou avisos próprios" + (f" (havia {plural(exemplos, 'aviso de exemplo do modelo', 'avisos de exemplo do modelo')}, ignorado)." if exemplos else "."))
        linhas += ["", "O Delta-11 antigo inteiro está nesta gaveta (`.delta-11/anterior-v6/`) e na marca `antes-do-v7` do git; para voltar atrás, peça ao Claude: "
                       "voltar este projeto para a marca antes-do-v7.", ""]
        return "\n".join(linhas)
    texto = escrever(90, 22, 18, 10**6)
    for apertado in ((60, 14, 12, 10**6), (40, 10, 9, 25), (30, 8, 8, 12), (20, 6, 6, 8)):
        if len(texto.split()) <= PALAVRAS_DO_PONTO_DE_PARTIDA:
            break
        texto = escrever(*apertado)
    return texto, numeros


# ───────────── o diagnóstico (nada é mudado aqui) ─────────────

def diagnosticar(destino: Path, opcoes: dict) -> dict:
    topo = raiz_do_git(destino)
    com_git = topo == destino
    fatos: dict = {"destino": destino, "nome": destino.name, "tem_v7": tem_o_v7(destino), "tem_v6": tem_o_v6(destino), "com_git": com_git, "topo_do_git": topo}
    if fatos["tem_v7"] or not fatos["tem_v6"]:
        return fatos
    delta = destino / ".delta-11"
    fatos["conversas"] = conversas_abertas(destino)
    quadro = delta / "kanban.md"
    fatos["ultimo_uso"] = max((p.stat().st_mtime for p in sinais_do_trabalho(delta)), default=None)
    fatos["itens_sem_commit"] = git(destino, "status", "--porcelain").stdout.splitlines() if com_git else []
    fatos["soltos"] = arquivos_soltos(destino, com_git)
    soltos_sem_pesados = [a for a in fatos["soltos"] if "node_modules" not in a.split("/")[:-1]]
    fatos["node_modules_soltos"] = len(soltos_sem_pesados) != len(fatos["soltos"])
    fatos["segredos"] = sorted(a for a in fatos["soltos"] if e_segredo(a))
    fatos["segredos_versionados"] = segredos_versionados(destino) if com_git else []
    fatos["pesados"] = sorted(a for a in soltos_sem_pesados if (destino / a).is_file() and (destino / a).lstat().st_size >= LIMITE_ARQUIVO_SOLTO)
    fatos["peso_dos_soltos"] = sum((destino / a).lstat().st_size for a in soltos_sem_pesados if os.path.lexists(destino / a) and not (destino / a).is_dir())
    copias, soltas = copias_de_agentes(destino) if com_git else ([], [])
    fatos["copias"], fatos["copias_soltas"] = copias, soltas
    for copia in copias:
        if com_git and not copia["sumida"]:
            soltos_da_copia = [a for a in git(copia["caminho"], "ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0") if a]
            copia["segredos"] = sorted(a for a in soltos_da_copia if e_segredo(a))
        else:
            copia["segredos"] = []
        copia["pendente"] = not copia["sumida"] and (copia["suja"] or not copia["juntada"])
    fatos["gaveta"] = medir(delta)
    fatos["raiz"] = itens_da_raiz(destino)
    ganchos = {}
    for relativo in CONFIGURACOES_COM_GANCHOS:
        arquivo = destino / relativo
        if arquivo.is_file():
            dados = pegar_json(arquivo)
            ganchos[relativo] = contar_ganchos(dados) if dados is not None else None
    fatos["ganchos"] = ganchos
    fatos["tamanho_da_pasta"] = medir(destino)[0] if not com_git else 0
    fatos["marca"] = nome_da_marca(destino)
    fatos["no_registro"] = esta_no_registro(destino)
    fatos["ponto"] = montar_ponto_de_partida(delta, datetime.date.today().isoformat())[1]
    return fatos


def recusas(fatos: dict, opcoes: dict, instalador) -> list[str]:
    destino: Path = fatos["destino"]
    if fatos["tem_v7"]:
        return [f"esta pasta já está no v7 ({destino}); para trocar o motor pela versão nova, use `instalar.py --atualizar`."]
    if not fatos["tem_v6"]:
        return [f"não achei o Delta-11 antigo nesta pasta ({destino} não tem uma .delta-11/ do v6); para uma pasta nova, instale sem --passar-do-v6."]
    motivos = list(fatos["conversas"])
    pendentes = [c for c in fatos["copias"] if c["pendente"]]
    if pendentes and not opcoes["guardar_copias"]:
        descricao = [f"{c['nome']} ({'mudança sem commit' if c['suja'] else ''}{' e ' if c['suja'] and not c['juntada'] else ''}"
                     f"{('ramo ' + c['ramo'] + ' não juntado ao principal') if not c['juntada'] and c['ramo'] else ('trabalho sem ramo, não juntado ao principal' if not c['juntada'] else '')})" for c in pendentes]
        motivos.append(f"há {plural(len(pendentes), 'cópia de agente com trabalho', 'cópias de agentes com trabalho')} que ainda não entrou no ramo principal: {'; '.join(descricao)}. "
                       "Rode de novo com --guardar-copias: o trabalho de cada cópia vai para um commit do ramo dela e as cópias vão para "
                       ".delta-11/anterior-v6/copias-de-agentes/ (nada é apagado).")
    if not fatos["com_git"] and not opcoes["criar_git"]:
        onde = f"o git que existe é o de cima, {fatos['topo_do_git']}" if fatos["topo_do_git"] else "não há git"
        motivos.append(f"a pasta não tem git próprio ({onde}); o v7 precisa de git, para a esteira e para a volta atrás. Rode de novo com --criar-git: antes de mudar qualquer coisa, "
                       f"a pasta inteira vira um .tar.gz em {pasta_das_copias()}, e o git próprio é criado com o primeiro commit \"estado antes do v7\".")
    copias_dir = pasta_das_copias()
    if not fatos["com_git"]:
        for varrido in VARRIDOS_PELOS_MONITORES:
            if copias_dir.is_relative_to((Path.home() / varrido).resolve()) or copias_dir.is_relative_to(Path.home() / varrido):
                motivos.append(f"a pasta das cópias ({copias_dir}) fica dentro de {Path.home() / varrido}, que o sincronizador e o monitor varrem; "
                               "o .tar.gz traria uma .delta-11/ solta para eles. Use DELTA11_COPIAS_ANTES_DO_V7 com outra pasta.")
                break
        if copias_dir.is_relative_to(destino):
            motivos.append(f"a pasta das cópias ({copias_dir}) fica dentro do próprio projeto.")
        elif not motivos:
            existe = copias_dir
            while not existe.exists():
                existe = existe.parent
            if shutil.disk_usage(existe).free < fatos["tamanho_da_pasta"] + 100 * 1024 * 1024:
                motivos.append(f"não há espaço livre para o .tar.gz em {copias_dir} ({tamanho(shutil.disk_usage(existe).free)} livres; a pasta tem {tamanho(fatos['tamanho_da_pasta'])}).")
    if fatos["pesados"]:
        motivos.append(f"há arquivo grande que o git não ignora e que iria para o histórico do projeto ({', '.join(f'{a} ({tamanho((destino / a).lstat().st_size)})' for a in fatos['pesados'][:4])}); "
                       "ponha-o no .gitignore do projeto (ou tire-o da pasta) e rode de novo.")
    if fatos["peso_dos_soltos"] > LIMITE_TOTAL_SOLTO:
        motivos.append(f"o que o git não conhece e não ignora soma {tamanho(fatos['peso_dos_soltos'])}, e iria para o histórico do projeto; ponha o que é pesado no .gitignore e rode de novo.")
    delta = destino / ".delta-11"
    if delta.is_symlink():
        motivos.append(".delta-11 é um link, não uma pasta; a passagem não sabe mover isso com segurança.")
    if (delta / "anterior-v6").exists():
        motivos.append("a gaveta já existe (.delta-11/anterior-v6/); a passagem não escreve por cima de uma gaveta. Veja o que há nela e tire-a do caminho.")
    if (destino / NOME_TEMPORARIO).exists():
        motivos.append(f"o nome temporário {NOME_TEMPORARIO} já existe nesta pasta (sobra de uma passagem que parou?); veja o que há nele e tire-o do caminho. A gaveta já existe ou está por existir.")
    for relativo in CONFIGURACOES_COM_GANCHOS:
        if (destino / relativo).is_file() and pegar_json(destino / relativo) is None:
            motivos.append(f"{relativo} existe mas não é JSON válido; conserte ou mova esse arquivo antes da passagem.")
    for copia in fatos["copias"]:
        if copia["sumida"]:
            continue
    return motivos


# ───────────── o ensaio ─────────────

def descrever_ensaio(fatos: dict, opcoes: dict, programa: str) -> str:
    destino: Path = fatos["destino"]
    copias = [c for c in fatos["copias"] if not c["sumida"]]
    pendentes = [c for c in copias if c["pendente"]]
    quando = f"último uso do quadro: {data_e_hora(fatos['ultimo_uso'])}" if fatos["ultimo_uso"] else "sem quadro"
    cabeca = f"nenhuma conversa aberta ({quando})"
    sobre_copias = plural(len(copias), "cópia de agente", "cópias de agentes") + (f", {len(pendentes)} com trabalho que seria guardado em ramo" if pendentes else ", sem trabalho pendente") if copias else "nenhuma cópia de agente"
    if fatos["copias_soltas"]:
        sobre_copias += f"; {plural(len(fatos['copias_soltas']), 'pasta solta', 'pastas soltas')} em worktrees/ que o git não conhece ficam onde estão"
    git_proprio = "sim" if fatos["com_git"] else "não (seria criado, por causa de --criar-git)"
    guardar = []
    if fatos["com_git"]:
        guardar.append(f"commit \"estado antes do v7\" com {plural(len(fatos['itens_sem_commit']), 'item sem commit', 'itens sem commit')}")
    else:
        guardar.append(f"cópia compactada da pasta inteira ({tamanho(fatos['tamanho_da_pasta'])}) em {pasta_das_copias()}/{destino.name}-<data>.tar.gz, antes de qualquer mudança")
        guardar.append(f"criaria o git próprio e o primeiro commit \"estado antes do v7\" com {plural(len(fatos['soltos']), 'arquivo', 'arquivos')}")
        if fatos["topo_do_git"]:
            guardar.append(f"o git maior ({fatos['topo_do_git']}) passaria a ver a pasta como repositório aninhado")
    if copias and opcoes["guardar_copias"]:
        guardar.append(f"o trabalho de {plural(len(pendentes), 'cópia', 'cópias')} iria para commits e ramos delas")
    guardar.append(f"marca {fatos['marca']}")
    segredos = ", ".join(fatos["segredos"]) or "nenhum"
    for copia in copias:
        if copia["segredos"] and opcoes["guardar_copias"]:
            segredos += f" (na cópia {copia['nome']}: {', '.join(copia['segredos'])}, que não entrariam no commit dela)"
    guardar.append(f"segredos que passariam a ser ignorados: {segredos}")
    if fatos["segredos_versionados"]:
        guardar.append(f"ATENÇÃO: já estavam no git, desde antes: {', '.join(fatos['segredos_versionados'])} (troque essas chaves)")
    bytes_, arquivos = fatos["gaveta"]
    ganchos = fatos["ganchos"]
    sobre_ganchos = []
    for relativo in CONFIGURACOES_COM_GANCHOS:
        if ganchos.get(relativo) is not None and relativo in ganchos:
            v6, dono = ganchos[relativo]
            if v6 or relativo == ".claude/settings.json":
                sobre_ganchos.append(f"{plural(v6, 'gancho do v6 sairia', 'ganchos do v6 sairiam')} de {relativo}"
                                     + (f"; {plural(dono, 'gancho do dono ficaria', 'ganchos do dono ficariam').replace(' ficaria', ' ficaria').replace('gancho do dono ficaria', 'gancho do dono ficaria')}" if dono else "; nenhum gancho do dono"))
    raiz = [descricao for _, descricao in fatos["raiz"]]
    gaveta = [f".delta-11/ antiga ({tamanho(bytes_)}, {numero(arquivos)} arquivos) → .delta-11/anterior-v6/ (fora do git)"]
    if raiz:
        gaveta.append(f"{' e '.join(raiz)} → anterior-v6/raiz/")
    if copias and opcoes["guardar_copias"]:
        gaveta.append(f"{plural(len(copias), 'cópia de agente', 'cópias de agentes')} → anterior-v6/copias-de-agentes/ (git worktree move)")
    gaveta += sobre_ganchos
    ponto = fatos["ponto"]
    sobre_ponto = (f"\"Fase atual\" {'vazia' if ponto['fase_vazia'] else 'preenchida'} no quadro; descrição {'não preenchida' if ponto['descricao_vazia'] else 'preenchida'}; "
                   f"{plural(ponto['decisoes'], 'decisão', 'decisões')}; {plural(ponto['avisos'], 'aviso', 'avisos')}; {plural(ponto['tarefas'], 'tarefa aberta', 'tarefas abertas')}")
    registro = (f"a pasta sairia da lista do sincronizador antigo ({registro_do_sincronizador()})" if fatos["no_registro"]
                else f"a pasta não está na lista do sincronizador antigo ({registro_do_sincronizador()}); nada a tirar")
    linhas = [f"ENSAIO — nada foi mudado. A passagem de {destino.name} para o v7 faria:",
              f"  1. Conferências: {cabeca}; {sobre_copias}; git próprio: {git_proprio}.",
              f"  2. Guardar: {'; '.join(guardar)}.",
              f"  3. Gaveta: {'; '.join(gaveta)}.",
              f"  4. Instalar o v7 (programa: {programa}); a conferência dos pulsos da trava, da tela e da esteira roda só na passagem de verdade.",
              f"  5. Ponto de partida: {sobre_ponto}.",
              "  6. Commit \"passagem do Delta-11 v6 para o v7\"; git status limpo (a gaveta é ignorada).",
              f"  7. Registro: {registro}.",
              "  Para fazer de verdade: rode o mesmo comando sem --ensaio."]
    return "\n".join(linhas)


# ───────────── a volta (o que muda de lugar é registrado para poder voltar) ─────────────

class Desfazedor:
    def __init__(self) -> None:
        self.passos: list[tuple[str, object]] = []

    def registrar(self, descricao: str, funcao) -> None:
        self.passos.append((descricao, funcao))

    def desfazer(self) -> list[str]:
        problemas = []
        for descricao, funcao in reversed(self.passos):
            try:
                funcao()
            except Exception as erro:  # um passo que não volta não pode impedir os outros
                problemas.append(f"{descricao}: {type(erro).__name__}: {erro}")
        return problemas


def ponto_de_falha(passo: str) -> None:
    if os.environ.get("DELTA11_PULSO_PASSAGEM_FALHAR_DEPOIS_DE") == passo:
        raise Falhou(f"falha de mentira depois do passo '{passo}' (variável DELTA11_PULSO_PASSAGEM_FALHAR_DEPOIS_DE, só do pulso)")


def mover(origem: Path, destino: Path, volta: Desfazedor) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    os.rename(origem, destino)
    volta.registrar(f"devolver {destino.name} a {origem}", lambda: os.rename(destino, origem) if destino.exists() and not os.path.lexists(origem) else None)


def copiar_original(origem: Path, destino: Path, volta: Desfazedor) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)

    def apagar_a_copia() -> None:
        destino.unlink(missing_ok=True)
        pasta = destino.parent
        while pasta.name and pasta != pasta.parent:
            try:
                pasta.rmdir()  # só some se ficou vazia: o que é de outro nunca é tocado
            except OSError:
                break
            pasta = pasta.parent
    volta.registrar(f"tirar a cópia do original {destino.name}", apagar_a_copia)


def devolver_a_gaveta(destino: Path) -> None:
    """Desfaz o passo da gaveta: a .delta-11/ nova (só do que a instalação criou) sai, a antiga volta ao lugar."""
    delta, gaveta, temporario = destino / ".delta-11", destino / GAVETA, destino / NOME_TEMPORARIO
    if not destino.name or delta.name != ".delta-11":
        raise Falhou("caminho da .delta-11 vazio ou estranho; não toquei em nada")
    if gaveta.exists() and not temporario.exists():
        os.rename(gaveta, temporario)
    if not temporario.exists():
        return
    guarda = delta / "motor" / "instrucoes-anteriores"  # o que o instalador guardou de outro sistema volta ao lugar de onde saiu
    for nome in CANDIDATOS_A_INSTRUCAO_ANTIGA:
        guardado = guarda / nome.replace("/", "_").lstrip(".")
        if guardado.exists() and not os.path.lexists(destino / nome):
            (destino / nome).parent.mkdir(parents=True, exist_ok=True)
            os.rename(guardado, destino / nome)
    if guarda.is_dir() and any(guarda.iterdir()):
        raise Falhou(f"sobrou algo em {guarda} que não sei devolver; a .delta-11 antiga está em {temporario}")
    for acrescentada in ("raiz", "copias-de-agentes"):  # pastas que a passagem criou dentro da gaveta; já devolveram o que tinham
        pasta = temporario / acrescentada
        if pasta.is_dir():
            for raiz_, _, arquivos in os.walk(pasta):
                if arquivos:
                    raise Falhou(f"sobrou arquivo em {pasta} que não sei devolver; a .delta-11 antiga está em {temporario}")
            for raiz_, subpastas, _ in sorted(os.walk(pasta), key=lambda t: -len(t[0])):
                os.rmdir(raiz_)
    if delta.exists():
        shutil.rmtree(delta)  # a .delta-11 NOVA, criada pela instalação (a antiga está a salvo no nome temporário)
    os.rename(temporario, delta)


# ───────────── a passagem ─────────────

def guardar_estado_antes(destino: Path, fatos: dict, opcoes: dict, volta: Desfazedor, relato: dict) -> None:
    """Passo 2: tudo o que protege o projeto, antes de qualquer mudança de lugar."""
    com_git = fatos["com_git"]
    originais = {r: (destino / r).read_bytes() if (destino / r).is_file() else None for r in ORIGINAIS_GUARDADOS}
    relato["originais"] = originais
    if not com_git:
        copias_dir = pasta_das_copias()
        copias_dir.mkdir(parents=True, exist_ok=True)
        agora = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        arquivo, n = copias_dir / f"{destino.name}-{agora}.tar.gz", 1
        while arquivo.exists():
            n += 1
            arquivo = copias_dir / f"{destino.name}-{agora}-{n}.tar.gz"
        feito = subprocess.run(["tar", "-czf", str(arquivo), "-C", str(destino.parent), destino.name], capture_output=True, text=True,
                               env={**os.environ, "COPYFILE_DISABLE": "1"})
        esperado = 1 + sum(len(s) + sum(1 for a in arq if not stat.S_ISSOCK(os.lstat(os.path.join(r, a)).st_mode)) for r, s, arq in os.walk(destino))
        lidos = subprocess.run(["tar", "-tzf", str(arquivo)], capture_output=True, text=True)
        if feito.returncode != 0 or lidos.returncode != 0 or len(lidos.stdout.splitlines()) != esperado:
            arquivo.unlink(missing_ok=True)  # um .tar.gz que não confere seria uma falsa rede de segurança
            raise Falhou(f"a cópia compactada não conferiu (esperava {esperado} itens, o .tar.gz tem {len(lidos.stdout.splitlines())}): {feito.stderr.strip()[:200]}")
        relato["tar"], relato["tar_itens"] = arquivo, esperado
    linhas_novas = [linha_de_ignorar(a) for a in fatos["segredos"]]
    if not com_git:
        linhas_novas = ["node_modules/", *LINHAS_DE_SEGREDO, *linhas_novas]
    elif fatos["node_modules_soltos"]:
        linhas_novas = ["node_modules/", *linhas_novas]
    linhas_novas.append(".claude/worktrees/")  # as cópias de agentes nunca entram no commit do projeto (são repositórios por dentro)
    if (destino / ".kilo" / "worktrees").is_dir():
        linhas_novas.append(".kilo/worktrees/")
    escrever_no_gitignore(destino, linhas_novas, "Delta-11: antes da passagem para o v7", originais[".gitignore"], volta)
    if not com_git:
        feito = git(destino, "init", "-q", "-b", "main")
        if feito.returncode != 0:
            raise Falhou(f"não consegui criar o git próprio: {feito.stderr.strip()}")
        relato["git_criado"] = True
    for segredo in fatos["segredos"]:
        if git(destino, "check-ignore", "-q", segredo).returncode != 0:
            raise Falhou(f"o segredo {segredo} continua sem estar ignorado depois de eu o pôr no .gitignore; nada foi commitado")
    relato["segredos"] = list(fatos["segredos"])
    adicionado = git(destino, "add", "-A", "--", ".")
    if adicionado.returncode != 0:
        raise Falhou(f"o git não aceitou os arquivos do projeto: {adicionado.stderr.strip()[:300]}")
    tirar_do_indice_o_que_nao_entra(destino, fatos["segredos_versionados"])
    entrou = [a for a in git(destino, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if a and e_segredo(a) and a not in fatos["segredos_versionados"]]
    if entrou:
        raise Falhou(f"um segredo ia entrar no commit ({', '.join(entrou[:3])}); parei antes de commitar")
    tem_commit = git(destino, "rev-parse", "-q", "--verify", "HEAD").returncode == 0
    tem_algo = git(destino, "diff", "--cached", "--quiet").returncode != 0
    if tem_algo or not tem_commit:
        feito = git_que_grava(destino, "commit", "-q", "--no-verify", *([] if tem_algo else ["--allow-empty"]), "-m", "estado antes do v7\n\nDelta-11: instalado")
        if feito.returncode != 0:
            raise Falhou(f"o git não guardou o estado antes do v7: {feito.stderr.strip()[:300]}")
        relato["commit_antes"] = git(destino, "rev-parse", "--short", "HEAD").stdout.strip()
    else:
        relato["commit_antes"] = None
    relato["copias_guardadas"] = []
    if opcoes["guardar_copias"]:
        guardar_as_copias(destino, fatos, relato)
    marca = nome_da_marca(destino)
    feito = git_que_grava(destino, "tag", marca)
    if feito.returncode != 0:
        raise Falhou(f"o git não criou a marca {marca}: {feito.stderr.strip()[:200]}")
    relato["marca"], relato["marca_em"] = marca, git(destino, "rev-parse", "--short", "HEAD").stdout.strip()


def tirar_do_indice_o_que_nao_entra(pasta: Path, _sobra: list[str]) -> None:
    """Depois do `git add -A`: o que está pronto para o commit e é segredo ou é de node_modules sai do índice (o que o git já guardava volta ao que era)."""
    prontos = [a for a in git(pasta, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if a]
    fora = [a for a in prontos if e_segredo(a) or "node_modules" in a.split("/")[:-1]]
    tem_commit = git(pasta, "rev-parse", "-q", "--verify", "HEAD").returncode == 0
    for inicio in range(0, len(fora), 200):
        lote = [f":(literal){a}" for a in fora[inicio:inicio + 200]]
        if tem_commit:
            git(pasta, "reset", "-q", "--", *lote)
        else:
            git(pasta, "rm", "-q", "--cached", "-r", "-f", "--ignore-unmatch", "--", *lote)


def escrever_no_gitignore(destino: Path, linhas: list[str], cabecalho: str, original: bytes | None, volta: Desfazedor) -> None:
    arquivo = destino / ".gitignore"
    atuais = original.decode("utf-8", errors="replace").splitlines() if original is not None else []
    faltam = [l for l in dict.fromkeys(linhas) if l not in atuais]
    if not faltam:
        return
    texto = ((original or b"").decode("utf-8", errors="replace"))
    texto += ("\n" if texto and not texto.endswith("\n") else "") + (("\n" if atuais else "") + f"# {cabecalho}\n" + "\n".join(faltam) + "\n")
    arquivo.write_text(texto, encoding="utf-8")
    volta.registrar("restaurar o .gitignore",
                    lambda: arquivo.write_bytes(original) if original is not None else arquivo.unlink(missing_ok=True))


def guardar_as_copias(destino: Path, fatos: dict, relato: dict) -> None:
    for copia in fatos["copias"]:
        if copia["sumida"]:
            continue
        pasta, nome = copia["caminho"], copia["nome"]
        ramo = copia["ramo"]
        existentes = set(git(destino, "branch", "--format=%(refname:short)").stdout.split())
        if not ramo and (copia["suja"] or not copia["juntada"]):
            ramo, n = f"copia-antes-do-v7/{nome}", 1
            while ramo in existentes:
                n += 1
                ramo = f"copia-antes-do-v7/{nome}-{n}"
            if copia["suja"]:
                feito = git_que_grava(pasta, "switch", "-q", "-c", ramo)
            else:
                feito = git_que_grava(pasta, "branch", ramo, "HEAD")
            if feito.returncode != 0:
                raise Falhou(f"não consegui criar o ramo {ramo} para a cópia {nome}: {feito.stderr.strip()[:200]}")
        commit = None
        if copia["suja"]:
            adicionado = git(pasta, "add", "-A", "--", ".")
            if adicionado.returncode != 0:
                raise Falhou(f"o git não aceitou o trabalho da cópia {nome}: {adicionado.stderr.strip()[:200]}")
            tirar_do_indice_o_que_nao_entra(pasta, [])
            if any(e_segredo(a) for a in git(pasta, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if a):
                raise Falhou(f"um segredo ia entrar no commit da cópia {nome}; parei antes de commitar")
            if git(pasta, "diff", "--cached", "--quiet").returncode != 0:
                feito = git_que_grava(pasta, "commit", "-q", "--no-verify", "-m", "trabalho da cópia guardado antes do v7\n\nDelta-11: instalado")
                if feito.returncode != 0:
                    raise Falhou(f"o git não guardou o trabalho da cópia {nome}: {feito.stderr.strip()[:200]}")
                commit = git(pasta, "rev-parse", "--short", "HEAD").stdout.strip()
        relato["copias_guardadas"].append({"nome": nome, "ramo": ramo or f"(detached em {copia['sha'][:7]}, já alcançável por um ramo)", "commit": commit,
                                           "segredos_fora": copia["segredos"], "familia": copia["familia"], "caminho": pasta})


def levar_para_a_gaveta(destino: Path, fatos: dict, opcoes: dict, volta: Desfazedor, relato: dict) -> None:
    """Passo 3: a .delta-11/ antiga vira a gaveta (renomear, criar a nova, renomear para dentro) e o que era do sistema antigo vai junto."""
    delta, temporario, gaveta = destino / ".delta-11", destino / NOME_TEMPORARIO, destino / GAVETA
    os.rename(delta, temporario)
    try:
        delta.mkdir()
        os.rename(temporario, gaveta)
    except Exception:
        if gaveta.exists() and not temporario.exists():
            os.rename(gaveta, temporario)
        if delta.is_dir() and not any(delta.iterdir()):
            delta.rmdir()
        if temporario.exists() and not delta.exists():
            os.rename(temporario, delta)
        raise
    volta.registrar("devolver a .delta-11 antiga ao lugar", lambda: devolver_a_gaveta(destino))
    for relativo, original in relato["originais"].items():  # o original de cada arquivo que a passagem muda no lugar fica na gaveta
        if original is not None:
            alvo = gaveta / "raiz" / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(original)
            volta.registrar(f"tirar a cópia do original {relativo}", lambda a=alvo: apagar_e_podar(a))
    levados = []
    for relativo, descricao in fatos["raiz"]:
        mover(destino / relativo, gaveta / "raiz" / relativo, volta)
        levados.append(descricao)
    relato["raiz"] = levados
    relato["ganchos_tirados"] = []
    for relativo in CONFIGURACOES_COM_GANCHOS:
        arquivo = destino / relativo
        if not arquivo.is_file():
            continue
        antigo = arquivo.read_bytes()
        dados = json.loads(antigo.decode("utf-8"))
        novo, saiu = tirar_ganchos_do_v6(dados)
        if saiu:
            comandos = sorted(_comandos(dados) - _comandos(novo))
            arquivo.write_text(json.dumps(novo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            volta.registrar(f"devolver {relativo} como era", lambda a=arquivo, b=antigo: a.write_bytes(b))
            relato["ganchos_tirados"].append((relativo, saiu, comandos, contar_ganchos(novo)[1]))
        if relativo == ".claude/settings.local.json" or relativo == ".claude/settings.json":
            relato.setdefault("configuracoes_que_existiam", []).append(relativo)
    relato["configuracoes_que_existiam"] = [r for r in CONFIGURACOES_COM_GANCHOS if (destino / r).is_file() or relato["originais"].get(r) is not None]
    if opcoes["guardar_copias"] and fatos["copias"]:
        destino_das_copias = gaveta / "copias-de-agentes"
        usados = set()
        for copia in relato["copias_guardadas"]:
            nome = copia["nome"] if copia["nome"] not in usados else f"{copia['familia'].strip('.')}-{copia['nome']}"
            usados.add(nome)
            novo = destino_das_copias / nome
            antigo = copia["caminho"]
            destino_das_copias.mkdir(parents=True, exist_ok=True)
            feito = git(destino, "worktree", "move", str(antigo), str(novo))
            if feito.returncode != 0 and "locked" in feito.stderr:
                feito = git(destino, "worktree", "move", "--force", "--force", str(antigo), str(novo))
            if feito.returncode != 0:
                raise Falhou(f"o git não moveu a cópia {copia['nome']} para a gaveta: {feito.stderr.strip()[:300]}")
            copia["novo_caminho"] = novo
            volta.registrar(f"devolver a cópia {copia['nome']} ao lugar",
                            lambda n=novo, a=antigo: (a.parent.mkdir(parents=True, exist_ok=True), git(destino, "worktree", "move", "--force", "--force", str(n), str(a))))


def _comandos(no) -> set[str]:
    achados: set[str] = set()
    if isinstance(no, dict):
        if isinstance(no.get("command"), str):
            achados.add(no["command"])
        for v in no.values():
            achados |= _comandos(v)
    elif isinstance(no, list):
        for item in no:
            achados |= _comandos(item)
    return achados


def apagar_e_podar(arquivo: Path) -> None:
    arquivo.unlink(missing_ok=True)
    pasta = arquivo.parent
    while pasta.name and pasta != pasta.parent:
        try:
            pasta.rmdir()
        except OSError:
            break
        pasta = pasta.parent


def instalar_o_v7(destino: Path, programa: str, caminho: str, instalador, volta: Desfazedor, relato: dict) -> list[str]:
    """Passo 4: o caminho normal do instalador, com tudo desfeito se ele recusar no meio."""
    snapshot = {r: ((destino / r).read_bytes(), (destino / r).stat().st_mode) if (destino / r).is_file() else None
                for r in (".claude/settings.json", ".claude/settings.local.json", "CLAUDE.md", ".gitignore", ".worktreeinclude", "esteira", "esteira-comandos.txt",
                          ".claude/settings.json.antes-do-delta-11")}
    agentes_antes = {p.name for p in (destino / ".claude" / "agents").glob("*")} if (destino / ".claude" / "agents").is_dir() else None
    tinha = {c: (destino / c).exists() for c in (".claude", ".claude/hooks", ".claude/hooks/delta-11", ".claude/agents")}

    def desfazer_a_instalacao() -> None:
        for relativo, guardado in snapshot.items():
            alvo = destino / relativo
            if guardado is None:
                alvo.unlink(missing_ok=True)
            else:
                alvo.write_bytes(guardado[0])
                alvo.chmod(stat.S_IMODE(guardado[1]))
        agentes = destino / ".claude" / "agents"
        if agentes.is_dir():
            for agente in agentes.glob("*"):
                if agentes_antes is None or agente.name not in agentes_antes:
                    agente.unlink()
            if agentes_antes is None:
                agentes.rmdir()
        if not tinha[".claude/hooks/delta-11"] and (destino / ".claude/hooks/delta-11").exists():
            shutil.rmtree(destino / ".claude/hooks/delta-11")  # criada pela instalação (não existia antes)
        for relativo in (".claude/hooks", ".claude"):
            if not tinha[relativo]:
                try:
                    (destino / relativo).rmdir()
                except OSError:
                    pass
    volta.registrar("desfazer a instalação do v7", desfazer_a_instalacao)
    try:
        instalador.preparar_git(destino)
        instalador.guardar_instrucoes_antigas(destino)
        quantos = instalador.instalar_agentes(destino, False)
        instalador.instalar_ganchos_e_modelos(destino)
        da_esteira = instalador.instalar_esteira(destino)
        instalador.juntar_configuracao(destino)
        instalador.juntar_configuracao_local(destino, caminho)
        # A passagem instala com a IA padrão (o Claude, que não escreve nada na configuração local); outra IA, depois, com trocar-ia.py.
        instalador.marcar_versao(destino, False, programa, instalador.perfil_de_ia().PERFIL_PADRAO)
    except SystemExit as saida:
        raise Falhou("o instalador do v7 recusou a instalação (o motivo está acima)") from saida
    relato["agentes"] = quantos
    return da_esteira


def ignorar_a_gaveta(destino: Path) -> None:
    """A gaveta fica fora do git, numa linha DEPOIS das exceções `!.delta-11/` do v7 (no .gitignore vale a última linha que bate)."""
    arquivo = destino / ".gitignore"
    texto = arquivo.read_text(encoding="utf-8") if arquivo.is_file() else ""
    linhas = [".delta-11/anterior-v6/"]
    if (destino / ".kilo" / "worktrees").is_dir():
        linhas.append(".kilo/worktrees/")
    atuais = texto.splitlines()
    ultima_excecao = max((i for i, l in enumerate(atuais) if l.startswith("!.delta-11")), default=-1)
    for linha in linhas:
        if linha not in atuais[ultima_excecao + 1:]:
            texto += ("\n" if texto and not texto.endswith("\n") else "") + ("\n# Delta-11 v7: a gaveta do v6 fica fora do git (a marca antes-do-v7 guarda o que estava no git)\n" if linha == linhas[0] else "") + linha + "\n"
    arquivo.write_text(texto, encoding="utf-8")
    prova = git(destino, "check-ignore", "-v", ".delta-11/anterior-v6/PONTO-DE-PARTIDA.md").stdout
    if "\t" not in prova or prova.split("\t")[0].split(":")[-1] != ".delta-11/anterior-v6/":
        raise Falhou(f"o .gitignore não ignora a gaveta (o git diz: {prova.strip() or 'nada'})")


def commit_da_passagem(destino: Path, da_esteira: list[str], instalador, fatos: dict) -> str:
    """Passo 7: tudo o que mudou entra num commit só (o que o git ignora, a gaveta inclusive, fica de fora)."""
    # -f: o motor entra mesmo numa pasta que já ignorava .claude/ (o que é de fora do git continua fora pelo .gitignore do Delta-11), como no instalador.
    caminhos = [c for c in (".gitignore", "CLAUDE.md", ".worktreeinclude", ".claude/agents", ".claude/hooks/delta-11", ".claude/settings.json", *da_esteira) if (destino / c).exists()]
    adicionado = git(destino, "add", "-A", "-f", "--", *caminhos)
    if adicionado.returncode != 0:
        raise Falhou(f"o git não aceitou os arquivos instalados: {adicionado.stderr.strip()[:300]}")
    git(destino, "add", "-A")
    git(destino, "reset", "-q", "--", ".claude/hooks/delta-11/vivos", ".claude/hooks/delta-11/__pycache__", ".claude/hooks/delta-11/motores/__pycache__")
    versionados = fatos["segredos_versionados"]
    if versionados:
        git(destino, "reset", "-q", "--", *versionados)  # um segredo que já estava no git não leva o valor novo para o histórico
    entrou = [a for a in git(destino, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if a and e_segredo(a) and a not in versionados]
    if entrou:
        raise Falhou(f"um segredo ia entrar no commit da passagem ({', '.join(entrou[:3])}); parei antes de commitar")
    feito = git_que_grava(destino, "commit", "-q", "--no-verify", "--allow-empty", "-m", "passagem do Delta-11 v6 para o v7\n\nDelta-11: instalado")
    if feito.returncode != 0:
        raise Falhou(f"o git não guardou a passagem: {feito.stderr.strip()[:300]}")
    return git(destino, "rev-parse", "--short", "HEAD").stdout.strip()


def tirar_do_registro(destino: Path) -> str:
    caminho = registro_do_sincronizador()
    if not caminho.is_file():
        return f"o registro {caminho} não existe; nada a tirar"
    texto = caminho.read_text(encoding="utf-8")
    dados = json.loads(texto)
    if not isinstance(dados, dict) or not isinstance(dados.get("projects"), list):
        return f"o registro {caminho} não tem a lista `projects`; deixei como está"
    antes = len(dados["projects"])
    dados["projects"] = [e for e in dados["projects"] if not (isinstance(e, (str, dict)) and mesmo_caminho(e if isinstance(e, str) else e.get("path", ""), destino))]
    if len(dados["projects"]) == antes:
        return f"a pasta não estava na lista do registro {caminho}"
    indentacao = re.search(r"\n( +)\"", texto)
    novo = json.dumps(dados, ensure_ascii=False, indent=len(indentacao.group(1)) if indentacao else 2) + ("\n" if texto.endswith("\n") else "")
    temporario = caminho.with_name(caminho.name + ".passagem-do-v6")
    temporario.write_text(novo, encoding="utf-8")
    temporario.chmod(stat.S_IMODE(caminho.stat().st_mode))
    os.replace(temporario, caminho)
    return f"tirei a pasta da lista `projects` do registro {caminho} (o resto do arquivo ficou igual)"


def receita_de_volta(destino: Path, relato: dict) -> str:
    q = shlex.quote
    if relato.get("git_criado"):
        tar = relato["tar"]
        return ("# A pasta não tinha git próprio: a volta é a cópia compactada de antes da passagem. Rode de dentro da pasta de cima.\n"
                f"cd {q(str(destino.parent))}\nmv {q(destino.name)} {q(destino.name + '-v7-guardado')}\ntar -xzf {q(str(tar))} -C {q(str(destino.parent))}\n"
                f"# a pasta {destino.name} volta como era; a versão do v7 fica em {destino.name}-v7-guardado (nada é apagado)\n")
    comandos = ["set -e"]
    pais = sorted({Path(Path(c["caminho"]).relative_to(destino)).parent.as_posix() for c in relato["copias_guardadas"] if "novo_caminho" in c})
    comandos += [f"mkdir -p {q(p)}" for p in pais]
    for copia in relato["copias_guardadas"]:
        if "novo_caminho" in copia:
            comandos.append(f"git worktree move {q(Path(copia['novo_caminho']).relative_to(destino).as_posix())} {q(Path(copia['caminho']).relative_to(destino).as_posix())}")
    comandos += ["mv .delta-11 .delta-11-v7-guardado", f"git reset --hard {relato['marca']}"]
    sobrescrever = [r for r in ORIGINAIS_GUARDADOS if relato["originais"].get(r) is not None]
    novos_na_volta = [r for r in (".claude/settings.local.json",) if relato["originais"].get(r) is None]
    comandos.append("python3 - <<'PY'")
    comandos += [
        "import os, shutil",
        "gaveta = '.delta-11-v7-guardado/anterior-v6'",
        f"sobrescrever = {sobrescrever!r}",
        "def levar(origem, destino, por_cima=()):",
        "    for nome in sorted(os.listdir(origem)):",
        "        o, d = os.path.join(origem, nome), os.path.join(destino, nome)",
        "        if os.path.isdir(o) and not os.path.islink(o):",
        "            os.makedirs(d, exist_ok=True)",
        "            levar(o, d, por_cima)",
        "        elif d.removeprefix('./') in por_cima or not os.path.lexists(d):",
        "            os.makedirs(os.path.dirname(d) or '.', exist_ok=True)",
        "            shutil.copy2(o, d, follow_symlinks=False)",
        "for nome in os.listdir(gaveta):",
        "    if nome not in ('raiz', 'copias-de-agentes', 'PONTO-DE-PARTIDA.md', 'RELATO-DA-PASSAGEM.md'):",
        "        o, d = os.path.join(gaveta, nome), os.path.join('.delta-11', nome)",
        "        if os.path.isdir(o) and not os.path.islink(o):",
        "            os.makedirs(d, exist_ok=True)",
        "            levar(o, d)",
        "        elif not os.path.lexists(d):",
        "            shutil.copy2(o, d, follow_symlinks=False)",
        "if os.path.isdir(gaveta + '/raiz'):",
        "    levar(gaveta + '/raiz', '.', sobrescrever)",
        "PY"]
    for relativo in novos_na_volta:
        comandos.append(f"[ ! -e {q(relativo)} ] || mv {q(relativo)} {q(relativo + '.do-v7')}   # não existia antes da passagem")
    comandos.append(f"# o v7 fica em .delta-11-v7-guardado (nada é apagado); a passagem está no commit {relato['commit_da_passagem']}, que o git ainda guarda")
    return "\n".join(comandos) + "\n"


def escrever_relato(destino: Path, fatos: dict, opcoes: dict, relato: dict, avisos: list[str], registro: str) -> str:
    gaveta_bytes, gaveta_arquivos = fatos["gaveta"]
    linhas = [f"# Relato da passagem de {destino.name} do Delta-11 v6 para o v7", "",
              f"Feita em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}. Pasta: `{destino}`.", "", "## O que foi guardado e onde", ""]
    if relato.get("git_criado"):
        linhas.append(f"- A pasta não tinha git próprio: antes de mudar qualquer coisa, a pasta inteira foi guardada em `{relato['tar']}` ({numero(relato['tar_itens'])} itens, conferidos).")
        linhas.append("- Criei o git próprio nesta pasta, com o primeiro commit \"estado antes do v7\" (tudo o que havia, menos os segredos).")
        if fatos["topo_do_git"]:
            linhas.append(f"- Esta pasta está dentro de outro git ({fatos['topo_do_git']}): esse git maior passa a ver a pasta como repositório aninhado.")
    elif relato.get("commit_antes"):
        linhas.append(f"- Commit \"estado antes do v7\" ({relato['commit_antes']}) com o que estava sem commit ({plural(len(fatos['itens_sem_commit']), 'item', 'itens')}).")
    else:
        linhas.append("- Não havia nada sem commit: a marca aponta para o último commit do projeto.")
    linhas.append(f"- Marca `{relato['marca']}` no commit {relato['marca_em']}: o projeto como estava no git antes do v7.")
    for copia in relato["copias_guardadas"]:
        linhas.append(f"- Cópia de agente `{copia['nome']}`: ramo `{copia['ramo']}`" + (f", trabalho guardado no commit {copia['commit']}" if copia["commit"] else ", sem trabalho novo a guardar")
                      + (f"; segredos que ficaram fora do commit dela: {', '.join(copia['segredos_fora'])}" if copia["segredos_fora"] else "") + ".")
    linhas += ["", "## O que foi para a gaveta (`.delta-11/anterior-v6/`, fora do git)", "",
               f"- A `.delta-11/` antiga inteira ({tamanho(gaveta_bytes)}, {numero(gaveta_arquivos)} arquivos), renomeada, não copiada: nada foi apagado (o que o git ignorava só existe aqui).",
               "- Quem escreve na gaveta: ninguém. Quem lê: todos menos o Revisor."]
    if relato["raiz"]:
        linhas.append(f"- Na raiz: {', '.join(relato['raiz'])} → `anterior-v6/raiz/`. O CLAUDE.md do v6 foi só para a gaveta (não para `instrucoes-anteriores`): são regras do sistema antigo, que o ATLAS leria como ordens contra as do v7.")
    for copia in relato["copias_guardadas"]:
        if "novo_caminho" in copia:
            linhas.append(f"- Cópia `{copia['nome']}` → `{Path(copia['novo_caminho']).relative_to(destino).as_posix()}` (git worktree move; o git a acha lá).")
    if any(v is not None for v in relato["originais"].values()):
        linhas.append("- Os originais dos arquivos que mudei no lugar (" + ", ".join(f"`{r}`" for r, v in relato["originais"].items() if v is not None) + ") estão em `anterior-v6/raiz/`.")
    linhas += ["", "## Ganchos que saíram das configurações", ""]
    if relato["ganchos_tirados"]:
        for arquivo, quantos, comandos, ficaram in relato["ganchos_tirados"]:
            linhas.append(f"- `{arquivo}`: {plural(quantos, 'gancho do v6 saiu', 'ganchos do v6 saíram')}; {plural(ficaram, 'gancho do dono ficou', 'ganchos do dono ficaram')}.")
            linhas += [f"  - `{c}`" for c in comandos]
    else:
        linhas.append("- Nenhum: as configurações não tinham ganchos do v6.")
    linhas += ["", "## Segredos que passaram a ser ignorados pelo git", ""]
    linhas.append("- " + (", ".join(f"`{s}`" for s in relato["segredos"]) + " (o `.gitignore` ganhou uma linha para cada um; nenhum entrou em commit)." if relato["segredos"] else "Nenhum arquivo de segredo solto."))
    if fatos["segredos_versionados"]:
        linhas.append(f"- ATENÇÃO: já estavam no git, desde antes da passagem: {', '.join(fatos['segredos_versionados'])}. Troque essas chaves: o histórico as guarda.")
    linhas += ["", "## O v7", "", f"- Instalado ({relato['agentes']} agentes, programa de agentes `{opcoes['motor']}`), no commit \"passagem do Delta-11 v6 para o v7\" ({relato['commit_da_passagem']}).",
               "- O aviso de abertura leva o ATLAS ao `PONTO-DE-PARTIDA.md` enquanto não houver `.delta-11/luz.md`.", f"- Registro: {registro}.",
               f"- `git status`: {'limpo' if not relato['sobrou_sem_commit'] else 'ainda com ' + str(len(relato['sobrou_sem_commit'])) + ' item(ns): ' + ', '.join(relato['sobrou_sem_commit'][:5])}."]
    for aviso in avisos:
        linhas.append(f"- Aviso do instalador: {aviso}")
    linhas += ["", "## Como voltar atrás", "",
               "Feche qualquer conversa aberta nesta pasta e peça ao Claude: \"voltar este projeto para a marca antes-do-v7\". Ele roda isto (de dentro da pasta do projeto):", "",
               "```sh", receita_de_volta(destino, relato).rstrip("\n"), "```", "",
               "Nada é apagado: o v7 fica ao lado, em `.delta-11-v7-guardado`. Trabalho feito depois da passagem entra num commit antes de voltar. "
               "Para o sincronizador antigo voltar a cuidar da pasta, ponha o caminho dela de novo na lista `projects` do registro (`~/.delta-11-registry.json`).", ""]
    return "\n".join(linhas)


def interpretar(argumentos: list[str]) -> dict | None:
    opcoes = {"pasta": None, "ensaio": False, "criar_git": False, "guardar_copias": False, "motor": ""}
    resto = list(argumentos)
    while resto:
        atual = resto.pop(0)
        if atual == "--passar-do-v6":
            if not resto or resto[0].startswith("-"):
                return None
            opcoes["pasta"] = resto.pop(0)
        elif atual == "--ensaio":
            opcoes["ensaio"] = True
        elif atual == "--criar-git":
            opcoes["criar_git"] = True
        elif atual == "--guardar-copias":
            opcoes["guardar_copias"] = True
        elif atual == "--motor":
            if not resto or resto[0].startswith("-"):
                return None
            opcoes["motor"] = resto.pop(0)
        else:
            return None
    return opcoes if opcoes["pasta"] else None


def executar(argumentos: list[str], instalador) -> int:
    opcoes = interpretar(argumentos)
    if opcoes is None:
        print(__doc__)
        return 2
    destino = instalador.resolver(opcoes["pasta"])
    instalador.recusar_lugares_proibidos(destino, dentro_de_git_maior_ok=True)
    if not destino.is_dir():
        instalador.erro(f"{destino} não é uma pasta que existe.")
    programa = opcoes["motor"] or instalador.PROGRAMA_PADRAO
    conhecidos = instalador.programas_do_motor()
    if programa not in conhecidos:
        instalador.erro(f"o motor ainda não sabe falar com o programa de agentes '{programa}' (os que ele conhece: {', '.join(conhecidos)}).")
    opcoes["motor"] = programa
    caminho = instalador.caminho_de_busca_do_terminal()
    instalador.conferir_dependencias(caminho)
    fatos = diagnosticar(destino, opcoes)
    motivos = recusas(fatos, opcoes, instalador)
    if motivos:
        if opcoes["ensaio"]:
            print(f"ENSAIO — nada foi mudado. A passagem de {destino.name} para o v7 seria RECUSADA:")
            print("\n".join(f"  - {m}" for m in motivos))
        else:
            print("\n".join(f"RECUSADO: {m}" for m in motivos) + "\nNada foi mudado.")
        return 1
    if opcoes["ensaio"]:
        instalador.conferir_antes_de_mexer(destino, False, ignorar_mudancas_sem_commit=True)
        print(descrever_ensaio(fatos, opcoes, programa))
        return 0
    instalador.conferir_motor()
    instalador.conferir_antes_de_mexer(destino, False, ignorar_mudancas_sem_commit=True)
    # A conversa pode ter começado nos minutos que a conferência do motor levou: olha de novo, já no limite de mudar algo.
    de_novo = conversas_abertas(destino)
    if de_novo:
        print("\n".join(f"RECUSADO: {m}" for m in de_novo) + "\nNada foi mudado.")
        return 1
    volta, relato = Desfazedor(), {"copias_guardadas": [], "originais": {}, "raiz": [], "ganchos_tirados": [], "motor": programa}
    try:
        guardar_estado_antes(destino, fatos, opcoes, volta, relato)
        ponto_de_falha("guardar")
        levar_para_a_gaveta(destino, fatos, opcoes, volta, relato)
        ponto_de_falha("gaveta")
        da_esteira = instalar_o_v7(destino, programa, caminho, instalador, volta, relato)
        ponto_de_falha("instalar-o-v7")
        ignorar_a_gaveta(destino)
        ponto, _ = montar_ponto_de_partida(destino / GAVETA, datetime.date.today().isoformat())
        arquivo_do_ponto = destino / GAVETA / "PONTO-DE-PARTIDA.md"
        arquivo_do_ponto.write_text(ponto, encoding="utf-8")
        volta.registrar("tirar o ponto de partida", arquivo_do_ponto.unlink)
        ponto_de_falha("ponto-de-partida")
        relato["commit_da_passagem"] = commit_da_passagem(destino, da_esteira, instalador, fatos)
    except BaseException as erro:  # inclusive Ctrl+C: o que mudou de lugar volta
        motivo = str(erro) if isinstance(erro, (Falhou, SystemExit)) and str(erro) else f"{type(erro).__name__}: {erro}"
        problemas = volta.desfazer()
        if problemas:
            print(f"ERRO: {motivo}\nNÃO consegui devolver tudo ao que era. O que sobrou:\n" + "\n".join(f"  - {p}" for p in problemas)
                  + f"\nA .delta-11 antiga está em {destino / NOME_TEMPORARIO} ou em {destino / GAVETA} (nada foi apagado); o git guarda o estado de antes (marca antes-do-v7).")
        else:
            print(f"ERRO: {motivo}\nA pasta foi devolvida ao que era (conteúdo, caminhos e permissões). A rede de segurança fica: o commit \"estado antes do v7\", "
                  "a marca antes-do-v7, o trabalho das cópias em ramos e o .tar.gz (se houve). Nada foi apagado.")
        if isinstance(erro, KeyboardInterrupt):
            raise
        return 1
    relato["sobrou_sem_commit"] = git(destino, "status", "--porcelain").stdout.splitlines()
    registro = "nada tirado do registro"
    try:
        registro = tirar_do_registro(destino)
    except Exception as erro:  # a passagem já está feita e guardada: o registro vira aviso, não desfaz
        instalador.avisos.append(f"não consegui tirar a pasta do registro ({type(erro).__name__}: {erro}); tire-a à mão da lista `projects` de {registro_do_sincronizador()}.")
    texto = escrever_relato(destino, fatos, opcoes, relato, instalador.avisos, registro)
    try:
        (destino / GAVETA / "RELATO-DA-PASSAGEM.md").write_text(texto, encoding="utf-8")
    except OSError as erro:
        instalador.avisos.append(f"não consegui gravar o relato na gaveta ({erro}); ele está aqui na tela.")
    print(f"OK — a passagem de {destino.name} do Delta-11 v6 para o v7 terminou (commit {relato['commit_da_passagem']}, marca {relato['marca']}).\n")
    print(texto)
    print("Próximo passo do dono: abrir esta pasta no VSCode, abrir o painel do Claude e aceitar a pergunta de confiança na pasta (só na primeira vez). "
          "O ATLAS começa a Luz pelo meio, com o que o produto já é.")
    return 0
