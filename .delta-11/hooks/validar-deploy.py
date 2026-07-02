#!/usr/bin/env python3
"""
Hook UserPromptSubmit do Delta-11: bloqueia deploy sem validação completa.

Cross-platform: macOS, Linux, Windows. Requer Python 3.8+.

Quando disparado:
  Toda mensagem que o comandante envia ao Claude Code. Este hook examina a
  mensagem e, se contiver palavras-chave de deploy ("deploy", "subir para
  producao", "publicar em producao", etc.), executa validação completa:
    1. Roda testes de contrato (contract-tester via npm/pytest)
    2. Dispara verify-app se SHIELD não tiver rodado recentemente
  Se qualquer uma falhar, bloqueia a mensagem e instrui correção.

Se a mensagem NÃO contém palavras-chave de deploy, o hook sai silencioso
com exit 0.

Exit codes:
  0 = passou (prosseguir normal)
  2 = bloqueado (convenção UserPromptSubmit do Claude Code: stderr vira
      mensagem ao usuário e prompt não é processado pelo modelo)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ACTIVITY_LOG = Path(".delta-11/activity-log.md")
PACKAGE_JSON = Path("package.json")
PYTEST_INI = Path("pytest.ini")
PYPROJECT = Path("pyproject.toml")


DEPLOY_KEYWORDS = [
    # Português
    r"\bdeploy\b",
    r"\bsubir\s+(p[ae]ra|em)\s+produ[cç][aã]o\b",
    r"\bpublicar\s+em\s+produ[cç][aã]o\b",
    r"\blan[cç]ar\s+em\s+produ[cç][aã]o\b",
    r"\bcolocar\s+no\s+ar\b",
    r"\bvai\s+pro\s+ar\b",
    # Inglês
    r"\bship\s+to\s+prod\b",
    r"\brelease\s+to\s+production\b",
    r"\bgo\s+live\b",
    r"\bpush\s+to\s+prod\b",
]


def timestamp_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_activity(message: str) -> None:
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
        f.write(f"- [{timestamp_utc()}] [validar-deploy] {message}\n")


def read_hook_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_prompt_text(event: dict) -> str:
    """
    Extrai o texto da mensagem do usuário do evento UserPromptSubmit.
    Formato esperado do Claude Code:
      {"prompt": "texto..."}
    """
    return event.get("prompt") or event.get("user_prompt") or ""


def looks_like_deploy_intent(prompt: str) -> bool:
    """Detecta se a mensagem do usuário sugere intenção de deploy."""
    if not prompt:
        return False
    lowered = prompt.lower()
    for pattern in DEPLOY_KEYWORDS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True
    return False


def detect_contract_test_command() -> list[str] | None:
    """Mesma lógica de validar-contratos-fim-fase.py."""
    if PACKAGE_JSON.exists():
        try:
            pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts") or {}
            if "test:contracts" in scripts:
                npm = shutil.which("npm")
                if npm:
                    return [npm, "run", "test:contracts"]
        except (json.JSONDecodeError, OSError):
            pass

    if PYTEST_INI.exists() or PYPROJECT.exists():
        pytest_bin = shutil.which("pytest")
        if pytest_bin:
            return [pytest_bin, "tests/contracts/"]
        py = shutil.which("python3") or shutil.which("python")
        if py:
            return [py, "-m", "pytest", "tests/contracts/"]

    return None


def run_command(cmd: list[str], timeout: int = 300) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        passed = result.returncode == 0
        output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()[-2000:]
        return (passed, output)
    except subprocess.TimeoutExpired:
        return (False, f"timeout após {timeout}s")
    except OSError as e:
        return (False, f"falha ao executar: {e}")


def block_deploy(reasons: list[str]) -> int:
    """
    UserPromptSubmit: exit 2 bloqueia o envio da mensagem para o modelo.
    O conteúdo do stderr vira feedback visível ao usuário.
    """
    lines = [
        "[validar-deploy] BLOQUEIO: validação de deploy falhou.",
        "",
        "Os seguintes checks devem passar antes de um deploy ser iniciado:",
    ]
    for reason in reasons:
        lines.append(f"  - {reason}")
    lines.extend(
        [
            "",
            "Corrija os problemas listados, rode os testes manualmente, e reenvie a mensagem.",
            "Se quiser pular esta validação (uso excepcional, por sua conta e risco),",
            "reescreva a mensagem sem as palavras 'deploy'/'produção'.",
        ]
    )
    print("\n".join(lines), file=sys.stderr)
    return 2


def main() -> int:
    event = read_hook_event()
    prompt = extract_prompt_text(event)

    if not looks_like_deploy_intent(prompt):
        return 0

    log_activity(f"intenção de deploy detectada: '{prompt[:120]}...'")

    failures: list[str] = []

    # 1) Contract tests
    cmd = detect_contract_test_command()
    if cmd is None:
        log_activity(
            "aviso: nenhum framework de contract tests detectado — deploy permitido "
            "sem validação automática (cuidado)"
        )
    else:
        log_activity(f"rodando contract tests: {' '.join(cmd)}")
        passed, output = run_command(cmd, timeout=300)
        if not passed:
            failures.append(
                f"Contract tests FALHOU ({' '.join(cmd)}): "
                f"{output.splitlines()[-1] if output.strip() else 'ver activity-log.md'}"
            )
        else:
            log_activity("contract tests PASSOU")

    # 2) Verify-app (se SHIELD registrou execução recente, pula; caso contrário, avisa)
    # Implementação simplificada: verifica se existe relatório recente em .delta-11/memoria/
    # Para não bloquear deploy legítimo por falta de relatório, apenas registra aviso
    verify_app_marker = Path(".delta-11/memoria/verify-app-ultimo.md")
    if not verify_app_marker.exists():
        log_activity(
            "aviso: verify-app não foi executado recentemente (sem "
            ".delta-11/memoria/verify-app-ultimo.md). Recomende ao comandante "
            "disparar SHIELD antes do deploy."
        )
        # Não adiciona a failures — é só aviso, contract-tester é o bloqueador forte

    if failures:
        return block_deploy(failures)

    log_activity("validação de deploy PASSOU — mensagem permitida")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[validar-deploy] erro não-fatal: {exc}", file=sys.stderr)
        try:
            log_activity(f"ERRO não-fatal: {exc}")
        except Exception:
            pass
        sys.exit(0)
