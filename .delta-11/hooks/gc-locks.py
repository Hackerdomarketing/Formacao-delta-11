#!/usr/bin/env python3
"""
Hook SessionStart do Delta-11 v5.2: coletor de lixo (garbage collector) de sessão.

Implementa a regra que JÁ EXISTIA em prosa no protocolo de comunicação
("Locks com mais de 2 horas são removidos automaticamente") mas nunca tinha
execução técnica — achado empírico: locks de 45 dias pendurados em projeto real,
porque o hook Stop não roda quando a sessão morre bruta.

O QUE LIMPA (idade pelo mtime):
  1. .delta-11/locks/*.lock         com mais de 2 horas   → remove (dir ou arquivo)
  2. .delta-11/scratch/*            com mais de 7 dias    → remove (M-14)
  3. .delta-11/logs/sub-agentes/*   com mais de 30 dias   → remove (M-12)

NUNCA TOCA: kanban, memoria/, planos/, ativacoes/, .contract-backup/ (rotação de
backups é responsabilidade do regenerar-contratos.py — M-16), código do projeto.

Sempre exit 0 — GC nunca bloqueia nada. Só remove e loga no activity-log.
"""

from __future__ import annotations

import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

LOCKS_DIR = Path(".delta-11/locks")
SCRATCH_DIR = Path(".delta-11/scratch")
LOGS_DIR = Path(".delta-11/logs/sub-agentes")
ACTIVITY_LOG = Path(".delta-11/activity-log.md")

IDADE_MAX_LOCK_SEGUNDOS = 2 * 60 * 60          # 2 horas (regra já documentada)
IDADE_MAX_SCRATCH_SEGUNDOS = 7 * 24 * 60 * 60  # 7 dias
IDADE_MAX_LOG_SEGUNDOS = 30 * 24 * 60 * 60     # 30 dias


def log_activity(mensagem: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"- [{ts}] [gc-locks] {mensagem}\n")
    except OSError:
        pass


def remover(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def limpar_pasta(pasta: Path, idade_max: float, rotulo: str) -> int:
    if not pasta.exists():
        return 0
    agora = time.time()
    removidos = 0
    for item in pasta.iterdir():
        if item.name in {".gitkeep", "README.md"}:
            continue
        try:
            idade = agora - item.stat().st_mtime
        except OSError:
            continue
        if idade > idade_max:
            remover(item)
            removidos += 1
            log_activity(f"{rotulo} removido (idade {idade/3600:.1f}h): {item.name}")
    return removidos


def main() -> int:
    total = 0
    total += limpar_pasta(LOCKS_DIR, IDADE_MAX_LOCK_SEGUNDOS, "lock orfao")
    total += limpar_pasta(SCRATCH_DIR, IDADE_MAX_SCRATCH_SEGUNDOS, "scratch expirado")
    total += limpar_pasta(LOGS_DIR, IDADE_MAX_LOG_SEGUNDOS, "log antigo")
    if total:
        log_activity(f"GC de sessao concluido: {total} item(ns) removido(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        try:
            log_activity(f"ERRO nao-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        sys.exit(0)  # GC nunca bloqueia
