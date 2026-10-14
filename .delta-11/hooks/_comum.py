#!/usr/bin/env python3
"""
Utilitario comum dos vigias (hooks) Python do Delta-11 — v6.3 (2026-10-14).

NAO e um vigia: nao e registrado no settings. Os vigias importam este arquivo
(`import _comum`) para que todos facam as mesmas coisas do mesmo jeito:

  1. Descobrir a PASTA PRINCIPAL do projeto (D25): `git rev-parse --git-common-dir`
     -> a pasta principal e o pai desse resultado. Fora do git: CLAUDE_PROJECT_DIR;
     senao, a pasta atual. Assim, um agente dentro de uma worktree [copia isolada
     do projeto] grava diario, travas e memoria na pasta principal, que o CRONOS ve.
  2. Escrever no diario de atividades num formato UNICO (D25):
        - [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem
  3. Ler os limites configuraveis de `.delta-11/.config-limites.json` (D36), com
     valores padrao quando o arquivo falta ou esta quebrado.
  4. Reconhecer o kanban e as conclusoes de tarefa de um jeito so (C-015), olhando
     o ANTES e o DEPOIS da edicao (C-036): so conta o que mudou.
  5. Identificar o agente pelo `agent_id`/`agent_type` do evento (C-035).
  6. Tratar erro interno de vigia sempre igual (C-016): registra `ERRO-INTERNO` no
     diario, mostra aviso no stderr e sai com codigo 1 (o Claude Code mostra o aviso
     e NAO bloqueia). Nenhum vigia libera em silencio.

Identificacao do agente (C-035, D28):
  - O Claude Code manda `agent_id` e `agent_type` quando a acao acontece dentro de
    um sub-agente. Como os executores sao disparados com
    `subagent_type: "general-purpose"`, o `agent_type` nao diz qual agente e.
  - Por isso, quando um agente grava o proprio ACK (`ativacoes/ack-NOME.txt`, Passo
    0), o vigia heartbeat.sh anota o vinculo em `ativacoes/agentes-sessao.json`
    (chave "agente:<agent_id>" ou "principal:<session_id>" -> campo "agente").
    Este modulo so LE esse vinculo (um fato, um lugar).
  - Sem vinculo: o ACK mais recente, ignorando agentes vinculados a outra sessao.

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

VERSAO = "v6.3"

# ─── Agentes ────────────────────────────────────────────────────────────────
TODOS_OS_AGENTES = {
    "ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM",
    "BACK", "ENGINE", "VAULT", "SHIELD", "SCOUT",
}
# D6: executores que NAO leem o project-core.md inteiro (leem as fatias)
EXECUTORES_SEM_PROJECT_CORE = {"VAULT", "BACK", "ENGINE", "FRONT", "PIXEL", "FORM"}
# D11: executores que passam pela revisao do SHIELD
EXECUTORES = EXECUTORES_SEM_PROJECT_CORE | {"SCOUT"}
# Executores para regras de produto/despacho (inclui o SHIELD como executor de testes)
EXECUTORES_COM_SHIELD = EXECUTORES | {"SHIELD"}
SUB_AGENTES = {
    "build-validator", "contract-tester", "code-architect", "schema-validator",
    "verify-app", "fresh-reviewer", "cold-start-tester", "impact-mapper",
    "tool-provisioner", "qa-ui-tandem",
}

# ─── Limites (D36) ──────────────────────────────────────────────────────────
LIMITES_PADRAO = {
    "brief_max_tokens": 2000,
    "produto_max_tokens": 500,
    "paralelo_max": 3,
    "janela_horas": 4,
    "lock_horas": 2,
}
# Chaves opcionais (nao precisam estar no arquivo; valem estes padroes)
LIMITES_OPCIONAIS = {
    "contexto_janela_tokens": 200000,   # tamanho da memoria de curto prazo do modelo
    "contexto_alerta_pct": 85,          # % a partir da qual o anti-autocompact trava
}
ARQUIVO_LIMITES = ".config-limites.json"
CHARS_POR_TOKEN = 4

# ─── Marcadores de kanban (C-015) ───────────────────────────────────────────
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
# Evento
# ═══════════════════════════════════════════════════════════════════════════
_EVENTO_ATUAL: dict = {}


def read_event() -> dict:
    """Le o evento JSON do stdin. Vazio = {}. JSON quebrado = erro interno (C-016)."""
    global _EVENTO_ATUAL
    bruto = sys.stdin.read()
    if not bruto.strip():
        _EVENTO_ATUAL = {}
        return {}
    evento = json.loads(bruto)  # erro aqui vira ERRO-INTERNO visivel (run())
    if not isinstance(evento, dict):
        raise ValueError("evento do hook nao e um objeto JSON")
    _EVENTO_ATUAL = evento
    return evento


def event_cwd(evento: dict | None = None) -> Path:
    evento = evento if evento is not None else _EVENTO_ATUAL
    pasta = (evento or {}).get("cwd") or os.getcwd()
    return Path(pasta)


def tool_input(evento: dict) -> dict:
    entrada = evento.get("tool_input") or {}
    return entrada if isinstance(entrada, dict) else {}


def target_path_text(evento: dict) -> str:
    entrada = tool_input(evento)
    return entrada.get("file_path") or entrada.get("path") or entrada.get("notebook_path") or ""


def absolute_target(evento: dict) -> Path | None:
    """Caminho absoluto do arquivo alvo, resolvido contra o cwd do evento."""
    texto = target_path_text(evento)
    if not texto:
        return None
    caminho = Path(texto)
    if not caminho.is_absolute():
        caminho = event_cwd(evento) / caminho
    return Path(os.path.realpath(str(caminho)))


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
    pasta = Path(os.path.realpath(str(cwd if cwd is not None else event_cwd())))
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


# ═══════════════════════════════════════════════════════════════════════════
# Identidade do agente (C-035, D28)
# ═══════════════════════════════════════════════════════════════════════════
ARQUIVO_VINCULOS = "agentes-sessao.json"  # gravado pelo heartbeat.sh (D28)


def load_links() -> dict:
    """`chaves` de .delta-11/ativacoes/agentes-sessao.json (pasta principal)."""
    try:
        dados = json.loads((delta_dir() / "ativacoes" / ARQUIVO_VINCULOS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    chaves = dados.get("chaves") if isinstance(dados, dict) else None
    return chaves if isinstance(chaves, dict) else {}


def event_key(evento: dict) -> str:
    if evento.get("agent_id"):
        return f"agente:{evento['agent_id']}"
    return f"principal:{evento.get('session_id') or 'desconhecida'}"


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


def identify_agent(evento: dict | None = None, fallback_latest_ack: bool = True) -> str | None:
    """
    Nome do agente Delta-11 que fez a acao (D28), ou None. Ordem:
      1. `agent_type` do evento que ja e um nome Delta-11;
      2. vinculo em ativacoes/agentes-sessao.json — chave "agente:<agent_id>"
         (sub-agente) ou "principal:<session_id>" (sessao principal), campo
         "agente" (o heartbeat.sh grava o vinculo quando o agente escreve o ACK);
      3. (padrao) o ACK mais recente, IGNORANDO os agentes ja vinculados a outra
         sessao/sub-agente ainda ativo (assim o ATLAS da sessao principal nao e
         confundido com o BACK que acabou de fazer ACK numa worktree — C-035).
    """
    evento = evento if evento is not None else _EVENTO_ATUAL
    evento = evento or {}
    tipo = str(evento.get("agent_type") or "").strip().upper()
    if tipo in TODOS_OS_AGENTES:
        return tipo
    chaves = load_links()
    chave = event_key(evento)
    vinculo = chaves.get(chave)
    if isinstance(vinculo, dict):
        nome = str(vinculo.get("agente") or "").upper()
        if nome in TODOS_OS_AGENTES:
            return nome
    if not fallback_latest_ack:
        return None
    de_outros = {
        str(v.get("agente") or "").upper()
        for k, v in chaves.items()
        if k != chave and isinstance(v, dict) and v.get("agente") and not v.get("encerrado_em")
    }
    return latest_ack_agent(de_outros)


def dispatch_target(evento: dict) -> str:
    """
    Alvo de um disparo do Agent tool (Agent/Task). Ordem:
      1. campo `name` (ex.: "back-onda-2" -> BACK; "cronos" -> CRONOS);
      2. `subagent_type` que ja e nome Delta-11;
      3. linha "Agente: NOME" no prompt;
      4. nome de sub-agente (em minusculas) na descricao ou no prompt.
    "" se nao identificar.
    """
    entrada = tool_input(evento)
    nome = str(entrada.get("name") or "")
    achado = re.match(r"([a-z]+)", nome.lower())
    if achado and achado.group(1).upper() in TODOS_OS_AGENTES:
        return achado.group(1).upper()
    tipo = str(entrada.get("subagent_type") or "").upper()
    if tipo in TODOS_OS_AGENTES:
        return tipo
    prompt = str(entrada.get("prompt") or "")
    achado = re.search(r"Agente:\s*([A-Z_-]+)", prompt)
    if achado:
        return achado.group(1).strip()
    descricao = str(entrada.get("description") or "").lower()
    for sub in sorted(SUB_AGENTES):
        if sub in descricao or sub in prompt.lower():
            return sub
    return ""


def is_main_session(evento: dict | None = None) -> bool:
    evento = evento if evento is not None else _EVENTO_ATUAL
    return not (evento or {}).get("agent_id")


def is_sub_agent_type(evento: dict | None = None) -> bool:
    evento = evento if evento is not None else _EVENTO_ATUAL
    tipo = str((evento or {}).get("agent_type") or "").lower()
    return tipo in SUB_AGENTES


def agent_label(evento: dict | None = None) -> str:
    """Rotulo [AGENTE] do diario: nome, sub-agente, SUBAGENTE ou MAIN."""
    evento = evento if evento is not None else _EVENTO_ATUAL
    evento = evento or {}
    nome = identify_agent(evento, fallback_latest_ack=False)
    if nome:
        return nome
    tipo = str(evento.get("agent_type") or "").strip()
    if tipo and tipo.lower() != "general-purpose":
        return tipo
    if evento.get("agent_id"):
        return "SUBAGENTE"
    return "MAIN"


# ═══════════════════════════════════════════════════════════════════════════
# Diario de atividades (D25 — formato unico)
# ═══════════════════════════════════════════════════════════════════════════
def log(hook: str, mensagem: str, agente: str | None = None) -> None:
    """- [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem"""
    try:
        rotulo = agente or agent_label()
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


def before_and_after(evento: dict) -> tuple[str, str]:
    """(conteudo atual no disco, conteudo que ficara depois do Edit/Write)."""
    alvo = absolute_target(evento)
    antes = read_text(alvo)
    entrada = tool_input(evento)
    ferramenta = evento.get("tool_name", "")
    if ferramenta == "Write":
        return antes, entrada.get("content") or ""
    if ferramenta == "Edit":
        return antes, _apply_edit(
            antes, entrada.get("old_string") or "", entrada.get("new_string") or "",
            bool(entrada.get("replace_all")),
        )
    if ferramenta == "MultiEdit":
        depois = antes
        for item in entrada.get("edits") or []:
            if isinstance(item, dict):
                depois = _apply_edit(
                    depois, item.get("old_string") or "", item.get("new_string") or "",
                    bool(item.get("replace_all")),
                )
        return antes, depois
    return antes, antes


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


def is_kanban_event(evento: dict) -> bool:
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return False
    return is_kanban(target_path_text(evento)) or is_kanban(absolute_target(evento))


def task_id(linha: str) -> str | None:
    achado = ID_NEGRITO_RE.search(linha) or ID_TAREFA_RE.search(linha)
    return achado.group(1).upper() if achado else None


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
    antes, depois = before_and_after(evento)
    return antes, depois, new_conclusions(antes, depois)


# ─── Selo de fase ───────────────────────────────────────────────────────────
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
# "concluida" so vale colada no nome da fase ("Fase 3 concluída"), para que um
# resumo como "Fase 3 — 2 tarefas concluídas" nao seja lido como selo.
_CONCLUIDA_COLADA = r"\s*[-—:]?\s*conclu[ií]d[ao]\b"


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


PENDENTE_RE = re.compile(r"^\s*[-*+]?\s*\[ \]")


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


ANY_SEAL_RE = re.compile(
    r"\[\s*SELO\s*(?:D[AO]\s+)?(?:FASE\s*)?\d+(?:[.,]\d)?\s*\]"
    rf"|\bFase\s*\d+(?:[.,]\d)?\b[^\n]{{0,40}}?\b{_PALAVRA_SELO}\b"
    rf"|\bFase\s*\d+(?:[.,]\d)?{_CONCLUIDA_COLADA}"
    r"|\bDia\s*[1-7]\b[^\n]{0,20}?\b(?:selad[ao]|consagrad[ao])\b",
    re.IGNORECASE,
)
FASE_ATUAL_RE = re.compile(r"\*{0,2}Fase atual:?\*{0,2}\s*:?\s*(.+)", re.IGNORECASE)


def current_phase(texto: str) -> str | None:
    for linha in texto.splitlines():
        achado = FASE_ATUAL_RE.search(linha)
        if achado:
            return " ".join(achado.group(1).split())
    return None


def phase_artifacts(prefixo: str, total: int) -> tuple[list[int], list[int], list[str]]:
    """
    Entregaveis de fase em memoria/decisoes/ com nome `...<prefixo>-NN-*.md`.
    Retorna (numeros presentes, numeros faltando de 1..total, nomes encontrados).
    Arquivo vazio nao conta.
    """
    pasta = delta_dir() / "memoria" / "decisoes"
    padrao = re.compile(rf"(?:^|-){re.escape(prefixo)}-(\d{{2}})(?:-|\.md$)", re.IGNORECASE)
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
        if 1 <= numero <= total and not vazio:
            presentes.add(numero)
            nomes.append(arquivo.name)
    faltando = [n for n in range(1, total + 1) if n not in presentes]
    return sorted(presentes), faltando, nomes


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


PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]|\{\{[^}]*\}\}|<[^>]*>|\(preencher[^)]*\)", re.IGNORECASE)


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
