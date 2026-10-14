#!/usr/bin/env python3
"""
Vigia "forca despacho" — Delta-11 v6.3 (2026-10-14). Itens C-015, C-029, C-036.

Furo 2 da auditoria 2026-08-11: agentes escreviam "PASS" sem rodar os
sub-agentes de validacao. Este vigia exige PROVA de que o sub-agente rodou.

Quando age (PreToolUse em Edit|Write do `.delta-11/kanban.md`):
  - So para tarefas que PASSAM a ficar concluidas nesta edicao (compara antes e
    depois — reescrever o kanban inteiro nao reconta tarefas antigas, C-036).
  - O dono da tarefa sai da propria linha: "Por: BACK", "Agente: BACK", "[BACK]"
    ou "| BACK |". Linha de tarefa (com ID T-XXX ou **[ID]**) sem dono BLOQUEIA:
    nao da mais para escapar tirando a etiqueta (C-029).
  - ATLAS e CRONOS sao isentos.

Sub-agentes obrigatorios por dono:
  BACK, ENGINE, VAULT -> build-validator E contract-tester
  FRONT, PIXEL, FORM, SCOUT -> build-validator
  SHIELD -> verify-app

Prova aceita (D32): arquivo em `.delta-11/logs/sub-agentes/` da pasta principal,
gravado pelo vigia do evento SubagentStop:
    AAAAMMDDTHHMMSSZ-[agent_type].log   (com agent_id e a ultima mensagem)
dentro da janela (`janela_horas`, padrao 4 h; vale o horario do nome do arquivo,
ou a data do arquivo se o nome nao tiver horario). Como os sub-agentes sao
disparados como `general-purpose`, o log traz tambem as linhas:
    subagente_detectado: build-validator
    agente_delta11: BACK
  - Tipo: a linha `subagente_detectado:`; sem ela, o nome do arquivo ou o
    conteudo ("build-validator", "Build Validation Report", "contract-tester").
  - Dono: a linha `agente_delta11:`; sem ela, o nome do executor em maiusculas.
    Log do tipo certo com OUTRO dono nao vale; log do tipo certo sem dono
    identificado vale (o relatorio nem sempre diz para quem rodou).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "forca-despacho"
OBRIGATORIOS = {
    "BACK": ["build-validator", "contract-tester"],
    "ENGINE": ["build-validator", "contract-tester"],
    "VAULT": ["build-validator", "contract-tester"],
    "FRONT": ["build-validator"],
    "PIXEL": ["build-validator"],
    "FORM": ["build-validator"],
    "SCOUT": ["build-validator"],
    "SHIELD": ["verify-app"],
}
ASSINATURAS = {
    "build-validator": [r"build[-_ ]validator", r"build validation report"],
    "contract-tester": [r"contract[-_ ]tester", r"contract test", r"testes de contrato"],
    "verify-app": [r"verify[-_ ]app"],
}
NOME_LOG_RE = re.compile(r"^(\d{8}T\d{6}Z)-")
ISENTOS = {"ATLAS", "CRONOS"}
LEITURA_MAXIMA = 200_000


def log_time(arquivo: Path) -> datetime | None:
    achado = NOME_LOG_RE.match(arquivo.name)
    if achado:
        try:
            return datetime.strptime(achado.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(arquivo.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def recent_logs() -> list[tuple[str, str]]:
    """[(nome do arquivo, texto)] dos logs de sub-agente dentro da janela."""
    pasta = comum.delta_dir() / "logs" / "sub-agentes"
    if not pasta.is_dir():
        return []
    agora = comum.now_utc()
    janela = comum.window_seconds()
    recentes = []
    for arquivo in pasta.iterdir():
        if not arquivo.is_file() or arquivo.name == "shield-falhas.log":
            continue
        quando = log_time(arquivo)
        if quando is None or (agora - quando).total_seconds() > janela:
            continue
        try:
            with arquivo.open("r", encoding="utf-8", errors="replace") as fh:
                texto = fh.read(LEITURA_MAXIMA)
        except OSError:
            texto = ""
        recentes.append((arquivo.name, texto))
    return recentes


def field(texto: str, nome: str) -> str | None:
    """Valor de uma linha `nome: valor` gravada pelo fim-subagente.sh; '-' = vazio."""
    achado = re.search(rf"^{nome}:\s*(\S+)", texto, re.MULTILINE)
    if not achado or achado.group(1) == "-":
        return None
    return achado.group(1)


def log_kind(nome: str, texto: str, sub_agente: str) -> bool:
    detectado = field(texto, "subagente_detectado")
    if detectado:
        return detectado.lower() == sub_agente
    padroes = [re.compile(p, re.IGNORECASE) for p in ASSINATURAS[sub_agente]]
    return any(p.search(nome) or p.search(texto) for p in padroes)


def log_owner(nome: str, texto: str) -> str | None:
    """Dono pelo campo `agente_delta11:`; sem o campo, um nome de executor
    em MAIUSCULAS no nome do arquivo ou no texto (relatorio antigo)."""
    if re.search(r"^agente_delta11:", texto, re.MULTILINE):
        dono = field(texto, "agente_delta11")
        return dono.upper() if dono else None
    achado = re.search(r"\b(" + "|".join(OBRIGATORIOS) + r")\b", nome.upper() + "\n" + texto)
    return achado.group(1) if achado else None


def has_proof(agente: str, sub_agente: str, logs: list[tuple[str, str]]) -> bool:
    """
    Prova = log do tipo certo na janela cujo dono e o agente; um log do tipo
    certo SEM dono identificado tambem vale (o relatorio nem sempre diz para
    quem rodou). Log de outro dono nao vale.
    """
    for nome, texto in logs:
        if not log_kind(nome, texto, sub_agente):
            continue
        dono = log_owner(nome, texto)
        if dono is None or dono == agente:
            return True
    return False


def message_missing(agente: str, linha: str, faltando: list[str]) -> str:
    horas = comum.limits()["janela_horas"]
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — sub-agente obrigatorio sem prova de execucao\n"
        f"\n"
        f"Tarefa: {linha[:160]}\n"
        f"Dono: {agente}\n"
        f"Falta prova de: {', '.join(faltando)} (nas ultimas {horas} h)\n"
        f"\n"
        f"Prova aceita: o log que o vigia do SubagentStop grava sozinho em\n"
        f"  .delta-11/logs/sub-agentes/AAAAMMDDTHHMMSSZ-[tipo].log\n"
        f"quando o sub-agente termina. Ele so existe se o sub-agente for disparado\n"
        f"de verdade pelo Agent tool (o CRONOS dispara — D5).\n"
        f"\n"
        f"O que fazer:\n"
        f"  1. Dispare {', '.join(faltando)} para a tarefa de {agente} (inclua\n"
        f"     \"Agente: {agente}\" no pedido e peca que o relatorio cite o agente).\n"
        f"  2. Se o sub-agente REPROVAR: nao conclua; mova a tarefa para BLOQUEADO.\n"
        f"  3. Com o log gravado, marque a conclusao de novo.\n"
    )
    return texto


def message_without_owner(linhas: list[str]) -> str:
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — tarefa concluida sem dono identificado\n"
        f"\n"
        + "".join(f"  - {l[:160]}\n" for l in linhas[:5])
        + "\nToda tarefa concluida precisa dizer quem fez, no formato do kanban:\n"
        "  **T-012** — Descricao | Por: BACK | Aprovado: SHIELD | Data: 2026-10-14\n"
        "Aceito tambem: \"Agente: BACK\", \"[BACK]\" ou a coluna \"| BACK |\".\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not comum.is_kanban_event(evento):
        return 0
    _antes, _depois, novas = comum.kanban_change(evento)
    if not novas:
        return 0

    sem_dono = [l for l in novas if comum.task_id(l) and not comum.line_agent(l)]
    if sem_dono:
        return comum.block(HOOK, message_without_owner(sem_dono), f"{len(sem_dono)} tarefa(s) concluida(s) sem dono")

    logs = None
    for linha in novas:
        agente = comum.line_agent(linha)
        if not agente or agente in ISENTOS or agente not in OBRIGATORIOS:
            continue
        if logs is None:
            logs = recent_logs()
        faltando = [s for s in OBRIGATORIOS[agente] if not has_proof(agente, s, logs)]
        if faltando:
            return comum.block(
                HOOK, message_missing(agente, linha, faltando),
                f"{agente} concluiu {comum.task_id(linha) or 'tarefa'} sem {', '.join(faltando)}",
            )
        comum.log(HOOK, f"OK: {agente} {comum.task_id(linha) or ''} com prova de {', '.join(OBRIGATORIOS[agente])}")
    return 0


if __name__ == "__main__":
    comum.run(main, HOOK)
