#!/usr/bin/env python3
"""
ADAPTADOR CODEX — Delta-11 v7 (motor multiempresa).

O Codex CLI (openai/codex) e o terceiro motor. Ele e o mais proximo do Claude
Code: tem hooks de verdade, com o MESMO formato de arquivo (`matcher` +
`hooks` + `command`) e o MESMO contrato de bloqueio (codigo de saida 2 + o
motivo no stderr). Por isso o grosso do motor e reuso.

Fatos medidos no binario do Codex (codex-cli 0.162.1) e na documentacao
oficial (developers.openai.com/codex/hooks), em 2026-10-31:

  PAYLOAD (o que chega no stdin do vigia):
    - `tool_name`: "Bash", "apply_patch", "exec_command", ou o nome de uma
      ferramenta MCP (ex.: "mcp__filesystem__read_file").
    - `tool_input`: para `apply_patch`, o campo `command` traz o patch no
      formato do Codex (ver abaixo). Para `Bash`, traz o comando.
    - `session_id`: "thr_123..." (o Codex usa prefixo `thr_`).
    - `transcript_path`: caminho do rollout.jsonl.
    - `cwd`: a pasta da acao.
    - `hook_event_name`: o evento ("PreToolUse", "PostToolUse", ...).
    - `turn_id`: marca EXCLUSIVA do Codex (o Claude Code nao tem).
    - `permission_mode`: "default" | "acceptEdits" | "plan" | "dontAsk" |
      "bypassPermissions" — tambem exclusiva.
    - `agent_type`: presente nos eventos de sub-agente (SubagentStart/Stop).

  FORMATO DO PATCH (extraido do binario):
    *** Begin Patch
    *** Update File: caminho/do/arquivo.py
    *** Add File: caminho/novo.py
    *** Delete File: caminho/apagado.py
    *** Move to: novo/caminho.py
    @@ contexto
    - linha removida
    + linha adicionada
    *** End Patch

  DIFERENCAS QUE IMPORTAM (e o que este adaptador resolve):
    1. O Codex edita arquivos por `apply_patch`, nao por `Write`/`Edit`. O
       patch traz o CAMINHO DENTRO do texto, nao em `file_path`. Este
       adaptador extrai o caminho e reconstrói o conteudo depois da edicao,
       para que os vigias que contam "o que mudou" (kanban, selo, conclusao
       de tarefa) continuem funcionando.
    2. O Codex casa `spawn_agent` como `Agent` no matcher, e o sub-agente
       e identificado por `agent_type` (o evento de sub-agente traz
       `agent_id` tambem).
    3. O Codex nao manda `agent_id` na sessao principal; a distincao
       principal/sub-agente vem de `agent_type` e do vinculo do ACK.

  ONDE OS HOOKS FICAM (documentacao oficial):
    - `<repo>/.codex/hooks.json`  (formato JSON, igual ao do Claude Code)
    - `<repo>/.codex/config.toml`  (tabelas [hooks] inline)
  O repositorio tambem pode ter `AGENTS.md` na raiz — o equivalente do
  `CLAUDE.md` para o Codex (lido automaticamente em cada execucao).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_NUCLEO_DIR = Path(__file__).resolve().parent.parent / "nucleo"
if str(_NUCLEO_DIR) not in sys.path:
    sys.path.insert(0, str(_NUCLEO_DIR))

from nucleo import (  # noqa: E402
    SUB_AGENTES,
    SUB_AGENTE_LINHA_RE,
    TODOS_OS_AGENTES,
    _apply_edit,
    _first_sub_agent,
    is_kanban,
    latest_ack_agent,
    load_links,
    read_text,
)

NOME = "codex"

# No Codex, `apply_patch` cobre o papel de Edit/Write/MultiEdit.
FERRAMENTAS_DE_ESCRITA = frozenset({"apply_patch", "Edit", "Write"})
# `spawn_agent` casa como "Agent" no matcher do Codex.
FERRAMENTAS_DE_DISPATCH = frozenset({"spawn_agent", "Agent", "Task"})

# ─── Extracao do patch do Codex ─────────────────────────────────────────────
_ARQUIVO_DO_PATCH_RE = re.compile(
    r"^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s*(.+?)\s*$", re.MULTILINE
)
_MOVER_DO_PATCH_RE = re.compile(r"^\*\*\*\s+Move to:\s*(.+?)\s*$", re.MULTILINE)


def _patch_do_evento(evento: dict) -> str:
    """O texto do patch, venha ele de onde vier."""
    entrada = tool_input(evento)
    comando = entrada.get("command")
    if isinstance(comando, str):
        return comando
    if isinstance(comando, list):
        # Forma em array: ["apply_patch", "*** Begin Patch\n..."]
        for parte in comando:
            if isinstance(parte, str) and "*** Begin Patch" in parte:
                return parte
    patch = entrada.get("patch")
    return patch if isinstance(patch, str) else ""


def _arquivos_do_patch(patch: str) -> list[str]:
    """Os caminhos tocados pelo patch, na ordem em que aparecem."""
    encontrados = _ARQUIVO_DO_PATCH_RE.findall(patch or "")
    if not encontrados:
        movo = _MOVER_DO_PATCH_RE.findall(patch or "")
        encontrados = movo
    return [p.strip() for p in encontrados if p and p.strip()]


def normalizar_evento(evento: dict) -> dict:
    """
    Traduz o payload do Codex para a forma que o nucleo entende.

    O nucleo e o Claude Code esperam `tool_input.file_path` e
    `tool_input.content`/`old_string`/`new_string`. O Codex manda o patch.
    Aqui traduzimos o patch para esses campos, sem perder a informacao
    original (o patch continua em `tool_input.command`).
    """
    if not isinstance(evento, dict):
        return evento
    entrada = evento.get("tool_input")
    if not isinstance(entrada, dict):
        return evento

    ferramenta = str(evento.get("tool_name") or "")
    if ferramenta not in FERRAMENTAS_DE_ESCRITA:
        return evento

    # Ja veio em forma Claude Code? Entao nao mexe.
    if entrada.get("file_path") or entrada.get("content") is not None:
        return evento

    patch = _patch_do_evento(evento)
    if not patch:
        return evento

    arquivos = _arquivos_do_patch(patch)
    if not arquivos:
        return evento

    novo = dict(entrada)
    novo["file_path"] = arquivos[0]
    novo["codex_patch"] = patch
    novo["codex_arquivos"] = arquivos

    # O conteudo depois da edicao, reconstruido do patch.
    if ferramenta == "apply_patch":
        depois = _aplicar_patch(texto_atual(evento, arquivos[0]), patch, arquivos[0])
        if depois is not None:
            novo["content"] = depois

    evento = dict(evento)
    evento["tool_input"] = novo
    # O Codex chama a edicao de arquivo de `apply_patch`; o restante do
    # sistema (vigias) conhece `Write`/`Edit`/`MultiEdit`. Traduzimos o NOME
    # da ferramenta aqui, no limite do motor, para que nenhum vigia precise
    # saber que o Codex existe.
    #
    # O Codex tem TRES operacoes de patch, distinguidas pelo conteudo:
    #   - so `+` (sem `-`): arquivo novo ou sobrescrita -> Write
    #   - com `-` e `+`: edicao de trecho existente -> Edit
    #   - com varios hunks: edicao multi-trecho       -> MultiEdit
    evento["tool_name"] = _ferramenta_de_escrita_do_patch(patch, arquivos)
    evento["_codex_tool_name_original"] = ferramenta
    return evento


def _ferramenta_de_escrita_do_patch(patch: str, arquivos: list[str]) -> str:
    """Traduz o patch do Codex para Write / Edit / MultiEdit."""
    tem_remocao = False
    hunks = 0
    for linha in (patch or "").splitlines():
        if linha.startswith("@@"):
            hunks += 1
        elif linha.startswith("-"):
            tem_remocao = True
    if not tem_remocao:
        return "Write"
    return "MultiEdit" if hunks > 1 else "Edit"


def texto_atual(evento: dict, caminho: str) -> str:
    """O conteudo atual do arquivo, lido do disco."""
    base = event_cwd(evento)
    alvo = Path(caminho)
    if not alvo.is_absolute():
        alvo = base / alvo
    return read_text(Path(os.path.realpath(str(alvo))))


def _aplicar_patch(antes: str, patch: str, caminho: str) -> str | None:
    """
    Reconstroi o conteudo do arquivo depois do patch.

    SEMANTICA DO CODEX (medida no binario): o patch e uma sequencia de
    "hunks" delimitados por `@@`. Cada hunk tem linhas de CONTEXTO (prefixo
    espaco), linhas REMOVIDAS (`-`) e linhas ADICIONADAS (`+`). O hunk
    substitui, no arquivo, o trecho formado por contexto + remocoes pelo
    trecho formado por contexto + adicoes.

    Diferente do diff unificado classico: o `@@` pode trazer um fragmento de
    codigo (`@@ def x():`) que NAO e parte do trecho — e so uma dica de
    onde ancorar.

    Devolve None quando o patch nao pode ser aplicado com seguranca (o
    trecho procurado nao existe no arquivo). O vigia entao trata como
    "antes == depois", que e o comportamento seguro: nao inventa conteudo.
    """
    if not patch:
        return None

    # 1. Isola os hunks deste arquivo.
    hunks: list[list[str]] = []
    hunk_atual: list[str] | None = None
    dentro_do_arquivo = False

    for linha in patch.splitlines():
        if linha.startswith("*** Update File:"):
            dentro_do_arquivo = caminho.strip() in linha
            hunk_atual = None
            continue
        if linha.startswith("*** Add File:"):
            dentro_do_arquivo = caminho.strip() in linha
            hunk_atual = None
            continue
        if linha.startswith("*** Delete File:"):
            dentro_do_arquivo = caminho.strip() in linha
            hunk_atual = None
            continue
        if linha.startswith("*** Move to:"):
            continue
        if linha.startswith("*** Begin Patch") or linha.startswith("*** End Patch"):
            continue
        if not dentro_do_arquivo:
            continue
        if linha.startswith("@@"):
            hunk_atual = []
            hunks.append(hunk_atual)
            continue
        if hunk_atual is not None:
            hunk_atual.append(linha)

    if not hunks:
        return None

    # 2. Aplica cada hunk, em ordem, sobre o texto.
    texto = antes
    for hunk in hunks:
        antigo: list[str] = []
        novo: list[str] = []
        for linha in hunk:
            if linha.startswith("-"):
                antigo.append(linha[1:])
            elif linha.startswith("+"):
                novo.append(linha[1:])
            elif linha.startswith(" "):
                antigo.append(linha[1:])
                novo.append(linha[1:])
            elif linha == "":
                # linha vazia no patch = linha vazia no arquivo
                antigo.append("")
                novo.append("")
            else:
                # sem prefixo: contexto literal
                antigo.append(linha)
                novo.append(linha)

        if not antigo:
            # hunk so de adicoes: insere no fim
            texto = texto + ("\n" if texto and not texto.endswith("\n") else "") + "\n".join(novo)
            continue

        # Procura o trecho "antigo" no texto. Tenta a posicao exata primeiro
        # (o caso comum: o Codex manda o trecho literal), depois qualquer
        # posicao.
        trecho = "\n".join(antigo)
        pos = texto.find(trecho)
        if pos < 0:
            # Ultimo recurso: compara linha a linha, ignorando espacos a direita
            linhas_texto = texto.splitlines()
            alvo = [l.rstrip() for l in antigo]
            encontrado = None
            for i in range(len(linhas_texto) - len(alvo) + 1):
                if [l.rstrip() for l in linhas_texto[i:i + len(alvo)]] == alvo:
                    encontrado = i
                    break
            if encontrado is None:
                return None  # nao da para aplicar com seguranca
            pos = len("\n".join(linhas_texto[:encontrado]))
            if encontrado > 0:
                pos += 1

        texto = texto[:pos] + "\n".join(novo) + texto[pos + len(trecho):]

    return texto


# ─── Contrato do adaptador ──────────────────────────────────────────────────
def read_event() -> dict:
    """Le o evento JSON do stdin. Vazio = {}. JSON quebrado = excecao."""
    bruto = sys.stdin.read()
    if not bruto.strip():
        return {}
    evento = json.loads(bruto)
    if not isinstance(evento, dict):
        raise ValueError("evento do hook nao e um objeto JSON")
    return evento


def event_cwd(evento: dict | None = None) -> Path:
    evento = evento if evento is not None else {}
    pasta = (evento or {}).get("cwd") or os.getcwd()
    return Path(pasta)


def tool_input(evento: dict) -> dict:
    entrada = (evento or {}).get("tool_input") or {}
    return entrada if isinstance(entrada, dict) else {}


def target_path_text(evento: dict) -> str:
    entrada = tool_input(evento)
    caminho = entrada.get("file_path") or entrada.get("path") or ""
    if caminho:
        return str(caminho)
    # O Codex traz o caminho dentro do patch
    arquivos = entrada.get("codex_arquivos") or []
    return str(arquivos[0]) if arquivos else ""


def absolute_target(evento: dict) -> Path | None:
    texto = target_path_text(evento)
    if not texto:
        return None
    caminho = Path(texto)
    if not caminho.is_absolute():
        caminho = event_cwd(evento) / caminho
    return Path(os.path.realpath(str(caminho)))


def event_key(evento: dict) -> str:
    """Chave do agente. O Codex usa `thr_...` como session_id."""
    evento = evento or {}
    agent_id = evento.get("agent_id")
    if agent_id:
        return f"agente:{agent_id}"
    return f"principal:{evento.get('session_id') or 'desconhecida'}"


def identify_agent(evento: dict | None = None, fallback_latest_ack: bool = True) -> str | None:
    evento = evento if evento is not None else {}
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
    Alvo de um disparo de sub-agente. No Codex, o sub-agente e criado por
    `spawn_agent`. Ordem:
      1. `name`/`agent` da entrada (ex.: "back-onda-2" -> BACK);
      2. `agent_type` que ja e nome Delta-11;
      3. `subagent_type` que ja e nome Delta-11;
      4. nome de sub-agente na `description`;
      5. linha "Sub-agente: .../<nome>.md" do prompt;
      6. linha "Agente: NOME" no prompt;
      7. o primeiro nome de sub-agente citado no prompt.
    """
    entrada = tool_input(evento)
    for chave in ("name", "agent", "agent_name"):
        nome = str(entrada.get(chave) or "")
        achado = re.match(r"([a-z]+)", nome.lower())
        if achado and achado.group(1).upper() in TODOS_OS_AGENTES:
            return achado.group(1).upper()
    for chave in ("agent_type", "subagent_type"):
        tipo = str(entrada.get(chave) or "").upper()
        if tipo in TODOS_OS_AGENTES:
            return tipo
    prompt = str(entrada.get("prompt") or "")
    sub = _first_sub_agent(str(entrada.get("description") or ""))
    if sub:
        return sub
    for achado in SUB_AGENTE_LINHA_RE.finditer(prompt):
        if achado.group(1).lower() in SUB_AGENTES:
            return achado.group(1).lower()
    achado = re.search(r"Agente:\s*([A-Z_-]+)", prompt)
    if achado:
        return achado.group(1).strip()
    return _first_sub_agent(prompt)


def is_main_session(evento: dict | None = None) -> bool:
    evento = evento if evento is not None else {}
    return not (evento or {}).get("agent_id")


def is_sub_agent_type(evento: dict | None = None) -> bool:
    evento = evento if evento is not None else {}
    tipo = str((evento or {}).get("agent_type") or "").lower()
    return tipo in SUB_AGENTES


def agent_label(evento: dict | None = None) -> str:
    evento = evento if evento is not None else {}
    evento = evento or {}
    nome = identify_agent(evento, fallback_latest_ack=False)
    if nome:
        return nome
    tipo = str(evento.get("agent_type") or "").strip()
    if tipo and tipo.lower() != "default":
        return tipo
    if evento.get("agent_id"):
        return "SUBAGENTE"
    return "MAIN"


def before_and_after(evento: dict) -> tuple[str, str]:
    """(conteudo atual no disco, conteudo que ficara depois da acao)."""
    alvo = absolute_target(evento)
    antes = read_text(alvo)
    entrada = tool_input(evento)
    ferramenta = str(evento.get("tool_name") or "")

    if ferramenta in {"Write", "Edit", "MultiEdit"} and entrada.get("content") is not None:
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


def is_kanban_event(evento: dict) -> bool:
    if str(evento.get("tool_name") or "") not in FERRAMENTAS_DE_ESCRITA:
        return False
    return is_kanban(target_path_text(evento)) or is_kanban(absolute_target(evento))
