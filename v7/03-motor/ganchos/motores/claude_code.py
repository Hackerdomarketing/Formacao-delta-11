"""Tradutor do Claude Code (o programa em que o v7 nasceu): o evento dele já é o pedido comum do motor.

A tradução é a identidade: os nomes das ferramentas e a entrada delas são os do Claude Code. Acrescenta só o nome comum
do evento, a lista dos arquivos que a ação escreve (um só no Claude Code) e o caminho da conversa do agente chamado.
Campos que o Claude Code manda e o motor não usa (permission_mode, prompt_id, effort, tool_use_id...) ficam de fora:
nenhum deles diz qual programa é, nem muda o que a trava decide.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

NOME = "Claude Code"
SEM_RAIZ = "sem CLAUDE_PROJECT_DIR não dá para saber onde fica o produto."
EVENTOS = {"PreToolUse": "antes", "PostToolUse": "depois", "SessionStart": "abertura",
           "SubagentStart": "inicio-de-agente", "SubagentStop": "fim-de-agente"}
ESCREVEM = ("Write", "Edit", "NotebookEdit")


def traduzir(evento: dict) -> dict:
    ferramenta = evento.get("tool_name", "")
    dados = evento.get("tool_input") or {}
    agente = evento.get("agent_id") or ""
    caminho = (dados.get("file_path") or dados.get("notebook_path") or "") if ferramenta in ESCREVEM and isinstance(dados, dict) else ""
    return {
        "evento": EVENTOS.get(str(evento.get("hook_event_name") or ""), ""),
        "papel": (evento.get("agent_type") or "").lower(),
        "agente_id": agente,
        "sessao": evento.get("session_id") or "",
        "pasta": evento.get("cwd") or "",
        "ferramenta": ferramenta,
        "dados": dados,
        "arquivos": [caminho] if caminho else [],
        "origem": evento.get("source") or "",
        "conversa": evento.get("transcript_path") or "",
        # A do agente chamado vem no fim dele; no começo, fica ao lado da conversa principal, em subagents/.
        "conversa_do_agente": evento.get("agent_transcript_path")
        or (str(evento.get("transcript_path", "")).removesuffix(".jsonl") + f"/subagents/agent-{agente}.jsonl"),
    }


def raiz() -> Path | None:
    valor = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(valor) if valor else None


def avisar(texto: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": texto}}))


def processo_do_motor() -> int:
    """O processo do Claude Code desta conversa: o primeiro ancestral cujo programa se chama claude."""
    pid = os.getpid()
    for _ in range(8):
        saida = subprocess.run(["ps", "-o", "ppid=,comm=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
        if not saida:
            return 0
        pai, _, _ = saida.partition(" ")
        pid = int(pai)
        if pid <= 1:
            return 0
        nome = subprocess.run(["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
        if os.path.basename(nome) == "claude":
            return pid
    return 0


def processo_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    nome = subprocess.run(["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return os.path.basename(nome) == "claude"


def pastas_privadas() -> list[Path]:
    return [Path.home() / ".claude" / "projects"]


def caches_liberados(principal: Path) -> list[Path]:
    """Os que a caixa de areia do Claude Code libera para gravar (`allowWrite` de `.claude/settings.json`)."""
    config = json.loads((principal / ".claude" / "settings.json").read_text(encoding="utf-8"))
    return [Path(c).expanduser() for c in config.get("sandbox", {}).get("filesystem", {}).get("allowWrite", [])]
