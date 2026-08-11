#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.2: BLOQUEIA Edits com keyword de
deploy se topologia do projeto nao esta' declarada.

Materializa o Furo 9 da auditoria 2026-08-11 (D-scan completo):
'Deploy assumido monolitico (worker ok, painel 404)'. Hooks
existentes (validar-deploy.py) rodam tests, mas nao conhecem
a topologia do projeto (worker + pages, ou API + admin, etc).
Quando agente faz deploy assumindo arquitetura, pode subir so
parte do sistema.

ALVO: Edits/Write com keywords de deploy.

LOGICA:
  1. Detecta keyword no conteudo: "deploy", "subir para producao",
     "publicar em producao", "wrangler deploy", etc.
  2. Verifica existencia de .delta-11/memoria/topologia.json
  3. Se nao existe OU esta' vazio: BLOQUEIA
  4. Se existe e declara pelo menos worker_url + pages_url: PASSA
  5. SENAO: BLOQUEIA com instrucao de criar topologia.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
TOPOLOGIA_FILE = Path(".delta-11/memoria/topologia.json")

# Keywords de deploy
DEPLOY_KEYWORDS_RE = re.compile(
    r"\b(deploy|subir para produ[cç][ãa]o|publicar em produ[cç][ãa]o|"
    r"wrangler deploy|vercel deploy|netlify deploy|ship to prod)\b",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [topologia-deploy] {mensagem}\n")
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
        + "\n"
        + tool_input.get("command", "")
    )


def has_deploy_keyword(content: str) -> bool:
    return bool(DEPLOY_KEYWORDS_RE.search(content))


def topologia_valida() -> bool:
    if not TOPOLOGIA_FILE.exists():
        return False
    try:
        data = json.loads(TOPOLOGIA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    # Precisa ter pelo menos worker_url + pages_url (ou api_url + admin_url)
    has_worker = "worker_url" in data or "api_url" in data
    has_pages = "pages_url" in data or "admin_url" in data
    return has_worker and has_pages


def block_no_topologia(file_path: str) -> int:
    msg = (
        f"[topologia-deploy] BLOQUEIO v6.2.0 — topologia nao declarada\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que deploy\n"
        f"assumiu arquitetura monolitica: 'worker ok, painel 404'.\n"
        f"Agente fez deploy achando que era 1 sistema, mas era worker\n"
        f"+ pages separados. Hooks existentes (validar-deploy.py) rodam\n"
        f"tests, mas nao conhecem a topologia do projeto.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. Crie .delta-11/memoria/topologia.json com a estrutura\n"
        f"     real do seu projeto:\n"
        f"\n"
        f'     {{\n'
        f'       "worker_url": "https://api.seu-projeto.com",\n'
        f'       "pages_url": "https://admin.seu-projeto.com",\n'
        f'       "tipo": "worker + pages",\n'
        f'       "deploy_cmd_worker": "wrangler deploy",\n'
        f'       "deploy_cmd_pages": "wrangler pages deploy"\n'
        f"     }}\n"
        f"\n"
        f"     Ou para outros tipos:\n"
        f'     {{"api_url": "...", "admin_url": "..."}}\n'
        f"\n"
        f"  2. Salve o arquivo.\n"
        f"  3. Repita o deploy. Hook passara quando topologia estiver\n"
        f"     declarada.\n"
        f"\n"
        f"Referencia: Furo 9 da auditoria 2026-08-11 (D-scan completo).\n"
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

        if not has_deploy_keyword(combined):
            return 0

        if topologia_valida():
            log_activity(f"OK: deploy com topologia declarada em {file_path}")
            return 0

        log_activity(
            f"BLOQUEIO: deploy em {file_path} sem topologia.json"
        )
        sys.exit(block_no_topologia(file_path))

    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[topologia-deploy] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[topologia-deploy] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)