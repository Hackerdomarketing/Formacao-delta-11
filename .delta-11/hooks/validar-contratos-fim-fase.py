#!/usr/bin/env python3
"""
Vigia "testes de contrato no fim da fase" — Delta-11 v6.3 (2026-10-14). C-015, C-043.

Roda os testes de contrato [testes que conferem se o codigo cumpre os acordos de
API e banco do project-core] antes de deixar uma FASE ser fechada no kanban.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`) — so na TRANSICAO
DE FASE (C-043), comparando o kanban antes e depois:
  - a edicao ACRESCENTA uma linha que declara o selo de uma fase
    ("Fase 3 selada", "Fase 4 concluída", "[SELO 3.5]", "Dia 4 selado"...); ou
  - o campo "**Fase atual:**" muda de valor.
Concluir tarefas avulsas ou reescrever o kanban inteiro sem mudar de fase NAO
roda a bateria.

Como roda (na PASTA PRINCIPAL do projeto):
  - Node: `npm run test:contracts` (se existir no package.json)
  - Python: `pytest tests/contracts/` (com pytest.ini ou pyproject.toml, a pasta
    tests/contracts/ existindo e o pytest instalado)
  - Sem framework reconhecido: libera e registra AVISO no diario.
  - Tempo maximo: 110 s (o registro do vigia tem 120 s — D30). Estourou = falhou.

Falhou -> bloqueia (exit 2) com o fim da saida dos testes.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "validar-contratos-fim-fase"
TEMPO_MAXIMO = 110


def phase_transition(antes: str, depois: str) -> str | None:
    """Descricao da transicao de fase desta edicao, ou None."""
    for linha in comum.new_lines(antes, depois):
        if comum.PENDENTE_RE.match(linha):
            continue
        if comum.ANY_SEAL_RE.search(linha):
            return linha
    fase_antes, fase_depois = comum.current_phase(antes), comum.current_phase(depois)
    if fase_depois and fase_antes != fase_depois:
        return f"Fase atual: {fase_antes or '(vazia)'} -> {fase_depois}"
    return None


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    antes, depois = comum.before_and_after(evento)
    transicao = phase_transition(antes, depois)
    if not transicao:
        return 0
    raiz = comum.main_project_dir()
    comando = comum.contract_test_command(raiz)
    if comando is None:
        comum.log(HOOK, "AVISO: nenhum framework de testes de contrato detectado — transicao liberada sem conferencia")
        return 0
    comum.log(HOOK, f"transicao de fase ({transicao[:80]}): rodando {' '.join(comando[1:])}")
    passou, saida = comum.run_contract_tests(comando, raiz, TEMPO_MAXIMO)
    if passou:
        comum.log(HOOK, "OK: testes de contrato passaram")
        return 0
    ultimas = "\n".join(saida.splitlines()[-15:]) or "(sem saida)"
    return comum.block(
        HOOK,
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — testes de contrato falharam na transicao de fase\n"
        f"\n"
        f"Transicao: {transicao[:160]}\n"
        f"Comando: {' '.join(comando)}\n"
        f"Final da saida:\n{ultimas}\n"
        f"\n"
        f"Corrija a implementacao OU peca ao ATLAS para ajustar o contrato no project-core\n"
        f"(o CRONOS roda o contract-tester de novo depois). Entao feche a fase outra vez.\n",
        "testes de contrato falharam na transicao de fase",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
