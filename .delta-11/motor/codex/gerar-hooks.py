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

import argparse
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


def mesclar(usuario: dict, modelo: dict) -> dict:
    """
    Mescla os hooks do modelo do Δ-11 com os hooks que ja estavam no
    arquivo do usuario — SEM apagar os do usuario.

    É a MESMA politica que o Claude Code usa no `.claude/settings.json`
    (C-058): os hooks do Δ-11 entram; os outros ficam. Isso importa porque
    o usuario pode ter hooks proprios (notificacoes, ferramentas de third
    party) que NAO podem ser destruidos por uma sincronizacao.

    Os hooks do Δ-11 sao reconhecidos pelo caminho `.delta-11/hooks/` no
    comando. Se o arquivo do usuario ja tiver um hook do Δ-11 (de uma
    sincronizacao anterior), ele e substituido pelo novo — e nao
    duplicado.
    """
    def eh_do_delta11(handler: dict) -> bool:
        return ".delta-11/hooks/" in str(handler.get("command", ""))

    ph = usuario.get("hooks") or {}
    mh = modelo.get("hooks") or {}

    # Remove os hooks do Δ-11 que ja estavam no arquivo do usuario.
    limpo: dict[str, list] = {}
    for evento, grupos in ph.items():
        grupos_limpos = []
        for grupo in grupos:
            handlers = [h for h in (grupo.get("hooks") or []) if not eh_do_delta11(h)]
            if handlers:
                novo = dict(grupo)
                novo["hooks"] = handlers
                grupos_limpos.append(novo)
        if grupos_limpos:
            limpo[evento] = grupos_limpos

    # Junta: os do modelo primeiro, os do usuario depois.
    eventos = list(dict.fromkeys(list(mh.keys()) + list(limpo.keys())))
    resultado = dict(usuario)
    hooks: dict[str, list] = {}
    for evento in eventos:
        grupos = list(mh.get(evento, []))
        grupos.extend(limpo.get(evento, []))
        if grupos:
            hooks[evento] = grupos
    resultado["hooks"] = hooks
    if "description" in modelo:
        resultado["description"] = modelo["description"]
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera o hooks.json do Codex a partir do modelo do Δ-11.",
    )
    parser.add_argument(
        "--mesclar",
        help="Arquivo hooks.json existente para MESCLAR (em vez de gerar do zero).",
    )
    parser.add_argument(
        "--saida",
        help="Arquivo de saida. Sem isso, imprime na stdout.",
    )
    args = parser.parse_args()

    if not FONTE.is_file():
        print(f"ERRO: template do Claude Code nao encontrado em {FONTE}", file=sys.stderr)
        return 1
    origem = json.loads(FONTE.read_text(encoding="utf-8"))
    modelo = gerar(origem)

    if args.mesclar:
        caminho = Path(args.mesclar)
        if not caminho.is_file():
            print(f"ERRO: arquivo para mesclar nao encontrado: {caminho}", file=sys.stderr)
            return 1
        try:
            usuario = json.loads(caminho.read_text(encoding="utf-8"))
        except ValueError as exc:
            print(
                f"ERRO: {caminho} nao e um JSON valido ({exc}). "
                "NAO foi alterado — corija o JSON e rode de novo.",
                file=sys.stderr,
            )
            return 1
        resultado = mesclar(usuario, modelo)
    else:
        resultado = modelo

    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print(f"hooks.json do Codex escrito em {args.saida}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
