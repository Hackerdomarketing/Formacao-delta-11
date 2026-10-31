#!/usr/bin/env python3
"""
ADAPTADOR KILO — Delta-11 v7 (motor multiempresa).

O Kilo (fork do Roo Code, rodando dentro do VS Code) e o motor mais
diferente dos tres: NAO TEM HOOKS. O schema oficial de configuracao dele
(`app.kilo.ai/config.json`) nao tem a chave "hooks", e nao existe
"PreToolUse" em lugar nenhum do pacote. Entao o Kilo nao entrega o evento
da acao a um vigia por conta propria.

O QUE O KILO ENTREGA (medido em 2026-10-31):
  - O log em `~/.local/share/kilo/log/opencode.log` registra cada acao com
    `action.permission=<recurso>` e `action.action=allow|ask|deny`, onde o
    recurso e um de: bash, read, edit, glob, grep, agent, board, external.
  - As permissoes nativas sao por recurso e efeito:
        { "action": "edit", "resource": "src/**", "effect": "deny" }
    efeito = allow | ask | deny.
  - As sessoes do Agent Manager nascem em worktree Git (como o Claude Code),
    e cada sessao tem um `name` (ex.: "back-onda-2").

COMO O DELTA-11 FUNCIONA NESTE MOTOR
------------------------------------
O adaptador traduz o payload do PORTAO (`.delta-11/motor/porteiro/porteiro.py`)
para a forma que o nucleo entende. O portao e quem o agente chama antes de
agir — e quem aplica as permissoes nativas do Kilo como uma das camadas.

O payload do portao e um evento no MESMO formato do Claude Code:

    {"tool_name": "Write", "tool_input": {"file_path": "..."},
     "cwd": "...", "session_id": "...", "kilo_agent_id": "..."}

O campo `kilo_agent_id` e a MARCA do motor Kilo (o Claude Code nao tem; o
Codex tem `turn_id`). E por ela que a fachada sabe qual adaptador usar.

O que o Kilo faz de diferente do Claude Code:
  - As ferramentas de edicao no Kilo sao as mesmas (`edit`, `write`, `read`),
    mas o nome que chega no payload e o do Kilo. O adaptador aceita os dois
    conjuntos de nomes.
  - O despacho de sub-agente no Kilo e pelo Agent Manager, com `tasks[].name`
    (ex.: "back-onda-2") e `tasks[].agent`. O `name` e a chave mais forte
    para identificar o agente.

As permissoes NATIVAS do Kilo (o que o motor ganha de graca):
  - `edit` fora da zona do agente -> deny
  - `bash` com comando que mexe em arquivo travado -> deny (via porta)
  - `agent` (dispatch) sem o pre-despacho rodar -> deny
Estas regras sao geradas por `.delta-11/motor/kilo/gerar-permissoes.py`.
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

NOME = "kilo"

# O Kilo usa os mesmos nomes de edicao de arquivo. Aceitamos tambem os
# nomes do Claude Code, porque o portao pode ser chamado por qualquer um.
FERRAMENTAS_DE_ESCRITA = frozenset({"edit", "write", "Edit", "Write", "MultiEdit"})
FERRAMENTAS_DE_DISPATCH = frozenset({"agent", "Agent", "Task"})


def read_event() -> dict:
    """Le o evento JSON do stdin (o portao entrega o mesmo formato do hook)."""
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
    caminho = entrada.get("file_path") or entrada.get("path") or entrada.get("notebook_path") or ""
    return str(caminho) if caminho else ""


def absolute_target(evento: dict) -> Path | None:
    texto = target_path_text(evento)
    if not texto:
        return None
    caminho = Path(texto)
    if not caminho.is_absolute():
        caminho = event_cwd(evento) / caminho
    return Path(os.path.realpath(str(caminho)))


def event_key(evento: dict) -> str:
    """
    Chave do agente. No Kilo, o identificador da sessao do Agent Manager e
    `session_id` (formato "ses_...") e o do sub-agente e `kilo_agent_id`.
    """
    evento = evento or {}
    agent_id = evento.get("kilo_agent_id") or evento.get("agent_id")
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
    Alvo de um disparo de sub-agente. No Kilo, o despacho e pelo Agent
    Manager, com `tasks[].name` (ex.: "back-onda-2") e `tasks[].agent`.
    Ordem:
      1. `name` da entrada (ex.: "back-onda-2" -> BACK);
      2. `agent` da entrada, se ja for nome Delta-11;
      3. `agent_type`/`subagent_type` que ja e nome Delta-11;
      4. nome de sub-agente na `description`;
      5. linha "Sub-agente: .../<nome>.md" do prompt;
      6. linha "Agente: NOME" no prompt;
      7. o primeiro nome de sub-agente citado no prompt.
    """
    entrada = tool_input(evento)
    nome = str(entrada.get("name") or "")
    achado = re.match(r"([a-z]+)", nome.lower())
    if achado and achado.group(1).upper() in TODOS_OS_AGENTES:
        return achado.group(1).upper()
    for chave in ("agent", "agent_type", "subagent_type"):
        valor = str(entrada.get(chave) or "").upper()
        if valor in TODOS_OS_AGENTES:
            return valor
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
    return not (evento or {}).get("kilo_agent_id")


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
    if tipo and tipo.lower() != "general":
        return tipo
    if evento.get("kilo_agent_id"):
        return "SUBAGENTE"
    return "MAIN"


def before_and_after(evento: dict) -> tuple[str, str]:
    """(conteudo atual no disco, conteudo que ficara depois da acao)."""
    alvo = absolute_target(evento)
    antes = read_text(alvo)
    entrada = tool_input(evento)
    ferramenta = str(evento.get("tool_name") or "")

    if ferramenta in {"Write", "write", "edit"} and entrada.get("content") is not None:
        return antes, entrada.get("content") or ""
    if ferramenta in {"Edit", "edit"}:
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
