#!/usr/bin/env python3
"""
Vigia PreToolUse "pre-selo" — Delta-11 v6.3 (2026-10-14). M4, C-160, C-184.

Materializa o M4 dos Mecanismos da Criacao (produto × historia, D22): o arquivo
`.delta-11/memoria/[AGENTE]-produto.md` guarda SO o que existe agora e precisa
caber no limite `produto_max_tokens` (padrao 500 tokens, em
.delta-11/.config-limites.json — D36). O diario completo vai para
`[AGENTE]-historia.md` (sem limite).

Isentos (D8): ATLAS e CRONOS — carregam visao e estado de varias fases.
Os executores (VAULT, BACK, ENGINE, FRONT, PIXEL, FORM, SHIELD, SCOUT) mantem o
limite.

Logica:
  1. So age em Edit/Write de `.delta-11/memoria/[AGENTE]-produto.md` (caminho
     relativo ou absoluto).
  2. Calcula o arquivo FINAL (simula o Edit) e conta tokens (4 caracteres = 1).
  3. Acima do limite: bloqueia (exit 2) com instrucao de compactar.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "pre-selo"
ISENTOS = {"ATLAS", "CRONOS"}


def log_activity(message: str) -> None:
    comum.log(HOOK, message)


def eh_arquivo_produto(event: dict) -> str | None:
    """
    Detecta se o Edit/Write atinge um arquivo [AGENTE]-produto.md.
    Retorna o nome do agente se sim, None caso contrário.
    """
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""

    # Match: .delta-11/memoria/[AGENTE]-produto.md
    match = re.search(
        r"(?:^|[\\/])\.delta-11[\\/]memoria[\\/]([A-Z_-]+)-produto\.md$",
        file_path,
    )
    if match:
        return match.group(1)
    return None


def obter_novo_conteudo(event: dict) -> str:
    """Conteudo final do arquivo depois do Edit/Write (simulado)."""
    _antes, depois = comum.before_and_after(event)
    return depois


def resolver_limite(agente: str) -> int | None:
    """None = ISENTO (ATLAS/CRONOS). Demais: produto_max_tokens (D36)."""
    if agente in ISENTOS:
        return None
    return int(comum.limits()["produto_max_tokens"])


def block_edit(agente: str, tokens: int, limite: int) -> int:
    """Exit 2 bloqueia a ferramenta (PreToolUse hook convention)."""
    excesso = tokens - limite
    print(
        f"[pre-selo] BLOQUEIO {comum.VERSAO} — M4 dos Mecanismos da Criação (produto × história)\n"
        f"\n"
        f"Arquivo {agente}-produto.md excede o limite de {limite} tokens.\n"
        f"Tamanho estimado: {tokens} tokens ({excesso} tokens acima do limite).\n"
        f"\n"
        f"O produto não cabe em {limite} tokens — a compactação foi mal feita.\n"
        f"\n"
        f"AÇÃO REQUERIDA:\n"
        f"  1. Releia o CLAUDE.md Passo 1a do Protocolo de Finalização\n"
        f"  2. Mova detalhes históricos para {agente}-historia.md (sem limite)\n"
        f"  3. No {agente}-produto.md deixe APENAS:\n"
        f"     - O que EXISTE agora (3-5 frases funcionais)\n"
        f"     - Como está estruturado (mínimo para próxima fase construir)\n"
        f"     - O que foi DECIDIDO NÃO FAZER\n"
        f"     - Descobertas que afetam fases futuras\n"
        f"     - Próxima tarefa pendente\n"
        f"  4. Reescreva e tente novamente\n"
        f"\n"
        f"Princípio: Gênesis 1:2 compacta o estado inicial em UMA frase.\n"
        f"Se seu produto não cabe em {limite} tokens, não está selado.\n"
        f"\n"
        f"Obs: ATLAS e CRONOS são ISENTOS deste limite — papéis\n"
        f"arquitetural/orquestrador legitimamente carregam visão multi-fase.\n"
        f"Os executores mantêm {limite} tokens (produto_max_tokens em .config-limites.json).",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = comum.read_event()
    if event.get("tool_name") not in {"Edit", "Write", "MultiEdit"}:
        return 0

    agente = eh_arquivo_produto(event)
    if not agente:
        # Não é edit em arquivo de produto — deixa passar
        return 0

    limite = resolver_limite(agente)
    if limite is None:
        # Agente ISENTO (ATLAS / CRONOS) — papel arquitetural sem limite
        log_activity(f"{agente}-produto.md ISENTO (papel arquitetural sem limite)")
        return 0

    conteudo_novo = obter_novo_conteudo(event)
    tokens = comum.estimate_tokens(conteudo_novo)

    if tokens <= limite:
        log_activity(f"{agente}-produto.md OK ({tokens} tokens ≤ {limite})")
        return 0

    log_activity(f"BLOQUEIO: {agente}-produto.md com {tokens} tokens > {limite}")
    return block_edit(agente, tokens, limite)


if __name__ == "__main__":
    comum.run(main, HOOK)
