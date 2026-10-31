#!/usr/bin/env python3
"""
NUCLEO PORTATIL do Delta-11 — a parte que nao sabe nada sobre orquestrador.

Este arquivo contem a LOGICA do sistema que e identica em qualquer motor
(Claude Code, Kilo, Codex ou outro): leitura do kanban, contagem de tokens,
selos, limites, diario de atividades, pasta principal do projeto, contrato de
bloqueio (exit 2 + stderr) e leitura/escrita do product-core.

O que NAO esta aqui: tudo que depende do payload de um motor especifico
(como o agente se identifica, como o caminho do arquivo editado vem no
evento, como o alvo de um disparo e reconhecido). Isso vive nos adaptadores,
em `.delta-11/motor/<motor>/`, e e resolvido por `_comum.py` (a fachada).

Regra de ouro da Formacao: um fato, um lugar. Se algo precisa mudar para
suportar um motor novo, ele entra no adaptador — o nucleo nao cresce.

Gerado de `.delta-11/hooks/_comum.py` na v7 (motor multiempresa).
Requer Python 3.8+. Usa so a biblioteca padrao.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSAO = "v7-motor-multiempresa"

TODOS_OS_AGENTES = {
    "ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM",
    "BACK", "ENGINE", "VAULT", "SHIELD", "SCOUT",
}

# ═══════════════════════════════════════════════════════════════════════════
# Resolução tardia do contrato de motor
# ═══════════════════════════════════════════════════════════════════════════
# O nucleo usa 3 funcoes que dependem do motor: `event_cwd`, `agent_label` e
# `before_and_after`. Em vez de o nucleo saber de motor, ele pergunta ao
# ADAPTADOR em tempo de chamada. A fachada `_comum.py` registra o adaptador
# ativo aqui (ver `registrar_adaptador`).
#
# Sem adaptador registrado (uso direto do nucleo em teste), cai no
# comportamento padrao, que e o do Claude Code — o motor de referencia.

_ADAPTADOR_ATIVO = None


def registrar_adaptador(adaptador) -> None:
    """A fachada chama isto quando escolhe o motor da sessao."""
    global _ADAPTADOR_ATIVO
    _ADAPTADOR_ATIVO = adaptador


def _do_motor(nome: str, *args, **kwargs):
    """Chama uma funcao do adaptador ativo. Sem adaptador: comportamento padrao."""
    if _ADAPTADOR_ATIVO is not None:
        func = getattr(_ADAPTADOR_ATIVO, nome, None)
        if callable(func):
            return func(*args, **kwargs)
    return _MOTOR_PADRAO[nome](*args, **kwargs)


# O comportamento padrao (Claude Code) para cada funcao do contrato, usado
# quando nao ha adaptador registrado. E o mesmo do motor de referencia.
def _padrao_event_cwd(evento: dict | None = None) -> Path:
    evento = evento if evento is not None else _EVENTO_ATUAL
    pasta = (evento or {}).get("cwd") or os.getcwd()
    return Path(pasta)


def _padrao_agent_label(evento: dict | None = None) -> str:
    evento = evento if evento is not None else _EVENTO_ATUAL
    evento = evento or {}
    tipo = str(evento.get("agent_type") or "").strip()
    if tipo and tipo.lower() != "general-purpose":
        return tipo
    if evento.get("agent_id"):
        return "SUBAGENTE"
    return "MAIN"


def _padrao_before_and_after(evento: dict) -> tuple[str, str]:
    return "", ""


_MOTOR_PADRAO = {
    "event_cwd": _padrao_event_cwd,
    "agent_label": _padrao_agent_label,
    "before_and_after": _padrao_before_and_after,
}


EXECUTORES_SEM_PROJECT_CORE = {"VAULT", "BACK", "ENGINE", "FRONT", "PIXEL", "FORM"}

EXECUTORES = EXECUTORES_SEM_PROJECT_CORE | {"SCOUT"}

EXECUTORES_COM_SHIELD = EXECUTORES | {"SHIELD"}

SUB_AGENTES = {
    "build-validator", "contract-tester", "code-architect", "schema-validator",
    "verify-app", "fresh-reviewer", "cold-start-tester", "impact-mapper",
    "tool-provisioner", "qa-ui-tandem",
}

LIMITES_PADRAO = {
    "brief_max_tokens": 4000,
    "produto_max_tokens": 500,
    "paralelo_max": 5,
    "janela_horas": 4,
    "lock_horas": 2,
}

LIMITES_OPCIONAIS = {
    "contexto_janela_tokens": 1000000,  # memoria de curto prazo do agente (Opus/Sonnet atuais = 1 milhao); o projeto pode mudar
    "contexto_alerta_pct": 85,          # % a partir da qual o anti-autocompact trava
}

ARQUIVO_LIMITES = ".config-limites.json"

CHARS_POR_TOKEN = 4

MARCADOR_CONCLUSAO_RE = re.compile(r"\[[xX]\]|✅|\bCONCLU[IÍ]D[OA]S?\b", re.IGNORECASE)

TITULO_RE = re.compile(r"^(#{1,6})\s+(.*)$")

ID_TAREFA_RE = re.compile(r"\b(T-[A-Za-z0-9][A-Za-z0-9._-]*)", re.IGNORECASE)

ID_NEGRITO_RE = re.compile(r"\*\*\[?([A-Z][A-Z0-9]*-[A-Za-z0-9._-]+)\]?\*\*")

_NOMES = "|".join(sorted(TODOS_OS_AGENTES))

AGENTE_POR_RE = re.compile(rf"\bPor\s*:\s*\[?\s*({_NOMES})\b", re.IGNORECASE)

AGENTE_CAMPO_RE = re.compile(rf"\bAgente\s*:\s*\[?\s*({_NOMES})\b", re.IGNORECASE)

AGENTE_ETIQUETA_RE = re.compile(rf"\[({_NOMES})\]")

AGENTE_COLUNA_RE = re.compile(rf"\|\s*({_NOMES})\s*(?:\||$)")

CARIMBO_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2}))\]")

ARQUIVO_VINCULOS = "agentes-sessao.json"  # gravado pelo heartbeat.sh (D28)

SUB_AGENTE_LINHA_RE = re.compile(
    r"^[ \t>*_-]*Sub-agente\**\s*:\s*[`*]*\s*(?:\S*/)?([a-z][a-z-]*?)(?:\.md)?\b[`*]*",
    re.IGNORECASE | re.MULTILINE,
)

AJUSTE_MARCA_RE = re.compile(r"\[AJUSTE\]", re.IGNORECASE)

COMANDANTE_DECISAO_RE = re.compile(r"\[COMANDANTE\]\s+(APROVADO|REPROVADO)\s+([A-Za-z][\w.]*-[\w.-]+)", re.IGNORECASE)

_FASE_RE = {
    "3": r"3(?![.,]\d)",
    "3.5": r"3[.,]5",
    "4.5": r"4[.,]5",
    "7": r"7(?:[.,]0)?(?![.,]\d)",
}

_DIA_DA_FASE = {"3": "3", "3.5": "4", "4.5": "6", "7": "7"}

_ETIQUETAS_DA_FASE = {
    "3": [r"FUNDA[ÇC][ÃA]O"],
    "3.5": [r"RITMO"],
    "4.5": [r"CONSCI[ÊE]NCIA"],
    "7": [r"DESCANSO", r"CONSAGRA[ÇC][ÃA]O"],
}

_PALAVRA_SELO = r"(?:selad[ao]|consagrad[ao])"

_CONCLUIDA_COLADA = r"\s*[-—:]?\s*conclu[ií]d[ao]\b"

PENDENTE_RE = re.compile(r"^\s*[-*+]?\s*\[ \]")

ANY_SEAL_RE = re.compile(
    r"\[\s*SELO\s*(?:D[AO]\s+)?(?:FASE\s*)?\d+(?:[.,]\d)?\s*\]"
    rf"|\bFase\s*\d+(?:[.,]\d)?\b[^\n]{{0,40}}?\b{_PALAVRA_SELO}\b"
    rf"|\bFase\s*\d+(?:[.,]\d)?{_CONCLUIDA_COLADA}"
    r"|\bDia\s*[1-7]\b[^\n]{0,20}?\b(?:selad[ao]|consagrad[ao])\b",
    re.IGNORECASE,
)

FASE_ATUAL_RE = re.compile(r"\*{0,2}Fase atual:?\*{0,2}\s*:?\s*(.+)", re.IGNORECASE)

CICLO_ATUAL_RE = re.compile(r"\*{0,2}Ciclo\s+atual:?\*{0,2}\s*:?\s*\*{0,2}\s*(\d+)", re.IGNORECASE)

CICLO_NUMERO_RE = re.compile(r"\bCiclo\s*(\d+)", re.IGNORECASE)

FASE_ATUAL_JS_RE = re.compile(r"""\bfase_atual\s*:\s*(["'`])(.*?)\1""")

_SEM_MUDANCA_RE = re.compile(r"\bsem\s+mudan[çc]as?\b|\bn[ãa]o\s+se\s+aplica\b", re.IGNORECASE)

_MUDANCA_RE = re.compile(r"\bmud(?:ou|an[çc]as?)\s*[:—–-]\s*\S", re.IGNORECASE)

PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]|\{\{[^}]*\}\}|<[^>]*>|\(preencher[^)]*\)", re.IGNORECASE)



# ═══════════════════════════════════════════════════════════════════════════
# Tempo
# ═══════════════════════════════════════════════════════════════════════════
def now_utc() -> datetime:
    return datetime.now(timezone.utc)



def timestamp_utc() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")



def timestamp_for_filename() -> str:
    return now_utc().strftime("%Y%m%dT%H%M%SZ")



def parse_timestamp(texto: str) -> datetime | None:
    """Converte '2026-10-14T13:05:00Z' (ou com +00:00) em datetime com fuso."""
    if not texto:
        return None
    valor = texto.strip()
    if valor.endswith("Z"):
        valor = valor[:-1] + "+00:00"
    if re.search(r"[+-]\d{4}$", valor):
        valor = valor[:-2] + ":" + valor[-2:]
    try:
        data = datetime.fromisoformat(valor)
    except ValueError:
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return data



def line_timestamp(linha: str) -> datetime | None:
    achado = CARIMBO_RE.search(linha)
    return parse_timestamp(achado.group(1)) if achado else None



# ═══════════════════════════════════════════════════════════════════════════
# Pasta principal (D25)
# ═══════════════════════════════════════════════════════════════════════════
def _git(argumentos: list[str], pasta: Path) -> str | None:
    try:
        resultado = subprocess.run(
            ["git"] + argumentos, cwd=str(pasta),
            capture_output=True, text=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if resultado.returncode != 0:
        return None
    return resultado.stdout.strip() or None



def _nearest_delta_ancestor(inicio: Path, limite: Path | None) -> Path | None:
    atual = inicio
    while True:
        if (atual / ".delta-11").is_dir():
            return atual
        if limite is not None and atual == limite:
            return None
        if atual.parent == atual:
            return None
        atual = atual.parent



def main_project_dir(cwd: Path | None = None) -> Path:
    """Pasta principal do projeto (a que contem a .delta-11 compartilhada)."""
    pasta = Path(os.path.realpath(str(cwd if cwd is not None else _do_motor("event_cwd"))))
    if not pasta.is_dir():
        pasta = Path(os.path.realpath(os.getcwd()))
    comum = _git(["rev-parse", "--git-common-dir"], pasta)
    topo = _git(["rev-parse", "--show-toplevel"], pasta)
    if comum and topo:
        comum_abs = Path(comum)
        if not comum_abs.is_absolute():
            comum_abs = pasta / comum_abs
        raiz_principal = Path(os.path.realpath(str(comum_abs))).parent
        topo_abs = Path(os.path.realpath(topo))
        # A .delta-11 pode estar numa subpasta do repositorio
        ancestral = _nearest_delta_ancestor(pasta, topo_abs)
        if ancestral is not None:
            relativo = os.path.relpath(str(ancestral), str(topo_abs))
            candidato = Path(os.path.normpath(str(raiz_principal / relativo)))
            if (candidato / ".delta-11").is_dir():
                return candidato
            return ancestral
        return raiz_principal
    projeto = os.environ.get("CLAUDE_PROJECT_DIR")
    if projeto and Path(projeto).is_dir():
        return Path(os.path.realpath(projeto))
    ancestral = _nearest_delta_ancestor(pasta, None)
    return ancestral if ancestral is not None else pasta



def delta_dir(cwd: Path | None = None) -> Path:
    return main_project_dir(cwd) / ".delta-11"



def delta_dir_of_path(caminho: Path | None) -> Path | None:
    """A pasta .delta-11 que contem `caminho` (ou None)."""
    if caminho is None:
        return None
    for parte in [caminho] + list(caminho.parents):
        if parte.name == ".delta-11":
            return parte
    return None



# ═══════════════════════════════════════════════════════════════════════════
# Limites (D36)
# ═══════════════════════════════════════════════════════════════════════════
def limits(cwd: Path | None = None) -> dict:
    valores = dict(LIMITES_PADRAO)
    valores.update(LIMITES_OPCIONAIS)
    try:
        arquivo = delta_dir(cwd) / ARQUIVO_LIMITES
        if arquivo.is_file():
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            if isinstance(dados, dict):
                for chave, padrao in list(valores.items()):
                    novo = dados.get(chave)
                    if isinstance(novo, (int, float)) and not isinstance(novo, bool) and novo > 0:
                        valores[chave] = type(padrao)(novo)
    except (OSError, ValueError):
        pass
    return valores



def window_seconds(cwd: Path | None = None) -> float:
    return float(limits(cwd)["janela_horas"]) * 3600.0



def load_links() -> dict:
    """`chaves` de .delta-11/ativacoes/agentes-sessao.json (pasta principal)."""
    try:
        dados = json.loads((delta_dir() / "ativacoes" / ARQUIVO_VINCULOS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    chaves = dados.get("chaves") if isinstance(dados, dict) else None
    return chaves if isinstance(chaves, dict) else {}



def latest_ack_agent(ignorar: set | None = None) -> str | None:
    pasta = delta_dir() / "ativacoes"
    try:
        acks = sorted(pasta.glob("ack-*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for ack in acks:
        nome = ack.stem[len("ack-"):].upper()
        if nome in TODOS_OS_AGENTES and nome not in (ignorar or set()):
            return nome
    return None



def _first_sub_agent(texto: str) -> str:
    """Sub-agente citado PRIMEIRO no texto (posicao, nao ordem alfabetica)."""
    texto = texto.lower()
    posicoes = [(texto.find(sub), sub) for sub in SUB_AGENTES if sub in texto]
    return min(posicoes)[1] if posicoes else ""



# ═══════════════════════════════════════════════════════════════════════════
# Diario de atividades (D25 — formato unico)
# ═══════════════════════════════════════════════════════════════════════════
def log(hook: str, mensagem: str, agente: str | None = None) -> None:
    """- [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem"""
    try:
        rotulo = agente or _do_motor("agent_label")
        texto = " ".join(str(mensagem).split())
        arquivo = delta_dir() / "activity-log.md"
        if not arquivo.parent.is_dir():
            return  # projeto sem Delta-11: nao cria pastas por conta propria
        with arquivo.open("a", encoding="utf-8") as fh:
            fh.write(f"- [{timestamp_utc()}] [{hook}] [{rotulo}] {texto}\n")
    except OSError:
        pass



def block(hook: str, mensagem: str, resumo_log: str) -> int:
    """Bloqueio padrao (PreToolUse / UserPromptSubmit): stderr + diario + 2."""
    log(hook, f"BLOQUEIO: {resumo_log}")
    print(mensagem.rstrip() + "\n", file=sys.stderr)
    return 2



def run(main, hook: str) -> None:
    """
    Executa o main() do vigia e sai com o codigo certo.
    Erro interno (C-016): registra ERRO-INTERNO no diario, avisa no stderr e sai
    com 1 — o Claude Code mostra o aviso ao comandante e NAO bloqueia a acao.
    """
    try:
        codigo = main()
    except SystemExit as saida:
        codigo = saida.code if isinstance(saida.code, int) else (0 if saida.code is None else 1)
    except Exception as exc:  # noqa: BLE001
        descricao = f"{type(exc).__name__}: {exc}"
        try:
            log(hook, f"ERRO-INTERNO (acao liberada, vigia nao conferiu): {descricao}")
        except Exception:  # noqa: BLE001
            pass
        print(
            f"[{hook}] ERRO INTERNO DO VIGIA — a acao foi LIBERADA sem conferencia.\n"
            f"Detalhe: {descricao}\n"
            f"Registrado no activity-log como ERRO-INTERNO. Avise o comandante/CRONOS.",
            file=sys.stderr,
        )
        codigo = 1
    sys.exit(codigo if isinstance(codigo, int) else 0)



# ═══════════════════════════════════════════════════════════════════════════
# Conteudo antes / depois de Edit e Write
# ═══════════════════════════════════════════════════════════════════════════
def read_text(caminho: Path | None) -> str:
    if caminho is None:
        return ""
    try:
        return caminho.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""



def _apply_edit(texto: str, antigo: str, novo: str, todos: bool) -> str:
    if antigo == "":
        return novo if texto == "" else texto
    if antigo not in texto:
        return texto  # o Edit vai falhar: nada muda
    return texto.replace(antigo, novo) if todos else texto.replace(antigo, novo, 1)



def new_lines(antes: str, depois: str) -> list[str]:
    """Linhas (sem espacos nas pontas) que aparecem no depois e nao no antes."""
    contagem = Counter(l.strip() for l in antes.splitlines() if l.strip())
    novas = []
    for linha in depois.splitlines():
        chave = linha.strip()
        if not chave:
            continue
        if contagem.get(chave, 0) > 0:
            contagem[chave] -= 1
        else:
            novas.append(chave)
    return novas



# ═══════════════════════════════════════════════════════════════════════════
# Kanban (C-015, C-036)
# ═══════════════════════════════════════════════════════════════════════════
def is_kanban(caminho: Path | str | None) -> bool:
    """`.delta-11/kanban.md` — relativo ou absoluto, / ou \\."""
    if not caminho:
        return False
    texto = str(caminho).replace("\\", "/")
    return texto == ".delta-11/kanban.md" or texto.endswith("/.delta-11/kanban.md")



def task_id(linha: str) -> str | None:
    achado = ID_NEGRITO_RE.search(linha) or ID_TAREFA_RE.search(linha)
    return achado.group(1).upper() if achado else None



def is_light_track(linha: str) -> bool:
    """Tarefa do trilho leve: a linha do kanban traz [AJUSTE]."""
    return bool(AJUSTE_MARCA_RE.search(linha or ""))



def light_track_proof(tarefa: str | None) -> tuple[bool, str | None]:
    """
    Provas do trilho leve no activity-log, dentro da janela:
      (o vigia trilho-leve gravou "VISUAL-OK <tarefa>", ultima decisao do COMANDANTE para a tarefa).
    """
    if not tarefa:
        return False, None
    texto = read_text(delta_dir() / "activity-log.md")
    agora = now_utc()
    janela = window_seconds()
    visual_ok, decisao = False, None
    visual_re = re.compile(rf"\[trilho-leve\].*\bVISUAL-OK\s+{re.escape(tarefa)}\b", re.IGNORECASE)
    for linha in texto.splitlines():
        quando = line_timestamp(linha)
        if quando is None or (agora - quando).total_seconds() > janela:
            continue
        if visual_re.search(linha):
            visual_ok = True
        achado = COMANDANTE_DECISAO_RE.search(linha)
        if achado and achado.group(2).upper() == tarefa.upper():
            decisao = achado.group(1).upper()
    return visual_ok, decisao



def line_agent(linha: str) -> str | None:
    """Dono da tarefa: 'Por: X' > 'Agente: X' > '[X]' > '| X |'."""
    for padrao in (AGENTE_POR_RE, AGENTE_CAMPO_RE, AGENTE_ETIQUETA_RE, AGENTE_COLUNA_RE):
        achado = padrao.search(linha)
        if achado:
            return achado.group(1).upper()
    return None



def _is_content_line(linha: str) -> bool:
    texto = linha.strip()
    if not texto or texto.startswith("#") or texto.startswith("<!--") or texto.startswith(">"):
        return False
    if re.fullmatch(r"[-=*_|:\s]+", texto):
        return False
    return True



def concluded_lines(texto: str) -> dict[str, str]:
    """
    {chave: linha} das tarefas concluidas. Uma linha conta como concluida se:
      - esta numa secao cujo titulo tem CONCLU (ex.: '## ✅ CONCLUÍDO'), ou
      - tem caixa marcada [x], ✅ ou a palavra CONCLUIDO/CONCLUIDA.
    A chave e o ID da tarefa (T-012, **[ID]**) ou o texto normalizado.
    Comentarios HTML (<!-- ... -->) sao ignorados.
    """
    resultado: dict[str, str] = {}
    nivel_concluido = 0
    em_comentario = False
    for bruta in texto.splitlines():
        linha = bruta.strip()
        if em_comentario:
            if "-->" in linha:
                em_comentario = False
            continue
        if linha.startswith("<!--"):
            if "-->" not in linha:
                em_comentario = True
            continue
        titulo = TITULO_RE.match(linha)
        if titulo:
            nivel = len(titulo.group(1))
            if nivel_concluido and nivel <= nivel_concluido:
                nivel_concluido = 0
            if MARCADOR_CONCLUSAO_RE.search(titulo.group(2)):
                nivel_concluido = nivel
            continue
        if not _is_content_line(linha):
            continue
        if nivel_concluido or MARCADOR_CONCLUSAO_RE.search(linha):
            chave = task_id(linha) or _normalize(linha)
            resultado[chave] = linha
    return resultado



def _normalize(linha: str) -> str:
    texto = re.sub(r"\[[ xX]\]|✅", " ", linha)
    return " ".join(texto.lower().split())



def new_conclusions(antes: str, depois: str) -> list[str]:
    """Linhas concluidas no depois que NAO estavam concluidas no antes (C-036)."""
    ja = concluded_lines(antes)
    return [linha for chave, linha in concluded_lines(depois).items() if chave not in ja]



def kanban_change(evento: dict) -> tuple[str, str, list[str]]:
    """(antes, depois, novas_conclusoes) de uma edicao do kanban."""
    antes, depois = _do_motor("before_and_after", evento)
    return antes, depois, new_conclusions(antes, depois)



def seal_regex(fase: str) -> re.Pattern:
    f = _FASE_RE[fase]
    d = _DIA_DA_FASE[fase]
    partes = [
        rf"\[\s*SELO\s*(?:D[AO]\s+)?(?:FASE\s*)?{f}\s*\]",
        rf"\bFase\s*{f}\b[^\n]{{0,40}}?\b{_PALAVRA_SELO}\b",
        rf"\bFase\s*{f}{_CONCLUIDA_COLADA}",
        rf"\bDia\s*{d}\b[^\n]{{0,20}}?\b(?:selad[ao]|consagrad[ao])\b",
    ]
    for etiqueta in _ETIQUETAS_DA_FASE[fase]:
        partes.append(rf"\[{etiqueta}\][^\n]*\b(?:selad[ao]|consagrad[ao]|SELO)\b")
    return re.compile("|".join(partes), re.IGNORECASE)



def declares_seal(linhas: list[str], fase: str) -> list[str]:
    """
    Das linhas dadas, as que declaram o selo (fim) da fase.
    Linha de tarefa PENDENTE ("- [ ] ...") nunca e selo. "Selar a Fase N" so conta
    quando a linha esta concluida ([x], ✅, CONCLUIDO).
    """
    padrao = seal_regex(fase)
    selar = re.compile(rf"\bsel(?:ar|o|agem)\s+(?:d[ao]\s+)?Fase\s*{_FASE_RE[fase]}\b", re.IGNORECASE)
    achadas = []
    for linha in linhas:
        if PENDENTE_RE.match(linha):
            continue
        if padrao.search(linha) or (selar.search(linha) and MARCADOR_CONCLUSAO_RE.search(linha)):
            achadas.append(linha)
    return achadas



def current_phase(texto: str) -> str | None:
    for linha in texto.splitlines():
        achado = FASE_ATUAL_RE.search(linha)
        if achado:
            return " ".join(achado.group(1).split())
    return None



def phase_artifacts(prefixo: str, total: int, ciclo: int | None = None) -> tuple[list[int], list[int], list[str]]:
    """
    Entregaveis de fase em memoria/decisoes/ com nome `...<prefixo>-NN-*.md`.
    Retorna (numeros presentes, numeros faltando de 1..total, nomes encontrados).
    Arquivo vazio nao conta. Com `ciclo`, so conta o documento que cita "Ciclo N"
    no texto (documento completo feito NESTE ciclo, e nao herdado de um anterior).
    """
    pasta = delta_dir() / "memoria" / "decisoes"
    padrao = re.compile(rf"(?:^|-){re.escape(prefixo)}-(\d{{2}})(?:-|\.md$)", re.IGNORECASE)
    do_ciclo = re.compile(rf"\bCiclo\s*0*{int(ciclo)}(?!\d)", re.IGNORECASE) if ciclo else None
    presentes: set[int] = set()
    nomes: list[str] = []
    try:
        arquivos = sorted(pasta.iterdir()) if pasta.is_dir() else []
    except OSError:
        arquivos = []
    for arquivo in arquivos:
        if not arquivo.is_file() or not arquivo.name.lower().endswith(".md"):
            continue
        achado = padrao.search(arquivo.name)
        if not achado:
            continue
        numero = int(achado.group(1))
        try:
            vazio = arquivo.stat().st_size == 0
        except OSError:
            vazio = True
        if do_ciclo and not vazio and not do_ciclo.search(read_text(arquivo)):
            continue
        if 1 <= numero <= total and not vazio:
            presentes.add(numero)
            nomes.append(arquivo.name)
    faltando = [n for n in range(1, total + 1) if n not in presentes]
    return sorted(presentes), faltando, nomes



def cycle_in_text(texto: str | None) -> int | None:
    """Numero de "Ciclo N" num trecho de texto (o primeiro), ou None."""
    achado = CICLO_NUMERO_RE.search(texto or "")
    return int(achado.group(1)) if achado and int(achado.group(1)) >= 1 else None



def current_cycle(kanban_texto: str | None = None) -> int:
    """
    Numero do ciclo atual. Ordem de leitura:
      1. `**Ciclo atual:** N` no kanban.md (o texto dado ou, sem ele, o do disco);
      2. "Ciclo N" na linha `**Fase atual:**` do kanban.md;
      3. "Ciclo N" no campo `fase_atual` do kanban-data.js;
      4. sem informacao: 1 (o ciclo mais exigente — documentos completos).
    """
    if kanban_texto is None:
        kanban_texto = read_text(delta_dir() / "kanban.md")
    for linha in kanban_texto.splitlines():
        achado = CICLO_ATUAL_RE.search(linha)
        if achado and int(achado.group(1)) >= 1:
            return int(achado.group(1))
    numero = cycle_in_text(current_phase(kanban_texto))
    if numero:
        return numero
    achado = FASE_ATUAL_JS_RE.search(read_text(delta_dir() / "kanban-data.js"))
    numero = cycle_in_text(achado.group(2)) if achado else None
    return numero or 1



def _item_number_re(numero: int) -> re.Pattern:
    """Linha que comeca pelo numero do item: "| 01 |", "- 01.", "01)", "**01** —"."""
    return re.compile(
        rf"^\s*(?:[-*+]\s*)?(?:\[[ xX]\]\s*)?(?:\|\s*)?(?:\*\*)?0?{numero}(?:\*\*)?\s*(?:[|.):—–]|-\s)",
        re.IGNORECASE,
    )



def cycle_checklist(prefixo: str, ciclo: int, itens: dict[int, str]) -> tuple[str | None, list[tuple[int, str]]]:
    """
    Checklist do ciclo leve em memoria/decisoes/ (`...-<prefixo>-checklist-ciclo-N.md`).
    Retorna (nome do arquivo, pendencias). Sem arquivo (ou so arquivo vazio): (None, []).
    Pendencia = (numero do item, motivo). Cada item precisa de uma linha (com o numero
    ou o slug) que diga "sem mudanca" / "nao se aplica" ou "mudou: <o que mudou>"; os
    marcadores [..] do modelo nao contam. Se a linha cita um documento completo
    (`<prefixo>-NN-...md`), ele precisa existir e nao estar vazio.
    O vigia NAO julga se a mudanca era grande o bastante para exigir documento
    completo: quem confere isso e o SHIELD (protocolos fase-ritmo e fase-consciencia).
    """
    pasta = delta_dir() / "memoria" / "decisoes"
    nome_re = re.compile(
        rf"(?:^|-){re.escape(prefixo)}-checklist-ciclo-0*{int(ciclo)}(?!\d)[^/]*\.md$", re.IGNORECASE
    )
    citado_re = re.compile(rf"{re.escape(prefixo)}-(\d{{2}})-[A-Za-z0-9._-]*?\.md", re.IGNORECASE)
    presentes = set(phase_artifacts(prefixo, len(itens))[0])
    try:
        arquivos = sorted(pasta.iterdir()) if pasta.is_dir() else []
    except OSError:
        arquivos = []
    melhor: tuple[str | None, list[tuple[int, str]]] = (None, [])
    for arquivo in arquivos:
        if not arquivo.is_file() or not nome_re.search(arquivo.name):
            continue
        texto = read_text(arquivo)
        if not texto.strip():
            continue
        linhas = texto.splitlines()
        pendencias: list[tuple[int, str]] = []
        for numero, slug in sorted(itens.items()):
            por_numero = _item_number_re(numero)
            candidatas = [l for l in linhas if por_numero.search(l)]
            if not candidatas:  # sem linha numerada: procura o slug
                candidatas = [l for l in linhas if slug.lower() in l.lower()]
            candidatas = [PLACEHOLDER_RE.sub(" ", l) for l in candidatas]
            respondidas = [l for l in candidatas if _SEM_MUDANCA_RE.search(l) or _MUDANCA_RE.search(l)]
            if not candidatas:
                pendencias.append((numero, "item ausente no checklist"))
            elif not respondidas:
                pendencias.append((numero, 'sem resposta ("sem mudança" ou "mudou: ...")'))
            else:
                citados = {int(n) for l in respondidas for n in citado_re.findall(l)}
                if any(n not in presentes for n in citados):
                    pendencias.append((numero, "cita documento completo que nao existe (ou esta vazio)"))
        if melhor[0] is None or len(pendencias) < len(melhor[1]):
            melhor = (arquivo.name, pendencias)
    return melhor



# ═══════════════════════════════════════════════════════════════════════════
# Testes de contrato (validar-contratos-fim-fase e validar-deploy)
# ═══════════════════════════════════════════════════════════════════════════
def contract_test_command(raiz: Path) -> list[str] | None:
    """Comando dos testes de contrato do projeto (Node ou Python), ou None."""
    pacote = raiz / "package.json"
    if pacote.is_file():
        try:
            scripts = json.loads(pacote.read_text(encoding="utf-8")).get("scripts") or {}
        except (OSError, ValueError, AttributeError):
            scripts = {}
        if "test:contracts" in scripts and shutil.which("npm"):
            return [shutil.which("npm"), "run", "test:contracts"]
    tem_config = (raiz / "pytest.ini").is_file() or (raiz / "pyproject.toml").is_file()
    if tem_config and (raiz / "tests" / "contracts").is_dir():
        if shutil.which("pytest"):
            return [shutil.which("pytest"), "tests/contracts/"]
        if importlib.util.find_spec("pytest") is not None:
            return [sys.executable, "-m", "pytest", "tests/contracts/"]
    return None



def run_contract_tests(comando: list[str], raiz: Path, tempo_maximo: int) -> tuple[bool, str]:
    try:
        resultado = subprocess.run(
            comando, cwd=str(raiz), capture_output=True, text=True, timeout=tempo_maximo,
        )
    except subprocess.TimeoutExpired:
        return False, f"tempo esgotado ({tempo_maximo} s)"
    except OSError as erro:
        return False, f"falha ao executar: {erro}"
    saida = ((resultado.stdout or "") + "\n" + (resultado.stderr or "")).strip()
    return resultado.returncode == 0, saida[-2000:]



# ═══════════════════════════════════════════════════════════════════════════
# Markdown
# ═══════════════════════════════════════════════════════════════════════════
def section(texto: str, titulo_re: re.Pattern) -> str | None:
    """Conteudo da secao cujo titulo casa com `titulo_re` (ate o proximo titulo
    do mesmo nivel ou maior). None se nao existe."""
    linhas = texto.splitlines()
    for indice, linha in enumerate(linhas):
        achado = TITULO_RE.match(linha.strip())
        if not achado or not titulo_re.search(achado.group(2)):
            continue
        nivel = len(achado.group(1))
        corpo = []
        for seguinte in linhas[indice + 1:]:
            outro = TITULO_RE.match(seguinte.strip())
            if outro and len(outro.group(1)) <= nivel:
                break
            corpo.append(seguinte)
        return "\n".join(corpo)
    return None



def has_real_text(texto: str, minimo_letras: int = 3) -> bool:
    """True se, tirando marcadores [preencher], {{X}}, <...> e pontuacao, sobra texto."""
    limpo = PLACEHOLDER_RE.sub(" ", texto)
    limpo = re.sub(r"[*_`#>|:\-—–•]", " ", limpo)
    return len(re.findall(r"[A-Za-zÀ-ÿ]", limpo)) >= minimo_letras



def estimate_tokens(texto: str) -> int:
    return len(texto or "") // CHARS_POR_TOKEN



def is_inside(caminho: Path | None, pasta: Path) -> bool:
    if caminho is None:
        return False
    try:
        caminho.relative_to(pasta)
        return True
    except ValueError:
        return False
