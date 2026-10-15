#!/usr/bin/env python3
"""
Vigia "validacao retroativa Dia 2 <- Dia 3" — Delta-11 v6.3 (2026-10-14). C-042.

Metodologia Genesis: quando o Dia 3 (schema, modelos e contratos) se completa, o
time pergunta: "a arquitetura do Dia 2 sustenta os modelos do Dia 3?". Se SIM, o
Dia 2 e declarado bom; se NAO, o Dia 2 e refeito antes de seguir.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`): so quando a
edicao ACRESCENTA uma linha que declara o SELO da Fase 3 (C-042 — pela fase, nao
por palavras soltas como "banco", "schema" ou "RLS"), por exemplo:
  "Fase 3 selada"   "Fase 3 concluída"   "[SELO 3]"   "[SELO FASE 3]"
  "Dia 3 selado"    "[FUNDAÇÃO] ... SELO"
"Fase 3.5" nao conta como Fase 3. Concluir tarefas individuais da Fase 3 nao e
bloqueado (a retrovalidacao so pode ser respondida no fim do Dia 3).

O que exige: no kanban FINAL (depois da edicao), a tarefa
  "Validação Retroativa Dia 2 ← Dia 3" (ou "Retroativa Dia 2")
concluida e com a resposta **SUSTENTA** na MESMA linha. Vale a ultima linha
concluida dessa tarefa.
  - REFAZER -> bloqueia (o Dia 2 precisa ser refeito pelo ATLAS)
  - ausente, pendente ou concluida sem resposta -> bloqueia com instrucao

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "validar-arquitetura-vs-modelos"
RETRO_RE = re.compile(r"Valida[cç][ãa]o\s+Retroativa\s+Dia\s+2|Retroativa\s+Dia\s+2", re.IGNORECASE)
SUSTENTA_RE = re.compile(r"\bSUSTENTA\b", re.IGNORECASE)
REFAZER_RE = re.compile(r"\bREFAZER\b|\bREFACER\b", re.IGNORECASE)


def retro_status(kanban: str) -> str:
    """SUSTENTA | REFAZER | SEM_RESPOSTA | PENDENTE | AUSENTE"""
    if not RETRO_RE.search(kanban):
        return "AUSENTE"
    concluidas = [l for l in comum.concluded_lines(kanban).values() if RETRO_RE.search(l)]
    if not concluidas:
        return "PENDENTE"
    ultima = concluidas[-1]
    if REFAZER_RE.search(ultima):
        return "REFAZER"
    if SUSTENTA_RE.search(ultima):
        return "SUSTENTA"
    return "SEM_RESPOSTA"


ACOES = {
    "REFAZER": (
        "A retrovalidacao do Dia 2 esta marcada como REFAZER.",
        "A arquitetura do Dia 2 precisa ser REFEITA antes de selar a Fase 3. O CRONOS\n"
        "dispara o ATLAS para revisar a arquitetura; quando o Dia 2 for refeito, a\n"
        "resposta da tarefa de retrovalidacao muda para **SUSTENTA**.",
    ),
    "SEM_RESPOSTA": (
        "A retrovalidacao esta concluida, mas sem **SUSTENTA** ou **REFAZER** na linha.",
        "Escreva a resposta na MESMA linha da tarefa, por exemplo:\n"
        "  - [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3 — **SUSTENTA** | Por: ATLAS",
    ),
    "PENDENTE": (
        "A tarefa de retrovalidacao existe, mas ainda nao foi concluida.",
        "Responda a pergunta 'A arquitetura do Dia 2 sustenta os modelos do Dia 3?' e\n"
        "conclua a tarefa com **SUSTENTA** ou **REFAZER** na mesma linha.",
    ),
    "AUSENTE": (
        "Nao existe a tarefa 'Validação Retroativa Dia 2 ← Dia 3' no kanban.",
        "Crie a tarefa e conclua com a resposta na mesma linha:\n"
        "  - [x] T-RETRO-001 Validação Retroativa Dia 2 ← Dia 3 — **SUSTENTA** | Por: ATLAS\n"
        "  (ou **REFAZER**, se a arquitetura do Dia 2 nao aguenta os modelos do Dia 3)",
    ),
}


def message(selo: str, status: str) -> str:
    motivo, acao = ACOES[status]
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Verificacao Retroativa do Dia 2 pelo Dia 3\n"
        f"\n"
        f"Linha que declara o selo da Fase 3: {selo[:160]}\n"
        f"Motivo: {motivo}\n"
        f"\n{acao}\n"
        f"\nReferencia: .delta-11/conhecimento/metodologia-genesis-camadas.md → Dia 2 e Dia 3,\n"
        f"secao 'Verificacao Retroativa'.\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    antes, depois = comum.before_and_after(evento)
    selo = comum.declares_seal(comum.new_lines(antes, depois), "3")
    if not selo:
        return 0
    status = retro_status(depois)
    if status == "SUSTENTA":
        comum.log(HOOK, "OK: selo da Fase 3 com retrovalidacao SUSTENTA")
        return 0
    return comum.block(HOOK, message(selo[0], status), f"selo da Fase 3 com retrovalidacao {status}")


if __name__ == "__main__":
    comum.run(main, HOOK)
