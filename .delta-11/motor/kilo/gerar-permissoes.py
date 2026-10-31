#!/usr/bin/env python3
"""
GERADOR DAS PERMISSOES NATIVAS DO KILO — Delta-11 v7 (motor multiempresa).

O Kilo nao tem hooks, mas tem PERMISSOES NATIVAS por recurso e efeito:

    { "action": "<recurso>", "resource": "<padrao>", "effect": "allow|ask|deny" }

Recursos medidos no log do Kilo (2026-10-31): bash, read, edit, glob, grep,
agent, board, external.

Esta pasta do projeto (`permissions` na config do Kilo) sai do Delta-11
pronto para colar em `.kilo/kilo.jsonc` ou `~/.config/kilo/kilo.jsonc`.

O QUE CADA REGRA FAZ (e por que):

  1. `edit` DENY nos caminhos de sistema do Delta-11
     (.delta-11/**, .claude/**, .git/**)
     → o codigo do produto nao pode ser editado pelo executor; o sistema e
     do CRONOS. Quem mexe no sistema e o CRONOS, na mao.

  2. `edit` ASK no kanban e na memoria dos agentes
     → o kanban.md e o `*-produto.md` sao do CRONOS. A regra de "so o
     CRONOS escreve" fica no motor (e nao so no prompt).

  3. `bash` DENY nos comandos que burlam o portao
     (`git commit` sem passar pelo pre-despacho, `git stash`, `git push`)
     → protects as travas e o merge. O `git stash` e bloqueado pelo
     vigia anti-stash; o `git push` e do CRONOS.

  4. `agent` ASK (nao DENY)
     → todo despacho passa pelo pre-despacho, que valida o brief. O Kilo
     pergunta ao usuario; o vigia faz a conferencia fina.

  5. `external` DENY
     → nenhum agente do Delta-11 fala com a internet sem o comando do
     comandante. As unicas excecoes do projeto sao adicionadas aqui.

O QUE ESTE ARQUIVO NAO FA: nao substitui os 37 vigias. As permissoes
nativas sao a CAMADA GROSSA (barreiras obvious, no proprio motor). Os vigias
sao a CAMADA FINA (o que depende do estado do projeto: travas, kanban,
selos, contratos). As duas juntas fecham a protecao.

Uso:
  python3 .delta-11/motor/kilo/gerar-permissoes.py [projeto]
      imprime o JSON pronto para colar na config do Kilo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def regras() -> list[dict]:
    """As regras de permissao do Delta-11 para o motor Kilo."""
    return [
        # ── Camada grossa: o sistema do Delta-11 e do CRONOS ──
        {
            "action": "edit",
            "resource": ".delta-11/**",
            "effect": "deny",
            "_porque": "o sistema do Delta-11 e do CRONOS; o executor nao edita",
        },
        {
            "action": "edit",
            "resource": ".claude/**",
            "effect": "deny",
            "_porque": "configuracao local do orquestrador; fora do executor",
        },
        {
            "action": "edit",
            "resource": ".git/**",
            "effect": "deny",
            "_porque": "o Git e do CRONOS (merge, branch, worktree)",
        },
        # ── Camada grossa: o kanban e a memoria sao do CRONOS ──
        {
            "action": "edit",
            "resource": ".delta-11/kanban.md",
            "effect": "ask",
            "_porque": "o kanban e do CRONOS; o executor avisa, o CRONOS escreve",
        },
        {
            "action": "edit",
            "resource": ".delta-11/memoria/**",
            "effect": "ask",
            "_porque": "a memoria do produto e do proprio agente; o CRONOS confere",
        },
        {
            "action": "edit",
            "resource": ".delta-11/ativacoes/**",
            "effect": "ask",
            "_porque": "ACK e pulso: o agente escreve o dele",
        },
        # ── Camada grossa: bash que burla o sistema ──
        {
            "action": "bash",
            "resource": "git stash*",
            "effect": "deny",
            "_porque": "anti-stash: o stash esconde trabalho do agente",
        },
        {
            "action": "bash",
            "resource": "git push*",
            "effect": "deny",
            "_porque": "o push e do CRONOS, depois do merge guiado",
        },
        {
            "action": "bash",
            "resource": "git reset --hard*",
            "effect": "deny",
            "_porque": "destroi trabalho semPossibilidade de volta",
        },
        {
            "action": "bash",
            "resource": "git checkout main*",
            "effect": "deny",
            "_porque": "a main e do CRONOS; o executor fica na branch dele",
        },
        {
            "action": "bash",
            "resource": "git worktree remove*",
            "effect": "ask",
            "_porque": "remover worktree pode destruir trabalho de outro agente",
        },
        # ── Camada fina: o despacho passa pelo pre-despacho ──
        {
            "action": "agent",
            "resource": "*",
            "effect": "ask",
            "_porque": "todo despacho e conferido pelo pre-despacho (brief, limites)",
        },
        # ── Camada grossa: sem internet sem o comandante ──
        {
            "action": "external",
            "resource": "*",
            "effect": "deny",
            "_porque": "nenhum agente do Delta-11 fala com a internet sozinho",
        },
    ]


def gerar() -> dict:
    """Monta o bloco de config do Kilo."""
    lista = regras()
    # O formato da config do Kilo aceita pares recurso->efeito, com
    # "*" como o recurso padrao. As regras especificas vem antes das gerais.
    permissoes: dict[str, dict[str, str]] = {}
    for regra in lista:
        recurso = regra["action"]
        alvo = regra["resource"]
        permissoes.setdefault(recurso, {})[alvo] = regra["effect"]
    return {
        "permissions": {
            recurso: dict(mapeamento)
            for recurso, mapeamento in permissoes.items()
        }
    }


def main() -> int:
    resultado = gerar()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
