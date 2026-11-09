"""O tradutor do motor do Delta-11 v7: todo gancho lê por aqui o que o programa de agentes mandou.

Cada programa de agentes (o Claude Code; depois o Codex e o Kilo) avisa os ganchos do jeito dele. Um tradutor por
programa, em `motores/`, transforma o aviso no pedido comum, sempre do mesmo jeito; a trava, o relógio, o aviso de
abertura e o registro de CRONOS só conhecem o pedido comum. As regras (`lugares.json`, as rotas, a esteira) não citam
programa nenhum.

Qual programa: o dito na instalação, nunca adivinhado pelo evento. O instalador o grava em `.delta-11/motor/VERSAO`
(campo `motor`) e o escreve, à vista, no fim do comando de cada gancho: `python3 -B ".../trava.py" claude-code`. Sem
programa dito, ou com um que o motor não conhece, `ler()` recusa (SemPrograma), e a trava barra.

O pedido comum (um dicionário):
  motor               o programa ("claude-code")
  evento              "antes" (de uma ferramenta), "depois", "abertura" (da conversa), "inicio-de-agente", "fim-de-agente"
  papel               o agente que age, em minúsculas ("" na conversa sem papel)
  agente_id, sessao   o agente chamado e a conversa ("" quando o programa não diz)
  pasta               a pasta em que o pedido roda ("" quando o programa não diz)
  ferramenta, dados   a ferramenta e a entrada dela, com os nomes e o formato do Claude Code (Write, Edit, NotebookEdit,
                      Read, Grep, Glob, Bash, Agent, SendMessage, TaskStop)
  arquivos            todos os arquivos que a ação escreve (vazio quando ela não escreve)
  origem              na abertura: startup, resume, clear, compact ou fork
  conversa, conversa_do_agente   onde ficam as transcrições da conversa e do agente chamado
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
# O nome dito na instalação → o arquivo do tradutor em motores/.
PROGRAMAS = {"claude-code": "claude_code"}
_tradutores: dict = {}


class SemPrograma(Exception):
    """O comando do gancho não diz o programa de agentes, ou diz um que o motor não conhece."""


class SemRaiz(Exception):
    """O programa de agentes não disse onde fica a pasta do produto."""


def tradutor_de(nome: str):
    if nome not in PROGRAMAS:
        raise SemPrograma(f"o comando deste gancho não diz qual programa de agentes o chamou (recebeu '{nome or 'nenhum'}'; o motor "
                          f"conhece: {', '.join(PROGRAMAS)}). O programa é dito na instalação, nunca adivinhado: sem ele, nada passa. "
                          "Quem mantém o Delta-11 reinstala o motor (`instalar.py --atualizar <pasta do produto>`).")
    if nome not in _tradutores:
        arquivo = AQUI / "motores" / f"{PROGRAMAS[nome]}.py"
        especificacao = importlib.util.spec_from_file_location(f"motor_{PROGRAMAS[nome]}", arquivo)
        modulo = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(modulo)
        _tradutores[nome] = modulo
    return _tradutores[nome]


def programa() -> str:
    """O programa dito no comando do gancho: a palavra depois do nome do arquivo."""
    return sys.argv[1] if len(sys.argv) > 1 else ""


def tradutor():
    return tradutor_de(programa())


def traduzir(evento: dict, nome: str) -> dict:
    pedido = tradutor_de(nome).traduzir(evento)
    pedido["motor"] = nome
    return pedido


def ler(aceita_vazio: bool = False) -> dict:
    """O pedido comum, lido da entrada do gancho. JSON quebrado: ValueError (a trava barra); entrada vazia só vale para
    quem aceita (o relógio, o aviso de abertura, o registro de CRONOS)."""
    nome = programa()
    tradutor_de(nome)  # sem programa conhecido, recusa antes de ler
    texto = sys.stdin.read()
    return traduzir(json.loads(texto or "{}") if aceita_vazio else json.loads(texto), nome)


def raiz(obrigatoria: bool = True) -> Path | None:
    """A pasta do produto, como o programa a diz (sem resolver atalhos). Sem ela: SemRaiz, ou None quando não é obrigatória."""
    try:
        achada = tradutor().raiz()
    except SemPrograma:
        if obrigatoria:
            raise
        return None
    if achada is None and obrigatoria:
        raise SemRaiz(tradutor().SEM_RAIZ)
    return achada


def barrar(texto: str) -> None:
    """Barra a ação: o motivo na saída de erros e o código 2 (os três programas aceitam; no Kilo, o complemento o troca por um erro)."""
    print(texto, file=sys.stderr)
    sys.exit(2)


def avisar(texto: str) -> None:
    """O contexto extra que o agente recebe depois de cada ferramenta (o relógio)."""
    tradutor().avisar(texto)


def processo_do_motor() -> int:
    """O processo do programa de agentes que chamou o gancho (o da conversa); 0 se não achou."""
    return tradutor().processo_do_motor()


def processo_vivo(pid: int) -> bool:
    """O processo ainda roda e é do programa de agentes (a conversa não fechou)."""
    return tradutor().processo_vivo(pid)


def pastas_privadas() -> list[Path]:
    """Onde o programa grava as conversas (o que cada agente viu, inclusive segredos e testes): ninguém as lê."""
    return tradutor().pastas_privadas()


def programa_da_instalacao(raiz_do_produto: Path) -> str:
    """O programa que o instalador gravou na VERSAO, para quem não é gancho (a caixa do produto não recebe o nome no comando)."""
    try:
        return str(json.loads((raiz_do_produto / ".delta-11" / "motor" / "VERSAO").read_text(encoding="utf-8")).get("motor") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def caches_liberados(principal: Path) -> list[Path]:
    """As pastas de cache das ferramentas (npm, pip...) em que o terminal grava, pelo tradutor do programa da instalação.
    Sem programa gravado na VERSAO, nenhuma: a caixa do produto só aperta."""
    nome = programa_da_instalacao(principal)
    return tradutor_de(nome).caches_liberados(principal) if nome in PROGRAMAS else []
