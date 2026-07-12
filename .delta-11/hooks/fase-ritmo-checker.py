#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: bloqueia conclusão da Fase 3.5
(Ritmo Temporal) sem os 10 artefatos do Dia 4 em .delta-11/memoria/decisoes/.

Materializa o Princípio de Selagem (Princípio 2 da Metodologia Gênesis
aplicado ao Dia 4): "Cada camada precisa ser selada antes da próxima
começar. Selado = capacidade estrutural completa."

Para o Dia 4, "selar" significa: os 10 artefatos estão documentados em
arquivos com nome padrao `ritmo-temporal-NN-*.md` na pasta .delta-11/memoria/decisoes/.

ALVO: edicoes em .delta-11/kanban.md que tentam marcar tarefas da
Fase 3.5 como CONCLUIDAS sem os 10 artefatos presentes.

LOGICA:
  1. Detecta se Edit atinge .delta-11/kanban.md
  2. Detecta se há tarefa da Fase 3.5 (tag [3.5] ou [RITMO]) sendo concluída
  3. Se NAO for Fase 3.5 → exit 0 (deixa passar)
  4. Se for Fase 3.5 → verifica quantos arquivos ritmo-temporal-* existem em memoria/decisoes/
  5. Se houver < 10 artefatos → BLOQUEIA (exit 2) com mensagem listando os 10
  6. Se houver 10+ artefatos → exit 0 (passa)

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention)
  1 = erro interno (nao bloqueia)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
Inspirado em validar-contratos-fim-fase.py e validar-arquitetura-vs-modelos.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
DECISOES_DIR = Path(".delta-11/memoria/decisoes")

# Regex para detectar conclusao
CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅",
    re.IGNORECASE,
)

# Regex para tag de Fase 3.5 (pode ser [3.5] ou [RITMO])
FASE_3_5_RE = re.compile(
    r"\[3\.5\]|\[RITMO\]|ritmo\s+temporal",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [fase-ritmo-checker] {message}\n")
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


def is_fase_3_5(content: str) -> bool:
    return bool(FASE_3_5_RE.search(content))


def count_ritmo_artifacts(base_dir: str | None = None) -> tuple[int, list[str]]:
    """
    Conta quantos artefatos de ritmo temporal existem em memoria/decisoes.
    Procura por arquivos com nome contendo 'ritmo-temporal' no nome.
    Retorna (count, lista_de_nomes).
    """
    search_dir = DECISOES_DIR
    if base_dir:
        search_dir = Path(base_dir) / ".delta-11/memoria/decisoes"

    if not search_dir.exists():
        return (0, [])

    artifact_names = []
    for f in search_dir.iterdir():
        if f.is_file() and "ritmo-temporal" in f.name.lower():
            artifact_names.append(f.name)

    return (len(artifact_names), sorted(artifact_names))


def block_edit(file_path: str, count: int, missing: list[str]) -> int:
    msg = (
        f"[fase-ritmo-checker] BLOQUEIO v6.0.0 — Princípio de Selagem do Dia 4\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"A tarefa da Fase 3.5 (Ritmo Temporal) está sendo marcada como CONCLUÍDA,\n"
        f"mas só {count} de 10 artefatos do Dia 4 estão presentes em\n"
        f".delta-11/memoria/decisoes/.\n"
        f"\n"
        f"Sem os 10 artefatos, o Dia 4 NÃO está selado. A Metodologia Gênesis é\n"
        f"explícita: 'Astros para governar o tempo não foram feitos antes de\n"
        f"existir dia e noite.' Construir código de funcionalidade sem ritmo\n"
        f"temporal é 'fazer os peixes antes de haver águas'.\n"
        f"\n"
        f"Os 10 artefatos do Dia 4 que devem existir:\n"
        f"  01. sistema-eventos\n"
        f"  02. filas (escolha do provedor)\n"
        f"  03. jobs-agendados\n"
        f"  04. cache-ttl\n"
        f"  05. timeouts\n"
        f"  06. retries (with backoff)\n"
        f"  07. circuit-breakers\n"
        f"  08. ci-cd-staging\n"
        f"  09. observabilidade\n"
        f"  10. sub-contraposicao (dominantes vs testemunhas)\n"
        f"\n"
    )
    if missing:
        msg += f"Faltam {len(missing)} artefatos. Crie cada um usando o template\n"
        msg += f".delta-11/templates/fase-ritmo-template.md e salve em\n"
        msg += f".delta-11/memoria/decisoes/AAAA-MM-DD-ritmo-temporal-<NN>-<slug>.md\n"
    else:
        msg += "Artefatos encontrados:\n"
        msg += "\n".join(f"  - {name}" for name in missing[:10]) + "\n"

    msg += (
        f"\n"
        f"Referência conceitual: .delta-11/conhecimento/metodologia-genesis-camadas.md\n"
        f"  → Dia 4 (Os Astros)\n"
        f"Protocolo formal: .delta-11/protocolos/fase-ritmo.md\n"
        f"Template: .delta-11/templates/fase-ritmo-template.md\n"
        f"\n"
        f"AÇÃO REQUERIDA:\n"
        f"  1. Crie os 10 artefatos usando o template\n"
        f"  2. Salve cada um em .delta-11/memoria/decisoes/ com nome padrao\n"
        f"  3. Repita a edição que tentou marcar Fase 3.5 como concluída\n"
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

        if not is_fase_3_5(combined):
            return 0

        # Eh conclusao de tarefa da Fase 3.5 → checa artefatos
        # Determina o diretorio base a partir do file_path do kanban
        # (caso hook esteja rodando em outro diretorio)
        base_dir = None
        tool_input = event.get("tool_input") or {}
        file_path_str = tool_input.get("file_path", "")
        if file_path_str:
            # Extrai base (pai de .delta-11/kanban.md)
            # Path is like /Users/foo/projeto/.delta-11/kanban.md
            parts = file_path_str.replace("\\", "/").split("/.delta-11/")
            if len(parts) >= 2:
                base_dir = parts[0]

        count, names = count_ritmo_artifacts(base_dir)

        if count >= 10:
            log_activity(
                f"Fase 3.5 com {count} artefatos >= 10 — conclusao permitida"
            )
            return 0

        log_activity(
            f"Fase 3.5 com {count} de 10 artefatos — conclusao BLOQUEADA"
        )
        return block_edit(
            file_path,
            count=count,
            missing=names,
        )

    except Exception as exc:  # noqa: BLE001
        print(
            f"[fase-ritmo-checker] erro não-fatal: {exc}",
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
            f"[fase-ritmo-checker] erro fatal: {exc}",
            file=sys.stderr,
        )
        sys.exit(0)