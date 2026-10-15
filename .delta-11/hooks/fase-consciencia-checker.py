#!/usr/bin/env python3
"""
Vigia da Fase 4.5 (Consciencia Dominante, Dia 6) — Delta-11 v6.4 (2026-10-15). C-015, C-026, V9.

Principio de Selagem: a Fase 4.5 so pode ser SELADA com os 5 entregaveis do Dia 6
em `.delta-11/memoria/decisoes/` da pasta principal, um por numero (C-026):
  AAAA-MM-DD-consciencia-NN-<slug>.md   (NN = 01 a 05, arquivo nao vazio)
    01 auditoria-imutavel · 02 rate-limiting · 03 motor-regras · 04 lgpd ·
    05 fluxos-aprovacao
Cinco arquivos quaisquer com "consciencia" no nome nao bastam: precisa ser um de
cada numero.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`, caminho relativo
ou absoluto — C-026): so quando a edicao ACRESCENTA uma linha que declara o selo
da fase, por exemplo "Fase 4.5 selada", "[SELO 4.5]", "Dia 6 selado",
"[CONSCIÊNCIA] ... SELO" (protocolos/fase-consciencia.md: "SHIELD declara 'Fase
4.5 selada' no kanban"). Concluir as tarefas que produzem os entregaveis nao e
bloqueado.

Ciclo leve (v6.4 — V9): do Ciclo 2 em diante, o checklist de 1 pagina do ciclo
vale como equivalente (e obrigatório: documentos de ciclos anteriores não o substituem) aos 5 documentos:
  AAAA-MM-DD-consciencia-checklist-ciclo-N.md
com os 5 itens, cada um "sem mudança" ou "mudou: <ate 3 linhas>" (modelo:
templates/consciencia-checklist-template.md). O numero do ciclo vem da linha do
selo ("Ciclo N"), senao do kanban (`**Ciclo atual:** N` ou "Ciclo N" na Fase
atual) ou do `fase_atual` do kanban-data.js; sem informacao, Ciclo 1. No Ciclo 1
o checklist NAO vale. Checklist do ciclo atual COMECADO e incompleto bloqueia.
Limite conhecido: quando o ciclo MEXE na area (muda a autenticacao, cria fluxo
de aprovacao novo...), o item afetado precisa do documento completo — isso o
vigia nao julga; quem confere e o SHIELD (protocolos/fase-consciencia.md).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "fase-consciencia-checker"
FASE = "4.5"
PREFIXO = "consciencia"
ENTREGAVEIS = {
    1: "auditoria-imutavel", 2: "rate-limiting", 3: "motor-regras",
    4: "lgpd", 5: "fluxos-aprovacao",
}


CHECKLIST_MODELO = ".delta-11/templates/consciencia-checklist-template.md"


def message(selo: list[str], faltando: list[int], nomes: list[str], ciclo: int = 1,
            checklist: str | None = None, pendencias: list[tuple[int, str]] | None = None) -> str:
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — Selo da Fase 4.5 (Consciencia Dominante, Dia 6) — Ciclo {ciclo}\n"
        f"\n"
        f"Linha que declara o selo: {selo[0][:160]}\n"
    )
    if ciclo >= 2:
        if checklist and pendencias:
            texto += f"\nO checklist do Ciclo {ciclo} ({checklist}) esta incompleto:\n"
            texto += "".join(f"  {n:02d}. {ENTREGAVEIS[n]} — {motivo}\n" for n, motivo in pendencias)
            texto += "\nComplete esses itens e declare o selo de novo.\n"
            return texto
        texto += (
            f"\nCiclo {ciclo} (ciclo leve): basta UM checklist de 1 pagina com os 5 itens:\n"
            f"  .delta-11/memoria/decisoes/AAAA-MM-DD-{PREFIXO}-checklist-ciclo-{ciclo}.md\n"
            f"  (modelo: {CHECKLIST_MODELO})\n"
            f"(Os documentos de ciclos anteriores não substituem o checklist do ciclo atual.)\n\n"
        )
    texto += f"Presentes: {len(ENTREGAVEIS) - len(faltando)} de {len(ENTREGAVEIS)}. Faltam:\n"
    texto += "".join(
        f"  {n:02d}. {ENTREGAVEIS[n]}  -> .delta-11/memoria/decisoes/AAAA-MM-DD-{PREFIXO}-{n:02d}-{ENTREGAVEIS[n]}.md\n"
        for n in faltando
    )
    if nomes:
        texto += "\nJa existem:\n" + "".join(f"  - {n}\n" for n in nomes)
    texto += (
        "\nCrie os que faltam com .delta-11/templates/fase-consciencia-template.md e\n"
        "declare o selo de novo. Protocolo: .delta-11/protocolos/fase-consciencia.md\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    antes, depois = comum.before_and_after(evento)
    selo = comum.declares_seal(comum.new_lines(antes, depois), FASE)
    if not selo:
        return 0
    ciclo = comum.cycle_in_text(selo[0]) or comum.current_cycle(depois)
    _presentes, faltando, nomes = comum.phase_artifacts(PREFIXO, len(ENTREGAVEIS))
    if ciclo >= 2:
        checklist, pendencias = comum.cycle_checklist(PREFIXO, ciclo, ENTREGAVEIS)
        if checklist and not pendencias:
            comum.log(HOOK, f"OK: selo da Fase 4.5 do Ciclo {ciclo} com o checklist {checklist} (ciclo leve)")
            return 0
        if checklist and pendencias:
            return comum.block(
                HOOK, message(selo, faltando, nomes, ciclo, checklist, pendencias),
                f"selo da Fase 4.5 do Ciclo {ciclo}: checklist com {len(pendencias)} item(ns) pendente(s)",
            )
        if not checklist:
            # Documentos COMPLETOS feitos neste ciclo (citam "Ciclo N") valem mais que o checklist: liberam o selo.
            _do_ciclo, faltando_do_ciclo, _nomes = comum.phase_artifacts(PREFIXO, len(ENTREGAVEIS), ciclo)
            if not faltando_do_ciclo:
                comum.log(HOOK, f"OK: selo da Fase 4.5 do Ciclo {ciclo} com os documentos completos do ciclo")
                return 0
            # v6.4 (integração): do Ciclo 2 em diante, documentos de ciclos anteriores NÃO substituem o checklist
            # do ciclo atual (senão o vigia liberaria sempre: os documentos do Ciclo 1 continuam na pasta).
            return comum.block(
                HOOK,
                f"Selo da Fase 4.5 do Ciclo {ciclo} sem o checklist do ciclo atual (ciclo leve, V9).\n"
                f"Crie memoria/decisoes/AAAA-MM-DD-consciencia-checklist-ciclo-{ciclo}.md a partir de\n"
                "templates/consciencia-checklist-template.md: um item por linha, 'sem mudança' ou 'mudou: ...'\n"
                "(item que o ciclo mexeu cita o documento completo novo).\n"
                f"Ou: todos os documentos completos, cada um citando 'Ciclo {ciclo}' no texto.",
                f"selo da Fase 4.5 do Ciclo {ciclo} sem checklist do ciclo",
            )
    if not faltando:
        comum.log(HOOK, f"OK: selo da Fase 4.5 do Ciclo {ciclo} com os 5 entregaveis")
        return 0
    return comum.block(
        HOOK, message(selo, faltando, nomes, ciclo),
        f"selo da Fase 4.5 do Ciclo {ciclo} com {len(faltando)} entregavel(is) faltando",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
