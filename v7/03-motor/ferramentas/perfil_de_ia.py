"""A IA de cada produto do Delta-11 v7: os perfis (agentes/perfis-de-ia.json) e a função que os aplica à configuração local do produto.

O Delta-11 mora no programa de agentes (o Claude Code), não na IA. DeepSeek, MiniMax e Kimi oferecem uma porta compatível com a API da
Anthropic; trocar de IA é, então, trocar variáveis de ambiente do Claude Code, escritas em `.claude/settings.local.json` do produto (que
fica fora do git e vale no painel do VSCode e no terminal). A chave NUNCA vai para arquivo: o `apiKeyHelper` guarda só o comando que a
tira do cofre na hora (ferramentas/chave-do-cofre.py).

Usado por instalar.py (--ia) e por trocar-ia.py. Só biblioteca padrão.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

FERRAMENTAS = Path(__file__).resolve().parent
MOTOR = FERRAMENTAS.parent
AJUDANTE_DO_COFRE = FERRAMENTAS / "chave-do-cofre.py"
PERFIL_PADRAO = "claude"
# As variáveis que um perfil de IA escreve no `env` da configuração local (e que trocar de perfil sempre tira antes de escrever as novas).
VARIAVEIS_DA_IA = ("ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                   "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL")
LEMBRETE_DO_LIMITE = "Lembrete: com outra IA, a qualidade do trabalho é a da IA escolhida; o Delta-11 garante a trava, a esteira e o processo."


class RecusaDePerfil(Exception):
    """Um pedido de IA que não pode ser atendido; a mensagem é a frase para o dono."""


def caminho_dos_perfis() -> Path:
    return Path(os.environ.get("DELTA11_PERFIS_DE_IA") or MOTOR / "agentes" / "perfis-de-ia.json")


def carregar_perfis() -> dict:
    try:
        perfis = json.loads(caminho_dos_perfis().read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        raise RecusaDePerfil(f"não consegui ler os perfis de IA ({caminho_dos_perfis()}): {erro}") from erro
    if not isinstance(perfis, dict) or PERFIL_PADRAO not in perfis:
        raise RecusaDePerfil(f"o arquivo de perfis de IA ({caminho_dos_perfis()}) está fora do formato.")
    return perfis


def comando_da_chave(entrada_do_cofre: str) -> str:
    """O comando que o Claude Code roda para ter a chave: só o caminho do ajudante e o NOME da entrada do cofre, nunca o valor."""
    return " ".join(shlex.quote(parte) for parte in (sys.executable, str(AJUDANTE_DO_COFRE), entrada_do_cofre))


def conferir_chave_no_cofre(nome_do_fornecedor: str, entrada_do_cofre: str) -> None:
    """Confere só se a entrada existe (a lista de nomes do cofre); o valor nunca é lido aqui."""
    feito = subprocess.run([sys.executable, "-B", str(AJUDANTE_DO_COFRE), "--existe", entrada_do_cofre], capture_output=True, text=True)
    if feito.returncode == 0:
        return
    if feito.returncode == 1:
        raise RecusaDePerfil(f"não achei a chave do {nome_do_fornecedor} no cofre (entrada {entrada_do_cofre}); guarde-a no cofre e rode de novo")
    motivo = feito.stderr.strip().replace("chave-do-cofre: ", "") or "sem resposta"
    raise RecusaDePerfil(f"não consegui abrir o cofre para conferir a chave do {nome_do_fornecedor} (entrada {entrada_do_cofre}): {motivo}")


def endereco_valido(endereco: str) -> bool:
    return endereco.startswith("https://") or endereco.startswith(("http://localhost", "http://127.0.0.1"))


def preparar_perfil(perfil: str, endereco: str = "", modelo_forte: str = "", modelo_medio: str = "", modelo_leve: str = "",
                    entrada_do_cofre: str = "") -> dict:
    """Confere o pedido (perfil conhecido, o que o gateway pede, a chave no cofre) e devolve o que vai para a configuração local.
    Nada é escrito aqui: serve também ao instalador, que confere antes de mexer na pasta."""
    perfis = carregar_perfis()
    if perfil not in perfis:
        raise RecusaDePerfil(f"não conheço o perfil de IA '{perfil}'; os perfis são: {', '.join(perfis)}.")
    dados = perfis[perfil]
    avisos = []
    if dados.get("conferido") is False:
        avisos.append(f"os nomes deste perfil não foram conferidos na fonte oficial ({dados.get('motivo', 'sem motivo escrito')}); confira-os antes de confiar.")
    pedido_extra = {"--endereco": endereco, "--modelo-forte": modelo_forte, "--modelo-medio": modelo_medio, "--modelo-leve": modelo_leve}
    if perfil == "claude":
        if any(pedido_extra.values()) or entrada_do_cofre:
            raise RecusaDePerfil("o perfil claude não troca nada; não há endereço, modelo nem entrada do cofre para dizer.")
        return {"perfil": perfil, "nome": dados["nome"], "variaveis": {}, "comando_da_chave": "", "avisos": avisos, "dados": dados}
    if perfil == "gateway":
        faltam = [opcao for opcao, valor in pedido_extra.items() if not valor]
        if faltam:
            raise RecusaDePerfil("o perfil gateway pede o endereço e os três modelos na linha de comando: --endereco <URL> --modelo-forte <nome> "
                                 f"--modelo-medio <nome> --modelo-leve <nome> (faltou: {', '.join(faltam)}); se a chave não estiver na entrada "
                                 f"{dados['entrada_do_cofre']} do cofre, diga também --entrada-do-cofre <NOME>.")
        if not endereco_valido(endereco):
            raise RecusaDePerfil(f"o endereço do gateway ({endereco}) precisa começar com https:// (ou http://localhost para um gateway nesta máquina).")
        valores = {"endereco": endereco, "modelo_forte": modelo_forte, "modelo_medio": modelo_medio, "modelo_leve": modelo_leve}
    else:
        if any(pedido_extra.values()):
            raise RecusaDePerfil(f"só o perfil gateway aceita endereço e modelos na linha de comando; o perfil {perfil} usa os de {caminho_dos_perfis().name}.")
        valores = {chave: dados[chave] for chave in ("endereco", "modelo_forte", "modelo_medio", "modelo_leve")}
    entrada = entrada_do_cofre or dados["entrada_do_cofre"]
    conferir_chave_no_cofre(dados["nome"], entrada)
    variaveis = {"ANTHROPIC_BASE_URL": valores["endereco"], "ANTHROPIC_MODEL": valores["modelo_forte"],
                 "ANTHROPIC_DEFAULT_OPUS_MODEL": valores["modelo_forte"], "ANTHROPIC_DEFAULT_SONNET_MODEL": valores["modelo_medio"],
                 "ANTHROPIC_DEFAULT_HAIKU_MODEL": valores["modelo_leve"], "CLAUDE_CODE_SUBAGENT_MODEL": valores["modelo_medio"]}
    return {"perfil": perfil, "nome": dados["nome"], "variaveis": variaveis, "comando_da_chave": comando_da_chave(entrada), "entrada_do_cofre": entrada,
            "avisos": avisos, "dados": dados}


def ler_configuracao_local(arquivo: Path) -> dict:
    if not arquivo.exists():
        return {}
    try:
        atual = json.loads(arquivo.read_text(encoding="utf-8"))
    except ValueError as erro:
        raise RecusaDePerfil(f"{arquivo} existe mas não é JSON válido; conserte ou mova esse arquivo antes de trocar a IA.") from erro
    if not isinstance(atual, dict):
        raise RecusaDePerfil(f"{arquivo} não é uma configuração do Claude Code.")
    return atual


def aplicar_perfil_de_ia(destino: Path, perfil: str, endereco: str = "", modelo_forte: str = "", modelo_medio: str = "", modelo_leve: str = "",
                         entrada_do_cofre: str = "") -> dict:
    """Escreve (ou tira, no perfil claude) a IA na configuração local do produto e devolve o resumo para o dono.
    Mexe só em `env` (as variáveis da IA) e em `apiKeyHelper` (só se for o nosso); o resto da configuração local fica como estava."""
    pedido = preparar_perfil(perfil, endereco, modelo_forte, modelo_medio, modelo_leve, entrada_do_cofre)
    arquivo = destino / ".claude" / "settings.local.json"
    atual = ler_configuracao_local(arquivo)
    avisos = list(pedido["avisos"])
    ambiente = dict(atual.get("env") or {}) if isinstance(atual.get("env"), dict) else {}
    tirou = [variavel for variavel in VARIAVEIS_DA_IA if ambiente.pop(variavel, None) is not None]
    ajudante_nosso = AJUDANTE_DO_COFRE.name in str(atual.get("apiKeyHelper") or "")
    if ajudante_nosso:
        atual.pop("apiKeyHelper")
        tirou.append("apiKeyHelper")
    if pedido["comando_da_chave"]:
        if atual.get("apiKeyHelper"):
            avisos.append("a configuração local tinha um apiKeyHelper de outro sistema; troquei pelo do cofre.")
        atual["apiKeyHelper"] = pedido["comando_da_chave"]
        ambiente.update(pedido["variaveis"])
    if ambiente:
        atual["env"] = ambiente
    else:
        atual.pop("env", None)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=arquivo.parent, prefix=".settings.local.", suffix=".tmp", delete=False) as provisorio:
        provisorio.write(json.dumps(atual, ensure_ascii=False, indent=2) + "\n")
    os.replace(provisorio.name, arquivo)
    dados = pedido["dados"]
    return {"perfil": perfil, "nome": pedido["nome"], "modelo_forte": pedido["variaveis"].get("ANTHROPIC_DEFAULT_OPUS_MODEL", ""),
            "modelo_medio": pedido["variaveis"].get("ANTHROPIC_DEFAULT_SONNET_MODEL", ""), "modelo_leve": pedido["variaveis"].get("ANTHROPIC_DEFAULT_HAIKU_MODEL", ""),
            "entrada_do_cofre": pedido.get("entrada_do_cofre", ""), "fonte": dados.get("fonte", ""), "lido_em": dados.get("lido_em", ""),
            "conferido": dados.get("conferido") is not False, "avisos": avisos, "tirou": tirou}


def arquivo_da_versao(destino: Path) -> Path:
    return destino / ".delta-11" / "motor" / "VERSAO"


def ia_instalada(destino: Path) -> str:
    """A IA que a VERSAO da pasta diz (vazio numa instalação de antes dos perfis de IA)."""
    try:
        return str(json.loads(arquivo_da_versao(destino).read_text(encoding="utf-8")).get("ia") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def gravar_ia_na_versao(destino: Path, perfil: str) -> None:
    arquivo = arquivo_da_versao(destino)
    marca = json.loads(arquivo.read_text(encoding="utf-8"))
    marca["ia"] = perfil
    arquivo.write_text(json.dumps(marca, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
