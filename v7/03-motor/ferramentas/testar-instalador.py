#!/usr/bin/env python3
"""Pulso do instalador (ferramentas/instalar.py): instala em pastas descartáveis e confere o que tem de sair.

Confere a configuração que segura o motor (ATLAS principal, modo fork e equipes desligados, caixa de areia com porta
local e com as proibições de gravar, os ganchos), a configuração local (instruções pessoais de fora, caminho de busca),
os arquivos da trava, o commit da instalação, a limpeza do que furaria a caixa de areia e as recusas.
Uso: python3 testar-instalador.py   (sai com 1 se algo não sair como deve)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
INSTALAR = MOTOR / "ferramentas" / "instalar.py"


# Sem as variáveis GIT_* de um commit em andamento: dentro do gancho, elas apontariam o git do teste para o repositório real.
FORA_DA_CAIXA = json.loads((MOTOR / "porta-de-entrada" / "settings.json").read_text())["sandbox"]["excludedCommands"]
AMBIENTE = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
PROGRAMA = "claude-code"  # o programa de agentes padrão, que a instalação escreve no fim do comando de cada gancho


def situacao(pasta: Path) -> str:
    """O aviso de abertura da conversa, como o ATLAS o lê ao abrir a pasta (o comando do gancho diz o programa de agentes)."""
    return subprocess.run([sys.executable, "-B", str(pasta / ".claude/hooks/delta-11/situacao.py"), PROGRAMA], input="{}", capture_output=True, text=True,
                          env={**AMBIENTE, "CLAUDE_PROJECT_DIR": str(pasta)}).stdout


ULTIMAS_INSTALACOES: list[tuple[tuple[str, ...], subprocess.CompletedProcess]] = []


def instalar(*args: str) -> subprocess.CompletedProcess:
    feito = subprocess.run([sys.executable, "-B", str(INSTALAR), *args], capture_output=True, text=True, env=AMBIENTE)
    ULTIMAS_INSTALACOES.append((args, feito))
    del ULTIMAS_INSTALACOES[:-3]
    return feito


def mostrar_as_ultimas_instalacoes() -> None:
    """Quando um caso falha, o que o instalador disse nas últimas chamadas (sem isso, uma recusa inesperada só aparecia
    como um arquivo que faltava logo adiante, sem o motivo)."""
    for args, feito in ULTIMAS_INSTALACOES:
        print(f"      instalar {' '.join(args)} saiu {feito.returncode}: {(feito.stdout + feito.stderr).strip()[-1200:]}")


def main() -> int:
    try:
        return conferir_tudo()
    except Exception:  # um caso quebrou no meio: mostra o motivo e o que o instalador disse, em vez de só a linha do erro
        import traceback
        traceback.print_exc()
        mostrar_as_ultimas_instalacoes()
        print("PULSO DO INSTALADOR FALHOU — um caso quebrou no meio (acima, o erro e as últimas instalações).")
        return 1


def conferir_tudo() -> int:
    falhas: list[str] = []

    def conferir(nome: str, certo: bool) -> None:
        print(f"  {'ok' if certo else 'ERRADO'} — {nome}")
        if not certo:
            falhas.append(nome)
            mostrar_as_ultimas_instalacoes()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        # O pulso da esteira roda uma vez aqui; a marca (com a impressão digital da esteira e do pulso) poupa as instalações deste pulso.
        esteira = subprocess.run([sys.executable, "-I", "-B", str(MOTOR / "ferramentas" / "testar-esteira.py")], capture_output=True, text=True, env=AMBIENTE)
        conferir("a esteira do motor passa no pulso dela", esteira.returncode == 0)
        if esteira.returncode == 0:
            marca = tmp / ".pulso-da-esteira-passou"
            marca.write_text(hashlib.sha256((MOTOR / "esteira" / "esteira").read_bytes() + (MOTOR / "ferramentas" / "testar-esteira.py").read_bytes()).hexdigest())
            AMBIENTE["DELTA11_PULSO_DA_ESTEIRA_FEITO"] = str(marca)
        novo = tmp / "produto-novo"
        feito = instalar(str(novo))
        conferir("instala numa pasta nova", feito.returncode == 0)
        s = json.loads((novo / ".claude" / "settings.json").read_text())
        l = json.loads((novo / ".claude" / "settings.local.json").read_text())
        mapa = json.loads((MOTOR / "agentes" / "lugares.json").read_text())
        conferir("o ATLAS é o agente principal", s.get("agent") == "atlas")
        conferir("modo fork e equipes experimentais desligados", s.get("env", {}).get("CLAUDE_CODE_FORK_SUBAGENT") == "0"
                 and s.get("env", {}).get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "0")
        caixa = s.get("sandbox", {})
        conferir("caixa de areia ligada, sem saída e obrigatória", caixa.get("enabled") is True and caixa.get("allowUnsandboxedCommands") is False
                 and caixa.get("failIfUnavailable") is True)
        conferir("porta local liberada para servidor de teste", caixa.get("network", {}).get("allowLocalBinding") is True)
        conferir("o terminal de ninguém grava em .git/; só a esteira, a caixa do produto e a tela do app rodam fora da caixa de areia, com permissão",
                 ".git" in caixa.get("filesystem", {}).get("denyWrite", []) and caixa.get("excludedCommands") == FORA_DA_CAIXA
                 and all(f"Bash({c})" in s.get("permissions", {}).get("allow", []) for c in FORA_DA_CAIXA))
        conferir("o Node usa o caminho de rede da caixa de areia", s.get("env", {}).get("NODE_USE_ENV_PROXY") == "1")
        conferir("o terminal não grava em .delta-11/, na esteira nem nos arquivos de controle",
                 set(mapa["lugares_que_o_terminal_nao_grava"]) <= set(caixa.get("filesystem", {}).get("denyWrite", [])))
        ganchos = s.get("hooks", {})
        conferir("trava em toda ferramenta, barrando se falhar", any(
            "trava.py" in h["command"] and h.get("onFailure") == "block" for g in ganchos.get("PreToolUse", []) for h in g["hooks"]))
        conferir("aviso de abertura, relógio, registro de CRONOS e do Documentador", all(e in ganchos for e in
                 ("SessionStart", "PostToolUse", "SubagentStart", "SubagentStop")))
        conferir("instruções pessoais de fora", str(Path.home() / ".claude" / "CLAUDE.md") in l.get("claudeMdExcludes", []))
        conferir("caminho de busca do terminal", bool(l.get("env", {}).get("PATH")))
        conferir("o terminal de ninguém lê o teste guardado, o cofre e o leitor", set(mapa["lugares_que_o_terminal_nao_le"]) <= set(caixa.get("filesystem", {}).get("denyRead", [])))
        conferir("o .env fica fora do git", ".env" in (novo / ".gitignore").read_text().splitlines())
        trava = novo / ".claude" / "hooks" / "delta-11"
        conferir("arquivos da trava instalados", all((trava / a).is_file() for a in
                 ("trava.py", "registro_de_cronos.py", "situacao.py", "relogio.py", "cronos-vivo.py", "guardar-registro.py", "caixa-do-produto.py",
                  "tela-do-app.py", "lugares.json")) and any("tela-do-app.py" in c for c in FORA_DA_CAIXA))
        conferir("tabela de territórios e contrato da esteira nos modelos", (novo / ".delta-11/motor/modelos/territorios.md").is_file()
                 and (novo / ".delta-11/motor/modelos/esteira.md").is_file())
        log = subprocess.run(["git", "-C", str(novo), "log", "--oneline"], capture_output=True, text=True, env=AMBIENTE).stdout
        status = subprocess.run(["git", "-C", str(novo), "status", "--short"], capture_output=True, text=True, env=AMBIENTE).stdout
        conferir("a instalação vira commit e a pasta fica limpa", "instalado" in log and not status.strip())
        git_novo = lambda *a: subprocess.run(["git", "-C", str(novo), *a], capture_output=True, text=True, env=AMBIENTE).stdout
        da_esteira = (MOTOR / "esteira" / "esteira").read_text()
        conferir("a esteira do motor vai para a raiz, no commit `Delta-11: instalado`", (novo / "esteira").read_text() == da_esteira
                 and git_novo("show", "HEAD:esteira") == da_esteira and git_novo("log", "-1", "--format=%B").strip().endswith("Delta-11: instalado"))
        comandos = novo / "esteira-comandos.txt"
        conferir("o modelo de esteira-comandos.txt nasce na raiz, sem `testar:` (a esteira recusa até o BACK escrevê-lo), e entra no commit",
                 comandos.is_file() and all(l.startswith("#") for l in comandos.read_text().splitlines() if l.strip())
                 and git_novo("show", "HEAD:esteira-comandos.txt") == comandos.read_text())
        aviso = situacao(novo)
        conferir("com esteira-comandos.txt sem `testar:`, o aviso de abertura diz ao ATLAS que a esteira recusa tudo (e nada de esteira própria)",
                 "a esteira recusa tudo até os comandos serem escritos" in aviso and "esteira que o produto tinha" not in aviso)
        conferir("o modelo da automação do repositório vai nos modelos", (novo / ".delta-11/motor/modelos/esteira-automacao.yml").read_text()
                 == (MOTOR / "esteira" / "esteira-automacao.yml").read_text())
        # O programa de agentes é dito na instalação, nunca adivinhado: na VERSAO e, à vista, no fim do comando de cada gancho.
        do_delta = [h["command"] for grupos in ganchos.values() for g in grupos for h in g["hooks"] if "/.claude/hooks/delta-11/" in h["command"]]
        conferir("o programa de agentes (claude-code, o padrão) fica na VERSAO e no fim do comando de cada gancho do Delta-11",
                 json.loads((novo / ".delta-11/motor/VERSAO").read_text()).get("motor") == PROGRAMA and len(do_delta) >= 5
                 and all(c.endswith(".py " + PROGRAMA) for c in do_delta))
        conferir("o tradutor vai junto com a trava e entra no commit (motor.py e o tradutor do Claude Code)",
                 (trava / "motor.py").is_file() and (trava / "motores" / "claude_code.py").is_file()
                 and ".claude/hooks/delta-11/motores/claude_code.py" in git_novo("ls-files").split())
        caches = subprocess.run([sys.executable, "-I", "-B", "-c", "import importlib.util, sys; from pathlib import Path; "
                                 "s = importlib.util.spec_from_file_location('caixa', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                                 "print(chr(10).join(str(c) for c in m.caches_liberados(Path(sys.argv[2]))))",
                                 str(trava / "caixa-do-produto.py"), str(novo)], capture_output=True, text=True, env=AMBIENTE).stdout.splitlines()
        conferir("a caixa do produto lê pelo tradutor os caches que a caixa de areia do Claude Code libera",
                 caches == [str(Path(c).expanduser()) for c in caixa.get("filesystem", {}).get("allowWrite", [])] and len(caches) > 1)
        sem_tradutor = tmp / "programa-sem-tradutor"
        feito = instalar("--motor", "codex", str(sem_tradutor))
        conferir("recusa um programa de agentes que o motor ainda não traduz (--motor codex), sem mexer em nada",
                 feito.returncode != 0 and "'codex'" in feito.stdout and not sem_tradutor.exists())

        furada = tmp / "fura-caixa"
        (furada / ".claude").mkdir(parents=True)
        (furada / ".claude" / "settings.json").write_text('{"sandbox":{"excludedCommands":["sh"],"allowAllUnixSockets":true,"enableWeakerNestedSandbox":true,'
                                                          '"network":{"allowUnixSockets":["/var/run/docker.sock"]},"filesystem":{"allowWrite":["/"]}},"disableAllHooks":true}')
        (furada / ".claude" / "settings.local.json").write_text('{"disableAllHooks":true,"agent":"general-purpose","sandbox":{"enabled":false,"excludedCommands":["python3"]},'
                                                                '"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}')
        instalar(str(furada))
        s2 = json.loads((furada / ".claude" / "settings.json").read_text())
        l2 = json.loads((furada / ".claude" / "settings.local.json").read_text())
        c2 = s2.get("sandbox", {})
        conferir("tira o que furaria a caixa de areia e a trava", c2.get("excludedCommands") == FORA_DA_CAIXA and "disableAllHooks" not in s2
                 and "allowAllUnixSockets" not in c2 and "enableWeakerNestedSandbox" not in c2 and "allowUnixSockets" not in c2.get("network", {})
                 and "/" not in c2.get("filesystem", {}).get("allowWrite", []) and "disableAllHooks" not in l2 and "agent" not in l2
                 and l2.get("sandbox", {}).get("enabled") is not False and "excludedCommands" not in l2.get("sandbox", {})
                 and "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" not in l2.get("env", {}))

        travada = tmp / "regras-que-travam"
        (travada / ".claude").mkdir(parents=True)
        (travada / ".claude" / "settings.json").write_text('{"permissions":{"defaultMode":"plan","deny":["Agent","Bash(sh esteira *)","Bash(python3 -I -B .claude/hooks/delta-11/tela-do-app.py *)","Read(./segredo)"],"ask":["Write"]},'
                                                           '"env":{"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH":"1"}}')
        instalar(str(travada))
        s3 = json.loads((travada / ".claude" / "settings.json").read_text())
        conferir("tira as regras que desligariam o motor e mantém as outras", "defaultMode" not in s3.get("permissions", {})
                 and s3["permissions"].get("deny") == ["Read(./segredo)"] and not s3["permissions"].get("ask")
                 and "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH" not in s3.get("env", {}))
        ignora_delta = tmp / "ignora-delta"
        ignora_delta.mkdir()
        subprocess.run(["git", "init", "-q", str(ignora_delta)], env=AMBIENTE)
        (ignora_delta / ".gitignore").write_text(".delta-11/\n")
        subprocess.run(["git", "-C", str(ignora_delta), "add", "-A"], env=AMBIENTE)
        subprocess.run(["git", "-C", str(ignora_delta), "-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "base"], env=AMBIENTE)
        feito = instalar(str(ignora_delta))
        rastreados = subprocess.run(["git", "-C", str(ignora_delta), "ls-files"], capture_output=True, text=True, env=AMBIENTE).stdout
        conferir("instala numa pasta que ignorava .delta-11/ (o motor e o registro entram no git, o cofre não)",
                 feito.returncode == 0 and ".delta-11/motor/VERSAO" in rastreados and ".delta-11/cofre" not in rastreados)
        ignora = tmp / "ignora-claude"
        ignora.mkdir()
        subprocess.run(["git", "init", "-q", str(ignora)], env=AMBIENTE)
        (ignora / ".gitignore").write_text(".claude/\n")
        subprocess.run(["git", "-C", str(ignora), "add", "-A"], env=AMBIENTE)
        subprocess.run(["git", "-C", str(ignora), "-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "base"], env=AMBIENTE)
        feito = instalar(str(ignora))
        rastreados = subprocess.run(["git", "-C", str(ignora), "ls-files"], capture_output=True, text=True, env=AMBIENTE).stdout
        conferir("instala numa pasta que ignorava .claude/ (o motor entra no git)", feito.returncode == 0 and ".claude/hooks/delta-11/trava.py" in rastreados)
        com_agente = tmp / "com-agente"
        (com_agente / ".claude" / "agents").mkdir(parents=True)
        (com_agente / "CLAUDE.md").write_text("# outro sistema\n")
        (com_agente / ".claude" / "agents" / "atlas.md").write_text("---\nname: atlas\n---\n")
        feito = instalar(str(com_agente))
        conferir("recusa agente de outro sistema sem mexer em nada", feito.returncode != 0 and (com_agente / "CLAUDE.md").is_file()
                 and not (com_agente / ".delta-11").exists() and not (com_agente / ".git").exists())
        md = tmp / "ignora-md"
        md.mkdir()
        subprocess.run(["git", "init", "-q", str(md)], env=AMBIENTE)
        (md / ".gitignore").write_text("*.md\n")
        subprocess.run(["git", "-C", str(md), "add", "-A"], env=AMBIENTE)
        subprocess.run(["git", "-C", str(md), "-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "base"], env=AMBIENTE)
        feito = instalar(str(md))
        rastreados = subprocess.run(["git", "-C", str(md), "ls-files"], capture_output=True, text=True, env=AMBIENTE).stdout
        conferir("instala numa pasta que ignorava *.md (os modelos, a Luz e os agentes entram no git)", feito.returncode == 0
                 and ".delta-11/motor/modelos/esteira.md" in rastreados and ".claude/agents/atlas.md" in rastreados and "CLAUDE.md" in rastreados.split())
        velho = tmp / "gitignore-antigo"
        velho.mkdir()
        subprocess.run(["git", "init", "-q", str(velho)], env=AMBIENTE)
        (velho / ".gitignore").write_text(".claude/\n.claude/settings.local.json\n.delta-11/cofre/\nsub/\n")
        (velho / "sub" / "dep").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(velho / "sub" / "dep")], env=AMBIENTE)  # um repositório dentro do produto (submódulo, dependência)
        subprocess.run(["git", "-C", str(velho), "add", ".gitignore"], env=AMBIENTE)
        subprocess.run(["git", "-C", str(velho), "-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "base"], env=AMBIENTE)
        feito = instalar(str(velho))
        ignora = lambda c: subprocess.run(["git", "-C", str(velho), "check-ignore", "-q", c], env=AMBIENTE).returncode == 0
        conferir("instala num produto com .gitignore antigo e repositório dentro: o cofre e a configuração local seguem fora do git",
                 feito.returncode == 0 and ignora(".delta-11/cofre/x") and ignora(".claude/settings.local.json") and not ignora(".claude/agents/atlas.md"))
        metade = tmp / "com-trabalho-pela-metade"
        subprocess.run(["git", "init", "-q", str(metade)], env=AMBIENTE)
        (metade / "app.js").write_text("pela metade\n")
        feito = instalar(str(metade))
        conferir("recusa pasta com trabalho sem commit, sem mexer em nada", feito.returncode != 0 and not (metade / ".delta-11").exists())
        conferir("a tabela das camadas vai nos modelos", (novo / ".delta-11/motor/modelos/camadas.md").is_file())
        conferir("recusa pasta pessoal", instalar(str(tmp / "Documents")).returncode != 0)
        # Pastas de mentira dentro da fonte do v7 (o repositório onde esta ferramenta mora) e dentro da fonte da v6.4.1 que o
        # registro indica: nenhuma das duas pode receber um produto. Se a recusa falhasse, a pasta nasceria lá: sai no fim.
        dentro_da_fonte = INSTALAR.parents[3] / "pasta-de-mentira-do-pulso-do-instalador"
        fonte_v6_do_registro = tmp / "fonte-v6-do-registro"
        (fonte_v6_do_registro / ".delta-11").mkdir(parents=True)
        registro_de_mentira = tmp / "registro-de-mentira.json"
        registro_de_mentira.write_text(json.dumps({"source": str(fonte_v6_do_registro), "projects": []}), encoding="utf-8")
        try:
            feito = instalar(str(dentro_da_fonte))
            conferir("recusa pasta dentro da fonte do v7 (o repositório onde o motor mora), sem criar nada",
                     feito.returncode != 0 and "fonte do v7" in feito.stdout + feito.stderr and not dentro_da_fonte.exists())
            feito = subprocess.run([sys.executable, "-B", str(INSTALAR), str(fonte_v6_do_registro / "produto-de-mentira")], capture_output=True, text=True,
                                   env={**AMBIENTE, "DELTA11_REGISTRY": str(registro_de_mentira)})
            conferir("recusa pasta dentro da fonte da v6.4.1 que o registro do sincronizador indica, sem criar nada",
                     feito.returncode != 0 and "fonte da v6.4.1" in feito.stdout + feito.stderr and not (fonte_v6_do_registro / "produto-de-mentira").exists())
        finally:
            shutil.rmtree(dentro_da_fonte, ignore_errors=True)
        varios = tmp / "pasta-de-projetos"
        (varios / "outro-projeto" / ".git").mkdir(parents=True)
        conferir("recusa pasta que guarda outros projetos", instalar(str(varios)).returncode != 0 and not (varios / ".delta-11").exists())
        conferir("recusa --atualizar sem o v7", instalar("--atualizar", str(tmp / "sem-v7")).returncode != 0)
        conferir("recusa reinstalar sem --atualizar", instalar(str(novo)).returncode != 0)
        (novo / ".claude/hooks/delta-11/guardar-registro.sh").write_text("#!/bin/sh\n")
        (novo / "esteira").write_text("#!/bin/sh\necho esteira de uma versão anterior\n")
        do_produto = "testar: sh testes/rodar.sh\ntestes: testes/\n"
        comandos.write_text(do_produto)
        git_novo("add", "esteira", "esteira-comandos.txt")
        git_novo("-c", "core.hooksPath=/dev/null", "commit", "-qm", "back: esteira-comandos.txt\n\nEsteira: entrou")
        primeira_atualizacao = instalar("--atualizar", str(novo))
        conferir("atualiza a pasta que já tem o v7", primeira_atualizacao.returncode == 0)
        if primeira_atualizacao.returncode != 0:  # para achar a causa quando falha (a falha de 2026-11-09 não se repetiu)
            print("      saída do instalador:\n      " + "\n      ".join((primeira_atualizacao.stdout + primeira_atualizacao.stderr).strip().splitlines()[-12:]))
        conferir("a atualização mantém o programa de agentes da pasta", json.loads((novo / ".delta-11/motor/VERSAO").read_text()).get("motor") == PROGRAMA)
        conferir("a atualização tira o gancho de uma versão anterior", not (novo / ".claude/hooks/delta-11/guardar-registro.sh").exists())
        conferir("com os comandos escritos, o aviso de abertura não fala mais da esteira que recusa tudo", "a esteira recusa tudo" not in situacao(novo))
        conferir("a atualização troca a esteira pela do motor, no commit `Delta-11: instalado`, e não sobrescreve esteira-comandos.txt",
                 (novo / "esteira").read_text() == da_esteira and git_novo("show", "HEAD:esteira") == da_esteira
                 and comandos.read_text() == do_produto and git_novo("show", "HEAD:esteira-comandos.txt") == do_produto
                 and git_novo("log", "-1", "--format=%B").strip().endswith("Delta-11: instalado"))
        # Atualizar com uma camada aberta: a lista do que está pela metade vai ao aviso de abertura (para o ARQUITETO).
        (novo / ".delta-11/quadro/camada-2").mkdir(parents=True, exist_ok=True)
        (novo / ".delta-11/quadro/camada-2/abertura.md").write_text("# Abertura\n")
        (novo / ".delta-11/quadro/camada-2/quadro.md").write_text("# Quadro\n\nSituação: esperando o dono\n")
        (novo / ".delta-11/esteira").mkdir(parents=True, exist_ok=True)
        (novo / ".delta-11/esteira/back-2026-10-25-020400-000.log").write_text("esteira do Delta-11 v7\n$ swift test\n")
        (novo / "Pela-metade.swift").write_text("// sem entrega\n")
        rodando = novo / ".delta-11/esteira/rodando"
        rodando.mkdir(parents=True, exist_ok=True)
        comeco = subprocess.run(["ps", "-o", "lstart=", "-p", str(os.getpid())], capture_output=True, text=True).stdout.strip()
        (rodando / f"back-{os.getpid()}").write_text("camada-2\n" + comeco + "\n")
        com_entrega = instalar("--atualizar", str(novo))
        conferir("atualizar com uma entrega rodando: recusa, sem mexer em nada", com_entrega.returncode != 0 and "entrega está rodando" in com_entrega.stdout + com_entrega.stderr)
        shutil.rmtree(rodando)
        atualizado = instalar("--atualizar", str(novo))
        aviso_metade = situacao(novo)
        conferir("atualizar com camada aberta: a lista (camada aberta, mudança sem entrega, entrega sem fim) vai ao aviso de abertura, para o ARQUITETO",
                 atualizado.returncode == 0 and "trabalho pela metade" in atualizado.stdout and "camada-2 (esperando o dono)" in aviso_metade
                 and "Pela-metade.swift" in aviso_metade and "back-2026-10-25-020400-000.log" in aviso_metade and "ARQUITETO" in aviso_metade
                 and (novo / "Pela-metade.swift").is_file())
        propria = tmp / "com-esteira-propria"
        (propria / "pulsos").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(propria)], env=AMBIENTE)
        (propria / "esteira").write_text("#!/bin/sh\n# a esteira que o produto construiu\nsh pulsos/todos.sh && git commit -qm entrou\n")
        (propria / "pulsos" / "todos.sh").write_text("echo pulso antigo\n")
        subprocess.run(["git", "-C", str(propria), "add", "-A"], env=AMBIENTE)
        subprocess.run(["git", "-C", str(propria), "-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "base"], env=AMBIENTE)
        feito = instalar(str(propria))
        aviso = situacao(propria)
        conferir("num produto com esteira própria, a do motor a troca, o pulso antigo fica, e o aviso de abertura diz ao ATLAS que os testes e pulsos antigos continuam no código",
                 feito.returncode == 0 and (propria / "esteira").read_text() == da_esteira and (propria / "pulsos" / "todos.sh").is_file()
                 and (propria / ".delta-11/motor/esteira-propria-trocada.md").is_file() and "a esteira recusa tudo até os comandos serem escritos" in aviso
                 and "os testes e pulsos antigos dela continuam no código" in aviso)
        casa = tmp / "casa"
        (casa / ".claude").mkdir(parents=True)
        (casa / ".claude" / "settings.json").write_text('{"sandbox":{"excludedCommands":["docker *","sh *"],"filesystem":{"allowWrite":["~/fora"]},'
                                                        '"enableWeakerNetworkIsolation":true}}')
        pessoal = tmp / "com-pessoal"
        feito = subprocess.run([sys.executable, "-B", str(INSTALAR), str(pessoal)], capture_output=True, text=True, env={**AMBIENTE, "DELTA11_PULSO_CONFIGURACAO_PESSOAL": str(casa / ".claude" / "settings.json")})
        l4 = json.loads((pessoal / ".claude" / "settings.local.json").read_text()) if feito.returncode == 0 else {}
        conferir("desfaz na pasta os afrouxamentos da configuração pessoal, sem barrar a esteira",
                 "Bash(docker *)" in l4.get("permissions", {}).get("deny", []) and "Bash(sh *)" not in l4.get("permissions", {}).get("deny", [])
                 and str(Path.home() / "fora") in l4.get("sandbox", {}).get("filesystem", {}).get("denyWrite", [])
                 and l4.get("sandbox", {}).get("enableWeakerNetworkIsolation") is False and "sh *" in feito.stdout + feito.stderr)
        # O programa dito por extenso; e uma pasta instalada antes do tradutor (sem o programa na VERSAO nem nos comandos), atualizada.
        dito = tmp / "com-programa-dito"
        feito = instalar("--motor", PROGRAMA, str(dito))
        comandos_de = lambda pasta: [h["command"] for grupos in json.loads((pasta / ".claude/settings.json").read_text()).get("hooks", {}).values()
                                     for g in grupos for h in g["hooks"] if "/.claude/hooks/delta-11/" in h["command"]]
        conferir("instala com --motor claude-code dito por extenso", feito.returncode == 0 and f"programa de agentes: {PROGRAMA}" in feito.stdout
                 and json.loads((dito / ".delta-11/motor/VERSAO").read_text()).get("motor") == PROGRAMA
                 and all(c.endswith(".py " + PROGRAMA) for c in comandos_de(dito)))
        versao = json.loads((dito / ".delta-11/motor/VERSAO").read_text())
        versao.pop("motor")
        (dito / ".delta-11/motor/VERSAO").write_text(json.dumps(versao, indent=1) + "\n")
        configuracao = (dito / ".claude/settings.json").read_text()
        (dito / ".claude/settings.json").write_text(configuracao.replace(".py " + PROGRAMA + '"', '.py"'))
        sem_programa = not any(c.endswith(PROGRAMA) for c in comandos_de(dito))  # como era antes do tradutor
        aviso_sem_programa = subprocess.run([sys.executable, "-B", str(dito / ".claude/hooks/delta-11/situacao.py")], input="{}", capture_output=True,
                                            text=True, env={**AMBIENTE, "CLAUDE_PROJECT_DIR": str(dito)}).stdout
        feito = instalar("--atualizar", str(dito))
        conferir("uma pasta instalada antes do tradutor (sem o programa nos comandos): o aviso de abertura diz que a trava barra tudo; "
                 "a atualização põe o claude-code na VERSAO e nos comandos",
                 sem_programa and "a trava barra tudo" in aviso_sem_programa and feito.returncode == 0
                 and json.loads((dito / ".delta-11/motor/VERSAO").read_text()).get("motor") == PROGRAMA
                 and all(c.endswith(".py " + PROGRAMA) for c in comandos_de(dito)))
    if falhas:
        print(f"PULSO DO INSTALADOR FALHOU — {len(falhas)}: " + "; ".join(falhas))
        return 1
    print("PULSO DO INSTALADOR OK — a configuração que segura o motor sai inteira, e as recusas recusam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
