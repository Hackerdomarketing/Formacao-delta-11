"""Registro de CRONOS do motor do Delta-11 v7 (usado pela trava, pelo aviso de abertura e pelo gancho cronos-vivo).

Um CRONOS é conhecido pelo `agentId` que o programa de agentes devolve e pela pasta do quadro que ele conduz (tirada da
mensagem `Conduza .delta-11/quadro/<X>/`). "Trabalhando" vai do início ao fim da vez dele (ganchos de início e de fim
de agente); "a conversa dele roda" é o processo do programa de agentes que chamou o gancho estar vivo (qual processo é,
o tradutor diz: motor.py). O tempo de cada vez se
soma no trabalho do time daquele quadro (`trabalho/<quadro>.json`): a espera pelo dono e pelo tempo não conta, porque o
CRONOS encerra esperando; o relógio o diz ao CRONOS e ao ATLAS, para o freio do tempo.

Todo tempo aqui é tempo com o Mac acordado: o sono (e o computador desligado) não conta como silêncio, como linha parada
nem como trabalho do time. O motor guarda em `vivos/sono/historico.json` cada vez que o relógio da parede se afasta do relógio que para
no sono, e desconta essa diferença de toda idade que mede.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import motor

PASTA = Path(__file__).resolve().parent / "vivos"
SONO = PASTA / "sono" / "historico.json"  # fora de vivos/*.json, que são os registros de CRONOS
ARQUITETOS = PASTA / "arquitetos"
QUADRO_NA_MENSAGEM = re.compile(r"\.delta-11/quadro/([A-Za-z0-9-]+)/")


def mapa() -> dict:
    """Os valores vêm do mapa da trava (gerado de valores.md); sem ele, quem chamou barra ou avisa o defeito."""
    return json.loads((PASTA.parent / "lugares.json").read_text(encoding="utf-8"))


def acordado_agora() -> float:
    """O relógio que para quando o Mac dorme e volta a zero quando ele liga: o tempo acordado desde que ligou."""
    return time.clock_gettime(time.CLOCK_UPTIME_RAW) if hasattr(time, "CLOCK_UPTIME_RAW") else time.monotonic()


def ligado_em() -> float:
    """Quando o Mac ligou (relógio da parede), pelo relógio que conta também o sono: a marca do boot."""
    com_sono = getattr(time, "CLOCK_MONOTONIC_RAW", getattr(time, "CLOCK_BOOTTIME", None))
    return time.time() - (time.clock_gettime(com_sono) if com_sono is not None else time.monotonic())


def mesmo_boot(a: float, b: float) -> bool:
    return abs(a - b) < 120


def deslocamento() -> float:
    """O relógio da parede menos o que para quando o Mac dorme: dentro de um mesmo boot, só cresce no sono."""
    return time.time() - acordado_agora()


def agora_no_historico() -> list:
    return [time.time(), deslocamento(), ligado_em(), acordado_agora()]


def historico_do_sono() -> list:
    """Um registro por trecho acordado: [parede, deslocamento, boot, acordado] do último sinal desse trecho. Um trecho novo
    começa quando o Mac dorme (o deslocamento muda) ou liga de novo (o boot muda)."""
    try:
        return [h for h in json.loads(SONO.read_text(encoding="utf-8")) if isinstance(h, list) and len(h) == 4]
    except (OSError, ValueError):
        return []


def anotar_sono() -> None:
    """Cada gancho chama: no mesmo trecho, o último sinal anda (no máximo uma gravação por minuto); depois de um sono ou de
    um boot, começa outro trecho. A gravação é atômica: um arquivo novo trocado de uma vez."""
    novo = agora_no_historico()
    historico = historico_do_sono()
    ultimo = historico[-1] if historico else None
    if ultimo and mesmo_boot(ultimo[2], novo[2]) and abs(novo[1] - ultimo[1]) < 60:
        if novo[0] - ultimo[0] < 10:
            return
        historico[-1] = novo
    else:
        historico.append(novo)
    historico = [h for h in historico if novo[0] - h[0] < 30 * 86400][-400:]
    SONO.parent.mkdir(parents=True, exist_ok=True)
    provisorio = SONO.with_name(f".historico-{os.getpid()}.json")
    provisorio.write_text(json.dumps(historico), encoding="utf-8")
    os.replace(provisorio, SONO)


def _trecho_de(quando: float, historico: list) -> list:
    """O trecho acordado em que `quando` caiu. Até o último sinal de um trecho, é dele. Depois do último sinal e antes do
    primeiro instante possível do trecho seguinte (o último sinal mais o sono que veio, ou o boot novo), ainda é dele: o Mac
    só dormiu depois. O que vem depois do último trecho guardado é o de agora."""
    trechos = historico + [agora_no_historico()]
    for h, seguinte in zip(trechos, trechos[1:]):
        if quando <= h[0]:
            return h
        if mesmo_boot(h[2], seguinte[2]):
            if seguinte[1] - h[1] >= 60 and quando < h[0] + (seguinte[1] - h[1]):
                return h
        elif quando < seguinte[2]:
            return h
    return trechos[-1]


def acordado_desde(inicio: float, fim: float | None = None) -> float:
    """Os segundos com o Mac acordado entre `inicio` e `fim` (agora, sem fim). No mesmo boot: a parede menos o sono. Com
    um reinício no meio: o que faltava do boot de `inicio` até o último sinal dele, mais os boots do meio, mais o do fim."""
    ate = time.time() if fim is None else fim
    historico = historico_do_sono()
    de = _trecho_de(inicio, historico)
    para = agora_no_historico() if fim is None else _trecho_de(ate, historico)
    if mesmo_boot(de[2], para[2]):
        return max(0.0, (ate - inicio) - max(0.0, para[1] - de[1]))
    ultimos: dict = {}
    for h in historico:  # o último sinal de cada boot: até ali o Mac estava acordado
        chave = next((k for k in ultimos if mesmo_boot(k, h[2])), h[2])
        ultimos[chave] = h
    do_inicio = next((h for k, h in ultimos.items() if mesmo_boot(k, de[2])), de)
    no_de = max(0.0, do_inicio[3] - (inicio - de[1]))
    meio = sum(h[3] for k, h in ultimos.items() if de[2] + 120 <= k <= para[2] - 120)
    no_fim = max(0.0, ate - para[1])
    return min(max(0.0, ate - inicio), no_de + meio + no_fim)


def ultimo_sono() -> tuple[float, float]:
    """(quando o Mac voltou, quantos segundos ficou dormindo ou desligado): o maior intervalo que terminou na última hora;
    (0, 0) sem nenhum."""
    historico = historico_do_sono()
    achados = []
    for antes, depois in zip(historico, historico[1:]):
        if mesmo_boot(antes[2], depois[2]):
            parado, voltou = depois[1] - antes[1], antes[0] + (depois[1] - antes[1])
        else:  # ligou de novo: do último sinal do boot anterior até o boot novo
            parado, voltou = depois[2] - antes[0], depois[2]
        if parado >= 60 and time.time() - voltou < 3600:
            achados.append((voltou, parado))
    return max(achados, key=lambda a: a[1]) if achados else (0.0, 0.0)


def esteiras_rodando(raiz: Path | None = None) -> list[tuple[list[str], list[str]]]:
    """As esteiras que rodam agora: (os nomes de quem entrega, os quadros abertos quando ela começou), pelo sinal que cada
    uma deixa em `.delta-11/esteira/rodando/<nomes>-<pid>` (o de um processo morto não conta)."""
    pasta = (raiz or motor.raiz(obrigatoria=False) or Path(".")) / ".delta-11" / "esteira" / "rodando"
    achadas = []
    for sinal in sorted(pasta.glob("*")) if pasta.is_dir() else []:
        m = re.fullmatch(r"(.+)-(\d+)", sinal.name)
        if not m:
            continue
        try:
            linhas = sinal.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        comeco = subprocess.run(["ps", "-o", "lstart=", "-p", m.group(2)], capture_output=True, text=True).stdout.strip()
        if not comeco or len(linhas) < 2 or linhas[1].strip() != comeco:
            try:
                sinal.unlink()  # o processo morreu (ou o número é de outro): o sinal sai
            except OSError:
                pass
            continue
        achadas.append((m.group(1).split(","), linhas[0].split()))
    return achadas


def quadro_se_mexe(registro: dict, raiz: Path) -> bool:
    """Algo nos quadros deste CRONOS mudou há menos de `travado_max` (Mac acordado): o `quadro.md`, uma linha, uma esteira."""
    limite = int(mapa()["travado_max_minutos"]) * 60
    quadros = {registro.get("quadro"), *registro.get("quadros", [])} - {None, ""}
    if any(set(dela) & quadros for _, dela in esteiras_rodando(raiz)):
        return True
    for quadro in quadros:
        pasta = raiz / ".delta-11" / "quadro" / quadro
        sinais = [a.stat().st_mtime for a in [pasta / "quadro.md", *(pasta / "linhas").glob("*.md")] if a.is_file()]
        if sinais and acordado_desde(max(sinais)) <= limite:
            return True
    return False


def processo_da_conversa() -> int:
    """O processo do programa de agentes desta conversa (o tradutor diz qual; no Claude Code, o ancestral chamado claude)."""
    return motor.processo_do_motor()


def roda(pid: int) -> bool:
    """A conversa daquele processo ainda roda (o processo vive e é do programa de agentes)."""
    return motor.processo_vivo(pid)


def registros() -> list[dict]:
    if not PASTA.is_dir():
        return []
    achados = []
    for arquivo in sorted(PASTA.glob("*.json")):
        try:
            dado = json.loads(arquivo.read_text(encoding="utf-8"))
        except ValueError:
            continue
        dado["_arquivo"] = str(arquivo)
        achados.append(dado)
    return achados


def gravar(nome: str, dado: dict) -> None:
    PASTA.mkdir(exist_ok=True)
    (PASTA / nome).write_text(json.dumps({k: v for k, v in dado.items() if not k.startswith("_")}), encoding="utf-8")


def trabalhando_em(quadro: str) -> list[dict]:
    """CRONOS desse quadro que estão trabalhando agora, numa conversa que ainda roda."""
    return [r for r in registros() if (r.get("quadro") == quadro or quadro in r.get("quadros", [])) and r.get("trabalhando")
            and roda(r.get("pid", 0)) and ativo(r)]


def velho(registro: dict) -> bool:
    """Outro CRONOS, de outra conversa, conduziu o mesmo quadro depois deste: o que este tem na memória ficou velho."""
    quadros = {registro.get("quadro"), *registro.get("quadros", [])} - {None, ""}
    return any(r.get("sessao") != registro.get("sessao") and quadros & {r.get("quadro"), *r.get("quadros", [])}
               and r.get("mudou", 0) > registro.get("mudou", 0) for r in registros())


def parado(agente: str) -> None:
    """O ATLAS parou o CRONOS (TaskStop): o gancho de fim não roda; ele deixa de trabalhar aqui (a vez dele conta até o último sinal)."""
    for r in registros():
        if r.get("agente") == agente:
            if r.get("trabalhando") and r.get("inicio_da_vez"):
                somar_trabalho(r.get("quadro", ""), vez_acordada(r))
            r.update({"trabalhando": False, "mudou": time.time(), "inicio_da_vez": 0})
            gravar(f"{agente}.json", r)
    (ARQUITETOS / f"{agente}.json").unlink(missing_ok=True)  # um ARQUITETO parado também deixa de barrar os outros


def quadro_aberto(raiz: Path, quadro: str) -> bool:
    """Uma camada ou pedido com abertura ou quadro, e a situação do quadro não diz selado, encerrado, feito nem parada."""
    pasta = raiz / ".delta-11" / "quadro" / quadro
    texto = (pasta / "quadro.md").read_text(encoding="utf-8") if (pasta / "quadro.md").is_file() else ""
    if not (pasta / "abertura.md").is_file() and not texto:
        return False
    m = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", texto, re.IGNORECASE)
    valor = m.group(1).strip().strip("*_ ").lower() if m else ""
    return not (valor.startswith(("selad", "encerrad", "feit")) or re.match(r"parada\b", valor))


TRABALHO = PASTA / "trabalho"


def fim_da_vez(registro: dict) -> float | None:
    """Agora (None); para um CRONOS caído (sem sinal), a última vez que a conversa dele mudou."""
    conversa = Path(registro.get("conversa_do_agente") or "")
    if conversa.is_file() and not ativo(registro):
        return min(time.time(), conversa.stat().st_mtime)
    return None


def vez_acordada(registro: dict) -> float:
    """Os segundos da vez em curso de um CRONOS, com o Mac acordado (o sono não é trabalho do time)."""
    return acordado_desde(registro["inicio_da_vez"], fim_da_vez(registro)) if registro.get("inicio_da_vez") else 0.0


def somar_trabalho(quadro: str, segundos: float) -> None:
    if not quadro or segundos <= 0:
        return
    TRABALHO.mkdir(parents=True, exist_ok=True)
    arquivo = TRABALHO / f"{quadro}.json"
    try:
        antes = float(json.loads(arquivo.read_text(encoding="utf-8")).get("segundos", 0))
    except (OSError, ValueError):
        antes = 0.0
    arquivo.write_text(json.dumps({"quadro": quadro, "segundos": antes + segundos}), encoding="utf-8")


def trabalho(quadro: str) -> int:
    """Os segundos de trabalho do time num quadro: as vezes dos CRONOS dele que terminaram, mais a que está em curso."""
    try:
        feito = float(json.loads((TRABALHO / f"{quadro}.json").read_text(encoding="utf-8")).get("segundos", 0))
    except (OSError, ValueError):
        feito = 0.0
    em_curso = sum(vez_acordada(r) for r in registros()
                   if r.get("quadro") == quadro and r.get("trabalhando") and r.get("inicio_da_vez") and roda(r.get("pid", 0)))
    return int(feito + em_curso)


def quadros_com_trabalho() -> list[str]:
    nomes = {a.stem for a in TRABALHO.glob("*.json")} if TRABALHO.is_dir() else set()
    return sorted(nomes | {r["quadro"] for r in registros() if r.get("quadro") and r.get("trabalhando") and r.get("inicio_da_vez")})


def frase_do_trabalho(quadros: list[str]) -> str:
    """O que o relógio diz: `Trabalho do time em <quadro>: <minutos> min`, um por quadro."""
    return " ".join(f"Trabalho do time em {q}: {trabalho(q) // 60} min." for q in quadros)


def anotar_quadro(agente: str, quadro: str) -> None:
    """O CRONOS que passa a conduzir outra pasta (uma reabertura) fica conhecido nela também."""
    for r in registros():
        if r.get("agente") == agente and quadro != r.get("quadro") and quadro not in r.get("quadros", []):
            r["quadros"] = sorted(set(r.get("quadros", [])) | {quadro})
            gravar(f"{agente}.json", r)


def ativo(registro: dict) -> bool:
    """Um CRONOS parado sem o gancho de fim (caído, interrompido) deixa de contar quando a conversa toda para de mudar
    por `silencio_max` com o Mac acordado: a dele e a dos agentes que ele chamou (esperando um lote longo, só a dos
    chamados muda). Uma esteira rodando num quadro dele é sinal: o Construtor espera a entrega, sem escrever."""
    conversa = Path(registro.get("conversa_do_agente") or "")
    if not conversa.is_file():
        return True
    quadros = {registro.get("quadro"), *registro.get("quadros", [])} - {None, ""}
    if any(set(dela) & quadros for _, dela in esteiras_rodando()):
        return True
    pasta = conversa.parent
    conversas = list(pasta.glob("*.jsonl"))  # a principal não conta: o ATLAS e o vigia dele a mudam sempre
    mudou = max(c.stat().st_mtime for c in conversas if c.is_file())
    return acordado_desde(mudou) < int(mapa()["silencio_max_minutos"]) * 60


def trabalhando_na_linha(linha: Path) -> bool:
    try:
        texto = linha.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    m = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", texto, re.IGNORECASE)
    return bool(m and m.group(1).strip().strip("*_ ").lower().startswith("trabalhando"))


def papel_da_linha(linha: Path) -> str:
    return re.sub(r"-\d+\.md$", "", linha.name).lower()


def travados(registro: dict, raiz: Path) -> list[str]:
    """As linhas dos agentes deste CRONOS com a situação "trabalhando" e paradas há mais de `travado_max` com o Mac
    acordado: o agente dá sinal e não avança (valores.md). Linha mudada antes deste CRONOS começar é de um lote que já
    acabou: não conta. A esteira rodando por um agente é sinal dele. A linha do próprio CRONOS só conta parada quando
    nada no quadro se mexe: nem o `quadro.md`, nem a linha de um agente, nem uma esteira (ele espera os que chamou)."""
    limite, comeco = int(mapa()["travado_max_minutos"]) * 60, registro.get("mudou", 0)
    rodando = esteiras_rodando(raiz)
    achados = []
    for quadro in sorted({registro.get("quadro"), *registro.get("quadros", [])} - {None, ""}):
        pasta = raiz / ".delta-11" / "quadro" / quadro
        linhas = sorted((pasta / "linhas").glob("*.md"))
        sinais = [a.stat().st_mtime for a in [pasta / "quadro.md", *linhas] if a.is_file()]
        quadro_vivo = bool(sinais and acordado_desde(max(sinais)) <= limite) or any(quadro in dela for _, dela in rodando)
        for linha in linhas:
            try:
                quando = linha.stat().st_mtime
            except OSError:
                continue
            if not trabalhando_na_linha(linha) or comeco > quando or acordado_desde(quando) <= limite:
                continue
            papel = papel_da_linha(linha)
            if (papel == "cronos" and quadro_vivo) or any(papel in nomes for nomes, _ in rodando):
                continue
            achados.append(f"{quadro}/linhas/{linha.name}")
    return achados


def parados_no_meio(raiz: Path) -> list[str]:
    """Os quadros abertos com linhas "trabalhando" paradas há mais de `silencio_max` (Mac acordado), sem nenhum CRONOS
    trabalhando neles e sem esteira: o trabalho parou no meio (a conversa fechou, o CRONOS caiu), mesmo que o quadro diga
    que espera o dono. Uma frase por quadro."""
    limite = int(mapa()["silencio_max_minutos"]) * 60
    rodando = esteiras_rodando(raiz)
    frases = []
    quadros = raiz / ".delta-11" / "quadro"
    for pasta in sorted(p for p in quadros.iterdir() if p.is_dir()) if quadros.is_dir() else []:
        if not quadro_aberto(raiz, pasta.name) or trabalhando_em(pasta.name.lower()) or any(pasta.name in dela for _, dela in rodando):
            continue
        paradas = [l.name for l in sorted((pasta / "linhas").glob("*.md")) if trabalhando_na_linha(l) and acordado_desde(l.stat().st_mtime) > limite]
        if paradas:
            frases.append(f"{pasta.name}: {', '.join(paradas)} dizem trabalhando, sem nenhum CRONOS vivo nele")
    return frases


def anotar_pedido_de_arquiteto(sessao: str) -> None:
    """A trava deixou chamar um ARQUITETO: até ele começar (`cronos_nascer_max`), o pedido já conta como um trabalhando."""
    ARQUITETOS.mkdir(parents=True, exist_ok=True)
    (ARQUITETOS / f"pedido-{int(time.time() * 1000)}.json").write_text(json.dumps({"sessao": sessao, "inicio": time.time(), "pedido": True}), encoding="utf-8")


def arquiteto(agente: str, sessao: str, inicio: bool, conversa: str) -> None:
    """Gancho de início e fim do ARQUITETO: um por vez (a trava recusa o segundo enquanto este trabalha)."""
    arquivo = ARQUITETOS / f"{agente}.json"
    if not inicio:
        arquivo.unlink(missing_ok=True)
        return
    ARQUITETOS.mkdir(parents=True, exist_ok=True)
    for pedido in sorted(ARQUITETOS.glob("pedido-*.json"))[:1]:  # o pedido que virou este ARQUITETO
        pedido.unlink(missing_ok=True)
    arquivo.write_text(json.dumps({"agente": agente, "sessao": sessao, "pid": processo_da_conversa(), "inicio": time.time(), "conversa": conversa}),
                       encoding="utf-8")


def arquitetos_trabalhando() -> list[dict]:
    """Os ARQUITETOS que trabalham agora: a conversa do Claude Code viva e a deles mudando há menos de `silencio_max`
    (o que caiu sem o gancho de fim deixa de contar, e o registro dele sai)."""
    limite = int(mapa()["silencio_max_minutos"]) * 60
    vivos = []
    for arquivo in sorted(ARQUITETOS.glob("*.json")) if ARQUITETOS.is_dir() else []:
        try:
            dado = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if dado.get("pedido"):
            if time.time() - dado.get("inicio", 0) < recente():
                vivos.append(dado)
            else:
                arquivo.unlink(missing_ok=True)
            continue
        conversa = Path(dado.get("conversa") or "")
        mudou = conversa.stat().st_mtime if conversa.is_file() else dado.get("inicio", 0)
        if roda(dado.get("pid", 0)) and acordado_desde(mudou) < limite:
            vivos.append(dado)
        else:
            arquivo.unlink(missing_ok=True)
    return vivos


def recente() -> int:
    """`cronos_nascer_max` (valores.md): um pedido de CRONOS que não começou nesse tempo não começa mais."""
    return int(mapa()["cronos_nascer_max_segundos"])


def pedidos_recentes(sessao: str) -> list[dict]:
    agora = time.time()
    return [r for r in registros() if r.get("sessao") == sessao and not r.get("agente") and agora - r.get("quando", 0) < recente()]


def anotar_pedido(quadro: str, sessao: str) -> None:
    gravar(f"pedido-{sessao}-{quadro}-{int(time.time() * 1000)}.json",
           {"quadro": quadro, "sessao": sessao, "pid": processo_da_conversa(), "trabalhando": False, "agente": "", "quando": time.time()})
