#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# DELTA-11 — Hook PreToolUse: Guarda de Worktree (bug Anthropic #39886)
# ═══════════════════════════════════════════════════════════════
# Dispara ANTES de Edit/Write. Bloqueia dois erros silenciosos:
#
# CASO A — bug #39886: agente despachado com isolation:worktree nasce
#   no repo PRINCIPAL sem avisar. Sintoma detectável: a sessão está no
#   repo principal, existem worktrees de execução ativas, e o alvo é
#   arquivo de CÓDIGO (fora de .delta-11/ e .claude/). Nessa condição
#   a edição é bloqueada — código só nasce dentro de worktree.
#   Escape para o comandante: criar o arquivo
#   .delta-11/.permitir-edicao-main no repo principal desativa o CASO A.
#
# CASO B — erro inverso: agente DENTRO de worktree edita arquivo
#   compartilhado do .delta-11 (kanban, memoria, ativacoes...) por
#   caminho RELATIVO — grava na cópia invisível da worktree em vez do
#   repo principal. Bloqueado com instrução de usar o path absoluto.
#
# Filosofia v5: proteção técnica > instrução em prompt. Este hook é a
# versão executável do Passo 0.VW do CLAUDE.md.
# Em qualquer erro interno o hook LIBERA (exit 0) — nunca derruba o
# projeto por falha da própria guarda.
# ═══════════════════════════════════════════════════════════════
import json
import os
import subprocess
import sys

ARQUIVO_DE_ESCAPE = ".permitir-edicao-main"

PASTAS_COMPARTILHADAS_DO_DELTA = (
    "kanban.md",
    "kanban-data.js",
    "activity-log.md",
    "memoria",
    "ativacoes",
    "locks",
    "planos",
)


def rodar_git(argumentos, pasta):
    try:
        resultado = subprocess.run(
            ["git"] + argumentos,
            cwd=pasta,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if resultado.returncode != 0:
            return None
        return resultado.stdout.strip()
    except Exception:
        return None


def caminho_absoluto(base, caminho):
    if os.path.isabs(caminho):
        return os.path.realpath(caminho)
    return os.path.realpath(os.path.join(base, caminho))


def existe_worktree_de_execucao(raiz_do_repo):
    saida = rodar_git(["worktree", "list", "--porcelain"], raiz_do_repo)
    if not saida:
        return False
    worktrees = [
        linha[len("worktree "):]
        for linha in saida.splitlines()
        if linha.startswith("worktree ")
    ]
    raiz_real = os.path.realpath(raiz_do_repo)
    return any(os.path.realpath(w) != raiz_real for w in worktrees)


def bloquear(mensagem):
    print(mensagem, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        dados = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    entrada_da_ferramenta = dados.get("tool_input") or {}
    alvo = entrada_da_ferramenta.get("file_path")
    pasta_da_sessao = dados.get("cwd") or os.getcwd()
    if not alvo:
        sys.exit(0)

    raiz = rodar_git(["rev-parse", "--show-toplevel"], pasta_da_sessao)
    pasta_git = rodar_git(["rev-parse", "--git-dir"], pasta_da_sessao)
    pasta_git_comum = rodar_git(["rev-parse", "--git-common-dir"], pasta_da_sessao)
    if not raiz or not pasta_git or not pasta_git_comum:
        sys.exit(0)  # fora de repositório git — não é assunto desta guarda

    alvo = caminho_absoluto(pasta_da_sessao, alvo)
    pasta_git = caminho_absoluto(raiz, pasta_git)
    pasta_git_comum = caminho_absoluto(raiz, pasta_git_comum)
    estou_em_worktree = pasta_git != pasta_git_comum

    if estou_em_worktree:
        # ── CASO B: edição de arquivo compartilhado por caminho relativo ──
        pasta_delta_da_worktree = os.path.join(os.path.realpath(raiz), ".delta-11")
        if alvo.startswith(pasta_delta_da_worktree + os.sep):
            caminho_dentro_do_delta = os.path.relpath(alvo, pasta_delta_da_worktree)
            primeiro_pedaco = caminho_dentro_do_delta.split(os.sep)[0]
            if primeiro_pedaco in PASTAS_COMPARTILHADAS_DO_DELTA:
                repo_principal = os.path.dirname(pasta_git_comum)
                caminho_correto = os.path.join(
                    repo_principal, ".delta-11", caminho_dentro_do_delta
                )
                bloquear(
                    "GUARDA-WORKTREE (CASO B): voce esta DENTRO de uma worktree e tentou "
                    "editar um arquivo COMPARTILHADO do .delta-11 pela copia local da "
                    "worktree — essa copia e INVISIVEL para o CRONOS e os outros agentes.\n"
                    f"Arquivo tentado: {alvo}\n"
                    f"Use o PATH ABSOLUTO do repo principal: {caminho_correto}"
                )
        # ── CASO C: de dentro da worktree, editar CODIGO do repo principal
        #    por caminho absoluto (mesmo erro do CASO A, pela porta dos fundos) ──
        repo_principal = os.path.realpath(os.path.dirname(pasta_git_comum))
        delta_do_principal = os.path.join(repo_principal, ".delta-11")
        alvo_no_principal = alvo.startswith(repo_principal + os.sep)
        alvo_no_delta_do_principal = alvo.startswith(delta_do_principal + os.sep)
        if alvo_no_principal and not alvo_no_delta_do_principal:
            bloquear(
                "GUARDA-WORKTREE (CASO C): voce esta DENTRO de uma worktree e tentou "
                "editar CODIGO do repo PRINCIPAL por caminho absoluto. Codigo se edita "
                "na SUA worktree (caminho relativo) — so o CRONOS faz merge na main.\n"
                f"Arquivo tentado: {alvo}"
            )
        sys.exit(0)

    # ── Estou no repo PRINCIPAL ──
    raiz_real = os.path.realpath(raiz)
    dentro_do_delta = alvo.startswith(os.path.join(raiz_real, ".delta-11") + os.sep)
    dentro_do_claude = alvo.startswith(os.path.join(raiz_real, ".claude") + os.sep)
    é_claude_md = alvo == os.path.join(raiz_real, "CLAUDE.md")
    if dentro_do_delta or dentro_do_claude or é_claude_md:
        sys.exit(0)  # coordenação compartilhada — sempre permitida no principal

    if os.path.exists(os.path.join(raiz_real, ".delta-11", ARQUIVO_DE_ESCAPE)):
        sys.exit(0)  # comandante liberou explicitamente a edição na main

    if not os.path.isdir(os.path.join(raiz_real, ".delta-11")):
        sys.exit(0)  # projeto sem Delta-11 — guarda não se aplica

    # ── CASO A: código sendo editado na main com worktrees de execução ativas ──
    if existe_worktree_de_execucao(raiz_real):
        bloquear(
            "GUARDA-WORKTREE (CASO A — bug Anthropic #39886): existem worktrees de "
            "execucao ativas neste projeto, e voce esta editando CODIGO direto no repo "
            "PRINCIPAL (main). Se voce e um agente despachado com isolation:worktree, "
            "voce provavelmente nasceu na main por causa do bug #39886.\n"
            "PARE AGORA. Nao edite mais nada. Envie SendMessage ao CRONOS com o payload "
            '{"bug": "#39886", "current": "' + raiz_real + '"} e aguarde re-dispatch.\n'
            "Se voce e o COMANDANTE editando de proposito, crie o arquivo "
            f".delta-11/{ARQUIVO_DE_ESCAPE} para liberar (e apague depois)."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
