#!/usr/bin/env python3
"""
Vigia UserPromptSubmit "validar deploy" — Delta-11 v6.3 (2026-10-14). Item C-044.

Quando o comandante PEDE um deploy [publicar o sistema na internet], este vigia
roda os testes de contrato antes de a mensagem chegar ao agente. Se falharem, a
mensagem e barrada (exit 2) e o comandante ve o motivo.

So dispara em PEDIDO CLARO (C-044), por exemplo:
  "faça o deploy", "pode fazer o deploy?", "publique em produção", "sobe pra
  produção", "coloca no ar", "deploy" (sozinho), "/deploy", "ship it", "go live"
NAO dispara em:
  - negacao: "não faça deploy", "nao suba", "sem deploy", "don't deploy";
  - pergunta: "como funciona o deploy?", "quando vamos fazer o deploy?";
  - mencao solta: "o deploy de ontem falhou", relatorios de agentes
    (mensagens com <task-notification>, <teammate-message> ou que comecam com
    a etiqueta de um agente, ex.: "[CRONOS] ...").

Testes: os mesmos do validar-contratos-fim-fase (Node `npm run test:contracts` ou
Python `pytest tests/contracts/`), na pasta principal, ate 110 s (registro: 120 s —
D30). Sem framework de testes: libera e registra AVISO.

Erro interno: libera a mensagem, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "validar-deploy"
TEMPO_MAXIMO = 110

_ALVO = (
    r"(?:o\s+|um\s+|the\s+)?deploy\b"
    r"|(?:p[ae]ra|pra|em|no|na|to)\s+(?:a\s+)?produ[cç][ãa]o\b"
    r"|no\s+ar\b"
    r"|(?:to\s+)?prod(?:uction)?\b"
)
_VERBO = (
    r"fa[cç]a|faz(?:er)?|fazemos|rod[ae]r?|execut[ae]r?|dispar[ae]r?|mand[ae]r?|bora|vamos"
    r"|pode(?:mos)?(?:\s+fazer)?|quero|preciso|subir|sub[ae]|sobe|publi(?:que|ca|car)|coloc(?:a|ar|que)"
    r"|lan[cç](?:a|ar|e)|joga|jogar|push|ship|release|do|run|go"
)
PEDIDO_RE = re.compile(rf"\b(?:{_VERBO})\b\s+(?:\w+\s+){{0,2}}?(?:{_ALVO})", re.IGNORECASE)
SOZINHO_RE = re.compile(r"^\s*/?(?:deploy|ship\s+it|go\s+live)\s*[!.]*\s*$", re.IGNORECASE)
INGLES_RE = re.compile(r"\b(?:deploy\s+(?:it|now|to\s+prod\w*)|ship\s+it|go\s+live)\b", re.IGNORECASE)
NEGACAO_RE = re.compile(
    r"\b(?:n[ãa]o|nunca|jamais|sem|nem|evite|evitar|don'?t|do\s+not|never|no)\b[^.!?\n]{0,25}$",
    re.IGNORECASE,
)
PERGUNTA_INICIO_RE = re.compile(
    r"^\s*(?:como|quando|qual|quais|o\s+que|por\s*que|porque|onde|quem|j[áa]\s+|how|when|what|why|where|who|did|was|is)\b",
    re.IGNORECASE,
)
RELATORIO_RE = re.compile(
    r"<task-notification|<teammate-message|^\s*\[(?:" + "|".join(sorted(comum.TODOS_OS_AGENTES)) + r")\]",
    re.IGNORECASE,
)


def sentences(texto: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?\n])\s+", texto) if s.strip()]


def asks_for_deploy(texto: str) -> bool:
    if not texto or RELATORIO_RE.search(texto):
        return False
    if SOZINHO_RE.match(texto):
        return True
    for frase in sentences(texto):
        achado = PEDIDO_RE.search(frase) or INGLES_RE.search(frase)
        if not achado:
            continue
        if NEGACAO_RE.search(frase[:achado.start()]):
            continue
        if frase.rstrip().endswith("?") and PERGUNTA_INICIO_RE.match(frase):
            continue
        return True
    return False


def main() -> int:
    evento = comum.read_event()
    texto = evento.get("prompt") or evento.get("user_prompt") or ""
    if not asks_for_deploy(texto):
        return 0
    comum.log(HOOK, f"pedido de deploy detectado: {texto[:100]}")
    raiz = comum.main_project_dir()
    comando = comum.contract_test_command(raiz)
    if comando is None:
        comum.log(HOOK, "AVISO: nenhum framework de testes de contrato — deploy liberado sem conferencia")
        return 0
    passou, saida = comum.run_contract_tests(comando, raiz, TEMPO_MAXIMO)
    if passou:
        comum.log(HOOK, "OK: testes de contrato passaram — pedido de deploy liberado")
        return 0
    ultimas = "\n".join(saida.splitlines()[-10:]) or "(sem saida)"
    return comum.block(
        HOOK,
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — os testes de contrato falharam; o deploy nao foi pedido ao agente.\n"
        f"\n"
        f"Comando: {' '.join(comando)}\n"
        f"Final da saida:\n{ultimas}\n"
        f"\n"
        f"Peca a correcao primeiro (ex.: \"corrija os testes de contrato\"). Quando os\n"
        f"testes passarem, peca o deploy de novo.\n",
        "pedido de deploy com testes de contrato falhando",
    )


if __name__ == "__main__":
    comum.run(main, HOOK)
