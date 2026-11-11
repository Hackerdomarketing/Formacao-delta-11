#!/usr/bin/env python3
"""Trava do Delta-11 v7: o programa de agentes a chama antes de toda ferramenta que escreve, lê, usa o terminal, chama
agente, manda mensagem, pesquisa na internet ou usa uma ferramenta de fora (o navegador e os programas do computador).

Lê pelo tradutor (motor.py: o programa é o dito no fim do comando, como `trava.py claude-code`) qual agente age, com
qual ferramenta e em quais arquivos, e confere no mapa lugares.json (que mora ao lado deste arquivo, em
.claude/hooks/delta-11/, área que nenhum papel escreve e que a caixa de areia protege). Sai com 0 para deixar e com 2
para barrar, explicando o motivo. Sem programa dito, barra. Qualquer erro barra: no Claude Code, a configuração a chama
com "onFailure": "block", então nem um script ausente libera.
O disco do Mac não diferencia maiúsculas: a trava também não.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
import subprocess
import re
import shlex
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import registro_de_cronos as reg  # noqa: E402
import motor  # noqa: E402
TEMPORARIO = r"(?:/dev/null|/tmp/|\"?\$\{?TMPDIR)"
COMANDO_QUE_GRAVA = r"(?<![-\w.])(cp|mv|rm|ln|mkdir|touch|chmod|truncate|dd|patch|rsync|tee|unzip|wget|(?<![\w-]\s)install)(?=\s|$)(?!\s+(?:-\w+\s+)*" + TEMPORARIO + r")"
# Gravar pelo terminal: redirecionamento (também 2> e &>) para fora do temporário, edição no lugar, comando que grava,
# e programas de linguagem que abrem arquivo para escrita. O texto entre aspas (o que o comando manda) não conta,
# salvo o código de um programa de linguagem, que é conferido inteiro.
REDIRECIONA = re.compile(r"(?:^|[^<>&=-])(?:\d|&)?>>?(?!&)(?!=)(?!\s*" + TEMPORARIO + r")(?!\s*\d)")
GRAVA_PELO_TERMINAL = re.compile(r"\bsed\s+(-[a-zA-Z]*\s+)*-i|\bperl\s+(-[a-zA-Z]*\s+)*-i|\bcurl\b[^|;&]*\s-(o|O|-output)\b"
                                 r"|\btar\b[^|;&]*\s-?[a-zA-Z]*x|" + COMANDO_QUE_GRAVA)
SAIDA_DE_CURL_NO_TEMPORARIO = re.compile(r"\s-(o|O|-output)\s*" + TEMPORARIO)
PROGRAMA_QUE_GRAVA = re.compile(r"open\([^)]*['\"][wax+]b?['\"]|mode\s*=\s*['\"][wax+]|write_text|write_bytes|writeFile|appendFile|createWriteStream"
                               r"|fs\.write|shutil\.|os\.(remove|rename|unlink|system|symlink|link)|\bsymlink|subprocess|child_process|execSync|spawnSync")
GIT_QUE_MUDA = re.compile(r"(?:^|[;&|(\n]\s*|(?:sh|bash|zsh|dash)\s+-\w*c\w*\s+)(?:\w+=\S*\s+)*(?:(?:env|exec|nohup|time|command|sudo)\s+)*git\b[^|;&]*?\s(add|commit|merge|push|pull|reset|checkout|restore|rm|mv|stash(?!\s+(?:list|show))|rebase|cherry-pick|revert|apply|am|clean"
                          r"|switch|tag|branch\s+-[dDfmM]|worktree\s+(add|remove|move|prune)|config|init|update-ref|commit-tree|read-tree|update-index|gc|filter-branch)\b")
GIT_QUE_MOSTRA_HISTORIA = re.compile(r"\bgit\b[^|;&]*?\s(log|show|diff|blame|grep|cat-file|archive|reflog|clone|bundle|fast-export)\b")
LE_O_QUE_NAO_E_DELE = re.compile(r"(?<![\w-])\.del(?:t|\*|\?|\[)|(?:^|(?<=[\s/=]))\.[\w-]{0,8}[*?\[]|(?<![\w-])\.git(?![\w-])", re.IGNORECASE)
ARGUMENTO = r"(?:'[^']*'|\"[^\"$`]*\"|[^\s;&|<>`$()'\"]+)"
ESTEIRA_SOZINHA = re.compile(r"sh esteira" + r"(?: " + ARGUMENTO + r")+")  # caminho com ( ou $ vai entre aspas
# Rodar um programa: no começo de um comando da linha (depois de variáveis e de env, exec, nohup...). Ler, mudar a
# permissão ou procurar o arquivo (cat esteira, chmod +x esteira, git diff esteira) não é rodar.
COMECO_DE_COMANDO = r"(?:^|[;&|(\n]\s*|(?:sh|bash|zsh|dash)\s+-\w*c\w*\s+)(?:\w+=\S*\s+)*(?:(?:env|exec|nohup|time|command|builtin|nice|sudo)\s+(?:-\w+\s+)*)*"
CHAMA_A_ESTEIRA = re.compile(COMECO_DE_COMANDO + r"(?:(?:sh|bash|zsh|dash)\s+(?:-\w+\s+)*)?(?:\S*/)?esteira(?=\s|$)")
CHAMA_A_CAIXA = re.compile(COMECO_DE_COMANDO + r"(?:python3?(?:\.\d+)?\s+(?:-\w+\s+)*)?\S*caixa-do-produto\.py(?=\s|$)")
CHAMA_A_TELA = re.compile(COMECO_DE_COMANDO + r"(?:python3?(?:\.\d+)?\s+(?:-\w+\s+)*)?\S*tela-do-app\.py(?=\s|$)")
BUSCA = re.compile(r"\b(grep|egrep|rg|ag|ack|find|ls)\b([^|;&]*)")
CAMINHO_AMPLO = {".", "./", "/", "~", "~/", "..", "../", "*", "./*", "**"}


def busca_ampla(comando: str, raiz: Path | None = None) -> bool:
    """Busca recursiva sem apontar uma pasta do código (na raiz, em ".", ou sem pasta nenhuma)."""
    for m in BUSCA.finditer(comando):
        programa, resto = m.group(1), m.group(2).split()
        opcoes = [x for x in resto if x.startswith("-")]
        recursiva = programa in ("rg", "ag", "ack", "find") or any(("r" in o.lower() and not o.startswith("--")) or o in ("--recursive",) for o in opcoes) \
            or (programa == "ls" and any("R" in o for o in opcoes))
        if not recursiva:
            continue
        soltos = [x for x in resto if not x.startswith("-")]
        if programa in ("grep", "egrep", "rg", "ag", "ack") and soltos:
            soltos = soltos[1:]  # o primeiro é o que se procura
        if programa == "find":
            soltos = soltos[:1]
        if not soltos or any(x in CAMINHO_AMPLO or x.rstrip("/") in {".", "..", "~", ""} or raiz_inteira(x, raiz) for x in soltos):
            return True
    return False


def raiz_inteira(caminho: str, raiz: Path | None) -> bool:
    """O caminho é a raiz do produto (escrita por inteiro, ou com $PWD) ou a raiz de uma cópia de candidata."""
    limpo = caminho.rstrip("/").replace("$PWD", str(raiz or "")).replace("${PWD}", str(raiz or ""))
    if raiz is not None and limpo and minusculo(Path(limpo)) in (minusculo(raiz), minusculo(raiz.resolve())):
        return True
    return bool(re.fullmatch(r"(?:\./)?\.claude(?:/worktrees(?:/[^/]+)?)?|.*/\.claude(?:/worktrees(?:/[^/]+)?)?", limpo))


PROGRAMA_EM_LINHA = re.compile(r"\b(sh|bash|zsh|dash|eval|python3?|node|perl|ruby)\b\s+(-\w*[ce]\w*\b|[\"'])")


def sem_marcas_de_aspas(comando: str) -> str:
    """Tira só as marcas de aspas e as barras de escape, deixando o que estava dentro (git "commit" vira git commit)."""
    return re.sub(r"[\"'\\]", "", comando)


def sem_aspas(comando: str) -> str:
    """Tira o texto entre aspas (o que o comando manda), mas mantém um caminho temporário entre aspas ("$TMPDIR/x")."""
    def trocar(m: re.Match) -> str:
        dentro_das_aspas = m.group(0)[1:-1]
        return dentro_das_aspas if re.match(r"(\$\{?TMPDIR|/tmp/|/dev/null)", dentro_das_aspas) else " "
    return re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", trocar, comando)


def barrar(motivo: str) -> None:
    motor.barrar(f"TRAVA DO DELTA-11: {motivo} Não tente outro caminho (terminal, outro arquivo): se o trabalho precisa disso, é aviso para quem decide.")


def minusculo(p: Path) -> str:
    return p.as_posix().lower().rstrip("/")


def dentro(caminho: Path, pasta: Path) -> bool:
    c, d = minusculo(caminho), minusculo(pasta)
    return c == d or c.startswith(d + "/")


def relativo(caminho: Path, pasta: Path) -> str:
    return caminho.as_posix()[len(pasta.as_posix()):].lstrip("/") if dentro(caminho, pasta) else ""


def enderecos(base: Path, raiz: Path | None = None) -> dict[str, list[str]]:
    arquivo = base / ".delta-11" / "regras" / "enderecos.txt"
    if not arquivo.is_file() and raiz is not None:
        arquivo = raiz / ".delta-11" / "regras" / "enderecos.txt"  # a cópia de uma candidata lê os da pasta principal
    if not arquivo.is_file():
        return {}
    pastas: dict[str, list[str]] = {}
    for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
        partes = linha.split()
        if not partes or linha.lstrip().startswith("#"):
            continue
        if not re.fullmatch(r"[a-z]+", partes[0].lower()) or len(partes) < 2 or any(not re.fullmatch(r"[\w.@()$\[\]-]+(?:/[\w.@()$\[\]-]+)*/?", x) for x in partes[1:]):
            barrar(f".delta-11/regras/enderecos.txt fora do formato na linha {n} ('{linha.strip()}'): uma linha por território, `<nome> <pasta>/ [<outra pasta>/]` (o ARQUITETO a corrige).")
        for pasta in partes[1:]:  # mais de uma pasta na mesma linha; sem barra no fim e com extensão, um arquivo (o index.html da raiz)
            arquivo = not pasta.endswith("/") and "." in pasta.rsplit("/", 1)[-1]
            pastas.setdefault(partes[0].lower(), []).append(pasta.lower() if arquivo else pasta.strip("/").lower() + "/")
    return pastas


def lugar_de(mapa: dict, rel: str) -> dict:
    for lugar in mapa["lugares"]:
        if lugar["regex"] and re.match(lugar["regex"], rel, re.IGNORECASE):
            return lugar
    return next(l for l in mapa["lugares"] if not l["regex"])  # o código do produto


def pode_ler(papel: str, lugar: dict) -> bool:
    le = lugar["le"]
    return (papel not in le["menos"]) if le["todos"] else (papel in le["so"])


def raiz_da_regra(raiz: Path, alvo: Path) -> tuple[Path, str] | None:
    """Onde as regras de lugar valem para este arquivo: a cópia de uma candidata, se ele está numa; senão a pasta do produto."""
    copias = raiz / ".claude" / "worktrees"
    if dentro(alvo, copias) and not dentro(copias, alvo):
        copia = copias / relativo(alvo, copias).split("/")[0]
        return copia, relativo(alvo, copia)
    if dentro(alvo, raiz):
        return raiz, relativo(alvo, raiz)
    return None


def conferir_escrita(mapa: dict, papel: str, base: Path, alvo: Path, raiz: Path) -> None:
    if alvo.exists() and alvo.is_file() and os.stat(alvo).st_nlink > 1:
        barrar(f"o arquivo {alvo} tem mais de um nome (link): escrita barrada.")
    if not dentro(alvo, base):
        barrar(f"o papel {papel} não escreve fora da pasta em que trabalha ({alvo}).")
    rel = relativo(alvo, base)
    lugar = lugar_de(mapa, rel)
    quem = lugar["escreve"]
    if "todos" in quem or papel in quem:
        return
    if "todos_novo" in quem:
        if alvo.exists():
            barrar(f"em {lugar['lugar']} só se cria arquivo novo; {rel} já existe.")
        return
    if "o dono da linha" in quem:
        m = re.match(lugar["regex"], rel, re.IGNORECASE)
        if m and m.group("nome").lower() == papel:
            return
        barrar(f"o papel {papel} só escreve na própria linha ({rel} é de outro).")
    if "construtores_sem_territorios" in quem and papel in mapa["construtores"] and not enderecos(base, raiz):
        return  # o caminho pequeno: um Construtor só, com todo o código
    if "construtores" in quem and papel in mapa["construtores"]:
        pastas = enderecos(base, raiz)
        rel_min = rel.lower()
        if not pastas:
            return
        # Território dentro de território (front src/, pixel src/estilos/): vale a pasta mais específica.
        donos = sorted(((len(p), dono) for dono, ps in pastas.items() for p in ps if (rel_min == p if not p.endswith("/") else rel_min.startswith(p))), reverse=True)
        if donos and donos[0][1] == papel:
            return
        if not donos and (papel == "back" or base != raiz):
            return  # arquivo fora de todo território é do BACK; na cópia da candidata, dela (as dependências do coração)
        barrar(f"{rel} não fica nas pastas do território de {papel} (.delta-11/regras/enderecos.txt).")
    barrar(f"o papel {papel} não escreve em {lugar['lugar']} ({rel}).")


def conferir_leitura(mapa: dict, papel: str, raiz: Path, alvo: Path, pasta: bool, glob: bool = False) -> None:
    so_le_em = mapa["agentes"][papel]["so_le_em"]
    if so_le_em:
        atual = raiz / so_le_em / "atual.txt"
        nome = atual.read_text(encoding="utf-8").strip() if atual.is_file() else ""
        if not nome or "/" in nome or nome.startswith("."):
            barrar(f"o {papel} só lê a pasta do teste em curso, e {so_le_em}atual.txt não diz qual é.")
        if not dentro(alvo, raiz / so_le_em / nome):
            barrar(f"o {papel} só lê dentro de {so_le_em}{nome}/.")
        return
    if any(dentro(alvo, privada) for privada in motor.pastas_privadas()):
        barrar("as conversas gravadas do Claude Code guardam o que cada agente viu (inclusive segredos e testes): ninguém as lê.")
    for pessoal in (Path(l).expanduser() for l in mapa["lugares_que_o_terminal_nao_le"] if l.startswith("~")):
        if dentro(alvo, pessoal) or (pasta and dentro(pessoal, alvo) and alvo != raiz and not dentro(raiz, alvo)):
            barrar(f"{pessoal} é de quem usa o computador (chaves, configurações): nenhum agente o lê.")
    onde = raiz_da_regra(raiz, alvo)
    if onde is None:
        if not alvo.exists() and not alvo.parent.exists():
            barrar(f"{alvo} não existe: o caminho foi digitado errado. A pasta do produto é {raiz}; use o caminho a partir dela.")
        if ".delta-11" in minusculo(alvo).split("/"):
            barrar(f"{alvo} não fica nesta pasta (outro produto, a cópia temporária da esteira, ou o caminho digitado errado: confira): ninguém daqui lê o .delta-11 de fora.")
        return
    base, rel = onde
    if pasta:
        # Busca numa pasta que contém um lugar vedado a este papel ("todos menos ele") é barrada. Os lugares secretos de
        # "só ..." (teste guardado, cofre) ficam fora do git, e a busca do Claude Code não entra no que o git ignora: a trava
        # confere o .gitignore. O registro não é segredo (só não se lê para trabalhar): a leitura direta é que é barrada.
        sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        linhas_do_ignorar = (base / ".gitignore").read_text(encoding="utf-8").splitlines() if (base / ".gitignore").is_file() else []

        def ignora(fixo: str) -> bool:  # o que o git ignora de fato; sem git que responda, pelo texto do .gitignore
            feito = subprocess.run(["git", "-C", str(base), "check-ignore", "-q", "--no-index", fixo.rstrip("/") + "/x"], capture_output=True, env=sem_git)
            return feito.returncode == 0 if feito.returncode in (0, 1) else fixo in linhas_do_ignorar
        for lugar in mapa["lugares"]:
            if not lugar["regex"] or pode_ler(papel, lugar) or not dentro(base / lugar["fixo"].rstrip("/"), alvo):
                continue
            if lugar["le"]["todos"] or (lugar["fixo"].rstrip("/") in mapa["lugares_que_o_terminal_nao_le"] and (glob or not ignora(lugar["fixo"]))):
                barrar(f"o papel {papel} não busca em {rel or 'na raiz'}: ali dentro há {lugar['lugar']}, que não é dele. Busque numa pasta mais funda (do código, ou `.delta-11/quadro/`, por exemplo).")
        rel = rel + "/" if rel else rel
    lugar = lugar_de(mapa, rel)
    if re.fullmatch(r"\.delta-11/quadro/[a-z0-9-]+/linhas/" + re.escape(papel) + r"-\d+\.md", rel.lower()):
        return  # a própria linha, cada um lê
    if not pode_ler(papel, lugar):
        barrar(f"o papel {papel} não lê {lugar['lugar']}.")


def conferir_esteira(mapa: dict, papel: str, comando: str, cwd: Path, raiz: Path) -> None:
    """A esteira roda fora da caixa de areia: só a de verdade (na raiz), só por quem constrói, só com o próprio nome."""
    if not ESTEIRA_SOZINHA.fullmatch(comando):
        barrar("rode a esteira sozinha na linha, exatamente `sh esteira <nome> <arquivos>` (sem `&&`, `;`, `cd`, redirecionamento nem `$(...)`; caminho com parênteses ou $ vai entre aspas simples): só assim ela roda fora da caixa de areia e consegue juntar.")
    if mapa["agentes"][papel]["terminal"] != "livre":
        barrar(f"o {papel} não entrega à esteira: quem entrega é quem constrói.")
    if minusculo(cwd) != minusculo(raiz):
        barrar("a esteira só roda na raiz da pasta do produto (numa cópia de candidata, a escolhida entra por um agente novo da pasta principal).")
    nome = comando.split()[2].strip("'\"").lower()
    nomes = nome.split(",")
    if papel not in nomes or not set(nomes) <= set(mapa["construtores"]) | {"scout"} or (len(nomes) > 1 and "scout" in nomes):
        barrar(f"o {papel} entrega com o próprio nome: `sh esteira {papel} <arquivos>` (numa entrega conjunta, o nome dele está entre os da entrega).")
    for outro in (n for n in nomes if n != papel):  # o colega aceitou: escreveu na linha dele, numa camada aberta, os arquivos que entrega junto
        linhas = [l for l in (raiz / ".delta-11" / "quadro").glob(f"*/linhas/{outro}-*.md") if camada_aberta(raiz, l.parent.parent.name)]
        if not any(re.search(r"^\W*entrego junto\s*:[^\n<]*?[\w-]+(?:/[\w.-]*|\.\w+)", l.read_text(encoding="utf-8"), re.IGNORECASE | re.MULTILINE) for l in linhas):
            barrar(f"o {outro} não escreveu `Entrego junto: <arquivos>` na linha dele: a entrega conjunta precisa do aceite de cada um.")
    partes = comando.split()
    for opcao in ("--copia", "--descartar"):
        for i, parte in enumerate(partes):
            if parte == opcao:
                for alvo in partes[i + 1:]:
                    if alvo.startswith("--"):
                        break
                    if not re.fullmatch(r"\.claude/worktrees/[^/\s]+/?", alvo.strip("'\"")):
                        barrar(f"{opcao} só aceita a cópia de uma candidata, `.claude/worktrees/<cópia>` ({alvo} não é).")


def conferir_caixa(mapa: dict, comando: str, cwd: Path, base: Path) -> None:
    """A caixa do produto roda fora da caixa de areia do Claude Code: só sozinha na linha, e só a do motor (a da pasta
    principal; numa cópia de candidata, igual a ela)."""
    if not re.fullmatch(re.escape(mapa["caixa_do_produto"]) + r"(?: " + ARGUMENTO + r")+", comando):
        barrar(f"rode a caixa do produto sozinha na linha, exatamente `{mapa['caixa_do_produto']} <comando>` (sem `&&`, `;`, `|`, `cd`, "
               "redirecionamento nem `$(...)`; para encadear, o comando é `sh -c '<comandos>'`; caminho com parênteses ou $ vai entre aspas simples): "
               "só assim ela roda fora da caixa de areia, onde o navegador e o banco funcionam.")
    if "$(" in comando or "`" in comando:
        barrar("com `$(...)` ou crase, mesmo entre aspas, o Claude Code deixa a caixa do produto dentro da caixa de areia, onde ela não abre: "
               "ponha os comandos num roteiro (quem confere, em `.rascunho/`; quem constrói, no seu território) e rode o roteiro pela caixa.")
    try:  # as opções da caixa, lidas como o terminal as lê (sem as aspas), antes do comando
        palavras = shlex.split(comando)[len(shlex.split(mapa["caixa_do_produto"])):]
    except ValueError:
        barrar("o comando da caixa do produto não fecha as aspas.")
    while palavras:
        if palavras[0] == "--com-ambiente":
            barrar("só o publicar da esteira grava no ambiente do dono (o app instalado e os dados reais dele): rode o produto pela caixa "
                   "sem --com-ambiente, com os dados numa cópia de teste.")
        if palavras[0] == "olhar":
            palavras = palavras[1:]
        elif palavras[0] == "--raiz":
            palavras = palavras[2:]
        else:
            break
    if minusculo(cwd) != minusculo(base):
        barrar("a caixa do produto roda na raiz da pasta do produto (ou na raiz da cópia da candidata).")
    chamada = cwd / ".claude" / "hooks" / "delta-11" / "caixa-do-produto.py"
    if not chamada.is_file() or chamada.resolve() != chamada.absolute() or chamada.read_bytes() != (AQUI / "caixa-do-produto.py").read_bytes():
        barrar("esta cópia da caixa do produto não é a do motor (foi mudada): use a da pasta principal, que ninguém altera.")


def conferir_tela(mapa: dict, papel: str, comando: str, cwd: Path, base: Path) -> None:
    """A tela do app roda fora da caixa de areia do Claude Code: só por quem está em `usam_a_tela` no mapa (hoje, o Revisor),
    só sozinha na linha e só a do motor (a da pasta principal; numa cópia de candidata, igual a ela)."""
    if papel not in mapa["usam_a_tela"]:
        barrar(f"o {papel} não usa a tela do app: a tela do Mac é do dono, e só o Revisor a usa, na hora que ele libera; quem constrói prova pelo código, pela caixa.")
    if not re.fullmatch(re.escape(mapa["tela_do_app"]) + r"(?: " + ARGUMENTO + r")+", comando) or "$(" in comando or "`" in comando:
        barrar(f"rode a tela do app sozinha na linha, exatamente `{mapa['tela_do_app']} <ação> [\"<texto>\"]` (sem `&&`, `;`, `|`, `cd`, "
               "redirecionamento, `$(...)` nem a caixa do produto; texto com $ ou crase, entre aspas simples): só assim ela roda fora da caixa "
               "de areia, onde o macOS deixa ver e usar a janela do app.")
    if minusculo(cwd) != minusculo(base):
        barrar("a tela do app roda na raiz da pasta do produto (ou na raiz da cópia da candidata).")
    chamada = cwd / ".claude" / "hooks" / "delta-11" / "tela-do-app.py"
    if not chamada.is_file() or chamada.resolve() != chamada.absolute() or chamada.read_bytes() != (AQUI / "tela-do-app.py").read_bytes():
        barrar("esta cópia da tela do app não é a do motor (foi mudada): use a da pasta principal, que ninguém altera.")


def textos_de(dados) -> list[str]:
    """Todo texto que um pedido traz, em qualquer campo (nome de programa, lista de programas...)."""
    if isinstance(dados, str):
        return [dados]
    if isinstance(dados, dict):
        return [t for v in dados.values() for t in textos_de(v)]
    if isinstance(dados, list):
        return [t for v in dados for t in textos_de(v)]
    return []


def conferir_ferramenta_de_fora(mapa: dict, papel: str, ferramenta: str, dados: dict, raiz: Path) -> None:
    """O navegador do dono (Claude in Chrome) e os programas do computador (computer use): só quem tem o servidor na lista
    de ferramentas (agentes.md); ver vale sempre, mexer só no Dia 1 ou na hora que o dono liberou; terminal e editor de
    código, nunca. Qualquer outra ferramenta de fora é barrada."""
    de_fora = mapa["ferramentas_de_fora"]
    partes = ferramenta.split("__", 2)
    servidor, nome = (partes[1], partes[2]) if len(partes) == 3 else ("", ferramenta)
    if servidor not in de_fora["servidores"]:
        barrar(f"{ferramenta} é uma ferramenta de fora que o Delta-11 não conhece: nesta pasta só valem o navegador do dono (Claude in Chrome) "
               "e os programas do computador (computer use), e só para quem os tem.")
    if papel not in de_fora["servidores"][servidor]:
        barrar(f"o {papel} não usa {ferramenta}: a tela, o navegador e os programas são do dono, e só quem conversa com ele os usa.")
    if nome in ("request_access", "open_application"):
        proibido = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(n.lower()) for n in de_fora["programas_proibidos"]) + r")(?![a-z0-9])")
        for texto in textos_de(dados):
            achado = proibido.search(texto.lower())
            if achado:
                barrar(f"terminal e editor de código ({texto}) ficam de fora, mesmo com o dono pedindo: por eles se passaria por cima da trava. "
                       "Se o dono precisa de algo lá, ele mesmo faz, ou vira pedido para o time.")
    acao = str(dados.get("action") or "") if isinstance(dados, dict) else ""
    ver = nome in de_fora["ver"] or (nome == "computer" and acao in de_fora["ver_pelo_computer_do_navegador"])
    if not ver and not reg.pode_mexer(raiz):
        barrar("a Camada 1 já selou: daqui em diante, mexer no navegador e nos programas do dono só na hora que ele libera. Pergunte até que "
               "horas ele libera e escreva `.delta-11/tela-liberada.md` com `até: <AAAA-MM-DD HH:MM>` (no máximo `tela_liberada_max` adiante). "
               "Ver (a foto da tela, ler a página) continua liberado.")


def conferir_terminal(mapa: dict, papel: str, comando: str, cwd: Path, raiz: Path, base: Path) -> None:
    """Aviso cedo. A parede de verdade é a caixa de areia: o terminal de ninguém grava em .git/, .delta-11/ nem na esteira."""
    terminal = mapa["agentes"][papel]["terminal"]
    cru = sem_marcas_de_aspas(comando)
    # Um programa em linha (sh -c "...", python -c "...") é conferido inteiro; o resto, sem o texto que o comando manda.
    conferido = cru if PROGRAMA_EM_LINHA.search(comando) else sem_aspas(comando)
    mudanca = GIT_QUE_MUDA.search(cru)
    # Sem as marcas de aspas: sh "esteira" roda a esteira do mesmo jeito.
    if CHAMA_A_ESTEIRA.search(cru) and comando.strip() != "sh -n esteira":
        conferir_esteira(mapa, papel, comando.strip(), cwd, raiz)
    pela_caixa = bool(CHAMA_A_CAIXA.search(cru))
    if pela_caixa:
        conferir_caixa(mapa, comando.strip(), cwd, base)
        olhando = comando.strip().startswith(mapa["caixa_do_produto"] + " olhar ")
        if terminal == "vigiado" and not olhando:
            barrar(f"o terminal do {papel} é vigiado: rode o produto com `{mapa['caixa_do_produto']} olhar <comando>` (nada do que já existe na pasta muda).")
    pela_tela = bool(CHAMA_A_TELA.search(cru))
    if pela_caixa and "tela-do-app.py" in cru:
        barrar(f"rode a tela do app sozinha na linha, exatamente `{mapa['tela_do_app']} <ação>`, nunca pela caixa do produto (lá dentro o macOS não deixa ver a janela).")
    if pela_tela:
        conferir_tela(mapa, papel, comando.strip(), cwd, base)
    no_temporario = re.search(r"\bgit\b\s+(?:-C\s+|init\s+(?:-\w+\s+)*)[\"']?(?:/tmp/|/private/tmp/|/private/var/folders/|\$\{?TMPDIR)", cru) \
        or re.match(r"\s*cd\s+[\"']?(?:/tmp/|/private/tmp/|/private/var/folders/|\$\{?TMPDIR)[^;&|]*&&\s*git\b", cru)  # repositório de ensaio no temporário
    if terminal == "livre":
        if mudanca and not no_temporario:  # um repositório de ensaio no temporário é do agente
            if mudanca.group(1) in ("restore", "checkout"):
                barrar(f"o terminal não grava em .git/, e o git {mudanca.group(1)} precisa: para desfazer a sua mudança num arquivo, `git show HEAD:<arquivo> > <arquivo>`.")
            barrar(f"o {papel} não mexe na história do git (git {mudanca.group(1)}): a mudança entra pela esteira (sh esteira <nome> <arquivos>); numa cópia de candidata, deixe sem commit.")
        return
    if terminal != "vigiado":
        return
    em_linha = bool(PROGRAMA_EM_LINHA.search(comando))
    conferido = SAIDA_DE_CURL_NO_TEMPORARIO.sub(" ", conferido)
    gravaria = REDIRECIONA.search(conferido) or GRAVA_PELO_TERMINAL.search(conferido) or (em_linha and PROGRAMA_QUE_GRAVA.search(comando))
    if mudanca or (gravaria and not pela_caixa and not pela_tela):  # pela caixa com olhar, a caixa do Mac não deixa mudar o que existe
        barrar(f"o terminal do {papel} é vigiado: não grava arquivo, não copia, não apaga e não mexe no git.")
    if papel in ("revisor", "destruidor"):
        aspas_neutras = re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", " TEXTO ", comando)  # o que se procura não esconde a pasta
        sem_o_que_e_dele = re.sub(r"\b[a-z][a-z0-9+.-]*://\S+", " ", cru, flags=re.IGNORECASE)  # endereço na rede: o site publicado, não a pasta
        if papel == "destruidor":
            # As regras do produto são dele (o caminho sem `..`); o relato da cópia de ataque, só pela caixa (`relato-da-copia`).
            sem_o_que_e_dele = re.sub(r"\.delta-11/regras(?:/[\w./-]*)?", lambda m: m.group(0) if ".." in m.group(0) else " ", sem_o_que_e_dele)
        if LE_O_QUE_NAO_E_DELE.search(sem_o_que_e_dele) or busca_ampla(aspas_neutras, raiz):
            barrar(f"o {papel} não lê pelo terminal o que conta como foi feito (.delta-11/, a história do git, busca em tudo): busque com o caminho de uma pasta do código (ex.: grep -rn texto src/).")
        if GIT_QUE_MOSTRA_HISTORIA.search(cru):
            barrar(f"o {papel} não lê a história do git (ela conta como foi feito).")


def rotas_de(mapa: dict, papel: str, chamado: str) -> list[str]:
    return [r["jeito"] for r in mapa["rotas"] if r["quem"] == papel and chamado in r["chama"]]


def conferir_chamada(mapa: dict, papel: str, dados: dict, pedido: dict, raiz: Path) -> None:
    chamado = dados.get("subagent_type") or ""
    if not chamado:
        barrar("toda chamada de agente diz qual papel chama (subagent_type).")
    jeitos = [j for j in rotas_de(mapa, papel, chamado) if j != "mensagem"]
    if not jeitos:
        barrar(f"o {papel} não chama o {chamado} (rotas do motor).")
    isolamento = dados.get("isolation")
    if isolamento and (isolamento != "worktree" or "cópia isolada" not in jeitos):
        barrar(f"o {papel} não chama o {chamado} com isolamento '{isolamento}'.")
    quadros = raiz / ".delta-11" / "quadro"
    terceira = [p.name for p in quadros.iterdir() if p.is_dir() and re.fullmatch(r"camada-3(-r\d+)?", p.name)] if quadros.is_dir() else []
    if isolamento and not any(camada_aberta(raiz, q) for q in terceira):
        barrar("cópia isolada só para as candidatas do coração, com a Camada 3 aberta.")
    if "segundo plano" in jeitos and dados.get("run_in_background") is not True:
        barrar(f"o {chamado} é ligado em segundo plano (run_in_background), para a conversa do dono seguir livre.")
    if "segundo plano" not in jeitos and dados.get("run_in_background") is not False:
        barrar(f"o {chamado} é chamado em primeiro plano: diga run_in_background: false (sem isso o Claude Code o põe em segundo plano).")
    if chamado == "cronos":
        conferir_um_cronos(dados, pedido)
    if chamado == "arquiteto":
        vivos = reg.arquitetos_trabalhando()
        if vivos:
            barrar(f"um ARQUITETO trabalha agora{' (agentId ' + vivos[0]['agente'] + ')' if vivos[0].get('agente') else ' (acabou de ser chamado)'}: "
                   "espere a resposta dele e chame depois, um por vez. Dois ARQUITETOS escrevendo as regras e a abertura ao mesmo tempo apagam a "
                   "decisão um do outro.")
        reg.anotar_pedido_de_arquiteto(pedido["sessao"])


def camada_aberta(raiz: Path, quadro: str) -> bool:
    return reg.quadro_aberto(raiz, quadro)


def medindo(raiz: Path, quadro: str) -> str:
    """A Camada 7 esperando o tempo do teste supremo, com a hora ainda por vir: devolve até quando (vazio, se não)."""
    if not quadro.startswith("camada-7") or not camada_aberta(raiz, quadro):
        return ""
    arquivo = raiz / ".delta-11" / "quadro" / quadro / "quadro.md"
    m = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", arquivo.read_text(encoding="utf-8", errors="replace") if arquivo.is_file() else "", re.IGNORECASE)
    valor = m.group(1).strip().strip("*_ ").lower() if m else ""
    data = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ t]+(\d{1,2}:\d{2}))?", valor) if valor.startswith("esperando o tempo") else None
    if not data:
        return ""  # sem a data no formato do quadro, a trava não sabe a hora: o vigia decide
    try:
        fim = datetime.strptime(data.group(1) + " " + (data.group(2) or "00:00"), "%Y-%m-%d %H:%M")
    except ValueError:
        return ""
    return data.group(0) if datetime.now() < fim else ""


def barrar_na_medicao(raiz: Path, quadro: str, texto: str) -> None:
    ate = medindo(raiz, quadro)
    if ate and "O ARQUITETO reabriu" not in texto:
        barrar(f"a Camada 7 mede o produto sozinho até {ate} ({quadro}): até lá nenhum CRONOS dela trabalha; o pedido do dono espera o fim da medição (diga a ele quando ela acaba; o produto fora do ar é do SCOUT). Passada a hora, o vigia chama o CRONOS.")


def conferir_um_cronos(dados: dict, pedido: dict) -> None:
    """Um CRONOS por camada: com um trabalhando agora, o recado vai por mensagem (nesta conversa) ou espera (noutra)."""
    achado = reg.QUADRO_NA_MENSAGEM.search(dados.get("prompt") or "")
    if not achado:
        barrar("a mensagem que liga o CRONOS diz a pasta do quadro: 'Conduza .delta-11/quadro/<X>/'.")
    quadro, sessao = achado.group(1).lower(), pedido["sessao"] or "sem-sessao"
    for vivo in reg.trabalhando_em(quadro):
        if vivo.get("sessao") == sessao:
            barrar(f"o CRONOS de {quadro} está trabalhando nesta conversa: mande o recado por mensagem (SendMessage para {vivo.get('agente')}).")
        barrar(f"o CRONOS de {quadro} trabalha em outra conversa aberta nesta pasta; espere ela terminar.")
    raiz = motor.raiz().resolve()
    barrar_na_medicao(raiz, quadro, dados.get("prompt") or "")
    if quadro.startswith("pedido"):
        abertas = [p.name for p in (raiz / ".delta-11" / "quadro").glob("camada-*") if p.is_dir() and camada_aberta(raiz, p.name)]
        for aberta in abertas:
            barrar_na_medicao(raiz, aberta, "")
        if abertas:
            barrar(f"há uma camada aberta ({', '.join(sorted(abertas))}): o pedido vai ao CRONOS dela, como brief (mensagem); sem CRONOS vivo, ligue um CRONOS novo dela com o pedido.")
    if reg.pedidos_recentes(sessao):
        barrar("um CRONOS acabou de ser ligado nesta conversa e ainda não começou: ligue um por vez.")
    reg.anotar_pedido(quadro, sessao)


def conferir_mensagem(mapa: dict, papel: str, dados: dict, pedido: dict) -> None:
    para = (dados.get("to") or "").lower()
    sessao = pedido["sessao"] or "sem-sessao"
    if papel == "atlas" and "mensagem" in rotas_de(mapa, "atlas", "cronos"):
        alvo = next((r for r in reg.registros() if r.get("agente", "").lower() == para and r.get("sessao") == sessao), None)
        if alvo:
            quadro = alvo.get("quadro", "")
            if any(v.get("sessao") != sessao for v in reg.trabalhando_em(quadro)):
                barrar(f"um CRONOS de {quadro} trabalha em outra conversa aberta: não acorde o desta; espere a outra terminar.")
            if reg.velho(alvo):
                barrar(f"{quadro} foi conduzido depois por um CRONOS de outra conversa: o desta tem o quadro velho na memória. Ligue um CRONOS novo, que segue pelo quadro.")
            barrar_na_medicao(motor.raiz().resolve(), quadro, str(dados.get("message") or ""))
            return
        barrar(f"o ATLAS só manda mensagem a um CRONOS desta conversa, pelo agentId que a chamada devolveu ('{para}' não é um).")
    if papel == "cronos" and para == "main" and "mensagem" in rotas_de(mapa, "cronos", "atlas"):
        return
    barrar(f"o {papel} não manda mensagem para '{para}' (rotas do motor).")


def conferir_pausa(raiz: Path, papel: str, ferramenta: str, arquivos: list[str], cwd: Path) -> None:
    """Pausar do dono: com .delta-11/pausa.md dizendo "pausado", nada roda; só o ATLAS, e o CRONOS marcando o quadro."""
    pausa = raiz / ".delta-11" / "pausa.md"
    texto = pausa.read_text(encoding="utf-8") if pausa.is_file() else ""
    todas = re.findall(r"situa[cç][aã]o\W*:([^\n]*)", texto, re.IGNORECASE)
    valor = todas[-1].strip().strip("*_ ").lower() if todas else ""  # vale a última linha Situação
    pausado = bool(re.search(r"(?<!n[ãa]o )\bpausad", valor)) and not valor.startswith(("retomad", "despausad"))
    if not pausado or papel in ("atlas", "scout") or ferramenta in ("Read", "Grep", "Glob"):  # o SCOUT mantém de pé o que já está no ar
        return

    def no_dia(caminho: str) -> bool:  # a própria linha (e, do CRONOS, o quadro)
        alvo = (Path(caminho).expanduser() if Path(caminho).expanduser().is_absolute() else cwd / caminho).resolve()
        copias = raiz / ".claude" / "worktrees"
        casa = copias / relativo(alvo, copias).split("/")[0] if dentro(alvo, copias) and alvo != copias else raiz
        rel = relativo(alvo, casa) if dentro(alvo, casa) else ""
        return bool(re.fullmatch(r"\.delta-11/quadro/[a-z0-9-]+/linhas/" + re.escape(papel) + r"-\d+\.md", rel.lower())
                    or (papel == "cronos" and re.fullmatch(r"\.delta-11/quadro/[a-z0-9-]+/quadro\.md", rel.lower())))
    em_dia = ferramenta in ("Write", "Edit") and bool(arquivos) and all(no_dia(a) for a in arquivos)  # todos os arquivos da ação
    if (papel == "cronos" and ferramenta == "SendMessage") or em_dia:
        return  # deixar a própria linha (e, o CRONOS, o quadro) em dia; o resto dos lugares a trava confere em seguida
    barrar("o dono pausou o projeto (.delta-11/pausa.md): nada roda até ele voltar; encerre deixando a sua linha em dia.")


def main() -> None:
    try:
        pedido = motor.ler()  # pelo tradutor do programa dito no comando; sem programa dito, barra
    except motor.SemPrograma as erro:
        barrar(str(erro))
    except (ValueError, OSError):
        barrar("a trava não conseguiu ler o pedido.")
    try:
        raiz = motor.raiz().resolve()
    except motor.SemRaiz as erro:
        barrar(str(erro))
    try:
        reg.anotar_sono()  # antes da ferramenta: o primeiro gancho depois de o Mac acordar guarda o sono
    except OSError:
        pass
    mapa = json.loads((AQUI / "lugares.json").read_text(encoding="utf-8"))
    papel = pedido["papel"]
    if papel not in mapa["agentes"]:
        barrar(f"papel desconhecido ('{papel or 'conversa sem papel'}'): nesta pasta só trabalham os agentes do Delta-11.")
    cwd = Path(pedido["pasta"] or raiz).resolve()
    copias = raiz / ".claude" / "worktrees"
    base = raiz
    if dentro(cwd, copias) and not dentro(copias, cwd):
        base = copias / relativo(cwd, copias).split("/")[0]  # candidata do coração: a cópia dela é a pasta dela
    ferramenta, dados, arquivos = pedido["ferramenta"], pedido["dados"], pedido["arquivos"]
    conferir_pausa(raiz, papel, ferramenta, arquivos, cwd)

    def resolver(caminho: str) -> Path:
        p = Path(caminho).expanduser()
        return (p if p.is_absolute() else cwd / p).resolve()

    if ferramenta in ("Write", "Edit", "NotebookEdit"):
        if not arquivos:
            barrar("pedido de escrita sem arquivo.")
        for caminho in arquivos:  # todo arquivo que a ação escreve (no Claude Code, um só): um proibido barra a ação inteira
            conferir_escrita(mapa, papel, base, resolver(caminho), raiz)
        for caminho in arquivos:
            quadro_escrito = re.match(r"\.delta-11/quadro/([A-Za-z0-9-]+)/", relativo(resolver(caminho), raiz))
            if papel == "cronos" and quadro_escrito and pedido["agente_id"]:
                reg.anotar_quadro(pedido["agente_id"], quadro_escrito.group(1).lower())
    elif ferramenta == "Read":
        conferir_leitura(mapa, papel, raiz, resolver(dados.get("file_path") or ""), pasta=False)
    elif ferramenta in ("Grep", "Glob"):
        pasta = resolver(dados.get("path") or str(cwd))
        padrao = dados.get("pattern", "") if ferramenta == "Glob" else ""
        if padrao and not re.search(r"[*?\[{]", padrao):
            conferir_leitura(mapa, papel, raiz, resolver(str(pasta / padrao)), pasta=False)  # caminho exato: é um arquivo
            sys.exit(0)
        fixo = re.split(r"[*?\[{]", padrao)[0]
        if fixo and "/" in fixo:
            pasta = resolver(str(pasta / fixo.rsplit("/", 1)[0]))
        resto = padrao[len(fixo.rsplit("/", 1)[0]) + 1:] if "/" in fixo else padrao
        funda = ferramenta == "Grep" or "**" in padrao or "/" in resto  # `.delta-11/*` só lista o que está direto ali
        conferir_leitura(mapa, papel, raiz, pasta, pasta=(pasta.is_dir() or not pasta.exists()) and funda, glob=ferramenta == "Glob")  # a listagem não respeita o .gitignore
    elif ferramenta == "Bash":
        conferir_terminal(mapa, papel, dados.get("command", ""), cwd, raiz, base)
    elif ferramenta == "Agent":
        conferir_chamada(mapa, papel, dados, pedido, raiz)
    elif ferramenta == "SendMessage":
        conferir_mensagem(mapa, papel, dados, pedido)
    elif ferramenta.startswith("mcp__"):
        conferir_ferramenta_de_fora(mapa, papel, ferramenta, dados if isinstance(dados, dict) else {}, raiz)
    elif ferramenta == "TaskStop" and papel == "atlas":
        alvo = next((r for r in reg.registros() if r.get("agente") and r.get("agente") == str(dados.get("task_id") or "")), None)
        if alvo and alvo.get("trabalhando") and reg.roda(alvo.get("pid", 0)) and reg.quadro_se_mexe(alvo, raiz):
            barrar("este CRONOS tem agentes trabalhando (o quadro dele se mexe): pará-lo para todos eles. Mande-lhe mensagem para trocar só o "
                   "agente parado; se tudo parar, o próximo vigia o dá como caído.")
        reg.parado(str(dados.get("task_id") or ""))  # o CRONOS parado deixa de contar: o substituto pode nascer
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as erro:  # qualquer defeito barra: a trava nunca falha aberta
        barrar(f"defeito na trava ({type(erro).__name__}: {erro}).")
