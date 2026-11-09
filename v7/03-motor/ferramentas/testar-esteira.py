#!/usr/bin/env python3
"""Pulso da esteira do motor (esteira/esteira): prova cada caminho do contrato (modelos/esteira.md) em produtos descartáveis.

Monta, no temporário, um produto de mentira com o motor (a esteira, a caixa do produto, o mapa da trava) e comandos falsos
de instalar, montar, testar e publicar (roteiros sh que passam ou falham), para não depender de linguagem nenhuma. Cada
caso copia o produto, faz o que um agente faria e confere a última linha da esteira (ENTROU ou RECUSOU, pelo motivo certo)
e o que ficou no git, na pasta e no remoto. Se a caixa do produto não abre aqui (rodando dentro de outra caixa), roda os
comandos direto, presos pela de fora, como a própria caixa faz.
Uso: python3 testar-esteira.py   (sai com 1 se algum caso der o resultado errado)
"""
from __future__ import annotations

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
ESTEIRA = MOTOR / "esteira" / "esteira"
# Sem as variáveis GIT_* de um commit em andamento: dentro do gancho, elas apontariam o git do teste para o repositório real.
AMBIENTE = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
PRESO = bool(shutil.which("sandbox-exec")) and subprocess.run(["sandbox-exec", "-p", "(version 1)(allow default)", "/usr/bin/true"], capture_output=True).returncode != 0
if PRESO:
    AMBIENTE["DELTA11_DENTRO_DA_CAIXA_DO_PRODUTO"] = "1"  # já dentro de uma caixa: a caixa do produto roda direto, presa pela de fora
CAIXA_DO_MAC = bool(shutil.which("sandbox-exec")) and not PRESO
INSTALADO = "Delta-11 v7 instalado\n\nDelta-11: instalado"
COMANDOS = "instalar: sh instalar.sh\nmontar: sh montar.sh\ntestar: sh testes/rodar.sh\ntestes: testes/*.test.sh\npublicar: sh publicar.sh\nfluxo-principal: sh fluxo.sh\n"
ARQUIVOS = {
    ".gitignore": ".claude/worktrees/\n.claude/settings.local.json\n.delta-11/esteira/\n.delta-11/cofre/\n.env\n.env.local\ndist/\n.dependencias-instaladas\n",
    ".claude/settings.json": "{}\n",
    "esteira-comandos.txt": COMANDOS,
    "instalar.sh": '[ -n "$PULSO_REGISTRO" ] && echo instalou >> "$PULSO_REGISTRO"\n: > .dependencias-instaladas\n',
    "montar.sh": '[ -n "$PULSO_REGISTRO" ] && echo montou >> "$PULSO_REGISTRO"\nmkdir -p dist && cp src/telas/inicio.js dist/app.txt\n',
    "publicar.sh": '[ -n "$PULSO_PUBLICADO" ] || exit 0\nls -A > "$PULSO_PUBLICADO"\necho "chave=$CHAVE_DO_SERVICO" >> "$PULSO_PUBLICADO"\n',
    "fluxo.sh": '[ -n "$PULSO_PUBLICADO" ] && echo fluxo > "$PULSO_PUBLICADO.fluxo"\nexit 0\n',
    "testes/rodar.sh": ('[ -n "$PULSO_REGISTRO" ] && echo testou >> "$PULSO_REGISTRO"\n'
                        'if [ -n "$PULSO_SINAL" ] && [ ! -f "$PULSO_SINAL.solto" ]; then : > "$PULSO_SINAL"; '
                        'while [ ! -f "$PULSO_SINAL.solto" ]; do sleep 0.1; done; fi\n'
                        'for t in testes/*.test.sh; do sh "$t" || { echo "FALHOU: $t"; exit 1; }; done\necho "todos os testes passaram"\n'),
    "testes/a.test.sh": "grep -q BOM src/telas/inicio.js\n",
    "testes/b.test.sh": "test -f dist/app.txt\ntest -f .dependencias-instaladas\n",
    "testes/c.test.sh": '[ -n "$PULSO_SEM_ENV" ] || grep -q SEGREDO_DE_TESTE .env\n',  # a automação não tem o .env
    "testes/d.test.sh": "! grep -rq QUEBRA src\n",
    "src/telas/inicio.js": "BOM\n",
    "src/telas/velho.js": "velho\n",
    "banco/x.sql": "select 1;\n",
    ".delta-11/regras/enderecos.txt": "front src/telas/\nvault banco/\nshield testes/\n",
    ".delta-11/quadro/camada-3/abertura.md": "# Abertura\n",
    ".delta-11/quadro/camada-3/quadro.md": "# Quadro\n\nSituação: aberto\n",
}


def git(p: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(p), *args], capture_output=True, text=True, env=AMBIENTE).stdout.strip()


def escrever(p: Path, arquivo: str, texto: str) -> None:
    (p / arquivo).parent.mkdir(parents=True, exist_ok=True)
    (p / arquivo).write_text(texto, encoding="utf-8")


def modelo(base: Path) -> Path:
    """O produto de mentira, com o motor instalado e um commit `Delta-11: instalado`."""
    p = base / "modelo"
    for arquivo, texto in ARQUIVOS.items():
        escrever(p, arquivo, texto)
    ganchos = p / ".claude/hooks/delta-11"
    ganchos.mkdir(parents=True)
    shutil.copy2(MOTOR / "ganchos" / "caixa-do-produto.py", ganchos)
    shutil.copy2(MOTOR / "agentes" / "lugares.json", ganchos)
    shutil.copy2(ESTEIRA, p / "esteira")
    escrever(p, ".env", "SEGREDO_DE_TESTE=1\n")
    for args in (("init", "-q", "-b", "main"), ("config", "user.name", "pulso"), ("config", "user.email", "pulso@exemplo.invalid"),
                 ("config", "core.hooksPath", "/dev/null"), ("add", "-A"), ("commit", "-q", "-m", INSTALADO)):
        git(p, *args)
    return p


def esteira(p: Path, *args: str, **ambiente: str) -> tuple[int, str]:
    feito = subprocess.run(["sh", "esteira", *args], cwd=p, capture_output=True, text=True, env={**AMBIENTE, **ambiente}, timeout=300)
    return feito.returncode, feito.stdout + feito.stderr


def ultima(saida: str) -> str:
    linhas = [l for l in saida.splitlines() if l.strip()]
    return linhas[-1] if linhas else ""


def entrou(resultado: tuple[int, str]) -> bool:
    return resultado[0] == 0 and ultima(resultado[1]) == "ENTROU"


def recusou(resultado: tuple[int, str], motivo: str) -> bool:
    return resultado[0] == 1 and ultima(resultado[1]).startswith("RECUSOU:") and motivo.lower() in ultima(resultado[1]).lower()


def no_head(p: Path, arquivo: str) -> str | None:
    feito = subprocess.run(["git", "-C", str(p), "show", f"HEAD:{arquivo}"], capture_output=True, text=True, env=AMBIENTE)
    return feito.stdout if feito.returncode == 0 else None


def commit_por_baixo(p: Path, mudancas: dict[str, str | None], mensagem: str) -> str:
    """Outra entrega (ou um commit feito à mão) entra no ramo sem tocar na pasta: um índice à parte e o update-ref."""
    indice = p.parent / f"indice-{p.name}-{time.time_ns()}"
    env = {**AMBIENTE, "GIT_INDEX_FILE": str(indice)}
    g = lambda *a, entrada=None: subprocess.run(["git", "-C", str(p), *a], capture_output=True, text=True, env=env, input=entrada).stdout.strip()
    g("read-tree", "HEAD")
    for arquivo, texto in mudancas.items():
        if texto is None:
            g("update-index", "--force-remove", "--", arquivo)
        else:
            g("update-index", "--add", "--cacheinfo", f"100644,{g('hash-object', '-w', '--stdin', entrada=texto)},{arquivo}")
    novo = g("commit-tree", g("write-tree"), "-p", "HEAD", "-m", mensagem)
    git(p, "update-ref", "HEAD", novo)
    indice.unlink(missing_ok=True)
    return novo


def remoto_de(p: Path) -> Path:
    bare = p.parent / f"{p.name}-remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], capture_output=True, env=AMBIENTE)
    git(p, "remote", "add", "origin", str(bare))
    git(p, "push", "-q", "-u", "origin", "main")
    return bare


def outro_envia(p: Path, bare: Path, arquivo: str, texto: str) -> str:
    """Outra máquina (a automação, o SCOUT de lá) envia um commit ao remoto."""
    outro = p.parent / f"{p.name}-outro"
    subprocess.run(["git", "clone", "-q", str(bare), str(outro)], capture_output=True, env=AMBIENTE)
    for args in (("config", "user.name", "outro"), ("config", "user.email", "o@exemplo.invalid"), ("config", "core.hooksPath", "/dev/null")):
        git(outro, *args)
    escrever(outro, arquivo, texto)
    git(outro, "add", "-A")
    git(outro, "commit", "-q", "-m", f"scout: {arquivo}\n\nEsteira: entrou")
    git(outro, "push", "-q", "origin", "main")
    return git(outro, "rev-parse", "HEAD")


def esteira_mudada() -> str:
    """A esteira com a porta (o sh) igual e o programa trocado por um que diz ENTROU sem conferir nada."""
    return ESTEIRA.read_text(encoding="utf-8").split("#PYTHON\n", 1)[0] + "#PYTHON\nprint('ENTROU')\n"


def candidata(p: Path, nome: str, arquivos: dict[str, str]) -> None:
    git(p, "worktree", "add", "-q", "--detach", f".claude/worktrees/{nome}", "HEAD")
    for arquivo, texto in arquivos.items():
        escrever(p / ".claude/worktrees" / nome, arquivo, texto)


# ---------------------------------------------------------------- os casos (cada um num produto novo)
def entrega_simples(p: Path) -> tuple[bool, str]:
    antes = git(p, "rev-parse", "HEAD")
    escrever(p, "src/telas/inicio.js", "BOM 2\n")
    escrever(p, "src/telas/pela-metade.js", "QUEBRA\n")  # o trabalho pela metade de outro: fica fora da cópia limpa
    registro = p.parent / f"{p.name}-registro"
    r = esteira(p, "front", "src/telas/inicio.js", PULSO_REGISTRO=str(registro))
    feito = registro.read_text().split() if registro.exists() else []
    logs = list((p / ".delta-11/esteira").glob("front-*.log"))
    certo = (entrou(r) and git(p, "log", "-1", "--format=%B").strip().splitlines()[-1] == "Esteira: entrou" and git(p, "rev-parse", "HEAD^") == antes
             and no_head(p, "src/telas/inicio.js") == "BOM 2\n" and no_head(p, "src/telas/pela-metade.js") is None
             and (p / "src/telas/pela-metade.js").exists() and not git(p, "diff", "--cached", "--name-only")
             and not git(p, "status", "--porcelain", "--", "src/telas/inicio.js") and feito == ["instalou", "montou", "testou"]
             and len(logs) == 1 and logs[0].read_text().rstrip().endswith("ENTROU") and len(r[1].splitlines()) <= 15)
    return certo, r[1]


def fora_do_territorio(p: Path) -> tuple[bool, str]:
    antes = git(p, "rev-parse", "HEAD")
    escrever(p, "banco/x.sql", "select 2;\n")
    r = esteira(p, "front", "banco/x.sql")
    return recusou(r, "território de vault") and git(p, "rev-parse", "HEAD") == antes and (p / "banco/x.sql").read_text() == "select 2;\n", r[1]


def sem_enderecos(p: Path) -> tuple[bool, str]:
    (p / ".delta-11/regras/enderecos.txt").unlink()
    escrever(p, "banco/x.sql", "select 2;\n")
    r = esteira(p, "front", "banco/x.sql")
    return entrou(r) and no_head(p, "banco/x.sql") == "select 2;\n", r[1]


def conjunta_sem_aceite(p: Path) -> tuple[bool, str]:
    escrever(p, "src/telas/inicio.js", "BOM junto\n")
    escrever(p, "banco/x.sql", "select 3;\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/front-1.md", "Situação: trabalhando\n- Entrego junto: src/telas/inicio.js\n")
    r = esteira(p, "front,vault", "src/telas/inicio.js", "banco/x.sql")
    return recusou(r, "Entrego junto") and "vault" in ultima(r[1]), r[1]


def conjunta_com_aceite(p: Path) -> tuple[bool, str]:
    escrever(p, "src/telas/inicio.js", "BOM junto\n")
    escrever(p, "banco/x.sql", "select 3;\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/front-1.md", "Situação: trabalhando\n- Entrego junto: src/telas/inicio.js\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/vault-1.md", "Situação: encerrado\n- Entrego junto: `banco/x.sql`\n")
    r = esteira(p, "front,vault", "src/telas/inicio.js", "banco/x.sql")
    return entrou(r) and no_head(p, "banco/x.sql") == "select 3;\n" and git(p, "log", "-1", "--format=%s").startswith("front,vault:"), r[1]


def scout_em_qualquer_territorio(p: Path) -> tuple[bool, str]:
    escrever(p, "banco/x.sql", "select 4;\n")
    escrever(p, ".delta-11/alarmes/erro.md.resolvido", "resolvido\n")
    r = esteira(p, "scout", "banco/x.sql", ".delta-11/alarmes/erro.md.resolvido")
    return entrou(r) and no_head(p, ".delta-11/alarmes/erro.md.resolvido") == "resolvido\n", r[1]


def so_o_scout_nos_alarmes(p: Path) -> tuple[bool, str]:
    escrever(p, ".delta-11/alarmes/erro.md.resolvido", "resolvido\n")
    r = esteira(p, "back", ".delta-11/alarmes/erro.md.resolvido")
    return recusou(r, "só o SCOUT"), r[1]


def motor_nao_entra(p: Path) -> tuple[bool, str]:
    escrever(p, ".claude/settings.json", '{"disableAllHooks": true}\n')
    r1 = esteira(p, "back", ".claude/settings.json")
    escrever(p, "esteira", esteira_mudada())
    r2 = esteira(p, "back", "esteira")
    return recusou(r1, "do motor") and recusou(r2, "do motor"), r1[1] + r2[1]


def candidata_escolhida(p: Path) -> tuple[bool, str]:
    candidata(p, "c1", {"src/telas/inicio.js": "BOM da candidata\n", "src/telas/nova/tela.js": "nova\n", "compartilhado/util.js": "{}\n",
                        ".delta-11/quadro/camada-3/linhas/front-1.md": "Situação: encerrado\n"})
    candidata(p, "c2", {"src/telas/inicio.js": "BOM da outra\n", ".delta-11/quadro/camada-3/linhas/front-2.md": "Situação: encerrado\n"})
    r = esteira(p, "front", "--copia", ".claude/worktrees/c1", "--descartar", ".claude/worktrees/c2")
    pasta = p / ".delta-11/quadro/camada-3/candidatas"
    certo = (entrou(r) and no_head(p, "src/telas/inicio.js") == "BOM da candidata\n" and no_head(p, "src/telas/nova/tela.js") == "nova\n"
             and no_head(p, "compartilhado/util.js") == "{}\n" and (p / "src/telas/nova/tela.js").read_text() == "nova\n"
             and (p / "src/telas/inicio.js").read_text() == "BOM da candidata\n" and not (p / ".claude/worktrees/c1").exists()
             and not (p / ".claude/worktrees/c2").exists() and (pasta / "c1-front-1.md").is_file() and (pasta / "c2-front-2.md").is_file()
             and not git(p, "status", "--porcelain", "--", "src", "compartilhado"))
    return certo, r[1]


def candidata_dependencia_com_limite(p: Path) -> tuple[bool, str]:
    """A dependência da candidata é só arquivo novo numa pasta fora de todo território: um novo na raiz (manifesto) ou um que já
    existe fora dos territórios (instalar.sh) é do BACK."""
    candidata(p, "c1", {"src/telas/inicio.js": "BOM da candidata\n", "package.json": "{}\n",
                        ".delta-11/quadro/camada-3/linhas/front-1.md": "Situação: encerrado\n"})
    candidata(p, "c2", {"src/telas/inicio.js": "BOM da outra\n", "instalar.sh": "echo trocado\n",
                        ".delta-11/quadro/camada-3/linhas/front-2.md": "Situação: encerrado\n"})
    antes = git(p, "rev-parse", "HEAD")
    r1 = esteira(p, "front", "--copia", ".claude/worktrees/c1")
    r2 = esteira(p, "front", "--copia", ".claude/worktrees/c2")
    return (recusou(r1, "território de outro: package.json") and recusou(r2, "território de outro: instalar.sh")
            and git(p, "rev-parse", "HEAD") == antes and (p / ".claude/worktrees/c1").exists()), r1[1] + r2[1]


def candidata_fora_do_territorio(p: Path) -> tuple[bool, str]:
    candidata(p, "c1", {"src/telas/inicio.js": "BOM da candidata\n", "banco/x.sql": "drop table x;\n",
                        ".delta-11/quadro/camada-3/linhas/front-1.md": "Situação: encerrado\n"})
    antes = git(p, "rev-parse", "HEAD")
    r = esteira(p, "front", "--copia", ".claude/worktrees/c1")
    return recusou(r, "território de outro") and (p / ".claude/worktrees/c1").exists() and git(p, "rev-parse", "HEAD") == antes, r[1]


def descarte(p: Path) -> tuple[bool, str]:
    candidata(p, "c3", {"src/telas/inicio.js": "BOM descartada\n", ".delta-11/quadro/camada-3/linhas/front-3.md": "Situação: encerrado\n"})
    antes = git(p, "rev-parse", "HEAD")
    r = esteira(p, "front", "--descartar", ".claude/worktrees/c3")
    return (entrou(r) and not (p / ".claude/worktrees/c3").exists() and (p / ".delta-11/quadro/camada-3/candidatas/c3-front-3.md").is_file()
            and git(p, "rev-parse", "HEAD") == antes and ".claude/worktrees/c3" not in git(p, "worktree", "list")), r[1]


def arquivo_apagado(p: Path) -> tuple[bool, str]:
    (p / "src/telas/velho.js").unlink()
    registro = p.parent / f"{p.name}-registro"
    r = esteira(p, "front", "src/telas/velho.js", PULSO_REGISTRO=str(registro))
    return entrou(r) and no_head(p, "src/telas/velho.js") is None and "testou" in (registro.read_text() if registro.exists() else ""), r[1]


def parar(p: Path) -> tuple[bool, str]:
    escrever(p, ".delta-11/quadro/camada-2/abertura.md", "# Abertura\n\nParar do dono: 2026-10-24\n")
    escrever(p, ".delta-11/quadro/camada-2/quadro.md", "# Quadro\n\nSituação: aberto\n")
    (p / "src/telas/inicio.js").unlink()
    (p / "testes/a.test.sh").unlink()
    registro = p.parent / f"{p.name}-registro"
    r = esteira(p, "back", "src/telas/inicio.js", "testes/a.test.sh", PULSO_REGISTRO=str(registro))
    return (entrou(r) and no_head(p, "src/telas/inicio.js") is None and no_head(p, "testes/a.test.sh") is None and not registro.exists()
            and "Parar do dono" in r[1]), r[1]


def teste_que_falha(p: Path) -> tuple[bool, str]:
    antes = git(p, "rev-parse", "HEAD")
    escrever(p, "src/telas/inicio.js", "RUIM\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return (recusou(r, "teste vermelho") and git(p, "rev-parse", "HEAD") == antes and (p / "src/telas/inicio.js").read_text() == "RUIM\n"
            and git(p, "status", "--porcelain", "--", "src/telas/inicio.js").startswith("M")), r[1]


def teste_apagado_sem_aval(p: Path) -> tuple[bool, str]:
    antes = git(p, "rev-parse", "HEAD")
    (p / "testes/c.test.sh").unlink()
    r = esteira(p, "shield", "testes/c.test.sh")
    return recusou(r, "Aval") and "testes/c.test.sh (apagado)" in ultima(r[1]) and git(p, "rev-parse", "HEAD") == antes, r[1]


def teste_apagado_com_aval(p: Path) -> tuple[bool, str]:
    (p / "testes/c.test.sh").unlink()
    escrever(p, ".delta-11/quadro/camada-3/linhas/shield-1.md", "Situação: encerrado\n- Aval: testes/c.test.sh\n")
    r = esteira(p, "shield", "testes/c.test.sh")
    return entrou(r) and no_head(p, "testes/c.test.sh") is None, r[1]


def teste_afrouxado_sem_aval(p: Path) -> tuple[bool, str]:
    escrever(p, "testes/a.test.sh", "true\n")
    r1 = esteira(p, "shield", "testes/a.test.sh")
    escrever(p, "testes/a.test.sh", "grep -q BOM src/telas/inicio.js\n")
    escrever(p, "testes/b.test.sh", "test -f dist/app.txt\ntest -f .dependencias-instaladas\n# xit( pula o resto\n")
    r2 = esteira(p, "shield", "testes/b.test.sh")
    return recusou(r1, "afrouxado") and recusou(r2, "marcado para pular"), r1[1] + r2[1]


def testar_mudado_sem_aval(p: Path) -> tuple[bool, str]:
    escrever(p, "esteira-comandos.txt", COMANDOS.replace("testar: sh testes/rodar.sh", "testar: true"))
    r = esteira(p, "back", "esteira-comandos.txt")
    return recusou(r, "esteira-comandos.txt (muda o `testar:`"), r[1]


def outro_entrou_antes(p: Path) -> tuple[bool, str]:
    escrever(p, "src/telas/inicio.js", "BOM 3\n")
    sinal, registro = p.parent / f"{p.name}-sinal", p.parent / f"{p.name}-registro"
    processo = subprocess.Popen(["sh", "esteira", "front", "src/telas/inicio.js"], cwd=p, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                env={**AMBIENTE, "PULSO_SINAL": str(sinal), "PULSO_REGISTRO": str(registro)})
    limite = time.time() + 120
    while not sinal.exists() and time.time() < limite and processo.poll() is None:
        time.sleep(0.1)
    outro = commit_por_baixo(p, {"banco/y.sql": "select 9;\n"}, "vault: banco/y.sql\n\nEsteira: entrou")  # entra enquanto esta testa
    Path(str(sinal) + ".solto").write_text("")
    saida = processo.communicate(timeout=300)[0]
    r = (processo.returncode, saida)
    return (entrou(r) and "outra mudança entrou" in saida and git(p, "rev-parse", "HEAD^") == outro and no_head(p, "banco/y.sql") == "select 9;\n"
            and no_head(p, "src/telas/inicio.js") == "BOM 3\n" and registro.read_text().split().count("testou") == 2), saida


def outro_entrou_no_mesmo_arquivo(p: Path) -> tuple[bool, str]:
    escrever(p, "src/telas/inicio.js", "BOM 3\n")
    sinal = p.parent / f"{p.name}-sinal"
    processo = subprocess.Popen(["sh", "esteira", "front", "src/telas/inicio.js"], cwd=p, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                env={**AMBIENTE, "PULSO_SINAL": str(sinal)})
    limite = time.time() + 120
    while not sinal.exists() and time.time() < limite and processo.poll() is None:
        time.sleep(0.1)
    outro = commit_por_baixo(p, {"src/telas/inicio.js": "BOM do outro\n"}, "front: src/telas/inicio.js\n\nEsteira: entrou")
    Path(str(sinal) + ".solto").write_text("")
    saida = processo.communicate(timeout=300)[0]
    return recusou((processo.returncode, saida), "choque") and git(p, "rev-parse", "HEAD") == outro, saida


def remoto_avanco_simples(p: Path) -> tuple[bool, str]:
    bare = remoto_de(p)
    dele = outro_envia(p, bare, "banco/z.sql", "select 5;\n")
    escrever(p, "src/telas/inicio.js", "BOM 4\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return (entrou(r) and git(p, "rev-parse", "HEAD^") == dele and (p / "banco/z.sql").read_text() == "select 5;\n"
            and git(bare, "rev-parse", "main") == git(p, "rev-parse", "HEAD") and not git(p, "status", "--porcelain", "--", "banco")), r[1]


def remoto_com_registro_daqui(p: Path) -> tuple[bool, str]:
    bare = remoto_de(p)
    commit_por_baixo(p, {".delta-11/registro/r1.md": "registro\n"}, "registro do Delta-11")  # só daqui, só .delta-11/
    dele = outro_envia(p, bare, "banco/z.sql", "select 5;\n")
    escrever(p, "src/telas/inicio.js", "BOM 4\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    pais = git(p, "rev-list", "--parents", "-n", "1", "HEAD^").split()
    return (entrou(r) and len(pais) == 3 and dele in pais and no_head(p, ".delta-11/registro/r1.md") == "registro\n"
            and no_head(p, "banco/z.sql") == "select 5;\n" and git(bare, "rev-parse", "main") == git(p, "rev-parse", "HEAD")), r[1]


def remoto_com_choque(p: Path) -> tuple[bool, str]:
    bare = remoto_de(p)
    daqui = commit_por_baixo(p, {"banco/local.sql": "select 6;\n"}, "vault: banco/local.sql\n\nEsteira: entrou")  # código daqui não enviado
    outro_envia(p, bare, "banco/z.sql", "select 5;\n")
    escrever(p, "src/telas/inicio.js", "BOM 4\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return recusou(r, "código dos dois lados") and "ARQUITETO" in ultima(r[1]) and git(p, "rev-parse", "HEAD") == daqui, r[1]


def ensaio(p: Path) -> tuple[bool, str]:
    bare = remoto_de(p)
    escrever(p, ".delta-11/esteira/ensaio", "ensaio\n")
    escrever(p, "src/telas/inicio.js", "BOM 5\n")
    publicado = p.parent / f"{p.name}-publicado"
    antes = git(bare, "rev-parse", "main")
    r = esteira(p, "front", "src/telas/inicio.js", PULSO_PUBLICADO=str(publicado))
    return (entrou(r) and git(bare, "rev-parse", "main") == antes and not publicado.exists() and "ensaio: não envia" in r[1]
            and "ensaio: não publica" in r[1] and no_head(p, "src/telas/inicio.js") == "BOM 5\n"), r[1]


def publica(p: Path) -> tuple[bool, str]:
    escrever(p, ".delta-11/cofre/CHAVE_DO_SERVICO", "valor-do-cofre\n")
    escrever(p, "src/telas/inicio.js", "BOM 6\n")
    publicado = p.parent / f"{p.name}-publicado"
    r = esteira(p, "front", "src/telas/inicio.js", PULSO_PUBLICADO=str(publicado))
    visto = publicado.read_text().split() if publicado.exists() else []
    return (entrou(r) and "dist" in visto and "chave=valor-do-cofre" in visto and not {".env", ".delta-11", ".git", ".claude"} & set(visto)
            and Path(str(publicado) + ".fluxo").exists() and "fluxo principal: passou" in r[1]), r[1]


def sem_comandos(p: Path) -> tuple[bool, str]:
    commit_por_baixo(p, {"esteira-comandos.txt": None}, "Delta-11 v7 instalado\n\nDelta-11: instalado")
    (p / "esteira-comandos.txt").unlink()
    escrever(p, "src/telas/inicio.js", "BOM 7\n")
    r1 = esteira(p, "front", "src/telas/inicio.js")
    escrever(p, "esteira-comandos.txt", "montar: sh montar.sh\ntestes: testes/*.test.sh\n")
    r2 = esteira(p, "back", "esteira-comandos.txt")
    return recusou(r1, "falta esteira-comandos.txt") and "testar:" in ultima(r1[1]) and recusou(r2, "sem a linha `testar:`"), r1[1] + r2[1]


def versao_do_ultimo_commit(p: Path) -> tuple[bool, str]:
    (p / "esteira").write_text(esteira_mudada())  # a mesma porta, com o programa mudado na pasta: não roda
    escrever(p, "src/telas/inicio.js", "RUIM\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return recusou(r, "teste vermelho"), r[1]


def automacao(p: Path) -> tuple[bool, str]:
    instalacao = git(p, "rev-parse", "HEAD")
    r0 = esteira(p, "--automacao", instalacao, PULSO_SEM_ENV="1")
    commit_por_baixo(p, {"src/telas/inicio.js": "BOM direto\n"}, "front: commit direto")
    r1 = esteira(p, "--automacao", "HEAD~1..HEAD", PULSO_SEM_ENV="1")
    commit_por_baixo(p, {"src/telas/inicio.js": "BOM pela esteira\n"}, "front: src/telas/inicio.js\n\nEsteira: entrou")
    registro = p.parent / f"{p.name}-registro"
    r2 = esteira(p, "--automacao", "HEAD~1..HEAD", PULSO_REGISTRO=str(registro), PULSO_SEM_ENV="1")
    commit_por_baixo(p, {"src/telas/inicio.js": "RUIM\n"}, "front: src/telas/inicio.js\n\nEsteira: entrou")
    r3 = esteira(p, "--automacao", "HEAD~1..HEAD", PULSO_SEM_ENV="1")
    commit_por_baixo(p, {".delta-11/registro/r2.md": "registro\n"}, "registro do Delta-11")
    r4 = esteira(p, "--automacao", "HEAD~1..HEAD")
    certo = (entrou(r0) and recusou(r1, "sem `Esteira: entrou`") and entrou(r2) and "testou" in (registro.read_text() if registro.exists() else "")
             and recusou(r3, "teste vermelho") and entrou(r4) and "nada a montar" in r4[1])
    return certo, "\n".join(r[1] for r in (r0, r1, r2, r3, r4))


def presa_pela_caixa(p: Path) -> tuple[bool, str]:
    escrever(p, "testes/e.test.sh", f'echo x > "{p}/invadiu" 2>/dev/null; echo x > "{p}/.git/invadiu" 2>/dev/null; true\n')
    r = esteira(p, "shield", "testes/e.test.sh")
    return entrou(r) and not (p / "invadiu").exists() and not (p / ".git/invadiu").exists(), r[1]


def fluxo_sem_publicar(p: Path) -> tuple[bool, str]:
    """Sem `publicar:`, o teste do fluxo principal roda na cópia, antes do commit, como mais um teste."""
    commit_por_baixo(p, {"esteira-comandos.txt": COMANDOS.replace("publicar: sh publicar.sh\n", ""),
                         "fluxo.sh": 'echo fluxo >> "$PULSO_REGISTRO"\ngrep -q BOM src/telas/inicio.js || { echo "FALHOU: o fluxo principal"; exit 1; }\n'},
                     "back: esteira-comandos.txt\n\nEsteira: entrou")
    for arquivo in ("esteira-comandos.txt", "fluxo.sh"):
        escrever(p, arquivo, no_head(p, arquivo) or "")
    antes = git(p, "rev-parse", "HEAD")
    registro = p.parent / f"{p.name}-registro"
    escrever(p, "src/telas/inicio.js", "BOM 8\n")
    r1 = esteira(p, "front", "src/telas/inicio.js", PULSO_REGISTRO=str(registro))
    rodou = registro.read_text().split() if registro.exists() else []
    em_cima = git(p, "rev-parse", "HEAD^") == antes
    escrever(p, "src/telas/inicio.js", "BEM\n")  # sem BOM, só o fluxo falha (o teste que conferia BOM saiu antes, por baixo)
    commit_por_baixo(p, {"testes/a.test.sh": "true\n"}, "shield: testes/a.test.sh\n\nEsteira: entrou")
    escrever(p, "testes/a.test.sh", "true\n")
    meio = git(p, "rev-parse", "HEAD")
    r2 = esteira(p, "front", "src/telas/inicio.js", PULSO_REGISTRO=str(registro))
    return (entrou(r1) and "fluxo" in rodou and rodou.index("fluxo") > rodou.index("testou") and em_cima
            and recusou(r2, "o teste do fluxo principal falhou: FALHOU: o fluxo principal") and git(p, "rev-parse", "HEAD") == meio), r1[1] + r2[1]


def valor_esperado_mudado(p: Path) -> tuple[bool, str]:
    """Trocar o que um teste confere, comentar a conferência ou desligar o que vem embaixo pede o aval, mesmo sem tirar palavras."""
    escrever(p, "testes/a.test.sh", "grep -q B src/telas/inicio.js\n")
    r1 = esteira(p, "shield", "testes/a.test.sh")
    escrever(p, "testes/a.test.sh", "grep -q BOM src/telas/inicio.js\n")
    escrever(p, "testes/b.test.sh", "test -f dist/app.txt\ntrue # test -f .dependencias-instaladas\n")
    r2 = esteira(p, "shield", "testes/b.test.sh")
    escrever(p, "testes/b.test.sh", ARQUIVOS["testes/b.test.sh"])
    escrever(p, "testes/d.test.sh", "exit 0\n! grep -rq QUEBRA src\n")
    r3 = esteira(p, "shield", "testes/d.test.sh")
    escrever(p, "testes/d.test.sh", "! grep -rq QUEBRA src\necho conferido\n")  # mexer sem tocar na conferência entra
    r4 = esteira(p, "shield", "testes/d.test.sh")
    return (recusou(r1, "linha que confere") and recusou(r2, "linha que confere") and recusou(r3, "desliga o que vem embaixo")
            and entrou(r4)), "\n".join(r[1] for r in (r1, r2, r3, r4))


def valor_esperado_com_aval(p: Path) -> tuple[bool, str]:
    escrever(p, "testes/a.test.sh", "grep -q BO src/telas/inicio.js\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/shield-1.md", "Situação: encerrado\n- Aval: testes/a.test.sh\n")
    r = esteira(p, "shield", "testes/a.test.sh")
    return entrou(r) and no_head(p, "testes/a.test.sh") == "grep -q BO src/telas/inicio.js\n", r[1]


def aval_do_revisor_no_caminho_pequeno(p: Path) -> tuple[bool, str]:
    """Sem enderecos.txt (sem SHIELD), o Aval vem da linha do Revisor da camada aberta; com territórios, a dele não vale."""
    escrever(p, "testes/a.test.sh", "grep -q BO src/telas/inicio.js\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/revisor-1.md", "Situação: encerrado\n- Aval: testes/a.test.sh\n")
    r1 = esteira(p, "shield", "testes/a.test.sh")
    (p / ".delta-11/regras/enderecos.txt").unlink()
    r2 = esteira(p, "front", "testes/a.test.sh")
    return recusou(r1, "o Revisor") and entrou(r2), r1[1] + r2[1]


def montar_mudado_sem_aval(p: Path) -> tuple[bool, str]:
    escrever(p, "esteira-comandos.txt", COMANDOS.replace("montar: sh montar.sh", "montar: rm -f testes/c.test.sh && sh montar.sh"))
    r1 = esteira(p, "back", "esteira-comandos.txt")
    escrever(p, "esteira-comandos.txt", COMANDOS.replace("instalar: sh instalar.sh", "instalar: sh instalar.sh && rm -f testes/c.test.sh"))
    r2 = esteira(p, "back", "esteira-comandos.txt")
    escrever(p, "esteira-comandos.txt", COMANDOS + "app: Gastos\natalho: ctrl+option+g\n")  # o app e o atalho não mexem em teste
    r3 = esteira(p, "back", "esteira-comandos.txt")
    return recusou(r1, "muda o `montar:`") and recusou(r2, "muda o `instalar:`") and entrou(r3), "\n".join(r[1] for r in (r1, r2, r3))


def construtor_unico(p: Path) -> tuple[bool, str]:
    """Sem enderecos.txt (o caminho pequeno), o Construtor único entrega todo o código: .gitignore, os comandos e os testes."""
    escrever(p, ".gitignore", ARQUIVOS[".gitignore"] + ".build/\n")
    r1 = esteira(p, "front", ".gitignore")
    (p / ".delta-11/regras/enderecos.txt").unlink()
    escrever(p, "esteira-comandos.txt", COMANDOS + "app: Gastos\n")
    escrever(p, "testes/e.test.sh", "test -f dist/app.txt\n")
    r2 = esteira(p, "front", ".gitignore", "esteira-comandos.txt", "testes/e.test.sh")
    return (recusou(r1, ".gitignore é do BACK") and entrou(r2) and ".build/" in (no_head(p, ".gitignore") or "")
            and no_head(p, "testes/e.test.sh") is not None), r1[1] + r2[1]


def bloco_coracao_na_camada_2(p: Path) -> tuple[bool, str]:
    """O bloco Coração do caminho pequeno mora na pasta camada-2: o Parar do dono vale ali; na do bloco Luz (camada-1), não."""
    escrever(p, ".delta-11/quadro/camada-1/abertura.md", "# Abertura\n\nBloco: Luz (Camada 1)\nParar do dono: 2026-10-24\n")
    escrever(p, ".delta-11/quadro/camada-1/quadro.md", "# Quadro\n\nSituação: aberto\n")
    (p / "testes/c.test.sh").unlink()
    r1 = esteira(p, "shield", "testes/c.test.sh")
    escrever(p, ".delta-11/quadro/camada-2/abertura.md", "# Abertura\n\nBloco: Coração (Camadas 2 e 3)\nParar do dono: 2026-10-24\n")
    escrever(p, ".delta-11/quadro/camada-2/quadro.md", "# Quadro\n\nSituação: aberto\n")
    r2 = esteira(p, "back", "testes/c.test.sh")
    return recusou(r1, "Aval") and entrou(r2) and "Parar do dono" in r2[1] and no_head(p, "testes/c.test.sh") is None, r1[1] + r2[1]


def recusa_mostra_a_causa(p: Path) -> tuple[bool, str]:
    """O resumo do RECUSOU traz a última linha de erro do comando, e a dica para a caixa de um programa dentro da caixa."""
    rodar = ('if grep -q SWIFT src/telas/inicio.js; then echo "error: sandbox-exec: sandbox_apply: Operation not permitted";'
             ' i=0; while [ $i -lt 30 ]; do echo "compilando a parte $i"; i=$((i+1)); done; exit 1; fi\n' + ARQUIVOS["testes/rodar.sh"])
    commit_por_baixo(p, {"testes/rodar.sh": rodar}, "shield: testes/rodar.sh\n\nEsteira: entrou")
    escrever(p, "testes/rodar.sh", rodar)
    escrever(p, "src/telas/inicio.js", "BOM SWIFT\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return recusou(r, "teste vermelho: error: sandbox-exec: sandbox_apply: Operation not permitted") and "--disable-sandbox" in ultima(r[1]), r[1]


def ambiente_do_dono(p: Path) -> tuple[bool, str]:
    """Um app de Mac publica no ambiente do dono que `ambiente:` declara; sem a linha, a caixa barra; fora dos lugares do dono, recusa."""
    pasta = Path.home() / "Library" / "Logs" / f"delta11-pulso-esteira-{os.getpid()}-{p.parent.name}"
    publicar = f'mkdir -p "{pasta}" && cp dist/app.txt "{pasta}/app.txt"\n'
    try:
        commit_por_baixo(p, {"publicar.sh": publicar}, "back: publicar.sh\n\nEsteira: entrou")
        escrever(p, "publicar.sh", publicar)
        escrever(p, "src/telas/inicio.js", "BOM 9\n")
        r1 = esteira(p, "front", "src/telas/inicio.js")
        barrado = not (pasta / "app.txt").exists()
        escrever(p, "esteira-comandos.txt", COMANDOS + f"ambiente: ~/Library/Logs/{pasta.name}\n")
        r2 = esteira(p, "back", "esteira-comandos.txt")
        publicado = (pasta / "app.txt").is_file()
        fluxo = f'echo dado-de-teste > "{pasta}/do-fluxo.txt"\n'  # o fluxo principal nunca grava nos dados reais do dono
        commit_por_baixo(p, {"fluxo.sh": fluxo}, "back: fluxo.sh\n\nEsteira: entrou")
        escrever(p, "fluxo.sh", fluxo)
        escrever(p, "src/telas/inicio.js", "BOM 10\n")
        r4 = esteira(p, "front", "src/telas/inicio.js")
        fluxo_barrado = not (pasta / "do-fluxo.txt").exists()
        escrever(p, "esteira-comandos.txt", COMANDOS + "ambiente: ~/Documents/delta11-pulso\n")
        r3 = esteira(p, "back", "esteira-comandos.txt")
    finally:
        if pasta.name.startswith("delta11-pulso-esteira-") and pasta.is_dir():
            shutil.rmtree(pasta)
    return (entrou(r1) and "ALERTA: a publicação falhou" in r1[1] and barrado and entrou(r2) and publicado and "ALERTA" not in r2[1]
            and recusou(r3, "fora do ambiente do dono") and "~/Applications/ (o app: <App>.app)" in ultima(r3[1])
            and entrou(r4) and "ALERTA: o teste do fluxo principal falhou" in r4[1] and fluxo_barrado), "\n".join(r[1] for r in (r1, r2, r4, r3))


def liga_o_remoto(p: Path) -> tuple[bool, str]:
    bare = p.parent / f"{p.name}-novo.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], capture_output=True, env=AMBIENTE)
    r1 = esteira(p, "front", "--remoto", str(bare))
    r2 = esteira(p, "back", "--remoto", str(bare))
    return recusou(r1, "quem liga o remoto é o BACK") and entrou(r2) and git(bare, "rev-parse", "main") == git(p, "rev-parse", "HEAD"), r1[1] + r2[1]


def entrego_junto_com_pontuacao(p: Path) -> tuple[bool, str]:
    """`Entrego junto:` escrito como frase: a vírgula, o ponto final e a nota entre parênteses não fazem parte do nome."""
    escrever(p, "src/telas/inicio.js", "BOM junto\n")
    escrever(p, "banco/x.sql", "select 3;\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/front-1.md", "Situação: trabalhando\n- Entrego junto: src/telas/inicio.js (mudado), src/telas/velho.js (apagado).\n")
    escrever(p, ".delta-11/quadro/camada-3/linhas/vault-1.md", "Situação: encerrado\n- Entrego junto: banco/x.sql.\n")
    r = esteira(p, "front,vault", "src/telas/inicio.js", "banco/x.sql")
    return entrou(r) and no_head(p, "banco/x.sql") == "select 3;\n", r[1]


def recusa_cita_a_linha_da_falha(p: Path) -> tuple[bool, str]:
    """O RECUSOU cita a linha da falha do teste, não um aviso com "erros" no caminho nem o resumo do fim."""
    rodar = ('if grep -q CITA src/telas/inicio.js; then echo "warning: found 1 file(s) which are unhandled; /x/copia/logica/erros/LEIAME.md";'
             ' echo "testes/a.test.sh:3: error: esperava BOM, veio CITA"; echo "Executed 4 tests, with 1 failure"; exit 1; fi\n' + ARQUIVOS["testes/rodar.sh"])
    commit_por_baixo(p, {"testes/rodar.sh": rodar}, "shield: testes/rodar.sh\n\nEsteira: entrou")
    escrever(p, "testes/rodar.sh", rodar)
    escrever(p, "src/telas/inicio.js", "BOM CITA\n")
    r = esteira(p, "front", "src/telas/inicio.js")
    return recusou(r, "teste vermelho: testes/a.test.sh:3: error: esperava BOM") and "LEIAME" not in ultima(r[1]), r[1]


def com_vermelho(p: Path, vermelho: str) -> None:
    commit_por_baixo(p, {"esteira-comandos.txt": COMANDOS + f"vermelho: {vermelho}\n"}, "back: esteira-comandos.txt\n\nEsteira: entrou")
    escrever(p, "esteira-comandos.txt", COMANDOS + f"vermelho: {vermelho}\n")
    escrever(p, "src/telas/inicio.js", "BOM 2\n")


def vermelho_que_falha_com_a_marca(p: Path) -> tuple[bool, str]:
    """`vermelho:` que roda os testes com o vermelho plantado e falha dizendo a marca da esteira: os testes rodam de verdade, ENTROU."""
    com_vermelho(p, 'sh testes/rodar.sh && echo "FALHOU: o vermelho plantado ($DELTA11_VERMELHO)" && exit 1')
    r = esteira(p, "front", "src/telas/inicio.js")
    marcas = [l for l in r[1].splitlines() if "vermelho-" in l]
    return entrou(r) and no_head(p, "src/telas/inicio.js") == "BOM 2\n" and not marcas, r[1]


def vermelho_que_passa_ou_sem_marca(p: Path) -> tuple[bool, str]:
    """O vermelho plantado que passa (os testes não rodam) ou falha sem a marca (falhou outra coisa): RECUSOU, nada entra."""
    com_vermelho(p, "sh testes/rodar.sh")
    antes = git(p, "rev-parse", "HEAD")
    r1 = esteira(p, "front", "src/telas/inicio.js")
    r2_p = p.parent / "outro"
    shutil.copytree(p, r2_p, symlinks=True)
    com_vermelho(r2_p, 'echo "FALHOU: vermelho-0000"; exit 1')
    r2 = esteira(r2_p, "front", "src/telas/inicio.js")
    return (recusou(r1, "os testes não rodam de verdade: o sentinela passou")
            and recusou(r2, "não falhou com a marca da esteira") and git(p, "rev-parse", "HEAD") == antes), r1[1] + r2[1]


def sobras_e_sinal_de_rodando(p: Path) -> tuple[bool, str]:
    """No começo, a esteira apaga as cópias de esteiras que morreram; enquanto roda, deixa o sinal em .delta-11/esteira/rodando/,
    que some no fim."""
    morto = subprocess.Popen(["true"])
    morto.wait()
    sobra = Path(tempfile.gettempdir()).resolve() / f"esteira-{morto.pid}-pulso{os.getpid()}"
    (sobra / "copia").mkdir(parents=True, exist_ok=True)
    escrever(p, "src/telas/inicio.js", "BOM 4\n")
    sinal = p.parent / f"{p.name}-sinal"
    processo = subprocess.Popen(["sh", "esteira", "front", "src/telas/inicio.js"], cwd=p, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                env={**AMBIENTE, "PULSO_SINAL": str(sinal)})
    limite = time.time() + 120
    while not sinal.exists() and time.time() < limite and processo.poll() is None:
        time.sleep(0.1)
    durante = sorted(a.name for a in (p / ".delta-11/esteira/rodando").glob("*"))
    Path(str(sinal) + ".solto").write_text("")
    saida = processo.communicate(timeout=300)[0]
    depois = sorted(a.name for a in (p / ".delta-11/esteira/rodando").glob("*"))
    certo = (processo.returncode == 0 and not sobra.exists() and durante == [f"front-{processo.pid}"] and not depois)
    shutil.rmtree(sobra, ignore_errors=True)
    return certo, saida + f"\ndurante={durante} depois={depois} sobra={sobra.exists()}"


def sem_espaco_livre(p: Path) -> tuple[bool, str]:
    """Com menos espaço livre que `espaco_livre_min`, a esteira recusa antes de montar e diz que o aviso vai ao dono."""
    escrever(p, "src/telas/inicio.js", "BOM 5\n")
    antes = git(p, "rev-parse", "HEAD")
    r = esteira(p, "front", "src/telas/inicio.js", DELTA11_ESPACO_LIVRE_MIN=str(10 ** 18))
    return recusou(r, "o Mac está sem espaço") and "chamada 2" in ultima(r[1]) and git(p, "rev-parse", "HEAD") == antes, r[1]



def caixa_nao_abre_app(p: Path) -> tuple[bool, str]:
    """A caixa nega abrir app, mandar ordem a outro programa, simular tecla, ligar serviço e chegar à tela: só a tela do app, na hora
    liberada. Provado sem abrir nada: o `open` e o `launchctl` não rodam, e um programa lá dentro não acha sessão de tela."""
    caixa = ["python3", "-I", "-B", ".claude/hooks/delta-11/caixa-do-produto.py"]
    abre = subprocess.run([*caixa, "/usr/bin/open", "-h"], cwd=p, capture_output=True, text=True, env=AMBIENTE)  # inofensivo: nem a ajuda do open roda
    liga = subprocess.run([*caixa, "/bin/launchctl", "print", "system"], cwd=p, capture_output=True, text=True, env=AMBIENTE)
    escrever(p, "sessao.py", 'import ctypes, ctypes.util\ncg = ctypes.CDLL(ctypes.util.find_library("CoreGraphics"))\n'
                             'cg.CGSessionCopyCurrentDictionary.restype = ctypes.c_void_p\nprint("SESSAO" if cg.CGSessionCopyCurrentDictionary() else "SEM")\n')
    tela = subprocess.run([*caixa, "python3", "-I", "sessao.py"], cwd=p, capture_output=True, text=True, env=AMBIENTE)
    barrado = lambda feito: feito.returncode == 71 or "Operation not permitted" in feito.stdout + feito.stderr  # a caixa negou rodar
    return barrado(abre) and barrado(liga) and "SEM" in tela.stdout, abre.stderr + liga.stderr + tela.stdout + tela.stderr


def copia_de_ataque(p: Path) -> tuple[bool, str]:
    """A cópia de ataque do Destruidor: o último commit como repositório novo no temporário, sem o que conta como foi feito; a esteira
    entra nela pela caixa no modo de olhar, e o produto fica intacto."""
    nome = f"pulso-{os.getpid()}-{p.parent.name}"
    caixa = ["python3", "-I", "-B", ".claude/hooks/delta-11/caixa-do-produto.py"]
    feito = subprocess.run([*caixa, "copia-de-ataque", nome], cwd=p, capture_output=True, text=True, env=AMBIENTE)
    copia = Path(tempfile.gettempdir()).resolve() / f"delta11-ataque-{nome}"
    try:
        montada = (feito.returncode == 0 and (copia / "esteira").is_file() and not (copia / ".delta-11/quadro/camada-3").exists()
                   and (copia / ".delta-11/quadro/ataque/quadro.md").is_file() and not (copia / ".env").exists()
                   and (copia / ".delta-11/regras/enderecos.txt").is_file())
        escrever(copia, "src/telas/inicio.js", "BOM ataque\n")
        publicado = p.parent / f"{p.name}-publicado-no-ataque"
        r = subprocess.run([*caixa, "olhar", "--raiz", str(copia), "sh", "esteira", "front", "src/telas/inicio.js"], cwd=p, capture_output=True,
                           text=True, env={**AMBIENTE, "PULSO_SEM_ENV": "1", "PULSO_PUBLICADO": str(publicado)}, timeout=300)
        la = (r.returncode, r.stdout + r.stderr)
        relato = subprocess.run([*caixa, "olhar", "relato-da-copia", nome], cwd=p, capture_output=True, text=True, env=AMBIENTE)
        subprocess.run([*caixa, "olhar", "apagar-copia-de-ataque", nome], cwd=p, capture_output=True, text=True, env=AMBIENTE)
        certo = (montada and entrou(la) and git(copia if copia.exists() else p, "show", "HEAD:src/telas/inicio.js") in ("BOM ataque", "BOM")
                 and no_head(p, "src/telas/inicio.js") == "BOM\n" and not publicado.exists() and "ensaio" in la[1]
                 and relato.returncode == 0 and "ENTROU" in relato.stdout and not copia.exists())
        return certo, feito.stdout + feito.stderr + la[1]
    finally:
        shutil.rmtree(copia, ignore_errors=True)


def marca_do_vermelho_reservada(p: Path) -> tuple[bool, str]:
    """Só o teste lê a marca do sentinela: no código do produto, RECUSOU; num teste, pede o aval do SHIELD."""
    escrever(p, "src/telas/ajuda.js", "if (process.env.DELTA11_VERMELHO) {}\n")
    antes = git(p, "rev-parse", "HEAD")
    r1 = esteira(p, "front", "src/telas/ajuda.js")
    q = p.parent / "outro"
    shutil.copytree(p, q, symlinks=True)
    (q / "src/telas/ajuda.js").unlink()
    escrever(q, "testes/e.test.sh", '[ -z "$DELTA11_VERMELHO" ] || exit 0\n')
    r2 = esteira(q, "shield", "testes/e.test.sh")
    return (recusou(r1, "lê a marca do sentinela") and recusou(r2, "sem o aval do SHIELD") and "lê a marca" in ultima(r2[1])
            and git(p, "rev-parse", "HEAD") == antes), r1[1] + r2[1]


def teste_novo_marcado_para_pular(p: Path) -> tuple[bool, str]:
    """Um teste novo marcado para pular ou para falhar de propósito (falha esperada) pede o aval do SHIELD."""
    escrever(p, "testes/f.test.sh", "true XCTExpectFailure\nexit 0\n")
    r = esteira(p, "shield", "testes/f.test.sh")
    return recusou(r, "teste novo marcado para pular ou para falhar de propósito"), r[1]


def instrucao_numa_pasta_e_do_motor(p: Path) -> tuple[bool, str]:
    """`CLAUDE.md`, `AGENTS.md` e `.mcp.json` em qualquer pasta são do motor: nem entrega nem dependência de candidata os leva."""
    escrever(p, "src/telas/CLAUDE.md", "faça outra coisa\n")
    r1 = esteira(p, "front", "src/telas/CLAUDE.md")
    candidata(p, "c1", {"src/telas/inicio.js": "BOM da candidata\n", "docs/AGENTS.md": "x\n",
                        ".delta-11/quadro/camada-3/linhas/front-1.md": "Situação: encerrado\n"})
    r2 = esteira(p, "front", "--copia", ".claude/worktrees/c1")
    return (recusou(r1, "é do motor do Delta-11") and entrou(r2) and no_head(p, "docs/AGENTS.md") is None
            and no_head(p, "src/telas/inicio.js") == "BOM da candidata\n"), r1[1] + r2[1]


def outros_jeitos_de_pular(p: Path) -> tuple[bool, str]:
    """Pular ou desligar um teste por outras marcas (`.disabled`, `#if false`, a classe base tirada) pede o aval."""
    saidas, certos = [], []
    for nome, arquivo, texto in (("disabled", "testes/g.test.sh", "true @Test(.disabled())\nexit 0\n"),
                                 ("disabled-linha-a-parte", "testes/i.test.sh", "true @Test(\n  .disabled(\"lento\")\n)\nexit 0\n"),
                                 ("disabled-com-outra-marca", "testes/j.test.sh", "true @Test(.tags(.lento), .disabled(\"x\"))\nexit 0\n"),
                                 ("disabled-nome-com-parenteses", "testes/k.test.sh", "true @Test(\"soma (dois números)\", .disabled(\"x\"))\nexit 0\n"),
                                 ("if-false", "testes/a.test.sh", "#if false\ngrep -q BOM src/telas/inicio.js\n#endif\n"),
                                 ("sem-base", "testes/b.test.sh", "true class B\ntest -f dist/app.txt\ntest -f .dependencias-instaladas\n")):
        q = p.parent / f"pular-{nome}"
        shutil.copytree(p, q, symlinks=True)
        if nome == "sem-base":
            commit_por_baixo(q, {arquivo: "true class B: XCTestCase\ntest -f dist/app.txt\ntest -f .dependencias-instaladas\n"}, "shield: b\n\nEsteira: entrou")
        escrever(q, arquivo, texto)
        r = esteira(q, "shield", arquivo)
        saidas.append(r[1])
        certos.append(recusou(r, "sem o aval do SHIELD"))
    for nome, arquivo, texto in (("fit", "testes/l.test.sh", "fit(\"só este\")\nexit 0\n"),
                                 ("qunit", "testes/m.test.sh", "true 'QUnit.only(\"x\")'\nexit 0\n"),
                                 ("doc-embrulha", "testes/a.test.sh", "/**\ngrep -q BOM src/telas/inicio.js\n*/\n")):
        q = p.parent / f"pular-{nome}"
        shutil.copytree(p, q, symlinks=True)
        escrever(q, arquivo, texto)
        r = esteira(q, "shield", arquivo)
        saidas.append(r[1])
        certos.append(recusou(r, "sem o aval do SHIELD"))
    honesto = p.parent / "pular-honesto"  # um teste novo e honesto que confere um botão desligado entra
    shutil.copytree(p, honesto, symlinks=True)
    escrever(honesto, "testes/h.test.sh", "# confere que botao.disabled fica ligado no formulário vazio\ntrue '  .disabled(true)'\n"
                                          "true '@Test(arguments: [ButtonState.enabled, ButtonState.disabled])'\ntrue '  ButtonState.disabled,'\n"
                                          "true 'Ideia.find().skip(10)'\ntrue \"api.todo('abc-123')\"\ntrue 'expect(opcoes.skip)'\ntrue 'await modelo.fit(xs, ys)'\n"
                                          "true \"ajustador.fit('título longo', 20)\"\n# /** a documentação de um teste\n"
                                          "true '/** confere o formulário'\ntrue ' * vazio'\ntrue ' */'\ntest -f dist/app.txt\n")
    r = esteira(honesto, "shield", "testes/h.test.sh")
    saidas.append(r[1])
    certos.append(entrou(r))
    return all(certos), "\n".join(saidas)


CASOS = [
    ("entrega simples: entra com a marca, numa cópia limpa (com o .env, sem o trabalho pela metade), instala, monta e testa; índice acertado; relato inteiro", entrega_simples),
    ("fora do território: RECUSOU e nada entra", fora_do_territorio),
    ("sem enderecos.txt, todo o código é de qualquer Construtor", sem_enderecos),
    ("entrega conjunta sem o `Entrego junto:` do colega: RECUSOU", conjunta_sem_aceite),
    ("entrega conjunta com o `Entrego junto:` de cada um, numa camada aberta: ENTROU", conjunta_com_aceite),
    ("o SCOUT entrega em qualquer território e em .delta-11/alarmes/", scout_em_qualquer_territorio),
    ("só o SCOUT entrega em .delta-11/alarmes/", so_o_scout_nos_alarmes),
    ("o que é do motor (.claude/, a própria esteira) não entra", motor_nao_entra),
    ("candidata escolhida: pasta nova, arquivo mudado e dependência entram; as cópias somem e as linhas vão para candidatas/", candidata_escolhida),
    ("candidata que mexe no território de outro: RECUSOU e a cópia fica", candidata_fora_do_territorio),
    ("dependência da candidata: só arquivo novo numa pasta fora de todo território; o da raiz ou o que já existe, RECUSOU", candidata_dependencia_com_limite),
    ("descarte sem escolhida: a cópia some, a linha vai para candidatas/, nada entra", descarte),
    ("arquivo apagado: entregar o apagado o tira, depois de testar", arquivo_apagado),
    ("Parar do dono: o BACK apaga em qualquer território, testes inclusive, sem montar nem testar", parar),
    ("teste que falha: RECUSOU, nada entra e a mudança fica na pasta", teste_que_falha),
    ("teste apagado sem o aval do SHIELD: RECUSOU", teste_apagado_sem_aval),
    ("teste apagado com `Aval:` na linha do SHIELD: ENTROU", teste_apagado_com_aval),
    ("teste afrouxado ou marcado para pular sem aval: RECUSOU", teste_afrouxado_sem_aval),
    ("mudar o `testar:` de esteira-comandos.txt sem aval: RECUSOU", testar_mudado_sem_aval),
    ("outro entrou antes do commit: refaz a montagem e os testes e entra por cima", outro_entrou_antes),
    ("outro entrou no mesmo arquivo: RECUSOU (choque)", outro_entrou_no_mesmo_arquivo),
    ("remoto com avanço simples: traz, entra por cima e envia", remoto_avanco_simples),
    ("remoto com o registro daqui: junta por cima (merge-tree), entra e envia", remoto_com_registro_daqui),
    ("remoto com código dos dois lados: RECUSOU com aviso ao ARQUITETO", remoto_com_choque),
    ("ensaio (.delta-11/esteira/ensaio): entra, mas não envia nem publica", ensaio),
    ("publica pela caixa só o que a montagem gera, com a credencial do cofre, e roda o fluxo principal", publica),
    ("sem esteira-comandos.txt, ou sem `testar:`: RECUSOU ensinando o formato", sem_comandos),
    ("roda a esteira do último commit, não a mudada na pasta", versao_do_ultimo_commit),
    ("automação: recusa commit sem `Esteira: entrou` e o que não passa nos testes; aceita o da instalação e o só de .delta-11/", automacao),
    ("--remoto: só o BACK liga o remoto, e o envio sobe", liga_o_remoto),
    ("sem `publicar:`, o fluxo principal roda na cópia depois dos testes; falhou: RECUSOU", fluxo_sem_publicar),
    ("trocar o valor que um teste confere, comentar a conferência ou desligar o que vem embaixo, sem aval: RECUSOU; mexer sem tocar nela entra", valor_esperado_mudado),
    ("trocar o valor que um teste confere com `Aval:` na linha do SHIELD: ENTROU", valor_esperado_com_aval),
    ("sem enderecos.txt, o Aval vem da linha do Revisor; com territórios, não", aval_do_revisor_no_caminho_pequeno),
    ("mudar o `montar:` ou o `instalar:` sem aval: RECUSOU; acrescentar `app:` e `atalho:` entra", montar_mudado_sem_aval),
    ("sem enderecos.txt, o Construtor único entrega .gitignore, esteira-comandos.txt e testes; com territórios, o .gitignore é do BACK", construtor_unico),
    ("o bloco Coração na pasta camada-2: o Parar do dono vale; o bloco Luz (camada-1) não é o Parar", bloco_coracao_na_camada_2),
    ("o RECUSOU mostra a última linha de erro do comando e a dica do `--disable-sandbox`", recusa_mostra_a_causa),
    ("`Entrego junto:` escrito como frase (vírgulas, ponto final, notas entre parênteses): ENTROU", entrego_junto_com_pontuacao),
    ("o RECUSOU cita a linha da falha do teste, não um caminho com 'erros' nem o resumo", recusa_cita_a_linha_da_falha),
    ("`vermelho:` que falha com a marca da esteira: ENTROU, e a marca não aparece na tela", vermelho_que_falha_com_a_marca),
    ("`vermelho:` que passa, ou que falha sem a marca: RECUSOU", vermelho_que_passa_ou_sem_marca),
    ("as cópias de esteiras mortas somem no começo; o sinal de rodando existe só enquanto ela roda", sobras_e_sinal_de_rodando),
    ("sem espaço livre (`espaco_livre_min`): RECUSOU antes de montar, com a chamada 2", sem_espaco_livre),
    ("a marca do sentinela é só do teste: no código do produto, RECUSOU; num teste, pede o aval", marca_do_vermelho_reservada),
    ("teste novo marcado para pular ou para falhar de propósito: pede o aval", teste_novo_marcado_para_pular),
    ("outros jeitos de pular ou desligar um teste (@Test(.disabled), #if false, a classe base tirada): pedem o aval; botao.disabled num teste honesto entra", outros_jeitos_de_pular),
    ("CLAUDE.md, AGENTS.md e .mcp.json em qualquer pasta são do motor", instrucao_numa_pasta_e_do_motor),
]
if CAIXA_DO_MAC:  # só no Mac, fora de outra caixa: a caixa do produto prende de verdade (como no pulso da trava)
    CASOS.append(("os comandos do produto rodam presos pela caixa do produto: não gravam na pasta principal nem em .git/", presa_pela_caixa))
    CASOS.append(("a cópia de ataque do Destruidor: o último commit, sem o quadro nem o .env; a esteira entra nela pela caixa sem publicar; o relato se lê pela caixa; a cópia se apaga", copia_de_ataque))
    CASOS.append(("pela caixa do produto, nada abre app no Mac do dono (lsopen negado)", caixa_nao_abre_app))
    CASOS.append(("app de Mac: publica no ambiente do dono que `ambiente:` declara; sem a linha, a caixa barra (ALERTA); fora dos lugares do dono, RECUSOU ensinando", ambiente_do_dono))


def main() -> int:
    falhas: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp).resolve()
        molde = modelo(base)
        if no_head(molde, "esteira") is None:
            print("PULSO DA ESTEIRA FALHOU — o produto de mentira não montou")
            return 1

        def rodar_caso(indice: int) -> tuple[bool, str]:
            pasta = base / f"caso-{indice:02d}"
            pasta.mkdir()
            p = pasta / "produto"
            shutil.copytree(molde, p, symlinks=True)
            try:
                return CASOS[indice][1](p)
            except Exception as erro:  # um caso que quebra é um caso errado
                return False, f"{type(erro).__name__}: {erro}"
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as grupo:
            resultados = list(grupo.map(rodar_caso, range(len(CASOS))))
        for (nome, _), (certo, saida) in zip(CASOS, resultados):
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else "\n      " + "\n      ".join(saida.strip().splitlines()[-6:])))
            if not certo:
                falhas.append(nome)
    if falhas:
        print(f"PULSO DA ESTEIRA FALHOU — {len(falhas)} de {len(CASOS)} casos: " + "; ".join(falhas))
        return 1
    print(f"PULSO DA ESTEIRA OK — {len(CASOS)} casos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
