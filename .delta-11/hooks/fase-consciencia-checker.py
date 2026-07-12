#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: bloqueia conclusão da Fase 4.5
(Consciência Dominante) sem os 5 entregáveis do Dia 6.

Materializa o Princípio de Selagem (Princípio 2) aplicado ao Dia 6
da Metodologia Gênesis: "Cada camada precisa ser selada antes da
próxima começar."

Para o Dia 6, "selar" significa: os 5 entregáveis estão documentados
em arquivos com nome padrao `consciencia-NN-*.md` na pasta
.delta-11/memoria/decisoes/.

ALVO: edicoes em .delta-11/kanban.md que tentam marcar tarefas da
Fase 4.5 como CONCLUIDAS sem os 5 entregáveis presentes.

LOGICA:
  1. Detecta se Edit atinge .delta-11/kanban.md
  2. Detecta se há tarefa da Fase 4.5 (tag [4.5] ou [CONSCIÊNCIA])
     sendo concluída
  3. Se NAO for Fase 4.5 → exit 0 (deixa passar)
  4. Se for Fase 4.5 → conta quantos arquivos consciencia-* existem
     em memoria/decisoes/
  5. Se houver < 5 entregáveis → BLOQUEIA (exit 2)
  6. Se houver 5+ → exit 0 (passa)

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention)
  1 = erro interno (nao bloqueia)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
Inspirado em fase-ritmo-checker.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
DECISOES_DIR = Path(".delta-11/memoria/decisoes")

CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅",
    re.IGNORECASE,
)

FASE_4_5_RE = re.compile(
    r"\[4\.5\]|\[CONSCI[ÊE]NCIA\]|consci[êe]ncia\s+dominante",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [fase-consciencia-checker] {message}\n")
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


def is_fase_4_5(content: str) -> bool:
    return bool(FASE_4_5_RE.search(content))


def count_consciencia_artifacts(base_dir: str | None = None) -> tuple[int, list[str]]:
    """
    Conta quantos artefatos de consciencia existem em memoria/decisoes.
    Retorna (count, lista_de_nomes).
    """
    search_dir = DECISOES_DIR
    if base_dir:
        search_dir = Path(base_dir) / ".delta-11/memoria/decisoes"

    if not search_dir.exists():
        return (0, [])

    artifact_names = []
    for f in search_dir.iterdir():
        if f.is_file() and "consciencia" in f.name.lower():
            artifact_names.append(f.name)

    return (len(artifact_names), sorted(artifact_names))


def block_edit(file_path: str, count: int, names: list[str]) -> int:
    msg = (
        f"[fase-consciencia-checker] BLOQUEIO v6.0.0 — Princípio de Selagem do Dia 6\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"A tarefa da Fase 4.5 (Consciência Dominante) está sendo marcada\n"
        f"como CONCLUÍDA, mas só {count} de 5 entregáveis do Dia 6 estão\n"
        f"presentes em .delta-11/memoria/decisoes/.\n"
        f"\n"
        f"Sem os 5 entregáveis, o Dia 6 NÃO está selado. A Metodologia\n"
        f"Gênesis é explícita: este é o único dia com a expressão *tov meod*\n"
        f"(muito bom). Construir testes de integração com sistema sem\n"
        f"consciência de domínio é validar um sistema irresponsável.\n"
        f"\n"
        f"Os 5 entregáveis do Dia 6 que devem existir:\n"
        f"  01. auditoria-imutavel (audit_log append-only)\n"
        f"  02. rate-limiting (endpoints críticos)\n"
        f"  03. motor-regras (central, com testes)\n"
        f"  04. lgpd (consentimento, export, direito ao esquecimento)\n"
        f"  05. fluxos-aprovacao (state machine)\n"
        f"\n"
    )
    if names:
        msg += "Artefatos encontrados:\n"
        msg += "\n".join(f"  - {n}" for n in names[:10]) + "\n"
        msg += "\n"
    else:
        msg += "Nenhum artefato consciencia-* encontrado ainda.\n\n"

    msg += (
        f"Use o template .delta-11/templates/fase-consciencia-template.md\n"
        f"para preencher cada um. Salve em formato:\n"
        f".delta-11/memoria/decisoes/AAAA-MM-DD-consciencia-<NN>-<slug>.md\n"
        f"\n"
        f"Referência conceitual: .delta-11/conhecimento/metodologia-genesis-camadas.md\n"
        f"  → Dia 6 (A Consciência Que Domina)\n"
        f"Protocolo formal: .delta-11/protocolos/fase-consciencia.md\n"
        f"Skills globais integradas: ~/.claude/skills/supabase-rls/, ~/.claude/skills/owasp-top10/\n"
        f"\n"
        f"AÇÃO REQUERIDA:\n"
        f"  1. Crie os 5 entregáveis usando o template\n"
        f"  2. Salve cada um em .delta-11/memoria/decisoes/ com nome padrao\n"
        f"  3. SHIELD valida e sela, Comandante aprova\n"
        f"  4. Repita a edição que tentou marcar Fase 4.5 como concluída\n"
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

        if not is_fase_4_5(combined):
            return 0

        # Determina diretorio base
        tool_input = event.get("tool_input") or {}
        file_path_str = tool_input.get("file_path", "")
        base_dir = None
        if file_path_str:
            parts = file_path_str.replace("\\", "/").split("/.delta-11/")
            if len(parts) >= 2:
                base_dir = parts[0]

        count, names = count_consciencia_artifacts(base_dir)

        if count >= 5:
            log_activity(
                f"Fase 4.5 com {count} entregaveis >= 5 — conclusao permitida"
            )
            return 0

        log_activity(
            f"Fase 4.5 com {count} de 5 entregaveis — conclusao BLOQUEADA"
        )
        return block_edit(file_path, count, names)

    except Exception as exc:  # noqa: BLE001
        print(
            f"[fase-consciencia-checker] erro não-fatal: {exc}",
            file=sys.stderr,
        )
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
        print(
            f"[fase-consciencia-checker] erro fatal: {exc}",
            file=sys.stderr,
        )
        sys.exit(0)