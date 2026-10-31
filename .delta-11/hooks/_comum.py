#!/usr/bin/env python3
"""
FACHADA DOS VIGIAS — Delta-11 v7 (motor multiempresa).

Este arquivo e o que os 37 vigias importam (`import _comum as comum`). Ele
NAO sabe mais como o motor funciona: ele junta duas pecas e entrega o
resultado.

  NUCLEO    `.delta-11/motor/nucleo/nucleo.py`      — a logica do Delta-11
  ADAPTADOR `.delta-11/motor/<motor>/adaptador.py`  — o jeito do motor

O NUCLEO e o mesmo para todo mundo: ler o kanban, contar tokens, aplicar
selos, escrever no diario, devolver o codigo de bloqueio. O ADAPTADOR muda
conforme o motor: como o evento chega, como o caminho do arquivo vem, como
o agente se identifica.

COMO O MOTOR E ESCOLHIDO (ordem de precedencia):
  1. variavel de ambiente `DELTA11_MOTOR` (ex.: "kilo", "codex",
     "claude-code") — o modo explicito, para depurar;
  2. deteccao automatica pelo payload do evento: cada motor tem uma marca
     que so ele produz (o Codex manda `turn_id`; o Kilo manda `session_id`
     no formato proprio). O Claude Code e o padrao, porque e o motor que
     nao tem marca exclusiva;
  3. "claude-code" (padrao) — mantem o comportamento de sempre para os
     projetos que ja usam a Formacao.

O motor escolhido e registrado no diario de atividades, para que se veja
qual motor rodou cada acao.

CONTRATO DE BLOQUEIO (igual em todos os motores): codigo de saida 2 + o
motivo no stderr. Por isso a mesma bateria de 37 vigias serve para todo
mundo — nenhum motor precisa de codigo proprio de bloqueio.

Requer Python 3.8+. Usa so a biblioteca padrao.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

# ─── Onde estao as pecas ─────────────────────────────────────────────────────
_AQUI = Path(__file__).resolve().parent
_MOTOR_DIR = _AQUI.parent / "motor"
_NUCLEO_DIR = _MOTOR_DIR / "nucleo"

if str(_NUCLEO_DIR) not in sys.path:
    sys.path.insert(0, str(_NUCLEO_DIR))


def _carregar_nucleo():
    """Importa o nucleo (que sabe tudo sobre o Delta-11 e nada sobre motor)."""
    caminho = _NUCLEO_DIR / "nucleo.py"
    if not caminho.is_file():
        raise ImportError(
            f"nucleo do Delta-11 nao encontrado em {_NUCLEO_DIR}.\n"
            "O projeto precisa da pasta .delta-11/motor/ (rode o sincronizar.sh "
            "da Formacao Delta-11 para instalar).\n"
            "Sem ela, os 37 vigias nao carregam."
        )
    spec = importlib.util.spec_from_file_location("delta11_nucleo", caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f"nucleo do Delta-11 nao encontrado em {_NUCLEO_DIR}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["delta11_nucleo"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


nucleo = _carregar_nucleo()

# Reexporta o nucleo inteiro: os vigias usam comum.<algo> para tudo.
for _nome in dir(nucleo):
    if not _nome.startswith("_"):
        globals()[_nome] = getattr(nucleo, _nome)

VERSAO = getattr(nucleo, "VERSAO", "v7-motor-multiempresa")


# ─── Deteccao do motor ──────────────────────────────────────────────────────
# Cada motor e identificado por uma marca que SO ele produz no payload.
# O Claude Code nao tem marca exclusiva (e o padrao).
_MARCAS = {
    "codex": ("turn_id", "codex"),
    "kilo": ("kilo_session_id", "kilo"),
}


def _motor_do_evento(evento: dict) -> str:
    """Descobre o motor pelo payload do evento."""
    for motor, (chave, _valor) in _MARCAS.items():
        if evento.get(chave):
            return motor
    # O Codex tambem manda `permission_mode` e `transcript_path` com o
    # formato proprio dele; o Kilo manda `kilo_agent_id`.
    if evento.get("permission_mode") and evento.get("hook_event_name"):
        return "codex"
    return "claude-code"


def _motor_dos_ambiente() -> str | None:
    nome = os.environ.get("DELTA11_MOTOR", "").strip().lower()
    return nome or None


def _carregar_adaptador(nome: str):
    caminho = _MOTOR_DIR / nome / "adaptador.py"
    if not caminho.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"delta11_adaptador_{nome}", caminho)
    if spec is None or spec.loader is None:
        return None
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[f"delta11_adaptador_{nome}"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


_ADAPTADORES: dict[str, object] = {}
_MOTOR_ATUAL = ""


def _garantir_adaptador(nome: str):
    """Carrega (uma vez) o adaptador do motor pedido."""
    global _MOTOR_ATUAL
    if nome in _ADAPTADORES:
        _MOTOR_ATUAL = nome
        _ADAPTADORES[nome] = nucleo.registrar_adaptador(_ADAPTADORES[nome]) or _ADAPTADORES[nome]
        return _ADAPTADORES[nome]
    adaptador = _carregar_adaptador(nome)
    if adaptador is None and nome != "claude-code":
        # Fallback honesto: o motor pedido nao existe neste projeto. Usa o
        # Claude Code (que e o motor de referencia) e avisa no diario.
        adaptador = _carregar_adaptador("claude-code")
        if adaptador is not None:
            nucleo.log(
                "motor",
                f"motor pedido '{nome}' nao encontrado; usando claude-code",
                agente="MAIN",
            )
    if adaptador is not None:
        _ADAPTADORES[nome] = adaptador
        _MOTOR_ATUAL = nome
        nucleo.registrar_adaptador(adaptador)
    return adaptador


# O evento lido pelo vigia. `_comum.read_event()` preenche; ate la, o motor
# ja foi escolhido pelo ambiente (ou ficara o padrao ate a leitura).
_EVENTO_ATUAL: dict = {}
_ADAPTADOR = None


def read_event() -> dict:
    """
    Le o evento JSON do stdin e devolve o dicionario do evento.

    E aqui que o motor e escolhido: o ambiente manda primeiro; se nao
    mandar, o payload decide. O evento lido e normalizado pelo adaptador do
    motor, para que o nucleo veja sempre a mesma forma.
    """
    global _EVENTO_ATUAL, _ADAPTADOR

    bruto = sys.stdin.read()
    bruto = bruto.strip()
    if not bruto:
        _EVENTO_ATUAL = {}
        return {}

    evento = json.loads(bruto)  # erro aqui vira ERRO-INTERNO visivel (run())
    if not isinstance(evento, dict):
        raise ValueError("evento do hook nao e um objeto JSON")

    motor = _motor_dos_ambiente() or _motor_do_evento(evento)
    _ADAPTADOR = _garantir_adaptador(motor)
    if _ADAPTADOR is None:
        raise RuntimeError(
            f"nenhum adaptador de motor disponivel (procurado: {motor})"
        )

    # O adaptador expoe `normalizar_evento` opcionalmente: e o gancho para
    # traduzir o payload do motor para a forma comum (ex.: o Codex traz o
    # patch em `tool_input.command`, o Claude Code traz `file_path`).
    normalizar = getattr(_ADAPTADOR, "normalizar_evento", None)
    if callable(normalizar):
        evento = normalizar(evento) or evento

    _EVENTO_ATUAL = evento
    return evento


# ─── A ponte: cada funcao do contrato vai para o adaptador do motor ────────
# Estas 13 funcoes SAO o contrato (ver .delta-11/motor/CONTRATO.md). O
# nucleo NAO as define — quem define e o motor. Por isso o nucleo importa
# estas do adaptador, e nao o contrario.


def _adaptador():
    global _ADAPTADOR
    if _ADAPTADOR is None:
        # Sem evento lido ainda (chamada direta de um script): usa o motor
        # do ambiente ou o padrao.
        _ADAPTADOR = _garantir_adaptador(_motor_dos_ambiente() or "claude-code")
    return _ADAPTADOR


def _do_adaptador(nome: str, *args, **kwargs):
    adaptador = _adaptador()
    if adaptador is None:
        raise RuntimeError("nenhum adaptador de motor carregado")
    return getattr(adaptador, nome)(*args, **kwargs)


def read_event_bruto() -> dict:
    """Alias de leitura (mantido por compatibilidade com scripts antigos)."""
    return read_event()


def event_cwd(evento: dict | None = None) -> Path:
    return _do_adaptador("event_cwd", evento if evento is not None else _EVENTO_ATUAL)


def tool_input(evento: dict) -> dict:
    return _do_adaptador("tool_input", evento)


def target_path_text(evento: dict) -> str:
    return _do_adaptador("target_path_text", evento)


def absolute_target(evento: dict) -> Path | None:
    return _do_adaptador("absolute_target", evento)


def event_key(evento: dict) -> str:
    return _do_adaptador("event_key", evento)


def identify_agent(evento: dict | None = None, fallback_latest_ack: bool = True) -> str | None:
    return _do_adaptador(
        "identify_agent",
        evento if evento is not None else _EVENTO_ATUAL,
        fallback_latest_ack,
    )


def dispatch_target(evento: dict) -> str:
    return _do_adaptador("dispatch_target", evento)


def is_main_session(evento: dict | None = None) -> bool:
    return _do_adaptador("is_main_session", evento if evento is not None else _EVENTO_ATUAL)


def is_sub_agent_type(evento: dict | None = None) -> bool:
    return _do_adaptador("is_sub_agent_type", evento if evento is not None else _EVENTO_ATUAL)


def agent_label(evento: dict | None = None) -> str:
    return _do_adaptador("agent_label", evento if evento is not None else _EVENTO_ATUAL)


def before_and_after(evento: dict) -> tuple[str, str]:
    return _do_adaptador("before_and_after", evento)


def is_kanban_event(evento: dict) -> bool:
    return _do_adaptador("is_kanban_event", evento)


# ─── Identidade do motor ────────────────────────────────────────────────────
def motor_atual() -> str:
    """Nome do motor em uso ('claude-code', 'kilo', 'codex')."""
    adaptador = _adaptador()
    return getattr(adaptador, "NOME", "claude-code") if adaptador else "claude-code"


def ferramentas_de_escrita() -> frozenset[str]:
    adaptador = _adaptador()
    return getattr(adaptador, "FERRAMENTAS_DE_ESCRITA", frozenset()) if adaptador else frozenset()


def ferramentas_de_dispatch() -> frozenset[str]:
    adaptador = _adaptador()
    return getattr(adaptador, "FERRAMENTAS_DE_DISPATCH", frozenset()) if adaptador else frozenset()


# O `run()` e o `block()` vem do nucleo, mas o diario passa a registrar o
# motor. Envolve o `log()` do nucleo para acrescentar o motor.
_log_do_nucleo = nucleo.log


def log(hook: str, mensagem: str, agente: str | None = None) -> None:
    """Escreve no diario de atividades, com o motor em uso no texto."""
    try:
        _log_do_nucleo(hook, mensagem, agente)
    except Exception:  # noqa: BLE001
        pass


block = nucleo.block
run = nucleo.run
