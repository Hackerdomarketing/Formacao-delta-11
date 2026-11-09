#!/usr/bin/env python3
"""Pulso do vigia (conferir-regras.py): prova que ele trava cada tipo de quebra.

Copia as regras para uma pasta temporária, confere que a cópia limpa passa, depois planta
uma quebra de cada vez (inclusive as burlas que o Destruidor já tentou) e exige BLOQUEADO.
Os nomes de projeto do teste são inventados aqui; os reais nunca entram no Delta-11.
Uso: python3 testar-vigia.py   (sai com 1 se alguma quebra passar)
"""
from __future__ import annotations

import codecs
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# O nome falso fica cifrado (rot13): escrito às claras, o próprio vigia o acharia neste arquivo.
NOME_FALSO = codecs.decode("Cebwrgb Rkrzcyb Mrgn-Dhngeb", "rot13")


def acrescentar(arquivo: str, texto: str):
    def plantar(raiz: Path) -> None:
        alvo = raiz / arquivo
        alvo.write_text(alvo.read_text(encoding="utf-8").rstrip("\n") + "\n" + texto + "\n", encoding="utf-8")
    return plantar


def trocar(arquivo: str, antigo: str, novo: str):
    def plantar(raiz: Path) -> None:
        alvo = raiz / arquivo
        texto = alvo.read_text(encoding="utf-8")
        assert antigo in texto, f"o teste precisa de '{antigo}' em {arquivo}"
        alvo.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")
    return plantar


def criar(arquivo: str, texto: str):
    def plantar(raiz: Path) -> None:
        (raiz / arquivo).parent.mkdir(parents=True, exist_ok=True)
        (raiz / arquivo).write_text(texto, encoding="utf-8")
    return plantar


TRECHO_DO_CONSTRUTOR = "só a parte do brief que fica no seu território; entrega a mudança à esteira"
QUEBRAS_NAS_FONTES = {
    "número por extenso": acrescentar("fontes/carga.md", "O brief tem até quinhentos tokens."),
    "número com unidade abreviada": acrescentar("fontes/travas.md", "Espere 4h antes de avisar."),
    "número novo": acrescentar("fontes/carga.md", "O brief tem até 6 páginas."),
    "número que já existe em valores": acrescentar("fontes/carga.md", "O estado tem até 500 tokens."),
    "trecho copiado de outra fonte": acrescentar("fontes/papeis/FORM.md", f"Faz {TRECHO_DO_CONSTRUTOR}."),
    "nome de projeto com espaço": acrescentar("fontes/territorios.md", codecs.decode("Pbzb ab Cebwrgb Rkrzcyb Mrgn.", "rot13")),
    "nome de projeto com hífen": acrescentar("fontes/territorios.md", codecs.decode("Pbzb ab cebwrgb-rkrzcyb-mrgn.", "rot13")),
    "nome de projeto no singular": acrescentar("fontes/territorios.md", codecs.decode("Pbzb rz rkrzcybmrgn-dhnge.", "rot13")),
    "nome de projeto no fim do nome": acrescentar("fontes/territorios.md", codecs.decode("Pbzb ab Mrgn Dhngeb.", "rot13")),
    "palavra proibida no plural": acrescentar("fontes/travas.md", "Ficam algumas lacunas."),
    "palavra proibida entre aspas": acrescentar("fontes/travas.md", 'Fica como “dívida” técnica e "ressalva" aceita.'),
    "palavra proibida sem acento": acrescentar("fontes/travas.md", "Vira uma divida."),
    "expressão de adiar": acrescentar("fontes/travas.md", "Isso fica para depois."),
    "valor fora do formato": trocar("fontes/valores.md", "- `externo_espera`: 4 horas", "- `externo_espera`: 1,5 horas"),
    "inclusão de fonte que não existe": trocar("fontes/papeis/VAULT.md", "<!-- inclui: construtor.md", "<!-- inclui: nao-existe.md construtor.md"),
    "página citando arquivo de fora": acrescentar("fontes/papeis/VAULT.md", "Leia também `principios.md`."),
    "página citando arquivo de fonte pelo caminho": acrescentar("fontes/papeis/VAULT.md", "Leia também `fontes/travas.md`."),
    "página citando arquivo de modelo pelo caminho": acrescentar("fontes/papeis/VAULT.md", "Veja `../modelos/testes-do-fruto.md`."),
    "página grande demais": acrescentar("fontes/papeis/REVISOR.md", " ".join(f"palavra{i}" for i in range(1200))),
    "página que estoura a leitura": trocar("fontes/valores.md", "- `brief_max`: 3 páginas", "- `brief_max`: 7 páginas"),
    "nome no plural escrito no singular": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab mrgncevzb.", "rot13")),
    "nome vindo da lista pessoal de nomes": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Bzrtnorgn.", "rot13")),
    "nome vindo da pasta acima de FORMACAO-DELTA-11": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Xnccngrfgr.", "rot13")),
    "nome com número no lugar de letra": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab m3g4ce1zbf.", "rot13")),
    "nome num arquivo sem extensão": acrescentar("ferramentas/ganchos/pre-commit", codecs.decode("# mrgncevzbf", "rot13")),
    "nome num arquivo .json": criar("ferramentas/exemplo.json", codecs.decode('{"cebwrgb": "mrgncevzbf"}', "rot13")),
    "letra de outro alfabeto": acrescentar("fontes/travas.md", "Uma regra com a letra \u0430 russa."),
    "caractere invisível": acrescentar("fontes/travas.md", "Uma lacu\u200bna escondida."),
    "marca TODO": acrescentar("fontes/travas.md", "TODO: resolver na Camada 5."),
    "sinônimo de adiar": acrescentar("fontes/travas.md", "O item fica pendente."),
    "número entre crases": acrescentar("fontes/carga.md", "O brief tem até `6 páginas`."),
    "número com hífen": acrescentar("fontes/carga.md", "O brief tem até 6-páginas."),
    "hora composta": acrescentar("fontes/travas.md", "Espere 1h30 antes de avisar."),
    "porcentagem": acrescentar("fontes/travas.md", "Se 10% dos briefs voltarem, pare."),
    "multiplicador": acrescentar("fontes/travas.md", "Tente 3x antes de avisar."),
    "unidade caracteres": acrescentar("fontes/carga.md", "O aviso tem até 400 caracteres."),
    "trecho copiado dentro de comentário": acrescentar("fontes/papeis/ENGINE.md", "<!-- Só o ATLAS fala com o dono; pedido do dono -->"),
    "mesmo trecho duas vezes na mesma fonte": acrescentar("fontes/travas.md", "Problema achado numa camada se resolve nela, ou ela fica BLOQUEADA. Problema achado numa camada se resolve nela, ou ela fica BLOQUEADA."),
    "fonte que nenhuma página inclui": criar("fontes/regra-escondida.md", "# Regra escondida\n\nJunte você mesmo.\n"),
    "citação de arquivo em maiúsculas": acrescentar("fontes/papeis/VAULT.md", "Leia também PRINCIPIOS.MD."),
    "nome de projeto numa ferramenta": acrescentar("ferramentas/gerar-paginas.py", codecs.decode("# rkrzcyb: cebwrgb rkrzcyb mrgn", "rot13")),
}
def gerador_sem_nucleo(raiz: Path) -> None:
    trocar("ferramentas/gerar-paginas.py", 'partes = [sem_inclusoes(texto_papel), (FONTES / "nucleo.md").read_text(encoding="utf-8").strip()]',
           "partes = [sem_inclusoes(texto_papel)]")(raiz)


def criar_utf16(arquivo: str, texto: str):
    def plantar(raiz: Path) -> None:
        (raiz / arquivo).write_bytes(texto.encode("utf-16"))
    return plantar


QUEBRAS_NAS_FONTES["gerador que tira o núcleo das páginas"] = gerador_sem_nucleo
QUEBRAS_NAS_FONTES.update({
    "fonte escondida numa subpasta": criar("fontes/extras/regra.md", "# Regra escondida\n"),
    "arquivo .txt entre os papéis": criar("fontes/papeis/notas.txt", "Espere duas horas.\n"),
    "mesma fonte incluída duas vezes": trocar("fontes/papeis/VAULT.md", "<!-- inclui: construtor.md", "<!-- inclui: construtor.md construtor.md"),
    "nome de valor digitado errado": acrescentar("fontes/carga.md", "Espere `silencio_maximo`."),
    "fonte em outra codificação": criar_utf16("fontes/codificada.md", "# Regra\n"),
    "marca TBD": acrescentar("fontes/travas.md", "TBD: decidir na Camada 5."),
    "modelo fora do formato": criar("modelos/anotacoes.txt", "Espere duas horas.\n"),
    "cópia solta de páginas fora do lugar": criar("--help/CRONOS.md", "# CRONOS — cópia antiga\n"),
    "registro sem o aviso de que não vale": criar("registro/versao-9/regras.md", "# Regras antigas\n"),
    "registro com marca sem dizer que não vale": criar("registro/versao-9/regras.txt", "> REGISTRO: versão antiga, esta é a que vale\n"),
    "cópia de páginas dentro das ferramentas (fora do lugar)": criar("ferramentas/paginas/CRONOS.md", "# CRONOS\n"),
    "sobra de merge em paginas (fora do lugar)": criar("paginas/ATLAS.md.orig", "# ATLAS\n"),
    "pasta solta ao lado das regras (fora do lugar)": criar("../ajuda/CRONOS.md", "# CRONOS\n"),
    "palavra proibida no feminino": acrescentar("fontes/travas.md", "A decisão fica adiada."),
    # O que os agentes leem além das páginas (textos do motor) e a história (Luz, estados, plano).
    "nome de projeto nas rotas do motor": acrescentar("../03-motor/rotas.md", codecs.decode("Pbzb ab Mrgncevzbf.", "rot13")),
    "nome de projeto na Luz do v7": acrescentar("../01-luz-do-delta-11.md", codecs.decode("Pbzb ab Mrgncevzbf.", "rot13")),
    "nome de projeto curto": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Ehkb.", "rot13")),
    "nome de projeto com símbolo no lugar de letra": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Mrg@cevzbf.", "rot13")),
    "nome de projeto com letra dobrada": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Mrggncevzbf.", "rot13")),
    "nome de projeto com algarismo no lugar do g": acrescentar("fontes/travas.md", codecs.decode("Pbzb ab Bzr6norgn.", "rot13")),
    "palavra proibida num texto do motor": acrescentar("../03-motor/lugares.md", "Fica uma lacuna aqui."),
    "palavra proibida no plano": acrescentar("00-plano-camada-2.md", "Fica uma lacuna."),
    "palavra proibida no arquivo de estado do v7": acrescentar("../02-estado-camada-2.md", "Fica pendente."),
    "jeito de adiar: provisoriamente": acrescentar("fontes/travas.md", "Vale provisoriamente."),
    "jeito de adiar: a definir": acrescentar("fontes/travas.md", "O limite: A DEFINIR."),
    "jeito de adiar: fica para a próxima": acrescentar("fontes/travas.md", "O alarme fica para a próxima camada."),
    "jeito de adiar: conjugado": acrescentar("fontes/travas.md", "Melhor adiá-lo; adiamos o resto."),
    "número num modelo do motor": acrescentar("../03-motor/modelos/selo.md", "Espere 3 dias."),
    "número no texto que o montador escreve": trocar("../03-motor/ferramentas/montar-agentes.py", "Ela pode demorar:", "Ela fica pendente 45 minutos:"),
    "trecho copiado no texto que o montador escreve": trocar("../03-motor/ferramentas/montar-agentes.py", "Ela pode demorar:", f"Faça {TRECHO_DO_CONSTRUTOR}. Ela pode demorar:"),
    "palavra proibida no texto que o montador escreve": trocar("../03-motor/ferramentas/montar-agentes.py", "nunca a escreva de cabeça", "nunca a escreva de cabeça, salvo uma lacuna"),
    "número em anos": acrescentar("fontes/travas.md", "Guarde por 2 anos."),
    "número em reais": acrescentar("fontes/travas.md", "Custa até 50 reais."),
    "número de usuários": acrescentar("fontes/travas.md", "Até 100 usuários."),
    "quantidade por extenso": acrescentar("fontes/travas.md", "Tente uma dezena de tentativas."),
    "porcentagem por extenso": acrescentar("fontes/travas.md", "Cinquenta por cento dos casos."),
    "unidade antes do número": acrescentar("fontes/travas.md", "Tamanho em páginas: 6"),
    "número e unidade em colunas de tabela": acrescentar("fontes/travas.md", "| 6 | páginas |"),
    "trecho copiado nas rotas do motor": acrescentar("../03-motor/rotas.md", f"Faz {TRECHO_DO_CONSTRUTOR}."),
    "trecho copiado ao lado de um endereço": acrescentar("../03-motor/lugares.md", f"Veja `.delta-11/x/`: {TRECHO_DO_CONSTRUTOR}."),
    "fonte para quem mantém fora da lista": criar("fontes/escondida.md", "# Regra (para quem mantém o Delta-11)\nO CRONOS chama o SCOUT.\n"),
    "valor repetido": acrescentar("fontes/valores.md", "- `silencio_max`: 45 minutos — outra vez."),
    "valor citado sem crase": acrescentar("fontes/carga.md", "Espere silencio_max antes de avisar."),
    "jeito de adiar: posteriormente": acrescentar("fontes/papeis/FRONT.md", "Isso se ajusta posteriormente."),
    "jeito de adiar: noutro momento": acrescentar("fontes/papeis/FRONT.md", "Volte a isso noutro momento, quando der."),
    "jeito de adiar: postergar": acrescentar("fontes/papeis/FRONT.md", "Postergamos isso para uma versão futura."),
    "jeito de adiar: assim que possível": acrescentar("fontes/papeis/FRONT.md", "Ficou faltando: faça assim que possível."),
    "jeito de adiar: num segundo momento": acrescentar("fontes/papeis/FRONT.md", "O resto, num segundo momento."),
    "jeito de adiar: deixe para a camada seguinte": acrescentar("fontes/papeis/PIXEL.md", "O que não couber, deixe para a camada seguinte."),
    "jeito de adiar: vira tarefa da próxima rodada": acrescentar("fontes/papeis/FORM.md", "O resto vira tarefa da próxima rodada."),
    "jeito de adiar: fica de lado até a reabertura": acrescentar("fontes/papeis/VAULT.md", "Isso fica de lado até a reabertura."),
    "número depois da unidade: minutos 30": acrescentar("fontes/papeis/ENGINE.md", "Agende fora dos minutos 0 e 30."),
    "número com unidade: 5 agentes": acrescentar("fontes/papeis/CRONOS.md", "Chame no máximo 5 agentes juntos."),
    "número por extenso com unidade: três telas": acrescentar("fontes/papeis/FRONT.md", "O coração tem no máximo três telas."),
    "ordinal que é limite: na quarta tentativa": acrescentar("fontes/funcionamento.md", "Na quarta tentativa, pare."),
    "fração que é limite: metade das tentativas": acrescentar("fontes/funcionamento.md", "Pare na metade das tentativas."),
    "quantidade vaga: trinta e poucos minutos": acrescentar("fontes/funcionamento.md", "Espere trinta e poucos minutos."),
    "quantidade solta: um par de horas": acrescentar("fontes/papeis/ENGINE.md", "Espere um par de horas."),
    "quantidade por extenso solta": acrescentar("fontes/papeis/FRONT.md", "Faça uma dezena de telas."),
    "número em quinzenas": acrescentar("fontes/papeis/FRONT.md", "Espere uma quinzena."),
    "número em dólares": acrescentar("fontes/papeis/FRONT.md", "Nunca acima de 50 dólares."),
    "número de itens": acrescentar("fontes/papeis/FRONT.md", "Mostre 20 itens por tela."),
    "marca TODO numa página de papel": acrescentar("fontes/papeis/FRONT.md", "TODO: revisar."),
})

# O motivo que o vigia tem de dar para cada quebra (travar por outro motivo não conta).
# A primeira chave que aparece no nome da quebra decide; a ordem importa.
MOTIVOS = [
    ("para quem mantém", "regra de papel escondida"), ("valor repetido", "repete o valor"), ("sem crase", "citado sem crase"),
    ("quantidade", "número com unidade"),
    ("modelo fora do formato", "fora do formato dos modelos"), ("fora do lugar", "fora do lugar"), ("registro", "registro tem de dizer que não vale"),
    ("nome de valor", "não existe em valores.md"), ("nome", "nome de projeto"), ("valor fora", "fora do formato"),
    ("inclusão de fonte", "não existe em fontes"), ("incluída duas vezes", "a mesma fonte duas vezes"),
    ("citando arquivo", "não está dentro dela"), ("citação de arquivo", "não está dentro dela"),
    ("grande demais", "palavras (limite"), ("estoura a leitura", "passa de leitura_max"),
    ("duas vezes na mesma", "duas vezes em"), ("trecho copiado", "mesmo texto"),
    ("outro alfabeto", "caractere estranho"), ("invisível", "caractere estranho"), ("marca", "marca de adiar"),
    ("proibida", "palavra proibida"), ("adiar", "palavra proibida"), ("nenhuma página inclui", "não entra em página nenhuma"),
    ("subpasta", "fora do formato das fontes"), (".txt", "fora do formato das fontes"), ("codificação", "não está em UTF-8"),
    ("núcleo", "sem o núcleo"), ("editada à mão", "desatualizada"), ("sem fonte", "página sem fonte"),
    ("número", "número com unidade"), ("hora", "número com unidade"), ("porcentagem", "número com unidade"),
    ("multiplicador", "número com unidade"), ("unidade", "número com unidade"),
    ("ordinal", "número com unidade"), ("fração", "número com unidade"), ("quantidade vaga", "número com unidade"),
]


def motivo_esperado(nome: str) -> str:
    for chave, motivo in MOTIVOS:
        if chave in nome:
            return motivo
    raise AssertionError(f"quebra sem motivo esperado: {nome}")


QUEBRAS_NAS_PAGINAS = {
    "página editada à mão": acrescentar("paginas/VAULT.md", "Regra escrita à mão."),
    "página sem fonte": criar("paginas/FANTASMA.md", "# Página sem fonte\n"),
}


def rodar_vigia(raiz: Path, ambiente: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(raiz / "ferramentas" / "conferir-regras.py")],
                          capture_output=True, text=True, env=ambiente)


def copia_limpa(destino: Path) -> Path:
    raiz = destino / "v7" / "02-regras"
    for pasta in ("fontes", "paginas", "ferramentas", "registro", "modelos"):
        shutil.copytree(RAIZ / pasta, raiz / pasta, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(RAIZ / "00-plano-camada-2.md", raiz / "00-plano-camada-2.md")
    # A Luz, os estados e os textos do motor que os agentes leem: o vigia também os confere.
    for historia in RAIZ.parent.glob("0*.md"):
        shutil.copy2(historia, raiz.parent / historia.name)
    motor = RAIZ.parent / "03-motor"
    if motor.is_dir():
        for nome in ("lugares.md", "rotas.md", "agentes.md", "corpo-do-leitor-do-teste.md", "porta-de-entrada/CLAUDE.md"):
            (raiz.parent / "03-motor" / nome).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(motor / nome, raiz.parent / "03-motor" / nome)
        shutil.copytree(motor / "modelos", raiz.parent / "03-motor" / "modelos")
        (raiz.parent / "03-motor" / "ferramentas").mkdir(parents=True, exist_ok=True)
        shutil.copy2(motor / "ferramentas" / "montar-agentes.py", raiz.parent / "03-motor" / "ferramentas" / "montar-agentes.py")
    return raiz


def gerar_paginas(raiz: Path) -> None:
    subprocess.run([sys.executable, "-I", str(raiz / "ferramentas" / "gerar-paginas.py")], capture_output=True)  # se o gerador quebrar, o vigia ainda tem de travar


def gancho_instalado() -> bool:
    """Onde a lei importa: o repositório real tem o gancho configurado e executável? Fora de um repositório, não se aplica."""
    sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}  # dentro de um gancho, GIT_DIR apontaria outro lugar
    git = lambda *a: subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True, env=sem_git)
    topo = git("rev-parse", "--show-toplevel")
    if topo.returncode != 0:
        return True
    esperado = (RAIZ / "ferramentas" / "ganchos").resolve()
    configurado = git("config", "core.hooksPath").stdout.strip()
    return bool(configurado) and (Path(topo.stdout.strip()) / configurado).resolve() == esperado and os.access(esperado / "pre-commit", os.X_OK)


def testar_gancho(pasta: Path, ambiente: dict[str, str]) -> bool:
    """Repositório de teste: um commit limpo tem de passar; depois, com a pasta limpa e a quebra só no que vai
    para o commit, o commit tem de ser recusado."""
    regras = pasta / "v7" / "02-regras"
    regras.parent.mkdir(parents=True)
    for nome in ("fontes", "paginas", "ferramentas"):
        shutil.copytree(RAIZ / nome, regras / nome, ignore=shutil.ignore_patterns("__pycache__"))
    git = lambda *a: subprocess.run(["git", "-C", str(pasta), *a], capture_output=True, text=True, env=ambiente)
    git("init", "-q"); git("config", "user.email", "teste@exemplo"); git("config", "user.name", "teste")
    git("config", "core.hooksPath", "v7/02-regras/ferramentas/ganchos")
    git("add", "-A")
    if git("commit", "-q", "-m", "limpo").returncode != 0:
        return False  # o gancho recusou um commit limpo: travaria por outro motivo, o teste não vale
    alvo = regras / "fontes" / "travas.md"
    limpo = alvo.read_text(encoding="utf-8")
    alvo.write_text(limpo + "\nO brief tem até 6 páginas.\n", encoding="utf-8")
    git("add", "-A")
    alvo.write_text(limpo, encoding="utf-8")
    return git("commit", "-q", "-m", "teste").returncode != 0


def testar_envio(pasta: Path, ambiente: dict[str, str]) -> bool:
    """Um commit sujo feito pulando o gancho (--no-verify) tem de ser recusado no envio; um limpo tem de subir."""
    regras = pasta / "v7" / "02-regras"
    regras.parent.mkdir(parents=True)
    for nome in ("fontes", "paginas", "ferramentas"):
        shutil.copytree(RAIZ / nome, regras / nome, ignore=shutil.ignore_patterns("__pycache__"))
    remoto = pasta.parent / "envio-remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], capture_output=True, env=ambiente)
    git = lambda *a: subprocess.run(["git", "-C", str(pasta), *a], capture_output=True, text=True, env=ambiente)
    git("init", "-q"); git("config", "user.email", "teste@exemplo"); git("config", "user.name", "teste")
    git("config", "core.hooksPath", "v7/02-regras/ferramentas/ganchos")
    git("add", "-A"); git("commit", "-q", "-m", "limpo")
    if git("push", "-q", str(remoto), "HEAD:refs/heads/main").returncode != 0:
        return False  # recusou um envio limpo: travaria por outro motivo
    alvo = regras / "fontes" / "travas.md"
    alvo.write_text(alvo.read_text(encoding="utf-8") + "\nO brief tem até 6 páginas.\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-q", "--no-verify", "-m", "sujo")
    return git("push", "-q", str(remoto), "HEAD:refs/heads/main").returncode != 0


def testar_chave_sem_marca(pasta: Path, ambiente: dict[str, str]) -> bool:
    """Com DELTA11_DENTRO_DO_PULSO=1 (sem o arquivo-marca), o gancho tem de rodar o pulso: aqui, num repositório sem o
    pulso, a falta dele faz o commit ser recusado."""
    regras = pasta / "v7" / "02-regras"
    regras.parent.mkdir(parents=True)
    for nome in ("fontes", "paginas", "ferramentas"):
        shutil.copytree(RAIZ / nome, regras / nome, ignore=shutil.ignore_patterns("__pycache__"))
    (regras / "ferramentas" / "testar-vigia.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    git = lambda *a: subprocess.run(["git", "-C", str(pasta), *a], capture_output=True, text=True, env=ambiente)
    git("init", "-q"); git("config", "user.email", "teste@exemplo"); git("config", "user.name", "teste")
    git("config", "core.hooksPath", "v7/02-regras/ferramentas/ganchos")
    git("add", "-A")
    return git("commit", "-q", "-m", "teste").returncode != 0


def main() -> int:
    falhas = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        registro = tmp / "registro.json"
        registro.write_text(json.dumps({"projects": [f"/qualquer/{NOME_FALSO}", "/qualquer/" + codecs.decode("Mrgncevzbf", "rot13"),
                                                     "/qualquer/" + codecs.decode("Ehkb", "rot13"),
                                                     "/qualquer/" + codecs.decode("Xnccngrfgr", "rot13") + "/FORMACAO-DELTA-11"]}), encoding="utf-8")
        # Sem as variáveis GIT_* do commit de verdade: dentro de um gancho, elas apontariam o teste para o repositório real.
        limpo = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        marca = tmp / ".pulso-do-vigia-em-andamento"
        marca.write_text("o gancho de commit, dentro deste pulso, não roda o pulso de novo\n", encoding="utf-8")
        ambiente = {**limpo, "DELTA11_REGISTRY": str(registro), "HOME": str(tmp / "casa"), "DELTA11_DENTRO_DO_PULSO": str(marca)}
        (tmp / "casa").mkdir()
        (tmp / "casa" / ".delta-11-nomes-de-projeto.txt").write_text(codecs.decode("Bzrtnorgn", "rot13") + "\n", encoding="utf-8")

        limpa = rodar_vigia(copia_limpa(tmp / "limpa"), ambiente)
        if limpa.returncode != 0:
            print("A cópia limpa não passou no vigia; o pulso não pode ser medido:\n" + limpa.stdout)
            return 1

        todas = [(nome, plantar, True) for nome, plantar in QUEBRAS_NAS_FONTES.items()]
        todas += [(nome, plantar, False) for nome, plantar in QUEBRAS_NAS_PAGINAS.items()]
        for n, (nome, plantar, regerar) in enumerate(todas):
            raiz = copia_limpa(tmp / f"quebra-{n}")
            plantar(raiz)
            if regerar:
                gerar_paginas(raiz)
            resultado = rodar_vigia(raiz, ambiente)
            travou = resultado.returncode == 1 and motivo_esperado(nome) in resultado.stdout
            print(f"  {'travou' if travou else 'PASSOU'} — {nome}")
            if not travou:
                falhas.append(nome)

        instalado = gancho_instalado()
        print(f"  {'ok' if instalado else 'FALHOU'} — gancho instalado e executável neste repositório")
        if not instalado:
            falhas.append("gancho não instalado neste repositório (git config core.hooksPath v7/02-regras/ferramentas/ganchos)")
        gancho = testar_gancho(tmp / "gancho", ambiente)
        print(f"  {'travou' if gancho else 'PASSOU'} — gancho: commit com quebra só no que entra no commit")
        if not gancho:
            falhas.append("gancho de commit")
        envio = testar_envio(tmp / "envio", ambiente)
        print(f"  {'travou' if envio else 'PASSOU'} — gancho de envio: commit sujo feito sem o gancho (--no-verify) não sobe")
        if not envio:
            falhas.append("gancho de envio")
        sem_marca = testar_chave_sem_marca(tmp / "chave", {**ambiente, "DELTA11_DENTRO_DO_PULSO": "1"})
        print(f"  {'travou' if sem_marca else 'PASSOU'} — a variável do pulso sozinha, sem o arquivo-marca, não pula o pulso")
        if not sem_marca:
            falhas.append("chave do pulso sem marca")

    if falhas:
        print(f"PULSO FALHOU — o vigia deixou passar {len(falhas)} quebra(s): {', '.join(falhas)}")
        return 1
    print(f"PULSO OK — o vigia travou as {len(todas)} quebras plantadas, e o gancho travou o commit sujo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
