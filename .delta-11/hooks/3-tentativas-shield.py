#!/usr/bin/env python3
"""
Vigia "3 tentativas do SHIELD" — Delta-11 v6.3 (2026-10-14). Itens C-002, C-018, D23, D35.

Regra (D23): quando o SHIELD reprova o trabalho de um mesmo agente 3 vezes dentro da
janela (`janela_horas`, padrao 4 h, em .config-limites.json), o CRONOS NAO dispara
de novo esse agente para insistir: dispara um SCOUT NOVO com contexto limpo (um
resumo do problema). Depois de 6 falhas no total, o CRONOS dispara o ATLAS.

Formato lido (D35) em `.delta-11/logs/sub-agentes/shield-falhas.log` da pasta
principal:
    [AAAA-MM-DDTHH:MM:SSZ] [AGENTE-AVALIADO] FAIL T-XXX motivo
  - O agente e o colchete logo DEPOIS do horario (C-018). Uma linha antiga no
    formato "[TS] [SHIELD] [AGENTE] FAIL" nao e contada como falha "do SHIELD": o
    agente certo e o colchete seguinte.
  - Linha sem horario e ignorada (nao da para saber se ainda vale).
  - Uma aprovacao posterior no activity-log (`[SHIELD] APROVADO T-XXX [AGENTE]`,
    D33) zera a contagem daquele agente.

Eventos (registro feito em settings-hooks.json):
  - PreToolUse com matcher "Agent|Task": bloqueia (exit 2) SO o disparo de agente
    cujo alvo esta travado:
        alvo com 3+ falhas (exceto SCOUT)  -> bloqueia; dispare um SCOUT novo
        alvo SCOUT com 6+ falhas no total  -> bloqueia; dispare o ATLAS
    ATLAS, CRONOS e sub-agentes nunca sao bloqueados.
  - SessionStart: nao bloqueia (o Claude Code nao deixa). Sai com 0 e devolve um
    aviso em `additionalContext` listando os agentes travados.

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

HOOK = "3-tentativas-shield"
LIMITE_FALHAS = 3
LIMITE_TOTAL = 6  # D23: depois de 6, o CRONOS dispara o ATLAS
_ID = r"[A-Za-z][\w.]*-[\w.-]+"
FALHA_RE = re.compile(
    r"^\s*-?\s*\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2}))\]\s*"
    r"(?:\[SHIELD\]\s*)?"            # formato antigo "[TS] [SHIELD] [AGENTE] FAIL"
    rf"\[([A-Za-z_-]+)\]\s*FAIL\b\s*({_ID})?",
)
APROVADO_RE = re.compile(rf"\[SHIELD\]\s+APROVADO\s+({_ID})\s+\[([A-Z]+)\]")
NAO_BLOQUEIA = {"ATLAS", "CRONOS"}


def last_approvals() -> dict:
    """{AGENTE: datetime da ultima aprovacao do SHIELD} lida do activity-log."""
    texto = comum.read_text(comum.delta_dir() / "activity-log.md")
    ultimas: dict = {}
    for linha in texto.splitlines():
        achado = APROVADO_RE.search(linha)
        quando = comum.line_timestamp(linha)
        if achado and quando:
            agente = achado.group(2)
            if agente not in ultimas or quando > ultimas[agente]:
                ultimas[agente] = quando
    return ultimas


def count_failures() -> dict:
    """{AGENTE: [linhas de falha]} dentro da janela e depois da ultima aprovacao."""
    texto = comum.read_text(comum.delta_dir() / "logs" / "sub-agentes" / "shield-falhas.log")
    if not texto:
        return {}
    agora = comum.now_utc()
    janela = comum.window_seconds()
    aprovacoes = last_approvals()
    falhas: dict = {}
    for linha in texto.splitlines():
        achado = FALHA_RE.match(linha)
        if not achado:
            continue
        quando = comum.parse_timestamp(achado.group(1))
        agente = achado.group(2).upper()
        if agente == "SHIELD" or quando is None or (agora - quando).total_seconds() > janela:
            continue
        if agente in aprovacoes and aprovacoes[agente] >= quando:
            continue
        falhas.setdefault(agente, []).append(linha.strip())
    return falhas


def limit_for(agente: str) -> int:
    return LIMITE_TOTAL if agente == "SCOUT" else LIMITE_FALHAS


def travados() -> dict:
    return {a: l for a, l in count_failures().items() if len(l) >= limit_for(a)}


def message(agente: str, linhas: list) -> str:
    horas = comum.limits()["janela_horas"]
    lista = "\n".join(f"  {l}" for l in linhas[-6:])
    if agente == "SCOUT":
        proximo = (
            "Ja foram 6 falhas ou mais no total. Pela regra D23 o CRONOS agora dispara o\n"
            "ATLAS (problema estrutural) e, se preciso, avisa o comandante."
        )
    else:
        proximo = (
            f"Nao dispare {agente} de novo para insistir na mesma tarefa. Pela regra D23 o\n"
            "CRONOS dispara um SCOUT NOVO, com contexto limpo e um resumo do problema\n"
            "(o que foi tentado e por que o SHIELD reprovou)."
        )
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — o SHIELD reprovou {agente} {len(linhas)}x nas ultimas {horas} h\n"
        f"\n"
        f"Falhas registradas (.delta-11/logs/sub-agentes/shield-falhas.log):\n{lista}\n"
        f"\n{proximo}\n"
        f"\nA trava some quando o SHIELD gravar `[SHIELD] APROVADO T-XXX [{agente}]` no\n"
        f"activity-log, ou quando as falhas saem da janela de {horas} h.\n"
    )


def main() -> int:
    evento = comum.read_event()

    if evento.get("hook_event_name") == "SessionStart":
        presos = travados()
        if presos:
            aviso = "; ".join(f"{a}: {len(l)} reprovacoes do SHIELD" for a, l in presos.items())
            comum.log(HOOK, f"AVISO SessionStart: {aviso}", "SISTEMA")
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        "Delta-11 — regra das 3 tentativas (D23): " + aviso + ". "
                        "O CRONOS nao redispara esses agentes; dispara um SCOUT novo com contexto "
                        "limpo (e o ATLAS depois de 6 falhas)."
                    ),
                }
            }, ensure_ascii=False))
        return 0

    if evento.get("tool_name") not in {"Agent", "Task"}:
        return 0
    alvo = comum.dispatch_target(evento)
    if not alvo or alvo in NAO_BLOQUEIA or alvo.lower() in comum.SUB_AGENTES:
        return 0
    linhas = travados().get(alvo.upper())
    if not linhas:
        return 0
    return comum.block(HOOK, message(alvo.upper(), linhas), f"disparo de {alvo} com {len(linhas)} falhas do SHIELD")


if __name__ == "__main__":
    comum.run(main, HOOK)
