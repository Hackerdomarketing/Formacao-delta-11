#!/usr/bin/env python3
"""
Hook PostToolUse do Delta-11: regenera testes de contrato quando project-core.md muda.

Invocado pelo Claude Code quando Edit/Write atinge project-core.md. Compara o hash
atual com o salvo em .delta-11/.contract-hash. Se mudou, faz backup dos testes,
dispara contract-tester e impact-mapper, atualiza hash, notifica agentes ativos.

Cross-platform: funciona em macOS, Linux e Windows. Usa apenas biblioteca padrão.
Requer Python 3.8+.

Uso pelo Claude Code:
  Configurado em .claude/settings.json na seção "hooks.PostToolUse":
  {"matcher": "Edit|Write", "hooks": [{"type": "command",
   "command": "python3 .delta-11/hooks/regenerar-contratos.py"}]}

Input: recebe o JSON do evento do hook via stdin.
Output (stdout): log legível; exit code 0 = sucesso, 1 = erro não-bloqueante.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_CORE_RELATIVE = Path(".delta-11/memoria/project-core.md")
CONTRACT_HASH_FILE = Path(".delta-11/.contract-hash")
CONTRACTS_DIR = Path("tests/contracts")
BACKUP_ROOT = Path(".delta-11/.contract-backup")
ACTIVATIONS_DIR = Path(".delta-11/ativacoes")
ACTIVITY_LOG = Path(".delta-11/activity-log.md")
IMPACT_REPORT_DIR = Path(".delta-11/memoria")


def sha256_of_file(path: Path) -> str:
    """SHA-256 de um arquivo, em hex. Trata arquivo inexistente como string vazia."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_hook_event() -> dict:
    """Lê evento JSON do stdin (formato do Claude Code hook)."""
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_edited_path(event: dict) -> Path | None:
    """
    Extrai o path do arquivo modificado a partir do evento do hook.

    O Claude Code envia algo como:
      {"tool_input": {"file_path": "/abs/path/to/file.md"}, ...}
    Retorna o Path ou None se não for um Edit/Write em arquivo.
    """
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        return None
    return Path(file_path)


def is_project_core(edited: Path | None) -> bool:
    """Detecta se o arquivo editado é project-core.md (qualquer localização)."""
    if edited is None:
        return False
    # compara por sufixo do path (funciona em qualquer SO)
    return edited.as_posix().endswith(PROJECT_CORE_RELATIVE.as_posix())


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp_filename() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def log_activity(message: str) -> None:
    """Acrescenta linha ao activity-log.md com timestamp."""
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = f"- [{timestamp_utc()}] [regenerar-contratos] {message}\n"
    with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
        f.write(entry)


def backup_contracts() -> Path | None:
    """Copia tests/contracts/ atual para .delta-11/.contract-backup/[timestamp]/."""
    if not CONTRACTS_DIR.exists():
        return None
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    target = BACKUP_ROOT / timestamp_filename()
    shutil.copytree(CONTRACTS_DIR, target)
    return target


def agents_currently_active() -> list[str]:
    """Lê .delta-11/ativacoes/ack-*.txt e retorna nomes dos agentes com ACK ativo."""
    if not ACTIVATIONS_DIR.exists():
        return []
    names: list[str] = []
    for p in ACTIVATIONS_DIR.glob("ack-*.txt"):
        name = p.stem[len("ack-"):]
        if name:
            names.append(name.upper())
    return names


def notify_active_agents(active: list[str]) -> None:
    """Cria arquivos contrato-alterado-AGENTE.txt para agentes ativos."""
    if not active:
        return
    ACTIVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    for agent in active:
        path = ACTIVATIONS_DIR / f"contrato-alterado-{agent}.txt"
        path.write_text(
            f"Formação Δ-11 — Notificação automática\n"
            f"Timestamp: {timestamp_utc()}\n"
            f"Agente: {agent}\n\n"
            f"O project-core.md foi alterado. Os testes de contrato foram regenerados "
            f"automaticamente pelo hook. Antes de iniciar a próxima tarefa, releia "
            f"a seção do project-core.md relevante para você e rode os testes de "
            f"contrato atualizados em tests/contracts/ para confirmar que sua "
            f"implementação continua conforme.\n",
            encoding="utf-8",
        )


def dispatch_contract_tester() -> tuple[bool, str]:
    """
    Tenta disparar contract-tester via claude CLI. Se não disponível, retorna
    instrução para execução manual (Onda 1 funciona assim; Onda 2 troca pelo SDK).

    Retorna (sucesso, mensagem).
    """
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return (
            False,
            "CLI 'claude' não encontrado no PATH — contract-tester deve ser disparado "
            "manualmente pelo agente ativo ou pela Onda 2 via SDK nativo.",
        )
    prompt = (
        "Você é o sub-agente contract-tester do Delta-11. Leia "
        ".delta-11/sub-agentes/contract-tester.md e siga o cenário 2 (Regeneração). "
        "Motivo: project-core.md foi alterado; hash antigo não bate. Gere "
        "novamente os arquivos em tests/contracts/ preservando os marcados com "
        "// CONTRATO INCOMPLETO. Retorne o relatório estruturado."
    )
    try:
        # Dispara em background (não bloqueia o hook).
        subprocess.Popen(
            [claude_bin, "--print", prompt],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        return (True, "contract-tester disparado via claude CLI (background)")
    except OSError as e:
        return (False, f"falha ao disparar contract-tester: {e}")


def dispatch_impact_mapper() -> tuple[bool, str]:
    """
    Dispara impact-mapper em paralelo. Mesmo fallback se CLI ausente.
    Retorna (sucesso, mensagem).
    """
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return (
            False,
            "CLI 'claude' não encontrado no PATH — impact-mapper deve ser disparado "
            "manualmente.",
        )
    prompt = (
        "Você é o sub-agente impact-mapper do Delta-11. Leia "
        ".delta-11/sub-agentes/impact-mapper.md e execute o protocolo. Motivo: "
        "project-core.md foi alterado; o CRONOS precisa do relatório de impacto "
        "para decidir quais tarefas criar no kanban. Gere o arquivo "
        ".delta-11/memoria/impacto-mudanca-[timestamp].md e atualize kanban.md "
        "com tarefas [IMPACTO-MUDANCA]."
    )
    try:
        subprocess.Popen(
            [claude_bin, "--print", prompt],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        return (True, "impact-mapper disparado via claude CLI (background)")
    except OSError as e:
        return (False, f"falha ao disparar impact-mapper: {e}")


def save_new_hash(new_hash: str) -> None:
    CONTRACT_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_HASH_FILE.write_text(new_hash + "\n", encoding="utf-8")


def main() -> int:
    # Só age se o arquivo editado é project-core.md
    event = read_hook_event()
    edited = extract_edited_path(event)

    if not is_project_core(edited):
        # Evento não relevante — sair silencioso com sucesso
        return 0

    # Garante working directory do projeto (Claude Code costuma rodar hook lá)
    core_path = PROJECT_CORE_RELATIVE
    if not core_path.exists():
        print(f"[regenerar-contratos] {core_path} não existe; nada a fazer.")
        return 0

    # Compara hashes
    new_hash = sha256_of_file(core_path)
    old_hash = ""
    if CONTRACT_HASH_FILE.exists():
        old_hash = CONTRACT_HASH_FILE.read_text(encoding="utf-8").strip()

    if new_hash == old_hash:
        # project-core.md foi reescrito mas conteúdo idêntico — nada a fazer
        print(f"[regenerar-contratos] hash inalterado ({new_hash[:12]}); nada a fazer.")
        return 0

    log_activity(
        f"project-core.md alterado: hash {old_hash[:12] or '(vazio)'} -> {new_hash[:12]}"
    )

    # 1) Backup dos testes de contrato atuais
    backup = backup_contracts()
    if backup:
        log_activity(f"backup de tests/contracts/ em {backup.as_posix()}")

    # 2) Dispara contract-tester (regeneração)
    ok_ct, msg_ct = dispatch_contract_tester()
    log_activity(f"contract-tester: {msg_ct}")
    print(f"[regenerar-contratos] contract-tester: {msg_ct}")

    # 3) Dispara impact-mapper (em paralelo — ambos analisam o mesmo diff)
    ok_im, msg_im = dispatch_impact_mapper()
    log_activity(f"impact-mapper: {msg_im}")
    print(f"[regenerar-contratos] impact-mapper: {msg_im}")

    # 4) Atualiza hash salvo
    save_new_hash(new_hash)
    log_activity(f"contract-hash atualizado para {new_hash[:12]}")

    # 5) Notifica agentes ativos
    active = agents_currently_active()
    if active:
        notify_active_agents(active)
        log_activity(f"agentes ativos notificados: {', '.join(active)}")
        print(f"[regenerar-contratos] notificados: {', '.join(active)}")

    # exit 0 mesmo se CLI ausente — dispatch fallback é responsabilidade do agente
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        # Hook nunca deve travar fluxo de Edit/Write por erro próprio
        print(f"[regenerar-contratos] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO não-fatal: {exc}")
        except Exception:
            pass
        sys.exit(0)
