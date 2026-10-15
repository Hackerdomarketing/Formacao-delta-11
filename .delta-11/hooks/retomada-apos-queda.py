#!/usr/bin/env python3
"""
Vigia SessionStart "retomada apos queda" — Delta-11 v6.4.1 (2026-10-15).

Problema que resolve: quando a sessao principal cai (Mac reiniciou, VS Code fechou,
contexto acabou), TODOS os agentes que ela disparou morrem junto. Mas o painel, o
kanban-data.js e o pulsos-data.js continuam dizendo "T-258 em andamento", "SHIELD
ativo". Quem retoma confiando no painel fica esperando um trabalho que nao existe.
(Caso real: salvahacks, 2026-10-15 — o ATLAS percebeu sozinho, conferindo o disco.)

Quando age (SessionStart, exceto o retorno de compactacao — `source: "compact"` —
em que a sessao continua viva e os agentes em segundo plano tambem):
  - agentes com `tarefa_atual` preenchida no kanban-data.js;
  - agentes com status "ativo"/"aguardando"/"trabalhando" no pulsos-data.js.
Devolve um aviso em `additionalContext`: esses trabalhos NAO estao rodando; confira o
disco (branch/worktree da tarefa, relatorio, commits) antes de redisparar.
Nunca bloqueia (o Claude Code nao deixa no SessionStart) e nao altera arquivo nenhum.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "retomada-apos-queda"
STATUS_VIVOS = {"ativo", "aguardando", "trabalhando", "contexto_critico"}
TAREFA_ATUAL_RE = re.compile(
    r"""agente\s*:\s*["'`]([^"'`]+)["'`][^{}]*?tarefa_atual\s*:\s*["'`]([^"'`]*)["'`]""", re.IGNORECASE
)
PULSOS_RE = re.compile(r"window\.D11_PULSOS\s*=\s*(\{.*\})\s*;?\s*$", re.DOTALL)


def tasks_in_progress(delta) -> list[tuple[str, str]]:
    texto = comum.read_text(delta / "kanban-data.js")
    return [(a.strip(), t.strip()) for a, t in TAREFA_ATUAL_RE.findall(texto) if t.strip()]


def agents_marked_alive(delta) -> list[tuple[str, str, str]]:
    achado = PULSOS_RE.search(comum.read_text(delta / "pulsos-data.js").strip())
    if not achado:
        return []
    try:
        dados = json.loads(achado.group(1))
    except ValueError:
        return []
    vivos = []
    for agente, pulso in (dados.get("agentes") or {}).items():
        if isinstance(pulso, dict) and str(pulso.get("status") or "").lower() in STATUS_VIVOS:
            vivos.append((agente, str(pulso.get("status")), str(pulso.get("ultimo_sinal") or "sem sinal")))
    return vivos


def main() -> int:
    evento = comum.read_event()
    if evento.get("hook_event_name") not in (None, "SessionStart"):
        return 0
    if str(evento.get("source") or "").lower() == "compact":
        return 0
    delta = comum.delta_dir()
    if not delta.is_dir():
        return 0
    tarefas = tasks_in_progress(delta)
    vivos = agents_marked_alive(delta)
    if not tarefas and not vivos:
        return 0
    linhas = ["RETOMADA APOS QUEDA (vigia retomada-apos-queda): esta e uma sessao NOVA. Nenhum agente da",
              "sessao anterior continua rodando — eles morrem junto com a sessao principal. Estes registros",
              "dizem o contrario e estao DESATUALIZADOS:"]
    linhas += [f"  - kanban-data.js: {a} — tarefa_atual \"{t[:120]}\"" for a, t in tarefas]
    linhas += [f"  - pulsos-data.js: {a} com status \"{s}\" (ultimo sinal {u})" for a, s, u in vivos]
    linhas += ["Antes de redisparar ou de esperar por qualquer um deles, confira o DISCO: a branch/worktree da",
               "tarefa, o relatorio esperado, os commits e o activity-log. O que nao terminou e redisparado;",
               "o que terminou e registrado. Nao confie no painel para esses itens."]
    aviso = "\n".join(linhas)
    comum.log(HOOK, f"AVISO SessionStart: {len(tarefas)} tarefa(s) e {len(vivos)} pulso(s) da sessao anterior", "SISTEMA")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": aviso}}))
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
