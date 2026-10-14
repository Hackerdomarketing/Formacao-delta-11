#!/usr/bin/env python3
"""
Vigia "URLs validas" — Delta-11 v6.3 (2026-10-14). Item C-041, decisao D34.

Furo 10 da auditoria 2026-08-11: o brief de retomada levou URLs quebradas (sem
dominio completo, cortadas). Este vigia barra URL mal formada em Edit/Write.

Validas (D34):
  - dominio com terminacao de 2+ letras: https://api.exemplo.com/x
  - localhost, 127.0.0.1 (e outros IPs), [::1], *.local: http://localhost:3000
  - nome interno com porta (ex.: docker): http://db:5432
Ignoradas (nao sao URL "de verdade"):
  - aspas, crase e < > em volta sao descartados: "https://api.x.com" e valida
  - marcadores de modelo no endereco: https://${HOST}/api, https://{{dominio}},
    https://[seu-dominio], https://<host> — nao sao conferidos
  - pontuacao no fim da frase (. , ; : ! ?) e parenteses/colchetes de fechamento
Invalidas (bloqueia, exit 2):
  - sem endereco depois de http(s)://, nome sem terminacao e sem porta
    (https://exemplo), terminacao numerica ou com caractere proibido.

Quando age: PreToolUse em Edit|Write, em qualquer arquivo; confere so o texto NOVO
(new_string / content).

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import ipaddress
import os
import re
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "urls-validas"
URL_RE = re.compile(r"https?://[^\s\"'`<>]*", re.IGNORECASE)
PONTUACAO_FINAL = ".,;:!?)]}*_"
MARCADORES = ("${", "{{", "{", "}", "[", "]", "<", ">", "%", "$", "*")
ROTULO_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")
TERMINACAO_RE = re.compile(r"^(?:[A-Za-z]{2,63}|xn--[A-Za-z0-9-]{2,59})$")


def clean(url: str) -> str:
    while url and url[-1] in PONTUACAO_FINAL:
        if url[-1] == ")" and url.count("(") >= url.count(")"):
            break
        url = url[:-1]
    return url


def check(url: str) -> str | None:
    """None se valida (ou ignorada); senao, o motivo."""
    depois = url.split("://", 1)[1] if "://" in url else ""
    if not depois:
        return None  # "https://" sozinho: texto sobre o protocolo, nao endereco
    autoridade = re.split(r"[/?#]", depois, maxsplit=1)[0]
    if any(m in autoridade for m in MARCADORES if m not in ("[", "]")) or (
        "[" in autoridade and not autoridade.startswith("[")
    ):
        return None  # marcador de modelo
    try:
        partes = urlsplit(url)
        host = partes.hostname or ""
        porta = partes.port
    except ValueError:
        if autoridade.startswith("["):
            return None  # [seu-dominio] — marcador
        return "porta ou endereco invalido"
    if not host:
        return "sem endereco depois de http(s)://"
    if autoridade.startswith("["):
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            return None  # [seu-dominio] — marcador
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        pass
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        return None
    rotulos = host.split(".")
    if any(not ROTULO_RE.match(r) for r in rotulos):
        return "caractere invalido no endereco"
    if len(rotulos) == 1:
        if porta is not None:
            return None  # nome interno com porta (docker, rede local)
        return "sem terminacao de dominio (ex.: .com, .com.br)"
    if not TERMINACAO_RE.match(rotulos[-1]):
        return "terminacao de dominio invalida"
    return None


def message(invalidas: list[tuple[str, str]], caminho: str) -> str:
    texto = (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — URL mal formada\n"
        f"\n"
        f"Arquivo: {caminho}\n"
        f"URLs com problema:\n"
    )
    texto += "".join(f"  - {u}\n    Motivo: {m}\n" for u, m in invalidas[:10])
    texto += (
        "\nFormato certo: https://dominio.com/caminho. Tambem valem localhost,\n"
        "127.0.0.1, *.local e nome interno com porta (http://db:5432).\n"
        "Marcadores de modelo (https://${HOST}, https://{{dominio}}) sao aceitos.\n"
    )
    return texto


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0
    entrada = comum.tool_input(evento)
    textos = [entrada.get("new_string") or "", entrada.get("content") or ""]
    for item in entrada.get("edits") or []:
        if isinstance(item, dict):
            textos.append(item.get("new_string") or "")
    invalidas = []
    for bruta in URL_RE.findall("\n".join(textos)):
        url = clean(bruta)
        motivo = check(url)
        if motivo:
            invalidas.append((url, motivo))
    if not invalidas:
        return 0
    caminho = comum.target_path_text(evento) or "<desconhecido>"
    return comum.block(HOOK, message(invalidas, caminho), f"{len(invalidas)} URL(s) invalida(s) em {caminho}")


if __name__ == "__main__":
    comum.run(main, HOOK)
