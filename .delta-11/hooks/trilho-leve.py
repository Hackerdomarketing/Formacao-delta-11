#!/usr/bin/env python3
"""
Vigia PreToolUse "trilho leve" — Delta-11 v6.4.1 (2026-10-15). Decisao do comandante.

Problema que resolve: uma troca de 3 linhas de estilo passava pela mesma cerimonia de
uma funcionalidade nova (worktree, autocritica, 2 validadores, SHIELD recompilando e
rodando ~850 testes, QA) — 6 sessoes de agente e ~30 min no Selo do salvahacks.
No TRILHO LEVE (tarefa marcada `[AJUSTE]` no kanban — protocolos/trilho-leve.md):
um executor faz, compila uma vez e fotografa; NAO ha SHIELD nem validadores; quem
aprova e o COMANDANTE ao ver o resultado. Este vigia garante a unica condicao que
torna isso seguro: a mudanca e SO VISUAL.

Quando age (PreToolUse em Bash): comando `git merge` cuja mensagem cita `[AJUSTE]`
(ex.: git merge --no-ff worktree-agent-x -m "[AJUSTE] T-271 colunas iguais").
Calcula os arquivos alterados pela branch (`git diff --name-only HEAD...<branch>`):
  - so arquivos visuais (ARQUIVOS_VISUAIS) + .delta-11/ e *.md -> libera e grava
    no activity-log "VISUAL-OK T-XXX" (prova que o shield-aprovado aceita);
  - .html/.htm entram so se as linhas novas nao trazem <script> nem on...= ;
  - qualquer outro arquivo (JS, TS, regras do banco, testes, config...) -> BLOQUEIA:
    nao e ajuste visual; a tarefa volta para o trilho completo (SHIELD).
Merge sem `[AJUSTE]` na mensagem: nao e com este vigia (libera).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "trilho-leve"
ARQUIVOS_VISUAIS = (
    ".css", ".scss", ".sass", ".less", ".styl",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".md",
)
HTML = (".html", ".htm")
CODIGO_NO_HTML_RE = re.compile(r"<\s*script\b|\son[a-z]+\s*=", re.IGNORECASE)
AJUSTE_RE = re.compile(r"\[AJUSTE\]", re.IGNORECASE)
OPCOES_COM_VALOR = {"-m", "--message", "-s", "--strategy", "-X", "--strategy-option", "-F", "--file"}


def git(argumentos: list[str], pasta: str) -> str | None:
    try:
        resultado = subprocess.run(["git", *argumentos], cwd=pasta, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return resultado.stdout if resultado.returncode == 0 else None


def merge_branches(comando: str) -> list[str] | None:
    """Branches de um `git merge ...` (None = nao e merge). Olha cada trecho separado por && ; ||."""
    for trecho in re.split(r"&&|\|\||;|\n", comando):
        try:
            partes = shlex.split(trecho)
        except ValueError:
            continue
        if len(partes) < 2 or partes[0] != "git":
            continue
        resto = partes[1:]
        while resto and resto[0].startswith("-"):  # git -C pasta merge ...
            resto = resto[2:] if resto[0] in {"-C", "-c"} else resto[1:]
        if not resto or resto[0] != "merge":
            continue
        branches, pular = [], False
        for arg in resto[1:]:
            if pular:
                pular = False
                continue
            if arg in OPCOES_COM_VALOR:
                pular = True
                continue
            if arg.startswith("-"):
                continue
            branches.append(arg)
        return branches
    return None


def non_visual(raiz: str, branch: str) -> tuple[list[str], list[str]] | None:
    """(arquivos alterados, os que NAO sao visuais). None = branch invalida."""
    nomes = git(["diff", "--name-only", f"HEAD...{branch}"], raiz)
    if nomes is None:
        return None
    arquivos = [n for n in nomes.splitlines() if n.strip()]
    ruins = []
    for nome in arquivos:
        baixo = nome.lower()
        if baixo.startswith(".delta-11/") or baixo.endswith(ARQUIVOS_VISUAIS):
            continue
        if baixo.endswith(HTML):
            diff = git(["diff", f"HEAD...{branch}", "--", nome], raiz) or ""
            novas = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
            if not any(CODIGO_NO_HTML_RE.search(l) for l in novas):
                continue
        ruins.append(nome)
    return arquivos, ruins


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") != "Bash":
        return 0
    comando = str((evento.get("tool_input") or {}).get("command") or "")
    if "merge" not in comando or not AJUSTE_RE.search(comando):
        return 0
    branches = merge_branches(comando)
    if branches is None:
        return 0
    tarefa = comum.task_id(comando) or "T-?"
    raiz = str(comum.main_project_dir())
    if not branches:
        return comum.block(
            HOOK,
            f"[{HOOK}] BLOQUEIO {comum.VERSAO} — merge de [AJUSTE] sem branch identificavel.\n"
            "Use: git merge --no-ff <branch-da-worktree> -m \"[AJUSTE] T-XXX <resumo>\"\n",
            f"merge [AJUSTE] {tarefa} sem branch",
        )
    for branch in branches:
        resultado = non_visual(raiz, branch)
        if resultado is None:
            return comum.block(
                HOOK,
                f"[{HOOK}] BLOQUEIO {comum.VERSAO} — branch '{branch}' nao encontrada para conferir o [AJUSTE] {tarefa}.\n",
                f"merge [AJUSTE] {tarefa}: branch {branch} invalida",
            )
        arquivos, ruins = resultado
        if ruins:
            lista = "".join(f"  - {r}\n" for r in ruins[:15])
            return comum.block(
                HOOK,
                f"[{HOOK}] BLOQUEIO {comum.VERSAO} — {tarefa} NAO e ajuste visual\n"
                "\n"
                "O trilho leve (sem SHIELD) so vale para mudanca SO VISUAL (CSS, imagens, fontes,\n"
                "HTML sem script). Esta branch tambem muda:\n"
                f"{lista}"
                "\n"
                "Tire o [AJUSTE] da tarefa e siga o TRILHO COMPLETO: validadores + SHIELD antes\n"
                "do merge (protocolos/trilho-leve.md).\n",
                f"{tarefa} marcada [AJUSTE] muda arquivo nao visual: {', '.join(ruins[:3])}",
            )
        comum.log(HOOK, f"VISUAL-OK {tarefa} branch {branch} ({len(arquivos)} arquivo(s), so visuais)")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
