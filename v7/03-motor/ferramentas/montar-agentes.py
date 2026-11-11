#!/usr/bin/env python3
"""Monta os agentes do v7 e o mapa da trava, a partir de quatro fontes (um fato, um lugar).

- ../agentes.md: as escolhas de cada agente (ferramentas, modelo, terminal, cor).
- ../lugares.md: quem escreve e quem lê cada lugar da pasta do produto.
- ../rotas.md: quem chama quem, quando e de que jeito.
- v7/02-regras/paginas/: a página de cada papel (o corpo do agente).
Cada agente = frontmatter + página + "Onde você escreve e lê" + "Como você chama e quem te chama".
O mapa da trava e do porteiro vai para ../agentes/lugares.json. Nunca edite agentes/ à mão.
Uso: python3 montar-agentes.py            (escreve em ../agentes/)
     python3 montar-agentes.py --conferir (só confere; sai com 1 se algo estiver desatualizado ou grande demais)
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
V7 = MOTOR.parent
REGRAS = V7 / "02-regras"
PAGINAS = REGRAS / "paginas"
SAIDA = MOTOR / "agentes"
MAPA = SAIDA / "lugares.json"
CONSTRUTORES = ["vault", "engine", "front", "pixel", "form", "back", "shield"]
# Quem mexe no código lê só o brief, o código e estes lugares (a carga dele); listar o resto só gastaria leitura.
# A caixa de areia barra o terminal de todos aqui (relativo à raiz do produto); a configuração da pasta usa esta lista.
NAO_GRAVA_PELO_TERMINAL = [".delta-11", ".git", "esteira", "CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".mcp.json", ".gitignore", ".worktreeinclude", ".claude/rules", ".claude/CLAUDE.md",
                           ".claude/worktrees/*/.claude", ".claude/worktrees/*/.delta-11"]  # nas cópias das candidatas, a trava e as linhas delas
# Segredos e o teste guardado: o terminal de ninguém os lê (a ferramenta de ler, a trava confere quem pode).
# O jeito de rodar o produto: o único comando, além da esteira, que roda fora da caixa de areia do Claude Code.
CAIXA_DO_PRODUTO = "python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py"
# Ver e usar a janela de um app de Mac: também fora da caixa de areia, só para quem constrói e quem confere o app.
TELA_DO_APP = "python3 -I -B .claude/hooks/delta-11/tela-do-app.py"
USAM_A_TELA = ["revisor"]  # a tela do Mac do dono: só quem confere usando, na hora que ele libera; quem constrói prova pelo código
# Também as chaves pessoais de quem usa o computador: a rede da caixa do produto é livre.
NAO_LE_PELO_TERMINAL = [".delta-11/teste-guardado", ".delta-11/cofre", ".delta-11/leitor", "~/.claude", "~/.ssh", "~/.aws", "~/.gnupg", "~/.netrc", "~/.docker/config.json", "~/.secretctl"]
LE_QUEM_MEXE_NO_CODIGO = {"`.delta-11/esteira/`", "`.delta-11/regras/enderecos.txt`", "`.delta-11/regras/`", "`.delta-11/estado/`", "`.delta-11/motor/`", "`.delta-11/cofre/`", "`.delta-11/quadro/<X>/`"}
CABECALHO_CORPO = "Você é o {papel} do Delta-11 v7. A sua página está abaixo: siga só ela. Os números estão ao lado de cada nome, entre parênteses; cada página tem {palavras} palavras (conte as do que você escreve).\n\n"

_spec = importlib.util.spec_from_file_location("gerar", REGRAS / "ferramentas" / "gerar-paginas.py")
gerar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar)


def tabela(arquivo: Path) -> list[dict[str, str]]:
    linhas = [l for l in arquivo.read_text(encoding="utf-8").splitlines()
              if l.startswith("|") and not set(l) <= set("|-: ")]
    cabeca = [c.strip() for c in linhas[0].strip("|").split("|")]
    return [dict(zip(cabeca, [c.strip() for c in l.strip("|").split("|")])) for l in linhas[1:]]


def valores() -> dict[str, tuple[int, str]]:
    achados = {}
    for linha in (REGRAS / "fontes" / "valores.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- `([a-z_]+)`: (\d+) (\S+) — ", linha)
        if m:
            achados[m.group(1)] = (int(m.group(2)), m.group(3))
    return achados


def nomes(celula: str) -> list[str]:
    return [n.strip() for n in celula.split(",") if n.strip()]


def regra_de_leitura(celula: str) -> dict:
    if celula == "todos":
        return {"todos": True, "menos": []}
    if celula.startswith("todos menos "):
        return {"todos": True, "menos": nomes(celula[len("todos menos "):])}
    if celula.startswith("só "):
        return {"todos": False, "so": nomes(celula[len("só "):])}
    raise SystemExit(f"lugares.md: coluna 'lê' fora do formato: {celula!r}")


def padrao(lugar: str) -> tuple[str, str]:
    """Devolve (regex, prefixo fixo) para um lugar de lugares.md."""
    if lugar == "o código do produto":
        return "", ""
    caminho = lugar.strip("`")
    regex = ""
    for parte in re.split(r"(<[a-zX]+>)", caminho):
        regex += {"<X>": "[^/]+", "<N>": "[0-9]+", "<nome>": "(?P<nome>[a-z-]+?)", "<n>": "[0-9]+"}.get(parte, re.escape(parte))
    regex = "^" + regex + (".*$" if caminho.endswith("/") else "$")
    fixo = caminho.split("<")[0]
    return regex, fixo


def ler_lugares(agentes: list[dict]) -> list[dict]:
    conhecidos = {a["nome"] for a in agentes}
    lugares = []
    for l in tabela(MOTOR / "lugares.md"):
        regex, fixo = padrao(l["lugar"])
        escreve = l["escreve"]
        if escreve in ("todos", "ninguém", "o dono da linha"):
            quem = [escreve]
        elif escreve == "todos, só arquivo novo":
            quem = ["todos_novo"]
        else:
            quem = []
            for n in nomes(escreve):
                quem.append({"os Construtores do território": "construtores", "os Construtores sem territórios": "construtores_sem_territorios"}.get(n, n))
        for n in quem + regra_de_leitura(l["lê"]).get("menos", []) + regra_de_leitura(l["lê"]).get("so", []):
            if n not in conhecidos | {"todos", "todos_novo", "ninguém", "o dono da linha", "construtores", "construtores_sem_territorios"}:
                raise SystemExit(f"lugares.md: '{n}' não é um agente de agentes.md")
        lugares.append({"lugar": l["lugar"], "o_que_e": l["o que é"], "regex": regex, "fixo": fixo,
                        "escreve": quem, "le": regra_de_leitura(l["lê"])})
    return lugares


def ler_rotas(agentes: list[dict]) -> list[dict]:
    conhecidos = {a["nome"] for a in agentes}
    rotas = []
    for r in tabela(MOTOR / "rotas.md"):
        chamados = [n for c in nomes(r["chama"]) for n in (CONSTRUTORES if c == "construtores" else [c])]
        for n in [r["quem"], *chamados]:
            if n not in conhecidos:
                raise SystemExit(f"rotas.md: '{n}' não é um agente de agentes.md")
        if r["jeito"] not in ("segundo plano", "primeiro plano", "pela resposta", "cópia isolada", "mensagem"):
            raise SystemExit(f"rotas.md: jeito desconhecido {r['jeito']!r}")
        rotas.append({"quem": r["quem"], "chama": chamados, "quando": r["quando"], "jeito": r["jeito"], "como": r["como"]})
    return rotas


def pode_escrever(nome: str, lugar: dict) -> bool:
    q = lugar["escreve"]
    return ("todos" in q or "todos_novo" in q or "o dono da linha" in q or nome in q or ("construtores" in q and nome in CONSTRUTORES))


def pode_ler(nome: str, lugar: dict) -> bool:
    le = lugar["le"]
    return (nome not in le["menos"]) if le["todos"] else (nome in le["so"])


def trecho_do_motor(agente: dict, lugares: list[dict], rotas: list[dict]) -> str:
    nome = agente["nome"]
    linhas = ["## Onde você escreve e lê (o motor do Delta-11)"]
    marcas = re.search(r"^\*\*Marcas:\*\*.*$", (MOTOR / "rotas.md").read_text(encoding="utf-8"), re.M).group(0)
    if agente["só lê em"] != "—":
        linhas.append(f"Você só lê dentro de {agente['só lê em']} e não escreve em lugar nenhum; a trava barra o resto.")
    else:
        escreve, le = [], []
        for l in lugares:
            if l["lugar"] in ("`.delta-11/`", "`.claude/`", "`.git/`"):
                continue
            if pode_escrever(nome, l):
                if "o dono da linha" in l["escreve"]:
                    escreve.append(f"- `.delta-11/quadro/<X>/linhas/{nome}-<n>.md`: a sua linha (nunca a de outro).")
                elif "todos_novo" in l["escreve"]:
                    escreve.append(f"- {l['lugar']}: {l['o_que_e']} (só arquivo novo).")
                elif l["lugar"] == "o código do produto":
                    escreve.append("- o código do produto, " + ("em qualquer território." if nome == "scout" else
                                   "só nas pastas do seu território (`.delta-11/regras/enderecos.txt`; sem esse arquivo, todo o código, `.gitignore` inclusive)."))
                else:
                    escreve.append(f"- {l['lugar']}: {l['o_que_e']}.")
            elif pode_ler(nome, l) and l["lugar"] not in ("o código do produto", "`.delta-11/`", "`.claude/`", "`.git/`") and (
                    nome not in CONSTRUTORES + ["scout"] or l["lugar"] in LE_QUEM_MEXE_NO_CODIGO):
                le.append(l["lugar"])
        linhas += ["Você escreve só em (a trava barra o resto):", *escreve]
        if nome not in CONSTRUTORES + ["scout"]:
            le.append("o código do produto e as cópias das candidatas (`.claude/worktrees/`)")
        if le:
            linhas.append("Você lê também: " + ", ".join(le) + ".")
        if any(not pode_ler(nome, l) for l in lugares):
            linhas.append("A trava barra a leitura do que não está nestas listas" + (", fora o código." if nome in CONSTRUTORES + ["scout"] else "."))
    if agente["terminal"] in ("vigiado", "livre"):
        linhas.append("A hora da sua linha (Atualizado), tire-a do terminal (`date '+%Y-%m-%d %H:%M'`); nunca a escreva de cabeça.")
        linhas.append("No Mac, quem tem terminal não tem as ferramentas Grep e Glob: busque pelo terminal, com o caminho de uma pasta do código (`grep -rn texto src/`).")
    if agente["terminal"] == "vigiado":
        linhas.append("Pelo terminal, a trava barra gravar arquivo e mexer no git" + (" e tocar em `.delta-11/`" if nome in ("revisor", "destruidor") else "") + "; testes e o produto rodam à vontade.")
    elif agente["terminal"] == "livre":
        linhas.append("O terminal grava só no código do produto e nos caches das ferramentas (a caixa de areia barra `.delta-11/` e os arquivos de controle da raiz).")
    if agente["terminal"] in ("vigiado", "livre"):
        olhar = " olhar" if agente["terminal"] == "vigiado" else ""
        linhas.append("Rodar o produto (testes, navegador de teste, servidor, banco, as ferramentas dos serviços como `gh` e `supabase`): sozinho na linha, na pasta em que você trabalha, `" + CAIXA_DO_PRODUTO + olhar + " <comando>` (para encadear, o comando é `sh -c '<comandos>'`); a cópia de uma candidata, da raiz: `" + CAIXA_DO_PRODUTO + olhar + " --raiz .claude/worktrees/<cópia> <comando>`, que roda dentro dela. Fora dela o navegador não abre e o banco não conecta; dentro, ela lê o `.env` e nunca grava em `.git/`, `.delta-11/` nem `.claude/`. O `ps` não roda em caixa nenhuma: `pgrep -fl` e `pkill -f` pela caixa.")
        if olhar:
            linhas.append("Com `olhar`, a pasta fica só para ler: a montagem grava só no que o git ignora. Os seus roteiros de ataque ou de teste: escreva-os em `.rascunho/<seu-nome>-<n>.<extensão>` pela ferramenta de escrever e rode-os pela caixa (de lá eles acham as dependências do produto); um programa na linha, `node -e '...'`, também serve.")
    if nome in USAM_A_TELA:
        linhas.append("A janela do app de Mac (o `app:` dos comandos da esteira), sozinha na linha, na raiz: `" + TELA_DO_APP + " <ação>` (`abrir`, `ver`, `foto` em `.rascunho/`, `clicar \"<rótulo>\"`, `digitar \"<texto>\"`, `tecla`, `atalho`, `fechar`).")
    if nome in CONSTRUTORES:
        linhas.append("Entregar à esteira: na raiz do produto, exatamente `sh esteira <seu-nome> <os arquivos que você mudou>` (o nome do papel, como `front`, não o da sua linha; quando o brief manda entregar junto com outro território: `sh esteira <seu-nome>,<o-outro> <os arquivos dos dois>`) (sem `cd`, redirecionamento nem `$(...)` na mesma linha); ela responde por último ENTROU ou RECUSOU, com o motivo, e guarda o relato inteiro em `.delta-11/esteira/`. Ela pode demorar: chame-a com o maior tempo do terminal (`timeout` 600000); se ela for para segundo plano, não encerre antes da resposta (leia o relato dela até a última linha). A história do git é só da esteira: o terminal de ninguém grava em `.git/`. Numa cópia isolada, deixe o trabalho sem commit; a esteira o pega da cópia.")
    minhas = [r for r in rotas if r["quem"] == nome]
    if minhas:
        linhas.append("`<X>` é a pasta da camada ou do pedido (`camada-3`, `pedido-12`).")
        linhas.append(marcas)

    linhas += ["", "## Como você chama e quem te chama (o motor do Delta-11)"]
    for r in minhas:
        alvo = ", ".join(r["chama"]).upper()
        verbo = {"pela resposta": "Recado ao", "mensagem": "Mensagem ao"}.get(r["jeito"], "Chame o")
        linhas.append(f"- **{verbo} {alvo}** ({r['jeito']}). Quando: {r['quando']}. Como: {r['como']}.")
    chamam: dict[str, list[str]] = {}
    for r in rotas:
        if nome in r["chama"]:
            chamam.setdefault(r["quem"], []).append(r["quando"])
    if chamam:
        linhas.append("- **Quem te chama ou te manda recado:** " + "; ".join(f"{q.upper()} ({'; '.join(qs)})" for q, qs in chamam.items()) + ".")
    if not minhas:
        linhas.append("- Você não chama ninguém.")
    return gerar.com_valores("\n".join(linhas))


def montar(agente: dict, lugares: list[dict], rotas: list[dict]) -> tuple[str, int, int]:
    principal = agente["nome"] == "atlas"
    frente = ["---", f"name: {agente['nome']}", f"description: {json.dumps(agente['quando usar'], ensure_ascii=False)}",
              f"tools: {agente['ferramentas']}", f"model: {agente['modelo']}"]
    if not principal:
        frente += ["permissionMode: auto", "omitClaudeMd: true"]
    frente += [f"color: {agente['cor']}", "---"]
    papel_arquivo = PAGINAS / f"{agente['papel'].upper()}.md"
    if papel_arquivo.is_file():
        pagina = re.sub(r"^<!-- GERADO.*?-->\n\n", "", papel_arquivo.read_text(encoding="utf-8"))
        corpo = CABECALHO_CORPO.format(papel=agente["papel"], palavras=valores()["palavras_por_pagina"][0]) + pagina.rstrip()
    else:
        corpo = (MOTOR / f"corpo-do-{agente['nome']}.md").read_text(encoding="utf-8").rstrip()
    extra = trecho_do_motor(agente, lugares, rotas)
    texto = "\n".join(frente) + "\n\n" + corpo + "\n\n---\n\n" + extra + "\n"
    cabecalho = len(CABECALHO_CORPO.format(papel=agente["papel"], palavras=valores()["palavras_por_pagina"][0]).split()) if papel_arquivo.is_file() else 0
    return texto, len(corpo.split()) - cabecalho, len(extra.split()) + cabecalho  # o cabeçalho é do motor, não regra do papel


def ferramentas_de_fora(agentes: list[dict]) -> dict:
    """A seção "Ferramentas de fora" de agentes.md: quem usa cada servidor (pela coluna "ferramentas", `mcp__<servidor>__*`),
    o que é ver (vale sempre) e os programas que ninguém abre."""
    servidores: dict[str, list[str]] = {}
    for a in agentes:
        for servidor in re.findall(r"mcp__([a-z0-9-]+)__\*", a["ferramentas"]):
            servidores.setdefault(servidor, []).append(a["nome"])
    texto = (MOTOR / "agentes.md").read_text(encoding="utf-8").split("## Ferramentas de fora", 1)
    if len(texto) != 2:
        raise SystemExit("agentes.md: falta a seção \"Ferramentas de fora\"")
    listas = {m.group(1).replace(" ", "_"): nomes(m.group(2)) for m in re.finditer(r"^- \*\*([a-z ]+):\*\* (.+)$", texto[1], re.MULTILINE)}
    for chave in ("ver", "ver_pelo_computer_do_navegador", "programas_proibidos"):
        if not listas.get(chave):
            raise SystemExit(f"agentes.md: a seção \"Ferramentas de fora\" não traz a lista **{chave.replace('_', ' ')}:**")
    return {"servidores": servidores, **{k: listas[k] for k in ("ver", "ver_pelo_computer_do_navegador", "programas_proibidos")}}


def mapa(agentes: list[dict], lugares: list[dict], rotas: list[dict]) -> str:
    v = valores()
    return json.dumps({
        "aviso": "GERADO por v7/03-motor/ferramentas/montar-agentes.py a partir de lugares.md, rotas.md e agentes.md. Não edite.",
        "construtores": CONSTRUTORES,
        "agentes": {a["nome"]: {"terminal": a["terminal"], "so_le_em": a["só lê em"].strip("`") if a["só lê em"] != "—" else ""} for a in agentes},
        "lugares": [{k: l[k] for k in ("lugar", "regex", "fixo", "escreve", "le")} for l in lugares],
        "rotas": [{k: r[k] for k in ("quem", "chama", "jeito")} for r in rotas if r["jeito"] != "pela resposta"],
        "lugares_que_o_terminal_nao_grava": NAO_GRAVA_PELO_TERMINAL,
        "silencio_max_minutos": v["silencio_max"][0],
        "travado_max_minutos": v["travado_max"][0],
        "cronos_nascer_max_segundos": v["cronos_nascer_max"][0],
        "espaco_livre_min_gb": v["espaco_livre_min"][0],
        "tela_liberada_max_horas": v["tela_liberada_max"][0],
        "lugares_que_o_terminal_nao_le": NAO_LE_PELO_TERMINAL,
        "caixa_do_produto": CAIXA_DO_PRODUTO,
        "tela_do_app": TELA_DO_APP,
        "usam_a_tela": USAM_A_TELA,
        "ferramentas_de_fora": ferramentas_de_fora(agentes),
    }, ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    conferir = "--conferir" in sys.argv
    if len(sys.argv) > 1 and not conferir:
        print(__doc__)
        return 0 if sys.argv[1] in ("-h", "--help") else 2
    agentes = tabela(MOTOR / "agentes.md")
    lugares, rotas = ler_lugares(agentes), ler_rotas(agentes)
    v = valores()
    por_pagina = v["palavras_por_pagina"][0]
    limite_pagina, limite_motor = v["pagina_papel_max"][0] * por_pagina, v["motor_max"][0] * por_pagina
    leitura, brief = v["leitura_max"][0] * por_pagina, v["brief_max"][0] * por_pagina
    # perfis-de-ia.json mora nesta pasta mas é fonte escrita à mão (as IAs que um produto pode usar), não gerada: não é sobra.
    problemas, esperados = [], {"lugares.json", "perfis-de-ia.json"}
    # O brief do BACK e do SHIELD leva a Luz compacta, o contrato da esteira e as linhas das leis da camada (carga.md):
    # para o trabalho, sobra ao menos meia página na camada que tem mais linhas.
    contrato = len((MOTOR / "modelos" / "esteira.md").read_text(encoding="utf-8").split())
    por_camada: dict[str, int] = {}
    for linha in (REGRAS / "modelos" / "leis-do-produto.md").read_text(encoding="utf-8").splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) == 3 and re.search(r"\d", celulas[2]):
            for camada in re.findall(r"\d+", celulas[2]):
                por_camada[camada] = por_camada.get(camada, 0) + len(linha.split())
    leis = max(por_camada.values(), default=0)
    sobra = brief - contrato - v["luz_compacta_max"][0] * por_pagina - leis
    if sobra < por_pagina // 2:
        problemas.append(f"brief do BACK e do SHIELD: contrato ({contrato}) + Luz compacta + linhas das leis ({leis}) deixam {sobra} palavras do brief_max para o trabalho")
    for a in agentes:
        nome = f"{a['nome']}.md"
        esperados.add(nome)
        texto, palavras_pagina, palavras_motor = montar(a, lugares, rotas)
        if palavras_pagina > limite_pagina:
            problemas.append(f"{nome}: a página tem {palavras_pagina} palavras (limite {limite_pagina})")
        if palavras_motor > limite_motor:
            problemas.append(f"{nome}: o motor acrescenta {palavras_motor} palavras (limite motor_max, {limite_motor})")
        if a["nome"] in CONSTRUTORES and palavras_pagina + palavras_motor + brief > leitura:
            problemas.append(f"{nome}: página + motor + brief_max passam de leitura_max ({leitura} palavras)")
        alvo = SAIDA / nome
        if conferir:
            if not alvo.is_file() or alvo.read_text(encoding="utf-8") != texto:
                problemas.append(f"{nome} desatualizado (rode montar-agentes.py)")
        else:
            SAIDA.mkdir(exist_ok=True)
            alvo.write_text(texto, encoding="utf-8")
            print(f"{nome:22s} página {palavras_pagina:5d} + motor {palavras_motor:4d} palavras")
    texto_mapa = mapa(agentes, lugares, rotas)
    if conferir:
        if not MAPA.is_file() or MAPA.read_text(encoding="utf-8") != texto_mapa:
            problemas.append("lugares.json desatualizado (rode montar-agentes.py)")
    else:
        MAPA.write_text(texto_mapa, encoding="utf-8")
    sobra = sorted(p.name for p in SAIDA.iterdir() if p.name not in esperados) if SAIDA.is_dir() else []
    problemas += [f"{s} sem agente em agentes.md" for s in sobra]
    for modelo in (MOTOR / "modelos").glob("*.md"):
        for achado in re.findall(r"linhas/[^\s`)]+", modelo.read_text(encoding="utf-8")):
            if not re.fullmatch(r"linhas/<nome>-<n>\.md", achado):
                problemas.append(f"modelos/{modelo.name}: nome de linha fora do padrão linhas/<nome>-<n>.md ({achado})")
    if problemas:
        print("BLOQUEADO — " + "; ".join(problemas))
        return 1
    print(f"OK — {len(agentes)} agentes e o mapa da trava em dia.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
