#!/usr/bin/env python3
"""
Vigia PreToolUse "guarda de worktree" — Delta-11 v6.3 (2026-10-14). C-006, C-016.

Dispara ANTES de Edit/Write. Bloqueia tres erros silenciosos:

CASO A — bug Anthropic #39886: agente despachado com isolation:worktree nasce no
  repo PRINCIPAL sem avisar. Sintoma: a sessao esta no repo principal, existem
  worktrees [copias isoladas] de execucao ativas e o alvo e CODIGO (fora de
  .delta-11/, .claude/ e CLAUDE.md). A edicao e bloqueada — codigo so nasce dentro
  de worktree. Escape do comandante: criar `.delta-11/.permitir-edicao-main`.

CASO B — erro inverso: agente DENTRO da worktree edita um arquivo COMPARTILHADO
  da .delta-11 (kanban, kanban-data.js, pulsos-data.js, monitor-data.js,
  activity-log, memoria/, ativacoes/, locks/, logs/, planos/) pela copia da
  worktree — que e invisivel para o CRONOS (D25). Bloqueado com o caminho certo.

CASO C — de dentro da worktree, editar CODIGO do repo principal por caminho
  absoluto (o CASO A pela porta dos fundos).

Versao executavel do Passo 0.VW. Fora de repositorio git ou de projeto Delta-11,
nao se aplica.

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

HOOK = "guarda-worktree"
ARQUIVO_DE_ESCAPE = ".permitir-edicao-main"
COMPARTILHADOS_DO_DELTA = (
    "kanban.md", "kanban-data.js", "pulsos-data.js", "monitor-data.js",
    "activity-log.md", "memoria", "ativacoes", "locks", "logs", "planos",
)


def git(argumentos: list[str], pasta: str) -> str | None:
    try:
        resultado = subprocess.run(
            ["git"] + argumentos, cwd=pasta, capture_output=True, text=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if resultado.returncode != 0:
        return None
    return resultado.stdout.strip()


def absolute(base: str, caminho: str) -> str:
    if os.path.isabs(caminho):
        return os.path.realpath(caminho)
    return os.path.realpath(os.path.join(base, caminho))


def has_execution_worktree(raiz: str) -> bool:
    saida = git(["worktree", "list", "--porcelain"], raiz)
    if not saida:
        return False
    worktrees = [l[len("worktree "):] for l in saida.splitlines() if l.startswith("worktree ")]
    raiz_real = os.path.realpath(raiz)
    return any(os.path.realpath(w) != raiz_real for w in worktrees)


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0
    alvo_texto = comum.target_path_text(evento)
    if not alvo_texto:
        return 0
    pasta_da_sessao = str(comum.event_cwd(evento))
    if not os.path.isdir(pasta_da_sessao):
        return 0

    raiz = git(["rev-parse", "--show-toplevel"], pasta_da_sessao)
    pasta_git = git(["rev-parse", "--git-dir"], pasta_da_sessao)
    pasta_git_comum = git(["rev-parse", "--git-common-dir"], pasta_da_sessao)
    if not raiz or not pasta_git or not pasta_git_comum:
        return 0  # fora de repositorio git

    alvo = absolute(pasta_da_sessao, alvo_texto)
    pasta_git = absolute(pasta_da_sessao, pasta_git)
    pasta_git_comum = absolute(pasta_da_sessao, pasta_git_comum)
    raiz_real = os.path.realpath(raiz)

    if pasta_git != pasta_git_comum:
        # ── estou DENTRO de uma worktree ──
        delta_da_worktree = os.path.join(raiz_real, ".delta-11")
        repo_principal = os.path.realpath(os.path.dirname(pasta_git_comum))
        if alvo.startswith(delta_da_worktree + os.sep):
            dentro = os.path.relpath(alvo, delta_da_worktree)
            if dentro.split(os.sep)[0] in COMPARTILHADOS_DO_DELTA:
                certo = os.path.join(str(comum.main_project_dir()), ".delta-11", dentro)
                return comum.block(
                    HOOK,
                    "GUARDA-WORKTREE (CASO B): voce esta DENTRO de uma worktree e tentou editar um\n"
                    "arquivo COMPARTILHADO do .delta-11 pela copia da worktree — essa copia e\n"
                    "INVISIVEL para o CRONOS e os outros agentes.\n"
                    f"Arquivo tentado: {alvo}\n"
                    f"Use o CAMINHO ABSOLUTO da pasta principal: {certo}\n"
                    "Lembrete: kanban e kanban-data.js so o CRONOS escreve (D10); voce grava o seu\n"
                    "-produto.md e avisa o CRONOS por SendMessage.",
                    f"CASO B — compartilhado pela copia da worktree: {dentro}",
                )
        delta_do_principal = os.path.join(repo_principal, ".delta-11")
        if alvo.startswith(repo_principal + os.sep) and not alvo.startswith(delta_do_principal + os.sep):
            return comum.block(
                HOOK,
                "GUARDA-WORKTREE (CASO C): voce esta DENTRO de uma worktree e tentou editar CODIGO\n"
                "do repo PRINCIPAL por caminho absoluto. Codigo se edita na SUA worktree\n"
                "(caminho relativo) — so o CRONOS faz merge na main.\n"
                f"Arquivo tentado: {alvo}",
                f"CASO C — codigo da main editado de dentro da worktree: {alvo}",
            )
        return 0

    # ── estou no repo PRINCIPAL ──
    for permitido in (os.path.join(raiz_real, ".delta-11"), os.path.join(raiz_real, ".claude")):
        if alvo.startswith(permitido + os.sep):
            return 0
    if alvo == os.path.join(raiz_real, "CLAUDE.md"):
        return 0
    if not os.path.isdir(os.path.join(raiz_real, ".delta-11")):
        return 0  # projeto sem Delta-11
    if os.path.exists(os.path.join(raiz_real, ".delta-11", ARQUIVO_DE_ESCAPE)):
        return 0  # comandante liberou de proposito
    if has_execution_worktree(raiz_real):
        return comum.block(
            HOOK,
            "GUARDA-WORKTREE (CASO A — bug Anthropic #39886): existem worktrees de execucao\n"
            "ativas neste projeto e voce esta editando CODIGO direto no repo PRINCIPAL (main).\n"
            "Se voce e um agente despachado com isolation:worktree, voce provavelmente nasceu\n"
            "na main por causa do bug #39886.\n"
            "PARE AGORA. Nao edite mais nada. Envie SendMessage ao CRONOS com\n"
            '{"bug": "#39886", "current": "' + raiz_real + '"} e aguarde novo disparo.\n'
            "Se voce e o COMANDANTE editando de proposito, crie o arquivo\n"
            f".delta-11/{ARQUIVO_DE_ESCAPE} para liberar (e apague depois).",
            f"CASO A — codigo na main com worktrees ativas: {alvo}",
        )
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
