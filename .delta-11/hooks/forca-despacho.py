#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: bloqueia mark CONCLUIDO no kanban
se o agente executor (BACK, FRONT, PIXEL, FORM, ENGINE, VAULT, SHIELD,
SCOUT) nao tiver disparado sub-agente de validacao obrigatorio antes.

Materializa o Furo #2 da auditoria 2026-08-11: 'Zero disparo formal
de sub-agentes via Task tool'. BACK.md:164 manda via prompt 'Dispare
via Task tool'; pre-despacho.py valida o brief mas NAO FORCA disparo.
Agentes pulam e escrevem 'PASS' sem rodar.

ALVO: Edits no kanban.md que marcam tarefa como CONCLUIDA.

LOGICA:
  1. Detecta edit em .delta-11/kanban.md
  2. Verifica se novo conteudo inclui "CONCLUIDO" / "✅" (transicao)
  3. Se sim, identifica o agente da tarefa (por [AGENTE] no texto)
  4. Verifica no .delta-11/logs/sub-agentes/ se ha log recente de
     sub-agente build-validator ou contract-tester para este agente
     (ultimas 4 horas)
  5. Se agente eh executor e NAO tem log de sub-agente: BLOQUEIA
  6. Se agente eh executor e TEM log: PASSA
  7. Se agente NAO eh executor (ATLAS, CRONOS): PASSA (isentos)

EXIT CODES:
  0 = pode prosseguir (sub-agente foi disparado OU agente isento)
  2 = BLOQUEAR (sub-agente obrigatorio nao foi disparado)
  1 = erro interno (nao bloqueia)

Cross-platform. Python 3.8+.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
KANBAN_FILE = Path(".delta-11/kanban.md")
LOGS_DIR = Path(".delta-11/logs/sub-agentes")

# Janela de tempo: 4 horas. Sub-agente disparado mais de 4h atras
# NAO conta como "disparado recentemente".
JANELA_SEGUNDOS = 4 * 60 * 60

# Agentes executores que DEVEM disparar sub-agente antes de CONCLUIDO
AGENTES_EXECUTORES = {
    "BACK", "FRONT", "PIXEL", "FORM",
    "ENGINE", "VAULT", "SHIELD", "SCOUT",
}

# Sub-agentes obrigatorios por agente executor
SUB_AGENTES_OBRIGATORIOS = {
    "BACK": ["build-validator", "contract-tester"],
    "FRONT": ["build-validator"],
    "PIXEL": ["build-validator"],
    "FORM": ["build-validator"],
    "ENGINE": ["build-validator", "contract-tester"],
    "VAULT": ["build-validator", "contract-tester"],
    "SHIELD": ["verify-app"],
    "SCOUT": ["build-validator"],
}

# Marcadores de conclusao
CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE
)
# Tag de agente
AGENTE_TAG_RE = re.compile(r"\[([A-Z_-]+)\]")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [forca-despacho] {mensagem}\n")
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


def is_kanban_edit(event: dict) -> bool:
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return (
        file_path.endswith("/.delta-11/kanban.md")
        or file_path.endswith("\\.delta-11\\kanban.md")
    )


def get_combined_content(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    return (
        tool_input.get("new_string", "")
        + "\n"
        + tool_input.get("content", "")
    )


def touches_conclusion(content: str) -> bool:
    return bool(CONCLUSAO_RE.search(content))


def extract_agente_from_content(content: str) -> str | None:
    """Extrai o agente (ex: [BACK], [FRONT]) de uma tarefa concluida no kanban."""
    # Procura [AGENTE] em linhas que tambem tem marcador de conclusao
    lines = content.split("\n")
    for line in lines:
        if CONCLUSAO_RE.search(line):
            match = AGENTE_TAG_RE.search(line)
            if match:
                agente = match.group(1)
                if agente in AGENTES_EXECUTORES:
                    return agente
    return None


def has_recent_subagente_log(agente: str) -> bool:
    """Verifica se ha log de sub-agente obrigatorio nas ultimas 4 horas."""
    if not LOGS_DIR.exists():
        return False

    obrigatorios = SUB_AGENTES_OBRIGATORIOS.get(agente, [])
    if not obrigatorios:
        return True  # Agente sem sub-agente obrigatorio = ok

    import time
    agora = time.time()

    for log_file in LOGS_DIR.iterdir():
        if not log_file.is_file():
            continue
        # Verifica se o log eh de um sub-agente obrigatorio
        if not any(sub in log_file.name for sub in obrigatorios):
            continue
        # Verifica se eh do agente correto
        if agente.lower() not in log_file.name.lower():
            continue
        # Verifica idade
        try:
            idade = agora - log_file.stat().st_mtime
            if idade <= JANELA_SEGUNDOS:
                return True
        except OSError:
            continue

    return False


def block_conclusion(agente: str, file_path: str, sub_obrigatorios: list[str]) -> int:
    msg = (
        f"[forca-despacho] BLOQUEIO v6.2.0 — Sub-agente obrigatorio nao disparado\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Agente: {agente}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"Esta tentando marcar tarefa como CONCLUIDO no kanban, mas\n"
        f"a auditoria de 2026-08-11 (D-scan) documentou que BACK e outros\n"
        f"agentes pulavam o disparo de sub-agentes de validacao, escrevendo\n"
        f"'PASS' no relatorio sem realmente rodar. Isso quebra o\n"
        f"Principio 2 do D-11: 'Protecao que depende de agente obedecer\n"
        f"prompt NAO e' protecao'.\n"
        f"\n"
        f"Sub-agentes obrigatorios para {agente}:\n"
    )
    for sub in sub_obrigatorios:
        msg += f"  - {sub}\n"

    msg += (
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. ANTES de marcar CONCLUIDO, dispare cada sub-agente via\n"
        f"     Agent tool (subagent_type: general-purpose) com prompt\n"
        f"     incluindo o caminho absoluto do projeto:\n"
        f"\n"
        f"     Agent(\n"
        f"       description: \"{sub_obrigatorios[0]} para {agente}\",\n"
        f"       subagent_type: \"general-purpose\",\n"
        f"       run_in_background: false,\n"
        f"       prompt: \"Projeto em: [caminho]. Agente: {agente}.\n"
        f"         Rode os checks de {sub_obrigatorios[0]} agora.\"\n"
        f"     )\n"
        f"\n"
        f"  2. O log do sub-agente sera salvo em\n"
        f"     .delta-11/logs/sub-agentes/ automaticamente.\n"
        f"\n"
        f"  3. Apos o log existir (ate 4 horas), repita o CONCLUIDO no\n"
        f"     kanban. Hook passara.\n"
        f"\n"
        f"  4. Se sub-agente FALHAR: NAO marque CONCLUIDO. Crie tarefa\n"
        f"     adicional com tag [BLOQUEADO] para resolver o problema.\n"
        f"\n"
        f"Referencia: Furo 2 da auditoria 2026-08-11 (D-scan completo).\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        event = read_hook_event()

        if not is_kanban_edit(event):
            return 0

        file_path = (
            (event.get("tool_input") or {}).get("file_path", "")
            or "<desconhecido>"
        )
        combined = get_combined_content(event)

        if not touches_conclusion(combined):
            return 0

        agente = extract_agente_from_content(combined)
        if not agente:
            # Nao conseguiu identificar agente da tarefa = passa
            return 0

        if has_recent_subagente_log(agente):
            log_activity(f"OK: {agente} tem sub-agente recente — CONCLUIDO permitido")
            return 0

        log_activity(
            f"BLOQUEIO: {agente} tentou CONCLUIDO sem sub-agente recente"
        )
        return block_conclusion(
            agente,
            file_path,
            SUB_AGENTES_OBRIGATORIOS.get(agente, []),
        )

    except Exception as exc:  # noqa: BLE001
        print(f"[forca-despacho] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO nao-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[forca-despacho] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)