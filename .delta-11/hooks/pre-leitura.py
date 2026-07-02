#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v5: bloqueia o agente executor de ler o
`project-core.md` monolítico.

Materializa a Mudança Estrutural v5 — guarda técnica do project-core.
Em v4.0.4 a regra "executores não leem project-core" era APENAS textual.
A v5 transforma em bloqueio com hook.

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.

Invocação:
  PreToolUse matcher = "Read"
  command = python3 .delta-11/hooks/pre-leitura.py

Lógica:
  1. Lê o evento JSON via stdin
  2. Verifica se a tool é Read
  3. Verifica se o file_path matcha .delta-11/memoria/project-core.md
  4. Identifica o agente que está lendo (via ACK mais recente em
     .delta-11/ativacoes/)
  5. Se ATLAS ou CRONOS → exit 0 (libera)
  6. Se um dos 8 executores → exit 2 (bloqueia + mensagem orientadora)
  7. Se não conseguir identificar → exit 0 (degradação graciosa — não trava
     o sistema; v5 prefere falhar aberto a falhar fechado)

Exit codes:
  0 = pode prosseguir
  2 = BLOQUEAR (PreToolUse hook convention da Anthropic)
  1 = erro interno (não bloqueia por default — loga e deixa passar)

Identificação do agente (heurística v5):
  - Lista .delta-11/ativacoes/ack-*.txt
  - Pega o arquivo com mtime mais recente
  - Extrai o nome do agente do filename: ack-VAULT.txt → VAULT
  - Limitação conhecida: agentes paralelos ativados em janela <2s podem
    confundir a identificação. Aceitável para v5; refinar em v6 com
    mapeamento session_id → agente.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


# Agentes que PODEM ler o project-core.md inteiro
AGENTES_AUTORIZADOS = {"ATLAS", "CRONOS"}

# Agentes que NÃO podem (executores)
AGENTES_EXECUTORES = {
    "BACK", "FRONT", "PIXEL", "FORM",
    "ENGINE", "VAULT", "SHIELD", "SCOUT",
}

ACTIVITY_LOG = Path(".delta-11/activity-log.md")
ACK_DIR = Path(".delta-11/ativacoes")


def log_activity(mensagem: str) -> None:
    """Anexa linha ao activity-log (mesmo padrão do pre-selo.py)."""
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{timestamp}] pre-leitura: {mensagem}\n")
    except OSError:
        # Falha em log não deve travar o hook
        pass


def read_hook_event() -> dict:
    """Lê o evento JSON via stdin (mesmo padrão do pre-selo.py)."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def eh_leitura_de_project_core(event: dict) -> bool:
    """
    Detecta se a tool é Read e o arquivo é o project-core.md monolítico.
    Bloqueia APENAS o documento principal — fatias por domínio em
    .delta-11/memoria/project-core/ são liberadas (executor pode ler).
    """
    tool_name = event.get("tool_name", "")
    if tool_name != "Read":
        return False

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""

    # Match exato: .delta-11/memoria/project-core.md (documento principal)
    # Não bloqueia: .delta-11/memoria/project-core/banco.md (fatia)
    return bool(re.search(
        r"[\\/]\.delta-11[\\/]memoria[\\/]project-core\.md$",
        file_path,
    ))


def identificar_agente_corrente() -> str | None:
    """
    Heurística v5: olha o ACK mais recentemente modificado em
    .delta-11/ativacoes/ack-[NOME].txt. Retorna o NOME ou None se não
    conseguir identificar.
    """
    if not ACK_DIR.exists():
        return None

    acks = list(ACK_DIR.glob("ack-*.txt"))
    if not acks:
        return None

    # Mais recente por mtime
    acks.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    mais_recente = acks[0]

    # ack-VAULT.txt → VAULT
    match = re.match(r"ack-([A-Z_-]+)\.txt$", mais_recente.name)
    if not match:
        return None
    return match.group(1)


def bloquear_leitura(agente: str) -> int:
    """Exit 2 bloqueia a tool (PreToolUse hook convention)."""
    print(
        f"[pre-leitura] BLOQUEIO v5 — Guarda Técnica do project-core\n"
        f"\n"
        f"Agente {agente} tentou ler `.delta-11/memoria/project-core.md` (documento\n"
        f"principal). Executores (BACK, FRONT, PIXEL, FORM, ENGINE, VAULT, SHIELD,\n"
        f"SCOUT) NÃO devem ler o project-core monolítico — ele contém visão\n"
        f"arquitetural multi-fase que polui o contexto.\n"
        f"\n"
        f"O que fazer:\n"
        f"  1. Releia seu mini-plano em `.delta-11/planos/{agente}-plan.md`\n"
        f"     — o CRONOS já recortou as fatias relevantes pra você lá.\n"
        f"  2. Se precisar de info adicional do project-core, envie SendMessage\n"
        f"     ao CRONOS com payload:\n"
        f"     {{\"agente\": \"{agente}\", \"pedido\": \"preciso da fatia X do\n"
        f"      project-core sobre TÓPICO_Y\"}}\n"
        f"  3. CRONOS responderá com o trecho específico (ou autorizará leitura).\n"
        f"\n"
        f"Fatias acessíveis SEM bloqueio (se existirem no projeto):\n"
        f"  - `.delta-11/memoria/project-core/banco.md`\n"
        f"  - `.delta-11/memoria/project-core/contratos.md`\n"
        f"  - `.delta-11/memoria/project-core/visual.md`\n"
        f"  - `.delta-11/memoria/project-core/decisoes-tecnicas.md`\n"
        f"\n"
        f"Princípio v5: cada agente da camada vê SÓ o que precisa pra construir\n"
        f"sua peça, sem carregar o todo do projeto. Janela de contexto limpa =\n"
        f"trabalho mais exato.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = read_hook_event()

    if not eh_leitura_de_project_core(event):
        # Não é leitura do project-core — deixa passar
        return 0

    agente = identificar_agente_corrente()
    if agente is None:
        # Não conseguiu identificar — degradação graciosa, deixa passar
        log_activity("Leitura de project-core SEM identificação de agente (allow)")
        return 0

    if agente in AGENTES_AUTORIZADOS:
        log_activity(f"Leitura de project-core por {agente} (autorizado)")
        return 0

    if agente in AGENTES_EXECUTORES:
        log_activity(f"Leitura de project-core BLOQUEADA — agente {agente} é executor")
        return bloquear_leitura(agente)

    # Agente desconhecido — log e libera
    log_activity(f"Leitura de project-core por agente desconhecido: {agente} (allow)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        log_activity(f"ERRO no hook: {exc}")
        # Erro interno não bloqueia (mesmo padrão do pre-selo.py)
        sys.exit(1)
