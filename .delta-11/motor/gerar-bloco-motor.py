#!/usr/bin/env python3
"""
GERADOR DO BLOCO DE MOTOR DO CLAUDE.md — Delta-11 v7 (motor multiempresa).

O CLAUDE.md da Formacao tem ~40 mil caracteres que descrevem o motor
original (o Claude Code): como disparar, como os hooks disparam, como o
Agent tool faz worktree, como o SendMessage funciona.

Em vez de manter 6 secoes diferentes (uma por motor), o v7 troca esse bloco
por UM bloco que descreve o motor ATIVO. O resto do CLAUDE.md (a
metodologia — as 7 camadas, as 17 regras inviolaveis, o protocolo de codigo,
os templates) nao muda: ela e a mesma em todo motor.

ESTE GERADOR faz a troca:
  - le o CLAUDE.md da fonte;
  - substitui o bloco `<!-- MOTOR:INICIO --> ... <!-- MOTOR:FIM -->` pelo
    bloco do motor pedido;
  - se o bloco nao existir ainda, insere depois do titulo principal.

Motores disponiveis:
  claude-code  o original (hooks nativos, Agent tool, SendMessage)
  codex        hooks nativos com o mesmo formato, apply_patch, spawn_agent
  kilo         sem hooks: porteiro + permissoes nativas + Agent Manager

Uso:
  python3 .delta-11/motor/gerar-bloco-motor.py <motor> [--saida ARQUIVO]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DELTA_DIR = AQUI.parent
INICIO = "<!-- MOTOR:INICIO -->"
FIM = "<!-- MOTOR:FIM -->"


# ─────────────────────────────────────────────────────────────────────────────
# O BLOCO (o que o agente do motor ativo lê)
# ─────────────────────────────────────────────────────────────────────────────
BLOCO_COMUM = """
## 🧭 MOTOR ATIVO: {MOTOR_NOME}

Este projeto roda a Formação Δ-11 no motor **{MOTOR_NOME}**.
A metodologia (as 7 camadas, as 17 regras inviolaveis, o protocolo de
código, os templates) e a MESMA em todo motor. O que muda e COMO o motor
executa o protocolo — e esta secao diz como.

{bloco_de_motor}

### A regra que vale em todo motor

O `CLAUDE.md` desta pasta e o da Formacao (o motor trocou as secoes
tecnicas por este bloco). O contexto permanente do PROJETO esta em
`docs/contexto-do-projeto-kpi-metrics.md` (ou no arquivo que o projeto
apontar). Leia os dois: este diz COMO trabalhar, aquele diz O QUE o produto e.
"""

BLOCO_CLAUDE_CODE = """
**Voce tem hooks nativos.** Os 37 vigias disparam sozinhos, antes de cada
acao. Nao precisa chamar nada.

| O protocolo fala em | Use |
|---|---|
| `Agent` tool com `isolation: "worktree"` | a tool `Agent`, com `isolation: "worktree"`, `run_in_background: true`, `name` |
| `SendMessage` ao CRONOS | a tool `SendMessage` (destino: o `name` da sessao) |
| `$CLAUDE_PROJECT_DIR` | a variavel de ambiente de mesmo nome |
| `subagent_type: "general-purpose"` | `subagent_type: "general-purpose"` + `name: "<agente>-onda-<N>"` |

Os hooks estao em `.claude/settings.json` (gerado de
`.delta-11/templates/settings-hooks.json`).
"""

BLOCO_CODEX = """
**Voce tem hooks nativos**, com o mesmo formato do Claude Code. Os 37
vigias disparam sozinhos, antes de cada acao.

| O protocolo fala em | Use |
|---|---|
| `Agent` tool com `isolation: "worktree"` | `spawn_agent` (ou `Agent` no matcher); worktree via `git worktree add` em `$CODEX_HOME/worktrees` |
| `SendMessage` ao CRONOS | a tool de sub-agente (pedir por resumo no prompt) + o arquivo `-produto.md` como verdade |
| `$CLAUDE_PROJECT_DIR` | `$(git rev-parse --show-toplevel)` (o Codex nao tem essa variavel) |
| `Edit`/`Write` | `apply_patch` (o caminho vem DENTRO do patch) |
| `subagent_type: "general-purpose"` | `[agents]` em `.codex/config.toml` ou `.codex/agents/*.toml` |

Os hooks estao em `.codex/hooks.json` (gerado por
`python3 .delta-11/motor/codex/gerar-hooks.py`).

**O `AGENTS.md`** e o equivalente do `CLAUDE.md` no Codex: ele e lido
automaticamente em cada execucao. O `CLAUDE.md` desta pasta continua valendo
para quem le Claude Code.
"""

BLOCO_KILO = """
**Voce NAO tem hooks.** O Kilo nao dispara vigia sozinho — a protecao do
Delta-11 roda pelo **PORTAO**, que voce chama antes de agir.

| O protocolo fala em | Use |
|---|---|
| `Agent` tool com `isolation: "worktree"` | o **Agent Manager** (`mode: worktree`), com `tasks[].name` e `tasks[].branchName` |
| `run_in_background: true` | o Agent Manager ja roda em paralelo: todas as tarefas da onda saem na MESMA chamada |
| `SendMessage` ao CRONOS | o **quadro** (`board_post`): a mensagem e aviso, o ARQUIVO e a verdade |
| `$CLAUDE_PROJECT_DIR` | o caminho absoluto da **pasta principal** (veja o Passo 0) |
| `subagent_type: "general-purpose"` | `tasks[].agent` = o nome do agente customizado (ex.: `back-onda-2`) |

**O PORTAO** (a protecao que substitui os hooks):

```bash
python3 .delta-11/motor/porteiro/porteiro.py <vigia> <<< '<evento json>'
```

`exit 0` = liberado. `exit 2` = **BLOQUEADO**, com o motivo no stderr.
Para conferir a acao contra TODOS os vigias de uma vez (sem bloquear):

```bash
python3 .delta-11/motor/porteiro/porteiro.py --auditar <<< '<evento json>'
```

O evento JSON tem o mesmo formato do Claude Code:
`{{"tool_name": "Write", "tool_input": {{"file_path": "..."}}, "cwd": "..."}}`.

**As permissoes nativas do Kilo** sao a camada GROSSA das protecoes (as
barreiras obvious, no proprio motor): `.delta-11/**`, `.claude/**` e
`.git/**` sao `deny` para edicao; `git stash`/`push`/`reset --hard` sao
`deny`; todo despacho de agente e `ask`; `external` e `deny`. As regras
completas: `python3 .delta-11/motor/kilo/gerar-permissoes.py`.

**Os agentes do Delta-11** sao agentes customizados do Kilo
(`~/.config/kilo/agent/*.md` ou `.kilo/agent/*.md`), gerados por
`python3 .delta-11/motor/kilo/gerar-agentes.py`. Cada um carrega a
identidade canonica (`.delta-11/operativos/`) e o bloco de motor.

**Regra de ouro:** um vigia que bloqueia e uma barreira, nao uma sugestao.
Se o portao devolveu 2, a acao NAO foi feita.
"""

BLOCOS = {
    "claude-code": ("Claude Code", BLOCO_CLAUDE_CODE),
    "codex": ("Codex CLI", BLOCO_CODEX),
    "kilo": ("Kilo", BLOCO_KILO),
}


def gerar_bloco(motor: str) -> str:
    nome, corpo = BLOCOS[motor]
    return BLOCO_COMUM.replace("{MOTOR_NOME}", nome).replace("{bloco_de_motor}", corpo.strip())


def aplicar(texto: str, motor: str) -> str:
    """Substitui (ou insere) o bloco de motor no CLAUDE.md."""
    bloco = f"{INICIO}\n{gerar_bloco(motor)}\n{FIM}"
    if INICIO in texto and FIM in texto:
        antes, _, depois = texto.partition(INICIO)
        _, _, depois = depois.partition(FIM)
        return antes + bloco + depois
    # Insere logo depois do primeiro titulo de nivel 1 ou 2.
    linhas = texto.splitlines(keepends=True)
    for i, linha in enumerate(linhas):
        if linha.startswith("## "):
            return "".join(linhas[: i + 1]) + "\n" + bloco + "\n" + "".join(linhas[i + 1:])
    return bloco + "\n" + texto


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("motor", choices=sorted(BLOCOS))
    parser.add_argument("--saida", help="Arquivo de saida. Padrao: a stdout.")
    parser.add_argument("--fonte", help="CLAUDE.md de entrada. Padrao: a raiz da Formacao.")
    args = parser.parse_args()

    fonte = Path(args.fonte) if args.fonte else DELTA_DIR.parent / "CLAUDE.md"
    if not fonte.is_file():
        print(f"ERRO: CLAUDE.md nao encontrado em {fonte}", file=sys.stderr)
        return 1
    texto = fonte.read_text(encoding="utf-8")
    resultado = aplicar(texto, args.motor)

    if args.saida:
        Path(args.saida).write_text(resultado, encoding="utf-8")
        print(f"bloco do motor '{args.motor}' escrito em {args.saida}")
    else:
        print(resultado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
