#!/usr/bin/env python3
"""
Hook SessionStart do Delta-11 v6.2: BLOQUEIA nova execucao de
agente se SHIELD review falhou 3 vezes nas ultimas 4h.

Materializa o Furo 6 da auditoria 2026-08-11 (D-scan completo):
'3 tentativas SHIELD Onda D morreram sem autocrítica'. Quando
SHIELD review falha 3x, o sistema deve parar e pedir intervencao
humana, nao continuar indefinidamente.

ALVO: SessionStart. Roda quando Claude Code inicia sessao.

LOGICA:
  1. Le .delta-11/logs/sub-agentes/shield-falhas.log
  2. Filtra ultimas 4h
  3. Conta falhas por agente
  4. Se algum agente >= 3 falhas: BLOQUEIA
  5. SENAO: PASSA (exit 0)

EXIT CODES:
  0 = pode prosseguir (sem 3+ falhas SHIELD)
  2 = BLOQUEAR (3+ falhas SHIELD para um agente)
  1 = erro interno
"""

from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
SHIELD_FALHAS_LOG = Path(".delta-11/logs/sub-agentes/shield-falhas.log")

# Janela: 4 horas
JANELA_SEGUNDOS = 4 * 60 * 60
LIMITE_FALHAS = 3

# Regex: "- [TIMESTAMP] [SHIELD] [AGENTE] FAIL"
LINHA_FALHA_RE = re.compile(
    r"\[([A-Z_-]+)\].*FAIL",
    re.IGNORECASE,
)


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [3-tentativas-shield] {mensagem}\n")
    except OSError:
        pass


def count_shield_failures() -> dict[str, int]:
    """
    Le shield-falhas.log e retorna dict {agente: count} de falhas
    nas ultimas 4h. Suporta formato com timestamp ISO no inicio
    de cada linha.
    """
    if not SHIELD_FALHAS_LOG.exists():
        return {}

    try:
        conteudo = SHIELD_FALHAS_LOG.read_text(encoding="utf-8")
    except OSError:
        return {}

    agora = time.time()
    falhas = defaultdict(int)

    for line in conteudo.splitlines():
        match = LINHA_FALHA_RE.search(line)
        if not match:
            continue
        agente = match.group(1)
        # Tenta extrair timestamp da linha (formato ISO)
        ts_match = re.search(r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]", line)
        if ts_match:
            try:
                ts = datetime.fromisoformat(ts_match.group(1).replace("Z", "+00:00")).timestamp()
                if agora - ts > JANELA_SEGUNDOS:
                    continue
            except ValueError:
                pass
        falhas[agente] += 1

    return dict(falhas)


def block_3_failures(agente: str, count: int) -> int:
    msg = (
        f"[3-tentativas-shield] BLOQUEIO v6.2.0 — SHIELD review falhou {count}x nas ultimas 4h\n"
        f"\n"
        f"Agente: {agente}\n"
        f"\n"
        f"Por que isso e' importante:\n"
        f"A auditoria de 2026-08-11 (D-scan) documentou que '3 tentativas\n"
        f"SHIELD Onda D morreram sem autocrítica'. SHIELD tentou revisar\n"
        f"BACK/ENGINE/VAULT 3 vezes, todas falharam, e o sistema\n"
        f"continuou tentando indefinidamente. Em vez disso, deveria\n"
        f"PARAR e escalar ao comandante.\n"
        f"\n"
        f"Acao requerida (v6.2+):\n"
        f"  1. Abra o shield-falhas.log para entender o motivo:\n"
        f"     cat .delta-11/logs/sub-agentes/shield-falhas.log\n"
        f"\n"
        f"  2. Intervencao manual necessaria: corrija o problema\n"
        f"     (talvez seja bug do agente, talvez seja mudanca\n"
        f"     estrutural, talvez seja falso positivo do SHIELD).\n"
        f"\n"
        f"  3. Limpe o log de falhas (ou renomeie para .log.old):\n"
        f"     mv .delta-11/logs/sub-agentes/shield-falhas.log \\\n"
        f"        .delta-11/logs/sub-agentes/shield-falhas.log.YYYYMMDD\n"
        f"\n"
        f"  4. Reinicie a sessao. Hook passara com shield-falhas.log\n"
        f"     vazio ou com menos de 3 falhas em 4h.\n"
        f"\n"
        f"Referencia: Furo 6 da auditoria 2026-08-11 (D-scan completo).\n"
    )
    print(msg, file=sys.stderr)
    return 2


def main() -> int:
    try:
        falhas = count_shield_failures()
        for agente, count in falhas.items():
            if count >= LIMITE_FALHAS:
                log_activity(
                    f"BLOQUEIO: {agente} tem {count} falhas SHIELD em 4h"
                )
                sys.exit(block_3_failures(agente, count))

        log_activity(
            f"OK: nenhum agente com {LIMITE_FALHAS}+ falhas SHIELD em 4h"
        )
        return 0

    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[3-tentativas-shield] erro não-fatal: {exc}", file=sys.stderr)
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
        print(f"[3-tentativas-shield] erro fatal: {exc}", file=sys.stderr)
        sys.exit(0)