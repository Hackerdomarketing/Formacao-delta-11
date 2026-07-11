#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: força validação retroativa do Dia 2
(Container) antes de permitir conclusão da Fase 3 (Fundação).

Materializa a Verificação Retroativa da Metodologia Gênesis:
"Quando o dia três se completa com schema, modelos e contratos
materializados, o time precisa parar e fazer uma pergunta específica:
a arquitetura macro escolhida no dia dois sustenta os modelos concretos
que emergiram no dia três? Se sim, o dia dois é retroativamente
declarado 'bom'. Se não, o dia dois precisa ser refeito antes do dia
três continuar."

ANTES do v6.0: nada no sistema forçava essa pergunta. O DIA 2 recebia
"selo" sozinho sem validação. Resultado: arquitetura rachada só era
descoberta muito depois (custo 10x).

LOGICA:
  1. Detecta se Edit atinge .delta-11/kanban.md
  2. Detecta se o novo conteudo tem marcador de conclusao (CONCLUIDO/✅/CONCLUÍDO)
  3. Detecta se a conclusao e de tarefa da FASE 3 (VAULT / Banco / Fundação)
  4. Se for conclusao de tarefa Fase 3:
     - Busca no kanban.md se ja existe tarefa CONCLUIDA com texto
       "Validação Retroativa Dia 2 ← Dia 3" + resposta SUSTENTA
     - Se NAO existe → BLOQUEIA (exit 2)
     - Se existe SUSTENTA → passa (exit 0)
     - Se existe REFAZER → BLOQUEIA (exit 2) ate Dia 2 ser refeito

ALVO: edicoes em .delta-11/kanban.md

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention do Claude Code)
  1 = erro interno (nao bloqueia)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
Inspirado em validar-contratos-fim-fase.py (formato, exit codes, log).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
KANBAN_FILE = Path(".delta-11/kanban.md")


# Regex para detectar conclusao
CONCLUSAO_RE = re.compile(
    r"\[x\]|CONCLU[IÍ]DO|CONCLUIDA|✅",
    re.IGNORECASE,
)

# Regex para detectar tarefa que seja da Fase 3 (Fundacao/VAULT/Banco)
# Cobre tags de agente VAULT, termos como banco, schema, RLS, migracao, etc.
FASE_3_RE = re.compile(
    r"\[VAULT\]|VAULT\s*[:|]|T-VAULT|bancos?\b|migrac|schema|RLS|autentic|Fundação|Fundacao",
    re.IGNORECASE,
)

# Regex da tarefa de validacao retroativa (titulo canonico sugerido)
RETROVALIDACAO_RE = re.compile(
    r"Valida[cç][ãa]o\s+Retroativa\s+Dia\s+2.*Dia\s+3|Retroativa\s+Dia\s+2",
    re.IGNORECASE,
)

# Regex para respostas SUSTENTA / REFAZER
SUSTENTA_RE = re.compile(
    r"\*\*SUSTENTA\*\*|\bSUSTENTA\b",
    re.IGNORECASE,
)
REFAZER_RE = re.compile(
    r"\*\*REFAZER\*\*|\*\*REFACER\*\*|\bREFAZER\b|\bREFACER\b",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    """Timestamp ISO 8601 UTC."""
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    """Log no activity-log.md (padrao dos hooks D-11)."""
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [validar-arquitetura-vs-modelos] {message}\n")
    except OSError:
        pass  # Nunca bloquear por erro de log


def read_hook_event() -> dict:
    """Le evento JSON do Claude Code via stdin."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def is_kanban_edit(event: dict) -> bool:
    """Detecta se o Edit/Write atinge .delta-11/kanban.md."""
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return (
        file_path.endswith("/.delta-11/kanban.md")
        or file_path.endswith("\\.delta-11\\kanban.md")
    )


def get_combined_content(event: dict) -> str:
    """Pega conteudo combinado (new_string + content)."""
    tool_input = event.get("tool_input") or {}
    return (
        tool_input.get("new_string", "")
        + "\n"
        + tool_input.get("content", "")
    )


def is_tarefa_fase_3(content: str) -> bool:
    """Detecta se o conteudo novo concluiu tarefa da Fase 3."""
    return bool(FASE_3_RE.search(content))


def is_conclusao_event(content: str) -> bool:
    """Detecta se o conteudo novo tem marcador de conclusao."""
    return bool(CONCLUSAO_RE.search(content))


def read_kanban_current_state(event: dict) -> str:
    """
    Le estado ATUAL do kanban.md (que o agente está prestes a modificar).
    Usado para verificar se a tarefa de retrovalidacao ja existe.
    Retorna string vazia se nao conseguir ler.
    """
    file_path = (
        (event.get("tool_input") or {}).get("file_path", "")
        or (event.get("tool_input") or {}).get("path", "")
    )
    if not file_path:
        return ""
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def retrovalidacao_status(kanban_full_content: str) -> str:
    """
    Retorna o status da tarefa de retrovalidacao:
    - "SUSTENTA": tarefa CONCLUIDA com SUSTENTA explicito
    - "REFAZER": tarefa CONCLUIDA com REFAZER explicito
    - "PENDENTE": tarefa existe mas nao concluida
    - "AUSENTE": tarefa nao existe no kanban
    """
    # Procura qualquer menção a tarefa de retrovalidacao
    if not RETROVALIDACAO_RE.search(kanban_full_content):
        return "AUSENTE"

    # Pega trecho da tarefa de retrovalidacao (ate 200 chars depois do match)
    match = RETROVALIDACAO_RE.search(kanban_full_content)
    if not match:
        return "AUSENTE"

    trecho = kanban_full_content[match.start():match.start() + 300]

    # Verifica conclusao
    is_done = CONCLUSAO_RE.search(trecho) is not None

    if not is_done:
        return "PENDENTE"

    # Verifica qual resposta
    if SUSTENTA_RE.search(trecho):
        return "SUSTENTA"
    if REFAZER_RE.search(trecho):
        return "REFAZER"

    # Concluida mas sem resposta explicita
    return "CONCLUIDA_SEM_RESPOSTA"


def block_edit(file_path: str, motivo: str, action: str = "") -> int:
    """Bloqueia a ferramenta (exit 2) com mensagem explicativa."""
    msg = (
        f"[validar-arquitetura-vs-modelos] BLOQUEIO v6.0.0 — "
        f"Verificação Retroativa do Dia 2 pelo Dia 3 (Metodologia Gênesis)\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"Motivo: {motivo}\n"
    )
    if action:
        msg += f"\n{action}\n"
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

        # Eh uma conclusao (CONCLUIDO / ✅)?
        if not is_conclusao_event(combined):
            return 0

        # A conclusao eh de tarefa da FASE 3?
        if not is_tarefa_fase_3(combined):
            return 0

        # Verifica status da retrovalidacao
        kanban_atual = read_kanban_current_state(event)
        status = retrovalidacao_status(kanban_atual)

        if status == "SUSTENTA":
            log_activity("retrovalidacao SUSTENTA registrada — conclusao Fase 3 permitida")
            return 0

        if status == "REFAZER":
            log_activity(
                "retrovalidacao REFAZER registrada — Dia 2 precisa ser refeito ANTES da Fase 3 concluir"
            )
            return block_edit(
                file_path,
                motivo="A retrovalidação do Dia 2 está marcada como REFAZER",
                action=(
                    "AÇÃO REQUERIDA:\n"
                    "  A arquitetura do Dia 2 precisa ser REFEITA antes que a Fase 3 possa\n"
                    "  ser concluída. Reative o ATLAS para revisar a arquitetura.\n"
                    "  Quando o Dia 2 for refeito, mude a resposta para **SUSTENTA**\n"
                    "  e tente novamente."
                ),
            )

        if status == "PENDENTE" or status == "AUSENTE":
            log_activity(
                "tarefa de retrovalidacao AUSENTE/PENDENTE — bloqueio de conclusao Fase 3"
            )
            return block_edit(
                file_path,
                motivo=(
                    f"Tarefa de 'Validação Retroativa Dia 2 ← Dia 3' está "
                    f"{status.upper()} no kanban"
                ),
                action=(
                    "AÇÃO REQUERIDA:\n"
                    "  1. Adicione uma tarefa no kanban com título:\n"
                    "     'T-RETRO-001 Validacao Retroativa Dia 2 ← Dia 3'\n"
                    "  2. Quando responder a pergunta 'A arquitetura do Dia 2 sustenta\n"
                    "     os modelos do Dia 3?', marque a tarefa como CONCLUÍDA com\n"
                    "     uma destas respostas:\n"
                    "       **SUSTENTA** (dia 2 aguenta — pode concluir Fase 3)\n"
                    "       **REFAZER** (dia 2 não aguenta — reative ATLAS antes)\n"
                    "  3. Só então repita a conclusao da tarefa da Fase 3.\n"
                    "\n"
                    "Referência conceitual: .delta-11/conhecimento/metodologia-genesis-camadas.md\n"
                    "  → Dia 2 (Container) e Dia 3 (Superfícies), seção 'Verificação Retroativa'."
                ),
            )

        if status == "CONCLUIDA_SEM_RESPOSTA":
            log_activity("retrovalidacao CONCLUIDA mas sem resposta SUSTENTA/REFAZER")
            return block_edit(
                file_path,
                motivo=(
                    "Tarefa de retrovalidação do Dia 2 existe e está concluída, "
                    "MAS sem resposta SUSTENTA ou REFAZER explícita"
                ),
                action=(
                    "AÇÃO REQUERIDA:\n"
                    "  Edite a tarefa de retrovalidação e adicione explicitamente\n"
                    "  **SUSTENTA** ou **REFAZER** logo após a conclusão.\n"
                    "  Sem isso, o hook não consegue distinguir os dois caminhos."
                ),
            )

        # Status inesperado — deixa passar com log
        log_activity(f"status inesperado da retrovalidacao: {status}")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(
            f"[validar-arquitetura-vs-modelos] erro não-fatal: {exc}",
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
            f"[validar-arquitetura-vs-modelos] erro fatal: {exc}",
            file=sys.stderr,
        )
        sys.exit(0)  # Nunca bloquear por erro interno