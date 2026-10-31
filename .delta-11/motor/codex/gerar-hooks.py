#!/usr/bin/env python3
"""
GERADOR DO ARQUIVO DE HOOKS DO CODEX — Delta-11 v7 (motor multiempresa).

O Codex CLI le hooks de `<repo>/.codex/hooks.json` (ou de tabelas [hooks] em
`<repo>/.codex/config.toml`). O FORMATO e o mesmo do Claude Code — `matcher`
+ `hooks` + `command` — mas o caminho da variavel de ambiente e diferente:

  Claude Code:  $CLAUDE_PROJECT_DIR   (a pasta do projeto)
  Codex:        nao tem equivalente — usa-se a RAIZ DO GIT, que e onde o
                Codex procura os hooks de repo (`<repo>/.codex/hooks.json`).

Por isso o comando gerado usa `$(git rev-parse --show-toplevel)`, que e a
pratica recomendada pela propria documentacao do Codex ("prefer resolving
from the git root instead of using a relative path").

DIFERENCAS DE MATCHER (o Codex casa por nome de ferramenta):
  - O Codex edita arquivos por `apply_patch`, nao por `Write`/`Edit`.
    Entao todo matcher que era "Edit|Write" vira "apply_patch|Edit|Write".
    (A documentacao do Codex diz: "matcher values can use `apply_patch`,
    `Edit`, or `Write`".)
  - O Codex dispara sub-agente por `spawn_agent`, que casa como `Agent`.
    Entao "Agent|Task" vira "spawn_agent|Agent|Task".
  - `Bash` continua `Bash` (o Codex tambem casa `exec_command` como Bash).

O resto do arquivo e o mesmo: o codigo de saida 2 bloqueia, com o motivo no
stderr (contrato igual ao do Claude Code).

Uso:
  python3 .delta-11/motor/codex/gerar-hooks.py [projeto]
      imprime o hooks.json pronto. Sem argumento, usa a pasta atual.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FONTE = AQUI.parent.parent / "templates" / "settings-hooks.json"

# Matcher do Claude Code -> matcher do Codex.
MATCHERS = {
    "Edit|Write": "apply_patch|Edit|Write",
    "Edit|Write|MultiEdit": "apply_patch|Edit|Write|MultiEdit",
    "Agent|Task": "spawn_agent|Agent|Task",
    "Agent|Task|Bash|Edit|Write": "spawn_agent|Agent|Task|Bash|apply_patch|Edit|Write",
}

# O Codex nao conhece estes eventos (medido na doc oficial):
#   SessionEnd -> existe no Codex; SubagentStop -> existe.
EVENTOS_INEXISTENTES = {"Notification"}

# $CLAUDE_PROJECT_DIR -> raiz do git (o Codex nao tem essa variavel).
def _converter_comando(comando: str) -> str:
    return comando.replace(
        '"$CLAUDE_PROJECT_DIR/', '"$(git rev-parse --show-toplevel)/'
    )


def _converter_matcher(matcher: str | None) -> str | None:
    if matcher is None:
        return None
    if matcher in MATCHERS:
        return MATCHERS[matcher]
    # matchers compound (ex.: "Edit|Write|Agent"): converte parte a parte
    partes = matcher.split("|")
    convertidas = []
    for parte in partes:
        if parte == "Edit":
            convertidas.append("apply_patch")
        elif parte == "Write":
            convertidas.append("Write")
        elif parte == "Agent":
            convertidas.append("spawn_agent")
        elif parte == "Task":
            convertidas.append("Task")
        else:
            convertidas.append(parte)
    saida = "|".join(convertidas)
    # nao repetir o mesmo nome
    vistas: list[str] = []
    for p in saida.split("|"):
        if p not in vistas:
            vistas.append(p)
    return "|".join(vistas)


def gerar(origem: dict) -> dict:
    """Converte o settings-hooks.json do Claude Code no hooks.json do Codex."""
    saida: dict = {"description": "Vigias da Formação Δ-11 (motor Codex)."}
    hooks: dict = {}
    for evento, grupos in (origem.get("hooks") or {}).items():
        if evento in EVENTOS_INEXISTENTES:
            continue
        novos_grupos = []
        for grupo in grupos:
            matcher = _converter_matcher(grupo.get("matcher"))
            handlers = []
            for h in grupo.get("hooks", []):
                novo = dict(h)
                novo["command"] = _converter_comando(h.get("command", ""))
                handlers.append(novo)
            if not handlers:
                continue
            novo_grupo: dict = {"hooks": handlers}
            if matcher:
                novo_grupo["matcher"] = matcher
            novos_grupos.append(novo_grupo)
        if novos_grupos:
            hooks[evento] = novos_grupos
    saida["hooks"] = hooks
    return saida


def main() -> int:
    if not FONTE.is_file():
        print(f"ERRO: template do Claude Code nao encontrado em {FONTE}", file=sys.stderr)
        return 1
    origem = json.loads(FONTE.read_text(encoding="utf-8"))
    resultado = gerar(origem)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
