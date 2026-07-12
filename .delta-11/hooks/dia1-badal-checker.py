#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v6.0: bloqueia edicao do PRD (ou
project-core na fase inicial) sem as 8 perguntas obrigatorias do
Dia 1 da Metodologia Genesis (Luz).

Materializa a CORRECAO do achado #2 da auditoria (Dia 1 sem teste
do badal).

ALVO: edicoes em
  - .delta-11/docs/prd.md (PRD no padrao Regra 16 / template)
  - fallback: .delta-11/memoria/project-core.md secao VISÃO/PRODUTO

O QUE VERIFICA (8 perguntas obrigatorias do Dia 1):
  1. Frase interna decisoria do usuario
  2. Identidade assumida (quem o usuario se torna ao usar)
  3. Identidade fugida (quem ele foge de continuar sendo)
  4. Teste do badal (nitidez entre as duas identidades)
  5. Unico inimigo derrotado
  6. Unico trauma curado
  7. Unico lago abandonado
  8. Nova categoria de solucao estabelecida

LOGICA:
  - Detecta arquivo alvo (PRD ou project-core)
  - Avalia conteudo no formato "Write" ou aplica edit em arquivo
    existente
  - Verifica presenca de pelo menos 6 dos 8 elementos (busca por
    sinonimos)
  - BLOQUEIA (exit 2) se menos de 6 elementos encontrados
  - PASSA (exit 0) se 6+ elementos encontrados

EXIT CODES:
  0 = pode prosseguir
  2 = bloquear
  1 = erro interno (nao bloqueia)

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")

# Regex para detectar arquivos alvo: PRD canonico + project-core fallback
PRD_RE = re.compile(
    r"[\\/]docs[\\/]prd\.md$",
    re.IGNORECASE,
)
PROJECT_CORE_RE = re.compile(
    r"(?:^|[\\/])\.delta-11[\\/]memoria[\\/]project-core\.md$",
    re.IGNORECASE,
)

# Os 8 elementos — busca por sinonimos (case-insensitive, sem acento)
ELEMENTOS_DIA1 = [
    # 1. Frase decisoria
    r"\bfrase\s+decis[oó]ri[ae]\b|\bfrase\s+intern[ae]\s+decis[oó]ri[ae]\b",
    # 2. Identidade assumida
    r"\bidentidade\s+assumida\b|\bidentidade\s+que\s+(?:o\s+)?usu[áa]rio\s+assume\b",
    # 3. Identidade fugida
    r"\bidentidade\s+fugida\b|\bidentidade\s+que\s+(?:ele\s+)?foge\b",
    # 4. Teste do badal
    r"\bteste\s+(?:do\s+)?badal\b|\bnitidez\s+entre\s+as\s+(?:duas\s+)?identidades\b|\bvayavdel\b",
    # 5. Inimigo unico
    r"\binimigo\s+[úu]nico\b|\b[úu]nico\s+inimigo\b",
    # 6. Trauma unico
    r"\btrauma\s+[úu]nico\b|\b[úu]nico\s+trauma\b",
    # 7. Lago abandonado
    r"\blago\s+abandonado\b|\b[úu]nico\s+lago\b",
    # 8. Nova categoria
    r"\bnova\s+categoria\b|\bcategoria\s+de\s+solu[çc][ãa]o\b",
]

MIN_ELEMENTOS = 6  # aceita ate 2 ausentes (justificativa documentada)


def timestamp_utc() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [dia1-badal-checker] {message}\n")
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


def is_target(event: dict) -> bool:
    """Detecta se o Edit/Write atinge PRD ou project-core."""
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    return bool(PRD_RE.search(file_path) or PROJECT_CORE_RE.search(file_path))


def get_content(event: dict) -> str:
    """Pega conteudo combinado (Write: content; Edit: new_string aplicado)."""
    tool_input = event.get("tool_input") or {}
    tool_name = event.get("tool_name", "")

    if tool_name == "Write":
        return tool_input.get("content", "")

    # Edit: aplica new_string sobre arquivo atual
    file_path = tool_input.get("file_path", "")
    new_fragment = tool_input.get("new_string", "")
    old_fragment = tool_input.get("old_string", "")
    if file_path and Path(file_path).exists():
        try:
            atual = Path(file_path).read_text(encoding="utf-8")
            if old_fragment in atual:
                return atual.replace(old_fragment, new_fragment, 1)
            return atual + new_fragment
        except OSError:
            return new_fragment
    return new_fragment


def count_elementos(content: str) -> tuple[int, list[str]]:
    """Conta quantos dos 8 elementos estao presentes."""
    encontrados = []
    for regex in ELEMENTOS_DIA1:
        if re.search(regex, content, re.IGNORECASE):
            encontrados.append(regex[:40])
    return (len(encontrados), encontrados)


def block_edit(file_path: str, encontrados: list[str]) -> int:
    """Bloqueia a ferramenta com mensagem explicando o que falta."""
    elementos = [
        ("1. Frase decisoria", "Qual a frase que o usuario pronuncia ao decidir usar?"),
        ("2. Identidade assumida", "Quem o usuario se torna ao usar?"),
        ("3. Identidade fugida", "Quem ele foge de continuar sendo?"),
        ("4. Teste do badal", "As duas identidades ficam nitidas entre si (sem confusao, sem eliminacao)?"),
        ("5. Inimigo unico", "Qual o UNICO inimigo que o software derrota?"),
        ("6. Trauma unico", "Qual o UNICO trauma que o software cura?"),
        ("7. Lago abandonado", "De qual UNICO lago o usuario migra?"),
        ("8. Nova categoria de Solucao", "Que categoria nova o software estabelece no mercado?"),
    ]

    msg = (
        f"[dia1-badal-checker] BLOQUEIO v6.0.0 — Dia 1 da Metodologia Genesis (Luz)\n"
        f"\n"
        f"Arquivo: {file_path}\n"
        f"\n"
        f"O arquivo NAO tem as 8 perguntas obrigatorias do Dia 1 da Metodologia Genesis.\n"
        f"A Luz do software e' o proposito nuclear encarnado. Sem ela, o software nasce\n"
        f"sem direcao — muita funcao, pouco proposito.\n"
        f"\n"
        f"Encontrados: {len(encontrados)} de 8 elementos (minimo para passar: {MIN_ELEMENTOS}).\n"
        f"\n"
        f"As 8 perguntas obrigatorias do Dia 1 (Metodologia Genesis v1.0):\n"
        f"\n"
    )
    for label, pergunta in elementos:
        msg += f"  {label}\n"
        msg += f"    -> {pergunta}\n"
        msg += f"\n"

    msg += (
        f"Aplicacao no D-11: preencha na secao 'Visao do Produto' do project-core.md\n"
        f"ou em docs/prd.md (template .delta-11/templates/prd-documento-de-requisitos-template.md).\n"
        f"\n"
        f"Referencia conceitual: .delta-11/conhecimento/metodologia-genesis-camadas.md → Dia 1\n"
        f"Texto hebraico chave (Gênesis 1:3-5): yehi or (haja luz) — vayavdel (separar com nitidez).\n"
        f"\n"
        f"Ação requerida: responda as 8 perguntas no documento. Use o teste do badal\n"
        f"para garantir que 'identidade assumida' e 'identidade fugida' ficam nitidas\n"
        f"entre si, sem eliminar uma pela outra.\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        event = read_hook_event()

        if not is_target(event):
            return 0

        file_path = (
            (event.get("tool_input") or {}).get("file_path", "")
            or "<desconhecido>"
        )

        content = get_content(event)
        count, encontrados = count_elementos(content)

        if count >= MIN_ELEMENTOS:
            log_activity(
                f"PRD/project-core com {count} de 8 elementos do Dia 1 — OK"
            )
            return 0

        log_activity(
            f"PRD/project-core com {count} de 8 elementos — BLOQUEADO"
        )
        return block_edit(file_path, encontrados)

    except Exception as exc:  # noqa: BLE001
        print(f"[dia1-badal-checker] erro nao-fatal: {exc}", file=sys.stderr)
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
        print(f"[dia1-badal-checker] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)