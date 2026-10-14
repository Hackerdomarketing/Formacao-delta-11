#!/usr/bin/env python3
"""
Vigia "brief preservado" — Delta-11 v6.3 (2026-10-14). Itens C-003, C-021.

Registrado em PostToolUse (DEPOIS da ferramenta rodar). Nunca bloqueia: so
registra ALERTA no activity-log para o comandante ver no painel.

O que vigia: os briefs [instrucoes de trabalho] em `.delta-11/ativacoes/*.txt` da
pasta principal. Arquivos de sinal nao sao briefs e ficam de fora: ack-*,
pulso-*, morte-*, contrato-alterado-*, contratos-desatualizados*, impacto-*,
janela-* e arquivos ocultos.

Como mede (C-021):
  - Depois de Edit/Write, le o TAMANHO REAL do arquivo ja salvo no disco (nao o
    trecho do Edit). Se o evento chegar como PreToolUse, simula o resultado final.
  - Se o tamanho cair mais de 50 % em relacao ao ultimo visto: ALERTA.
  - Depois de qualquer Bash, confere se algum brief conhecido SUMIU (ex.: `rm`):
    ALERTA de exclusao.
  - Historico: `.delta-11/memoria/brief-tamanhos.json` (chave = caminho dentro da
    .delta-11, igual na pasta principal e nas worktrees).

Erro interno: registra ERRO-INTERNO no activity-log e avisa no stderr (exit 1);
nunca bloqueia — ver _comum.run.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "brief-preservado"
PREFIXOS_DE_SINAL = (
    "ack-", "pulso-", "morte-", "contrato-alterado-", "contratos-desatualizados",
    "impacto-", "janela-", ".",
)
ATIVACAO_RE = re.compile(r"(?:^|/)\.delta-11/ativacoes/([^/]+\.txt)$")


def brief_name(caminho: Path | None) -> str | None:
    if caminho is None:
        return None
    achado = ATIVACAO_RE.search(str(caminho).replace("\\", "/"))
    if not achado:
        return None
    nome = achado.group(1)
    if nome.startswith(PREFIXOS_DE_SINAL):
        return None
    return nome


def history_file() -> Path:
    return comum.delta_dir() / "memoria" / "brief-tamanhos.json"


def load_history() -> dict:
    try:
        dados = json.loads(history_file().read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def save_history(historico: dict) -> None:
    arquivo = history_file()
    if not arquivo.parent.is_dir():
        return
    temporario = arquivo.with_name(f"{arquivo.name}.{os.getpid()}.tmp")
    temporario.write_text(json.dumps(historico, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(str(temporario), str(arquivo))


def check_deleted(historico: dict) -> bool:
    mudou = False
    pasta = comum.delta_dir() / "ativacoes"
    for nome in list(historico):
        if not (pasta / nome).exists():
            comum.log(HOOK, f"ALERTA: brief APAGADO (tinha {historico[nome]} caracteres): ativacoes/{nome}")
            del historico[nome]
            mudou = True
    return mudou


def main() -> int:
    evento = comum.read_event()
    ferramenta = evento.get("tool_name", "")
    historico = load_history()

    if ferramenta == "Bash":
        if historico and check_deleted(historico):
            save_history(historico)
        return 0
    if ferramenta not in {"Edit", "Write", "MultiEdit"}:
        return 0

    alvo = comum.absolute_target(evento)
    nome = brief_name(alvo)
    if not nome:
        return 0

    if evento.get("hook_event_name") == "PreToolUse":
        _antes, depois = comum.before_and_after(evento)
        novo = len(depois)
    else:
        novo = len(comum.read_text(alvo))

    antigo = historico.get(nome)
    if antigo is None:
        comum.log(HOOK, f"INFO: brief registrado: ativacoes/{nome} ({novo} caracteres)")
    elif antigo and novo < antigo * 0.5:
        queda = (1 - novo / antigo) * 100
        comum.log(
            HOOK,
            f"ALERTA: brief encolheu {queda:.0f}% ({antigo} -> {novo} caracteres): ativacoes/{nome}",
        )
    historico[nome] = novo
    save_history(historico)
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
