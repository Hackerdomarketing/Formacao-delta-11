#!/usr/bin/env python3
"""
Vigia SessionStart "coletor de lixo" — Delta-11 v6.3 (2026-10-14). Item C-030.

O que limpa, na pasta PRINCIPAL do projeto (D25):
  1. `.delta-11/locks/*.lock` [travas de arquivo] mais velhas que `lock_horas`
     (padrao 2 h, em .config-limites.json) — MAS so se o agente dono da trava
     estiver sem pulso [sinal de vida]. A trava de uma tarefa longa com o agente
     ainda vivo FICA (C-030). Dono = linha `AGENTE:` do `meta` da trava; pulso =
     `.delta-11/ativacoes/pulso-AGENTE.json` com `epoch` (gravado pelo heartbeat.sh)
     dentro de `lock_horas`.
     Trava sem dono conhecido e sem pulso e removida. Outros itens velhos da pasta
     (ex.: `activity-log.mutex` abandonado) tambem sao removidos.
  2. `.delta-11/scratch/*` com mais de 7 dias.
  3. `.delta-11/logs/sub-agentes/*` com mais de 30 dias.

Nunca toca: kanban, memoria/, planos/, ativacoes/, codigo do projeto.
Ignora `.gitkeep` e `README.md`. Nao escreve nada no stdout (no SessionStart o
stdout vira contexto do agente).

Sempre sai com 0 (limpeza nunca bloqueia). Erro interno: registra ERRO-INTERNO no
activity-log e avisa no stderr (exit 1, nao bloqueia) — ver _comum.run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "gc-locks"
IDADE_MAX_SCRATCH = 7 * 24 * 3600
IDADE_MAX_LOG = 30 * 24 * 3600
PROTEGIDOS = {".gitkeep", "README.md"}
AGENTE_META_RE = re.compile(r"^AGENTE:\s*(\S+)", re.MULTILINE)


def remove(item: Path, pasta_permitida: Path) -> None:
    """Remove `item` somente se ele estiver DENTRO de `pasta_permitida`."""
    real = Path(os.path.realpath(str(item)))
    base = Path(os.path.realpath(str(pasta_permitida)))
    if real == base or not comum.is_inside(real, base):
        return
    if item.is_dir() and not item.is_symlink():
        shutil.rmtree(item, ignore_errors=True)
    else:
        item.unlink(missing_ok=True)


def lock_owner(trava: Path) -> str | None:
    meta = trava / "meta" if trava.is_dir() else trava
    achado = AGENTE_META_RE.search(comum.read_text(meta))
    return achado.group(1).upper() if achado else None


def owner_alive(agente: str | None, limite: float) -> bool:
    """O dono tem pulso recente? Usa o campo `epoch` do pulso (heartbeat.sh);
    sem ele, a data do arquivo."""
    if not agente:
        return False
    pulso = comum.delta_dir() / "ativacoes" / f"pulso-{agente}.json"
    agora = comum.now_utc().timestamp()
    try:
        dados = json.loads(pulso.read_text(encoding="utf-8"))
        epoch = dados.get("epoch") if isinstance(dados, dict) else None
        if isinstance(epoch, (int, float)) and not isinstance(epoch, bool):
            return (agora - float(epoch)) <= limite
    except (OSError, ValueError):
        pass
    try:
        return (agora - pulso.stat().st_mtime) <= limite
    except OSError:
        return False


def clean_locks() -> int:
    pasta = comum.delta_dir() / "locks"
    if not pasta.is_dir():
        return 0
    limite = float(comum.limits()["lock_horas"]) * 3600
    agora = comum.now_utc().timestamp()
    removidos = 0
    for trava in pasta.iterdir():
        if trava.name in PROTEGIDOS:
            continue
        try:
            idade = agora - trava.stat().st_mtime
        except OSError:
            continue
        if idade <= limite:
            continue
        if not trava.name.endswith(".lock"):
            # ex.: activity-log.mutex abandonado por um processo que morreu
            remove(trava, pasta)
            removidos += 1
            comum.log(HOOK, f"trava auxiliar abandonada removida (idade {idade / 3600:.1f} h): {trava.name}", "SISTEMA")
            continue
        dono = lock_owner(trava)
        if owner_alive(dono, limite):
            comum.log(HOOK, f"trava mantida (dono {dono} com pulso, idade {idade / 3600:.1f} h): {trava.name}", "SISTEMA")
            continue
        remove(trava, pasta)
        removidos += 1
        comum.log(HOOK, f"trava orfa removida (dono {dono or '?'} sem pulso, idade {idade / 3600:.1f} h): {trava.name}", "SISTEMA")
    return removidos


def clean_folder(pasta: Path, idade_max: float, rotulo: str) -> int:
    if not pasta.is_dir():
        return 0
    agora = comum.now_utc().timestamp()
    removidos = 0
    for item in pasta.iterdir():
        if item.name in PROTEGIDOS:
            continue
        try:
            idade = agora - item.stat().st_mtime
        except OSError:
            continue
        if idade > idade_max:
            remove(item, pasta)
            removidos += 1
            comum.log(HOOK, f"{rotulo} removido (idade {idade / 86400:.1f} dias): {item.name}", "SISTEMA")
    return removidos


def main() -> int:
    comum.read_event()
    delta = comum.delta_dir()
    if not delta.is_dir():
        return 0
    total = clean_locks()
    total += clean_folder(delta / "scratch", IDADE_MAX_SCRATCH, "scratch expirado")
    total += clean_folder(delta / "logs" / "sub-agentes", IDADE_MAX_LOG, "log antigo")
    if total:
        comum.log(HOOK, f"limpeza de sessao concluida: {total} item(ns) removido(s)", "SISTEMA")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
