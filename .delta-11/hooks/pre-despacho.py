#!/usr/bin/env python3
"""
Vigia PreToolUse "pre-despacho" — Delta-11 v6.3 (2026-10-14). C-016, C-184.

Bloqueia o despacho de um agente EXECUTOR quando o brief (o `prompt` da chamada do
Agent tool) passa do limite `brief_max_tokens` (padrao 4.000 tokens, em
.delta-11/.config-limites.json — D36). O recado nao e "escreva briefs menores": e
"DIVIDA em sub-tarefas irmas PARALELAS" (v6.4 — V3), cada uma com um agente novo de contexto limpo.

Registro: PreToolUse com matcher "Agent|Task" (o Agent tool ja se chamou Task).

Logica:
  1. So age quando a ferramenta e Agent/Task.
  2. Identifica o alvo: campo `name` (ex.: "back-onda-2" -> BACK), linha
     "Agente: NOME" no prompt, ou nome de sub-agente na descricao/prompt.
  3. ATLAS, CRONOS e sub-agentes sao isentos. Alvo desconhecido passa.
  4. Executor (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SHIELD, SCOUT): conta
     tokens (4 caracteres = 1 token) e bloqueia (exit 2) acima do limite.

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

HOOK = "pre-despacho"
APROXIMACAO_CHARS_POR_TOKEN = comum.CHARS_POR_TOKEN

AGENTES_EXECUTORES = set(comum.EXECUTORES_COM_SHIELD)

# Isentos: ATLAS (arquiteto), CRONOS (orquestrador), e todos os sub-agentes
AGENTES_ISENTOS = {"ATLAS", "CRONOS"}
SUBAGENTES_NOMES = set(comum.SUB_AGENTES)


def limite_tokens() -> int:
    """D36: brief_max_tokens em .delta-11/.config-limites.json (padrao 4000)."""
    return int(comum.limits()["brief_max_tokens"])


def log_activity(mensagem: str) -> None:
    comum.log(HOOK, mensagem)


def eh_despacho_de_agente(event: dict) -> bool:
    """Detecta se a tool é o Agent tool (chamado 'Task' internamente)."""
    tool_name = event.get("tool_name", "")
    return tool_name in {"Task", "Agent"}


def obter_prompt(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    return tool_input.get("prompt", "") or ""


def identificar_alvo(event: dict, prompt: str) -> str:
    """Alvo do despacho — regra unica em _comum.dispatch_target."""
    return comum.dispatch_target(event)


def contar_tokens_aproximado(texto: str) -> int:
    if not texto:
        return 0
    return len(texto) // APROXIMACAO_CHARS_POR_TOKEN


def bloquear_despacho(alvo: str, tokens: int, prompt_preview: str) -> int:
    excesso = tokens - limite_tokens()
    log_activity(f"BLOQUEIO: despacho de {alvo} com {tokens} tokens > {limite_tokens()}")
    print(
        f"[pre-despacho] BLOQUEIO {comum.VERSAO} — Granularização forçada\n"
        f"\n"
        f"Você (CRONOS) está tentando despachar {alvo} com um brief de\n"
        f"{tokens} tokens. Limite duro para executores: {limite_tokens()} tokens.\n"
        f"Excesso: {excesso} tokens.\n"
        f"\n"
        f"NÃO suba o limite. NÃO compacte o brief só pra passar. Em vez disso:\n"
        f"\n"
        f"  DIVIDA EM SUB-TAREFAS IRMÃS PARALELAS (v6.4 — V3).\n"
        f"\n"
        f"Cada irmã é um agente NOVO, com contexto LIMPO, na sua própria worktree,\n"
        f"disparadas JUNTAS na mesma mensagem (nunca 'ondas em série' por tamanho).\n"
        f"Se você precisa de mais de {limite_tokens()} tokens pra explicar\n"
        f"uma tarefa, ela provavelmente é COMPLEXA DEMAIS pra um único brief.\n"
        f"Só fica em série se uma irmã depender da outra (dependência declarada).\n"
        f"\n"
        f"Como aplicar:\n"
        f"  1. Pegue as 6 seções do mini-plano (Objetivo da onda / Recorte da fase\n"
        f"     anterior / Tarefas / Critérios de aceite / Limites de escopo /\n"
        f"     Convenções — D17) e veja qual está engordando.\n"
        f"  2. Se 'Recorte da fase anterior' é grande, divida em irmãs: T-XXXa no\n"
        f"     sub-domínio A e T-XXXb no sub-domínio B, disparadas juntas.\n"
        f"  3. Se 'Critérios de aceite' tem 8+ itens, divida em 2-3 irmãs com 3\n"
        f"     critérios cada.\n"
        f"  4. Cada irmã tem seu mini-plano enxuto, com a linha 'Sub-tarefa irmã de:'.\n"
        f"\n"
        f"Por que o limite duro: na v4.0.x isso era diagnóstico (aviso) e, na\n"
        f"prática, os briefs foram inflando sem ninguém perceber. Desde a v5 é freio.\n"
        f"\n"
        f"Início do brief que foi bloqueado (primeiros 300 chars):\n"
        f"{prompt_preview[:300]}...\n"
        f"\n"
        f"Agentes ISENTOS deste limite: ATLAS, CRONOS e todos os sub-agentes\n"
        f"({', '.join(sorted(SUBAGENTES_NOMES))}).",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = comum.read_event()

    if not eh_despacho_de_agente(event):
        return 0

    prompt = obter_prompt(event)
    if not prompt:
        return 0

    alvo = identificar_alvo(event, prompt)

    # Isento: ATLAS / CRONOS / sub-agentes (sub-agentes têm nome em minúsculo)
    if alvo in AGENTES_ISENTOS or alvo.lower() in SUBAGENTES_NOMES:
        log_activity(f"Despacho de {alvo} ISENTO de limite (papel arquitetural/sub-agente)")
        return 0

    # Se alvo não foi identificado, libera (degradação graciosa)
    if not alvo:
        log_activity(
            "Despacho com alvo não identificado — allow (degradação graciosa)"
        )
        return 0

    # Se alvo NÃO é executor conhecido, libera (pode ser nome customizado)
    if alvo not in AGENTES_EXECUTORES:
        log_activity(f"Despacho de {alvo} — não é executor conhecido, allow")
        return 0

    # Alvo é executor — checa tokens
    tokens = contar_tokens_aproximado(prompt)
    if tokens <= limite_tokens():
        log_activity(
            f"Despacho de {alvo} OK ({tokens} tokens ≤ {limite_tokens()})"
        )
        return 0

    return bloquear_despacho(alvo, tokens, prompt)


if __name__ == "__main__":
    comum.run(main, HOOK)
