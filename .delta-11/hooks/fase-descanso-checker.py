#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: bloqueia conclusao da Fase 7
(Descanso Consagrado) sem os 10 entregaveis + teste supremo do Dia 7.

Materializa o Principio de Selagem (Principio 2) aplicado ao Dia 7
da Metodologia Genesis: "Cada camada precisa ser selada antes da
proxima comecar."

Para o Dia 7, "selar" significa DUAS condicoes:
1. Os 10 artefatos estao documentados em arquivos `descanso-NN-*.md`
2. Ha registro explicito do TESTE SUPREMO (operacao autonoma 2+ semanas)

ALVO: edicoes em .delta-11/kanban.md que tentam marcar tarefas da
Fase 7 como CONCLUIDAS sem ambos.

DIFERENCA das outras fases:
- Dia 4 (Ritmo): exige 10 artefatos
- Dia 6 (Consciencia): exige 5 entregaveis
- Dia 7 (Descanso): exige 10 entregaveis + TESTE SUPREMO explicito

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention)

Cross-platform. Inspirado em fase-ritmo-checker.py e fase-consciencia-checker.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
DECISOES_DIR = Path(".delta-11/memoria/decisoes")

CONCLUSAO_RE = re.compile(r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅", re.IGNORECASE)

FASE_7_RE = re.compile(
    r"\[7\]|\[DESCANSO\]|\[CONAGRAC|\bdescanso\s+consagrado",
    re.IGNORECASE,
)

TESTE_SUPREMO_RE = re.compile(
    r"\*\*TESTE SUPREMO\s+(?:PASSOU|OK|SIM)\b|opera[cç][ãa]o\s+aut[ôo]noma\s+de\s+2\s+semanas|2\s+semanas\s+sem\s+interven[cç][ãa]o",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [fase-descanso-checker] {message}\n")
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


def is_conclusao(content: str) -> bool:
    return bool(CONCLUSAO_RE.search(content))


def is_fase_7(content: str) -> bool:
    return bool(FASE_7_RE.search(content))


def count_descanso_artifacts(base_dir: str | None = None) -> tuple[int, list[str]]:
    search_dir = DECISOES_DIR
    if base_dir:
        search_dir = Path(base_dir) / ".delta-11/memoria/decisoes"
    if not search_dir.exists():
        return (0, [])
    names = []
    for f in search_dir.iterdir():
        if f.is_file() and "descanso" in f.name.lower():
            names.append(f.name)
    return (len(names), sorted(names))


def has_teste_supremo(combined_content: str, kanban_full: str) -> bool:
    """Procura registro explicito do teste supremo no kanban ou no edit."""
    corpus = combined_content + "\n" + kanban_full
    return bool(TESTE_SUPREMO_RE.search(corpus))


def block_edit(file_path: str, count: int, names: list[str], motivo: str) -> int:
    msg = (
        f"[fase-descanso-checker] BLOQUEIO v6.0.0 — Dia 7 (Descanso Consagrado)\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Motivo: {motivo}\n"
        f"\n"
        f"A tarefa da Fase 7 (Descanso Consagrado) está sendo marcada como CONCLUÍDA,\n"
        f"mas faltam condicoes. O Dia 7 exige:\n"
        f"  - Os 10 entregaveis documentados em .delta-11/memoria/decisoes/\n"
        f"  - Registro explicito do TESTE SUPREMO (2+ semanas operacao autonoma)\n"
        f"\n"
    )
    if count > 0:
        msg += f"Tem {count} artefatos descanso-* (faltam {10 - count} para os 10 obrigatorios).\n"
        msg += f"Encontrados:\n"
        msg += "\n".join(f"  - {n}" for n in names[:10]) + "\n"
    else:
        msg += "Nenhum artefato descanso-* encontrado ainda.\n"

    msg += (
        f"\n"
        f"Os 10 entregaveis do Dia 7 que devem existir:\n"
        f"  01. docs-tecnica\n"
        f"  02. docs-dominio\n"
        f"  03. e2e (testes de aceitacao)\n"
        f"  04. deploy-auto\n"
        f"  05. runbooks (especificos do projeto)\n"
        f"  06. monitoramento (dashboards + alertas)\n"
        f"  07. tag-release\n"
        f"  08. backup-testado\n"
        f"  09. dr-testado\n"
        f"  10. onboarding-testado\n"
        f"\n"
        f"ALEM DISSO: registro explicito do TESTE SUPREMO no kanban, no formato:\n"
        f"  **TESTE SUPREMO PASSOU** — 2+ semanas operacao autonoma\n"
        f"\n"
        f"Use o template .delta-11/templates/fase-descanso-template.md para\n"
        f"preencher cada um. Salve em formato:\n"
        f".delta-11/memoria/decisoes/AAAA-MM-DD-descanso-<NN>-<slug>.md\n"
        f"\n"
        f"Referencia: .delta-11/conhecimento/metodologia-genesis-camadas.md → Dia 7\n"
        f"Protocolo: .delta-11/protocolos/fase-descanso.md\n"
        f"Acao requerida: preencher os 10 + TESTE SUPREMO antes de marcar Fase 7.\n"
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

        if not is_conclusao(combined):
            return 0
        if not is_fase_7(combined):
            return 0

        # Determina base_dir
        tool_input = event.get("tool_input") or {}
        file_path_str = tool_input.get("file_path", "")
        base_dir = None
        if file_path_str:
            parts = file_path_str.replace("\\", "/").split("/.delta-11/")
            if len(parts) >= 2:
                base_dir = parts[0]

        count, names = count_descanso_artifacts(base_dir)

        # Le kanban atual (para buscar teste supremo em qualquer parte dele)
        kanban_full = ""
        if file_path_str:
            try:
                kanban_full = Path(file_path_str).read_text(encoding="utf-8")
            except OSError:
                pass

        # Condicao 1: 10 artefatos
        if count < 10:
            log_activity(
                f"Fase 7 com {count} de 10 artefatos — BLOQUEADA"
            )
            return block_edit(
                file_path, count, names,
                motivo=f"Apenas {count} de 10 artefatos do Dia 7 estao presentes",
            )

        # Condicao 2: teste supremo explicito
        if not has_teste_supremo(combined, kanban_full):
            log_activity(
                f"Fase 7 com 10 artefatos mas SEM teste supremo — BLOQUEADA"
            )
            return block_edit(
                file_path, count, names,
                motivo="10 artefatos presentes mas TESTE SUPREMO nao registrado",
            )

        log_activity(
            "Fase 7 com 10 artefatos + TESTE SUPREMO — conclusao permitida"
        )
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"[fase-descanso-checker] erro nao-fatal: {exc}", file=sys.stderr)
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
        print(f"[fase-descanso-checker] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)