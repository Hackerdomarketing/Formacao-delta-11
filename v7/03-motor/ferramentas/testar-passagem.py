#!/usr/bin/env python3
"""Pulso da passagem do v6 para o v7 (instalar.py --passar-do-v6): prova a passagem caso a caso, só em pastas descartáveis.

Monta projetos do Delta-11 v6 de mentira (com git, sem git, dentro de um git maior, com conversa aberta), com a forma dos
projetos reais, e prova: o ensaio e as recusas não mudam nada (impressão digital de tudo igual); a passagem real guarda
tudo antes de mudar (marca, commits, cópias de agentes, .tar.gz) e não perde nenhum arquivo (as listas batem); nenhum
segredo entra em commit; a gaveta fica fora do git; o sincronizador antigo não toca no projeto passado; a trava do v7
deixa o ATLAS ler a gaveta, barra todos de escrever nela e barra o Revisor de lê-la; e uma falha no meio devolve a pasta.

As variáveis de ambiente que só este pulso usa (e que o instalador documenta):
  DELTA11_REGISTRY                      o registro de mentira (o real nunca é tocado)
  DELTA11_COPIAS_ANTES_DO_V7            a pasta de mentira das cópias .tar.gz
  DELTA11_PULSO_LSOF_DE_MENTIRA         uma saída de mentira do `lsof` (só vale com o nome e a primeira linha certos)
  DELTA11_PULSO_DO_MOTOR_FEITO          a marca de que a trava, a tela e os agentes passaram no pulso (com a digital do motor)
  DELTA11_PULSO_DA_ESTEIRA_FEITO        a marca do pulso da esteira (a mesma do pulso do instalador)
  DELTA11_PULSO_PASSAGEM_FALHAR_DEPOIS_DE   faz a passagem falhar de propósito depois de um passo, para provar a volta
Uso: python3 testar-passagem.py   (sai com 1 se algo não sair como deve)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unicodedata
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
INSTALAR = MOTOR / "ferramentas" / "instalar.py"
PROGRAMA = "claude-code"
AMBIENTE = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
SINCRONIZADOR_OFICIAL = Path.home() / "Documents" / "VSCODE" / "Formacao-delta-11"
FRASE_DA_ABERTURA = ("Este produto veio do Delta-11 antigo. Antes de começar a Luz, leia `.delta-11/anterior-v6/PONTO-DE-PARTIDA.md` e comece a "
                     "conversa da Luz pelo meio: mostre ao dono, em poucas linhas, o que o produto é e onde parou, e peça que ele confirme ou corrija.")
MARCA_LSOF = "# pulso da passagem do v6: saída de mentira do lsof"
GANCHOS_DO_V6 = ['bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/heartbeat.sh"', 'node "$CLAUDE_PROJECT_DIR/.delta-11/hooks/log-activity.js"',
                 'python3 "$CLAUDE_PROJECT_DIR/.delta-11/hooks/pre-selo.py"']
GANCHO_DO_DONO = "say terminei"
DOIS_DIAS = 2 * 24 * 3600


# ───────────── ferramentas do pulso ─────────────

def git(pasta: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True, env=AMBIENTE)


def git_de_mentira(pasta: Path, *args: str) -> subprocess.CompletedProcess:
    return git(pasta, "-c", "user.name=Dono de Mentira", "-c", "user.email=dono@mentira.invalid", "-c", "commit.gpgsign=false",
               "-c", "core.hooksPath=/dev/null", *args)


def digital(raiz: Path, com_datas: bool = True, sem_git: bool = False) -> str:
    """Caminho, tamanho, data, permissão e conteúdo de tudo (o que `sincronizar.test.sh` faz): qualquer mudança muda o resultado."""
    h = hashlib.sha256()
    for pasta, subpastas, arquivos in os.walk(raiz):
        subpastas.sort()
        if sem_git:
            subpastas[:] = [s for s in subpastas if s != ".git"]
        for nome in sorted(subpastas + arquivos):
            caminho = os.path.join(pasta, nome)
            st = os.lstat(caminho)
            e_arquivo = os.path.isfile(caminho) and not os.path.islink(caminho)
            h.update(f"{os.path.relpath(caminho, raiz)}|{st.st_size if e_arquivo else 0}|{st.st_mtime_ns if com_datas else 0}|{st.st_mode:o}\n".encode())
            if e_arquivo:
                h.update(Path(caminho).read_bytes())
            elif os.path.islink(caminho):
                h.update(os.readlink(caminho).encode())
    return h.hexdigest()


def lista_de_arquivos(raiz: Path) -> dict[str, str]:
    """Cada arquivo (e link) com o hash do conteúdo: para provar que nada se perdeu."""
    achados = {}
    for pasta, subpastas, arquivos in os.walk(raiz):
        subpastas[:] = sorted(s for s in subpastas if s != ".git")  # a história muda de propósito; o que se prova é o que está em arquivo
        for nome in sorted(arquivos):
            caminho = Path(pasta) / nome
            achados[caminho.relative_to(raiz).as_posix()] = os.readlink(caminho) if caminho.is_symlink() else hashlib.sha256(caminho.read_bytes()).hexdigest()
    return achados


def envelhecer(pasta: Path) -> None:
    """Todo arquivo do projeto passa a ter dois dias: nenhum sinal de conversa aberta por acaso."""
    velho = time.time() - DOIS_DIAS
    for raiz, subpastas, arquivos in os.walk(pasta):
        subpastas[:] = [s for s in subpastas if s != ".git"]
        for nome in arquivos:
            os.utime(Path(raiz) / nome, (velho, velho), follow_symlinks=False)


def escrever(pasta: Path, relativo: str, texto: str) -> None:
    alvo = pasta / relativo
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")


# ───────────── os projetos v6 de mentira (com a forma dos projetos reais que passam do v6) ─────────────

KANBAN_PREENCHIDO = """# KANBAN — FORMAÇÃO Δ-11

**Projeto:** Loja de Teste
**Complexidade:** MÉDIA
**Fase atual:** Fase 3 — Construção das telas do carrinho
**Última atualização:** 2026-10-20 ATLAS

## 📋 BACKLOG (tarefas não atribuídas)

<!-- T-001 virou tarefa do FRONT -->

## 🏗️ ATLAS — A FAZER

### T-010 — Escrever o contrato de pagamentos

## 🎨 PIXEL — A FAZER

### T-011 — Ajustar as cores do botão de compra
- [ ] Revisar o espaçamento da vitrine
- [x] Item já feito que não deve aparecer

## ⚡ FAZENDO

<!-- T-099 saiu de FAZENDO em 2026-10-20 -->

### T-020 — FRONT — Tela de carrinho

## 👁️ REVISÃO

### T-021 — SHIELD — Revisar o cálculo de frete

## ✅ CONCLUÍDO

### T-001 — ATLAS — Escolher o banco (concluída)
"""

KANBAN_EM_BRANCO = """# KANBAN — FORMAÇÃO Δ-11

**Projeto:** [preenchido pelo ATLAS na Fase 2]
**Fase atual:** [preenchido pelo ATLAS]

## 🏗️ ATLAS — A FAZER

<!-- Tarefas de planejamento e arquitetura -->

## ⚡ FAZENDO

## 👁️ REVISÃO
"""

PROJECT_CORE_PREENCHIDO = """# MEMÓRIA CENTRAL DO PROJETO — FORMAÇÃO Δ-11

## PROJETO

**Nome:** Loja de Teste
**Descrição:** Uma loja de camisetas que vende pelo celular, com carrinho e pagamento por Pix.
**Usuários-alvo:** donas de pequenos negócios que vendem roupa
**Problema que resolve:** vender sem depender de marketplace e sem pagar comissão alta
"""

PROJECT_CORE_EM_BRANCO = """# MEMÓRIA CENTRAL DO PROJETO — FORMAÇÃO Δ-11

## PROJETO

**Nome:** [preenchido pelo ATLAS]
**Descrição:** [o que o sistema faz, em 2-3 frases]
**Usuários-alvo:** [para quem é]
**Problema que resolve:** [qual dor resolve]
"""

GOTCHAS = """# Gotchas do Projeto

## G-001: Supabase retorna lista vazia sem erro quando RLS bloqueia
> Semente do projeto. Fonte canônica desta lição: outro arquivo.
- **Registrado por:** exemplo
- **EVITE:** tratar `data: []` como "não existem registros"

## G-002: O frete só calcula depois do CEP
- **Registrado por:** FORM
- **EVITE:** chamar o cálculo de frete antes de o cliente digitar o CEP

## G-003: Imagens da vitrine precisam de largura fixa
- **Registrado por:** PIXEL
- **EVITE:** deixar a imagem sem largura, o painel quebra no celular
"""

CLAUDE_MD_DO_V6 = """<!-- MOTOR:CODIGO-INICIO -->
# FORMAÇÃO Δ-11 — instruções do sistema antigo (v6)

Você é um operativo da Formação Δ-11. ATLAS lê o kanban e distribui tarefas.
<!-- MOTOR:CODIGO-FIM -->
"""

AGENTS_MD_DO_MULTIEMPRESA = "## ⚡ ATIVAÇÃO DELTA-11 — PRIORIDADE ABSOLUTA (LER ANTES DE TUDO)\n\nVocê é um operativo da Formação Δ-11 (motor Codex).\n"


def escrever_v6(pasta: Path, preenchido: bool) -> None:
    """A pasta `.delta-11/` do v6 e os arquivos de sistema na raiz (sem git: o chamador decide o resto)."""
    d = ".delta-11/"
    escrever(pasta, d + "kanban.md", KANBAN_PREENCHIDO if preenchido else KANBAN_EM_BRANCO)
    escrever(pasta, d + "memoria/project-core.md", PROJECT_CORE_PREENCHIDO if preenchido else PROJECT_CORE_EM_BRANCO)
    if preenchido:
        escrever(pasta, d + "memoria/decisoes/2026-10-14-usar-banco-simples.md", "# ADR: Usar um banco simples para o carrinho\n\nContexto...\n")
        escrever(pasta, d + "memoria/decisoes/2026-10-15-pagar-por-pix.md", "# Pagar por Pix antes do cartão\n\nContexto...\n")
    else:
        (pasta / d / "memoria" / "decisoes").mkdir(parents=True, exist_ok=True)
    escrever(pasta, d + "memoria/gotchas.md", GOTCHAS)
    escrever(pasta, d + "memoria/ATLAS-estado.md", "# Estado do ATLAS\n")
    escrever(pasta, d + "operativos/ATLAS.md", "# ATLAS do v6\n")
    escrever(pasta, d + "protocolos/regras.md", "# regras do v6\n")
    escrever(pasta, d + "hooks/heartbeat.sh", "#!/bin/sh\n")
    escrever(pasta, d + "hooks/pre-selo.py", "print('vigia do v6')\n")
    escrever(pasta, d + "templates/modelo.md", "# modelo\n")
    escrever(pasta, d + "motor/CONTRATO.md", "# contrato do motor multiempresa\n")
    escrever(pasta, d + "scripts/monitor-delta11.sh", "#!/bin/sh\n")
    escrever(pasta, d + "ativacoes/agentes-sessao.json",
             json.dumps({"versao": 1, "chaves": {"agente:a1": {"agente": "SHIELD", "visto_em": "2026-10-17T10:44:51Z", "encerrado_em": "2026-10-17T10:44:51Z"}}}))
    escrever(pasta, d + "logs/autocritica/um.md", "log\n")
    escrever(pasta, d + "evidencias/prova.txt", "prova\n")
    escrever(pasta, d + "painel.html", "<html>painel do v6</html>\n")
    escrever(pasta, d + "monitor-status.json", "{}\n")
    escrever(pasta, d + "monitor-data.js", "window.m = {};\n")
    escrever(pasta, d + "activity-log.md", "# atividade\n")
    (pasta / d / "scratch").mkdir(parents=True, exist_ok=True)
    (pasta / d / "scratch" / "enorme.bin").write_bytes(b"\0" * (2 * 1024 * 1024))  # grande o bastante para notar
    escrever(pasta, "CLAUDE.md", CLAUDE_MD_DO_V6)
    escrever(pasta, ".claude/settings.json", json.dumps({"model": "opus", "hooks": {
        "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": GANCHOS_DO_V6[0], "timeout": 5}, {"type": "command", "command": GANCHOS_DO_V6[1]}]}],
        "PreToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": GANCHOS_DO_V6[2]}]}],
        "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": GANCHO_DO_DONO}, {"type": "command", "command": GANCHOS_DO_V6[0]}]}]}}, indent=2) + "\n")
    escrever(pasta, ".kilo/agent/atlas.md", "agente do multiempresa\n")
    escrever(pasta, ".kilo/agent/back.md", "agente do multiempresa\n")
    escrever(pasta, ".kilo/permissoes.json", '{"permissions": {}}\n')
    escrever(pasta, ".kilo/settings.json", '{"do": "dono"}\n')
    escrever(pasta, "AGENTS.md", AGENTS_MD_DO_MULTIEMPRESA)
    escrever(pasta, ".codex/hooks.json", json.dumps({"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
        {"type": "command", "command": GANCHOS_DO_V6[2]}, {"type": "command", "command": "echo gancho do dono do codex"}]}]}}, indent=2) + "\n")


def projeto_v6_de_mentira(pasta: Path, tipo: str, **opcoes) -> dict:
    """tipo: com-git, sem-git, dentro-de-git-maior, com-conversa-aberta (opção sinal: agentes-sessao, quadro, lsof)."""
    pasta.mkdir(parents=True)
    fatos: dict = {"pasta": pasta}
    if tipo in ("com-git", "com-conversa-aberta"):
        git_de_mentira(pasta, "init", "-q", "-b", "main")
        escrever(pasta, ".gitignore", "node_modules/\n.delta-11/scratch/\n.delta-11/evidencias/\n.delta-11/logs/\n.delta-11/ativacoes/\n.claude/worktrees/\n")
        escrever(pasta, "package.json", '{"name": "loja-de-teste"}\n')
        escrever(pasta, "src/app.js", "console.log('loja');\n")
        escrever(pasta, "CLAUDE.md", "# As minhas instruções do projeto\n")
        escrever(pasta, ".env.example", "CHAVE=\n")
        git_de_mentira(pasta, "add", "-A")
        git_de_mentira(pasta, "commit", "-q", "-m", "projeto de mentira")
        if tipo == "com-git":
            for nome in ("agent-suja", "agent-limpa"):
                git_de_mentira(pasta, "worktree", "add", "-q", "-b", f"worktree-{nome}", f".claude/worktrees/{nome}")
        escrever_v6(pasta, preenchido=True)
        escrever(pasta, ".env", "CHAVE=segredo-de-mentira-1\n")
        escrever(pasta, "config/credentials.json", '{"chave": "segredo-de-mentira-2"}\n')
        escrever(pasta, "src/novo.js", "// trabalho sem commit\n")
        if tipo == "com-git":
            suja = pasta / ".claude/worktrees/agent-suja"
            (suja / "src/app.js").write_text("console.log('mudado na cópia');\n")
            escrever(suja, "src/trabalho-novo.js", "// trabalho da cópia, sem commit\n")
            escrever(suja, ".env", "CHAVE=segredo-de-mentira-3\n")
            fatos["suja"], fatos["limpa"] = suja, pasta / ".claude/worktrees/agent-limpa"
    elif tipo == "sem-git":
        escrever_v6(pasta, preenchido=False)
        escrever(pasta, "src/app.js", "console.log('app');\n")
    elif tipo == "dentro-de-git-maior":
        git_de_mentira(pasta.parent, "init", "-q", "-b", "main")
        escrever(pasta.parent, "outro-arquivo.txt", "do git maior\n")
        git_de_mentira(pasta.parent, "add", "outro-arquivo.txt")
        git_de_mentira(pasta.parent, "commit", "-q", "-m", "git maior")
        escrever_v6(pasta, preenchido=True)
        escrever(pasta, "index.html", "<html></html>\n")
    envelhecer(pasta)
    if tipo == "com-conversa-aberta":
        sinal = opcoes.get("sinal", "agentes-sessao")
        if sinal == "agentes-sessao":
            arquivo = pasta / ".delta-11/ativacoes/agentes-sessao.json"
            dados = json.loads(arquivo.read_text())
            dados["chaves"]["agente:vivo"] = {"agente": "FRONT", "visto_em": "2026-11-09T01:21:00Z"}  # sem encerrado_em
            arquivo.write_text(json.dumps(dados))
        elif sinal == "quadro":
            (pasta / ".delta-11/kanban.md").write_text(KANBAN_PREENCHIDO + "\n<!-- mudou agora -->\n")
    return fatos


def registro_de_mentira(caminho: Path, projetos: list[Path]) -> None:
    caminho.write_text(json.dumps({"version": "6.4.1", "source": "/fonte/de/mentira", "backup": None, "projects": [str(p) for p in projetos] + ["/outro/projeto"],
                                   "observacao": {"nao": "mexer"}}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ───────────── o instalador como o pulso o chama ─────────────

class Rodada:
    def __init__(self, base: Path, marcas: dict[str, str]) -> None:
        self.base = base
        self.registro = base / "registro.json"
        self.copias = base / "copias-antes-do-v7"
        self.marcas = marcas

    def ambiente(self, extra: dict | None = None) -> dict:
        return {**AMBIENTE, "DELTA11_REGISTRY": str(self.registro), "DELTA11_COPIAS_ANTES_DO_V7": str(self.copias), **self.marcas, **(extra or {})}

    def passar(self, pasta: Path, *opcoes: str, extra: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(INSTALAR), "--passar-do-v6", str(pasta), *opcoes], capture_output=True, text=True, env=self.ambiente(extra))

    def digital_de_tudo(self) -> str:
        return digital(self.base)


def saida(feito: subprocess.CompletedProcess) -> str:
    return feito.stdout + feito.stderr


def preparar_marcas(tmp: Path, falhas_do_preparo: list[str]) -> dict[str, str]:
    """Roda uma vez os pulsos que a passagem exigiria a cada rodada (a esteira, a trava, a tela sem janela e os agentes) e deixa as
    marcas, com a digital do que foi provado: a passagem as aceita no lugar de rodar tudo de novo em cada projeto de mentira."""
    especificacao = importlib.util.spec_from_file_location("instalar_do_pulso", INSTALAR)
    instalador = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(instalador)
    marcas: dict[str, str] = {}
    externa = Path(os.environ.get("DELTA11_PULSO_DA_ESTEIRA_FEITO") or "/nenhuma")
    if instalador.esteira_ja_provada():
        marcas["DELTA11_PULSO_DA_ESTEIRA_FEITO"] = str(externa)
    else:
        esteira = subprocess.run([sys.executable, "-I", "-B", str(MOTOR / "ferramentas" / "testar-esteira.py")], capture_output=True, text=True, env=AMBIENTE)
        if esteira.returncode != 0:
            falhas_do_preparo.append("o pulso da esteira não passou: " + esteira.stdout.strip()[-200:])
        marca = tmp / ".pulso-da-esteira-passou"
        marca.write_text(instalador.digital_da_esteira())
        marcas["DELTA11_PULSO_DA_ESTEIRA_FEITO"] = str(marca)
    if instalador.motor_ja_provado():
        marcas["DELTA11_PULSO_DO_MOTOR_FEITO"] = os.environ["DELTA11_PULSO_DO_MOTOR_FEITO"]
    else:
        for script, opcao in (("montar-agentes.py", ["--conferir"]), ("testar-trava.py", []), ("testar-tela-do-app.py", ["--sem-janela"])):
            feito = subprocess.run([sys.executable, "-B", str(MOTOR / "ferramentas" / script), *opcao], capture_output=True, text=True, env=AMBIENTE)
            if feito.returncode != 0:
                falhas_do_preparo.append(f"o pulso {script} não passou: " + feito.stdout.strip()[-200:])
        marca = tmp / ".pulso-do-motor-passou"
        marca.write_text(instalador.digital_do_motor())
        marcas["DELTA11_PULSO_DO_MOTOR_FEITO"] = str(marca)
    return marcas


# ───────────── os casos ─────────────

def main() -> int:
    falhas: list[str] = []

    def conferir(nome: str, certo: bool, detalhe: str = "") -> None:
        print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo or not detalhe else f"\n      {detalhe}"))
        if not certo:
            falhas.append(nome)

    def seguro(nome: str, funcao) -> None:
        try:
            funcao()
        except Exception as erro:  # o pulso mostra o caso quebrado e segue com os outros
            conferir(nome, False, f"o pulso quebrou: {type(erro).__name__}: {erro}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        preparo: list[str] = []
        marcas = preparar_marcas(tmp, preparo)
        conferir("os pulsos que a passagem exigiria (esteira, trava, tela sem janela, agentes) passam e deixam a marca", not preparo, "; ".join(preparo))
        rodada = Rodada(tmp / "sandbox", marcas)
        (rodada.base).mkdir()

        # ── 1. o ensaio não muda nada (nem o projeto, nem o registro, nem a pasta de cópias) e mostra os números ──
        def caso_ensaio() -> None:
            projeto = rodada.base / "ensaio-com-git"
            fatos = projeto_v6_de_mentira(projeto, "com-git")
            sem_git = rodada.base / "ensaio-sem-git"
            projeto_v6_de_mentira(sem_git, "sem-git")
            maior = rodada.base / "git-maior" / "ensaio-dentro"
            projeto_v6_de_mentira(maior, "dentro-de-git-maior")
            registro_de_mentira(rodada.registro, [projeto, sem_git, maior])
            itens = len(git(projeto, "status", "--porcelain").stdout.splitlines())  # (o status do pulso pode atualizar o índice: a foto vem depois)
            antes = rodada.digital_de_tudo()
            feito = rodada.passar(projeto, "--ensaio", "--guardar-copias")
            texto = saida(feito)
            arquivos = sum(1 for _, _, a in os.walk(projeto / ".delta-11") for _ in a)
            conferir("--ensaio (com git, com cópias): sai 0, diz que nada foi mudado e mostra os números", feito.returncode == 0 and "ENSAIO — nada foi mudado" in texto
                     and f"{itens} itens sem commit" in texto and f"{arquivos} arquivos" in texto and "4 ganchos do v6 sairiam de .claude/settings.json" in texto and "1 gancho do v6 sairia de .codex/hooks.json" in texto and "1 gancho do dono" in texto
                     and "2 cópias de agentes" in texto and "marca antes-do-v7" in texto and "segredos que passariam a ser ignorados: .env, config/credentials.json" in texto
                     and "Para fazer de verdade: rode o mesmo comando sem --ensaio." in texto, texto[-700:])
            conferir("--ensaio (com git, com cópias) não mudou NENHUM arquivo (projeto, cópias, registro, pasta de cópias)", rodada.digital_de_tudo() == antes)
            sem_as_copias = rodada.passar(projeto, "--ensaio")
            conferir("--ensaio sem --guardar-copias, com trabalho nas cópias: diz que a passagem seria recusada, sem mudar nada",
                     sem_as_copias.returncode == 1 and "seria RECUSADA" in saida(sem_as_copias) and "agent-suja" in saida(sem_as_copias) and rodada.digital_de_tudo() == antes)
            feito = rodada.passar(sem_git, "--ensaio", "--criar-git")
            texto = saida(feito)
            conferir("--ensaio (sem git, com --criar-git): mostra a cópia compactada e o git novo, descrição não preenchida, e não mudou nada",
                     feito.returncode == 0 and "cópia compactada" in texto and "criaria o git" in texto and "descrição não preenchida" in texto
                     and rodada.digital_de_tudo() == antes and not rodada.copias.exists(), texto[-600:])
            feito = rodada.passar(maior, "--ensaio", "--criar-git")
            conferir("--ensaio (dentro de um git maior): diz que o git maior passa a ver a pasta como repositório aninhado, sem mudar nada",
                     feito.returncode == 0 and "repositório aninhado" in saida(feito) and rodada.digital_de_tudo() == antes)
        seguro("o ensaio", caso_ensaio)

        # ── 2. cada recusa recusa com a frase certa e não muda nada ──
        def caso_recusas() -> None:
            antes_de_tudo = rodada.digital_de_tudo()
            ja_v7 = rodada.base / "recusa-ja-v7"
            escrever(ja_v7, ".delta-11/motor/VERSAO", '{"delta11": "v7", "motor": "claude-code"}\n')
            escrever(ja_v7, ".claude/hooks/delta-11/agentes-instalados.txt", "atlas.md\n")
            sem_v6 = rodada.base / "recusa-sem-v6"
            escrever(sem_v6, "src/app.js", "x\n")
            conferir("recusa pasta que já tem o v7: 'esta pasta já está no v7'", "esta pasta já está no v7" in saida(rodada.passar(ja_v7)) and rodada.passar(ja_v7).returncode == 1)
            conferir("recusa pasta sem o Delta-11 antigo: 'não achei o Delta-11 antigo nesta pasta'",
                     "não achei o Delta-11 antigo nesta pasta" in saida(rodada.passar(sem_v6)) and rodada.passar(sem_v6).returncode == 1)
            for sinal, frase in (("agentes-sessao", "vínculo de agente ainda aberto"), ("quadro", "o quadro mudou há")):
                p = rodada.base / f"recusa-conversa-{sinal}"
                projeto_v6_de_mentira(p, "com-conversa-aberta", sinal=sinal)
                feito = rodada.passar(p, "--criar-git")
                conferir(f"conversa aberta pelo sinal '{sinal}': recusa com 'tem uma conversa aberta desde HH:MM; feche-a quando o trabalho dela terminar e rode de novo'",
                         feito.returncode == 1 and re.search(r"tem uma conversa aberta desde \d\d:\d\d; feche-a quando o trabalho dela terminar e rode de novo", saida(feito)) is not None
                         and frase in saida(feito), saida(feito)[-400:])
            p = rodada.base / "recusa-conversa-lsof"
            projeto_v6_de_mentira(p, "com-conversa-aberta", sinal="nenhum")
            falso = rodada.base / "saida-de-lsof-de-mentira.txt"
            falso.write_text(f"{MARCA_LSOF}\n# inicio 01:21\np4242\nfcwd\nn{p / 'src'}\n", encoding="utf-8")
            feito = rodada.passar(p, extra={"DELTA11_PULSO_LSOF_DE_MENTIRA": str(falso)})
            conferir("conversa aberta pelo sinal do lsof (saída de mentira, com a pasta de trabalho dentro do projeto): recusa 'desde 01:21'",
                     feito.returncode == 1 and "tem uma conversa aberta desde 01:21; feche-a quando o trabalho dela terminar e rode de novo" in saida(feito), saida(feito)[-400:])
            falso_ruim = rodada.base / "qualquer-nome.txt"
            falso_ruim.write_text(f"{MARCA_LSOF}\np4242\nfcwd\nn{p / 'src'}\n", encoding="utf-8")
            feito = rodada.passar(p, "--criar-git", extra={"DELTA11_PULSO_LSOF_DE_MENTIRA": str(falso_ruim)})
            conferir("a saída de mentira do lsof só vale com o nome de arquivo certo (senão é ignorada, e o lsof de verdade não acha ninguém)",
                     "tem uma conversa aberta desde" not in saida(feito) and feito.returncode == 0, saida(feito)[-300:])
            antes_dos_outros = rodada.digital_de_tudo()
            projeto_v6_de_mentira(rodada.base / "recusa-copias", "com-git")
            feito = rodada.passar(rodada.base / "recusa-copias")
            conferir("cópias com mudança sem commit, sem --guardar-copias: recusa e lista quais ('agent-suja') e manda usar --guardar-copias",
                     feito.returncode == 1 and "agent-suja" in saida(feito) and "--guardar-copias" in saida(feito) and "agent-limpa" not in saida(feito).split("--guardar-copias")[0],
                     saida(feito)[-500:])
            adiantada = rodada.base / "recusa-ramo-nao-juntado"
            projeto_v6_de_mentira(adiantada, "com-git")
            git_de_mentira(adiantada / ".claude/worktrees/agent-limpa", "commit", "-q", "--allow-empty", "-m", "ficou na cópia")
            (adiantada / ".claude/worktrees/agent-suja/src/app.js").write_text("console.log('loja');\n")  # a suja volta a ficar igual
            git_de_mentira(adiantada / ".claude/worktrees/agent-suja", "clean", "-fdq")
            feito = rodada.passar(adiantada)
            conferir("ramo de cópia ainda não juntado ao principal, sem --guardar-copias: recusa e lista a cópia ('agent-limpa')",
                     feito.returncode == 1 and "agent-limpa" in saida(feito) and "não juntado" in saida(feito), saida(feito)[-400:])
            sem = rodada.base / "recusa-sem-git"
            projeto_v6_de_mentira(sem, "sem-git")
            antes_sem = rodada.digital_de_tudo()
            feito = rodada.passar(sem)
            conferir("sem git próprio e sem --criar-git: recusa e explica ('não tem git próprio', '--criar-git')",
                     feito.returncode == 1 and "não tem git próprio" in saida(feito) and "--criar-git" in saida(feito) and rodada.digital_de_tudo() == antes_sem, saida(feito)[-400:])
            maior = rodada.base / "git-maior-recusa" / "dentro"
            projeto_v6_de_mentira(maior, "dentro-de-git-maior")
            feito = rodada.passar(maior)
            conferir("pasta dentro de um git maior, sem --criar-git: conta como sem git próprio e recusa", feito.returncode == 1 and "não tem git próprio" in saida(feito)
                     and "git-maior-recusa" in saida(feito))
            registro_de_mentira(rodada.registro, [rodada.base / "ensaio-com-git"])
            depois = rodada.digital_de_tudo()
            sobrou = [rodada.passar(ja_v7), rodada.passar(sem_v6), rodada.passar(adiantada), rodada.passar(sem), rodada.passar(maior), rodada.passar(rodada.base / "recusa-conversa-agentes-sessao")]
            conferir("nenhuma recusa mudou NADA (projetos, registro e pasta de cópias com a mesma impressão digital)", rodada.digital_de_tudo() == depois
                     and all(f.returncode == 1 for f in sobrou) and not rodada.copias.exists())
        seguro("as recusas", caso_recusas)

        # ── 3. a passagem real num projeto com git e com cópias de agentes ──
        passado: dict = {}

        def caso_passagem_com_git() -> None:
            projeto = rodada.base / "passagem-com-git"
            fatos = projeto_v6_de_mentira(projeto, "com-git")
            outro = rodada.base / "outro-projeto-do-registro"
            outro.mkdir()
            registro_de_mentira(rodada.registro, [projeto, outro])
            registro_antes = json.loads(rodada.registro.read_text())
            antigos = lista_de_arquivos(projeto / ".delta-11")
            kanban_antigo = (projeto / ".delta-11/kanban.md").read_text()
            claude_antigo = (projeto / "CLAUDE.md").read_text()
            configuracao_antiga = (projeto / ".claude/settings.json").read_text()
            app_antigo = (projeto / "src/app.js").read_text()
            codex_antigo = (projeto / ".codex/hooks.json").read_text()
            feito = rodada.passar(projeto, "--guardar-copias")
            texto = saida(feito)
            passado.update(pasta=projeto, texto=texto)
            conferir("passagem real em projeto com git e cópias (--guardar-copias): termina com OK", feito.returncode == 0 and texto.lstrip().startswith("OK"), texto[-900:])
            tags = git(projeto, "tag").stdout.split()
            conferir("a marca antes-do-v7 existe e contém o estado anterior (o que estava sem commit, inclusive o quadro antigo e o src/novo.js)",
                     "antes-do-v7" in tags and git(projeto, "show", "antes-do-v7:.delta-11/kanban.md").stdout == kanban_antigo
                     and git(projeto, "show", "antes-do-v7:src/novo.js").returncode == 0 and git(projeto, "show", "antes-do-v7:CLAUDE.md").stdout == claude_antigo)
            mensagens = git(projeto, "log", "--format=%s", "-3").stdout.splitlines()
            conferir("os dois commits da passagem: 'passagem do Delta-11 v6 para o v7' por cima de 'estado antes do v7'",
                     mensagens[:2] == ["passagem do Delta-11 v6 para o v7", "estado antes do v7"], str(mensagens))
            conferir("o commit da passagem termina com a marca do instalador (a esteira não o trata como entrega)",
                     git(projeto, "log", "-1", "--format=%B").stdout.strip().endswith("Delta-11: instalado"))
            conferir("o trabalho da cópia suja está num commit do ramo dela ('trabalho da cópia guardado antes do v7', com o arquivo novo)",
                     git(projeto, "log", "-1", "--format=%s", "worktree-agent-suja").stdout.strip() == "trabalho da cópia guardado antes do v7"
                     and git(projeto, "show", "worktree-agent-suja:src/trabalho-novo.js").returncode == 0)
            gaveta = projeto / ".delta-11" / "anterior-v6"
            lista = git(projeto, "worktree", "list", "--porcelain").stdout
            conferir("as duas cópias estão em .delta-11/anterior-v6/copias-de-agentes/ e o git worktree list as acha lá, sem 'prunable'",
                     (gaveta / "copias-de-agentes/agent-suja/.git").is_file() and (gaveta / "copias-de-agentes/agent-limpa/.git").is_file()
                     and str(gaveta / "copias-de-agentes/agent-suja") in lista and str(gaveta / "copias-de-agentes/agent-limpa") in lista and "prunable" not in lista
                     and not (projeto / ".claude/worktrees/agent-suja").exists() and git(gaveta / "copias-de-agentes/agent-suja", "rev-parse", "HEAD").returncode == 0)
            todo = git(projeto, "log", "--all", "--format=%H", "--", ".env", "config/credentials.json").stdout.strip()
            conteudo = subprocess.run(["git", "-C", str(projeto), "grep", "-l", "segredo-de-mentira", *git(projeto, "rev-list", "--all").stdout.split()],
                                      capture_output=True, text=True, env=AMBIENTE).stdout.strip()
            conferir("os segredos (.env e config/credentials.json, na pasta e na cópia) não entraram em nenhum commit (git log --all e git grep em todo o histórico vazios)",
                     not todo and not conteudo and git(projeto, "check-ignore", "-q", ".env").returncode == 0 and git(projeto, "check-ignore", "-q", "config/credentials.json").returncode == 0
                     and git(projeto, "check-ignore", "-q", ".env.example").returncode != 0, todo + conteudo)
            novos = lista_de_arquivos(gaveta)
            faltando = [a for a in antigos if novos.get(a) != antigos[a]]
            conferir("a gaveta tem TODOS os arquivos da .delta-11 antiga, com o mesmo conteúdo (as listas batem, inclusive o scratch que o git ignorava)", not faltando, str(faltando[:5]))
            conferir("o .kilo/agent/, o .kilo/permissoes.json, o AGENTS.md do multiempresa e o CLAUDE.md do v6 estão em anterior-v6/raiz/ (o resto do .kilo/ fica)",
                     (gaveta / "raiz/.kilo/agent/atlas.md").is_file() and (gaveta / "raiz/.kilo/permissoes.json").is_file() and (gaveta / "raiz/AGENTS.md").is_file()
                     and (gaveta / "raiz/CLAUDE.md").read_text() == claude_antigo and not (projeto / ".kilo/agent").exists() and not (projeto / ".kilo/permissoes.json").exists()
                     and not (projeto / "AGENTS.md").exists() and (projeto / ".kilo/settings.json").is_file())
            conferir("o CLAUDE.md da raiz agora é o do v7, e o do v6 NÃO foi duplicado em instrucoes-anteriores (são regras do sistema antigo)",
                     (projeto / "CLAUDE.md").read_text().startswith("<!-- delta-11 v7") and not (projeto / ".delta-11/motor/instrucoes-anteriores").exists())
            configuracao = (projeto / ".claude/settings.json").read_text()
            codex = (projeto / ".codex/hooks.json").read_text()
            conferir("o .claude/settings.json e o .codex/hooks.json não têm comando com .delta-11/hooks/ e mantêm o gancho do dono; os originais ficam na gaveta",
                     ".delta-11/hooks/" not in configuracao.replace(".claude/hooks/delta-11/", "") and GANCHO_DO_DONO in configuracao and ".delta-11/hooks/" not in codex
                     and "gancho do dono do codex" in codex and (gaveta / "raiz/.claude/settings.json").read_text() == configuracao_antiga
                     and (gaveta / "raiz/.codex/hooks.json").read_text() == codex_antigo and "trava.py" in configuracao)
            versao = json.loads((projeto / ".delta-11/motor/VERSAO").read_text())
            conferir("a VERSAO diz v7, com o programa de agentes claude-code, e o motor está instalado", versao.get("delta11") == "v7" and versao.get("motor") == PROGRAMA
                     and (projeto / ".claude/hooks/delta-11/trava.py").is_file() and (projeto / ".claude/agents/atlas.md").is_file())
            ponto = (gaveta / "PONTO-DE-PARTIDA.md").read_text() if (gaveta / "PONTO-DE-PARTIDA.md").is_file() else ""
            posicoes = [ponto.find(s) for s in ("## O que o produto é", "## Onde parou", "## Decisões já tomadas", "## Avisos que o time antigo deixou")]
            conferir("o PONTO-DE-PARTIDA.md tem as 4 seções na ordem, a Fase atual, as tarefas abertas (sem as concluídas), as 2 decisões, os avisos próprios (sem o exemplo do modelo) e até 1.000 palavras",
                     all(p >= 0 for p in posicoes) and posicoes == sorted(posicoes) and "Fase 3 — Construção das telas do carrinho" in ponto and "T-020" in ponto and "T-021" in ponto
                     and "T-010" in ponto and "Revisar o espaçamento da vitrine" in ponto and "T-001" not in ponto and "Item já feito" not in ponto
                     and "Usar um banco simples para o carrinho" in ponto and "Pagar por Pix antes do cartão" in ponto and "O frete só calcula depois do CEP" in ponto
                     and "Supabase" not in ponto and "Loja de Teste" in ponto and len(ponto.split()) <= 1000
                     and "para voltar atrás, peça ao Claude: voltar este projeto para a marca antes-do-v7" in ponto, ponto[:600])
            conferir("git status --porcelain vazio depois da passagem", git(projeto, "status", "--porcelain").stdout.strip() == "", git(projeto, "status", "--porcelain").stdout[:300])
            verificacao = git(projeto, "check-ignore", "-v", ".delta-11/anterior-v6/kanban.md").stdout
            conferir("a gaveta está ignorada pelo git (check-ignore -v mostra a linha da gaveta, não uma exceção com !) e nada dela está no git; o motor do v7 não está ignorado",
                     ".delta-11/anterior-v6/" in verificacao and "\t.delta-11/anterior-v6/" in verificacao and not git(projeto, "ls-files", ".delta-11/anterior-v6").stdout.strip()
                     and git(projeto, "check-ignore", "-q", ".delta-11/motor/VERSAO").returncode != 0 and git(projeto, "check-ignore", "-q", ".delta-11/luz.md").returncode != 0, verificacao)
            registro = json.loads(rodada.registro.read_text())
            esperado = dict(registro_antes)
            esperado["projects"] = [p for p in registro_antes["projects"] if p != str(projeto)]
            conferir("o registro de mentira não lista mais a pasta e o resto do arquivo ficou igual", registro == esperado and str(projeto) not in rodada.registro.read_text(), rodada.registro.read_text()[:300])
            relato = gaveta / "RELATO-DA-PASSAGEM.md"
            textos = relato.read_text() if relato.is_file() else ""
            conferir("o relato existe na gaveta e diz o que foi guardado onde (marca, commit, ramos das cópias), o que foi para a gaveta, os ganchos, os segredos e como voltar",
                     "antes-do-v7" in textos and "worktree-agent-suja" in textos and "anterior-v6/raiz" in textos and "heartbeat.sh" in textos and ".env" in textos
                     and "Como voltar atrás" in textos and git(projeto, "rev-parse", "--short", "HEAD").stdout.strip() in textos, textos[:500])
            conferir("o relato também sai impresso", "Como voltar atrás" in texto and "antes-do-v7" in texto)
            conferir("com git próprio não se cria .tar.gz (só sem git próprio)", not rodada.copias.exists() or not list(rodada.copias.glob("*")))
            conferir("o src/app.js e o src/novo.js do projeto ficaram onde estavam (o código não muda)", (projeto / "src/app.js").read_text() == app_antigo and (projeto / "src/novo.js").is_file())
        seguro("a passagem com git", caso_passagem_com_git)

        # ── 4. sem git e dentro de um git maior: cópia compactada e git próprio ──
        def caso_sem_git(nome: str, tipo: str, pai: str = "") -> None:
            projeto = rodada.base / pai / nome if pai else rodada.base / nome
            projeto_v6_de_mentira(projeto, tipo)
            # no registro, o caminho com os acentos na forma decomposta (NFD), como o sincronizador real grava ("é" = "e" + acento)
            registro_de_mentira(rodada.registro, [Path(unicodedata.normalize("NFD", str(projeto)))])
            antes = lista_de_arquivos(projeto)
            entradas = 1 + sum(len(s) + len(a) for _, s, a in os.walk(projeto))
            feito = rodada.passar(projeto, "--criar-git")
            texto = saida(feito)
            conferir(f"passagem real ({tipo}) com --criar-git: termina com OK", feito.returncode == 0 and texto.lstrip().startswith("OK"), texto[-900:])
            copias = sorted(rodada.copias.glob(f"{nome}-*.tar.gz")) if rodada.copias.exists() else []
            conferir(f"({tipo}) o .tar.gz existe com o nome <pasta>-AAAA-MM-DD-HHMM.tar.gz, fora das pastas varridas, com o mesmo número de itens da pasta",
                     len(copias) == 1 and re.fullmatch(rf"{re.escape(nome)}-\d{{4}}-\d\d-\d\d-\d{{4}}\.tar\.gz", copias[0].name) is not None
                     and not any(str(copias[0]).startswith(str(Path.home() / x)) for x in ("Documents/VSCODE", "projetos", "Downloads"))
                     and len(subprocess.run(["tar", "-tzf", str(copias[0])], capture_output=True, text=True).stdout.splitlines()) == entradas, str(copias))
            raiz = git(projeto, "rev-parse", "--show-toplevel").stdout.strip()
            conferir(f"({tipo}) o git próprio foi criado (a raiz do git é a própria pasta), com o commit 'estado antes do v7' e a marca antes-do-v7",
                     raiz == str(projeto) and "estado antes do v7" in git(projeto, "log", "--format=%s").stdout and "antes-do-v7" in git(projeto, "tag").stdout.split()
                     and git(projeto, "show", "antes-do-v7:.delta-11/kanban.md").returncode == 0 and git(projeto, "status", "--porcelain").stdout.strip() == "")
            conferir(f"({tipo}) nada se perdeu: todo arquivo de antes está na pasta, no mesmo lugar ou na gaveta, com o mesmo conteúdo",
                     all((lista_de_arquivos(projeto).get(a) == h) or (lista_de_arquivos(projeto / ".delta-11/anterior-v6").get(a.removeprefix(".delta-11/")) == h)
                         or (lista_de_arquivos(projeto / ".delta-11/anterior-v6/raiz").get(a) == h) for a, h in antes.items()
                         ))
            if copias:
                solto = rodada.base / f"extraido-{nome}"
                solto.mkdir()
                subprocess.run(["tar", "-xzf", str(copias[0]), "-C", str(solto)], capture_output=True, env={**AMBIENTE, "COPYFILE_DISABLE": "1"})
                conferir(f"({tipo}) o .tar.gz, aberto em outro lugar, tem a pasta como era antes da passagem (todos os arquivos, mesmo conteúdo)",
                         lista_de_arquivos(solto / nome) == antes)
            if tipo == "sem-git":
                ponto = (projeto / ".delta-11/anterior-v6/PONTO-DE-PARTIDA.md").read_text()
                conferir("(sem-git) o ponto de partida diz que o projeto antigo não tinha a descrição preenchida, nem a fase atual, nem decisões",
                         "o projeto antigo não tinha isto preenchido" in ponto and "o quadro antigo não dizia a fase atual" in ponto and ponto.count("## ") == 4, ponto[:500])
            else:
                conferir("(dentro de um git maior) o relato diz que o git maior passa a ver a pasta como repositório aninhado",
                         "repositório aninhado" in (projeto / ".delta-11/anterior-v6/RELATO-DA-PASSAGEM.md").read_text())
            conferir(f"({tipo}) o registro não lista mais a pasta, mesmo com o nome gravado lá com o acento na outra forma (NFD)",
                     json.loads(rodada.registro.read_text(encoding="utf-8"))["projects"] == ["/outro/projeto"], rodada.registro.read_text()[:300])
            conferir(f"({tipo}) o segredo do projeto (se houver) fica fora do primeiro commit: .gitignore criado com a proteção de segredos",
                     all(l in (projeto / ".gitignore").read_text().splitlines() for l in (".env", "*.pem", "*.key", "credentials.json")))
        seguro("a passagem sem git", lambda: caso_sem_git("passagem-sem-git", "sem-git"))
        seguro("a passagem dentro de um git maior", lambda: caso_sem_git("passagem-dentro-do-maior-léo", "dentro-de-git-maior", "pasta-mãe-com-git"))

        # ── 5. o sincronizador antigo não toca no projeto passado ──
        def caso_sincronizador() -> None:
            oficial = SINCRONIZADOR_OFICIAL / "sincronizar.sh"
            if not oficial.is_file() or not shutil.which("jq"):
                print("  pulado — o sincronizar.sh oficial (ou o jq) não está neste computador")
                return
            sb = rodada.base / "sincronizador"
            casa, fonte, busca = sb / "casa", sb / "fonte", sb / "busca"
            for pasta in (casa / ".claude/skills", busca, fonte / ".delta-11/operativos", fonte / ".delta-11/hooks", fonte / ".delta-11/templates"):
                pasta.mkdir(parents=True)
            for script in ("sincronizar.sh", "task-done.sh", "monitor-delta11.sh", "vigilante.sh"):
                shutil.copy2(SINCRONIZADOR_OFICIAL / script, fonte / script)
            shutil.copy2(SINCRONIZADOR_OFICIAL / ".delta-11/removidos.txt", fonte / ".delta-11/removidos.txt")
            escrever(fonte, "CLAUDE.md", "# CLAUDE v6 da fonte de mentira\n")
            escrever(fonte, ".delta-11/operativos/ATLAS.md", "# ATLAS\n")
            escrever(fonte, ".delta-11/templates/settings-hooks.json", '{"hooks":{}}\n')
            isca = sb / "fora" / "isca-v6"
            escrever(isca, ".delta-11/kanban.md", "# isca\n")
            projeto = passado["pasta"]
            registro = sb / "registro.json"
            registro.write_text(json.dumps({"version": "6.4", "source": str(fonte), "projects": [str(projeto), str(isca)]}), encoding="utf-8")
            ambiente = {**AMBIENTE, "HOME": str(casa), "DELTA11_REGISTRY": str(registro), "DELTA11_SEARCH_PATHS": str(busca)}
            antes = digital(projeto)
            seco = subprocess.run(["bash", str(fonte / "sincronizar.sh"), "--dry-run"], capture_output=True, text=True, env=ambiente)
            conferir("sincronizar.sh --dry-run: pula o projeto passado ('é produto do Delta-11 v7') e não muda nada nele", "passagem-com-git — é produto do Delta-11 v7" in seco.stdout + seco.stderr
                     and digital(projeto) == antes, (seco.stdout + seco.stderr)[-500:])
            real = subprocess.run(["bash", str(fonte / "sincronizar.sh")], capture_output=True, text=True, env=ambiente)
            conferir("sincronizar.sh (rodada real): não toca no projeto passado (impressão digital igual), mas sincroniza o projeto v6 de isca (prova de que ele rodou)",
                     digital(projeto) == antes and (isca / "CLAUDE.md").is_file(), (real.stdout + real.stderr)[-500:])
        seguro("o sincronizador", caso_sincronizador)

        # ── 6. a trava do produto passado: a gaveta ──
        def caso_trava() -> None:
            projeto = passado["pasta"]
            gaveta = projeto / ".delta-11" / "anterior-v6"

            def trava(papel: str, ferramenta: str, arquivo: Path) -> tuple[int, str]:
                pedido = {"tool_name": ferramenta, "tool_input": {"file_path": str(arquivo), "content": "x"}, "cwd": str(projeto), "session_id": "s", "agent_type": papel}
                feito = subprocess.run([sys.executable, str(projeto / ".claude/hooks/delta-11/trava.py"), PROGRAMA], input=json.dumps(pedido), capture_output=True, text=True,
                                       env={**AMBIENTE, "CLAUDE_PROJECT_DIR": str(projeto)})
                return feito.returncode, feito.stderr
            alvos = [gaveta / "kanban.md", gaveta / "PONTO-DE-PARTIDA.md", gaveta / "copias-de-agentes/agent-suja/src/app.js", gaveta / "raiz/CLAUDE.md"]
            barrados = [(p, a.name) for p in ("atlas", "arquiteto", "cronos", "documentador", "front", "back", "scout", "selador", "destruidor") for a in alvos
                        if not (trava(p, "Write", a)[0] == 2 and "não escreve em" in trava(p, "Write", a)[1])]
            conferir("escrever na gaveta: a trava barra todos os papéis, em todos os lugares dela", not barrados, str(barrados[:5]))
            codigo, motivo = trava("atlas", "Write", gaveta / "novo.md")
            conferir("a frase da trava diz que ninguém escreve em .delta-11/ (a gaveta cai na linha 'qualquer outro arquivo')", codigo == 2 and "não escreve em `.delta-11/`" in motivo, motivo)
            lidos = [(p, a.name) for p in ("atlas", "arquiteto", "front", "back", "documentador") for a in alvos if trava(p, "Read", a)[0] != 0]
            conferir("ler a gaveta: o ATLAS (e os outros papéis, menos o Revisor) leem", not lidos and (gaveta / "PONTO-DE-PARTIDA.md").is_file(), str(lidos[:5]))
            codigo, motivo = trava("revisor", "Read", gaveta / "PONTO-DE-PARTIDA.md")
            conferir("ler a gaveta: o Revisor é barrado", codigo == 2 and "não lê `.delta-11/`" in motivo, motivo)
            lugares = json.loads((MOTOR / "agentes" / "lugares.json").read_text())["lugares"]
            linha = next(l for l in lugares if re.match(l["regex"], ".delta-11/anterior-v6/PONTO-DE-PARTIDA.md"))
            conferir("o mapa (agentes/lugares.json) manda a gaveta para a linha '.delta-11/': ninguém escreve, todos menos o Revisor leem",
                     linha["fixo"] == ".delta-11/" and linha["escreve"] == ["ninguém"] and linha["le"] == {"todos": True, "menos": ["revisor"]}, str(linha))
        seguro("a trava e a gaveta", caso_trava)

        # ── 7. o aviso de abertura leva o ATLAS ao ponto de partida (só se ainda não há Luz) ──
        def caso_abertura() -> None:
            projeto = passado["pasta"]

            def abertura() -> str:
                return subprocess.run([sys.executable, "-B", str(projeto / ".claude/hooks/delta-11/situacao.py"), PROGRAMA], input="{}", capture_output=True, text=True,
                                      env={**AMBIENTE, "CLAUDE_PROJECT_DIR": str(projeto)}).stdout
            sem_luz = abertura()
            conferir("o aviso de abertura (claude-code) mostra o texto do ponto de partida quando não há .delta-11/luz.md", FRASE_DA_ABERTURA in sem_luz, sem_luz[-500:])
            (projeto / ".delta-11/luz.md").write_text("# A Luz\n")
            conferir("e não mostra quando já há a Luz", FRASE_DA_ABERTURA not in abertura() and "veio do Delta-11 antigo" not in abertura())
            (projeto / ".delta-11/luz.md").unlink()
            outro = rodada.base / "abertura-sem-gaveta"
            (outro / ".delta-11").mkdir(parents=True)
            sem_gaveta = subprocess.run([sys.executable, "-B", str(projeto / ".claude/hooks/delta-11/situacao.py"), PROGRAMA], input="{}", capture_output=True, text=True,
                                        env={**AMBIENTE, "CLAUDE_PROJECT_DIR": str(outro)}).stdout
            conferir("e não mostra num produto que nunca teve o Delta-11 antigo (sem a gaveta)", "veio do Delta-11 antigo" not in sem_gaveta)
        seguro("o aviso de abertura", caso_abertura)

        # ── 8. rodar de novo na mesma pasta recusa ──
        def caso_de_novo() -> None:
            projeto = passado["pasta"]
            antes = digital(projeto)
            feito = rodada.passar(projeto, "--guardar-copias")
            conferir("rodar a passagem de novo na mesma pasta: recusa ('esta pasta já está no v7') sem mudar nada", feito.returncode == 1 and "esta pasta já está no v7" in saida(feito)
                     and digital(projeto) == antes)
        seguro("a segunda rodada", caso_de_novo)

        # ── 9. falha no meio: para com erro claro e a pasta volta ao que era ──
        def caso_falha() -> None:
            ocupada = rodada.base / "falha-gaveta-ja-existe"
            projeto_v6_de_mentira(ocupada, "com-git")
            (ocupada / ".delta-11/anterior-v6").mkdir()
            (ocupada / ".delta-11/anterior-v6/algo.txt").write_text("uma gaveta que já existia\n")
            envelhecer(ocupada)
            antes = rodada.digital_de_tudo()
            feito = rodada.passar(ocupada, "--guardar-copias")
            conferir("a gaveta já existe: para com erro claro, antes de mudar qualquer coisa (impressão digital igual, git inclusive)",
                     feito.returncode == 1 and "gaveta" in saida(feito) and "já existe" in saida(feito) and rodada.digital_de_tudo() == antes, saida(feito)[-400:])
            projeto = rodada.base / "falha-no-meio"
            projeto_v6_de_mentira(projeto, "com-git")
            registro_de_mentira(rodada.registro, [projeto])
            registro_antes = rodada.registro.read_text()
            antes_do_conteudo = digital(projeto, com_datas=False, sem_git=True)
            lista_antes = git(projeto, "worktree", "list", "--porcelain").stdout
            for passo in ("instalar-o-v7", "ponto-de-partida"):
                if passo == "ponto-de-partida":
                    projeto = rodada.base / "falha-no-meio-2"
                    projeto_v6_de_mentira(projeto, "com-git")
                    antes_do_conteudo = digital(projeto, com_datas=False, sem_git=True)
                feito = rodada.passar(projeto, "--guardar-copias", extra={"DELTA11_PULSO_PASSAGEM_FALHAR_DEPOIS_DE": passo})
                texto = saida(feito)
                conferir(f"falha de mentira depois do passo '{passo}': sai 1, diz o motivo e que a pasta foi devolvida ao que era",
                         feito.returncode == 1 and "ERRO" in texto and passo in texto and "devolvida ao que era" in texto, texto[-500:])
                conferir(f"falha depois de '{passo}': o conteúdo, os caminhos e as permissões da pasta (fora do .git) voltaram ao que eram, cópias de agentes inclusive",
                         digital(projeto, com_datas=False, sem_git=True) == antes_do_conteudo
                         and (projeto / ".claude/worktrees/agent-suja/.git").is_file() and not (projeto / ".delta-11/anterior-v6").exists()
                         and not (projeto / ".claude/hooks/delta-11").exists() and "prunable" not in git(projeto, "worktree", "list", "--porcelain").stdout
                         and str(projeto / ".claude/worktrees/agent-suja") in git(projeto, "worktree", "list", "--porcelain").stdout)
                conferir(f"falha depois de '{passo}': a rede de segurança fica (marca antes-do-v7, commit do estado antes e o trabalho da cópia guardado), e o registro não mudou",
                         "antes-do-v7" in git(projeto, "tag").stdout.split() and git(projeto, "log", "-1", "--format=%s").stdout.strip() == "estado antes do v7"
                         and git(projeto, "log", "-1", "--format=%s", "worktree-agent-suja").stdout.strip() == "trabalho da cópia guardado antes do v7"
                         and rodada.registro.read_text() == registro_antes)
            del lista_antes
        seguro("a falha no meio", caso_falha)

        # ── 10. a volta atrás: a receita do relato devolve o projeto ao que era ──
        def caso_volta() -> None:
            projeto = rodada.base / "volta-atras"
            projeto_v6_de_mentira(projeto, "com-git")
            antes = lista_de_arquivos(projeto)
            registro_de_mentira(rodada.registro, [projeto])
            feito = rodada.passar(projeto, "--guardar-copias")
            relato = (projeto / ".delta-11/anterior-v6/RELATO-DA-PASSAGEM.md").read_text() if feito.returncode == 0 else ""
            receita = re.search(r"```sh\n(.*?)```", relato, re.S)
            conferir("o relato traz a receita de volta (um bloco de comandos) e ela devolve o projeto: os arquivos de antes voltam todos, com o mesmo conteúdo, e as cópias ao lugar delas",
                     bool(receita), relato[-600:])
            if not receita:
                return
            rodou = subprocess.run(["sh", "-ec", receita.group(1)], cwd=projeto, capture_output=True, text=True, env=AMBIENTE)
            depois = lista_de_arquivos(projeto)
            perdidos = [a for a, h in antes.items() if depois.get(a) != h]
            conferir("a receita de volta rodou sem erro, e o projeto ficou com todos os arquivos de antes (e o .delta-11 do v6 no lugar)",
                     rodou.returncode == 0 and not perdidos and (projeto / ".delta-11/kanban.md").is_file() and not (projeto / ".claude/hooks/delta-11").exists()
                     and (projeto / ".claude/worktrees/agent-suja/.git").is_file(), (rodou.stdout + rodou.stderr)[-500:] + str(perdidos[:5]))
        seguro("a volta atrás", caso_volta)

    if falhas:
        print(f"PULSO DA PASSAGEM FALHOU — {len(falhas)}: " + "; ".join(falhas))
        return 1
    print("PULSO DA PASSAGEM OK — o ensaio e as recusas não mudam nada, a passagem guarda tudo antes de mudar e não perde arquivo, e a volta atrás funciona.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
