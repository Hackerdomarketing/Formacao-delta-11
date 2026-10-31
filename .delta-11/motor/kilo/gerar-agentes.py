#!/usr/bin/env python3
"""
GERADOR DOS AGENTES DO DELTA-11 PARA O KILO — Delta-11 v7 (motor multiempresa).

O Kilo define agentes customizados em arquivos markdown:

    ~/.config/kilo/agent/<nome>.md     (global)
    .kilo/agent/<nome>.md              (do projeto)

com um cabecalho YAML (`name`, `description`, `mode`, `model`, `permissions`)
e o corpo como prompt de sistema.

Este gerador cria os 10 agentes da Formacao (ATLAS, CRONOS, FRONT, PIXEL,
FORM, BACK, ENGINE, VAULT, SHIELD, SCOUT) a partir da identidade canonica
(`.delta-11/operativos/<NOME>.md`) e dos perfis (`.delta-11/perfis/<NOME>.json`).

O QUE E ADAPTADO (e por que):
  - `mode`: "primary" para o ATLAS e o CRONOS (eles coordenam e o usuario
    conversa com eles); "all" para os executores (podem ser chamados como
    sub-agente Eprimary, porque o SHIELD e o SCOUT sao acionados por
    outros agentes).
  - `model`: vem do perfil do Delta-11 (D26 — Opus para ATLAS, CRONOS e
    SHIELD; Sonnet para os executores). No Kilo o campo e `model` com o
    formato "provider/model".
  - `system`: o prompt de sistema e o operativo do agente + o bloco de
    motor que explica como este motor (Kilo) executa o protocolo.
  - `permissions`: as regras do agente (so o executor, so o CRONOS).

O BLOCO DE MOTOR e o que troca "Claude Code" por "Kilo" no texto: onde o
protocolo fala em `Agent tool`, `SendMessage` ou `$CLAUDE_PROJECT_DIR`, o
bloco traduz para o equivalente do Kilo.

Uso:
  python3 .delta-11/motor/kilo/gerar-agentes.py [destino]
      grava os 10 arquivos .md no destino (padrao: .kilo/agent/ do projeto).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MOTOR_DIR = AQUI.parent
DELTA_DIR = MOTOR_DIR.parent

AGENTES = [
    "ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM",
    "BACK", "ENGINE", "VAULT", "SHIELD", "SCOUT",
]

# Modo no Kilo: "primary" = o usuario conversa com ele; "all" = tambem pode
# ser usado como sub-agente; "subagent" = so como sub-agente.
MODO = {
    "ATLAS": "primary",
    "CRONOS": "primary",
    "SHIELD": "all",
    "SCOUT": "all",
}

# O bloco que explica ao agente COMO este motor executa o protocolo.
BLOCO_DE_MOTOR = """
═══════════════════════════════════════════════════════════════
  MOTOR ATUAL: KILO (não é o Claude Code)
═══════════════════════════════════════════════════════════════

Este projeto roda a Formação Δ-11 no motor **Kilo** (fork do Roo Code no
VS Code). O protocolo é o mesmo; a ferramenta é diferente. Onde o protocolo
fala em ferramenta do Claude Code, use a equivalente do Kilo:

| O protocolo fala em      | No Kilo use                                              |
|--------------------------|----------------------------------------------------------|
| `Agent` tool com `isolation: "worktree"` | o **Agent Manager** (`mode: worktree`), com `tasks[].name` e `tasks[].branchName` |
| `run_in_background: true` | o Agent Manager ja roda em paralelo; todas as tarefas da onda saem na MESMA chamada |
| `SendMessage` ao CRONOS  | o **quadro** (`board_post`): a mensagem e aviso, o ARQUIVO e a verdade |
| `$CLAUDE_PROJECT_DIR`    | o caminho absoluto da **pasta principal** do projeto (descubra com `git rev-parse --path-format=absolute --git-common-dir` e pegue o diretório PAI) |
| `subagent_type: "general-purpose"` | `tasks[].agent` = o nome do agente customizado (ex.: `back-onda-2`) |
| hooks disparados sozinhos | **não existem no Kilo** — chame o **portão** antes de agir |

O PORTAO (a protecao que substitui os hooks):

    python3 .delta-11/motor/porteiro/porteiro.py <vigia> <<< '<evento json>'

Devolve `exit 0` (liberado) ou `exit 2` (BLOQUEADO, com o motivo no stderr).
Para conferir a acao contra TODOS os vigias de uma vez (sem bloquear):

    python3 .delta-11/motor/porteiro/porteiro.py --auditar <<< '<evento json>'

O evento JSON tem o mesmo formato do Claude Code:
`{"tool_name": "Write", "tool_input": {"file_path": "..."}, "cwd": "..."}`.

REGRA DE OURO: um vigia que bloqueia e uma barreira, nao uma sugestao. Se o
portao devolveu 2, a acao NAO foi feita — corrija e tente de novo.

TRABALHO EM WORKTREE: o executor trabalha na sua worktree (isolada). Tudo o
que for COMPARTILHADO (kanban, product-core, memoria do agente, travas,
logs) se grava pelo **caminho absoluto da pasta principal**, nunca pelo
caminho relativo da worktree — senao o CRONOS nao ve.
"""

# Substituicoes de texto do operativo: Claude Code -> Kilo.
SUBSTITUICOES = [
    (r"\bSendMessage\b", "quadro (board_post)"),
    (r"\$CLAUDE_PROJECT_DIR", "PASTA_PRINCIPAL"),
    (r"\bAgent tool\b", "Agent Manager"),
]


def _identidade(nome: str) -> str:
    caminho = DELTA_DIR / "operativos" / f"{nome}.md"
    if not caminho.is_file():
        return f"# {nome}\n\n(operativo nao encontrado em {caminho})"
    return caminho.read_text(encoding="utf-8")


def _perfil(nome: str) -> dict:
    caminho = DELTA_DIR / "perfis" / f"{nome}.json"
    if not caminho.is_file():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# O perfil do Delta-11 usa os apelidos "opus" e "sonnet" (D26). O Kilo
# precisa do slug completo "provider/model". O mapeamento e por PALAVRA
# CHAVE — o slug exato muda com as versoes, entao o usuario ajusta aqui
# quando quiser um modelo mais novo.
MODELOS = {
    "opus": "anthropic/claude-opus-4-8",
    "sonnet": "anthropic/claude-sonnet-4-5",
    "haiku": "anthropic/claude-haiku-4-5",
}


def _modelo_do_perfil(nome: str) -> str | None:
    """O modelo do perfil (D26). Formato do Kilo: "provider/model"."""
    perfil = _perfil(nome)
    modelo = perfil.get("model") or perfil.get("modelo")
    if not modelo:
        return None
    modelo = str(modelo).strip()
    if "/" in modelo:
        return modelo
    return MODELOS.get(modelo.lower())


def _descricao(nome: str) -> str:
    """A descricao curta do agente (quando o Kilo deve usa-lo)."""
    perfis = _perfil(nome)
    for chave in ("description", "descricao", "resumo"):
        if perfis.get(chave):
            return str(perfis[chave])
    # Fallback: o "papel" do perfil (ex.: "Gerente de Projeto e Orquestrador").
    if perfis.get("papel"):
        return f"{nome} — {perfis['papel']} da Formação Δ-11"
    return f"Agente {nome} da Formação Δ-11"


def _traduzir(texto: str) -> str:
    for padrao, troca in SUBSTITUICOES:
        texto = re.sub(padrao, troca, texto)
    return texto


def gerar_agente(nome: str) -> str:
    identidade = _traduzir(_identidade(nome))
    modelo = _modelo_do_perfil(nome)
    modo = MODO.get(nome, "all")
    descricao = _descricao(nome)

    cabecalho = [f"---", f"name: {nome.lower()}", f"description: {json.dumps(descricao, ensure_ascii=False)}"]
    if modelo:
        cabecalho.append(f"model: {modelo}")
    cabecalho.append(f"mode: {modo}")
    cabecalho.append(f"---")
    cabecalho.append("")

    return "\n".join(cabecalho) + identidade.rstrip() + "\n" + BLOCO_DE_MOTOR


def main() -> int:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".kilo/agent")
    destino.mkdir(parents=True, exist_ok=True)
    for nome in AGENTES:
        caminho = destino / f"{nome.lower()}.md"
        caminho.write_text(gerar_agente(nome), encoding="utf-8")
        print(f"  {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
