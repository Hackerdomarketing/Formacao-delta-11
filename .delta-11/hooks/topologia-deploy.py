#!/usr/bin/env python3
"""
Vigia "topologia de deploy" — Delta-11 v6.3 (2026-10-14). Item C-040.

Furo 9 da auditoria 2026-08-11: o deploy [publicar o sistema na internet] supos um
sistema so ("worker ok, painel 404"). Antes de publicar, o projeto precisa
declarar a sua topologia (quais partes existem e onde ficam).

Quando age (C-040): so no comando REAL de deploy, no evento Bash (PreToolUse com
matcher que inclui Bash). Escrever a palavra "deploy" em documento, kanban, ADR
ou no artefato descanso-04-deploy-auto NAO bloqueia mais.

Comandos reconhecidos (cada trecho separado por &&, ||, ;, | ou quebra de linha,
inclusive depois de `npx`, `pnpm dlx`, `bunx` e variaveis tipo `ENV=x`):
  wrangler deploy · wrangler pages deploy · vercel deploy · vercel --prod ·
  netlify deploy · firebase deploy · fly deploy / flyctl deploy · railway up ·
  supabase functions deploy · npm/pnpm/yarn/bun run deploy (e `pnpm deploy`)
Nao contam: `--dry-run`, `--help`, `echo "... deploy"`, `git commit -m "deploy"`,
`grep deploy` etc.

Topologia aceita: `.delta-11/memoria/topologia.json` da pasta principal com PELO
MENOS UMA URL (app com uma parte so e valido): worker_url, api_url, pages_url,
admin_url, app_url, site_url, url, ou uma lista `servicos` nao vazia.

Erro interno: libera a acao, registra ERRO-INTERNO no activity-log e avisa no
stderr (exit 1) — ver _comum.run.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as comum  # noqa: E402

HOOK = "topologia-deploy"
CAMPOS_URL = ("worker_url", "api_url", "pages_url", "admin_url", "app_url", "site_url", "url")
PREFIXOS_IGNORADOS = {"npx", "bunx", "sudo", "env", "time", "exec"}
SEPARADORES_RE = re.compile(r"&&|\|\||;|\||\n")


def tokens_of(trecho: str) -> list[str]:
    try:
        partes = shlex.split(trecho, posix=True)
    except ValueError:
        partes = trecho.split()
    while partes and (partes[0] in PREFIXOS_IGNORADOS or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", partes[0])):
        partes = partes[1:]
    if len(partes) >= 2 and partes[0] in {"pnpm", "yarn"} and partes[1] == "dlx":
        partes = partes[2:]
    return partes


def is_deploy_segment(partes: list[str]) -> bool:
    if not partes:
        return False
    if any(p in {"--dry-run", "--help", "-h"} for p in partes):
        return False
    programa = os.path.basename(partes[0])
    resto = partes[1:]
    if programa == "wrangler":
        return "deploy" in resto[:2] or resto[:1] == ["publish"]
    if programa == "vercel":
        return "deploy" in resto[:1] or "--prod" in resto
    if programa in {"netlify", "firebase", "fly", "flyctl"}:
        return resto[:1] == ["deploy"]
    if programa == "railway":
        return resto[:1] == ["up"]
    if programa == "supabase":
        return resto[:2] == ["functions", "deploy"]
    if programa in {"npm", "pnpm", "yarn", "bun"}:
        if resto[:2] == ["run", "deploy"] or resto[:1] == ["deploy"]:
            return True
        return bool(resto[:1] == ["run"] and len(resto) > 1 and resto[1].startswith("deploy:"))
    return False


def deploy_commands(comando: str) -> list[str]:
    achados = []
    for trecho in SEPARADORES_RE.split(comando or ""):
        if is_deploy_segment(tokens_of(trecho.strip())):
            achados.append(trecho.strip())
    return achados


def topology_ok() -> bool:
    arquivo = comum.delta_dir() / "memoria" / "topologia.json"
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(dados, dict):
        return False
    if any(isinstance(dados.get(c), str) and dados.get(c).strip() for c in CAMPOS_URL):
        return True
    servicos = dados.get("servicos")
    return isinstance(servicos, (list, dict)) and len(servicos) > 0


def message(comandos: list[str]) -> str:
    return (
        f"[{HOOK}] BLOQUEIO {comum.VERSAO} — deploy sem topologia declarada\n"
        f"\n"
        f"Comando de deploy: {comandos[0][:160]}\n"
        f"\n"
        f"Antes de publicar, declare as partes do sistema em\n"
        f".delta-11/memoria/topologia.json (pasta principal). Exemplos:\n"
        f'  App de uma parte:   {{"app_url": "https://app.seu-projeto.com"}}\n'
        f'  Worker + painel:    {{"worker_url": "https://api.seu-projeto.com",\n'
        f'                        "pages_url": "https://admin.seu-projeto.com",\n'
        f'                        "deploy_cmd_worker": "wrangler deploy",\n'
        f'                        "deploy_cmd_pages": "wrangler pages deploy"}}\n'
        f"Com varias partes, publique TODAS e confira cada URL depois.\n"
    )


def main() -> int:
    evento = comum.read_event()
    if evento.get("tool_name") != "Bash":
        return 0
    comandos = deploy_commands(comum.tool_input(evento).get("command") or "")
    if not comandos:
        return 0
    if topology_ok():
        comum.log(HOOK, f"OK: deploy com topologia declarada: {comandos[0][:80]}")
        return 0
    return comum.block(HOOK, message(comandos), f"deploy sem topologia.json: {comandos[0][:80]}")


if __name__ == "__main__":
    comum.run(main, HOOK)
