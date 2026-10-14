#!/usr/bin/env python3
"""
Vigia PreToolUse "pre-leitura" — Delta-11 v6.3 (2026-10-14). D6, C-035.

Regra D6: os executores VAULT, BACK, ENGINE, FRONT, PIXEL e FORM NAO leem o
`.delta-11/memoria/project-core.md` INTEIRO. Leem as FATIAS em
`.delta-11/memoria/project-core/` (banco.md, contratos.md, visual.md,
decisoes-tecnicas.md) — essas NUNCA sao bloqueadas.
Podem ler o project-core inteiro: ATLAS, CRONOS, SHIELD, SCOUT, a sessao principal
(comandante) e os sub-agentes (build-validator, code-architect, cold-start-tester,
contract-tester, fresh-reviewer, impact-mapper, qa-ui-tandem, schema-validator,
tool-provisioner e verify-app).

Como sabe quem esta lendo (C-035, D28 — _comum.identify_agent):
  1. `agent_type` do evento, se ja for um nome Delta-11;
  2. o vinculo gravado pelo heartbeat.sh em `ativacoes/agentes-sessao.json`
     ("agente:<agent_id>" ou "principal:<session_id>" -> "agente");
  3. so se nao houver vinculo: o ACK mais recente, ignorando os agentes ja
     vinculados a outra sessao/sub-agente ativo (assim o ATLAS da sessao
     principal nao e confundido com o BACK que fez ACK numa worktree).
  Sem identificacao: liberado, com registro no diario.

Registro: PreToolUse com matcher "Read".

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

HOOK = "pre-leitura"
PROJECT_CORE_INTEIRO_RE = re.compile(r"(?:^|/)\.delta-11/memoria/project-core\.md$")

FATIAS = "banco.md, contratos.md, visual.md, decisoes-tecnicas.md"


def message(agente: str) -> str:
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — {agente} nao le o project-core.md inteiro (D6)\n"
        f"\n"
        f"Executores leem as FATIAS do project-core, que estao liberadas:\n"
        f"  .delta-11/memoria/project-core/  — {FATIAS} (conforme o seu papel)\n"
        f"Mais: .delta-11/planos/{agente}-plan.md, a sua coluna do kanban,\n"
        f"pesquisa-tecnica.md e a sua base de conhecimento.\n"
        f"\n"
        f"Se faltar alguma informacao, peca ao CRONOS por SendMessage:\n"
        f"  {{\"agente\": \"{agente}\", \"pedido\": \"preciso do trecho do project-core sobre X\"}}\n"
    )


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") != "Read":
        return 0
    caminho = comum.target_path_text(evento).replace("\\", "/")
    if not PROJECT_CORE_INTEIRO_RE.search(caminho):
        return 0
    if comum.is_sub_agent_type(evento):
        return 0  # sub-agente (build-validator, qa-ui-tandem...) pode ler
    agente = comum.identify_agent(evento)
    if agente in comum.EXECUTORES_SEM_PROJECT_CORE:
        return comum.block(HOOK, message(agente), f"{agente} tentou ler o project-core.md inteiro")
    if agente is None:
        comum.log(HOOK, "INFO: leitura do project-core.md sem agente identificado (liberada)")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
