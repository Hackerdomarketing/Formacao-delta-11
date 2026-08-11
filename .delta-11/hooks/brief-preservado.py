#!/usr/bin/env python3
"""
Hook PostToolUse do Delta-11 v6.2: monitora .delta-11/ativacoes/*.txt
(briefs de agentes) — se arquivo for deletado ou sobrescrito com
tamanho < 50% do original, loga ALERTA no activity-log.

Materializa o Furo 8 da auditoria 2026-08-11 (D-scan completo):
'Brief inicial do CRONOS sumiu'. gc-locks.py NAO TOCA ativacoes.
Se agente sobrescreve ou deleta um brief, nao ha deteccao.

Este hook NAO BLOQUEIA (PostToolUse e' informativo). Apenas LOGA
o evento com severidade alta para o comandante ver no painel.

ALVO: PostToolUse em qualquer arquivo .delta-11/ativacoes/*.txt.

LOGICA:
  1. Detecta Write/Edit em .delta-11/ativacoes/*.txt
  2. Calcula tamanho novo do conteudo
  3. Compara com historico (se hook ja viu esse arquivo antes)
  4. Se tamanho novo < 50% do tamanho anterior (significa sobrescrita
     destrutiva ou delecao implicita): loga ALERTA
  5. Se arquivo eh novo: loga INFO (normal)
  6. Persiste historico em .delta-11/memoria/brief-tamanhos.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
HISTORICO_FILE = Path(".delta-11/memoria/brief-tamanhos.json")

ATIVACOES_RE = re.compile(
    r"(?:^|[\\/])\.delta-11[\\/]ativacoes[\\/].+\.txt$"
)


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str, severidade: str = "INFO") -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(
                f"- [{timestamp_utc()}] [{severidade}] [brief-preservado] {mensagem}\n"
            )
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


def is_ativacao_file(event: dict) -> str | None:
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if ATIVACOES_RE.search(file_path) and file_path.endswith(".txt"):
        return file_path
    return None


def get_new_content_size(event: dict) -> int:
    tool_input = event.get("tool_input") or {}
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    return len(content)


def load_historico() -> dict:
    if not HISTORICO_FILE.exists():
        return {}
    try:
        return json.loads(HISTORICO_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_historico(historico: dict) -> None:
    try:
        HISTORICO_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORICO_FILE.write_text(
            json.dumps(historico, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass


def main() -> int:
    try:
        event = read_hook_event()
        file_path = is_ativacao_file(event)
        if not file_path:
            return 0

        new_size = get_new_content_size(event)
        historico = load_historico()
        old_size = historico.get(file_path)

        if old_size is None:
            # Primeira vez vendo este arquivo: registra
            log_activity(
                f"INFO: brief criado/atualizado: {file_path} ({new_size} chars)"
            )
        elif new_size < old_size * 0.5:
            # Tamanho caiu mais de 50%: alerta!
            reducao_pct = (1 - new_size / old_size) * 100 if old_size else 0
            log_activity(
                f"ALERTA: brief sobrescrito com reducao de {reducao_pct:.0f}% "
                f"({old_size} -> {new_size} chars): {file_path}",
                severidade="ALERTA",
            )
        elif new_size < old_size:
            reducao_pct = (1 - new_size / old_size) * 100 if old_size else 0
            log_activity(
                f"INFO: brief atualizado com reducao de {reducao_pct:.0f}% "
                f"({old_size} -> {new_size} chars): {file_path}"
            )
        else:
            log_activity(
                f"INFO: brief atualizado/cresceu ({old_size} -> {new_size} chars): {file_path}"
            )

        historico[file_path] = new_size
        save_historico(historico)
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[brief-preservado] erro não-fatal: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())