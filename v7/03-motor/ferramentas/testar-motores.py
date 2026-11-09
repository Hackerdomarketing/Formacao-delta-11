#!/usr/bin/env python3
"""Pulso dos motores (ganchos/motor.py e ganchos/motores/): prova que os ganchos leem pelo tradutor do programa de
agentes sem mudar nada do que decidem.

(a) O espelho: o pulso da trava inteiro roda pelo tradutor do Claude Code, e cada chamada a um gancho (a trava, o
    relógio, o aviso de abertura, o registro de CRONOS e o do Documentador) dá o mesmo código e a mesma frase, inteira,
    gravados em amostras/espelho-da-trava.json (gravado da trava de antes do tradutor, commit 9c3e91f).
(b) Os eventos com todos os campos que o Claude Code de verdade manda (permission_mode, prompt_id, effort, tool_use_id,
    scratchpad_dir...; os da documentação dos ganchos, code.claude.com/docs/en/hooks, lida em 2026-11-09) dão o mesmo
    espelho; e o tradutor traduz cada tipo de evento como deve, sem nunca deduzir o programa pelos campos.
(c) Sem o programa dito no comando, ou com um que o motor não conhece, a trava barra; os outros ganchos não fazem nada,
    e o aviso de abertura diz que a trava barra tudo.
(d) Um pedido que escreve dois arquivos (como o patch do Codex vai trazer) barra se um deles é proibido, em qualquer
    ordem, também na pausa do dono; os dois permitidos passam.

Uso: python3 testar-motores.py   (sai com 1 se algo não sair como deve)
     python3 testar-motores.py --gravar-espelho [<pasta 03-motor de referência> ["<de onde veio>"]]
         grava o espelho de novo, com a trava daquela pasta (sem pasta, a atual). Só quando a trava muda de propósito:
         a diferença do arquivo no git mostra cada frase que mudou.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
FERRAMENTAS = MOTOR / "ferramentas"
ESPELHO = FERRAMENTAS / "amostras" / "espelho-da-trava.json"
PROGRAMA = "claude-code"
GANCHOS = ("trava.py", "relogio.py", "situacao.py", "cronos-vivo.py", "guardar-registro.py")
# Campos que o Claude Code manda e que não mudam o que os ganchos decidem (os que decidem, como session_id, cwd, agent_id,
# hook_event_name do registro de CRONOS e transcript_path, ficam como o pulso da trava os manda).
CAMPOS_REAIS = {
    "trava.py": {"hook_event_name": "PreToolUse", "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
                 "transcript_path": "/Users/dono/.claude/projects/-produto/abc123.jsonl", "scratchpad_dir": "/tmp/claude-501/-produto/abc123/scratchpad",
                 "permission_mode": "auto", "effort": {"level": "high"}, "tool_use_id": "toolu_01ABC123"},
    "relogio.py": {"hook_event_name": "PostToolUse", "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
                   "transcript_path": "/Users/dono/.claude/projects/-produto/abc123.jsonl", "permission_mode": "acceptEdits",
                   "effort": {"level": "xhigh"}, "tool_use_id": "toolu_01ABC123", "tool_response": {"filePath": "/x", "type": "create"}, "duration_ms": 12},
    "situacao.py": {"hook_event_name": "SessionStart", "transcript_path": "/Users/dono/.claude/projects/-produto/abc123.jsonl",
                    "model": "claude-opus-5", "seconds_since_last_response": 5400, "context_tokens": 182340,
                    "prompt_cache_likely_expired": True, "estimated_cache_write_usd": 1.1396},
    "cronos-vivo.py": {"permission_mode": "default", "stop_hook_active": False, "last_assistant_message": "Pronto.",
                       "background_tasks": [], "session_crons": []},
}


def carregar(arquivo: Path, nome: str):
    especificacao = importlib.util.spec_from_file_location(nome, arquivo)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def normalizar(texto: str, horas: bool = False) -> str:
    """Tira o que muda de uma vez para outra: a pasta temporária, a pasta pessoal e (no que o relógio e o aviso dizem) a hora."""
    base = tempfile.gettempdir()
    for pasta in sorted({base, str(Path(base).resolve())}, key=len, reverse=True):
        texto = re.sub(re.escape(pasta) + r"/tmp[\w-]+", "<TEMPORARIO>", texto)
    texto = texto.replace(str(Path.home()), "~")
    if horas:  # o aviso do relógio vem em JSON, com o acento escrito como é: as duas formas
        texto = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{4}", "<HORA>", texto)
        texto = re.sub(r"(h(?:á|\\u00e1) )\d+( minutos)", r"\1<N>\2", texto)
        texto = re.sub(r"(dormiu \d+ min, at(?:é|\\u00e9) )\d{2}:\d{2}", r"\1<HH:MM>", texto)
    return texto


def rodar_o_pulso_da_trava(motor_da_trava: Path, com_campos_reais: bool) -> tuple[int, list[dict], str]:
    """Roda o pulso da trava inteiro (com os ganchos de `motor_da_trava`), guardando cada chamada a um gancho e o que o
    pulso da trava imprimiu (para mostrar o caso que falhou, quando ele falha)."""
    pulso = carregar(FERRAMENTAS / "testar-trava.py", "pulso_da_trava")
    pulso.MOTOR = motor_da_trava
    chamadas: list[dict] = []
    original = subprocess.run

    def espiao(args, *a, **kw):
        gancho = next((Path(str(x)).name for x in args if Path(str(x)).name in GANCHOS), None) if isinstance(args, list) else None
        pedido = kw.get("input") or ""
        if gancho and com_campos_reais and gancho in CAMPOS_REAIS:
            try:
                evento = json.loads(pedido)
            except ValueError:
                evento = None
            if isinstance(evento, dict):  # o que o pulso manda vale; os campos a mais só entram onde ele não diz nada
                kw = {**kw, "input": json.dumps({**CAMPOS_REAIS[gancho], **evento})}
        feito = original(args, *a, **kw)
        if gancho:
            chamadas.append({"gancho": gancho, "pedido": normalizar(pedido), "codigo": feito.returncode,
                             "saida": normalizar(feito.stdout or "", horas=True), "erro": normalizar(feito.stderr or "")})
        return feito
    subprocess.run = espiao
    impresso = io.StringIO()
    try:
        with contextlib.redirect_stdout(impresso):
            codigo = pulso.main()
    finally:
        subprocess.run = original
    return codigo, chamadas, impresso.getvalue()


def guardar_a_falha(qual: str, codigo: int, impresso: str, erradas: list[str]) -> str:
    """Quando (a) ou (b) falha, grava tudo num arquivo no temporário e devolve o resumo: os casos ERRADO do pulso da
    trava e as primeiras chamadas que diferem do espelho (antes, a saída do pulso da trava era jogada fora)."""
    arquivo = Path(tempfile.gettempdir()) / f"testar-motores-falha-{qual}-{os.getpid()}.txt"
    casos = [linha.strip() for linha in impresso.splitlines() if "ERRADO" in linha or "FALHOU" in linha]
    arquivo.write_text(f"ponto: {qual}\no pulso da trava saiu: {codigo}\n\n== casos do pulso da trava que deram ERRADO ==\n"
                       + "\n".join(casos) + "\n\n== chamadas que diferem do espelho ==\n" + "\n".join(erradas)
                       + "\n\n== tudo o que o pulso da trava imprimiu ==\n" + impresso, encoding="utf-8")
    resumo = "; ".join(casos[:3] + erradas[:3]) or f"o pulso da trava saiu {codigo}"
    return f"{resumo} — detalhe completo em {arquivo}"


def resumo(chamada: dict) -> str:
    try:
        e = json.loads(chamada["pedido"])
    except ValueError:
        return f"{chamada['gancho']} com {chamada['pedido'][:60]!r}"
    if not isinstance(e, dict):
        return chamada["gancho"]
    return f"{chamada['gancho']}: {e.get('agent_type', '')} {e.get('tool_name', '') or e.get('hook_event_name', '') or e.get('source', '')} {json.dumps(e.get('tool_input', ''), ensure_ascii=False)[:90]}"


def comparar(gravadas: list[dict], agora: list[dict], qual: str) -> list[str]:
    falhas = []
    for i, (antes, depois) in enumerate(zip(gravadas, agora), 1):
        if (antes["gancho"], antes["pedido"]) != (depois["gancho"], depois["pedido"]):
            return falhas + [f"{qual}: na chamada {i}, o pulso da trava pediu outra coisa ({resumo(depois)}; o espelho tem {resumo(antes)}). "
                             "Se o pulso ou a trava mudaram de propósito, grave o espelho de novo (--gravar-espelho) e confira a diferença."]
        for campo, nome in (("codigo", "o código"), ("erro", "a frase"), ("saida", "a saída")):
            if antes[campo] != depois[campo]:
                falhas.append(f"{qual}: chamada {i} ({resumo(depois)}): {nome} era {str(antes[campo])[:300]!r}, agora {str(depois[campo])[:300]!r}")
    if len(gravadas) != len(agora):
        falhas.append(f"{qual}: o pulso da trava chamou os ganchos {len(agora)} vezes; o espelho tem {len(gravadas)}. "
                      "Se o pulso ganhou casos de propósito, grave o espelho de novo (--gravar-espelho).")
    return falhas


def motor_de_referencia(pasta: Path, destino: Path) -> Path:
    """Uma cópia de uma pasta 03-motor para o pulso da trava rodar com os ganchos dela (a de antes do tradutor não tem o
    motor.py, que o pulso copia: vai o atual, que os ganchos antigos não usam)."""
    shutil.copytree(pasta / "ganchos", destino / "ganchos", ignore=shutil.ignore_patterns("__pycache__", "vivos"))
    (destino / "agentes").mkdir(parents=True)
    shutil.copy2(pasta / "agentes" / "lugares.json", destino / "agentes" / "lugares.json")
    if not (destino / "ganchos" / "motor.py").is_file():
        shutil.copy2(MOTOR / "ganchos" / "motor.py", destino / "ganchos" / "motor.py")
        shutil.copytree(MOTOR / "ganchos" / "motores", destino / "ganchos" / "motores", ignore=shutil.ignore_patterns("__pycache__"))
    return destino


def gravar_espelho(referencia: Path, de_onde: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        codigo, chamadas, _ = rodar_o_pulso_da_trava(motor_de_referencia(referencia, Path(tmp) / "03-motor"), com_campos_reais=False)
    if codigo != 0:
        print("O pulso da trava não passou com essa trava: o espelho não foi gravado.")
        return 1
    if not de_onde:
        commit = subprocess.run(["git", "-C", str(referencia), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        de_onde = "a trava do motor" + (f" do commit {commit}" if commit else "") + ", pelo tradutor do Claude Code"
    ESPELHO.parent.mkdir(parents=True, exist_ok=True)
    ESPELHO.write_text(json.dumps({
        "o_que_e": "O que cada gancho do motor respondeu, chamada a chamada, ao pulso da trava (testar-trava.py), no Claude Code: "
                   "o código de saída, a saída e a frase de erro, sem a pasta temporária, a pasta pessoal e a hora. O pulso dos motores "
                   "(testar-motores.py) exige a mesma resposta pelo tradutor de cada programa de agentes.",
        "gravado_de": de_onde,
        "chamadas": chamadas}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ESPELHO GRAVADO — {len(chamadas)} chamadas aos ganchos, em {ESPELHO.relative_to(MOTOR)}.")
    return 0


def produto_pequeno(p: Path) -> Path:
    """Uma pasta de produto mínima, com a trava, o tradutor e o mapa, para os casos (c) e (d)."""
    ganchos = p / ".claude" / "hooks" / "delta-11"
    ganchos.mkdir(parents=True)
    for gancho in ("trava.py", "registro_de_cronos.py", "relogio.py", "situacao.py", "cronos-vivo.py", "guardar-registro.py", "motor.py"):
        shutil.copy2(MOTOR / "ganchos" / gancho, ganchos / gancho)
    shutil.copytree(MOTOR / "ganchos" / "motores", ganchos / "motores", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(MOTOR / "agentes" / "lugares.json", ganchos / "lugares.json")
    for pasta in ("src/telas", "banco", ".delta-11/quadro/camada-3/linhas", ".delta-11/regras", ".git"):
        (p / pasta).mkdir(parents=True, exist_ok=True)
    (p / ".git" / "config").write_text("x\n")
    (p / ".delta-11/quadro/camada-3/abertura.md").write_text("# Abertura\n")
    return ganchos


def main() -> int:
    if sys.argv[1:2] == ["--gravar-espelho"]:
        return gravar_espelho(Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else MOTOR, sys.argv[3] if len(sys.argv) > 3 else "")
    falhas: list[str] = []

    def conferir(nome: str, certo: bool, detalhe: str = "") -> None:
        print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else f" ({detalhe[:1500]})"))
        if not certo:
            falhas.append(nome)

    gravado = json.loads(ESPELHO.read_text(encoding="utf-8")) if ESPELHO.is_file() else {"chamadas": []}
    conferir("o espelho do Claude Code está gravado", bool(gravado["chamadas"]), f"falta {ESPELHO.relative_to(MOTOR)}: grave com --gravar-espelho")
    # (a) O espelho: o pulso da trava inteiro, pelo tradutor do Claude Code.
    codigo, chamadas, impresso = rodar_o_pulso_da_trava(MOTOR, com_campos_reais=False)
    erradas = comparar(gravado["chamadas"], chamadas, "espelho")
    travas = sum(1 for c in chamadas if c["gancho"] == "trava.py")
    certo = codigo == 0 and not erradas
    conferir(f"(a) espelho: o pulso da trava passa pelo tradutor, e as {len(chamadas)} chamadas aos ganchos ({travas} à trava) dão o mesmo código "
             f"e a mesma frase inteira que {gravado.get('gravado_de', 'o espelho')}", certo, "" if certo else guardar_a_falha("a", codigo, impresso, erradas))
    # (b) Com todos os campos do Claude Code de verdade.
    codigo, chamadas, impresso = rodar_o_pulso_da_trava(MOTOR, com_campos_reais=True)
    erradas = comparar(gravado["chamadas"], chamadas, "campos reais")
    certo = codigo == 0 and not erradas
    conferir("(b) com todos os campos que o Claude Code de verdade manda (permission_mode, prompt_id, effort, tool_use_id, scratchpad_dir, "
             "model...), cada chamada dá o mesmo espelho", certo, "" if certo else guardar_a_falha("b", codigo, impresso, erradas))
    motor = carregar(MOTOR / "ganchos" / "motor.py", "motor_do_pulso")
    comum = {"session_id": "abc123", "prompt_id": "550e8400-e29b-41d4-a716-446655440000", "transcript_path": "/u/.claude/projects/-p/abc123.jsonl",
             "cwd": "/u/produto", "scratchpad_dir": "/tmp/claude-501/-p/abc123/scratchpad", "permission_mode": "default", "effort": {"level": "high"}}
    escrita = {**comum, "hook_event_name": "PreToolUse", "agent_id": "a1", "agent_type": "FRONT", "tool_name": "Write",
               "tool_input": {"file_path": "/u/produto/src/a.js", "content": "x"}, "tool_use_id": "toolu_01ABC123"}
    pedido = motor.traduzir(escrita, PROGRAMA)
    conferir("(b) o tradutor do Claude Code: escrita vira o pedido comum (o programa dito, o papel em minúsculas, a entrada igual, um arquivo)",
             pedido["motor"] == PROGRAMA and pedido["evento"] == "antes" and pedido["papel"] == "front" and pedido["ferramenta"] == "Write"
             and pedido["dados"] is escrita["tool_input"] and pedido["arquivos"] == ["/u/produto/src/a.js"] and pedido["sessao"] == "abc123"
             and pedido["pasta"] == "/u/produto" and pedido["agente_id"] == "a1", repr(pedido))
    caderno = motor.traduzir({**escrita, "tool_name": "NotebookEdit", "tool_input": {"notebook_path": "/u/produto/n.ipynb", "new_source": "x"}}, PROGRAMA)
    terminal = motor.traduzir({**escrita, "tool_name": "Bash", "tool_input": {"command": "npm test", "description": "testes", "timeout": 120000}}, PROGRAMA)
    depois = motor.traduzir({**escrita, "hook_event_name": "PostToolUse", "tool_response": {"filePath": "/u/produto/src/a.js", "type": "create"}, "duration_ms": 12}, PROGRAMA)
    abertura = motor.traduzir({k: v for k, v in comum.items() if k not in ("permission_mode", "effort", "prompt_id")}
                              | {"hook_event_name": "SessionStart", "source": "resume", "model": "claude-opus-5", "agent_type": "atlas"}, PROGRAMA)
    inicio = motor.traduzir({**comum, "hook_event_name": "SubagentStart", "agent_id": "agent-abc123", "agent_type": "cronos"}, PROGRAMA)
    fim = motor.traduzir({**comum, "hook_event_name": "SubagentStop", "stop_hook_active": False, "agent_id": "def456", "agent_type": "Cronos",
                          "agent_transcript_path": "/u/.claude/projects/-p/abc123/subagents/agent-def456.jsonl", "last_assistant_message": "Pronto.",
                          "background_tasks": [], "session_crons": []}, PROGRAMA)
    conferir("(b) o tradutor do Claude Code: caderno, terminal, depois da ferramenta, abertura e início e fim de agente",
             caderno["arquivos"] == ["/u/produto/n.ipynb"] and terminal["arquivos"] == [] and terminal["dados"]["command"] == "npm test"
             and depois["evento"] == "depois" and abertura["evento"] == "abertura" and abertura["origem"] == "resume" and abertura["papel"] == "atlas"
             and inicio["evento"] == "inicio-de-agente" and inicio["conversa_do_agente"] == "/u/.claude/projects/-p/abc123/subagents/agent-agent-abc123.jsonl"
             and fim["evento"] == "fim-de-agente" and fim["papel"] == "cronos" and fim["conversa_do_agente"].endswith("/subagents/agent-def456.jsonl"),
             repr((caderno, terminal, depois, abertura, inicio, fim)))
    pegadinha = {**escrita, "turn_id": "t1", "kilo_agent_id": "k1"}  # os campos que o multiempresa usava para adivinhar o programa
    conferir("(b) o programa nunca é deduzido pelos campos: com permission_mode e hook_event_name (o defeito D1) e até com campos de outro "
             "programa, o pedido é do programa dito e igual", motor.traduzir(pegadinha, PROGRAMA) == pedido and "turn_id" not in json.dumps(pedido))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp).resolve() / "produto"
        ganchos = produto_pequeno(p)
        sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        ambiente = {**sem_git, "CLAUDE_PROJECT_DIR": str(p)}

        def gancho(nome: str, evento: dict, *programa: str, ambiente_do_gancho: dict | None = None) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-B", str(ganchos / nome), *programa], input=json.dumps(evento), capture_output=True,
                                  text=True, env=ambiente_do_gancho or ambiente)
        luz = {"agent_type": "atlas", "tool_name": "Write", "tool_input": {"file_path": str(p / ".delta-11/luz.md"), "content": "x"},
               "cwd": str(p), "session_id": "s1", "hook_event_name": "PreToolUse", "permission_mode": "default"}
        # (c) Sem o programa dito, a trava barra.
        com = gancho("trava.py", luz, PROGRAMA)
        sem = gancho("trava.py", luz)
        outro = gancho("trava.py", luz, "codex")
        maiusculo = gancho("trava.py", luz, "Claude-Code")
        conferir("(c) sem o programa dito no comando, a trava barra (o mesmo pedido, com claude-code, passa)",
                 com.returncode == 0 and sem.returncode == 2 and "TRAVA DO DELTA-11: o comando deste gancho não diz qual programa de agentes" in sem.stderr
                 and "recebeu 'nenhum'" in sem.stderr, f"{com.returncode} {com.stderr[:150]} / {sem.returncode} {sem.stderr[:200]}")
        conferir("(c) com um programa que o motor ainda não traduz (codex) ou escrito de outro jeito (Claude-Code), a trava barra",
                 outro.returncode == 2 and "recebeu 'codex'" in outro.stderr and maiusculo.returncode == 2 and "recebeu 'Claude-Code'" in maiusculo.stderr,
                 f"{outro.returncode} {outro.stderr[:150]} / {maiusculo.returncode}")
        quebrado = subprocess.run([sys.executable, "-B", str(ganchos / "trava.py")], input="isto não é json", capture_output=True, text=True, env=ambiente)
        conferir("(c) sem o programa dito, nem o pedido é lido: barra antes", quebrado.returncode == 2 and "não diz qual programa" in quebrado.stderr)
        relogio = gancho("relogio.py", {"agent_type": "atlas", "session_id": "s1", "tool_name": "Read"})
        abertura_sem = gancho("situacao.py", {"source": "startup", "session_id": "s1"})
        abertura_com = gancho("situacao.py", {"source": "startup", "session_id": "s1"}, PROGRAMA)
        vivos = ganchos / "vivos"
        antes_vivos = sorted(x.name for x in vivos.rglob("*.json")) if vivos.is_dir() else []
        cronos = gancho("cronos-vivo.py", {"hook_event_name": "SubagentStart", "agent_id": "a9", "agent_type": "arquiteto", "session_id": "s1"})
        depois_vivos = sorted(x.name for x in vivos.rglob("*.json")) if vivos.is_dir() else []
        conferir("(c) sem o programa dito, o relógio e o registro de CRONOS não fazem nada, e o aviso de abertura diz que a trava barra tudo",
                 relogio.returncode == 0 and relogio.stdout == "" and cronos.returncode == 0 and antes_vivos == depois_vivos
                 and "a9.json" not in depois_vivos and abertura_sem.returncode == 0 and "a trava barra tudo" in abertura_sem.stdout
                 and "não diz qual programa" in abertura_sem.stdout and "Situação do produto, contada pelo motor" in abertura_com.stdout,
                 f"{relogio.stdout[:100]!r} {depois_vivos} {abertura_sem.stdout[:200]!r}")
        com_relogio = gancho("relogio.py", {"agent_type": "atlas", "session_id": "s1", "tool_name": "Read"}, PROGRAMA)
        aviso = json.loads(com_relogio.stdout or "{}").get("hookSpecificOutput", {})
        conferir("(c) com o programa dito, o relógio avisa no formato do Claude Code (additionalContext depois da ferramenta)",
                 aviso.get("hookEventName") == "PostToolUse" and aviso.get("additionalContext", "").startswith("Hora agora (motor do Delta-11): "),
                 com_relogio.stdout[:200])
        # O registro do Documentador sem o programa dito: não guarda nada.
        git = lambda *a: subprocess.run(["git", "-C", str(p), *a], capture_output=True, text=True, env=sem_git)
        shutil.rmtree(p / ".git")
        git("init", "-q"); git("config", "user.email", "teste@exemplo"); git("config", "user.name", "teste")
        git("add", "-A"); git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "base")
        (p / ".delta-11" / "estado.md").write_text("estado\n")
        subprocess.run([sys.executable, "-B", str(ganchos / "guardar-registro.py")], input="{}", capture_output=True, text=True, env=ambiente)
        sem_guardar = git("log", "--format=%s").stdout.split("\n")[0]
        subprocess.run([sys.executable, "-B", str(ganchos / "guardar-registro.py"), PROGRAMA], input="{}", capture_output=True, text=True, env=ambiente)
        guardou = git("log", "--format=%s").stdout.split("\n")[0]
        conferir("(c) sem o programa dito, o registro do Documentador não guarda nada; com ele, guarda", sem_guardar == "base" and guardou == "registro do Delta-11",
                 f"{sem_guardar!r} {guardou!r}")
        # (d) Um pedido que escreve dois arquivos: o tradutor de um programa que manda vários (o patch do Codex) põe todos em `arquivos`.
        dois = ("import json, runpy, sys\n"
                "ganchos, trava, a_mais = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])\n"
                "sys.path.insert(0, ganchos)\n"
                "import motor\n"
                "ler = motor.ler\n"
                "def ler_com_mais(*args, **kwargs):\n"
                "    pedido = ler(*args, **kwargs)\n"
                "    pedido['arquivos'] = pedido['arquivos'] + a_mais\n"
                "    return pedido\n"
                "motor.ler = ler_com_mais\n"
                "sys.argv = [trava, sys.argv[4]]\n"
                "runpy.run_path(trava, run_name='__main__')\n")

        def escrever(papel: str, primeiro: str, *mais: str) -> subprocess.CompletedProcess:
            evento = {"agent_type": papel, "tool_name": "Edit", "cwd": str(p), "session_id": "s1", "hook_event_name": "PreToolUse",
                      "permission_mode": "auto", "tool_input": {"file_path": str(p / primeiro), "old_string": "a", "new_string": "b"}}
            return subprocess.run([sys.executable, "-B", "-c", dois, str(ganchos), str(ganchos / "trava.py"), json.dumps([str(p / m) for m in mais]), PROGRAMA],
                                  input=json.dumps(evento), capture_output=True, text=True, env=ambiente)
        for nome, papel, arquivos, motivo in [
                ("(d) dois arquivos, o segundo proibido (.git/), barra", "front", ("src/telas/a.js", ".git/config"), "não escreve em `.git/`"),
                ("(d) dois arquivos, o primeiro proibido, barra", "front", (".git/config", "src/telas/a.js"), "não escreve em `.git/`"),
                ("(d) dois arquivos, o segundo é a Luz (de outro papel), barra", "front", ("src/telas/a.js", ".delta-11/luz.md"), "não escreve em"),
                ("(d) dois arquivos do mesmo território passam", "front", ("src/telas/a.js", "src/telas/b.js"), None),
                ("(d) três arquivos, o do meio fora do território, barra (com territórios)", "front", ("src/telas/a.js", "banco/x.sql", "src/telas/b.js"),
                 "não fica nas pastas do território de front"),
                ("(d) a própria linha e a abertura (do ARQUITETO), barra", "cronos", (".delta-11/quadro/camada-3/quadro.md", ".delta-11/quadro/camada-3/abertura.md"),
                 "não escreve em `.delta-11/quadro/<X>/abertura.md`"),
                ("(d) na pausa, a própria linha sozinha passa", "front", (".delta-11/quadro/camada-3/linhas/front-1.md",), None),
                ("(d) na pausa, a própria linha e um arquivo do código, barra", "front", (".delta-11/quadro/camada-3/linhas/front-1.md", "src/telas/a.js"), "o dono pausou"),
                ("(d) na pausa, o código e depois a própria linha, barra", "front", ("src/telas/a.js", ".delta-11/quadro/camada-3/linhas/front-1.md"), "o dono pausou")]:
            if "território" in nome:
                (p / ".delta-11/regras/enderecos.txt").write_text("front src/telas/\nvault banco/\n")
            if "pausa" in nome:
                (p / ".delta-11/pausa.md").write_text("Situação: pausado\n")
            feito = escrever(papel, arquivos[0], *arquivos[1:])
            (p / ".delta-11/regras/enderecos.txt").unlink(missing_ok=True)
            (p / ".delta-11/pausa.md").unlink(missing_ok=True)
            certo = feito.returncode == 0 if motivo is None else (feito.returncode == 2 and motivo in feito.stderr)
            conferir(nome, certo, f"saiu {feito.returncode}: {feito.stderr.strip()[:200]}")
        so_um = escrever("front", "src/telas/a.js")
        conferir("(d) a mesma escrita com um arquivo só (o Claude Code) passa", so_um.returncode == 0, so_um.stderr[:200])
    if falhas:
        print(f"PULSO DOS MOTORES FALHOU — {len(falhas)}: " + "; ".join(falhas))
        return 1
    print("PULSO DOS MOTORES OK — os ganchos leem pelo tradutor do Claude Code e respondem igual, caso a caso; sem o programa dito, a trava barra; "
          "de dois arquivos, um proibido barra a ação.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
