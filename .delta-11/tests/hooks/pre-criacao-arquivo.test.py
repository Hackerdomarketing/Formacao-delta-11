#!/usr/bin/env python3
"""
Testes do hook pre-criacao-arquivo.py (guarda de zoneamento documental).

Estes são os 9 casos do F2 (auditoria v5.3) já validados, migrados para a
suíte automatizada do Estágio 0. Cada caso monta um evento JSON sintético
que imita o que o Claude Code envia via stdin no PreToolUse(Write), executa
o hook em um diretório-temporário isolado, e confere:

  - exit code (0 = liberar, 2 = bloquear)
  - trecho da mensagem de erro (quando bloqueia)

Casos cobertos:
  1. Criar docs/configuracao-kimi-moonshot.md  → BLOQUEIA (CASO A — caso Kimi)
  2. Criar config-openai.md em docs/           → BLOQUEIA (CASO A — prefixo config-)
  3. Criar setup-stripe.md em docs/            → BLOQUEIA (CASO A — prefixo setup-)
  4. Criar README.md na raiz                   → LIBERA  (exceção B)
  5. Criar plano-de-marketing.md na raiz       → BLOQUEIA (CASO B — .md na raiz)
  6. Criar doc-legado/skills/qualquer.md       → BLOQUEIA (CASO C — pasta legada)
  7. Criar src/lib/ia/analise/README.md        → LIBERA  (destino correto config-ext)
  8. Criar adr-2026-01-15-stack-escolhida.md na raiz → BLOQUEIA (CASO D — ADR)
  9. Criar bug-001-login-quebrado.md na raiz   → BLOQUEIA (CASO E — bug report)

Saída: exit 0 se todos os 9 passam, exit 1 se algum falha.

IMPORTANTE — isola cada caso em diretório /tmp temporário para não
poluir o repo real e não disparar a guarda em si quando o hook lê
os arquivos de escape.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent.parent / "hooks" / "pre-criacao-arquivo.py"


def fazer_evento(file_path: str, cwd: str) -> str:
    """Monta payload JSON idêntico ao que o Claude Code envia."""
    return json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "# teste"},
        "cwd": cwd,
    })


def rodar_hook(file_path: str, cwd: str) -> tuple[int, str]:
    """Executa o hook com o evento e retorna (exit_code, stderr)."""
    evento = fazer_evento(file_path, cwd)
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=evento.encode("utf-8"),
        capture_output=True,
        cwd=cwd,
        timeout=10,
    )
    return proc.returncode, proc.stderr.decode("utf-8", errors="replace")


def preparar_tmp() -> tuple[str, str]:
    """Cria diretório-temporário com .delta-11/ mínimo (sem escape)."""
    tmp = Path(tempfile.mkdtemp(prefix="delta11-test-"))
    (tmp / ".delta-11").mkdir()
    return str(tmp), str(tmp)


CASOS = [
    # (id, caminho_relativo, esperado_exit, trecho_esperado_no_stderr)
    ("F2-01-caso-kimi",            "docs/configuracao-kimi-moonshot.md",                2, "CASO A"),
    ("F2-02-caso-A-prefixo-config","docs/config-openai.md",                              2, "CASO A"),
    ("F2-03-caso-A-prefixo-setup", "docs/setup-stripe.md",                               2, "CASO A"),
    ("F2-04-excecao-README-raiz",  "README.md",                                          0, None),
    ("F2-05-caso-B-md-na-raiz",    "plano-de-marketing.md",                              2, "CASO B"),
    ("F2-06-caso-C-skills-legada", "skills/qualquer.md",                                 2, "CASO C"),
    ("F2-07-destino-correto",      "src/lib/ia/analise/README.md",                       0, None),
    ("F2-08-caso-D-ADR-fora",      "adr-2026-01-15-stack-escolhida.md",                  2, "CASO D"),
    ("F2-09-caso-E-bug-fora",      "bug-001-login-quebrado.md",                          2, "CASO E"),
]


def main() -> int:
    if not HOOK_PATH.exists():
        print(f"[FAIL] hook nao encontrado em {HOOK_PATH}")
        return 1

    tmp_dir, cwd = preparar_tmp()
    passou = 0
    falhou = 0

    try:
        for caso_id, rel_path, esperado_exit, trecho in CASOS:
            alvo_abs = os.path.join(tmp_dir, rel_path)
            # garantir que o path NAO existe (hook libera se já existe)
            if os.path.exists(alvo_abs):
                os.remove(alvo_abs)

            code, stderr = rodar_hook(alvo_abs, cwd)

            ok_code = (code == esperado_exit)
            ok_trecho = True
            if trecho:
                ok_trecho = trecho in stderr

            if ok_code and ok_trecho:
                print(f"  [OK]   {caso_id}")
                passou += 1
            else:
                motivo = []
                if not ok_code:
                    motivo.append(f"exit esperado={esperado_exit} obtido={code}")
                if not ok_trecho:
                    motivo.append(f"trecho '{trecho}' nao encontrado em stderr")
                print(f"  [FAIL] {caso_id}: {'; '.join(motivo)}")
                if stderr:
                    print(f"        stderr: {stderr[:200]}")
                falhou += 1

        print()
        if falhou == 0:
            print(f"[OK]   pre-criacao-arquivo: {passou}/{len(CASOS)} casos passaram")
            return 0
        else:
            print(f"[FAIL] pre-criacao-arquivo: {passou}/{len(CASOS)} passaram, {falhou} falharam")
            return 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())