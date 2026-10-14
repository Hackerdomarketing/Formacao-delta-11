#!/usr/bin/env python3
"""
Vigia PostToolUse "contratos desatualizados" — Delta-11 v6.3 (2026-10-14).
Itens C-037, C-038 e decisao D31.

O que mudou na v6.3 (D31): este vigia NAO dispara mais nenhum `claude --print`
escondido em segundo plano (custava uso, deixava processos soltos e nem tinha
permissao para gravar). Ele so AVISA:

  1. Quando o ATLAS altera o contrato — `.delta-11/memoria/project-core.md` ou
     uma fatia em `.delta-11/memoria/project-core/*.md` —, calcula o hash
     [impressao digital] do conjunto (project-core + fatias) da MESMA pasta
     .delta-11 do arquivo editado (C-037: nao usa mais caminho relativo).
  2. Se o hash mudou em relacao a `.delta-11/.contract-hash`, grava:
       - `.delta-11/ativacoes/contratos-desatualizados.txt` com o hash novo e a
         hora (o CRONOS ve o aviso, roda o contract-tester UMA vez depois que o
         ATLAS termina as edicoes, e apaga o aviso);
       - `.delta-11/ativacoes/contrato-alterado-[AGENTE].txt` para cada executor
         com ACK ativo (nome unico do aviso ao agente — C-038);
       - o hash novo em `.delta-11/.contract-hash`.
  3. O impact-mapper so roda a pedido e nunca cria tarefas no kanban sem o CRONOS
     aprovar — nada disso e feito aqui.

Nunca bloqueia (PostToolUse). Erro interno: registra ERRO-INTERNO no activity-log
e avisa no stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "regenerar-contratos"
AVISO_GERAL = "contratos-desatualizados.txt"
NAO_RECEBEM_AVISO = {"ATLAS", "CRONOS"}


def contract_files(delta: Path) -> list[Path]:
    memoria = delta / "memoria"
    arquivos = [memoria / "project-core.md"]
    fatias = memoria / "project-core"
    if fatias.is_dir():
        arquivos += sorted(fatias.glob("*.md"))
    return [a for a in arquivos if a.is_file()]


def contract_hash(delta: Path) -> str:
    soma = hashlib.sha256()
    for arquivo in contract_files(delta):
        soma.update(arquivo.relative_to(delta).as_posix().encode("utf-8") + b"\0")
        soma.update(arquivo.read_bytes() + b"\0")
    return soma.hexdigest()


def is_contract_file(caminho: Path | None) -> Path | None:
    """Devolve a pasta .delta-11 se `caminho` e o project-core ou uma fatia."""
    delta = comum.delta_dir_of_path(caminho)
    if delta is None or caminho is None:
        return None
    relativo = caminho.relative_to(delta).as_posix()
    if relativo == "memoria/project-core.md":
        return delta
    if relativo.startswith("memoria/project-core/") and relativo.endswith(".md"):
        return delta
    return None


def active_executors(delta: Path) -> list[str]:
    nomes = []
    for ack in sorted((delta / "ativacoes").glob("ack-*.txt")):
        nome = ack.stem[len("ack-"):].upper()
        if nome in comum.TODOS_OS_AGENTES and nome not in NAO_RECEBEM_AVISO:
            nomes.append(nome)
    return nomes


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0
    delta = is_contract_file(comum.absolute_target(evento))
    if delta is None:
        return 0

    novo = contract_hash(delta)
    arquivo_hash = delta / ".contract-hash"
    antigo = comum.read_text(arquivo_hash).strip()
    if novo == antigo:
        return 0

    agora = comum.timestamp_utc()
    ativacoes = delta / "ativacoes"
    ativacoes.mkdir(parents=True, exist_ok=True)
    (ativacoes / AVISO_GERAL).write_text(
        "Formação Δ-11 — contratos desatualizados (aviso automatico do vigia regenerar-contratos)\n"
        f"hash_novo: {novo}\n"
        f"hash_anterior: {antigo or '(nenhum)'}\n"
        f"alterado_em: {agora}\n"
        f"arquivo: {comum.target_path_text(evento)}\n\n"
        "CRONOS: quando o ATLAS terminar as edicoes do project-core, rode o contract-tester\n"
        "UMA vez (gera e roda os testes de contrato do que mudou) e apague este aviso.\n",
        encoding="utf-8",
    )
    avisados = active_executors(delta)
    for agente in avisados:
        (ativacoes / f"contrato-alterado-{agente}.txt").write_text(
            "Formação Δ-11 — aviso automatico\n"
            f"Agente: {agente}\n"
            f"Hora: {agora}\n\n"
            "O contrato (project-core e/ou fatias em memoria/project-core/) mudou. Antes da\n"
            "proxima tarefa, releia a SUA fatia e aguarde o CRONOS rodar o contract-tester.\n"
            "Apague este aviso depois de ler.\n",
            encoding="utf-8",
        )
    arquivo_hash.write_text(novo + "\n", encoding="utf-8")
    extra = f"; avisados: {', '.join(avisados)}" if avisados else ""
    comum.log(HOOK, f"contrato alterado: hash {antigo[:12] or '(vazio)'} -> {novo[:12]}{extra}")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
