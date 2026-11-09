#!/usr/bin/env python3
"""Vigia das regras do Delta-11 v7: um fato, um lugar.

O que ele trava, e o que não pega, está em fontes/principios.md ("O vigia das regras").
Os nomes de projeto vêm de fora do Delta-11: o registro de projetos da máquina e ~/.delta-11-nomes-de-projeto.txt.
Uso: python3 conferir-regras.py      (o pulso deste vigia é testar-vigia.py)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
import unicodedata
from itertools import combinations
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "fontes"
PAGINAS = RAIZ / "paginas"
MODELOS = RAIZ / "modelos"
V7 = RAIZ.parent
MOTOR = V7 / "03-motor"
# O que os agentes leem além das páginas: o motor acrescenta estes textos a cada agente e os leva à pasta do produto.
TEXTOS_DO_MOTOR = ["lugares.md", "rotas.md", "agentes.md", "corpo-do-leitor-do-teste.md", "porta-de-entrada/CLAUDE.md"]
# Tabelas que repetem de propósito dentro de si (uma linha por território, por lugar, por rota): só a repetição com outro arquivo conta.
SEM_CONFERIR_REPETICAO = {"agentes.md", "lugares.md", "rotas.md"}
FONTES_PARA_QUEM_MANTEM = {"principios.md", "leis-do-processo.md"}
# O descuido honesto de adiar com outras palavras (a lista oficial de palavras proibidas está no núcleo).
MARCAS_DE_ADIAR = re.compile(r"\badi(?!ant)[aoe]\w*|\bprovisori\w*|\btemporariamente\b|\ba definir\b|\bficam? para a proxima\b"
                             r"|\bposteriormente\b|\boportunamente\b|\b(?:em|n)outro momento\b|\boutra hora\b|\bquando der\b|\bmais pra frente\b"
                             r"|\betapa seguinte\b|\bversao futura\b|\bitem a fazer\b|\bpr[ao] uma proxima\b|\bposterg\w*"
                             r"|\bassim que possivel\b|\bficou faltando\b|\bnum segundo momento\b|\bfica\w* de lado\b|\bvira tarefa d[ao] proxim\w*"
                             r"|\bdeix\w* para (?:a|o) (?:proxim\w*|(?:camada|rodada|fase|etapa|ciclo) seguinte)\b")
# Quantidade por extenso conta como número, com ou sem unidade depois ("uma dezena de telas").
QUANTIDADE_SOLTA = re.compile(r"\b(dezenas?|centenas?|duzias?|quinzenas?|decadas?|um par de|um quarto de hora|e poucos|e poucas)\b"
                              # ordinal ou fração que é um limite: "na quarta tentativa", "depois da segunda recusa", "metade das vezes"
                              r"|\b(segund|terceir|quart|quint|sext|setim|oitav|non|decim)[ao]s? (vez|vezes|tentativas?|recusas?|rodadas?|tentativa)\b"
                              r"|\bmetade d[aeo]s? (vezes|tentativas|recusas|rodadas)\b")
FORMATO_VALOR = re.compile(r"^- `([a-z_]+)`: (\d+) (\S+) — .+$")
NUMEROS_POR_EXTENSO = (
    "um uma dois duas três tres quatro cinco seis sete oito nove dez onze doze treze catorze quatorze quinze "
    "dezesseis dezessete dezoito dezenove vinte trinta quarenta cinquenta sessenta setenta oitenta noventa "
    "cem cento duzentos duzentas trezentos trezentas quatrocentos quinhentos quinhentas seiscentos mil meia meio"
).split()
UNIDADES_EXTRAS = (
    "token tokens tok página páginas pagina paginas pág pag pg pgs linha linhas vez vezes hora horas h hr min minuto "
    "minutos seg segundo segundos dia dias semana semanas quinzena quinzenas mês mes meses situação situações palavra palavras "
    "caractere caracteres tentativa tentativas"
).split()
# Unidades que só contam depois de um número escrito com algarismos ("uma pessoa" é texto comum, "100 pessoas" é número).
UNIDADES_SO_COM_ALGARISMO = "ano anos real reais dolar dolares euro euros usuario usuarios usuaria usuarias pessoa pessoas item itens tela telas mb gb kb".split()
QUANTIDADES_POR_EXTENSO = "dezena dezenas centena centenas duzia duzias".split()
INCLUI = re.compile(r"^<!-- inclui: .*? -->\s*$", re.MULTILINE)
CARACTERES_PERMITIDOS = set("—–“”‘’·→÷×…≠≤≥")
PARA_QUEM_MANTEM = "(para quem mantém o Delta-11"
LUGARES = {"00-plano-camada-2.md", "fontes", "paginas", "ferramentas", "registro", "modelos"}
FERRAMENTAS = {"conferir-regras.py", "gerar-paginas.py", "testar-vigia.py", "ganchos/pre-commit", "ganchos/pre-merge-commit", "ganchos/pre-push"}
MARCA_DO_REGISTRO = "> REGISTRO: versão antiga"
NAO_VALE = "Não vale"


def conferir_lugares(falhas: list[str]) -> None:
    """Regra fora do lugar: uma cópia solta de página ou fonte seria a mesma regra em dois lugares."""
    solto = lambda p: p.name == ".DS_Store" and p.is_file()
    for item in sorted(RAIZ.parent.iterdir()):
        if not (re.match(r"^\d\d-", item.name) or solto(item)):
            falhas.append(f"fora do lugar: {item.name} ao lado da pasta das regras (só arquivos e pastas numerados das camadas)")
    for item in sorted(RAIZ.iterdir()):
        if item.name not in LUGARES and not solto(item):
            falhas.append(f"fora do lugar: {item.relative_to(RAIZ)} (só valem {', '.join(sorted(LUGARES))})")
    papeis = {p.name for p in (FONTES / "papeis").glob("*.md")}
    for p in sorted((RAIZ / "paginas").iterdir()):
        if not (solto(p) or (p.is_file() and p.name in papeis)):
            falhas.append(f"fora do lugar: {p.relative_to(RAIZ)} em paginas/ (só a página de cada papel)")
    for p in sorted((RAIZ / "ferramentas").rglob("*")):
        rel = p.relative_to(RAIZ / "ferramentas").as_posix()
        if p.is_file() and "__pycache__" not in p.parts and not solto(p) and rel not in FERRAMENTAS:
            falhas.append(f"fora do lugar: ferramentas/{rel} (ferramenta desconhecida)")
    for p in sorted((RAIZ / "registro").rglob("*")):
        if p.is_file() and not solto(p):
            primeira = p.read_text(encoding="utf-8", errors="ignore").split("\n", 1)[0]
            if not (primeira.startswith(MARCA_DO_REGISTRO) and NAO_VALE in primeira):
                falhas.append(f"{p.relative_to(RAIZ)}: registro tem de dizer que não vale na primeira linha")
FRASES_PERMITIDAS = ["uma vez por camada"]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def ler_valores(falhas: list[str]) -> dict[str, tuple[int, str]]:
    valores = {}
    for n, linha in enumerate((FONTES / "valores.md").read_text(encoding="utf-8").splitlines(), 1):
        if not linha.startswith("- "):
            continue
        m = FORMATO_VALOR.match(linha)
        if not m:
            falhas.append(f"valores.md:{n} fora do formato \"- `chave`: N unidade — o que mede\": {linha.strip()}")
            continue
        if m.group(1) in valores:
            falhas.append(f"valores.md:{n} repete o valor `{m.group(1)}` (um valor, um lugar)")
        valores[m.group(1)] = (int(m.group(2)), m.group(3))
    return valores


def conferir_numeros(textos: dict[Path, str], valores: dict[str, tuple[int, str]], falhas: list[str]) -> None:
    unidades = {sem_acento(u) for u in UNIDADES_EXTRAS} | {sem_acento(u) for _, u in valores.values()}
    numero = r"\d+(?:[.,]\d+)?|" + "|".join(sorted(map(sem_acento, NUMEROS_POR_EXTENSO + QUANTIDADES_POR_EXTENSO), key=len, reverse=True))
    lista = "|".join(sorted(map(re.escape, unidades), key=len, reverse=True))
    so_algarismo = "|".join(sorted(map(re.escape, UNIDADES_SO_COM_ALGARISMO), key=len, reverse=True))
    # Papéis e telas: "um agente", "uma tela" e "dois agentes no mesmo papel" são palavras, não limites; algarismo ou três para cima, sim.
    de_papel = r"(?<![\w])(\d+|tres|quatro|cinco|seis|sete|oito|nove|dez)\s+(agentes|construtores|telas|candidatas)\b"
    padrao = re.compile(de_papel + "|" + 
        rf"(?<![\w])({numero})[\s-]*(?:de\s+)?({lista})(?![a-z])"           # 6 páginas, uma dezena de tentativas
        rf"|(?<![\w])\d+(?:[.,]\d+)?[\s-]*({so_algarismo})(?![a-z])"        # 100 usuários, 50 reais, 2 anos
        rf"|(?<![\w])({numero})\s+por\s*cento\b|(?<![\w])\d+\s*%"          # cinquenta por cento, 30%
        rf"|(?<![\w])(?!dia\s+7\b)({lista})(?:\s*[:=]\s*|\s)\d+(?![\w./-])|(?<![\w])\d+x(?![a-z])")  # páginas: 6, minutos 30, 3x
    for p, t in textos.items():
        if p.name == "valores.md":
            continue
        for n, linha in enumerate(t.splitlines(), 1):
            limpa = sem_acento(linha).replace("|", " ")  # número e unidade em colunas vizinhas de uma tabela
            for frase in FRASES_PERMITIDAS:
                limpa = limpa.replace(frase, "")
            m = padrao.search(limpa) or QUANTIDADE_SOLTA.search(limpa)
            if m:
                falhas.append(f"número com unidade fora de valores.md em {nome_de(p)}:{n}: \"{m.group(0)}\" (use o nome do valor)")


def palavras_de(texto: str) -> list[str]:
    # Um endereço ou um comando entre crases (`.delta-11/licoes.md`, `sh esteira ... --copia ...`) é referência, não
    # conteúdo de regra: não conta como repetição.
    sem_enderecos = re.sub(r"`[^`\n]*(?:/|\s--)[^`\n]*`", " ", INCLUI.sub(" ", texto))
    return re.findall(r"[a-z0-9]+", sem_acento(sem_enderecos))


def conferir_repeticoes(textos: dict[Path, str], tamanho: int, falhas: list[str]) -> None:
    sequencias = {}
    for p, t in textos.items():
        ps = palavras_de(t)
        vistas: set[str] = set()
        for i in range(len(ps) - tamanho + 1):
            trecho = " ".join(ps[i:i + tamanho])
            if trecho in vistas and p.name not in SEM_CONFERIR_REPETICAO:
                falhas.append(f"mesmo texto duas vezes em {nome_de(p)}: \"{trecho}…\"")
                break
            vistas.add(trecho)
        sequencias[p] = vistas
    for a, b in combinations(sorted(sequencias), 2):
        if "montar-agentes.py" in {a.name, b.name} and {a.name, b.name} & {"lugares.md", "rotas.md", "agentes.md"}:
            continue  # o montador resume de propósito, para cada agente, as tabelas dos lugares, das rotas e dos agentes
        comuns = sorted(sequencias[a] & sequencias[b])
        if comuns:
            falhas.append(f"mesmo texto em {nome_de(a)} e {nome_de(b)} ({len(comuns)} trecho(s)): \"{comuns[0]}…\"")


def nomes_de_projeto() -> list[str]:
    nomes: set[str] = set()
    registro = Path(os.environ.get("DELTA11_REGISTRY", Path.home() / ".delta-11-registry.json"))
    try:
        for caminho in json.loads(registro.read_text(encoding="utf-8")).get("projects", []):
            pasta = Path(str(caminho))
            nome = pasta.parent.name if normalizar(pasta.name).startswith("formacaodelta") else pasta.name
            nomes.add(nome)
    except (OSError, ValueError):
        pass
    for arquivo in [Path.home() / ".delta-11-nomes-de-projeto.txt", os.environ.get("DELTA11_NOMES_ARQUIVO")]:
        if arquivo and Path(arquivo).is_file():
            nomes |= {l.strip() for l in Path(arquivo).read_text(encoding="utf-8").splitlines() if l.strip()}
    formas: set[str] = set()
    for nome in nomes:
        inteiro = normalizar(nome)
        if len(inteiro) >= 4:
            formas.add(inteiro)
            if inteiro.endswith("s") and len(inteiro) >= 7:
                formas.add(inteiro[:-1])
        partes = [normalizar(x) for x in re.split(r"[^\w]+", nome) if normalizar(x)]
        for i in range(len(partes)):
            for j in range(i + 2, len(partes) + 1):
                trecho = "".join(partes[i:j])
                if len(trecho) >= 8:
                    formas.add(trecho)
    return sorted(formas)


NUMERO_POR_LETRA = str.maketrans("4310572@6$", "aeiostzags")


def sem_dobra(texto: str) -> str:
    return re.sub(r"(.)\1+", r"\1", texto)


def conferir_nomes(falhas: list[str]) -> bool:
    """Em todo o v7 (regras, Luz, estados e motor): o nome inteiro, com número ou símbolo no lugar de letra, com letra dobrada."""
    formas = nomes_de_projeto()
    arquivos = [p for p in sorted(V7.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    for p in arquivos:
        bruto = p.read_bytes()
        if b"\0" in bruto:
            continue
        cru = bruto.decode("utf-8", errors="ignore")
        texto = normalizar(cru)
        trocado = sem_dobra(normalizar(sem_acento(cru).translate(NUMERO_POR_LETRA)))
        palavras = {sem_dobra(normalizar(w)) for w in re.findall(r"[\w@$]+", sem_acento(cru).translate(NUMERO_POR_LETRA))}
        for forma in formas:
            limpa = sem_dobra(forma.translate(NUMERO_POR_LETRA))
            achou = (forma in palavras or limpa in palavras) if len(forma) <= 5 else (forma in texto or limpa in trocado)
            if achou:
                falhas.append(f"nome de projeto ('{forma}') em {p.relative_to(V7)}")
    return bool(formas)


def conferir_caracteres(textos: dict[Path, str], falhas: list[str]) -> None:
    for p, t in textos.items():
        for n, linha in enumerate(t.splitlines(), 1):
            for c in linha:
                if ord(c) < 128 or ("À" <= c <= "ÿ" and c not in "×÷") or c in CARACTERES_PERMITIDOS:
                    continue
                falhas.append(f"caractere estranho (U+{ord(c):04X}) em {nome_de(p)}:{n}")
                break


def conferir_proibidas(textos: dict[Path, str], falhas: list[str]) -> None:
    linha_lista = next((l for l in (FONTES / "nucleo.md").read_text(encoding="utf-8").splitlines() if l.startswith("Palavras proibidas:")), "")
    proibidas = [sem_acento(p) for p in re.findall(r'"([^"]+)"', linha_lista)]
    if not proibidas:
        falhas.append("nucleo.md sem a linha 'Palavras proibidas:'")
        return
    for p, t in textos.items():
        for n, linha in enumerate(t.splitlines(), 1):
            if linha == linha_lista:
                continue
            limpa = sem_acento(linha)
            for palavra in proibidas:
                if re.search(rf"\b{re.escape(palavra)}s?\b", limpa):
                    falhas.append(f"palavra proibida '{palavra}' em {nome_de(p)}:{n}")
            if re.search(r"\b(TODO|FIXME|TBD|A FAZER)\b", linha):
                falhas.append(f"marca de adiar (TODO/FIXME/TBD/A FAZER) em {nome_de(p)}:{n}")
            m = MARCAS_DE_ADIAR.search(limpa)
            if m and p.name.startswith("01-luz") and m.group(0) == "num segundo momento":
                m = None  # na Luz, o texto do dono, é o público de depois (os alunos), não trabalho empurrado
            if m:
                falhas.append(f"palavra proibida (jeito de adiar: '{m.group(0)}') em {nome_de(p)}:{n}")


def conferir_paginas(valores: dict[str, tuple[int, str]], falhas: list[str]) -> None:
    spec = importlib.util.spec_from_file_location("gerar", Path(__file__).with_name("gerar-paginas.py"))
    gerar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gerar)
    incluidas_por_alguem = {"nucleo.md", "valores.md"}
    for papel in sorted((FONTES / "papeis").glob("*.md")):
        lista = gerar.inclusoes(papel.read_text(encoding="utf-8"))
        if len(lista) != len(set(lista)):
            falhas.append(f"{papel.relative_to(RAIZ)} inclui a mesma fonte duas vezes")
        for extra in lista:
            incluidas_por_alguem.add(extra)
            if not (FONTES / extra).is_file():
                falhas.append(f"{papel.relative_to(RAIZ)} inclui '{extra}', que não existe em fontes/")
    for fonte in sorted(FONTES.glob("*")):
        if fonte.is_file() and fonte.name not in incluidas_por_alguem:
            primeira = fonte.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
            if not (fonte.suffix == ".md" and primeira and PARA_QUEM_MANTEM in primeira[0]):
                falhas.append(f"fonte {fonte.name} não entra em página nenhuma e não diz '{PARA_QUEM_MANTEM}…' na primeira linha")
            elif fonte.name not in FONTES_PARA_QUEM_MANTEM:
                falhas.append(f"fonte {fonte.name} diz ser para quem mantém, mas não está na lista combinada ({', '.join(sorted(FONTES_PARA_QUEM_MANTEM))}): uma regra de papel escondida")
    nucleo = gerar.com_valores((FONTES / "nucleo.md").read_text(encoding="utf-8").strip())
    try:
        with tempfile.TemporaryDirectory() as tmp:
            esperadas = gerar.gerar(Path(tmp))
    except OSError as erro:
        falhas.append(f"o gerador não conseguiu montar as páginas: {erro}")
        return
    atuais = {p.name: p.read_text(encoding="utf-8") for p in PAGINAS.glob("*.md")}
    for nome, texto in esperadas.items():
        if atuais.get(nome) != texto:
            falhas.append(f"página desatualizada ou ausente: paginas/{nome} (rode gerar-paginas.py)")
    for nome in sorted(set(atuais) - set(esperadas)):
        falhas.append(f"página sem fonte: paginas/{nome}")

    por_pagina = valores.get("palavras_por_pagina", (500, ""))[0]
    limite = valores.get("pagina_papel_max", (4, ""))[0] * por_pagina
    brief, leitura = valores.get("brief_max", (0, ""))[0], valores.get("leitura_max", (0, ""))[0]
    for nome, texto in esperadas.items():
        palavras = len(texto.split())
        if palavras > limite:
            falhas.append(f"página {nome} com {palavras} palavras (limite {limite})")
        papel = (FONTES / "papeis" / nome).read_text(encoding="utf-8")
        incluidas = {"nucleo.md", "valores.md", *gerar.inclusoes(papel)}
        if "construtor.md" in incluidas and palavras / por_pagina + brief > leitura:
            falhas.append(f"página {nome} ({palavras / por_pagina:.1f} páginas) + brief_max ({brief}) passa de leitura_max ({leitura})")
        if nucleo not in texto:
            falhas.append(f"página {nome} sem o núcleo inteiro")
        corpo = texto.replace(gerar.CABECALHO, "")
        regras = {p.name.lower() for p in FONTES.rglob("*.md")} | ({p.name.lower() for p in MODELOS.rglob("*.md")} if MODELOS.is_dir() else set())
        for caminho, citado in sorted({(c[0].lower(), c[1].lower()) for c in re.findall(r"(?<![\w.-])((?:[\w.-]+/)*)([\w-]+\.(?:md|py|json|ya?ml|sh|txt))\b", corpo, re.IGNORECASE)}):
            if caminho.startswith((".delta-11/", ".claude/")):
                continue  # endereço na pasta do produto, não regra
            if caminho and citado not in regras:
                continue  # ferramenta ou outro arquivo citado pelo caminho (ex.: ferramentas/conferir-regras.py)
            if citado not in incluidas:
                falhas.append(f"página {nome} cita '{caminho}{citado}', que não está dentro dela")


def ler_fontes(falhas: list[str]) -> dict[Path, str]:
    textos = {}
    for p in sorted(FONTES.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(FONTES)
        if p.suffix != ".md" or (len(rel.parts) > 1 and rel.parts[0] != "papeis") or len(rel.parts) > 2:
            falhas.append(f"arquivo fora do formato das fontes: fontes/{rel} (só .md, em fontes/ ou fontes/papeis/)")
            continue
        try:
            textos[p] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            falhas.append(f"fontes/{rel} não está em UTF-8")
    # Os modelos (entregues no brief, não nas páginas) passam pelas mesmas conferências de texto.
    for p in sorted(MODELOS.rglob("*")) if MODELOS.is_dir() else []:
        if not p.is_file() or p.name == ".DS_Store":
            continue
        if p.suffix != ".md" or p.parent != MODELOS:
            falhas.append(f"arquivo fora do formato dos modelos: {p.relative_to(RAIZ)} (só .md, direto em modelos/)")
            continue
        try:
            textos[p] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            falhas.append(f"{p.relative_to(RAIZ)} não está em UTF-8")
    # O que o motor acrescenta aos agentes e leva ao produto passa pelas mesmas conferências de texto.
    if MOTOR.is_dir():
        for nome in TEXTOS_DO_MOTOR + sorted(f"modelos/{m.name}" for m in (MOTOR / "modelos").glob("*.md")):
            alvo = MOTOR / nome
            if alvo.is_file():
                textos[alvo] = alvo.read_text(encoding="utf-8")
            else:
                falhas.append(f"texto do motor ausente: 03-motor/{nome}")
        montador = MOTOR / "ferramentas" / "montar-agentes.py"
        if montador.is_file():
            textos[montador] = textos_do_montador(montador)
        else:
            falhas.append("texto do motor ausente: 03-motor/ferramentas/montar-agentes.py")
    return textos


def textos_do_montador(arquivo: Path) -> str:
    """As frases que o montador escreve nos agentes (o cabeçalho e o trecho do motor): são regra como as fontes."""
    import ast
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nos = [n for n in arvore.body if isinstance(n, ast.FunctionDef) and n.name in ("trecho_do_motor", "montar")]
    nos += [n for n in arvore.body if isinstance(n, ast.Assign) and any(getattr(a, "id", "") == "CABECALHO_CORPO" for a in n.targets)]
    frases = [c.value for n in nos for c in ast.walk(n) if isinstance(c, ast.Constant) and isinstance(c.value, str) and " " in c.value.strip()]
    return "\n".join(f.replace("\n", " ") for f in frases)


def nome_de(p: Path) -> str:
    return str(p.relative_to(V7)) if V7 in p.parents else str(p)


def ler_historia() -> dict[Path, str]:
    """A Luz, os arquivos de estado e o plano: não entram nas conferências de número nem de repetição, mas também não
    podem adiar nada nem citar projeto."""
    textos = {p: p.read_text(encoding="utf-8") for p in sorted(V7.glob("0*.md"))}
    plano = RAIZ / "00-plano-camada-2.md"
    if plano.is_file():
        textos[plano] = plano.read_text(encoding="utf-8")
    return textos


def conferir_valores_sem_crase(textos: dict[Path, str], valores: dict[str, tuple[int, str]], falhas: list[str]) -> None:
    for p, t in textos.items():
        if p.name == "valores.md":
            continue
        for nome in valores:
            if re.search(rf"(?<![`\w]){re.escape(nome)}(?![`\w])", t):
                falhas.append(f"`{nome}` citado sem crase em {nome_de(p)} (sem crase o número não aparece ao lado)")


def conferir_nomes_de_valores(textos: dict[Path, str], valores: dict[str, tuple[int, str]], falhas: list[str]) -> None:
    for p, t in textos.items():
        for nome in sorted(set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", t))):
            if nome not in valores:
                falhas.append(f"`{nome}` em {nome_de(p)} não existe em valores.md")


def main() -> int:
    falhas: list[str] = []
    conferir_lugares(falhas)
    valores = ler_valores(falhas)
    textos = ler_fontes(falhas)
    conferir_nomes_de_valores(textos, valores, falhas)
    conferir_numeros(textos, valores, falhas)
    conferir_valores_sem_crase(textos, valores, falhas)
    if "frase_repetida_palavras" in valores:
        conferir_repeticoes(textos, valores["frase_repetida_palavras"][0], falhas)
    else:
        falhas.append("valores.md sem `frase_repetida_palavras`")
    conferiu_nomes = conferir_nomes(falhas)
    conferir_caracteres(textos, falhas)
    conferir_proibidas({**textos, **ler_historia()}, falhas)
    conferir_paginas(valores, falhas)
    if falhas:
        print(f"BLOQUEADO — {len(falhas)} problema(s):")
        for f in falhas:
            print("  -", f)
        return 1
    aviso = "" if conferiu_nomes else " (sem lista de nomes de projeto nesta máquina: nomes NÃO conferidos)"
    print(f"OK — {len(textos)} fontes, {len(list(PAGINAS.glob('*.md')))} páginas, nenhum problema.{aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
