#!/usr/bin/env python3
"""
ADAPTADOR CLAUDE CODE — Delta-11 v7 (motor multiempresa).

Este e o motor ORIGINAL: o Claude Code entrega o evento da acao no stdin em
JSON e os 37 vigias do Delta-11 sao registrados em `.claude/settings.json`
(gerado de `.delta-11/templates/settings-hooks.json`).

Fatos sobre o payload do Claude Code (medidos em 2026-10-31):
  - `tool_name`: "Edit", "Write", "MultiEdit", "Read", "Bash", "Agent", "Task"...
  - `tool_input`: {"file_path": ..., "content": ..., "old_string": ...,
                   "new_string": ..., "replace_all": bool, "edits": [...]}
  - `agent_id` / `agent_type`: presentes quando a acao e de um sub-agente;
    `agent_type` vale "general-purpose" para os executores do Delta-11, entao
    NAO diz qual agente e (o vinculo vem do ACK, ver `identify_agent`).
  - `session_id`: da sessao.
  - `cwd`: a pasta da acao (a worktree, quando o agente esta numa).

O `CLAUDE_PROJECT_DIR` so e usado como FALLBACK em `main_project_dir`
(dentro do nucleo): a pasta principal e descoberta pelo git, que e o jeito
que funciona em worktree.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

NOME = "claude-code"

FERRAMENTAS_DE_ESCRITA = frozenset({"Edit", "Write", "MultiEdit"})
FERRAMENTAS_DE_DISPATCH = frozenset({"Agent", "Task"})

# Dependencias do NUCLEO (a parte que nao sabe de motor). Importadas pelo
# caminho relativo, porque o adaptador vive dois niveis abaixo dos hooks.
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

# O evento lido do stdin. As funcoes que recebem `evento=None` usam este
# valor como PADRAO.
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



def event_key(evento: dict) -> str:
    if evento.get("agent_id"):
        return f"agente:{evento['agent_id']}"
    return f"principal:{evento.get('session_id') or 'desconhecida'}"



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
      3. nome de sub-agente na `description` (o primeiro citado);
      4. linha "Sub-agente: .../<nome>.md" do prompt;
      5. linha "Agente: NOME" no prompt;
      6. o primeiro nome de sub-agente citado no resto do prompt.
    "" se nao identificar.
    v6.4: os passos 3 e 4 vem antes do resto do prompt. Antes, a busca olhava o
    prompt inteiro em ordem alfabetica e um contract-tester (cujo texto cita o
    build-validator) aparecia como "build-validator".
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



def is_kanban_event(evento: dict) -> bool:
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return False
    return is_kanban(target_path_text(evento)) or is_kanban(absolute_target(evento))
