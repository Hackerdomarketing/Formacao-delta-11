#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: bloqueia edição de project-core.md
se o arquivo NÃO declarar a contraposição lateral do dia.

Materializa o Princípio 3 da Metodologia Gênesis (Rafa Marks, v1.0):
"Cada camada precisa declarar sua contraposição lateral do tipo
específico correto, herdado do dia correspondente em Gênesis. Isso é
obrigatório para o Selo da camada."

ALVO: edições em `.delta-11/memoria/project-core.md`

LÓGICA:
  1. Detecta se o Edit/Write atinge project-core.md (regex no file_path)
  2. Se NÃO atinge → exit 0 (deixa passar, não é alvo)
  3. Se atinge → busca padrão de contraposição no CONTEÚDO NOVO
  4. Se padrão encontrado → exit 0 (deixa passar, contraposição declarada)
  5. Se padrão NÃO encontrado → exit 2 (bloqueia, emite mensagem)

PADRÕES DE CONTRAPOSIÇÃO ACEITOS (case-insensitive):
  - "**Contraposição**:" (formato Markdown bold preferido)
  - "Contraposição:" (sem bold)
  - "contraposicao:" (sem acento, formato ASCII)
  - "contraposição lateral" (frase genérica que cobre qualquer dia)
  - "Lateral:" (atalho usado em alguns templates)

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention do Claude Code)
  1 = erro interno (não bloqueia por default — loga e deixa passar)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
Inspirado em pre-selo.py (formato de exit codes + log + mensagem).

INVOCAÇÃO:
  Configurado em .claude/settings.json em hooks.PreToolUse com matcher
  "Edit|Write" apontando para este script. Recebe evento JSON via stdin.

LIMITES CONHECIDOS (v6.0.0):
  - Validação por presença da PALAVRA "contraposição", não por tipo correto
    por dia. A Etapa futura pode evoluir para validar TIPO 1 a TIPO 7.
  - Aceita tanto "Contraposição:" quanto "contraposição lateral". Pode
    gerar falso positivo se a palavra for usada em comentário. Risco
    aceitável para v6.0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# Caminhos canonicos
ACTIVITY_LOG = Path(".delta-11/activity-log.md")

# Padroes regex que indicam que a contraposicao lateral foi declarada.
# Case-insensitive. Aceita variacoes de Markdown bold, acento, formatos.
CONTRA_POSICAO_PATTERNS = [
    r"\*\*[Cc]ontraposi[cç][ãa]o\*\*\s*:",          # **Contraposição:**
    r"[Cc]ontraposi[cç][ãa]o\s+lateral\b",          # Contraposição lateral
    r"[Cc]ontraposi[cç][ãa]o\s*:",                  # Contraposição:
    r"\bLateral\s*:\s*[Tt]ipo\s+[1-7]",             # Lateral: Tipo N (mais rigoroso)
]

# Regex combinada para detectar qualquer um dos padroes
CONTRA_POSICAO_RE = re.compile(
    "|".join(CONTRA_POSICAO_PATTERNS),
    re.IGNORECASE | re.MULTILINE,
)

# Regex para detectar se o arquivo alvo eh o project-core.md
# Aceita path absoluto, relativo, com / ou \, com ou sem prefixo
PROJECT_CORE_RE = re.compile(
    r"(?:^|[\\/])\.delta-11[\\/]memoria[\\/]project-core\.md$",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    """Timestamp ISO 8601 UTC."""
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    """Log no activity-log.md para auditoria (mesmo padrao de pre-selo.py)."""
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [contraposicao-checker] {message}\n")
    except OSError:
        # NUNCA bloquear por erro de log
        pass


def read_hook_event() -> dict:
    """Le evento JSON do Claude Code via stdin."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def is_project_core(event: dict) -> bool:
    """
    Detecta se o Edit/Write atinge .delta-11/memoria/project-core.md.
    Retorna True se for alvo do hook, False caso contrario.
    """
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return bool(PROJECT_CORE_RE.search(file_path))


def get_new_content(event: dict) -> str:
    """
    Extrai o conteudo NOVO que o Edit/Write vai gravar.
    - Write: usa tool_input.content
    - Edit: precisa aplicar new_string + estado atual (estimativa segura)
    """
    tool_input = event.get("tool_input") or {}
    tool_name = event.get("tool_name", "")

    if tool_name == "Write":
        return tool_input.get("content", "")

    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        new_fragment = tool_input.get("new_string", "")
        old_fragment = tool_input.get("old_string", "")

        if file_path and Path(file_path).exists():
            try:
                atual = Path(file_path).read_text(encoding="utf-8")
                # Simula o resultado do edit
                if old_fragment in atual:
                    return atual.replace(old_fragment, new_fragment, 1)
                return atual + new_fragment
            except OSError:
                return new_fragment
        return new_fragment

    return ""


def has_contraposicao(content: str) -> bool:
    """Verifica se o conteudo declara contraposicao lateral."""
    if not content:
        return False
    return bool(CONTRA_POSICAO_RE.search(content))


def block_edit(file_path: str, missing_examples: list[str]) -> int:
    """
    Bloqueia a ferramenta (exit 2) e emite mensagem explicando o que falta.
    """
    examples = "\n".join(f"  - {ex}" for ex in missing_examples)
    print(
        f"[contraposicao-checker] BLOQUEIO v6.0.0 — Princípio 3 da Metodologia Gênesis\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"O project-core.md precisa DECLARAR a contraposição lateral de cada Dia.\n"
        f"Sem essa declaração, o sistema perde a rastreabilidade do Princípio 3\n"
        f"(Contraposição Lateral Obrigatória) e o Selo da camada fica incompleto.\n"
        f"\n"
        f"Adicione UMA das seguintes formas no project-core.md, dentro da seção\n"
        f"do Dia correspondente:\n"
        f"\n"
        f"{examples}\n"
        f"\n"
        f"Referência conceitual: .delta-11/conhecimento/metodologia-genesis-camadas.md\n"
        f"\n"
        f"AÇÃO REQUERIDA:\n"
        f"  1. Identifique qual Dia foi adicionado/editado no project-core.md\n"
        f"  2. Declare a contraposição lateral do tipo correto (Tipo 1 a Tipo 7)\n"
        f"  3. Repita a edição\n"
        f"\n"
        f"Princípio: Gênesis capítulo 1, cada dia termina com separação explícita\n"
        f"(luz/trevas, águas de cima/baixo, terra/mar, dia/noite, peixes/aves,\n"
        f"homem/animais, obra consumada/descanso). Sem declaração de contraposição\n"
        f"no project-core.md, o Selo do dia NÃO se completa.\n",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    try:
        event = read_hook_event()

        # NAO eh arquivo project-core → deixa passar
        if not is_project_core(event):
            return 0

        file_path = (
            (event.get("tool_input") or {}).get("file_path")
            or (event.get("tool_input") or {}).get("path")
            or "<desconhecido>"
        )

        content = get_new_content(event)

        # Verifica se ha contraposicao declarada
        if has_contraposicao(content):
            log_activity(f"project-core.md OK (contraposicao lateral declarada)")
            return 0

        # Nao declarou contraposicao → bloqueia
        log_activity(
            f"project-core.md BLOQUEADO (contraposicao lateral NAO declarada)"
        )
        return block_edit(
            file_path,
            missing_examples=[
                "**Contraposição:** existencial-identitária (identidade assumida vs fugida)  [Tipo 1, Dia 1]",
                "**Contraposição:** estrutural tripla (arquitetura, mundo externo, mundo interno)  [Tipo 2, Dia 2]",
                "**Contraposição:** substância + estrutural-reprodutiva  [Tipo 3, Dia 3]",
                "**Contraposição:** funcional-temporal + hierárquica (síncrono/assíncrono, dominante/testemunha)  [Tipo 4, Dia 4]",
                "**Contraposição:** territorial + escalar (backend/frontend, principal/secundário)  [Tipo 5, Dia 5]",
                "**Contraposição:** complementar + hierárquica (autenticação/autorização, dominadores/dominados)  [Tipo 6, Dia 6]",
                "**Contraposição:** de estado (consumado/em curso)  [Tipo 7, Dia 7]",
            ],
        )

    except Exception as exc:  # noqa: BLE001
        # Erro interno NAO bloqueia — loga e deixa passar (padrao pre-selo.py)
        print(f"[contraposicao-checker] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[contraposicao-checker] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)  # Nunca bloquear por erro interno