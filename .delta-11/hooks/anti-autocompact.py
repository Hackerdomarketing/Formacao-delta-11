#!/usr/bin/env python3
"""
Vigia "anti-autocompact" — Delta-11 v6.3 (2026-10-14). Itens C-019 e C-181.

Problema que resolve: quando a conversa [memoria de curto prazo do agente] enche,
o Claude Code compacta sozinho (autocompact) e o agente pode perder o estado. O
pedido original (fev/2026) era: o agente perceber SOZINHO que esta perto do limite
e passar o trabalho para uma versao nova de si mesmo.

Como mede (C-019): le o arquivo da conversa indicado no evento (`transcript_path`)
e pega o `usage` da ULTIMA resposta do modelo:
    input_tokens + cache_read_input_tokens + cache_creation_input_tokens
Esse numero e o tamanho REAL do contexto naquele momento (ja descontada qualquer
compactacao anterior). Nao mede mais um pedaco de texto isolado.
  - Dentro de um sub-agente (evento com `agent_id`), procura a conversa do proprio
    sub-agente (`.../subagents/agent-<agent_id>.jsonl`). Se nao achar, NAO bloqueia
    (nao da para medir com seguranca) e registra no diario.
  - Janela do modelo: `contexto_janela_tokens` (padrao 200.000) e alerta em
    `contexto_alerta_pct` (padrao 85 %), lidos de .config-limites.json. Se o uso
    observado ja passou de 200.000, o modelo tem janela grande (1 milhao) e o
    calculo usa 1.000.000.

Registro: PreToolUse com matcher "Edit|Write|Agent|Task|Bash".
O que bloqueia: trabalho novo — editar
codigo e rodar comandos — quando o contexto passou do alerta.
Vale para agentes disparados (evento com `agent_id`: CRONOS e executores). Na
sessao principal (comandante/ATLAS) so registra AVISO no diario.
NUNCA bloqueia (para o agente conseguir salvar o estado e passar o bastao):
  - gravar dentro de `.delta-11/` (produto, historia, ativacoes, planos);
  - disparar agente (Agent/Task) e SendMessage.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "anti-autocompact"
JANELA_GRANDE = 1_000_000
LEITURA_MAXIMA_BYTES = 4 * 1024 * 1024
FERRAMENTAS_SEMPRE_LIBERADAS = {"Agent", "Task", "SendMessage", "Read", "Glob", "Grep"}


def transcript_for(evento: dict) -> Path | None:
    principal = evento.get("transcript_path")
    agente_id = evento.get("agent_id")
    if not principal:
        return None
    caminho = Path(os.path.expanduser(principal))
    if not agente_id:
        return caminho if caminho.is_file() else None
    nome = f"agent-{agente_id}.jsonl"
    sessao = evento.get("session_id") or caminho.stem
    candidatos = [
        caminho.parent / sessao / "subagents" / nome,
        caminho.parent / caminho.stem / "subagents" / nome,
        caminho.parent / "subagents" / nome,
    ]
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    try:
        for achado in caminho.parent.glob(f"**/{nome}"):
            return achado
    except OSError:
        pass
    return None


def context_tokens(transcricao: Path) -> int | None:
    """Tokens de contexto da ultima resposta do modelo registrada na conversa."""
    try:
        tamanho = transcricao.stat().st_size
        with transcricao.open("rb") as fh:
            if tamanho > LEITURA_MAXIMA_BYTES:
                fh.seek(tamanho - LEITURA_MAXIMA_BYTES)
            bruto = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    for linha in reversed(bruto.splitlines()):
        if '"usage"' not in linha:
            continue
        try:
            registro = json.loads(linha)
        except ValueError:
            continue
        mensagem = registro.get("message") if isinstance(registro, dict) else None
        uso = (mensagem or {}).get("usage") if isinstance(mensagem, dict) else None
        if not isinstance(uso, dict):
            continue
        total = 0
        for campo in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
            valor = uso.get(campo)
            if isinstance(valor, (int, float)):
                total += int(valor)
        if total > 0:
            return total
    return None


def is_always_allowed(evento: dict) -> bool:
    ferramenta = evento.get("tool_name", "")
    if ferramenta in FERRAMENTAS_SEMPRE_LIBERADAS:
        return True
    if ferramenta in {"Edit", "Write", "MultiEdit"}:
        alvo = comum.absolute_target(evento)
        return alvo is not None and comum.delta_dir_of_path(alvo) is not None
    return False


def message(tokens: int, limite: int, janela: int) -> str:
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — contexto em {tokens:,} tokens "
        f"(limite de alerta {limite:,} de {janela:,})\n"
        f"\n"
        f"A conversa esta quase cheia. Se continuar, o Claude Code compacta sozinho e\n"
        f"voce pode perder o estado do trabalho.\n"
        f"\n"
        f"Faca AGORA, nesta ordem (estas acoes continuam liberadas):\n"
        f"  1. Grave o estado em .delta-11/memoria/[SEU-AGENTE]-produto.md (o que existe)\n"
        f"     e .delta-11/memoria/[SEU-AGENTE]-historia.md (o que fez e o que falta).\n"
        f"  2. Avise o CRONOS por SendMessage: \"contexto cheio, preciso de retomada\".\n"
        f"     O CRONOS dispara uma versao nova sua com contexto limpo (auto-retomada).\n"
        f"  3. Se voce E o CRONOS: grave CRONOS-produto.md e dispare a sua retomada\n"
        f"     (Agent, name: \"cronos\", sem worktree — D2).\n"
    )


def main() -> int:
    evento = comum.read_event()
    if not evento or is_always_allowed(evento):
        return 0
    transcricao = transcript_for(evento)
    if transcricao is None:
        if evento.get("agent_id"):
            comum.log(HOOK, "INFO: conversa do sub-agente nao encontrada — sem medicao, liberado")
        return 0
    tokens = context_tokens(transcricao)
    if tokens is None:
        return 0
    limites = comum.limits()
    janela = int(limites["contexto_janela_tokens"])
    if tokens > janela:
        janela = max(janela, JANELA_GRANDE)
    limite = int(janela * float(limites["contexto_alerta_pct"]) / 100.0)
    if tokens <= limite:
        return 0
    if comum.is_main_session(evento):
        # Sessao principal (comandante/ATLAS): so registra — quem passa o bastao sao
        # os agentes disparados (CRONOS e executores). Nao travamos o comandante.
        comum.log(HOOK, f"AVISO: sessao principal com contexto {tokens} > {limite} tokens")
        return 0
    return comum.block(HOOK, message(tokens, limite, janela), f"contexto {tokens} > {limite} tokens")


if __name__ == "__main__":
    comum.run(main, HOOK)
