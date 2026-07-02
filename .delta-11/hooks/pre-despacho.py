#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v5: bloqueia o despacho de um agente executor
quando o brief (prompt da chamada do Agent tool) ultrapassa 2.000 tokens.

Materializa o objetivo central da v5: forçar GRANULARIZAÇÃO em mais ondas
com janelas de contexto limpas. O limite NÃO é "escreva briefs menores"
— é "se você precisa de mais de 2.000 tokens pra explicar uma tarefa,
QUEBRE em mais ondas, cada uma com seu próprio agente novo de contexto
limpo".

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.

Invocação:
  PreToolUse matcher = "Task"  (o nome interno do Agent tool no Claude Code)
  command = python3 .delta-11/hooks/pre-despacho.py

Lógica:
  1. Lê o evento JSON via stdin
  2. Verifica se a tool é Task (Agent)
  3. Extrai o prompt do tool_input
  4. Identifica o agente-alvo pelo nome no prompt ("Agente: NOME") OU
     pelo campo `subagent_type` / `name`
  5. Se alvo é ATLAS, CRONOS ou sub-agente → exit 0 (liberado)
  6. Se alvo é um dos 8 executores → conta tokens do prompt
  7. Se tokens > 2.000 → exit 2 (bloqueia + instruir CRONOS a quebrar em
     mais ondas)
  8. Caso contrário → exit 0

Exit codes:
  0 = pode prosseguir
  2 = BLOQUEAR
  1 = erro interno (não bloqueia — loga e deixa passar)

Política de calibração v5:
  LIMITE_TOKENS_EXECUTOR = 2.000 (decisão do comandante 2026-06-23)
  APROXIMACAO_TOKEN = 4 chars/token (mesmo padrão do pre-selo.py)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


LIMITE_TOKENS_EXECUTOR = 2000
APROXIMACAO_CHARS_POR_TOKEN = 4

AGENTES_EXECUTORES = {
    "BACK", "FRONT", "PIXEL", "FORM",
    "ENGINE", "VAULT", "SHIELD", "SCOUT",
}

# Isentos: ATLAS (arquiteto), CRONOS (orquestrador), e todos os sub-agentes
AGENTES_ISENTOS = {"ATLAS", "CRONOS"}
SUBAGENTES_NOMES = {
    "build-validator", "code-simplifier", "contract-tester",
    "code-architect", "schema-validator", "verify-app",
    "fresh-reviewer", "cold-start-tester", "impact-mapper",
}

ACTIVITY_LOG = Path(".delta-11/activity-log.md")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{timestamp}] pre-despacho: {mensagem}\n")
    except OSError:
        pass


def read_hook_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def eh_despacho_de_agente(event: dict) -> bool:
    """Detecta se a tool é o Agent tool (chamado 'Task' internamente)."""
    tool_name = event.get("tool_name", "")
    return tool_name in {"Task", "Agent"}


def obter_prompt(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    return tool_input.get("prompt", "") or ""


def identificar_alvo(event: dict, prompt: str) -> str:
    """
    Tenta identificar quem é o agente-alvo do despacho.
    Ordem:
    1. Campo `name` ou `subagent_type` do tool_input (ex: "engine-onda-2")
    2. Linha "Agente: NOME" no prompt
    3. "" se não conseguir
    """
    tool_input = event.get("tool_input") or {}

    # 1. Campo name
    nome = tool_input.get("name", "")
    if nome:
        # name vem em minúsculo tipo "engine-onda-2"
        # Extrair a parte do nome do agente
        match = re.match(r"([a-z]+)", nome.lower())
        if match:
            candidato = match.group(1).upper()
            if candidato in AGENTES_EXECUTORES or candidato in AGENTES_ISENTOS:
                return candidato

    # 2. Linha "Agente: NOME" no prompt
    match = re.search(r"Agente:\s*([A-Z_-]+)", prompt)
    if match:
        return match.group(1).strip()

    # 3. Sub-agente? Procura nome de sub-agente no prompt/description
    description = (tool_input.get("description", "") or "").lower()
    for sub in SUBAGENTES_NOMES:
        if sub in description or sub in prompt.lower():
            return sub  # retorna em minúsculo pra distinguir

    return ""


def contar_tokens_aproximado(texto: str) -> int:
    if not texto:
        return 0
    return len(texto) // APROXIMACAO_CHARS_POR_TOKEN


def bloquear_despacho(alvo: str, tokens: int, prompt_preview: str) -> int:
    excesso = tokens - LIMITE_TOKENS_EXECUTOR
    print(
        f"[pre-despacho] BLOQUEIO v5 — Granularização forçada\n"
        f"\n"
        f"Você (CRONOS) está tentando despachar {alvo} com um brief de\n"
        f"{tokens} tokens. Limite duro para executores: {LIMITE_TOKENS_EXECUTOR} tokens.\n"
        f"Excesso: {excesso} tokens.\n"
        f"\n"
        f"NÃO suba o limite. NÃO compacte o brief só pra passar. Em vez disso:\n"
        f"\n"
        f"  QUEBRE A ONDA EM MAIS ONDAS.\n"
        f"\n"
        f"Princípio da v5: cada onda dispara um agente NOVO com contexto LIMPO.\n"
        f"Se você precisa de mais de {LIMITE_TOKENS_EXECUTOR} tokens pra explicar\n"
        f"uma tarefa, ela provavelmente é COMPLEXA DEMAIS pra um único brief.\n"
        f"Divida em 2-3 tarefas menores, cada uma virando uma onda separada.\n"
        f"\n"
        f"Como aplicar:\n"
        f"  1. Pegue as 5 seções do mini-plano (Produzir / Recorte / Critérios /\n"
        f"     Dependências / Limites de Escopo) e veja qual está engordando.\n"
        f"  2. Se 'Recorte da fase anterior' é grande, divida a tarefa em duas:\n"
        f"     a primeira foca em sub-domínio A, a segunda em sub-domínio B.\n"
        f"  3. Se 'Critérios de sucesso' tem 8+ itens, vire 2-3 ondas com 3 critérios\n"
        f"     cada.\n"
        f"  4. Cada nova onda terá seu próprio mini-plano enxuto e seu agente nasce\n"
        f"     com contexto limpo.\n"
        f"\n"
        f"Por que o limite duro: na v4.0.x isso era diagnóstico (warning), e na\n"
        f"prática briefs foram inflando sem você perceber. Na v5 vira freio.\n"
        f"\n"
        f"Início do brief que foi bloqueado (primeiros 300 chars):\n"
        f"{prompt_preview[:300]}...\n"
        f"\n"
        f"Agentes ISENTOS deste limite: ATLAS, CRONOS, todos os sub-agentes\n"
        f"(build-validator, code-simplifier, contract-tester, code-architect,\n"
        f"fresh-reviewer, cold-start-tester, etc.).",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = read_hook_event()

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
    if tokens <= LIMITE_TOKENS_EXECUTOR:
        log_activity(
            f"Despacho de {alvo} OK ({tokens} tokens ≤ {LIMITE_TOKENS_EXECUTOR})"
        )
        return 0

    log_activity(
        f"Despacho de {alvo} BLOQUEADO ({tokens} tokens > {LIMITE_TOKENS_EXECUTOR})"
    )
    return bloquear_despacho(alvo, tokens, prompt)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        log_activity(f"ERRO no hook: {exc}")
        sys.exit(1)
