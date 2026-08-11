#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA Edits com URLs mal-formadas.

Materializa o Furo 10 da auditoria 2026-08-11 (D-scan completo):
'URLs erradas no brief de retomada'. Agente escreve URL com
espaco, sem TLD, ou com protocolo invalido, e humano cola no
Claude Code. Hook previne que URL mal-formada entre no sistema.

ALVO: Edits em qualquer arquivo (Brief, kanban, project-core, etc).

LOGICA:
  1. Extrai URLs do conteudo (regex https?://...)
  2. Para cada URL, valida formato:
     - Tem TLD (parte final apos ultimo ponto)
     - Nao tem espacos
     - Nao tem caracteres invalidos
  3. Se alguma URL invalida: BLOQUEIA (exit 2)
  4. Caso contrario: PASSA (exit 0)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")

URL_RE = re.compile(r"https?://[^\s)]+", re.IGNORECASE)
# TLD: parte apos ultimo ponto deve ter 2+ chars alfanumericos
TLD_RE = re.compile(r"\.[a-zA-Z]{2,}(?:[/:?#]|$)")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [urls-validas] {mensagem}\n")
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


def get_combined_content(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    return (
        tool_input.get("new_string", "")
        + "\n"
        + tool_input.get("content", "")
    )


def extract_urls(content: str) -> list[str]:
    return URL_RE.findall(content)


def is_valid_url(url: str) -> tuple[bool, str]:
    """Valida URL. Retorna (valida, motivo_se_invalida)."""
    # TLD check
    if not TLD_RE.search(url):
        return False, f"sem TLD valido (ultimo segmento sem extensao): {url}"

    # Caracteres invalidos
    chars_invalidos = set(' \t\n"\'<>{}|\\^`')
    invalidos_encontrados = [c for c in url if c in chars_invalidos]
    if invalidos_encontrados:
        return False, f"caracteres invalidos {invalidos_encontrados}: {url}"

    return True, ""


def block_invalid_urls(invalid_urls: list[tuple[str, str]], file_path: str) -> int:
    msg = (
        f"[urls-validas] BLOQUEIO v6.2.0 — URL(s) mal-formada(s) detectada(s)\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"URLs invalidas:\n"
    )
    for url, motivo in invalid_urls:
        msg += f"  - {url}\n    Motivo: {motivo}\n"
    msg += (
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que o brief\n"
        f"de retomada continha URLs com espacos e formato invalido,\n"
        f"quebravam ao serem coladas em Claude Code ou navegador.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. Corrija as URLs acima (remova espacos, adicione TLD,\n"
        f"     use apenas https:// ou http://)\n"
        f"  2. URLs validas tem formato: https://dominio.com/caminho\n"
        f"  3. Repita o edit. Hook passara quando todas URLs forem validas.\n"
        f"\n"
        f"Referencia: Furo 10 da auditoria 2026-08-11 (D-scan completo).\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        event = read_hook_event()
        file_path = (
            (event.get("tool_input") or {}).get("file_path", "")
            or "<desconhecido>"
        )
        combined = get_combined_content(event)

        urls = extract_urls(combined)
        if not urls:
            return 0

        invalid = []
        for url in urls:
            valid, motivo = is_valid_url(url)
            if not valid:
                invalid.append((url, motivo))

        if invalid:
            log_activity(
                f"BLOQUEIO: {len(invalid)} URL(s) invalida(s) em {file_path}"
            )
            sys.exit(block_invalid_urls(invalid, file_path))

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[urls-validas] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[urls-validas] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)