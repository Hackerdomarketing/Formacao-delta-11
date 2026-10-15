#!/usr/bin/env python3
"""
Vigia PreToolUse "sistema no historico" — Delta-11 v6.4.1 (2026-10-15).

Problema que resolve: o `sincronizar.sh` (ou o comandante, ou o ATLAS) atualiza as
regras do sistema NO DISCO da pasta principal, mas cada worktree [copia isolada de
trabalho] nasce do HISTORICO do git (o ultimo commit). Enquanto as regras novas nao
forem commitadas, todo agente despachado com `isolation: "worktree"` le, dentro da
sua copia, os operativos/protocolos/perfis ANTIGOS. (Caso real: salvahacks,
2026-10-15 — o ATLAS percebeu sozinho depois da troca para a v6.4.1.)

Quando age (PreToolUse em Agent|Task): so quando o despacho pede
`isolation: "worktree"`. Confere `git status` da pasta principal SO nos arquivos de
sistema (ARQUIVOS_DE_SISTEMA abaixo). Se houver mudanca nao commitada, bloqueia
(exit 2) e mostra o comando exato que commita SO esses arquivos (nada do projeto).

Fora de repositorio git, ou sem mudanca nos arquivos de sistema: libera.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "sistema-no-historico"
ARQUIVOS_DE_SISTEMA = [
    "CLAUDE.md",
    ".claude/settings.json",
    ".delta-11/operativos",
    ".delta-11/protocolos",
    ".delta-11/sub-agentes",
    ".delta-11/templates",
    ".delta-11/conhecimento",
    ".delta-11/hooks",
    ".delta-11/ferramentas",
    ".delta-11/perfis",
    ".delta-11/mcp",
]


def uncommitted_system_files(raiz: str) -> list[str] | None:
    """Arquivos de sistema com mudanca nao commitada (None = nao e repositorio git)."""
    try:
        resultado = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *ARQUIVOS_DE_SISTEMA],
            cwd=raiz, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if resultado.returncode != 0:
        return None
    return [linha[3:] for linha in resultado.stdout.splitlines() if len(linha) > 3]


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Agent", "Task"}:
        return 0
    entrada = evento.get("tool_input") or {}
    if str(entrada.get("isolation") or "").lower() != "worktree":
        return 0
    raiz = str(comum.main_project_dir())
    if not os.path.isdir(os.path.join(raiz, ".delta-11")):
        return 0
    pendentes = uncommitted_system_files(raiz)
    if not pendentes:
        return 0
    # So os caminhos de sistema que TEM mudanca (todos existem no disco ou no historico): um caminho
    # inexistente na lista faria o `git add` inteiro falhar ("pathspec did not match").
    tocados = [c for c in ARQUIVOS_DE_SISTEMA if any(p == c or p.startswith(c + "/") for p in pendentes)]
    caminhos = " ".join(f"\"{c}\"" if " " in c else c for c in tocados)
    lista = "".join(f"  - {p}\n" for p in pendentes[:15])
    if len(pendentes) > 15:
        lista += f"  ... e mais {len(pendentes) - 15}\n"
    return comum.block(
        HOOK,
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — regras do sistema fora do historico do git\n"
        "\n"
        "Este despacho pede isolation: \"worktree\", e a worktree nasce do ULTIMO COMMIT.\n"
        f"Ha {len(pendentes)} arquivo(s) de sistema alterado(s) na pasta principal e ainda nao commitado(s):\n"
        f"{lista}"
        "O agente leria, dentro da worktree, as regras ANTIGAS.\n"
        "\n"
        "Commite SO os arquivos de sistema (nada do projeto entra) e despache de novo:\n"
        f"  cd \"{raiz}\"\n"
        f"  git add -A -- {caminhos}\n"
        f"  git commit -m \"chore(delta-11): guardar as regras do sistema no historico\" -- {caminhos}\n",
        f"despacho em worktree com {len(pendentes)} arquivo(s) de sistema fora do historico",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
