#!/usr/bin/env python3
"""
Hook PreToolUse do Delta-11 v4.0.4: bloqueia selo de fase se arquivo
[AGENTE]-produto.md ultrapassar o limite do agente.

Materializa o Mecanismo 6 da Geometria da Criação: compactação dura obrigatória
no Arquivo de Estado. Se o produto não couber no limite, a compactação foi
mal feita — o agente precisa revisar e reduzir.

EXCEÇÃO v4.0.4 (decisão do comandante, 2026-05-22):
  ATLAS (arquiteto) e CRONOS (orquestrador) ficam SEM LIMITE — carregam
  visão arquitetural multi-fase e estado de orquestração multi-onda que
  legitimamente não cabem em 500 tokens. Os 8 agentes executores (BACK,
  FRONT, PIXEL, FORM, ENGINE, VAULT, SHIELD, SCOUT) MANTÊM 500 tokens —
  produto deles é foco-por-tarefa, limite força disciplina saudável.

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.

Invocação:
  Configurado em .claude/settings.json em hooks.PreToolUse com matcher "Edit|Write"
  apontando para este script. Recebe evento JSON via stdin.

Lógica:
  1. Verifica se o Edit/Write atinge .delta-11/memoria/[AGENTE]-produto.md
  2. Resolve o limite do agente (None = ISENTO, int = limite específico)
  3. Se ISENTO, exit 0 imediato
  4. Conta tokens do novo conteúdo (aproximação: len(content)/4 chars por token)
  5. Se passou do limite, exit 2 (bloqueia + injeta mensagem)
  6. Caso contrário, exit 0

Exit codes:
  0 = pode prosseguir
  2 = bloquear (PreToolUse hook convention do Claude Code)
  1 = erro interno (não bloqueia por default — loga e deixa passar)

Política de calibração:
  LIMITE_TOKENS_DEFAULT = 500 (decisão do comandante, 2026-04-18)
  LIMITES_POR_AGENTE = exceções por papel arquitetural
  APROXIMACAO_TOKEN = 4 chars/token (regra prática GPT/Claude — não exato, mas
                                     suficiente para detectar overflow grosseiro)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


LIMITE_TOKENS_DEFAULT = 500
LIMITES_POR_AGENTE: dict[str, int | None] = {
    "ATLAS": None,   # ISENTO — arquiteto carrega visão arquitetural multi-fase
    "CRONOS": None,  # ISENTO — orquestrador carrega estado de despachança multi-onda
}
APROXIMACAO_CHARS_POR_TOKEN = 4

ACTIVITY_LOG = Path(".delta-11/activity-log.md")


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"- [{timestamp_utc()}] [pre-selo] {message}\n")
    except OSError:
        pass


def read_hook_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def eh_arquivo_produto(event: dict) -> str | None:
    """
    Detecta se o Edit/Write atinge um arquivo [AGENTE]-produto.md.
    Retorna o nome do agente se sim, None caso contrário.
    """
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""

    # Match: .delta-11/memoria/[AGENTE]-produto.md
    match = re.search(
        r"[\\/]\.delta-11[\\/]memoria[\\/]([A-Z_-]+)-produto\.md$",
        file_path,
    )
    if match:
        return match.group(1)
    return None


def contar_tokens_aproximado(texto: str) -> int:
    """Aproximação: 1 token ~ 4 caracteres. Suficiente para detectar overflow."""
    if not texto:
        return 0
    return len(texto) // APROXIMACAO_CHARS_POR_TOKEN


def obter_novo_conteudo(event: dict) -> str:
    """
    Extrai o novo conteúdo que o Edit/Write vai gravar.
    - Write: usa tool_input.content (conteúdo completo)
    - Edit: precisa aplicar new_string + estado atual (simplificado: usa new_string)
    """
    tool_input = event.get("tool_input") or {}
    tool_name = event.get("tool_name", "")

    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        # Para Edit, o conteúdo NOVO total é difícil de prever sem reaplicar o diff.
        # Aproximação segura: verificar o tamanho do arquivo ATUAL + delta do new_string
        file_path = tool_input.get("file_path", "")
        novo_fragmento = tool_input.get("new_string", "")
        antigo_fragmento = tool_input.get("old_string", "")
        if file_path and Path(file_path).exists():
            try:
                conteudo_atual = Path(file_path).read_text(encoding="utf-8")
                # Substitui para simular o resultado
                if antigo_fragmento in conteudo_atual:
                    return conteudo_atual.replace(antigo_fragmento, novo_fragmento, 1)
                return conteudo_atual + novo_fragmento
            except OSError:
                return novo_fragmento
        return novo_fragmento
    return ""


def resolver_limite(agente: str) -> int | None:
    """
    Retorna o limite efetivo do agente.
    None = ISENTO (sem limite). int = limite específico.
    Default = LIMITE_TOKENS_DEFAULT (500).
    """
    if agente in LIMITES_POR_AGENTE:
        return LIMITES_POR_AGENTE[agente]
    return LIMITE_TOKENS_DEFAULT


def block_edit(agente: str, tokens: int, limite: int) -> int:
    """Exit 2 bloqueia a ferramenta (PreToolUse hook convention)."""
    excesso = tokens - limite
    print(
        f"[pre-selo] BLOQUEIO v4.0.4 — Mecanismo 6 da Geometria da Criação\n"
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
        f"Obs (v4.0.4): ATLAS e CRONOS são ISENTOS deste limite — papéis\n"
        f"arquitetural/orquestrador legitimamente carregam visão multi-fase.\n"
        f"Os 8 executores mantêm 500 tokens.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    event = read_hook_event()

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
    tokens = contar_tokens_aproximado(conteudo_novo)

    if tokens <= limite:
        log_activity(f"{agente}-produto.md OK ({tokens} tokens ≤ {limite})")
        return 0

    log_activity(
        f"{agente}-produto.md BLOQUEADO ({tokens} tokens > {limite})"
    )
    return block_edit(agente, tokens, limite)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        # Erro interno não deve bloquear — loga e deixa passar
        print(f"[pre-selo] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO não-fatal: {exc}")
        except Exception:  # noqa: BLE001
            pass
        sys.exit(0)
