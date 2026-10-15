#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
Δ-11 v6.4 — Medidor de paralelismo (V12)
═══════════════════════════════════════════════════════════════

Para que serve: dizer, com números, quantos agentes estavam trabalhando AO
MESMO TEMPO num trecho de trabalho do Delta-11. Serve para comparar a mesma
fase rodada na v6.3 (conta-gotas) e na v6.4 (onda inteira de uma vez).

Uso:
  python3 .delta-11/ferramentas/medir-paralelismo.py [PASTA-DO-PROJETO]
      [--desde 2026-10-14T00:00:00-03:00] [--ate 2026-10-15T00:00:00-03:00]
      [--ultimas-horas N] [--sem-descontar] [--json]
      [--incluir-orquestrador] [--sem-processos-separados] [--sem-aninhados]
      [--sem-transcricoes] [--limite-parado-min 30] [--pasta-claude DIR]

O que lê (SOMENTE leitura — não grava nada no projeto nem em lugar nenhum):
  1. Transcrições do Claude Code (preferidas: dão início e fim exatos):
     - as citadas na linha `transcricao:` dos logs do SubagentStop;
     - as da pasta do projeto em ~/.claude/projects/<pasta-codificada>/
       (`<sessão>/subagents/agent-*.jsonl` = sub-agentes; `<sessão>.jsonl` =
       sessões; uma sessão só conta como agente quando a primeira mensagem
       ativa um agente ou sub-agente — a conversa do comandante não conta).
     O primeiro e o último carimbo `timestamp` dão o início e o fim.
  2. Logs do SubagentStop: `.delta-11/logs/sub-agentes/*.log` (fim de cada
     sub-agente: `evento: SubagentStop`, `quando:`, `agent_type:`,
     `agent_id:`, `agente_delta11:`).
  3. Activity-log: `.delta-11/activity-log.md`, linhas do pre-despacho
     "Despacho de X OK" / "ISENTO" (início). Aceita os 2 formatos:
       [ts] pre-despacho: Despacho de X OK (...)
       - [ts] [pre-despacho] [AGENTE] Despacho de X OK (...)
  4. Pulso: `.delta-11/ativacoes/pulso-*.json` (último sinal de vida de um
     agente cujo fim não foi registrado).
  Início e fim vindos dos logs só são pareados quando não há transcrição
  para aquele sub-agente. Pareamento conservador: cada fim pega o início
  MAIS RECENTE do mesmo agente (intervalos mais curtos, nunca inventados).
  Início sem fim e fim sem início são descartados e contados no aviso.

O que NÃO conta como "agente trabalhando":
  - o CRONOS (só coordena e espera) — use --incluir-orquestrador para contar;
  - a conversa principal do comandante.
  Conta: executores, revisores e sub-agentes internos (build-validator,
  contract-tester...), inclusive os disparados de dentro de um executor.
  --sem-processos-separados conta só os sub-agentes do Claude Code (tira as
  sessões `claude --print` disparadas por vigias, como o regenerar-contratos).
  --sem-aninhados tira o sub-agente aberto de dentro de outro agente que já
  está na conta (o executor esperando o build-validator conta 1, não 2) —
  mede só o paralelismo dos despachos do CRONOS. Precisa das transcrições
  (o parentAgentId vem delas).

Desconto: trecho com mais de 30 min sem NENHUMA atividade registrada
(nenhuma linha em transcrição, log ou activity-log) é máquina dormindo ou
comandante ausente — sai da conta, e a saída diz quanto foi descontado.
--sem-descontar mostra o número bruto. Um agente parado mais de 30 min na
própria transcrição (ex.: retomado horas depois) vira 2 trechos, a não ser
que um sub-agente filho dele estivesse rodando nesse meio-tempo.

Saída: relatório em português (padrão) ou JSON (--json).
Código de saída: 0 = medido; 2 = uso errado (pasta sem .delta-11, data inválida).
Só Python 3 puro — nada para instalar.
═══════════════════════════════════════════════════════════════
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

VERSAO = "6.4"
LIMITE_PARADO_PADRAO_MIN = 30
ORQUESTRADORES = {"CRONOS"}
AGENTES_DELTA11 = {"ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM", "BACK",
                   "ENGINE", "VAULT", "SHIELD", "SCOUT"}
SUBAGENTES_PADRAO = {"build-validator", "code-architect", "code-simplifier",
                     "cold-start-tester", "contract-tester", "fresh-reviewer",
                     "impact-mapper", "qa-ui-tandem", "schema-validator",
                     "tool-provisioner", "verify-app"}
# Tolerância para casar um "Despacho de X OK" com a transcrição que ele abriu.
DESPACHO_ANTES_S = 10
DESPACHO_DEPOIS_S = 300

UTC = dt.timezone.utc

LINHA_ACTIVITY_RE = re.compile(r"^\s*(?:-\s*)?\[(\d{4}-\d\d-\d\dT[^\]\s]+)\]\s*(.*)$")
DESPACHO_RE = re.compile(
    r"pre-despacho\]?:?.*?Despacho de (\S+?)\s+(OK\b|ISENTO\b|\S*\s*n[aã]o [eé] executor conhecido)")
SUBAGENTE_TEXTO_RE = re.compile(r"sub-agentes?[/ ]([a-z][a-z0-9-]+)")
VOCE_E_SUB_RE = re.compile(r"Voc[eê] [eé] o sub-agente ([a-z][a-z0-9-]+)")
AGENTE_CAMPO_RE = re.compile(r"Agente:\s*\**\s*([A-Z]{4,6})\b")
VOCE_E_RE = re.compile(r"Voc[eê] [eé] o (?:agente )?([A-Z]{4,6})\b")
OPERATIVO_RE = re.compile(r"operativos/([A-Z]{4,6})\.md")
JANELA_RE = re.compile(r"(?:janela|ativacao|ativação|bloco)[-_ ]([A-Z]{4,6})\b")


# ─── Datas ───────────────────────────────────────────────────
def ler_data(texto):
    """ISO 8601 com Z ou fuso (frações de segundo opcionais) → datetime com fuso."""
    if not texto:
        return None
    t = str(texto).strip()
    if t.endswith("Z") or t.endswith("z"):
        t = t[:-1] + "+00:00"
    m = re.match(r"^(\d{4}-\d\d-\d\d[T ]\d\d:\d\d(?::\d\d)?)(\.\d+)?(.*)$", t)
    if not m:
        return None
    base, fracao, resto = m.group(1), m.group(2) or "", m.group(3) or ""
    if fracao:
        fracao = "." + (fracao[1:] + "000000")[:6]
    try:
        d = dt.datetime.fromisoformat(base + fracao + resto)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.astimezone()  # sem fuso: horário local da máquina
    return d.astimezone(UTC)


def fmt_duracao(segundos):
    s = int(round(max(0, segundos)))
    if s < 60:
        return "%d s" % s
    h, resto = divmod(s, 3600)
    m = resto // 60
    if h:
        return "%d h %02d min" % (h, m)
    return "%d min" % m


def fmt_num(valor, casas=2):
    return ("%.*f" % (casas, valor)).replace(".", ",")


# ─── Pastas ──────────────────────────────────────────────────
def pasta_principal(pasta):
    """D25: rodando de dentro de uma worktree, lê a pasta PRINCIPAL."""
    try:
        r = subprocess.run(["git", "-C", pasta, "rev-parse", "--path-format=absolute",
                            "--git-common-dir"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            candidata = os.path.dirname(os.path.normpath(r.stdout.strip()))
            if os.path.isdir(os.path.join(candidata, ".delta-11")):
                return candidata
    except (OSError, subprocess.SubprocessError):
        pass
    return pasta


def pasta_claude_projetos(argumento):
    if argumento:
        return os.path.expanduser(argumento)
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "projects")


def codificar_pasta(caminho):
    """Mesmo nome que o Claude Code dá à pasta do projeto em ~/.claude/projects."""
    return re.sub(r"[^A-Za-z0-9]", "-", caminho)


def nomes_subagentes(raiz):
    nomes = set(SUBAGENTES_PADRAO)
    for arq in glob.glob(os.path.join(raiz, ".delta-11", "sub-agentes", "*.md")):
        nomes.add(os.path.splitext(os.path.basename(arq))[0].lower())
    return nomes


# ─── Transcrições ────────────────────────────────────────────
class Transcricao(object):
    def __init__(self, caminho, tipo):
        self.caminho = caminho
        self.tipo = tipo            # "sub-agente" ou "sessao"
        self.carimbos = []          # datetimes (UTC), em ordem
        self.primeiro_texto = ""
        self.meta = {}
        self.agent_id = None
        m = re.match(r"^agent-([A-Za-z0-9]+)\.jsonl$", os.path.basename(caminho))
        if m:
            self.agent_id = m.group(1)


def texto_de_conteudo(conteudo):
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        partes = []
        for x in conteudo:
            if isinstance(x, dict) and x.get("type") == "text":
                partes.append(str(x.get("text") or ""))
            elif isinstance(x, str):
                partes.append(x)
        return "\n".join(partes)
    return ""


def ler_transcricao(caminho, tipo):
    t = Transcricao(caminho, tipo)
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            for linha in f:
                if '"timestamp"' not in linha:
                    continue
                try:
                    obj = json.loads(linha)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                d = ler_data(obj.get("timestamp"))
                if d:
                    t.carimbos.append(d)
                if not t.primeiro_texto and obj.get("type") == "user":
                    msg = obj.get("message")
                    if isinstance(msg, dict):
                        t.primeiro_texto = texto_de_conteudo(msg.get("content"))[:6000]
    except OSError:
        return None
    t.carimbos.sort()
    meta_caminho = caminho[:-len(".jsonl")] + ".meta.json"
    if os.path.isfile(meta_caminho):
        try:
            with open(meta_caminho, encoding="utf-8") as f:
                meta = json.load(f)
            if isinstance(meta, dict):
                t.meta = meta
        except (OSError, ValueError):
            pass
    return t


def identificar(texto, descricao, subagentes):
    """Nome do agente ('FRONT', 'build-validator'...) pela descrição do despacho
    e pela primeira mensagem; None quando não há sinal claro.

    Ordem: a descrição dada por quem despachou vale mais; depois o começo do
    prompt ("Você é o sub-agente x", "Leia .../sub-agentes/x.md", "Agente: X");
    por último menções soltas (um prompt do SHIELD que cita
    sub-agentes/contract-tester.md no meio do texto continua SHIELD).
    """
    texto = texto or ""
    descricao = descricao or ""
    desc_baixa = descricao.lower()
    for nome in sorted(subagentes, key=len, reverse=True):
        if nome in desc_baixa or nome.replace("-", " ") in desc_baixa:
            return nome
    m = VOCE_E_SUB_RE.search(texto)
    if m and m.group(1) in subagentes:
        return m.group(1)
    m = SUBAGENTE_TEXTO_RE.search(texto[:300])   # "Leia .../sub-agentes/x.md e siga"
    if m and m.group(1) in subagentes:
        return m.group(1)
    for regex in (AGENTE_CAMPO_RE, VOCE_E_RE):
        m = regex.search(texto)
        if m and m.group(1) in AGENTES_DELTA11:
            return m.group(1)
    for palavra in re.findall(r"[A-Za-z]+", descricao):
        if palavra in AGENTES_DELTA11:
            return palavra
    m = SUBAGENTE_TEXTO_RE.search(texto)
    if m and m.group(1) in subagentes:
        return m.group(1)
    for regex in (OPERATIVO_RE, JANELA_RE):
        m = regex.search(texto)
        if m and m.group(1) in AGENTES_DELTA11:
            return m.group(1)
    return None


def achar_transcricoes(raiz, pasta_claude, desde):
    """Transcrições da pasta do projeto em ~/.claude/projects (e das worktrees dele)."""
    achadas = []
    if not os.path.isdir(pasta_claude):
        return achadas
    codigos = {codificar_pasta(raiz), codificar_pasta(os.path.realpath(raiz))}
    pastas = []
    for nome in os.listdir(pasta_claude):
        for codigo in codigos:
            if nome == codigo or nome.startswith(codigo + "--claude-worktrees-"):
                pastas.append(os.path.join(pasta_claude, nome))
                break
    limite_mtime = desde.timestamp() if desde else None
    for pasta in pastas:
        candidatos = [(c, "sessao") for c in glob.glob(os.path.join(pasta, "*.jsonl"))]
        candidatos += [(c, "sub-agente") for c in
                       glob.glob(os.path.join(pasta, "*", "subagents", "agent-*.jsonl"))]
        for caminho, tipo in candidatos:
            try:
                if limite_mtime and os.path.getmtime(caminho) < limite_mtime:
                    continue  # terminou antes do período
            except OSError:
                continue
            achadas.append((os.path.realpath(caminho), tipo))
    return achadas


# ─── Logs do SubagentStop, activity-log e pulsos ─────────────
def ler_logs_subagentstop(raiz):
    fins = []
    for arq in sorted(glob.glob(os.path.join(raiz, ".delta-11", "logs", "sub-agentes", "*.log"))):
        try:
            with open(arq, encoding="utf-8", errors="replace") as f:
                texto = f.read()
        except OSError:
            continue
        # Dois sub-agentes do mesmo tipo no mesmo segundo caem no MESMO arquivo.
        for bloco in re.split(r"(?m)^evento:\s*SubagentStop\s*$", texto)[1:]:
            campos = {}
            for linha in bloco.splitlines():
                if linha.startswith("--- ultima mensagem"):
                    break
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    campos[chave.strip()] = valor.strip()
            quando = ler_data(campos.get("quando"))
            if not quando:
                continue
            nome = None
            for chave in ("agente_delta11", "subagente_detectado", "agent_type"):
                valor = campos.get(chave)
                if valor and valor != "-":
                    nome = valor
                    break
            transc = campos.get("transcricao")
            fins.append({
                "quando": quando,
                "nome": nome or "desconhecido",
                "agent_id": campos.get("agent_id") if campos.get("agent_id") not in (None, "-", "sem-id") else None,
                "transcricao": os.path.expanduser(transc) if transc and transc != "-" else None,
            })
    return fins


def ler_activity_log(raiz):
    inicios, marcas, sem_alvo = [], [], []
    caminho = os.path.join(raiz, ".delta-11", "activity-log.md")
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
    except OSError:
        return inicios, marcas, sem_alvo
    for linha in linhas:
        m = LINHA_ACTIVITY_RE.match(linha)
        if not m:
            continue
        quando = ler_data(m.group(1))
        if not quando:
            continue
        marcas.append(quando)
        resto = m.group(2)
        if "pre-despacho" not in resto or "BLOQUEIO" in resto:
            continue
        d = DESPACHO_RE.search(resto)
        if d:
            inicios.append({"quando": quando, "nome": d.group(1).strip(".,:;")})
        elif "alvo n" in resto:
            sem_alvo.append((quando, "?"))
    return inicios, marcas, sem_alvo


def ler_pulsos(raiz):
    pulsos = {}
    for arq in glob.glob(os.path.join(raiz, ".delta-11", "ativacoes", "pulso-*.json")):
        try:
            with open(arq, encoding="utf-8") as f:
                dados = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(dados, dict):
            continue
        nome = str(dados.get("agente") or re.sub(r"^pulso-|\.json$", "", os.path.basename(arq)))
        sinal = ler_data(dados.get("ultimo_sinal") or dados.get("ultimo_update"))
        if sinal:
            chave = nome.split("-")[0].upper()
            if chave not in pulsos or sinal > pulsos[chave]:
                pulsos[chave] = sinal
    return pulsos


# ─── Intervalos ──────────────────────────────────────────────
def dividir_em_trechos(carimbos, limite_s, filhos):
    """Divide a vida de um agente onde a transcrição fica parada > limite,
    a não ser que um sub-agente filho estivesse rodando nesse meio-tempo."""
    if not carimbos:
        return []
    trechos = []
    ini = anterior = carimbos[0]
    for c in carimbos[1:]:
        if (c - anterior).total_seconds() > limite_s and not coberto(anterior, c, filhos, limite_s):
            trechos.append((ini, anterior))
            ini = c
        anterior = c
    trechos.append((ini, anterior))
    return trechos


def coberto(a, b, filhos, limite_s):
    """True se os filhos cobrem [a, b], tirando folgas de até limite_s
    (ex.: o filho terminou e o pai levou 2 min para voltar a escrever)."""
    if not filhos:
        return False
    return all((fim - ini).total_seconds() <= limite_s for ini, fim in subtrair([(a, b)], filhos))


def subtrair(trechos, cortes):
    """trechos − união(cortes)."""
    resultado = []
    for ini, fim in trechos:
        pedacos = [(ini, fim)]
        for cini, cfim in cortes:
            novos = []
            for pini, pfim in pedacos:
                if cfim <= pini or cini >= pfim:
                    novos.append((pini, pfim))
                    continue
                if cini > pini:
                    novos.append((pini, cini))
                if cfim < pfim:
                    novos.append((cfim, pfim))
            pedacos = novos
        resultado.extend(p for p in pedacos if p[1] > p[0])
    return resultado


def calcular(intervalos, desde, ate, descontos):
    """Varre a linha do tempo: tempo ativo, tempo com 0, média, pico, buracos."""
    pontos = {desde, ate}
    for ini, fim in intervalos:
        pontos.add(ini)
        pontos.add(fim)
    for ini, fim in descontos:
        pontos.add(ini)
        pontos.add(fim)
    pontos = sorted(p for p in pontos if desde <= p <= ate)
    eventos = {}
    for ini, fim in intervalos:
        eventos[ini] = eventos.get(ini, 0) + 1
        eventos[fim] = eventos.get(fim, 0) - 1
    descontos = sorted(descontos)
    ativo = zero = integral = 0.0
    pico, pico_quando = 0, None
    buracos, buraco_atual = [], None
    k = 0
    for i in range(len(pontos) - 1):
        a, b = pontos[i], pontos[i + 1]
        k += eventos.get(a, 0)
        dur = (b - a).total_seconds()
        if dur <= 0:
            continue
        descontado = any(dini <= a and b <= dfim for dini, dfim in descontos)
        if descontado:
            if buraco_atual:
                buracos.append(buraco_atual)
                buraco_atual = None
            continue
        ativo += dur
        integral += k * dur
        if k > pico:
            pico, pico_quando = k, a
        if k == 0:
            zero += dur
            if buraco_atual and buraco_atual[1] == a:
                buraco_atual = (buraco_atual[0], b)
            else:
                if buraco_atual:
                    buracos.append(buraco_atual)
                buraco_atual = (a, b)
        elif buraco_atual:
            buracos.append(buraco_atual)
            buraco_atual = None
    if buraco_atual:
        buracos.append(buraco_atual)
    buracos.sort(key=lambda x: (x[1] - x[0]).total_seconds(), reverse=True)
    return {
        "ativo_s": ativo,
        "zero_s": zero,
        "media": (integral / ativo) if ativo else 0.0,
        "pico": pico,
        "pico_quando": pico_quando,
        "buracos": buracos,
    }


# ─── Programa ────────────────────────────────────────────────
def montar_argumentos():
    p = argparse.ArgumentParser(
        description="Mede quantos agentes do Delta-11 trabalharam ao mesmo tempo (somente leitura).")
    p.add_argument("projeto", nargs="?", default=os.getcwd(),
                   help="pasta do projeto Delta-11 (padrão: a pasta atual)")
    p.add_argument("--desde", help="início do período (ISO, ex.: 2026-10-14T00:00:00-03:00)")
    p.add_argument("--ate", help="fim do período (ISO)")
    p.add_argument("--ultimas-horas", type=float, help="período = as últimas N horas")
    p.add_argument("--sem-descontar", action="store_true",
                   help="não desconta os trechos de mais de 30 min sem atividade")
    p.add_argument("--limite-parado-min", type=float, default=LIMITE_PARADO_PADRAO_MIN,
                   help="minutos sem atividade a partir dos quais o trecho é descontado (padrão 30)")
    p.add_argument("--incluir-orquestrador", action="store_true",
                   help="conta também o CRONOS como agente trabalhando")
    p.add_argument("--sem-processos-separados", action="store_true",
                   help="conta só os sub-agentes do Claude Code (tira sessões claude --print de vigias)")
    p.add_argument("--sem-aninhados", action="store_true",
                   help="não conta o sub-agente aberto DE DENTRO de outro agente que já está na conta "
                        "(ex.: build-validator de um executor) — mede só o paralelismo dos despachos")
    p.add_argument("--sem-transcricoes", action="store_true",
                   help="ignora as transcrições e usa só os logs (início + fim)")
    p.add_argument("--pasta-claude", help="pasta 'projects' do Claude Code (padrão: ~/.claude/projects)")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    return p


def main(argv=None):
    args = montar_argumentos().parse_args(argv)
    raiz = os.path.abspath(os.path.expanduser(args.projeto))
    if not os.path.isdir(raiz):
        print("ERRO: a pasta %s não existe." % raiz, file=sys.stderr)
        return 2
    raiz = pasta_principal(raiz)
    if not os.path.isdir(os.path.join(raiz, ".delta-11")):
        print("ERRO: %s não é um projeto Delta-11 (falta a pasta .delta-11)." % raiz, file=sys.stderr)
        return 2

    agora = dt.datetime.now(UTC)
    desde = ate = None
    fuso_saida = None
    for nome_opcao in ("desde", "ate"):
        valor = getattr(args, nome_opcao)
        if valor:
            d = ler_data(valor)
            if not d:
                print("ERRO: data inválida em --%s: %s" % (nome_opcao, valor), file=sys.stderr)
                return 2
            if fuso_saida is None:
                try:
                    fuso_saida = dt.datetime.fromisoformat(
                        valor.strip().replace("Z", "+00:00")).tzinfo
                except ValueError:
                    fuso_saida = None
            if nome_opcao == "desde":
                desde = d
            else:
                ate = d
    if args.ultimas_horas is not None:
        if args.ultimas_horas <= 0:
            print("ERRO: --ultimas-horas precisa ser maior que zero.", file=sys.stderr)
            return 2
        ate = ate or agora
        desde = ate - dt.timedelta(hours=args.ultimas_horas)
    if desde and ate and ate <= desde:
        print("ERRO: --ate precisa ser depois de --desde.", file=sys.stderr)
        return 2
    if fuso_saida is None:
        fuso_saida = dt.datetime.now().astimezone().tzinfo
    limite_s = args.limite_parado_min * 60
    avisos = []
    subagentes = nomes_subagentes(raiz)
    excluir = set() if args.incluir_orquestrador else set(ORQUESTRADORES)

    # 1. Logs e activity-log
    fins = ler_logs_subagentstop(raiz)
    inicios, marcas, sem_alvo = ler_activity_log(raiz)
    pulsos = ler_pulsos(raiz)
    marcas.extend(f["quando"] for f in fins)
    marcas.extend(pulsos.values())

    # 2. Transcrições (preferidas)
    transcricoes = {}
    if not args.sem_transcricoes:
        for f in fins:
            if f["transcricao"] and os.path.isfile(f["transcricao"]):
                caminho = os.path.realpath(f["transcricao"])
                transcricoes.setdefault(caminho, "sub-agente")
        for caminho, tipo in achar_transcricoes(raiz, pasta_claude_projetos(args.pasta_claude), desde):
            if caminho not in transcricoes or tipo == "sessao":
                transcricoes[caminho] = tipo

    lidas = []
    for caminho, tipo in transcricoes.items():
        t = ler_transcricao(caminho, tipo)
        if not t or not t.carimbos:
            continue
        if desde and t.carimbos[-1] < desde:
            continue
        if ate and t.carimbos[0] > ate:
            continue
        lidas.append(t)

    # Quem é quem
    ids_com_transcricao, caminhos_com_transcricao = set(), set()
    trabalhadores = []   # (Transcricao, nome)
    for t in lidas:
        marcas.extend(c for c in t.carimbos if (not desde or c >= desde) and (not ate or c <= ate))
        if t.tipo == "sub-agente":
            nome = identificar(t.primeiro_texto, t.meta.get("description"), subagentes)
            nome = nome or t.meta.get("agentType") or "sub-agente"
        else:
            nome = identificar(t.primeiro_texto, "", subagentes)
            if not nome:
                continue  # conversa do comandante: só serve de sinal de atividade
            if args.sem_processos_separados:
                continue
        if t.agent_id:
            ids_com_transcricao.add(t.agent_id)
        caminhos_com_transcricao.add(t.caminho)
        trabalhadores.append((t, nome))

    filhos_por_pai = {}
    for t, _ in trabalhadores:
        pai = t.meta.get("parentAgentId")
        if pai:
            filhos_por_pai.setdefault(pai, []).append((t.carimbos[0], t.carimbos[-1]))

    nome_por_id = {t.agent_id: nome for t, nome in trabalhadores if t.agent_id}
    intervalos = []   # dicts: ini, fim, nome, fonte
    for t, nome in trabalhadores:
        if nome.upper() in excluir:
            continue
        pai = t.meta.get("parentAgentId")
        if args.sem_aninhados and pai in nome_por_id and nome_por_id[pai].upper() not in excluir:
            continue  # o pai já está na conta (ex.: build-validator de um executor)
        for ini, fim in dividir_em_trechos(t.carimbos, limite_s, filhos_por_pai.get(t.agent_id, [])):
            intervalos.append({"ini": ini, "fim": fim, "nome": nome,
                               "fonte": "transcricao", "agente": t.agent_id or os.path.basename(t.caminho)})

    # 3. Logs: só o que nenhuma transcrição explicou
    nomes_transc = [(it["ini"], it["nome"].lower()) for it in intervalos]
    nomes_transc += [(t.carimbos[0], n.lower()) for t, n in trabalhadores if n.upper() in excluir]
    usados = set()
    inicios_restantes = []
    for ini in sorted(inicios, key=lambda x: x["quando"]):
        achou, melhor = None, None
        for idx, (quando_t, nome_t) in enumerate(nomes_transc):
            if idx in usados or nome_t != ini["nome"].lower():
                continue
            delta = (quando_t - ini["quando"]).total_seconds()
            if -DESPACHO_ANTES_S <= delta <= DESPACHO_DEPOIS_S and (melhor is None or abs(delta) < melhor):
                achou, melhor = idx, abs(delta)
        if achou is None:
            inicios_restantes.append(ini)
        else:
            usados.add(achou)
    fins_restantes = [f for f in fins
                      if not (f["agent_id"] and f["agent_id"] in ids_com_transcricao)
                      and not (f["transcricao"] and os.path.realpath(f["transcricao"]) in caminhos_com_transcricao)]

    pendentes, nome_original = {}, {}
    for ini in inicios_restantes:
        pendentes.setdefault(ini["nome"].lower(), []).append(ini["quando"])
        nome_original[ini["nome"].lower()] = ini["nome"]
    fim_sem_inicio = []
    pareados = []
    for f in sorted(fins_restantes, key=lambda x: x["quando"]):
        lista = pendentes.get(f["nome"].lower(), [])
        candidatos = [q for q in lista if q <= f["quando"]]
        if not candidatos:
            fim_sem_inicio.append((f["quando"], f["nome"]))
            continue
        q = max(candidatos)          # o início MAIS RECENTE (conservador)
        lista.remove(q)
        pareados.append((q, f["quando"], f["nome"], "logs"))
    inicio_sem_fim = []
    for nome, lista in pendentes.items():
        for q in lista:
            sinal = pulsos.get(nome.upper())
            if sinal and sinal > q:
                pareados.append((q, sinal, nome_original[nome], "pulso"))
            else:
                inicio_sem_fim.append((q, nome_original[nome]))
    for ini, fim, nome, fonte in pareados:
        if nome.upper() in excluir:
            continue
        intervalos.append({"ini": ini, "fim": fim, "nome": nome, "fonte": fonte, "agente": None})
        marcas.extend([ini, fim])

    # 4. Período
    if desde is None or ate is None:
        todos = sorted(marcas + [i["ini"] for i in intervalos] + [i["fim"] for i in intervalos])
        if not todos:
            print("Nenhuma atividade encontrada em %s." % raiz, file=sys.stderr)
            todos = [agora]
        desde = desde or todos[0]
        ate = ate or todos[-1]
    if ate > agora:
        avisos.append("O fim do período está no futuro: medido só até agora.")
        ate = max(agora, desde)
    fora_da_conta = {}
    for chave, lista, texto in (
            ("fim_sem_inicio", fim_sem_inicio, "fim(ns) de sub-agente sem início correspondente"),
            ("inicio_sem_fim", inicio_sem_fim, "despacho(s) sem fim registrado nem transcrição"),
            ("despacho_sem_alvo", sem_alvo, "despacho(s) com agente não identificado no activity-log")):
        no_periodo = sorted((q, n) for q, n in lista if desde <= q <= ate)
        fora_da_conta[chave] = no_periodo
        if no_periodo:
            avisos.append("%d %s — fora da conta (%s)." % (len(no_periodo), texto, ", ".join(
                "%s %s" % (n, q.astimezone(fuso_saida).strftime("%d/%m %H:%M")) for q, n in no_periodo[:5])
                + (" ..." if len(no_periodo) > 5 else "")))
    intervalos_cortados = []
    for it in intervalos:
        ini, fim = max(it["ini"], desde), min(it["fim"], ate)
        if fim > ini or (fim == ini and desde <= ini <= ate and it["fim"] == it["ini"]):
            intervalos_cortados.append(dict(it, ini=ini, fim=fim))
    intervalos = intervalos_cortados

    # 5. Desconto: trechos > limite sem nenhuma atividade
    descontos = []
    if not args.sem_descontar:
        pontos = sorted({desde, ate} | {m for m in marcas if desde <= m <= ate}
                        | {i["ini"] for i in intervalos} | {i["fim"] for i in intervalos})
        lacunas = [(a, b) for a, b in zip(pontos, pontos[1:]) if (b - a).total_seconds() > limite_s]
        # Intervalo sem transcrição (só início+fim nos logs) não tem sinais por dentro:
        # se ele cobre a lacuna, alguém estava trabalhando — não desconta essa parte.
        so_logs = [(i["ini"], i["fim"]) for i in intervalos if i["fonte"] != "transcricao"]
        descontos = subtrair(lacunas, so_logs)

    r = calcular([(i["ini"], i["fim"]) for i in intervalos if i["fim"] > i["ini"]], desde, ate, descontos)
    total_s = (ate - desde).total_seconds()
    descontado_s = sum((b - a).total_seconds() for a, b in descontos)
    contados = {}
    fontes = {}
    agentes_unicos = set()
    for it in intervalos:
        chave = it["agente"] or ("%s@%s" % (it["nome"], it["ini"].isoformat()))
        if chave in agentes_unicos:
            continue
        agentes_unicos.add(chave)
        contados[it["nome"]] = contados.get(it["nome"], 0) + 1
        fontes[it["fonte"]] = fontes.get(it["fonte"], 0) + 1
    n_agentes = len(agentes_unicos)

    def local(d):
        return d.astimezone(fuso_saida) if d else None

    resultado = {
        "versao": VERSAO,
        "projeto": raiz,
        "periodo": {"desde": local(desde).isoformat(), "ate": local(ate).isoformat()},
        "tempo_total_s": round(total_s),
        "descontado": {
            "ativo": not args.sem_descontar,
            "limite_min": args.limite_parado_min,
            "total_s": round(descontado_s),
            "trechos": [{"inicio": local(a).isoformat(), "fim": local(b).isoformat(),
                         "duracao_s": round((b - a).total_seconds())} for a, b in sorted(descontos)],
        },
        "tempo_ativo_s": round(r["ativo_s"]),
        "sub_agentes": {"total": n_agentes, "por_fonte": fontes,
                        "por_nome": dict(sorted(contados.items()))},
        "orquestrador_fora_da_conta": sorted(excluir),
        "tempo_com_zero_s": round(r["zero_s"]),
        "tempo_com_zero_pct": round(100.0 * r["zero_s"] / r["ativo_s"], 1) if r["ativo_s"] else 0.0,
        "media_simultaneos": round(r["media"], 2),
        "pico": {"agentes": r["pico"], "quando": local(r["pico_quando"]).isoformat() if r["pico_quando"] else None},
        "buracos": [{"inicio": local(a).isoformat(), "fim": local(b).isoformat(),
                     "duracao_s": round((b - a).total_seconds())} for a, b in r["buracos"][:5]],
        "fora_da_conta": {k: [{"quando": local(q).isoformat(), "agente": n} for q, n in v]
                          for k, v in fora_da_conta.items()},
        "avisos": avisos,
    }

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0

    def hora(d):
        return local(d).strftime("%d/%m %H:%M")

    fuso_txt = local(desde).strftime("%z")
    fuso_txt = fuso_txt[:3] + ":" + fuso_txt[3:] if fuso_txt else "?"
    print("════════════════════════════════════════════════════════════")
    print("  Δ-11 — Medição de paralelismo (quantos agentes ao mesmo tempo)")
    print("════════════════════════════════════════════════════════════")
    print("Projeto: %s" % raiz)
    print("Período analisado: %s → %s (horário %s)" % (
        local(desde).strftime("%d/%m/%Y %H:%M"), local(ate).strftime("%d/%m/%Y %H:%M"), fuso_txt))
    print("Tempo total do período: %s" % fmt_duracao(total_s))
    if args.sem_descontar:
        print("Desconto de pausas: DESLIGADO (--sem-descontar) — o número é bruto.")
    else:
        print("Descontado: %s em %d trecho(s) com mais de %s min sem NENHUMA atividade"
              % (fmt_duracao(descontado_s), len(descontos), fmt_num(args.limite_parado_min, 0)))
        print("  (máquina dormindo ou comandante ausente — não é culpa do Delta-11)")
    print("Tempo ativo considerado: %s" % fmt_duracao(r["ativo_s"]))
    print("")
    detalhe = ", ".join("%d por %s" % (v, {"transcricao": "transcrição do Claude Code",
                                             "logs": "início+fim nos logs",
                                             "pulso": "início no log + último pulso"}.get(k, k))
                        for k, v in sorted(fontes.items()))
    print("Sub-agentes que rodaram: %d%s" % (n_agentes, (" (%s)" % detalhe) if detalhe else ""))
    if excluir:
        print("  O %s não entra na conta: ele só coordena e espera os outros." % ", ".join(sorted(excluir)))
    print("")
    if r["ativo_s"] > 0:
        print("Tempo com 0 agentes trabalhando: %s = %s%% do tempo ativo"
              % (fmt_duracao(r["zero_s"]), fmt_num(100.0 * r["zero_s"] / r["ativo_s"], 0)))
        print("Média de agentes trabalhando ao mesmo tempo: %s" % fmt_num(r["media"]))
        if r["pico_quando"]:
            print("Pico: %d agente(s) ao mesmo tempo (primeira vez em %s)" % (r["pico"], hora(r["pico_quando"])))
        else:
            print("Pico: 0 agentes")
    else:
        print("Não sobrou tempo ativo no período (tudo descontado ou período vazio).")
    print("")
    if r["buracos"]:
        print("Os %d maiores buracos (ninguém trabalhando, só esperando):" % min(5, len(r["buracos"])))
        for i, (a, b) in enumerate(r["buracos"][:5], 1):
            print("  %d. %s → %s  (%s)" % (i, hora(a), local(b).strftime("%H:%M"), fmt_duracao((b - a).total_seconds())))
    else:
        print("Nenhum buraco: sempre havia pelo menos 1 agente trabalhando.")
    if avisos:
        print("")
        print("Avisos:")
        for a in avisos:
            print("  - %s" % a)
    print("")
    print("Como ler: média 1,00 = um agente por vez (em série). A v6.4 quer média perto de 3")
    print("ou mais nas fases de construção, e o mínimo possível de tempo com 0 agentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
