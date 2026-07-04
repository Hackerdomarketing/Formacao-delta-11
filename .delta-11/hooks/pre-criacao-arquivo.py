#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v5.2: guarda de zoneamento documental.

Materializa as Regras Invioláveis 14 e 15 + a seção "PARA IA EXTERNA" do CLAUDE.md.
Bloqueia a CRIAÇÃO de arquivos .md em zonas vigiadas quando o padrão de nome/lugar
indica decisão de organização ruim (o "caso Kimi": docs/configuracao-kimi-moonshot.md —
config de API nomeada pelo vendor, jogada na pasta de specs).

O QUE VIGIA (apenas CRIAÇÃO — arquivo que ainda não existe; edições passam livre):
  CASO A — .md novo em docs/ com nome de config/setup de vendor
           (prefixos: configuracao-, config-, setup-, integracao-)
           → destino certo: src/lib/[dominio]/[etapa]/README.md pelo template
             config-integracao-externa-template.md (Regra 15)
  CASO B — .md novo na RAIZ do projeto (fora as exceções: CLAUDE.md, README.md,
           AGENTS.md) → raiz é só para código/config de framework (zoneamento v5.2)
  CASO C — arquivo novo em skills/ na raiz → pasta legada; canônico é
           .delta-11/conhecimento/ (decisão v5.2 — M-20)

ESCAPE DO COMANDANTE: criar .delta-11/.permitir-docs-livres desativa os 3 casos
(mesmo padrão do .permitir-edicao-main da guarda-worktree). Apagar depois de usar.

Filosofia v5: proteção técnica > instrução em prompt. Em qualquer erro interno o
hook LIBERA (exit 0) — nunca derruba o projeto por falha da própria guarda.

Exit codes: 0 = prosseguir · 2 = bloquear (PreToolUse convention)
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ARQUIVO_DE_ESCAPE = ".delta-11/.permitir-docs-livres"
ACTIVITY_LOG = Path(".delta-11/activity-log.md")

# .md permitidos na raiz do projeto
EXCECOES_RAIZ = {"CLAUDE.md", "README.md", "AGENTS.md", "GEMINI.md"}

# prefixos que denunciam config de integração externa nomeada pelo vendor
PREFIXOS_CONFIG = ("configuracao-", "config-", "setup-", "integracao-")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"- [{ts}] [pre-criacao-arquivo] {mensagem}\n")
    except OSError:
        pass


def bloquear(mensagem: str) -> None:
    print(mensagem, file=sys.stderr)
    sys.exit(2)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    if event.get("tool_name") != "Write":
        return 0  # só vigia criação via Write; Edit em arquivo existente passa

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0

    cwd = event.get("cwd") or os.getcwd()
    raiz = os.path.realpath(cwd)

    # fora de projeto Delta-11 → guarda não se aplica
    if not os.path.isdir(os.path.join(raiz, ".delta-11")):
        return 0

    # escape do comandante
    if os.path.exists(os.path.join(raiz, ARQUIVO_DE_ESCAPE)):
        return 0

    alvo = os.path.realpath(
        file_path if os.path.isabs(file_path) else os.path.join(raiz, file_path)
    )

    # arquivo já existe → é sobrescrita/edição, não criação; passa
    if os.path.exists(alvo):
        return 0

    # fora do projeto → não é assunto desta guarda
    if not alvo.startswith(raiz + os.sep):
        return 0

    rel = os.path.relpath(alvo, raiz)
    partes = rel.split(os.sep)
    nome = os.path.basename(alvo)

    # ── CASO C: criação em skills/ na raiz (pasta legada) ──
    if partes[0] == "skills":
        log_activity(f"BLOQUEADO caso C (skills/ legada): {rel}")
        bloquear(
            "GUARDA-ZONEAMENTO (CASO C — v5.2): voce tentou criar arquivo em skills/ na raiz.\n"
            "Essa pasta e LEGADA. O endereco canonico de conhecimento para agentes e:\n"
            "  .delta-11/conhecimento/\n"
            f"Arquivo tentado: {rel}\n"
            "Regra: CLAUDE.md secao 'PARA IA EXTERNA' + decisao M-20 v5.2.\n"
            f"Escape do comandante: criar {ARQUIVO_DE_ESCAPE} (e apagar depois)."
        )

    if not nome.lower().endswith(".md"):
        return 0  # abaixo, só vigiamos .md

    # ── CASO A: config de vendor em docs/ ──
    if partes[0] == "docs" and nome.lower().startswith(PREFIXOS_CONFIG):
        log_activity(f"BLOQUEADO caso A (config de vendor em docs/): {rel}")
        bloquear(
            "GUARDA-ZONEAMENTO (CASO A — o 'caso Kimi', v5.2): voce tentou criar uma\n"
            "configuracao de integracao externa dentro de docs/ com nome de vendor.\n"
            f"Arquivo tentado: {rel}\n"
            "\n"
            "docs/ e para spec de produto do comandante. Configuracao de integracao vive\n"
            "AO LADO do codigo que a consome, nomeada pela FUNCAO no produto:\n"
            "  src/lib/[dominio]/[etapa]/README.md\n"
            "  (ex: src/lib/ia/analise-competitiva/README.md — nao 'configuracao-kimi.md')\n"
            "\n"
            "Use o template: .delta-11/templates/config-integracao-externa-template.md\n"
            "Antes, atualize: .delta-11/memoria/ferramentas-do-projeto.md (Regra 14)\n"
            "Regras Inviolaveis 14 e 15 (.delta-11/protocolos/regras-inviolaveis.md).\n"
            f"Escape do comandante: criar {ARQUIVO_DE_ESCAPE} (e apagar depois)."
        )

    # ── CASO B: .md novo na raiz do projeto ──
    if len(partes) == 1 and nome not in EXCECOES_RAIZ:
        log_activity(f"BLOQUEADO caso B (.md na raiz): {rel}")
        bloquear(
            "GUARDA-ZONEAMENTO (CASO B — v5.2): voce tentou criar um .md na RAIZ do projeto.\n"
            f"Arquivo tentado: {rel}\n"
            "\n"
            "A raiz e so para codigo/config de framework + CLAUDE.md + README.md.\n"
            "Enderecos canonicos (CLAUDE.md secao 'PARA IA EXTERNA'):\n"
            "  - Spec de produto            → docs/\n"
            "  - Docs pessoais do comandante → docs/comandante/\n"
            "  - Config de integracao        → src/lib/[dominio]/[etapa]/README.md\n"
            "  - Conhecimento para agentes   → .delta-11/conhecimento/\n"
            "  - Temporarios                 → .delta-11/scratch/\n"
            f"Escape do comandante: criar {ARQUIVO_DE_ESCAPE} (e apagar depois)."
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        # falha da guarda nunca derruba o fluxo
        try:
            log_activity(f"ERRO nao-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        sys.exit(0)
