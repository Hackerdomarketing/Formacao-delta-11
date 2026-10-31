#!/usr/bin/env python3
"""
CONTRATO DO ADAPTADOR DE MOTOR — Delta-11 v7 (motor multiempresa).

Um "motor" e o orquestrador que roda os agentes do Delta-11. Cada motor
(Claude Code, Kilo, Codex) tem seu proprio jeito de:

  1. entregar o evento da acao a um vigia (o JSON no stdin);
  2. dizer qual ferramenta esta sendo usada e com que argumentos;
  3. identificar o agente que esta agindo;
  4. avisar o CRONOS (ou outro agente) de um resultado.

O NUCLEO (`.delta-11/motor/nucleo/nucleo.py`) sabe tudo sobre o Delta-11 e
nada sobre o motor. O ADAPTADOR sabe tudo sobre o motor e nada sobre o
Delta-11. Este arquivo e o contrato entre os dois.

Implementacao de referencia: `.delta-11/motor/claude-code/adaptador.py`
(o motor original, do qual todos os outros foram derivados).

O contrato de BLOQUEIO e igual em todos os motores: um vigia bloqueia
devolvendo o codigo de saida 2 e escrevendo o motivo no stderr. O `block()`
do nucleo faz isso. Nenhum motor precisa de adaptacao para bloquear — e por
isso que a mesma bateria de 37 vigias serve para todo mundo.

O texto completo do contrato, com a descricao de cada funcao, esta em
`.delta-11/motor/CONTRATO.md`.
"""

from __future__ import annotations

# Nome do motor. Usado no diario de atividades e para diagnostico.
NOME = "generico"

# Nomes das ferramentas que MEXEM em arquivo (usado por before_and_after e
# is_kanban_event). Cada motor mapeia as suas.
FERRAMENTAS_DE_ESCRITA: frozenset[str] = frozenset()

# Nomes das ferramentas que DISPARAM outro agente.
FERRAMENTAS_DE_DISPATCH: frozenset[str] = frozenset()


# ─── O que todo adaptador precisa implementar ────────────────────────────────
# (as assinaturas estao documentadas em CONTRATO.md; aqui fica so a lista)

FUNCOES_DO_ADAPTADOR = (
    "read_event",
    "event_cwd",
    "tool_input",
    "target_path_text",
    "absolute_target",
    "event_key",
    "identify_agent",
    "dispatch_target",
    "is_main_session",
    "is_sub_agent_type",
    "agent_label",
    "before_and_after",
    "is_kanban_event",
)
