#!/usr/bin/env python3
"""
GERADOR DO CLAUDE.md POR MOTOR — Delta-11 v7 (motor multiempresa).

O CLAUDE.md da Formacao tem DUAS camadas:

  METODOLOGIA  as 7 camadas, as 17 regras inviolaveis, o protocolo de codigo,
               o painel, as correcoes aprendidas. A MESMA em todo motor.
               NUNCA e tocada.

  MOTOR        as 12 secoes que descrevem o COMO o orquestrador executa o
               protocolo: ativar, dispatch, hooks, worktree, SendMessage.
               Sao ~66 mil caracteres, e VALEM para o motor que as escreveu
               (Claude Code) — e nao para outro.

As secoes do motor estao marcadas no arquivo:
    <!-- MOTOR:CODIGO-INICIO --> ... <!-- MOTOR:CODIGO-FIM -->

Este gerador troca o que esta ENTRE os marcadores pela versao do motor
pedido. O que nao esta entre os marcadores (a metodologia) fica intacto.

O ORIGINAL fica guardado em `.delta-11/motor/CLAUDE-original.md` — a
referencia, consultavel, com o texto completo do motor Claude Code. Nao se
perde nada: a v7 troca o motor, nao o conhecimento.

Para o motor `claude-code`, o gerador NAO troca nada: o arquivo ja e a
versao do Claude Code. Isso e proposital — e o que garante que os 13
projetos que usam Claude Code fiquem com o texto de sempre.

Uso:
  python3 .delta-11/motor/gerar-claude-por-motor.py <motor> [--fonte F] [--saida S]
  python3 .delta-11/motor/gerar-claude-por-motor.py listar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DELTA_DIR = AQUI.parent
COD_INICIO = "<!-- MOTOR:CODIGO-INICIO -->"
COD_FIM = "<!-- MOTOR:CODIGO-FIM -->"

# O bloco de orientacao que fica no topo do arquivo (antes das secoes).
BLOCO_ATUAL = "<!-- MOTOR:INICIO -->"
BLOCO_FIM = "<!-- MOTOR:FIM -->"


# ─────────────────────────────────────────────────────────────────────────────
# O QUE CADA MOTOR ESCREVE NO LUGAR DAS SECOES MARCADAS
# ─────────────────────────────────────────────────────────────────────────────
#
# Cada motor recebe: (1) o bloco de orientacao no topo e (2) o texto que
# substitui as 12 secoes marcadas.
#
# O texto NAO precisa reescrever tudo: ele diz o que muda e manda ler o
# original para o resto. E o que evita duplicar 66 mil caracteres.

TEXTO_CLAUDE_CODE = """<!--
  ESTE BLOCO CONTÉM A DOCUMENTAÇÃO DO MOTOR CLAUDE CODE.

  O texto original (12 seções, ~66 mil caracteres) está guardado em
  `.delta-11/motor/CLAUDE-original.md`. Ele foi MOVIDO para lá porque
  descreve um motor específico — e os outros dois (Codex, Kilo) precisam
  de instruções que valem para eles.

  Mas no motor Claude Code este texto é o ATIVO: as 12 seções originales
  são a referência de como despachar, como os hooks disparam, o formato do
  prompt de ativação e a lista completa dos 37 vigias.

  Se você está lendo no Claude Code: leia a seção "MOTOR: ATIVO" acima e
  consulte `.delta-11/motor/CLAUDE-original.md` quando precisar do
  detalhe técnico (gatilhos, timeouts, formato exato do payload).

  Se você está lendo no Codex ou no Kilo: este bloco é substituído pelo
  texto daquele motor, e o original fica só como referência.
-->

"""

TEXTO_CODEX = """<!-- ════════════════════════════════════════════════════════════════
  MOTOR: CODEX CLI — o protocolo do Δ-11 neste motor
  ════════════════════════════════════════════════════════════════

O Codex CLI e a extensao do VS Code da OpenAI rodam o mesmo motor: tem
hooks de verdade, com o MESMO formato do Claude Code, e o MESMO contrato
de bloqueio (codigo de saida 2 + o motivo no stderr).

O QUE MUDA NESTE MOTOR (o resto do protocolo e o mesmo):

  DISPARO DE AGENTES
    O Claude Code usa a tool `Agent` com `isolation: "worktree"`. No Codex,
    o sub-agente e criado por `spawn_agent` (que casa como `Agent` no
    matcher). A worktree e criada pelo proprio Codex em
    `$CODEX_HOME/worktrees` — ou por `git worktree add` quando voce
    prefere controlar o caminho.

    O prompt de ativacao e o mesmo (a ESTRUTURA OBRIGATÓRIA DO PROMPT DE
    ATIVAÇÃO, abaixo). A unica troca e a ferramenta: onde o Claude Code
    diz "use a tool Agent", aqui o Codex diz "use spawn_agent" — e o
    sub-agente recebe o mesmo prompt, que e o que importa.

  OS 37 VIGIAS
    Os hooks do Codex tem o mesmo formato do Claude Code
    (matcher + hooks + command). O arquivo do projeto e
    `.codex/hooks.json`, e o global e `~/.codex/hooks.json`. Os DOIS
    sao lidos — e mesclados, nunca sobrescritos (o Delta-11 preserva os
    hooks que ja estavam la).

    O payload tem uma diferenca importante: o Codex edita arquivos por
    `apply_patch`, e o CAMINHO do arquivo vem DENTRO do patch (nao em
    `file_path`). O adaptador do Codex (`.delta-11/motor/codex/adaptador.py`)
    traduz isso no limite do motor: extrai o caminho, reconstroi o
    conteudo depois da edicao, e converte `apply_patch` em Write / Edit /
    MultiEdit. Por isso, do ponto de vista dos vigias, e como se fosse o
    Claude Code.

  IDENTIFICAR O AGENTE
    O Claude Code manda `agent_id` / `agent_type` / `session_id`. O Codex
    manda `session_id` (prefixo `thr_`), `turn_id`, `permission_mode`,
    `agent_type` e `agent_id` nos eventos de sub-agente. O vinculo com o
    ACK do agente continua o mesmo (`.delta-11/ativacoes/`).

  A PASTA PRINCIPAL
    O Claude Code usa a variavel `$CLAUDE_PROJECT_DIR`. O Codex nao tem
    essa variavel — a pasta principal se descobre pelo Git:
        GCD="$(git rev-parse --path-format=absolute --git-common-dir)"
        PRINCIPAL="$(cd "$GCD/.." && pwd)"
    E o que a documentacao oficial do Codex recomenda.

  O AGENTS.md
    No Codex, quem le as instrucoes automaticamente em cada execucao e o
    `AGENTS.md` da raiz do projeto (o equivalente do `CLAUDE.md`). O
    instalador do Delta-11 gera os dois, com o mesmo conteudo: o
    `CLAUDE.md` para o Claude Code e o `AGENTS.md` para o Codex.

  O TEXTO COMPLETO DO MOTOR CLAUDE CODE
    Onde este bloco esta, o texto original do motor Claude Code (12
    secoes, ~66 mil caracteres) esta guardado em
    `.delta-11/motor/CLAUDE-original.md`. Ele NAO foi perdido — foi
    MOVIDO para um arquivo so, porque descreve um motor especifico. As
    secoes que valem para todo motor (as 17 regras inviolaveis, o protocolo
    de codigo, o painel, as correcoes aprendidas) continuam NESTE ARQUIVO,
    inalteradas.

"""

TEXTO_KILO = """<!-- ════════════════════════════════════════════════════════════════
  MOTOR: KILO — o protocolo do Δ-11 neste motor
  ════════════════════════════════════════════════════════════════

O Kilo (fork do Roo Code, dentro do VS Code) e o motor mais diferente:
NAO TEM HOOKS. O schema oficial de configuracao dele nao tem a chave
"hooks", e nao existe "PreToolUse" no pacote. Entao o vigia nao dispara
sozinho — e o PORTAO que o agente chama antes de agir.

  DISPARO DE AGENTES
    O Claude Code usa a tool `Agent` com `isolation: "worktree"`. No Kilo,
    e o AGENT MANAGER: `mode: worktree`, com `tasks[].name` (o nome do
    agente, ex.: "back-onda-2"), `tasks[].branchName` e `tasks[].agent`.
    Todas as tarefas da onda saem na MESMA chamada — o paralelismo e
    nativo.

    O prompt de ativacao e o mesmo (a ESTRUTURA OBRIGATÓRIA DO PROMPT DE
    ATIVAÇÃO, abaixo). O `name` da sessao substitui o `name` do Agent
    tool, e e ele que o `SendMessage` usaria como destino.

  O PORTAO (a protecao que substitui os hooks)
    Antes de agir, o agente chama o PORTAO com o evento da acao:

        python3 .delta-11/motor/porteiro/porteiro.py <vigia> <<< '<evento json>'

    `exit 0` = liberado. `exit 2` = BLOQUEADO, com o motivo no stderr.
    O payload e o mesmo evento JSON que o Claude Code entrega nos hooks,
    entao o MESMO vigia roda.

    Para conferir a acao contra TODOS os vigias de uma vez (sem bloquear):

        python3 .delta-11/motor/porteiro/porteiro.py --auditar <<< '<evento json>'

    Um vigia que bloqueia e uma barreira, nao uma sugestao. Se o portao
    devolveu 2, a acao NAO foi feita.

  A CAMADA GROSSA DAS PROTECOES (nativa do Kilo)
    As permissoes do Kilo sao por recurso e efeito
    ({action, resource, effect}) e rodam no proprio motor — mesmo se o
    agente esquecer do portao:
      - `edit` DENY em `.delta-11/**`, `.claude/**`, `.git/**`
        (o sistema e do CRONOS)
      - `edit` ASK no kanban e na memoria dos agentes (o CRONOS confere)
      - `bash` DENY em `git stash`, `git push`, `git reset --hard`
      - `agent` ASK (todo despacho passa pelo pre-despacho)
      - `external` DENY (sem internet sem o comandante)
    As regras completas: `python3 .delta-11/motor/kilo/gerar-permissoes.py`.

  OS 10 AGENTES DO Δ-11
    Sao agentes customizados do Kilo (`~/.config/kilo/agent/*.md` ou
    `.kilo/agent/*.md`), gerados por
    `python3 .delta-11/motor/kilo/gerar-agentes.py`. Cada um carrega a
    identidade canonica (`.delta-11/operativos/`) e o bloco de motor.

  IDENTIFICAR O AGENTE
    O Claude Code manda `agent_id` / `agent_type`. O Kilo manda
    `kilo_agent_id` (a marca do motor) e `session_id` (formato `ses_...`,
    o do Agent Manager). O vinculo com o ACK continua o mesmo.

  A PASTA PRINCIPAL
    O Claude Code usa `$CLAUDE_PROJECT_DIR`. O Kilo nao tem essa
    variavel — a pasta principal se descobre pelo Git:
        GCD="$(git rev-parse --path-format=absolute --git-common-dir)"
        PRINCIPAL="$(cd "$GCD/.." && pwd)"

  A COMUNICACAO ENTRE AGENTES
    O Claude Code usa `SendMessage` (direto). No Kilo, o quadro
    (`board_post`): a mensagem e AVISO; o ARQUIVO e a verdade. O
    `-produto.md` do agente e o que o CRONOS le.

  O TEXTO COMPLETO DO MOTOR CLAUDE CODE
    Onde este bloco esta, o texto original do motor Claude Code (12
    secoes, ~66 mil caracteres) esta guardado em
    `.delta-11/motor/CLAUDE-original.md`. Ele NAO foi perdido — foi
    MOVIDO para um arquivo so, porque descreve um motor especifico. As
    secoes que valem para todo motor (as 17 regras inviolaveis, o protocolo
    de codigo, o painel, as correcoes aprendidas) continuam NESTE ARQUIVO,
    inalteradas.

"""

AVISO_CLAUDE_CODE = """<!--
  Seções do motor Claude Code (o motor de referência da Formação).

  O texto original completo (12 seções, ~66 mil caracteres) também está
  guardado em `.delta-11/motor/CLAUDE-original.md` — para consulta e para
  os outros motores (Codex, Kilo), que recebem instruções específicas
  deles no lugar destas seções.

  A METODOLOGIA (as 7 camadas, as 17 regras invioláveis, o protocolo de
  código, o painel, as correções aprendidas) NÃO está aqui: ela é a mesma
  em todo motor e vive fora destes marcadores.
-->

"""

TEXTOS = {
    "claude-code": TEXTO_CLAUDE_CODE,
    "codex": TEXTO_CODEX,
    "kilo": TEXTO_KILO,
}


def substituir_secoes(texto: str, motor: str) -> str:
    """
    Troca o que esta ENTRE os marcadores CODIGO-INICIO/FIM pelo texto do
    motor.

    COMO FUNCIONA (por bloco, nao no arquivo todo):
    - No motor `claude-code`: cada bloco mantem o SEU conteudo original. O
      Claude Code e o motor de referencia, e sao essas ~66 mil caracteres que
      ele le para saber despachar. O bloco ganha so um aviso de que o
      original tambem esta em `.delta-11/motor/CLAUDE-original.md`.
    - Nos motores `codex` e `kilo`: cada bloco e SUBSTITUIDO pelo texto
      daquele motor (que explica o que muda nele). O texto completo do
      motor Claude Code fica em `.delta-11/motor/CLAUDE-original.md`.

    A METODOLOGIA (fora dos marcadores) nunca e tocada.
    """
    if motor not in TEXTOS:
        raise ValueError(f"motor desconhecido: {motor}")
    if COD_INICIO not in texto:
        return texto

    partes = texto.split(COD_INICIO)
    saida = [partes[0]]
    for parte in partes[1:]:
        corpo, _sep, resto = parte.partition(COD_FIM)
        if motor == "claude-code":
            # Mantem o conteudo original deste bloco + o aviso.
            novo = AVISO_CLAUDE_CODE + "\n" + corpo
        else:
            novo = TEXTOS[motor]
        saida.append(f"{COD_INICIO}\n{novo}{COD_FIM}")
        saida.append(resto)
    return "".join(saida)


def trocar_bloco_atual(texto: str, motor: str) -> str:
    """Troca o bloco de orientacao do topo (MOTOR:INICIO/FIM)."""
    if BLOCO_ATUAL not in texto:
        return texto
    # O gerador do bloco tem hifen no nome (nao pode ser importado), entao
    # ele e carregado pelo caminho do arquivo.
    import importlib.util
    caminho = AQUI / "gerar-bloco-motor.py"
    spec = importlib.util.spec_from_file_location("delta11_bloco_motor", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    bloco = modulo.INICIO + "\n" + modulo.gerar_bloco(motor) + "\n" + modulo.FIM
    antes, _, depois = texto.partition(BLOCO_ATUAL)
    _, _, depois = depois.partition(BLOCO_FIM)
    return antes + bloco + depois


def gerar(texto: str, motor: str) -> str:
    return trocar_bloco_atual(substituir_secoes(texto, motor), motor)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("motor", help="claude-code | codex | kilo | listar")
    parser.add_argument("--fonte", help="CLAUDE.md de entrada. Padrao: a raiz da Formacao.")
    parser.add_argument("--saida", help="Arquivo de saida. Padrao: a stdout.")
    args = parser.parse_args()

    if args.motor == "listar":
        for nome in sorted(TEXTOS):
            print(f"  {nome}")
        return 0

    fonte = Path(args.fonte) if args.fonte else DELTA_DIR.parent / "CLAUDE.md"
    if not fonte.is_file():
        print(f"ERRO: CLAUDE.md nao encontrado em {fonte}", file=sys.stderr)
        return 1

    resultado = gerar(fonte.read_text(encoding="utf-8"), args.motor)

    if args.saida:
        Path(args.saida).write_text(resultado, encoding="utf-8")
        print(f"CLAUDE.md do motor '{args.motor}' escrito em {args.saida}")
    else:
        print(resultado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
