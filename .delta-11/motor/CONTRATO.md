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
Delta-11. Este arquivo e o contrato entre os dois: as funcoes abaixo sao as
unicas que um motor novo precisa implementar.

IMPLEMENTACAO DE REFERENCIA: `.delta-11/motor/claude-code/adaptador.py`
(o motor original, do qual todos os outros foram derivados).
