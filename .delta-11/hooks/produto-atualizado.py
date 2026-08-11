#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: bloqueia Edits no kanban.md
marcando CONCLUIDO se o [AGENTE]-produto.md do agente executor
NAO foi tocado nas ultimas 4 horas (sinal de desatualizacao).

Materializa o Furo #3 da auditoria 2026-08-11: 'FRONT/PIXEL/VAULT/
ATLAS-produto.md desatualizados'. pre-selo.py so' conta tokens;
nao detecta estagnacao.

ALVO: Edits no kanban.md que marcam tarefa como CONCLUIDA.

LOGICA:
  1. Detecta edit em .delta-11/kanban.md com transicao CONCLUIDO
  2. Identifica o agente (BACK, FRONT, PIXEL, FORM, ENGINE, VAULT,
     SHIELD, SCOUT) na tarefa
  3. Verifica o mtime do .delta-11/memoria/[AGENTE]-produto.md
  4. Se produto.md do agente NAO foi tocado nas ultimas 4 horas
     (idade > 4h): BLOQUEIA
  5. Se produto.md foi tocado em <=4h: PASSA
  6. Se produto.md NAO EXISTE: BLOQUEIA (agente nunca atualizou)

EXIT CODES:
  0 = pode prosseguir (produto.md tocado em <=4h)
  2 = BLOQUEAR (produto.md desatualizado ou ausente)
  1 = erro interno

Cross-platform. Python 3.8+.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
KANBAN_FILE = Path(".delta-11/kanban.md")
MEMORIA_DIR = Path(".delta-11/memoria")

# Janela: 4 horas. Se produto.md do agente nao foi tocado em <=4h,
# o agente provavelmente pulou a autualizacao e escreveu "CONCLUIDO"
# no kanban sem refletir no estado.
JANELA_SEGUNDOS = 4 * 60 * 60

# Agentes executores que devem manter produto.md atualizado
AGENTES_EXECUTORES = {
    "BACK", "FRONT", "PIXEL", "FORM",
    "ENGINE", "VAULT", "SHIELD", "SCOUT",
}

CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE
)
AGENTE_TAG_RE = re.compile(r"\[([A-Z_-]+)\]")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [produto-atualizado] {mensagem}\n")
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
    lines = content.split("\n")
    for line in lines:
        if CONCLUSAO_RE.search(line):
            match = AGENTE_TAG_RE.search(line)
            if match:
                agente = match.group(1)
                if agente in AGENTES_EXECUTORES:
                    return agente
    return None


def produto_mtime_idade(agente: str) -> float | None:
    """
    Retorna idade em segundos do [AGENTE]-produto.md.
    Retorna None se o arquivo nao existir.
    """
    path = MEMORIA_DIR / f"{agente}-produto.md"
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        return time.time() - mtime
    except OSError:
        return None


def block_stale(agente: str, file_path: str, idade: float | None) -> int:
    if idade is None:
        motivo = f"{agente}-produto.md NAO EXISTE em .delta-11/memoria/"
        acao = (
            f"  1. Crie/atualize .delta-11/memoria/{agente}-produto.md com o\n"
            f"     estado atual do produto para esta tarefa (limite: 500 tokens).\n"
        )
    else:
        horas = idade / 3600
        motivo = f"{agente}-produto.md foi tocado pela ultima vez ha {horas:.1f}h"
        acao = (
            f"  1. Atualize .delta-11/memoria/{agente}-produto.md AGORA com o\n"
            f"     estado atual do produto. Use o template estado-produto\n"
            f"     (max 500 tokens; hook pre-selo.py vai validar).\n"
        )

    msg = (
        f"[produto-atualizado] BLOQUEIO v6.2.0 — produto.md desatualizado\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Agente: {agente}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que FRONT/PIXEL/\n"
        f"VAULT e outros agentes marcavam tarefas como CONCLUIDO sem\n"
        f"atualizar o [AGENTE]-produto.md. Resultado: estado do projeto\n"
        f"ficou desatualizado, CRONOS perdia contexto, e a selagem\n"
        f"perdia rastreabilidade. 'Protecao que depende de agente\n"
        f"obedecer prompt NAO e' protecao' (Principio 2 do D-11).\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"{acao}"
        f"  2. Apos o update, repita a marcacao CONCLUIDO no kanban.\n"
        f"     Hook passara.\n"
        f"\n"
        f"  3. Janela permitida: 4h. Se passou mais que 4h desde o\n"
        f"     ultimo touch, hook BLOQUEIA novamente.\n"
        f"\n"
        f"Referencia: Furo 3 da auditoria 2026-08-11 (D-scan completo).\n"
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
            return 0

        idade = produto_mtime_idade(agente)

        if idade is None or idade > JANELA_SEGUNDOS:
            log_activity(
                f"BLOQUEIO: {agente} tentou CONCLUIDO sem produto.md atualizado"
            )
            return block_stale(agente, file_path, idade)

        log_activity(f"OK: {agente}-produto.md tocado em {idade/3600:.1f}h — CONCLUIDO liberado")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[produto-atualizado] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[produto-atualizado] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)