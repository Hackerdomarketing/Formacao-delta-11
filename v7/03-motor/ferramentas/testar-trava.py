#!/usr/bin/env python3
"""Pulso da trava do motor (ganchos/trava.py): prova que ela barra cada fraude e cada descuido, e deixa o trabalho certo.

Monta uma pasta de produto descartável com a trava e o mapa (agentes/lugares.json), e manda à trava, como o
Claude Code mandaria, um pedido de cada caso: quem age, com qual ferramenta, em qual arquivo. Cada caso diz se a
trava tem de deixar ou barrar, e por qual motivo. Inclui todas as burlas que o Destruidor do motor achou.
Uso: python3 testar-trava.py   (sai com 1 se algum caso der o resultado errado)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
DEIXA = None
CAIXA = "python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py"
TELA = "python3 -I -B .claude/hooks/delta-11/tela-do-app.py"
PROCESSOS: list = []
# O programa de agentes, no fim do comando de cada gancho, como a instalação o escreve (os ganchos leem pelo tradutor dele).
PROGRAMA = "claude-code"


def casos(p: Path) -> list[tuple]:
    """(nome do caso, papel, ferramenta, entrada, motivo esperado ou DEIXA, cwd relativo)."""
    w = lambda c: {"file_path": str(p / c), "content": "x"}
    r = lambda c: {"file_path": str(p / c)}
    copia = ".claude/worktrees/agent-candidata1"
    return [
        # Escrita: cada papel no seu lugar
        ("ATLAS escreve a Luz", "atlas", "Write", w(".delta-11/luz.md"), DEIXA, ""),
        ("ATLAS guarda um segredo no cofre", "atlas", "Write", w(".delta-11/cofre/chave.txt"), DEIXA, ""),
        ("ATLAS escreve código", "atlas", "Write", w("src/telas/inicio.js"), "não escreve em o código", ""),
        ("ATLAS edita um caderno no código (NotebookEdit)", "atlas", "NotebookEdit", {"notebook_path": str(p / "src/analise.ipynb")}, "não escreve em o código", ""),
        ("FRAUDE: ATLAS reescreve o mapa da trava", "atlas", "Write", w(".claude/hooks/delta-11/lugares.json"), "não escreve em `.claude/`", ""),
        ("FRAUDE: Documentador edita a própria trava", "documentador", "Edit", {"file_path": str(p / ".claude/hooks/delta-11/trava.py")}, "não escreve em `.claude/`", ""),
        ("FRAUDE: ATLAS troca a configuração do projeto", "atlas", "Write", w(".claude/settings.json"), "não escreve em `.claude/`", ""),
        ("FRAUDE: link com dois nomes para o código", "atlas", "Write", w(".delta-11/registro/atalho.txt"), "mais de um nome", ""),
        ("FRAUDE: link simbólico em .delta-11 apontando ao código", "atlas", "Write", w(".delta-11/registro/simbolico.js"), "não escreve em o código", ""),
        ("FRAUDE: caminho com ../ saindo para o código", "atlas", "Write", w(".delta-11/registro/../../src/telas/inicio.js"), "não escreve em o código", ""),
        ("FRAUDE: escrever no histórico do git", "front", "Write", w(".git/config"), "não escreve em `.git/`", ""),
        ("FRONT escreve nas configurações pessoais do computador", "front", "Write", {"file_path": str(Path.home() / ".claude" / "settings.json"), "content": "x"}, "fora da pasta em que trabalha", ""),
        ("FRONT escreve no território dele", "front", "Write", w("src/telas/inicio.js"), DEIXA, ""),
        ("FRAUDE: FRONT escreve no arquivo que tem um segundo nome", "front", "Write", w("src/telas/alvo-do-link.js"), "mais de um nome", ""),
        ("FRAUDE: FRONT escreve na pasta do PIXEL, que fica dentro da dele", "front", "Write", w("src/telas/estilos/cores.css"), "não fica nas pastas do território de front", ""),
        ("PIXEL escreve na pasta dele, dentro da do FRONT", "pixel", "Write", w("src/telas/estilos/cores.css"), DEIXA, ""),
        ("FRAUDE: Revisor lê as conversas gravadas do Claude Code", "revisor", "Read", {"file_path": str(Path.home() / ".claude/projects/qualquer/conversa.jsonl")}, "conversas gravadas", ""),
        ("FRONT escreve no território do VAULT", "front", "Write", w("banco/migracoes/1.sql"), "não fica nas pastas do território de front", ""),
        ("BACK escreve arquivo fora de todo território", "back", "Write", w("package.json"), DEIXA, ""),
        ("VAULT escreve arquivo fora de todo território", "vault", "Write", w("package.json"), "não fica nas pastas do território de vault", ""),
        ("SCOUT corrige em qualquer território", "scout", "Edit", {"file_path": str(p / "banco/migracoes/1.sql")}, DEIXA, ""),
        ("FRONT escreve a própria linha", "front", "Write", w(".delta-11/quadro/camada-3/linhas/front-1.md"), DEIXA, ""),
        ("FRONT escreve a linha do PIXEL", "front", "Write", w(".delta-11/quadro/camada-3/linhas/pixel-1.md"), "só escreve na própria linha", ""),
        ("FRONT escreve um brief", "front", "Write", w(".delta-11/quadro/camada-3/briefs/front-2.md"), "não escreve em `.delta-11/quadro/<X>/`", ""),
        ("CRONOS escreve um brief", "cronos", "Write", w(".delta-11/quadro/camada-3/briefs/front-2.md"), DEIXA, ""),
        ("CRONOS escreve a abertura (é do ARQUITETO)", "cronos", "Write", w(".delta-11/quadro/camada-3/abertura.md"), "não escreve em `.delta-11/quadro/<X>/abertura.md`", ""),
        ("ARQUITETO escreve a abertura", "arquiteto", "Write", w(".delta-11/quadro/camada-3/abertura.md"), DEIXA, ""),
        ("ARQUITETO escreve os endereços dos territórios", "arquiteto", "Write", w(".delta-11/regras/enderecos.txt"), DEIXA, ""),
        ("FRONT muda os endereços dos territórios", "front", "Write", w(".delta-11/regras/enderecos.txt"), "não escreve em `.delta-11/regras/enderecos.txt`", ""),
        ("CRONOS escreve o selo", "cronos", "Write", w(".delta-11/quadro/camada-3/selo.md"), "não escreve em `.delta-11/quadro/<X>/selo.md`", ""),
        ("Selador escreve o selo", "selador", "Write", w(".delta-11/quadro/camada-3/selo.md"), DEIXA, ""),
        ("Destruidor escreve o teste guardado", "destruidor", "Write", w(".delta-11/teste-guardado/camada-1.md"), DEIXA, ""),
        ("Destruidor conserta o código", "destruidor", "Edit", {"file_path": str(p / "src/telas/inicio.js")}, "não escreve em o código", ""),
        ("Revisor escreve no registro", "revisor", "Write", w(".delta-11/registro/revisor.md"), DEIXA, ""),
        ("Documentador escreve o arquivo de estado", "documentador", "Write", w(".delta-11/estado/camada-3.md"), DEIXA, ""),
        ("Leitor do teste tenta escrever", "leitor-do-teste", "Write", w(".delta-11/leitor/camada-1/x.md"), "não escreve em `.delta-11/leitor/`", ""),
        ("Candidata escreve o território dela na própria cópia", "front", "Write", {"file_path": str(p / copia / "src/telas/coracao.js"), "content": "x"}, DEIXA, copia),
        ("Candidata escreve fora do território na própria cópia", "front", "Write", {"file_path": str(p / copia / "banco/x.sql"), "content": "x"}, "não fica nas pastas do território de front", copia),
        ("Agente fora da cópia escreve dentro da cópia de uma candidata", "front", "Write", {"file_path": str(p / copia / "src/telas/coracao.js"), "content": "x"}, "não escreve em `.claude/`", ""),
        # Leitura
        ("CRONOS abre o teste guardado", "cronos", "Read", r(".delta-11/teste-guardado/camada-1.md"), "não lê `.delta-11/teste-guardado/`", ""),
        ("Selador abre o teste guardado", "selador", "Read", r(".delta-11/teste-guardado/camada-1.md"), DEIXA, ""),
        ("FRONT abre o cofre", "front", "Read", r(".delta-11/cofre/chave.txt"), "não lê `.delta-11/cofre/`", ""),
        ("BACK abre o cofre", "back", "Read", r(".delta-11/cofre/chave.txt"), DEIXA, ""),
        ("Revisor abre um brief", "revisor", "Read", r(".delta-11/quadro/camada-3/briefs/front-2.md"), "não lê `.delta-11/quadro/<X>/`", ""),
        ("Revisor abre o teste do fruto nos modelos", "revisor", "Read", r(".delta-11/motor/modelos/testes-do-fruto.md"), DEIXA, ""),
        ("Revisor busca na raiz", "revisor", "Grep", {"pattern": "x", "path": str(p)}, "não busca em na raiz", ""),
        ("Revisor busca no código", "revisor", "Grep", {"pattern": "x", "path": str(p / "src")}, DEIXA, ""),
        ("Revisor lista tudo com um padrão na raiz", "revisor", "Glob", {"pattern": "**/*.md"}, "não busca em na raiz", ""),
        ("Destruidor busca dentro do quadro da camada", "destruidor", "Grep", {"pattern": "x", "path": str(p / ".delta-11/quadro/camada-3")}, "não lê `.delta-11/quadro/<X>/`", ""),
        ("Destruidor abre a linha de um Construtor", "destruidor", "Read", r(".delta-11/quadro/camada-3/linhas/front-1.md"), "não lê `.delta-11/quadro/<X>/linhas/<nome>-<n>.md`", ""),
        ("Destruidor abre os inimigos da camada", "destruidor", "Read", r(".delta-11/quadro/camada-3/inimigos.md"), DEIXA, ""),
        ("Leitor do teste abre a Luz inteira", "leitor-do-teste", "Read", r(".delta-11/luz.md"), "só lê dentro de .delta-11/leitor/", ""),
        ("Leitor do teste abre o que o Selador separou", "leitor-do-teste", "Read", r(".delta-11/leitor/camada-1/luz-compacta.md"), DEIXA, ""),
        ("CRONOS busca na raiz (o teste guardado fica fora do git)", "cronos", "Grep", {"pattern": "x", "path": str(p)}, DEIXA, ""),
        # Terminal vigiado
        ("Destruidor roda os testes", "destruidor", "Bash", {"command": "npm test 2>&1 | tail -20"}, DEIXA, ""),
        ("Destruidor roda um comando com seta de JavaScript", "destruidor", "Bash", {"command": "node -e \"[1].map(x => x)\""}, DEIXA, ""),
        ("Destruidor grava arquivo pelo terminal", "destruidor", "Bash", {"command": "echo conserto > src/telas/inicio.js"}, "terminal do destruidor é vigiado", ""),
        ("Destruidor grava em arquivo temporário", "destruidor", "Bash", {"command": "curl -s localhost:3000 > /tmp/resposta.html"}, DEIXA, ""),
        ("Selador faz commit", "selador", "Bash", {"command": "git commit -am selo"}, "terminal do selador é vigiado", ""),
        ("Selador edita no lugar com sed", "selador", "Bash", {"command": "sed -i '' s/a/b/ src/x.js"}, "terminal do selador é vigiado", ""),
        ("Revisor lê o quadro pelo terminal", "revisor", "Bash", {"command": "cat .delta-11/quadro/camada-3/quadro.md"}, "não lê pelo terminal", ""),
        ("Selador copia arquivo", "selador", "Bash", {"command": "cp src/a.js src/b.js"}, "terminal do selador é vigiado", ""),
        ("FRONT usa o terminal livre", "front", "Bash", {"command": "npm install && npm run build > build.log"}, DEIXA, ""),
        # Porteiro
        ("ATLAS chama o ARQUITETO", "atlas", "Agent", {"subagent_type": "arquiteto", "prompt": "x", "run_in_background": False}, DEIXA, ""),
        ("ATLAS chama o ARQUITETO sem dizer o plano", "atlas", "Agent", {"subagent_type": "arquiteto", "prompt": "x"}, "diga run_in_background: false", ""),
        ("ATLAS liga o CRONOS com a pasta na mensagem", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-4/: leia a abertura.", "run_in_background": True}, DEIXA, ""),
        ("ATLAS liga o CRONOS sem dizer a pasta do quadro", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza a camada.", "run_in_background": True}, "diz a pasta do quadro", ""),
        ("ATLAS liga um segundo CRONOS com um trabalhando nesta conversa", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-3/.", "run_in_background": True}, "está trabalhando nesta conversa", ""),
        ("ATLAS liga o CRONOS de um pedido que outra conversa aberta conduz", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/pedido-7/.", "run_in_background": True}, "trabalha em outra conversa", ""),
        ("ATLAS liga o CRONOS de uma camada cuja conversa já fechou", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-8/.", "run_in_background": True}, DEIXA, ""),
        ("ATLAS manda mensagem ao CRONOS desta conversa pelo agentId", "atlas", "SendMessage", {"to": "a1cronos3", "message": "x"}, DEIXA, ""),
        ("ATLAS acorda o seu CRONOS de um pedido que outra conversa conduz agora", "atlas", "SendMessage", {"to": "a2fim", "message": "x"}, "trabalha em outra conversa aberta", ""),
        ("ATLAS liga dois CRONOS seguidos", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-9/.", "run_in_background": True}, "ligue um por vez", ""),
        ("ATLAS manda mensagem a um agentId que não é de CRONOS desta conversa", "atlas", "SendMessage", {"to": "a9outro", "message": "x"}, "só manda mensagem a um CRONOS desta conversa", ""),
        ("ATLAS manda mensagem a um Construtor", "atlas", "SendMessage", {"to": "front", "message": "x"}, "só manda mensagem a um CRONOS desta conversa", ""),
        ("CRONOS manda mensagem ao ATLAS (main)", "cronos", "SendMessage", {"to": "main", "message": "x"}, DEIXA, ""),
        ("FRONT manda mensagem ao ATLAS", "front", "SendMessage", {"to": "main", "message": "x"}, "não manda mensagem para 'main'", ""),
        ("CRONOS chama um Construtor em segundo plano", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "run_in_background": True}, "chamado em primeiro plano", ""),
        ("CRONOS chama candidata na Camada 3 reaberta", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "isolation": "worktree", "run_in_background": False}, DEIXA, "", "camada-3-reaberta"),
        ("CRONOS chama candidata em cópia isolada sem a Camada 3 aberta", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "isolation": "worktree"}, "só para as candidatas", "", "sem-camada-3"),
        # Só a esteira junta
        ("FRAUDE: FRONT faz commit direto na pasta principal", "front", "Bash", {"command": "git add -A && git commit -m pronto"}, "não mexe na história do git", ""),
        ("FRAUDE: FRONT volta a história com reset", "front", "Bash", {"command": "git reset --hard HEAD~3"}, "não mexe na história do git", ""),
        ("FRONT entrega pela esteira", "front", "Bash", {"command": "sh esteira front src/telas/inicio.js"}, DEIXA, ""),
        ("SHIELD roda o teste vermelho plantado do produto", "shield", "Bash", {"command": "sh testes/vermelho-plantado.sh && npx vitest run testes/vermelho.test.ts"}, DEIXA, ""),
        ("BACK confere a sintaxe da esteira", "back", "Bash", {"command": "sh -n esteira"}, DEIXA, ""),
        ("FRONT procura a palavra esteira no código", "front", "Bash", {"command": "grep -rn \"esteira\" src/"}, DEIXA, ""),
        ("FRONT entrega rota com parênteses e com $ entre aspas", "front", "Bash", {"command": "sh esteira front 'app/(auth)/login/page.tsx' 'app/routes/posts.$id.tsx'"}, DEIXA, ""),
        ("FRAUDE: FRONT roda uma esteira falsa de uma subpasta", "front", "Bash", {"command": "sh esteira front x"}, "só roda na raiz", "src/telas"),
        ("FRAUDE: FRONT entrega com o nome do ENGINE", "front", "Bash", {"command": "sh esteira engine src/servidor/rota.js"}, "entrega com o próprio nome", ""),
        ("FRAUDE: Selador roda a esteira", "selador", "Bash", {"command": "sh esteira front src/a.js"}, "não entrega à esteira", ""),
        ("BACK lê e confere o programa da esteira", "back", "Bash", {"command": "cat esteira && chmod +x esteira && shellcheck esteira && git diff esteira"}, DEIXA, ""),
        ("FRONT procura a palavra esteira num arquivo", "front", "Bash", {"command": "grep -n esteira README.md"}, DEIXA, ""),
        ("FRAUDE: Selador roda a esteira com o nome entre aspas", "selador", "Bash", {"command": 'sh "esteira" front src/a.js'}, "rode a esteira sozinha", ""),
        ("FRAUDE: Revisor roda a esteira depois de uma variável", "revisor", "Bash", {"command": "X=1 sh esteira front src/a.js"}, "rode a esteira sozinha", ""),
        # A caixa do produto: o jeito de rodar o produto, fora da caixa de areia do Claude Code
        ("FRONT roda o teste no navegador pela caixa do produto", "front", "Bash", {"command": CAIXA + " npx playwright test"}, DEIXA, ""),
        ("Revisor usa o produto pela caixa, encadeando com sh -c", "revisor", "Bash", {"command": CAIXA + " olhar sh -c 'npm run build && npm test'"}, DEIXA, ""),
        ("Revisor roda o produto pela caixa sem olhar", "revisor", "Bash", {"command": CAIXA + " npm test"}, "olhar", ""),
        ("Destruidor roda no navegador um roteiro com tags e seletor de filho", "destruidor", "Bash",
         {"command": CAIXA + """ olhar node -e 'p.goto("/?x=<script>"); p.click("form > button"); if (itens.length > total) console.log("<h1>")'"""}, DEIXA, ""),
        ("Selador roda a cópia de uma candidata da raiz", "selador", "Bash", {"command": CAIXA + " olhar --raiz .claude/worktrees/agent-candidata1 npm run build"}, DEIXA, ""),
        ("FRAUDE: Revisor lê a história do git pela caixa", "revisor", "Bash", {"command": CAIXA + " olhar git log --oneline"}, "não lê a história do git", ""),
        ("Destruidor escreve um roteiro de ataque no rascunho", "destruidor", "Write", w(".rascunho/destruidor-1.mjs"), DEIXA, ""),
        ("FRONT escreve no rascunho de quem confere", "front", "Write", w(".rascunho/x.mjs"), "não escreve em `.rascunho/`", ""),
        ("Destruidor confere se o site publicado mostra o .git", "destruidor", "Bash", {"command": CAIXA + " olhar curl -s https://meu-produto.pages.dev/.git/HEAD"}, DEIXA, ""),
        ("FRAUDE: Destruidor lê o .git da pasta pela caixa", "destruidor", "Bash", {"command": CAIXA + " olhar cat .git/HEAD"}, "não lê pelo terminal", ""),
        ("candidata acrescenta uma dependência na cópia dela", "front", "Edit", {"file_path": str(p / ".claude/worktrees/agent-candidata1/package.json")}, DEIXA, ".claude/worktrees/agent-candidata1"),
        ("FRONT muda o package.json na pasta principal", "front", "Edit", {"file_path": str(p / "package.json")}, "não fica nas pastas do território de front", ""),
        ("FRAUDE: CRONOS lista a raiz inteira (veria os nomes do cofre)", "cronos", "Glob", {"pattern": "**/*", "path": str(p)}, "não busca", ""),
        ("CRONOS lista o quadro", "cronos", "Glob", {"pattern": "**/*.md", "path": str(p / ".delta-11/quadro")}, DEIXA, ""),
        ("ATLAS lista o que está direto em .delta-11/ (Glob sem descer)", "atlas", "Glob", {"pattern": ".delta-11/*", "path": str(p)}, DEIXA, ""),
        ("FRAUDE: ATLAS lista .delta-11/ por dentro (veria os nomes do cofre)", "atlas", "Glob", {"pattern": ".delta-11/**", "path": str(p)}, "não busca", ""),
        ("FRAUDE: ATLAS lista um nível abaixo de .delta-11/", "atlas", "Glob", {"pattern": ".delta-11/*/*", "path": str(p)}, "não busca", ""),
        ("FRAUDE: Destruidor lê o quadro por um curinga", "destruidor", "Bash", {"command": "cat .d*/quadro/camada-3/briefs/front-1.md"}, "não lê pelo terminal", ""),
        ("FRAUDE: Revisor lê a Luz por .*", "revisor", "Bash", {"command": "cat .*/luz.md"}, "não lê pelo terminal", ""),
        ("FRAUDE: Revisor lê por .[d]elta", "revisor", "Bash", {"command": "cat .[d]elta-11/luz.md"}, "não lê pelo terminal", ""),
        ("FRAUDE: Revisor busca na raiz pelo caminho completo", "revisor", "Bash", {"command": f"grep -rn senha {p}/"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor lista a cópia de uma candidata inteira", "destruidor", "Bash", {"command": "ls -R .claude/worktrees/agent-candidata1"}, "não lê pelo terminal", ""),
        ("Destruidor procura arquivos de teste com curinga", "destruidor", "Bash", {"command": "find src -name *.[jt]s"}, DEIXA, ""),
        ("FRONT roda pela caixa um comando com $(...)", "front", "Bash", {"command": CAIXA + " sh -c 'echo $(date)'"}, "deixa a caixa do produto dentro da caixa de areia", ""),
        ("FRAUDE: Revisor roda a esteira escondida num sh -c pela caixa", "revisor", "Bash", {"command": CAIXA + " olhar sh -c 'sh esteira front src/a.js | tail -3'"}, "rode a esteira sozinha", ""),
        ("FRONT lê o relato inteiro da esteira", "front", "Read", r(".delta-11/esteira/front-2026-10-17-1200.log"), DEIXA, ""),
        ("Revisor lê o relato da esteira", "revisor", "Read", r(".delta-11/esteira/front-2026-10-17-1200.log"), "não lê", ""),
        ("FORM entrega junto com o ENGINE uma regra que só funciona junta", "form", "Bash", {"command": "sh esteira form,engine src/form/valida.mjs servidor/valida.mjs"}, DEIXA, ""),
        ("FRAUDE: FRONT entrega em nome de outros dois", "front", "Bash", {"command": "sh esteira form,engine src/a.js"}, "entrega com o próprio nome", ""),
        ("FRAUDE: FRONT entrega junto com o PIXEL, que não aceitou", "front", "Bash", {"command": "sh esteira front,pixel src/telas/a.js src/telas/estilos/b.css"}, "Entrego junto", ""),
        ("FRAUDE: FRONT usa o espaço em branco do modelo como aceite do PIXEL", "front", "Bash", {"command": "sh esteira front,pixel src/telas/a.js"}, "Entrego junto", ""),
        ("FRAUDE: FRONT usa o 'Entrego junto: nenhum' do VAULT como aceite", "front", "Bash", {"command": "sh esteira front,vault src/telas/a.js banco/x.sql"}, "Entrego junto", ""),
        ("FRAUDE: FRONT usa o aceite do FORM de uma camada já selada", "front", "Bash", {"command": "sh esteira front,form src/telas/a.js src/form/a.js"}, "Entrego junto", ""),
        ("SHIELD monta um repositório de ensaio da esteira no temporário", "shield", "Bash", {"command": 'git init -q "$TMPDIR/ensaio-esteira"'}, DEIXA, ""),
        ("SHIELD faz commit no repositório de ensaio do temporário", "shield", "Bash", {"command": 'git -C "$TMPDIR/ensaio-esteira" commit -qm base'}, DEIXA, ""),
        ("FRAUDE: FRONT liga um CRONOS de pedido com a camada aberta", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/pedido-30/.", "run_in_background": True}, "há uma camada aberta", ""),
        ("SHIELD monta o repositório de ensaio entrando no temporário", "shield", "Bash", {"command": 'cd "$TMPDIR/ensaio" && git init -q'}, DEIXA, ""),
        ("FRONT quer desfazer a mudança dele com git restore", "front", "Bash", {"command": "git restore src/telas/inicio.js"}, "git show HEAD:", ""),
        ("FRAUDE: FRONT se dá os poderes do SCOUT numa entrega conjunta", "front", "Bash", {"command": "sh esteira front,scout src/servidor/rota.ts"}, "entrega com o próprio nome", ""),
        ("FRAUDE: FORM põe um papel que não constrói na entrega conjunta", "form", "Bash", {"command": "sh esteira form,revisor src/a.js"}, "entrega com o próprio nome", ""),
        ("FRAUDE: Destruidor busca em todas as cópias de uma vez", "destruidor", "Bash", {"command": "grep -rn senha .claude/worktrees"}, "não lê pelo terminal", ""),
        ("FRAUDE: Revisor busca em .claude inteira", "revisor", "Bash", {"command": "grep -rln front .claude/"}, "não lê pelo terminal", ""),
        ("FRAUDE: CRONOS lê o cofre de outro produto", "cronos", "Read", {"file_path": str(p.parent / "outro-produto/.delta-11/cofre/x")}, "não fica nesta pasta", ""),
        ("FRAUDE: Revisor lê os briefs na cópia temporária da esteira", "revisor", "Read", {"file_path": str(p.parent / "esteira.abc/.delta-11/quadro/camada-3/briefs/front-1.md")}, "não fica nesta pasta", ""),
        ("FRAUDE: FRONT descarta uma pasta fora das cópias", "front", "Bash", {"command": "sh esteira front --descartar /Users/x/Documents"}, "só aceita a cópia de uma candidata", ""),
        ("FRAUDE: FRONT descarta a raiz", "front", "Bash", {"command": "sh esteira front --descartar ."}, "só aceita a cópia de uma candidata", ""),
        ("ARQUITETO digita errado o caminho do produto", "arquiteto", "Read", {"file_path": "/private/tmp/caminho-que-nao-existe-delta/produto/.delta-11/quadro/camada-3/abertura.md"}, "não existe", ""),
        ("FRONT procura a frase git push no código", "front", "Bash", {"command": 'grep -rn "git push" src/'}, DEIXA, ""),
        ("FRAUDE: FRONT faz commit escondido num sh -c", "front", "Bash", {"command": "sh -c 'git commit -qm x'"}, "não mexe na história do git", ""),
        ("Destruidor lista as regras do produto", "destruidor", "Bash", {"command": "ls .delta-11/regras/"}, DEIXA, ""),
        ("Destruidor lê o relato da cópia de ataque pela caixa", "destruidor", "Bash", {"command": CAIXA + " olhar relato-da-copia destruidor-1"}, DEIXA, ""),
        ("FRAUDE: FRONT pede à caixa para gravar nos dados reais do dono", "front", "Bash", {"command": CAIXA + " --com-ambiente sh -c 'echo x'"}, "só o publicar da esteira", ""),
        ("FRAUDE: BACK pede a gravação nos dados do dono com aspas simples", "back", "Bash", {"command": CAIXA + " '--com-ambiente' sh -c 'echo x'"}, "só o publicar da esteira", ""),
        ("FRAUDE: FRONT pede a gravação nos dados do dono com aspas duplas", "front", "Bash", {"command": CAIXA + ' "--com-ambiente" sh -c "echo x"'}, "só o publicar da esteira", ""),
        ("FRAUDE: Destruidor pede a gravação nos dados do dono no modo de olhar", "destruidor", "Bash", {"command": CAIXA + " olhar '--com-ambiente' sh -c 'echo x'"}, "só o publicar da esteira", ""),
        ("FRAUDE: FRONT pede a gravação nos dados do dono depois do --raiz", "front", "Bash", {"command": CAIXA + " --raiz .claude/worktrees/agent-candidata1 '--com-ambiente' sh -c 'echo x'"}, "só o publicar da esteira", ""),
        ("FRONT roda um comando cujo texto cita --com-ambiente", "front", "Bash", {"command": CAIXA + " sh -c 'echo --com-ambiente'"}, DEIXA, ""),
        ("FRAUDE: Destruidor lê .delta-11 por um --raiz de cópia de ataque", "destruidor", "Bash",
         {"command": CAIXA + " olhar --raiz /private/var/folders/xy/T/delta11-ataque-d1 sh -c 'cat .delta-11/esteira/*.log'"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor esconde o --raiz num comentário", "destruidor", "Bash",
         {"command": "cat .delta-11/licoes.md # --raiz /private/var/folders/xy/T/delta11-ataque-d1 x"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor clona o produto para o temporário", "destruidor", "Bash", {"command": "git clone -q . /tmp/clone-do-produto"}, "não lê a história do git", ""),
        ("FRAUDE: Destruidor cria um atalho para o produto num programa em linha", "destruidor", "Bash",
         {"command": "python3 -c \"import os; os.symlink('" + str(p) + "', '/tmp/atalho')\""}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Destruidor sobe das regras para as lições com ..", "destruidor", "Bash", {"command": "cat .delta-11/regras/../licoes.md"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor lê o quadro do produto por caminho absoluto, pela cópia de ataque", "destruidor", "Bash",
         {"command": CAIXA + " olhar --raiz /private/var/folders/xy/T/delta11-ataque-d1 cat " + str(p) + "/.delta-11/quadro/camada-3/quadro.md"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor lê .delta-11 de uma pasta no temporário", "destruidor", "Bash", {"command": "cat /tmp/d2-neutro/.delta-11/esteira/front.log"}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor sai do temporário com ../ para o quadro", "destruidor", "Bash", {"command": "cat /tmp/x/../.." + str(p) + "/.delta-11/quadro/camada-3/quadro.md"}, "não lê pelo terminal", ""),
        ("Destruidor monta a cópia de ataque pela caixa", "destruidor", "Bash", {"command": CAIXA + " olhar copia-de-ataque destruidor-1"}, DEIXA, ""),
        ("Revisor lista as regras do produto", "revisor", "Bash", {"command": "ls .delta-11/regras/"}, "não lê pelo terminal", ""),
        ("Destruidor lê a própria linha", "destruidor", "Read", r(".delta-11/quadro/camada-3/linhas/destruidor-1.md"), DEIXA, ""),
        ("Revisor lê a linha do Destruidor", "revisor", "Read", r(".delta-11/quadro/camada-3/linhas/destruidor-1.md"), "não lê", ""),
        ("FRAUDE: FRONT lê a chave pessoal do computador", "front", "Read", {"file_path": str(Path.home() / ".ssh" / "id_rsa")}, "de quem usa o computador", ""),
        ("FRAUDE: Revisor busca nas credenciais pessoais", "revisor", "Grep", {"pattern": "x", "path": str(Path.home() / ".aws")}, "de quem usa o computador", ""),
        ("FRAUDE: FRONT lê o cofre de senhas do dono (secretctl)", "front", "Read", {"file_path": str(Path.home() / ".secretctl" / "vault.db")}, "de quem usa o computador", ""),
        ("FRAUDE: Destruidor lista o cofre de senhas do dono", "destruidor", "Glob", {"pattern": "*", "path": str(Path.home() / ".secretctl")}, "de quem usa o computador", ""),
        ("Revisor lê o contrato da esteira", "revisor", "Read", r(".delta-11/motor/modelos/esteira.md"), "não lê", ""),
        ("VAULT roda as migrações pela caixa", "vault", "Bash", {"command": CAIXA + " supabase db push"}, DEIXA, ""),
        ("FRONT encadeia a caixa a outro comando", "front", "Bash", {"command": "npm ci && " + CAIXA + " npm test"}, "rode a caixa do produto sozinha", ""),
        ("FRONT redireciona a saída da caixa", "front", "Bash", {"command": CAIXA + " npm test > saida.txt"}, "rode a caixa do produto sozinha", ""),
        ("FRONT roda a caixa de uma subpasta", "front", "Bash", {"command": "python3 -I -B ../../.claude/hooks/delta-11/caixa-do-produto.py npm test"}, "rode a caixa do produto sozinha", "src/telas"),
        ("FRONT roda a caixa numa subpasta", "front", "Bash", {"command": CAIXA + " npm test"}, "roda na raiz", "src/telas"),
        ("candidata roda o produto pela caixa da cópia dela", "front", "Bash", {"command": CAIXA + " npm test"}, DEIXA, copia),
        ("FRAUDE: candidata roda uma caixa mudada na cópia dela", "front", "Bash", {"command": CAIXA + " npm test"}, "não é a do motor", ".claude/worktrees/agent-candidata2"),
        ("FRONT lê o programa da caixa", "front", "Bash", {"command": "cat .claude/hooks/delta-11/caixa-do-produto.py"}, DEIXA, ""),
        # A tela do app: ver e usar a janela de um app de Mac, fora da caixa de areia, só por quem constrói e quem confere o app
        ("Revisor vê a janela do app pela tela do app", "revisor", "Bash", {"command": TELA + " ver"}, DEIXA, ""),
        ("Revisor digita no app um texto com tags e >", "revisor", "Bash", {"command": TELA + " digitar '<script> > x'"}, DEIXA, ""),
        ("Destruidor não usa a tela do Mac do dono", "destruidor", "Bash", {"command": TELA + " digitar 'x'"}, "não usa a tela do app", ""),
        ("FRONT não usa a tela: prova pelo código", "front", "Bash", {"command": TELA + ' clicar "Salvar gasto"'}, "não usa a tela do app", ""),
        ("SHIELD não usa a tela", "shield", "Bash", {"command": TELA + ' tecla "cmd+n"'}, "não usa a tela do app", ""),
        ("candidata não usa a tela da cópia dela", "front", "Bash", {"command": TELA + " foto"}, "não usa a tela do app", copia),
        ("Selador usa a tela do app", "selador", "Bash", {"command": TELA + " ver"}, "não usa a tela do app", ""),
        ("SCOUT usa a tela do app", "scout", "Bash", {"command": TELA + " abrir"}, "não usa a tela do app", ""),
        ("Revisor encadeia a tela do app a outro comando", "revisor", "Bash", {"command": TELA + " ver && echo feito"}, "rode a tela do app sozinha", ""),
        ("FRAUDE: Revisor roda a tela do app pela caixa do produto", "revisor", "Bash", {"command": CAIXA + " olhar " + TELA + " ver"}, "rode a tela do app sozinha", ""),
        ("FRAUDE: Revisor digita no app o resultado de um $(...)", "revisor", "Bash", {"command": TELA + ' digitar "$(cat ~/.ssh/id_rsa)"'}, "rode a tela do app sozinha", ""),
        ("FRAUDE: Revisor esconde a tela do app num sh -c", "revisor", "Bash", {"command": "sh -c '" + TELA + " ver'"}, "rode a tela do app sozinha", ""),
        ("Revisor roda a tela do app numa subpasta", "revisor", "Bash", {"command": TELA + " ver"}, "roda na raiz", "src/telas"),
        ("FRAUDE: SCOUT muda a esteira, que é do motor", "scout", "Edit", {"file_path": str(p / "esteira")}, "não escreve em `esteira`", ""),
        ("SCOUT conserta o .gitignore", "scout", "Edit", {"file_path": str(p / ".gitignore")}, DEIXA, ""),
        ("BACK entrega junto com o SHIELD os comandos do produto e o teste plantado", "back", "Bash", {"command": "sh esteira back,shield esteira-comandos.txt testes/pulso.sh"}, DEIXA, ""),
        ("Destruidor confere o código de resposta sem gravar", "destruidor", "Bash", {"command": "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/"}, DEIXA, ""),
        ("Destruidor procura chamadas perigosas no código", "destruidor", "Bash", {"command": "grep -rn \"child_process\\|execSync\\|writeFile\" src/"}, DEIXA, ""),
        ("FRONT junta a esteira a outros comandos na mesma linha", "front", "Bash", {"command": "mkdir -p src && printf 'Olá' > src/a.html && sh esteira front src/a.html"}, "rode a esteira sozinha", ""),
        ("FRONT entrega a candidata escolhida pela esteira", "front", "Bash", {"command": "sh esteira front --copia .claude/worktrees/agent-1 --descartar .claude/worktrees/agent-2"}, DEIXA, ""),
        ("FRONT olha o que mudou", "front", "Bash", {"command": "git status && git diff"}, DEIXA, ""),
        ("Candidata tenta commit na própria cópia (deixa sem commit)", "front", "Bash", {"command": "git add -A && git commit -m candidata"}, "não mexe na história do git", copia),
        ("FRAUDE: FRONT esconde o commit entre aspas", "front", "Bash", {"command": "git \"add\" src/a.js && git \"commit\" -m x -m 'Esteira: entrou'"}, "não mexe na história do git", ""),
        ("FRAUDE: FRONT esconde o commit num sh -c", "front", "Bash", {"command": "sh -c \"git add -A && git commit -m pronto\""}, "não mexe na história do git", ""),
        ("FRAUDE: Revisor lê o quadro com o caminho entre aspas", "revisor", "Bash", {"command": "cat \".delta-11/quadro/camada-3/quadro.md\""}, "não lê pelo terminal", ""),
        ("FRAUDE: Destruidor lê a história com o comando entre aspas", "destruidor", "Bash", {"command": "git \"log\" -p"}, "não lê a história do git", ""),
        ("FRAUDE: Destruidor grava no código dentro de um sh -c", "destruidor", "Bash", {"command": "sh -c \"echo conserto > src/app.js\""}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Destruidor copia com install", "destruidor", "Bash", {"command": "install -m 644 /etc/hosts src/a.js"}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Selador faz commit com o comando entre aspas", "selador", "Bash", {"command": "git \"commit\" -am selo"}, "terminal do selador é vigiado", ""),
        ("FRONT instala dependências", "front", "Bash", {"command": "npm install && pip install requests"}, DEIXA, ""),
        ("FRAUDE: candidata envia a cópia ao GitHub", "front", "Bash", {"command": "git push origin HEAD"}, "não mexe na história do git", copia),
        ("FRAUDE: FRONT edita o programa da esteira", "front", "Edit", {"file_path": str(p / "esteira")}, "não escreve em `esteira`", ""),
        ("FRAUDE: BACK edita a esteira, que é do motor", "back", "Edit", {"file_path": str(p / "esteira")}, "não escreve em `esteira`", ""),
        ("BACK escreve os comandos do produto para a esteira", "back", "Write", w("esteira-comandos.txt"), DEIXA, ""),
        ("FRONT muda os comandos do produto para a esteira", "front", "Edit", {"file_path": str(p / "esteira-comandos.txt")}, "não fica nas pastas do território de front", ""),
        ("Candidata sem endereços na cópia escreve no território de outro", "front", "Write", {"file_path": str(p / ".claude/worktrees/agent-candidata2/banco/x.sql"), "content": "x"}, "não fica nas pastas do território de front", ".claude/worktrees/agent-candidata2"),
        # Terminal vigiado: o que manda texto não é gravar; gravar de outro jeito é
        ("Destruidor manda uma entrada com tags de tela", "destruidor", "Bash", {"command": "curl -s -d 'nome=<script>alert(1)</script>' localhost:3000 | grep -c '<div>'"}, DEIXA, ""),
        ("Destruidor grava a saída de erro num arquivo do produto", "destruidor", "Bash", {"command": "npm test 2> src/saida.txt"}, "terminal do destruidor é vigiado", ""),
        ("Selador grava por um programa de linguagem", "selador", "Bash", {"command": "python3 -c \"open('src/x.js','w').write('x')\""}, "terminal do selador é vigiado", ""),
        ("Selador grava num temporário entre aspas", "selador", "Bash", {"command": "npm test > \"$TMPDIR/saida.txt\""}, DEIXA, ""),
        ("Destruidor cria uma pasta temporária", "destruidor", "Bash", {"command": "mkdir -p \"$TMPDIR/ataque\""}, DEIXA, ""),
        ("Selador lista as cópias e os ramos das candidatas", "selador", "Bash", {"command": "git worktree list && git branch --list && git stash list"}, DEIXA, ""),
        ("Revisor busca em tudo pelo terminal", "revisor", "Bash", {"command": "grep -rn senha ."}, "não lê pelo terminal", ""),
        ("Revisor busca sem dizer a pasta", "revisor", "Bash", {"command": "rg senha"}, "não lê pelo terminal", ""),
        ("Destruidor busca numa pasta do código", "destruidor", "Bash", {"command": "grep -rn senha src/ && find src -name '*.js'"}, DEIXA, ""),
        ("Destruidor roda o produto pelo caminho completo (com 'delta' no meio)", "destruidor", "Bash", {"command": "cd /Users/x/construcao-delta-11/produto && npm run dev"}, DEIXA, ""),
        ("Revisor chama uma rota com 'delta' no nome", "revisor", "Bash", {"command": "curl -s localhost:3000/api/delta"}, DEIXA, ""),
        ("FRAUDE: Destruidor lê a história do git pela ferramenta de ler", "destruidor", "Read", r(".git/logs/HEAD"), "não lê `.git/`", ""),
        ("FRAUDE: Destruidor grava com /bin/cp", "destruidor", "Bash", {"command": "/bin/cp /etc/hosts src/a.js"}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Destruidor baixa direto para o código", "destruidor", "Bash", {"command": "curl -s -o src/a.js https://exemplo.invalid"}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Destruidor desempacota no código", "destruidor", "Bash", {"command": "tar -xzf pacote.tgz"}, "terminal do destruidor é vigiado", ""),
        ("FRAUDE: Selador grava por subprocesso", "selador", "Bash", {"command": "python3 -c \"import subprocess; subprocess.run(['cp','a','b'])\""}, "terminal do selador é vigiado", ""),
        ("Destruidor lê o quadro com curinga", "destruidor", "Bash", {"command": "cat .delta-1?/quadro/*/linhas/*.md"}, "não lê pelo terminal", ""),
        ("Destruidor lê a história do git pelo arquivo", "destruidor", "Bash", {"command": "cat .git/logs/HEAD"}, "não lê pelo terminal", ""),
        ("CRONOS chama candidata com isolamento remoto", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "isolation": "remote"}, "isolamento 'remote'", ""),
        ("ATLAS liga o CRONOS em primeiro plano", "atlas", "Agent", {"subagent_type": "cronos", "prompt": "x"}, "ligado em segundo plano", ""),
        ("ATLAS chama o Destruidor para a Luz", "atlas", "Agent", {"subagent_type": "destruidor", "prompt": "x", "run_in_background": False}, DEIXA, ""),
        ("ATLAS chama um Construtor", "atlas", "Agent", {"subagent_type": "front", "prompt": "x"}, "não chama o front", ""),
        ("CRONOS chama um Construtor", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "run_in_background": False}, DEIXA, ""),
        ("CRONOS chama uma candidata em cópia isolada", "cronos", "Agent", {"subagent_type": "front", "prompt": "x", "isolation": "worktree", "run_in_background": False}, DEIXA, ""),
        ("CRONOS chama o Destruidor em cópia isolada", "cronos", "Agent", {"subagent_type": "destruidor", "prompt": "x", "isolation": "worktree"}, "com isolamento", ""),
        ("CRONOS chama o agente comum", "cronos", "Agent", {"subagent_type": "general-purpose", "prompt": "x"}, "não chama o general-purpose", ""),
        ("CRONOS chama sem dizer o papel", "cronos", "Agent", {"prompt": "x"}, "diz qual papel chama", ""),
        ("Selador chama o leitor do teste", "selador", "Agent", {"subagent_type": "leitor-do-teste", "prompt": "x", "run_in_background": False}, DEIXA, ""),
        ("Selador chama o ativador da v6", "selador", "Agent", {"subagent_type": "delta-11", "prompt": "x"}, "não chama o delta-11", ""),
        ("FRONT chama outro Construtor", "front", "Agent", {"subagent_type": "pixel", "prompt": "x"}, "não chama o pixel", ""),
        # Maiúsculas (o disco do Mac não diferencia), cópias isoladas, caminho exato, registro e arquivos de controle
        ("FRAUDE: ATLAS escreve a configuração com outras maiúsculas", "atlas", "Write", w(".CLAUDE/settings.json"), "não escreve em `.claude/`", ""),
        ("FRAUDE: FRONT lê o cofre com outras maiúsculas", "front", "Read", r(".DELTA-11/COFRE/chave.txt"), "não lê `.delta-11/cofre/`", ""),
        ("FRAUDE: candidata lê o cofre da pasta principal pelo caminho completo", "front", "Read", r(".delta-11/cofre/chave.txt"), "não lê `.delta-11/cofre/`", copia),
        ("FRAUDE: Destruidor lê uma linha guardada na cópia de uma candidata", "destruidor", "Read", r(copia + "/.delta-11/quadro/camada-3/linhas/front-1.md"), "não lê `.delta-11/quadro/<X>/linhas/<nome>-<n>.md`", ""),
        ("Revisor confere um arquivo exato com Glob", "revisor", "Glob", {"pattern": ".delta-11/regras/enderecos.txt", "path": str(p)}, DEIXA, ""),
        ("Revisor procura um brief exato com Glob", "revisor", "Glob", {"pattern": ".delta-11/quadro/camada-3/briefs/front-2.md", "path": str(p)}, "não lê `.delta-11/quadro/<X>/`", ""),
        ("CRONOS reescreve um registro que já existe", "cronos", "Edit", {"file_path": str(p / ".delta-11/registro/existente.md")}, "só se cria arquivo novo", ""),
        ("CRONOS lê o registro", "cronos", "Read", r(".delta-11/registro/existente.md"), "não lê `.delta-11/registro/`", ""),
        ("Documentador lê o registro (registro final)", "documentador", "Read", r(".delta-11/registro/existente.md"), DEIXA, ""),
        ("BACK ajusta o .gitignore", "back", "Edit", {"file_path": str(p / ".gitignore")}, DEIXA, ""),
        ("FRONT mexe no .gitignore", "front", "Edit", {"file_path": str(p / ".gitignore")}, "não escreve em `.gitignore`", ""),
        ("BACK escreve um AGENTS.md na raiz", "back", "Write", w("AGENTS.md"), "não escreve em `AGENTS.md`", ""),
        ("Leitor do teste abre uma pasta de teste antiga", "leitor-do-teste", "Read", r(".delta-11/leitor/camada-0/velho.md"), "só lê dentro de .delta-11/leitor/camada-1/", ""),
        # Terminal vigiado: o que não é gravar não pode ser barrado
        ("Destruidor roda um container descartável", "destruidor", "Bash", {"command": "docker run --rm imagem-de-teste"}, DEIXA, ""),
        ("Selador instala as dependências para rodar os testes", "selador", "Bash", {"command": "npm install && npx playwright install"}, DEIXA, ""),
        ("Destruidor compara números num comando", "destruidor", "Bash", {"command": "node -e \"if (1 > 3) process.exit(1)\""}, DEIXA, ""),
        ("Selador faz commit com opção antes do comando", "selador", "Bash", {"command": "git -C . commit -m x"}, "terminal do selador é vigiado", ""),
        ("Revisor lê a história do git", "revisor", "Bash", {"command": "git log -p"}, "não lê a história do git", ""),
        ("Destruidor lê a diferença do último commit", "destruidor", "Bash", {"command": "git diff HEAD~1"}, "não lê a história do git", ""),
        ("Selador lê a história do git", "selador", "Bash", {"command": "git log --oneline"}, DEIXA, ""),
        # Ver e mexer junto com o dono (o navegador e os programas do computador); aqui a Camada 1 nunca selou: é o Dia 1
        ("ATLAS vê a tela pelo computer use", "atlas", "mcp__computer-use__screenshot", {}, DEIXA, ""),
        ("ATLAS lê a página aberta no navegador do dono", "atlas", "mcp__claude-in-chrome__read_page", {"tabId": 1}, DEIXA, ""),
        ("ATLAS clica no navegador do dono no Dia 1", "atlas", "mcp__claude-in-chrome__computer", {"action": "left_click", "coordinate": [10, 10]}, DEIXA, ""),
        ("ATLAS pede para usar um programa de desenho", "atlas", "mcp__computer-use__request_access", {"apps": ["Figma"]}, DEIXA, ""),
        ("FRAUDE: ATLAS pede para usar o Terminal junto com outro programa", "atlas", "mcp__computer-use__request_access", {"apps": ["Figma", "Terminal"]},
         "terminal e editor de código", ""),
        ("FRAUDE: ATLAS abre o editor de código pelo identificador dele", "atlas", "mcp__computer-use__open_application", {"app": "com.microsoft.VSCode"},
         "terminal e editor de código", ""),
        ("FRAUDE: ATLAS abre o PowerShell", "atlas", "mcp__computer-use__open_application", {"app": "Windows PowerShell"}, "terminal e editor de código", ""),
        ("FRAUDE: FRONT usa o navegador do dono", "front", "mcp__claude-in-chrome__navigate", {"url": "https://exemplo.com"}, "não usa mcp__claude-in-chrome__navigate", ""),
        ("FRAUDE: Destruidor tira foto da tela do dono", "destruidor", "mcp__computer-use__screenshot", {}, "não usa mcp__computer-use__screenshot", ""),
        ("FRAUDE: ATLAS usa uma ferramenta de fora que o Delta-11 não conhece", "atlas", "mcp__cofre__ler_segredo", {"nome": "X"}, "não conhece", ""),
        ("ATLAS pesquisa na internet", "atlas", "WebSearch", {"query": "concorrentes de agenda online"}, DEIXA, ""),
        ("ATLAS monta uma amostra para o dono escolher", "atlas", "Write", w(".delta-11/luz/amostras/cor-da-moldura-a.html"), DEIXA, ""),
        ("FRAUDE: FRONT escreve nas amostras da Luz", "front", "Write", w(".delta-11/luz/amostras/x.html"), "não escreve", ""),
        ("FRAUDE: ATLAS escreve nas referências do dono", "atlas", "Write", w("referencias/x.md"), "não escreve", ""),
        ("PIXEL lê uma referência do dono", "pixel", "Read", r("referencias/print.png"), DEIXA, ""),
        ("Revisor não lê as referências do dono", "revisor", "Read", r("referencias/print.png"), "não lê", ""),
        # Quem age
        ("Papel desconhecido", "general-purpose", "Write", w(".delta-11/registro/x.md"), "papel desconhecido", ""),
        ("Conversa sem papel", "", "Write", w(".delta-11/registro/x.md"), "papel desconhecido", ""),
    ]


def preparar(p: Path) -> None:
    trava = p / ".claude" / "hooks" / "delta-11"
    trava.mkdir(parents=True)
    for gancho in ("trava.py", "registro_de_cronos.py", "caixa-do-produto.py", "situacao.py", "tela-do-app.py", "cronos-vivo.py", "motor.py"):
        shutil.copy2(MOTOR / "ganchos" / gancho, trava / gancho)
    shutil.copytree(MOTOR / "ganchos" / "motores", trava / "motores", ignore=shutil.ignore_patterns("__pycache__"))  # os tradutores
    for copia, mudada in (("agent-candidata1", False), ("agent-candidata2", True)):
        for programa in ("caixa-do-produto.py", "tela-do-app.py"):
            dela = p / ".claude/worktrees" / copia / ".claude/hooks/delta-11" / programa
            dela.parent.mkdir(parents=True, exist_ok=True)
            dela.write_text((MOTOR / "ganchos" / programa).read_text() + ("\nCHAVES_PESSOAIS = []\n" if mudada else ""))
    shutil.copy2(MOTOR / "agentes" / "lugares.json", trava / "lugares.json")
    (p / ".claude" / "settings.json").write_text("{}\n")
    for pasta in ["src/telas", "banco/migracoes", ".delta-11/regras", ".delta-11/registro", ".delta-11/quadro/camada-3/linhas",
                  ".delta-11/quadro/camada-3/briefs", ".delta-11/teste-guardado", ".delta-11/cofre", ".delta-11/leitor/camada-1",
                  ".git", ".claude/worktrees/agent-candidata1/src/telas", ".claude/worktrees/agent-candidata1/.delta-11/regras"]:
        (p / pasta).mkdir(parents=True, exist_ok=True)
    for arquivo in ["src/telas/inicio.js", "src/telas/alvo-do-link.js", "banco/migracoes/1.sql", "package.json", ".git/config", "src/analise.ipynb",
                    ".delta-11/registro/existente.md", ".gitignore", ".claude/worktrees/agent-candidata1/.delta-11/quadro/camada-3/linhas/front-1.md"]:
        (p / arquivo).parent.mkdir(parents=True, exist_ok=True)
        (p / arquivo).write_text("x\n")
    (p / ".gitignore").write_text(".claude/worktrees/\n.delta-11/cofre/\n.delta-11/teste-guardado/\n.delta-11/leitor/\n")
    (p / ".delta-11/quadro/camada-3/abertura.md").write_text("# Abertura\n")
    (p / "esteira").write_text("#!/bin/sh\n")
    (p / ".claude/worktrees/agent-candidata2/banco").mkdir(parents=True)
    (p / ".delta-11/leitor/atual.txt").write_text("camada-1\n")
    for de_fora in ("outro-produto/.delta-11/cofre/x", "esteira.abc/.delta-11/quadro/camada-3/briefs/front-1.md"):  # o .delta-11 de outra pasta
        (p.parent / de_fora).parent.mkdir(parents=True, exist_ok=True)
        (p.parent / de_fora).write_text("x\n")
    for colega, arquivos in (("engine", "servidor/valida.mjs"), ("shield", "testes/pulso.sh")):  # o aceite da entrega conjunta
        (p / f".delta-11/quadro/camada-3/linhas/{colega}-1.md").write_text(f"Situação: encerrado\n- Entrego junto: {arquivos}\n")
    (p / ".delta-11/quadro/camada-3/linhas/pixel-1.md").write_text("Situação: trabalhando\n- Entrego junto: <arquivos>\n")  # o espaço em branco
    (p / ".delta-11/quadro/camada-3/linhas/vault-1.md").write_text("Situação: trabalhando\n- Entrego junto: nenhum (não entrego junto)\n")
    (p / ".delta-11/quadro/camada-2/linhas").mkdir(parents=True)
    (p / ".delta-11/quadro/camada-2/quadro.md").write_text("# Quadro\n\nSituação: selado\n")
    (p / ".delta-11/quadro/camada-2/linhas/form-1.md").write_text("Situação: encerrado\n- Entrego junto: src/form/a.js\n")  # camada selada
    # Outra conversa: uma ainda aberta (conversa mudou agora) conduz o pedido-7; uma fechada há tempo conduzia o camada-8.
    # Uma conversa que ainda roda (um processo falso chamado claude) e uma que já fechou (processo que não existe).
    falso = p.parent / "claude"
    falso.symlink_to("/bin/sleep")  # o Mac não roda cópia de programa do sistema; um atalho com o nome claude roda
    vivo = subprocess.Popen([str(falso), "600"])
    PROCESSOS.append(vivo)
    vivos = p / ".claude/hooks/delta-11/vivos"
    vivos.mkdir()
    for agente, quadro, sessao, pid, trabalhando in (("a1cronos3", "camada-3", "esta-conversa", vivo.pid, True), ("a7outra", "pedido-7", "outra", vivo.pid, True),
                                                      ("a8fechada", "camada-8", "outra", 999999, True), ("a2fim", "pedido-7", "esta-conversa", vivo.pid, False)):
        (vivos / f"{agente}.json").write_text(json.dumps({"agente": agente, "quadro": quadro, "sessao": sessao, "pid": pid, "trabalhando": trabalhando}))
    enderecos = "front src/telas/\nvault banco/\npixel src/telas/estilos/\n"
    (p / ".delta-11/regras/enderecos.txt").write_text(enderecos)
    (p / ".claude/worktrees/agent-candidata1/.delta-11/regras/enderecos.txt").write_text(enderecos)
    os.link(p / "src/telas/alvo-do-link.js", p / ".delta-11/registro/atalho.txt")
    os.symlink(p / "src/telas/inicio.js", p / ".delta-11/registro/simbolico.js")


def rodar(p: Path, papel: str, ferramenta: str, entrada: dict, cwd: str, ambiente: dict | None = None) -> tuple[int, str]:
    pedido = {"tool_name": ferramenta, "tool_input": entrada, "cwd": str(p / cwd) if cwd else str(p), "session_id": "esta-conversa"}
    if papel:
        pedido["agent_type"] = papel
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(p), **(ambiente or {})}
    feito = subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/trava.py"), PROGRAMA], input=json.dumps(pedido),
                           capture_output=True, text=True, env=env)
    return feito.returncode, feito.stderr


def registro_so_do_delta(base: Path) -> bool:
    """Com a esteira interrompida (código no índice), o gancho do registro guarda só .delta-11/ e tira o segredo do git."""
    q = base / "registro"
    (q / "src").mkdir(parents=True)
    (q / ".delta-11" / "cofre").mkdir(parents=True)
    sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    git = lambda *a: subprocess.run(["git", "-C", str(q), *a], capture_output=True, text=True, env=sem_git)
    git("init", "-q"); git("config", "user.email", "teste@exemplo"); git("config", "user.name", "teste")
    (q / "src/app.js").write_text("versao 1\n")
    (q / ".delta-11/cofre/segredo").write_text("x\n")  # entrou no git por engano
    git("add", "-A"); git("commit", "-q", "-m", "um")
    (q / "src/app.js").write_text("versao 2\n")
    git("add", "src/app.js")  # a esteira parou antes de acertar o índice
    (q / ".delta-11/estado.md").write_text("estado\n")
    subprocess.run([sys.executable, "-B", str(MOTOR / "ganchos" / "guardar-registro.py"), PROGRAMA], input="{}", capture_output=True, text=True,
                   env={**sem_git, "CLAUDE_PROJECT_DIR": str(q)})
    arquivos = git("ls-tree", "-r", "--name-only", "HEAD").stdout.split()
    return (git("log", "-1", "--format=%s").stdout.strip() == "registro do Delta-11" and ".delta-11/estado.md" in arquivos
            and ".delta-11/cofre/segredo" not in arquivos and git("show", "HEAD:src/app.js").stdout == "versao 1\n"
            and git("diff", "--cached", "--name-only").stdout.split() == ["src/app.js"] and (q / ".delta-11/cofre/segredo").is_file())


def caixa_com_acento(base: Path) -> bool:
    """Numa pasta com acento, as regras da caixa valem (o caminho vai como é, não como \\u00e7)."""
    q = base / "produção"
    trava = q / ".claude" / "hooks" / "delta-11"
    trava.mkdir(parents=True)
    shutil.copy2(MOTOR / "ganchos" / "caixa-do-produto.py", trava)
    shutil.copy2(MOTOR / "agentes" / "lugares.json", trava)
    (q / ".claude" / "settings.json").write_text("{}\n")
    (q / ".git").mkdir()
    feito = subprocess.run([sys.executable, "-I", "-B", str(trava / "caixa-do-produto.py"), "sh", "-c", "echo x > .git/prova; echo y > .claude/prova"],
                           capture_output=True, text=True, cwd=q)
    return not (q / ".git" / "prova").exists() and not (q / ".claude" / "prova").exists()


def caixa_no_ambiente_do_dono(base: Path) -> bool:
    """Um app de Mac: a caixa grava no ambiente do dono que esteira-comandos.txt declara, e só nele; um lugar fora dos do dono recusa."""
    q = base / "app-de-mac"
    trava = q / ".claude" / "hooks" / "delta-11"
    trava.mkdir(parents=True)
    shutil.copy2(MOTOR / "ganchos" / "caixa-do-produto.py", trava)
    shutil.copy2(MOTOR / "agentes" / "lugares.json", trava)
    (q / ".claude" / "settings.json").write_text("{}\n")
    (q / ".git").mkdir()
    pasta = Path.home() / "Library" / "Logs" / f"delta11-pulso-trava-{os.getpid()}"
    fora = Path.home() / "Library" / "Logs" / f"delta11-pulso-trava-{os.getpid()}-sem-declarar"
    comandos = q / "esteira-comandos.txt"
    caixa = lambda *a: subprocess.run([sys.executable, "-I", "-B", str(trava / "caixa-do-produto.py"), *a], capture_output=True, text=True, cwd=q)
    try:
        comandos.write_text(f"testar: true\ntestes: t/\nambiente: ~/Library/Logs/{pasta.name}\n")
        caixa("sh", "-c", f"mkdir -p '{pasta}' && echo x > '{pasta}/sem-pedir.txt'")
        sem_pedir_barrou = not (pasta / "sem-pedir.txt").exists()  # por padrão, nada grava no ambiente do dono
        caixa("--com-ambiente", "sh", "-c", f"mkdir -p '{pasta}' && echo x > '{pasta}/dado.txt'; mkdir -p '{fora}'")
        gravou, barrou = (pasta / "dado.txt").is_file() and sem_pedir_barrou, not fora.exists()
        caixa("olhar", "--com-ambiente", "sh", "-c", f"echo y > '{pasta}/do-olhar.txt'")
        no_olhar = (pasta / "do-olhar.txt").is_file()
        recusas = []
        for errado in ("~/Applications", "~/Library/Preferences/sub/x.plist", "~/Library/Preferences/x.txt", "~/Documents/x",
                       "~/Library/Logs/../../x", "relativo/x", "~/Library/LaunchAgents", "/Applications/Outro.app"):
            comandos.write_text(f"testar: true\nambiente: {errado}\n")
            feito = caixa("true")
            recusas.append(feito.returncode == 2 and "fora do ambiente do dono" in feito.stderr and "~/Applications/" in feito.stderr)
    finally:
        for criada in (pasta, fora):
            if criada.name.startswith("delta11-pulso-trava-") and criada.is_dir():
                shutil.rmtree(criada)
    # Os lugares aceitos, conferidos numa casa de mentira (nada se cria na pasta pessoal de verdade): no olhar, só os dados do app.
    casa = base / "casa-de-mentira"
    (casa / "Library").mkdir(parents=True)
    comandos.write_text("ambiente: ~/Applications/Gastos.app\nambiente: ~/Library/Application Support/com.exemplo.gastos\n"
                        "ambiente: ~/Library/Preferences/com.exemplo.gastos.plist\nambiente: ~/Library/LaunchAgents/com.exemplo.gastos.plist\n")
    feito = subprocess.run([sys.executable, "-I", "-B", "-c", "import importlib.util, sys; from pathlib import Path; "
                            "s = importlib.util.spec_from_file_location('caixa', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                            "print(len(m.ambiente_do_dono(Path(sys.argv[2]), False)), len(m.ambiente_do_dono(Path(sys.argv[2]), True)))",
                            str(trava / "caixa-do-produto.py"), str(q)], capture_output=True, text=True, env={**os.environ, "HOME": str(casa)})
    return gravou and barrou and no_olhar and all(recusas) and feito.stdout.split() == ["4", "2"] and (casa / "Applications").is_dir()


def caixa_na_copia_da_candidata(q: Path) -> bool:
    """Um produto com git de verdade e duas cópias de candidatas: a caixa da cópia 1 grava só nela."""
    sem_git = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    g = lambda *a, onde=q: subprocess.run(["git", "-C", str(onde), *a], capture_output=True, text=True, env=sem_git)
    trava = q / ".claude" / "hooks" / "delta-11"
    trava.mkdir(parents=True)
    shutil.copy2(MOTOR / "ganchos" / "caixa-do-produto.py", trava)
    shutil.copy2(MOTOR / "agentes" / "lugares.json", trava)
    (q / ".claude" / "settings.json").write_text("{}\n")
    (q / ".gitignore").write_text(".claude/worktrees/\ndist/\n*.local\n.vscode/*\n!.vscode/extensions.json\n")
    (q / ".vscode").mkdir()
    (q / ".vscode" / "extensions.json").write_text("{}\n")
    (q / "src").mkdir()
    (q / "src" / "app.js").write_text("x\n")
    g("init", "-q")
    g("add", "-A")
    g("-c", "user.name=p", "-c", "user.email=p@p", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "base")
    c1, c2 = q / ".claude/worktrees/c1", q / ".claude/worktrees/c2"
    g("worktree", "add", "-q", "--detach", str(c1), "HEAD")
    g("worktree", "add", "-q", "--detach", str(c2), "HEAD")
    subprocess.run([sys.executable, "-I", "-B", str(c1 / ".claude/hooks/delta-11/caixa-do-produto.py"), "sh", "-c",
                    f"echo a > nela.txt; echo b > '{c2}/invade.txt'; echo c > '{q}/principal.txt'; echo d > .claude/x;"
                    " git -c user.name=p -c user.email=p@p commit --allow-empty -qm x"],
                   capture_output=True, text=True, cwd=c1, env=sem_git)
    caixa = lambda *a: subprocess.run([sys.executable, "-I", "-B", str(q / ".claude/hooks/delta-11/caixa-do-produto.py"), *a],
                                      capture_output=True, text=True, cwd=q, env=sem_git)
    caixa("--raiz", ".claude/worktrees/c2", "sh", "-c", "echo m > montado.txt")  # da raiz, roda dentro da cópia
    fora = Path(tempfile.gettempdir()).resolve() / "caixa-olhar-prova"
    caixa("olhar", "sh", "-c", f"echo z > .gitignore; echo n > novo-do-olhar.txt; mv src '{fora}'; mkdir -p dist && echo m > dist/montado.js; echo w > .claude/worktrees/c1/olhar.txt; echo h > .env.local; echo h > .vscode/extensions.json; echo s > .vscode/settings.json")  # olhar: só lê
    dentro = caixa("sh", "-c", "python3 -I -B .claude/hooks/delta-11/caixa-do-produto.py echo dentro-da-caixa")
    return ((c1 / "nela.txt").exists() and not (c2 / "invade.txt").exists() and not (q / "principal.txt").exists()
            and not (c1 / ".claude/x").exists() and g("rev-list", "--count", "--all").stdout.strip() == "1"
            and (c2 / "montado.txt").exists() and (q / ".gitignore").read_text().startswith(".claude/worktrees/\ndist/\n") and not (q / ".env.local").exists()
            and (q / ".vscode" / "extensions.json").read_text() == "{}\n" and (q / ".vscode" / "settings.json").exists()
            and not (q / "novo-do-olhar.txt").exists() and (q / "src" / "app.js").exists() and not fora.exists()
            and (q / "dist" / "montado.js").exists() and not (c1 / "olhar.txt").exists() and "dentro-da-caixa" in dentro.stdout)


def main() -> int:
    falhas, extras = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp).resolve() / "produto"
        p.mkdir()
        preparar(p)
        todos = casos(p)
        for caso in todos:
            nome, papel, ferramenta, entrada, motivo, cwd = caso[:6]
            if len(caso) > 6:  # variação: a mesma pasta sem a Camada 3 aberta (ou com ela selada e reaberta em outra pasta)
                (p / ".delta-11/quadro/camada-3/abertura.md").rename(p / "abertura-guardada.md")
                if caso[6] == "camada-3-reaberta":
                    (p / ".delta-11/quadro/camada-3-r1").mkdir(exist_ok=True)
                    (p / ".delta-11/quadro/camada-3-r1/abertura.md").write_text("# Reabertura\n")
            if ferramenta == "Agent" and entrada.get("subagent_type") == "cronos" and "seguidos" not in nome:
                for pedido_velho in (p / ".claude/hooks/delta-11/vivos").glob("pedido-*.json"):
                    pedido_velho.unlink()  # o tempo passou: o pedido anterior já começou ou caducou
            codigo, saida = rodar(p, papel, ferramenta, entrada, cwd)
            if len(caso) > 6:
                (p / "abertura-guardada.md").rename(p / ".delta-11/quadro/camada-3/abertura.md")
                if caso[6] == "camada-3-reaberta":
                    shutil.rmtree(p / ".delta-11/quadro/camada-3-r1")
            if motivo is DEIXA:
                certo = codigo == 0
            else:
                certo = codigo == 2 and motivo in saida
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else f" (saiu {codigo}: {saida.strip()[:160]})"))
            if not certo:
                falhas.append(nome)
        # Falhas do ambiente: a trava barra em vez de liberar.
        especiais = [
            ("FALHA: pedido que não é JSON", lambda: subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/trava.py"), PROGRAMA],
                input="isto não é json", capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})),
            ("FALHA: sem CLAUDE_PROJECT_DIR", lambda: subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/trava.py"), PROGRAMA],
                input=json.dumps({"tool_name": "Write", "agent_type": "atlas", "tool_input": {"file_path": str(p / ".delta-11/luz.md")}}),
                capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"})),
        ]
        for nome, chamar in especiais:
            feito = chamar()
            certo = feito.returncode == 2
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}")
            if not certo:
                falhas.append(nome)
        # A Camada 1 selou: ver continua liberado; mexer só na hora que o dono libera.
        (p / ".delta-11/estado").mkdir(parents=True, exist_ok=True)
        (p / ".delta-11/estado/camada-1.md").write_text("# Arquivo de estado — camada-1\n")
        clique = {"action": "left_click", "coordinate": [10, 10]}
        for nome, ferramenta, entrada, esperado, liberada in [
                ("Camada 1 selada: ATLAS ainda vê a tela", "mcp__computer-use__screenshot", {}, DEIXA, False),
                ("Camada 1 selada: ATLAS ainda tira foto pelo navegador", "mcp__claude-in-chrome__computer", {"action": "screenshot"}, DEIXA, False),
                ("Camada 1 selada: ATLAS clica no navegador sem hora liberada", "mcp__claude-in-chrome__computer", clique, "a Camada 1 já selou", False),
                ("Camada 1 selada: ATLAS digita num programa sem hora liberada", "mcp__computer-use__type", {"text": "x"}, "a Camada 1 já selou", False),
                ("Camada 1 selada: ATLAS clica no navegador na hora liberada", "mcp__claude-in-chrome__computer", clique, DEIXA, True),
                ("Camada 1 reaberta: ATLAS mexe sem hora liberada", "mcp__claude-in-chrome__navigate", {"url": "https://exemplo.com"}, DEIXA, "reaberta")]:
            liberada_arquivo = p / ".delta-11/tela-liberada.md"
            if liberada is True:
                liberada_arquivo.write_text("até: " + time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 3600)) + "\n")
            if liberada == "reaberta":
                (p / ".delta-11/quadro/camada-1-r1").mkdir(parents=True, exist_ok=True)
                (p / ".delta-11/quadro/camada-1-r1/abertura.md").write_text("# Reabertura da Camada 1\n")
            codigo, saida = rodar(p, "atlas", ferramenta, entrada, "")
            liberada_arquivo.unlink(missing_ok=True)
            shutil.rmtree(p / ".delta-11/quadro/camada-1-r1", ignore_errors=True)
            certo = codigo == 0 if esperado is DEIXA else (codigo == 2 and esperado in saida)
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else f" (saiu {codigo}: {saida.strip()[:160]})"))
            if not certo:
                falhas.append(nome)
            extras += 1
        (p / ".delta-11/estado/camada-1.md").unlink()
        # O dono pausou: nada roda, menos o ATLAS e o CRONOS marcando o quadro.
        (p / ".delta-11/pausa.md").write_text("Situação: pausado\n")
        onde = {"pausa: candidata deixa a linha dela em dia, na cópia": ".claude/worktrees/agent-candidata1"}
        no_quadro = lambda c: {"file_path": str(p / ".delta-11/quadro/camada-3" / c), "content": "x"}
        for nome, papel, ferramenta, entrada, esperado in [
                ("pausa: Selador sela", "selador", "Write", no_quadro("selo.md"), "o dono pausou"),
                ("pausa: ARQUITETO abre uma camada", "arquiteto", "Write", {"file_path": str(p / ".delta-11/quadro/camada-4/abertura.md"), "content": "x"}, "o dono pausou"),
                ("pausa: CRONOS escreve um brief", "cronos", "Write", no_quadro("briefs/front-3.md"), "o dono pausou"),
                ("pausa: FRONT escreve a linha do PIXEL", "front", "Write", no_quadro("linhas/pixel-1.md"), "o dono pausou"),
                ("pausa: FRAUDE: FRONT escreve código passando pelo quadro com ../", "front", "Write", no_quadro("../../../src/telas/inicio.js"), "o dono pausou"),
                ("pausa: candidata deixa a linha dela em dia, na cópia", "front", "Write",
                 {"file_path": str(p / ".claude/worktrees/agent-candidata1/.delta-11/quadro/camada-3/linhas/front-1.md"), "content": "x"}, DEIXA),
                ("pausa: FRONT roda o produto pela caixa", "front", "Bash", {"command": CAIXA + " npm test"}, "o dono pausou"),
                ("pausa: o SCOUT mantém de pé o que está no ar", "scout", "Bash", {"command": "sh esteira scout src/telas/inicio.js"}, DEIXA),
                ("pausa: escrita como não pausado, o FRONT trabalha", "front", "Write", {"file_path": str(p / "src/telas/inicio.js"), "content": "x"}, DEIXA),
                ("pausa: com a linha retomado embaixo da pausado, o FRONT trabalha", "front", "Write", {"file_path": str(p / "src/telas/inicio.js"), "content": "x"}, DEIXA),
                ("pausa: com a palavra retomado no meio da frase", "front", "Write", {"file_path": str(p / "src/telas/inicio.js"), "content": "x"}, "o dono pausou"),
                ("pausa: com a situação escrita de outro jeito", "front", "Write", {"file_path": str(p / "src/telas/inicio.js"), "content": "x"}, "o dono pausou"),
                ("pausa: FRONT escreve no código", "front", "Write", {"file_path": str(p / "src/telas/inicio.js"), "content": "x"}, "o dono pausou"),
                ("pausa: CRONOS chama um Construtor", "cronos", "Agent", {"subagent_type": "front", "prompt": "x"}, "o dono pausou"),
                ("pausa: CRONOS marca o quadro", "cronos", "Write", {"file_path": str(p / ".delta-11/quadro/camada-3/quadro.md"), "content": "x"}, DEIXA),
                ("pausa: ATLAS escreve a pausa", "atlas", "Write", {"file_path": str(p / ".delta-11/pausa.md"), "content": "x"}, DEIXA),
                ("pausa: Selador lê", "selador", "Read", {"file_path": str(p / "src/telas/inicio.js")}, DEIXA),
                ("pausa: FRONT deixa a própria linha em dia", "front", "Write", {"file_path": str(p / ".delta-11/quadro/camada-3/linhas/front-1.md"), "content": "x"}, DEIXA),
                ("pausa: FRAUDE: FRONT escreve código numa pasta com nome de quadro", "front", "Write", {"file_path": str(p / "src/.delta-11/quadro/App.jsx"), "content": "x"}, "o dono pausou")]:
            if "não pausado" in nome:
                (p / ".delta-11/pausa.md").write_text("Situação: não pausado\n")
            if "retomado embaixo" in nome:
                (p / ".delta-11/pausa.md").write_text("Situação: pausado\nSituação: retomado\n")
            if "retomado no meio" in nome:
                (p / ".delta-11/pausa.md").write_text("Situação: pausado pelo dono até ele dizer que pode ser retomado\n")
            if "de outro jeito" in nome:
                (p / ".delta-11/pausa.md").write_text("Situação: projeto pausado pelo dono\n")
            codigo, saida = rodar(p, papel, ferramenta, entrada, onde.get(nome, ""))
            certo = codigo == 0 if esperado is DEIXA else (codigo == 2 and esperado in saida)
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else f" (saiu {codigo}: {saida.strip()[:160]})"))
            if not certo:
                falhas.append(nome)
        (p / ".delta-11/pausa.md").write_text("Situação: retomado\n")
        # O CRONOS que conduz uma reabertura fica conhecido na pasta dela: um segundo CRONOS ali é barrado.
        pedido = {"tool_name": "Write", "agent_type": "cronos", "agent_id": "a1cronos3", "session_id": "esta-conversa", "cwd": str(p),
                  "tool_input": {"file_path": str(p / ".delta-11/quadro/camada-2-r1/quadro.md"), "content": "x"}}
        subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/trava.py"), PROGRAMA], input=json.dumps(pedido), capture_output=True, text=True,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        codigo, saida = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-2-r1/.", "run_in_background": True}, "")
        certo = codigo == 2 and "está trabalhando nesta conversa" in saida
        print(f"  {'ok' if certo else 'ERRADO'} — o CRONOS da camada de cima, conduzindo a reabertura, barra um segundo CRONOS nela")
        if not certo:
            falhas.append("CRONOS na reabertura")
        # O ATLAS para um CRONOS travado (TaskStop): ele deixa de trabalhar, e o substituto nasce.
        (p / ".claude/hooks/delta-11/vivos/a6travado.json").write_text(json.dumps({"agente": "a6travado", "quadro": "camada-6", "sessao": "esta-conversa",
            "pid": PROCESSOS[0].pid, "trabalhando": True, "inicio_da_vez": time.time() - 120}))
        rodar(p, "atlas", "TaskStop", {"task_id": "a6travado"}, "")
        trabalho_6 = p / ".claude/hooks/delta-11/vivos/trabalho/camada-6.json"
        parado_conta = trabalho_6.is_file() and json.loads(trabalho_6.read_text())["segundos"] >= 100
        for pedido_velho in (p / ".claude/hooks/delta-11/vivos").glob("pedido-*.json"):
            pedido_velho.unlink()
        codigo, saida = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-6/.", "run_in_background": True}, "")
        certo = codigo == 0 and parado_conta
        print(f"  {'ok' if certo else 'ERRADO'} — o ATLAS para um CRONOS travado com TaskStop e liga o substituto (a vez do parado conta no trabalho do time)" + ("" if certo else f" ({saida.strip()[:120]}, {parado_conta})"))
        if not certo:
            falhas.append("TaskStop e substituto")
        for pedido_velho in (p / ".claude/hooks/delta-11/vivos").glob("pedido-*.json"):
            pedido_velho.unlink()
        # O relógio diz ao ATLAS, pelo motor, se o CRONOS desta conversa tem sinal (o vigia decide por isso, não pelo quadro).
        shutil.copy2(MOTOR / "ganchos" / "relogio.py", p / ".claude/hooks/delta-11/relogio.py")
        relogio = subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/relogio.py"), PROGRAMA], input=json.dumps({"agent_type": "atlas", "session_id": "esta-conversa"}),
                                 capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        certo = "camada-3 (agentId a1cronos3): trabalhando, com sinal" in relogio.stdout
        print(f"  {'ok' if certo else 'ERRADO'} — o relógio diz ao ATLAS que o CRONOS desta conversa trabalha com sinal" + ("" if certo else f" ({relogio.stdout[:160]})"))
        if not certo:
            falhas.append("relógio do ATLAS")
        registro = vivos_dir = p / ".claude/hooks/delta-11/vivos" / "a1cronos3.json"
        guardado_reg = registro.read_text()
        dado = json.loads(guardado_reg)
        linha = p / ".delta-11/quadro/camada-3/linhas/front-9.md"
        linha.parent.mkdir(parents=True, exist_ok=True)
        linha.write_text("# Linha de front-9\n\nSituação: trabalhando\nAtualizado: 2026-10-17 10:00\n")
        agora = time.time()
        os.utime(linha, (agora - 200 * 60, agora - 200 * 60))

        def perguntar_ao_relogio() -> str:
            return subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/relogio.py"), PROGRAMA], input=json.dumps({"agent_type": "atlas", "session_id": "esta-conversa"}),
                                  capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)}).stdout
        registro.write_text(json.dumps({**dado, "mudou": agora - 300 * 60}))
        resposta_travado = perguntar_ao_relogio()
        travado = ("TRAVADO" in resposta_travado or "com agente parado" in resposta_travado) and "front-9.md" in resposta_travado
        registro.write_text(json.dumps({**dado, "mudou": agora - 100 * 60}))  # o substituto começou depois da linha parada
        de_antes = "com sinal" in perguntar_ao_relogio()
        os.utime(linha, None)
        registro.write_text(json.dumps({**dado, "mudou": agora - 300 * 60}))
        refeita = "com sinal" in perguntar_ao_relogio()
        linha.unlink()
        registro.write_text(guardado_reg)
        certo = travado and de_antes and refeita
        print(f"  {'ok' if certo else 'ERRADO'} — o relógio dá TRAVADO o CRONOS com a linha de um agente parada há mais de travado_max; a linha refeita, ou de antes dele começar, não conta" + ("" if certo else f" ({travado, de_antes, refeita})"))
        if not certo:
            falhas.append("relógio: agente travado")
        # O trabalho do time: a vez de cada CRONOS do quadro (de SubagentStart a SubagentStop) se soma; o relógio o diz ao CRONOS e ao ATLAS.
        trabalho = p / ".claude/hooks/delta-11/vivos/trabalho"
        trabalho.mkdir(parents=True, exist_ok=True)
        (trabalho / "camada-3.json").write_text(json.dumps({"quadro": "camada-3", "segundos": 300}))
        registro.write_text(json.dumps({**dado, "trabalhando": True, "inicio_da_vez": time.time() - 600}))
        relogio_do = lambda papel: subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/relogio.py"), PROGRAMA], capture_output=True, text=True,
                                                  input=json.dumps({"agent_type": papel, "agent_id": "a1cronos3", "session_id": "esta-conversa"}),
                                                  env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)}).stdout
        (trabalho / "camada-1.json").write_text(json.dumps({"quadro": "camada-1", "segundos": 600}))  # um bloco já selado
        ao_cronos, ao_atlas, ao_arquiteto = relogio_do("cronos"), relogio_do("atlas"), relogio_do("arquiteto")
        subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/cronos-vivo.py"), PROGRAMA], capture_output=True, text=True,
                       input=json.dumps({"hook_event_name": "SubagentStop", "agent_id": "a1cronos3", "session_id": "esta-conversa"}),
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        somado = json.loads((trabalho / "camada-3.json").read_text())["segundos"]
        parou = json.loads(registro.read_text()).get("trabalhando") is False
        depois = relogio_do("atlas")
        registro.write_text(guardado_reg)
        shutil.rmtree(trabalho)
        certo = ("Trabalho do time em camada-3: 15 min" in ao_cronos and "Trabalho do time em camada-3: 15 min" in ao_atlas and 895 <= somado <= 960
                 and "Trabalho do time em camada-1: 10 min" in ao_arquiteto and "Trabalho do time em camada-3: 15 min" in ao_arquiteto
                 and parou and "Trabalho do time em camada-3: 15 min" in depois)
        print(f"  {'ok' if certo else 'ERRADO'} — o trabalho do time soma a vez de cada CRONOS do quadro (a que acabou e a em curso), e o relógio o diz ao CRONOS e ao ATLAS; ao ARQUITETO, o de todos os quadros (também o selado)" + ("" if certo else f" ({ao_cronos[-120:]!r}, {ao_atlas[-120:]!r}, {ao_arquiteto[-160:]!r}, {somado}, {parou}, {depois[-120:]!r})"))
        if not certo:
            falhas.append("trabalho do time")
        extras += 1
        # Um CRONOS que espera um lote longo: a conversa dele parada, a dos agentes que ele chamou mudando; continua vivo.
        sessao = Path(tmp).resolve() / "conversas" / "outra-sessao"
        (sessao / "subagents").mkdir(parents=True)
        dele, do_lote = sessao / "subagents" / "agent-a9lote.jsonl", sessao / "subagents" / "agent-b9.jsonl"
        for arquivo in (dele, do_lote, sessao.with_suffix(".jsonl")):
            arquivo.write_text("{}\n")
            os.utime(arquivo, (0, 0))
        os.utime(do_lote, None)
        (p / ".claude/hooks/delta-11/vivos/a9lote.json").write_text(json.dumps({"agente": "a9lote", "quadro": "camada-9", "sessao": "outra",
            "pid": PROCESSOS[0].pid, "trabalhando": True, "conversa_do_agente": str(dele)}))
        pedido_9 = {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-9/.", "run_in_background": True}
        codigo, saida = rodar(p, "atlas", "Agent", pedido_9, "")
        os.utime(do_lote, (0, 0))
        codigo2, _ = rodar(p, "atlas", "Agent", pedido_9, "")
        certo = codigo == 2 and "outra conversa" in saida and codigo2 == 0
        print(f"  {'ok' if certo else 'ERRADO'} — CRONOS esperando um lote longo continua vivo; com a conversa toda parada, deixa de contar")
        if not certo:
            falhas.append("CRONOS esperando o lote")
        # O sono não conta; o CRONOS que espera tem sinal pelo quadro; a esteira rodando é sinal de quem entrega.
        agora = time.time()
        desl = agora - (time.clock_gettime(time.CLOCK_UPTIME_RAW) if hasattr(time, "CLOCK_UPTIME_RAW") else time.monotonic())
        sono = p / ".claude/hooks/delta-11/vivos/sono"
        sono.mkdir(parents=True, exist_ok=True)
        linhas3 = p / ".delta-11/quadro/camada-3/linhas"
        linha9 = linhas3 / "front-9.md"
        linha9.write_text("# Linha de front-9\n\nSituação: trabalhando\n")
        os.utime(linha9, (agora - 200 * 60, agora - 200 * 60))
        registro.write_text(json.dumps({**dado, "mudou": agora - 300 * 60}))
        boot = agora - (time.clock_gettime(time.CLOCK_MONOTONIC_RAW) if hasattr(time, "CLOCK_MONOTONIC_RAW") else time.monotonic())
        antes_do_sono = agora - 195 * 60  # o último sinal antes de dormir; a linha foi escrita 5 min antes; dormiu 190 min
        (sono / "historico.json").write_text(json.dumps([[antes_do_sono, desl - 190 * 60, boot, antes_do_sono - (desl - 190 * 60)],
                                                         [agora, desl, boot, agora - desl]]))
        dormindo = perguntar_ao_relogio()
        (sono / "historico.json").unlink()
        (sono / "avisado").unlink(missing_ok=True)
        acordado = perguntar_ao_relogio()
        rodando = p / ".delta-11/esteira/rodando"
        rodando.mkdir(parents=True, exist_ok=True)
        comeco = subprocess.run(["ps", "-o", "lstart=", "-p", str(PROCESSOS[0].pid)], capture_output=True, text=True).stdout.strip()
        (rodando / f"front-{PROCESSOS[0].pid}").write_text("camada-3\n" + comeco + "\n")
        (rodando / "front-999999").write_text("camada-3\nMon Jan  1 00:00:00 2001\n")  # o de uma esteira morta: não conta e sai
        com_esteira = perguntar_ao_relogio()
        morta_saiu = not (rodando / "front-999999").exists()
        shutil.rmtree(rodando)
        linha9.unlink()
        certo = ("front-9.md" not in dormindo and "O Mac dormiu 190 min" in dormindo and "front-9.md" in acordado
                 and ("TRAVADO" in acordado or "com agente parado" in acordado) and "front-9.md" not in com_esteira and morta_saiu)
        print(f"  {'ok' if certo else 'ERRADO'} — o tempo do Mac dormindo não conta como linha parada (e o ATLAS sabe do sono); a esteira rodando é sinal de quem entrega"
              + ("" if certo else f" ({dormindo[-200:]!r}, {acordado[-160:]!r}, {com_esteira[-160:]!r})"))
        if not certo:
            falhas.append("relógio: sono e esteira")
        extras += 1
        # O caso do Selador: a linha muda depois do último registro do histórico e o Mac dorme 8 h; o sono não conta.
        agora = time.time()
        ultimo_registro = agora - (8 * 3600 + 60 + 12 * 60)
        (sono / "historico.json").write_text(json.dumps([[ultimo_registro, desl - 8 * 3600, boot, ultimo_registro - (desl - 8 * 3600)],
                                                         [agora, desl, boot, agora - desl]]))
        linha9.write_text("# Linha de front-9\n\nSituação: trabalhando\n")
        os.utime(linha9, (ultimo_registro + 30, ultimo_registro + 30))
        registro.write_text(json.dumps({**dado, "mudou": ultimo_registro - 60}))
        depois_do_registro = perguntar_ao_relogio()
        linha9.unlink()
        (sono / "historico.json").unlink()
        registro.write_text(guardado_reg)
        certo = "front-9.md" not in depois_do_registro and "SEM SINAL" not in depois_do_registro
        print(f"  {'ok' if certo else 'ERRADO'} — a linha mudada depois do último registro, e o Mac dormindo 8 h em seguida: o sono não conta" + ("" if certo else f" ({depois_do_registro[-200:]!r})"))
        if not certo:
            falhas.append("relógio: sono depois do último registro")
        extras += 1
        linha_c = linhas3 / "cronos-3.md"
        linha_c.write_text("# Linha de cronos-3\n\nSituação: trabalhando\n")
        os.utime(linha_c, (agora - 200 * 60, agora - 200 * 60))
        com_quadro_vivo = perguntar_ao_relogio()
        parados = [a for a in [p / ".delta-11/quadro/camada-3/quadro.md", *linhas3.glob("*.md")] if a.is_file()]
        for a_parado in parados:
            os.utime(a_parado, (agora - 200 * 60, agora - 200 * 60))
        tudo_parado = perguntar_ao_relogio()
        for a_parado in parados:
            os.utime(a_parado, None)
        linha_c.unlink()
        registro.write_text(guardado_reg)
        certo = "cronos-3.md" not in com_quadro_vivo and "TRAVADO" in tudo_parado and "cronos-3.md" in tudo_parado
        print(f"  {'ok' if certo else 'ERRADO'} — a linha parada do CRONOS que espera os agentes dele não o trava enquanto o quadro se mexe; com tudo parado, trava"
              + ("" if certo else f" ({com_quadro_vivo[-160:]!r}, {tudo_parado[-200:]!r})"))
        if not certo:
            falhas.append("relógio: linha do CRONOS")
        extras += 1
        # Trabalho parado no meio: linhas "trabalhando" num quadro esperando o dono, sem CRONOS vivo.
        meio = p / ".delta-11/quadro/camada-5"
        (meio / "linhas").mkdir(parents=True)
        (meio / "abertura.md").write_text("# Abertura\n")
        (meio / "quadro.md").write_text("# Quadro\n\nSituação: esperando o dono\n")
        (meio / "linhas/back-4.md").write_text("Situação: trabalhando\n")
        os.utime(meio / "linhas/back-4.md", (agora - 60 * 60, agora - 60 * 60))
        ao_atlas = perguntar_ao_relogio()
        na_abertura = subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/situacao.py"), PROGRAMA], input=json.dumps({"source": "startup", "session_id": "nova"}),
                                     capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)}).stdout
        shutil.rmtree(meio)
        certo = "Trabalho parado no meio" in ao_atlas and "camada-5: back-4.md" in ao_atlas and "Trabalho parado no meio em camada-5" in na_abertura
        print(f"  {'ok' if certo else 'ERRADO'} — linhas 'trabalhando' sem CRONOS vivo, num quadro esperando o dono: o relógio e o aviso de abertura dizem ao ATLAS"
              + ("" if certo else f" ({ao_atlas[-200:]!r}, {na_abertura[-300:]!r})"))
        if not certo:
            falhas.append("trabalho parado no meio")
        extras += 1
        # Um ARQUITETO por vez (o registro vem dos ganchos de início e fim).
        arquitetos = p / ".claude/hooks/delta-11/vivos/arquitetos"
        arquitetos.mkdir(parents=True, exist_ok=True)
        (arquitetos / "a1arq.json").write_text(json.dumps({"agente": "a1arq", "sessao": "esta-conversa", "pid": PROCESSOS[0].pid, "inicio": time.time(), "conversa": ""}))
        chamar_arq = {"subagent_type": "arquiteto", "prompt": "x", "run_in_background": False}
        codigo_1, saida_1 = rodar(p, "atlas", "Agent", chamar_arq, "")
        gancho = lambda evento, agente: subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/cronos-vivo.py"), PROGRAMA], capture_output=True, text=True,
                                                       input=json.dumps({"hook_event_name": evento, "agent_id": agente, "agent_type": "arquiteto", "session_id": "esta-conversa"}),
                                                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        gancho("SubagentStop", "a1arq")
        for pedido_velho in arquitetos.glob("pedido-*.json"):  # o pedido do caso fixo "ATLAS chama o ARQUITETO", lá em cima
            pedido_velho.unlink()
        codigo_2, _ = rodar(p, "atlas", "Agent", chamar_arq, "")
        codigo_3, saida_3 = rodar(p, "atlas", "Agent", chamar_arq, "")  # o segundo na mesma mensagem, antes de o primeiro começar
        gancho("SubagentStart", "a2arq")
        nasceu = (arquitetos / "a2arq.json").is_file()
        gancho("SubagentStop", "a2arq")
        certo = (codigo_1 == 2 and "um ARQUITETO trabalha agora" in saida_1 and codigo_2 == 0 and codigo_3 == 2 and "acabou de ser chamado" in saida_3
                 and nasceu and not (arquitetos / "a2arq.json").exists() and not list(arquitetos.glob("pedido-*.json")))
        print(f"  {'ok' if certo else 'ERRADO'} — com um ARQUITETO trabalhando (ou recém-chamado, na mesma mensagem), a trava recusa outro; o gancho de fim o libera" + ("" if certo else f" ({codigo_1}, {saida_1[:120]}, {codigo_2}, {codigo_3}, {nasceu})"))
        if not certo:
            falhas.append("um ARQUITETO por vez")
        extras += 1
        # O Documentador sem terminal: o relógio conta as palavras do que ele escreveu.
        escrito = p / ".delta-11/estado/camada-3.md"
        escrito.parent.mkdir(parents=True, exist_ok=True)
        escrito.write_text("um dois três quatro\n")
        contado = subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/relogio.py"), PROGRAMA], capture_output=True, text=True,
                                 input=json.dumps({"agent_type": "documentador", "tool_name": "Write", "tool_input": {"file_path": str(escrito)}}),
                                 env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)}).stdout
        escrito.unlink()
        certo = "camada-3.md: 4 palavras" in contado and "tokens" in contado
        print(f"  {'ok' if certo else 'ERRADO'} — o relógio diz ao Documentador as palavras e os tokens do arquivo que ele escreveu" + ("" if certo else f" ({contado[-160:]!r})"))
        if not certo:
            falhas.append("contagem do Documentador")
        extras += 1
        # Duas conversas: o CRONOS desta, terminado, ficou com o quadro velho (o de outra conversa conduziu depois).
        vivos = p / ".claude/hooks/delta-11/vivos"
        (vivos / "a5velho.json").write_text(json.dumps({"agente": "a5velho", "quadro": "pedido-5", "sessao": "esta-conversa", "pid": PROCESSOS[0].pid, "trabalhando": False, "mudou": 100}))
        (vivos / "b5outro.json").write_text(json.dumps({"agente": "b5outro", "quadro": "pedido-5", "sessao": "outra", "pid": PROCESSOS[0].pid, "trabalhando": False, "mudou": 200}))
        subprocess.run([sys.executable, str(p / ".claude/hooks/delta-11/situacao.py"), PROGRAMA], input=json.dumps({"source": "compact", "session_id": "esta-conversa"}),
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        codigo, saida = rodar(p, "atlas", "SendMessage", {"to": "a5velho", "message": "o dono respondeu"}, "")
        (vivos / "b5outro.json").write_text(json.dumps({"agente": "b5outro", "quadro": "pedido-5", "sessao": "outra", "pid": PROCESSOS[0].pid, "trabalhando": False, "mudou": 50}))
        codigo2, _ = rodar(p, "atlas", "SendMessage", {"to": "a5velho", "message": "o dono respondeu"}, "")
        certo = codigo == 2 and "quadro velho" in saida and codigo2 == 0
        print(f"  {'ok' if certo else 'ERRADO'} — o ATLAS não acorda um CRONOS com o quadro velho (outra conversa conduziu depois), nem depois do aviso de abertura; acorda o que é o mais novo")
        if not certo:
            falhas.append("CRONOS com o quadro velho")
        # A caixa do produto: o que roda nela não grava em .git/ nem fora da pasta, não lê o cofre nem as chaves pessoais (só no Mac).
        if shutil.which("sandbox-exec"):
            (p / ".delta-11/cofre/chave.txt").write_text("segredo\n")
            fora = Path.home() / "prova-da-caixa-do-produto.txt"
            caixa = subprocess.run([sys.executable, "-I", "-B", str(p / ".claude/hooks/delta-11/caixa-do-produto.py"), "sh", "-c",
                                    f"echo x > '{p}/.git/PROVA'; echo x > '{fora}'; echo x > '{p}/.claude/settings.json'; cat '{p}/.delta-11/cofre/chave.txt';"
                                    f" ls ~/.ssh ~/.claude ~/.secretctl; ls '{p}/.delta-11/cofre' >&2; echo livre > '{p}/src/livre.txt'"], capture_output=True, text=True, cwd=p)
            certo = (not (p / ".git/PROVA").exists() and not fora.exists() and (p / ".claude/settings.json").read_text() == "{}\n"
                     and "segredo" not in caixa.stdout and caixa.stdout.strip() == "" and "chave.txt" in caixa.stderr and (p / "src/livre.txt").exists())
            fora.unlink(missing_ok=True)
            print(f"  {'ok' if certo else 'ERRADO'} — caixa do produto: grava no código; não grava em .git/, .claude/ nem fora da pasta; não lê o conteúdo do cofre (a pasta se lista) nem as chaves pessoais")
            if not certo:
                falhas.append("caixa do produto")
            recusa = subprocess.run([sys.executable, "-I", "-B", str(p / ".claude/hooks/delta-11/caixa-do-produto.py"), "--raiz", str(Path.home()), "true"],
                                    capture_output=True, text=True, cwd=p)
            certo = recusa.returncode == 2 and "--raiz só aceita" in recusa.stderr
            print(f"  {'ok' if certo else 'ERRADO'} — caixa do produto recusa --raiz fora do temporário")
            if not certo:
                falhas.append("caixa do produto --raiz")
            certo = caixa_com_acento(Path(tmp).resolve())
            print(f"  {'ok' if certo else 'ERRADO'} — caixa do produto numa pasta com acento: não grava em .git/ nem em .claude/")
            if not certo:
                falhas.append("caixa com acento")
            certo = caixa_no_ambiente_do_dono(Path(tmp).resolve())
            print(f"  {'ok' if certo else 'ERRADO'} — caixa do produto: grava no ambiente do dono que `ambiente:` declara (no olhar, só nos dados do app), não no que ele não declara; fora dos lugares do dono, recusa ensinando")
            if not certo:
                falhas.append("caixa no ambiente do dono")
            extras += 1
            certo = caixa_na_copia_da_candidata(Path(tmp).resolve() / "com-git")
            print(f"  {'ok' if certo else 'ERRADO'} — caixa do produto: a candidata grava só na cópia dela; da raiz, --raiz roda na cópia; olhar só lê a pasta (nem renomeia) e grava no que o git ignora; dentro dela mesma, roda direto")
            if not certo:
                falhas.append("caixa do produto na cópia da candidata")
        # Um enderecos.txt fora do formato barra quem escreve no código, em vez de desligar os territórios em silêncio.
        guardado = (p / ".delta-11/regras/enderecos.txt").read_text()
        (p / ".delta-11/regras/enderecos.txt").write_text("- front: src/telas/\n")
        codigo, saida = rodar(p, "vault", "Write", {"file_path": str(p / "src/telas/x.js"), "content": "x"}, "")
        (p / ".delta-11/regras/enderecos.txt").write_text("front src/telas/ src/componentes/ index.html\nvault banco/\n")
        codigo2, _ = rodar(p, "front", "Write", {"file_path": str(p / "src/componentes/b.js"), "content": "x"}, "")
        codigo3, _ = rodar(p, "front", "Write", {"file_path": str(p / "index.html"), "content": "x"}, "")  # um arquivo da raiz no território
        codigo2 = codigo2 or codigo3
        (p / ".delta-11/regras/enderecos.txt").write_text(guardado)
        certo = codigo == 2 and "fora do formato" in saida and codigo2 == 0
        print(f"  {'ok' if certo else 'ERRADO'} — enderecos.txt fora do formato barra; um território com duas pastas e um arquivo da raiz numa linha vale")
        if not certo:
            falhas.append("enderecos.txt fora do formato")
        # Sem enderecos.txt (o caminho pequeno), o Construtor único escreve todo o código: .gitignore, os comandos e os testes.
        guardado = (p / ".delta-11/regras/enderecos.txt").read_text()
        (p / ".delta-11/regras/enderecos.txt").unlink()
        for nome, papel, caminho, esperado in [
                ("sem enderecos.txt, o Construtor único (FRONT) escreve o .gitignore", "front", ".gitignore", DEIXA),
                ("sem enderecos.txt, o Construtor único (VAULT) escreve esteira-comandos.txt", "vault", "esteira-comandos.txt", DEIXA),
                ("sem enderecos.txt, o Construtor único (FORM) escreve um teste e o código de outro território", "form", "testes/fluxo.test.js", DEIXA),
                ("sem enderecos.txt, o Revisor continua sem escrever o .gitignore", "revisor", ".gitignore", "não escreve em `.gitignore`"),
                ("sem enderecos.txt, o Construtor único continua sem escrever o .env", "front", ".env", "não escreve em `.env`")]:
            codigo, saida = rodar(p, papel, "Write", {"file_path": str(p / caminho), "content": "x"}, "")
            certo = codigo == 0 if esperado is DEIXA else (codigo == 2 and esperado in saida)
            print(f"  {'ok' if certo else 'ERRADO'} — {nome}" + ("" if certo else f" (saiu {codigo}: {saida.strip()[:160]})"))
            if not certo:
                falhas.append(nome)
            extras += 1
        (p / ".delta-11/regras/enderecos.txt").write_text(guardado)
        # Na medição da Camada 7, o pedido do dono espera o fim dela.
        (p / ".delta-11/quadro/camada-3/quadro.md").write_text("# Quadro\n\nSituação: selado\n")
        (p / ".delta-11/quadro/camada-7").mkdir(parents=True)
        (p / ".delta-11/quadro/camada-7/abertura.md").write_text("# Abertura\n\nBloco: Pronto (Camadas 4 a 7)\n")  # o último bloco mora na camada-7
        (p / ".delta-11/quadro/camada-7/quadro.md").write_text("# Quadro\n\nSituação: esperando o tempo até 2099-10-31 09:13\n")
        vivos = p / ".claude/hooks/delta-11/vivos"

        def limpar_pedidos() -> None:
            for pedido_velho in vivos.glob("pedido-*.json"):
                pedido_velho.unlink()
        limpar_pedidos()
        codigo, saida = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/pedido-40/.", "run_in_background": True}, "")
        # O pedido pelo caminho das rotas (o CRONOS da camada aberta, ou mensagem ao que terminou) também espera.
        limpar_pedidos()
        pela_rota, _ = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-7/: leia a abertura. Pedido do dono: trocar o texto do botão.", "run_in_background": True}, "")
        (vivos / "a7medindo.json").write_text(json.dumps({"agente": "a7medindo", "quadro": "camada-7", "sessao": "esta-conversa", "pid": PROCESSOS[0].pid, "trabalhando": False, "mudou": time.time()}))
        por_mensagem, _ = rodar(p, "atlas", "SendMessage", {"to": "a7medindo", "message": "Pedido do dono: trocar o texto do botão."}, "")
        limpar_pedidos()
        reabriu, _ = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-7/: leia a abertura. O ARQUITETO reabriu .delta-11/quadro/camada-5/.", "run_in_background": True}, "")
        (p / ".delta-11/quadro/camada-7/quadro.md").write_text("# Quadro\n\nSituação: esperando o tempo até 2020-01-01 00:00\n")
        limpar_pedidos()
        passou, _ = rodar(p, "atlas", "Agent", {"subagent_type": "cronos", "prompt": "Conduza .delta-11/quadro/camada-7/: leia a abertura. O tempo que a camada esperava passou.", "run_in_background": True}, "")
        limpar_pedidos()
        (vivos / "a7medindo.json").unlink()
        certo = (pela_rota, por_mensagem, reabriu, passou) == (2, 2, 0, 0)
        print(f"  {'ok' if certo else 'ERRADO'} — na medição, o CRONOS da Camada 7 não trabalha (nem pela camada aberta, nem por mensagem), salvo numa reabertura; passada a hora, o vigia o chama" + ("" if certo else f" ({(pela_rota, por_mensagem, reabriu, passou)})"))
        if not certo:
            falhas.append("medição por todos os caminhos")
        shutil.rmtree(p / ".delta-11/quadro/camada-7")
        (p / ".delta-11/quadro/camada-3/quadro.md").unlink()
        certo = codigo == 2 and "espera o fim da medição" in saida
        print(f"  {'ok' if certo else 'ERRADO'} — na medição da Camada 7 (o bloco Pronto, na pasta camada-7), o pedido do dono espera o fim dela" + ("" if certo else f" ({saida.strip()[:120]})"))
        if not certo:
            falhas.append("pedido na medição da Camada 7")
        certo = registro_so_do_delta(Path(tmp).resolve())
        print(f"  {'ok' if certo else 'ERRADO'} — o registro guarda só .delta-11/ (tira o segredo do git) e não leva nem desfaz o código parado no índice")
        if not certo:
            falhas.append("registro só do .delta-11")
        # O .gitignore perdeu as linhas do Delta-11: a busca na raiz passaria a entrar no teste guardado.
        (p / ".gitignore").write_text("node_modules/\n")
        codigo, saida = rodar(p, "cronos", "Grep", {"pattern": "x", "path": str(p)}, "")
        certo = codigo == 2 and "não busca em na raiz" in saida
        print(f"  {'ok' if certo else 'ERRADO'} — FRAUDE: .gitignore sem as linhas do Delta-11 barra a busca na raiz")
        if not certo:
            falhas.append(".gitignore adulterado")
        (p / ".delta-11/leitor/atual.txt").unlink()
        codigo, saida = rodar(p, "leitor-do-teste", "Read", {"file_path": str(p / ".delta-11/leitor/camada-1/luz-compacta.md")}, "")
        certo = codigo == 2 and "não diz qual é" in saida
        print(f"  {'ok' if certo else 'ERRADO'} — leitor do teste sem a pasta em curso não lê nada")
        if not certo:
            falhas.append("leitor sem pasta em curso")
        (p / ".claude/hooks/delta-11/lugares.json").write_text("{quebrado")
        codigo, _ = rodar(p, "atlas", "Write", {"file_path": str(p / ".delta-11/luz.md")}, "")
        certo = codigo == 2
        print(f"  {'ok' if certo else 'ERRADO'} — FALHA: mapa da trava corrompido")
        if not certo:
            falhas.append("mapa corrompido")
        total = len(todos) + len(especiais) + 12 + extras
    for processo in PROCESSOS:
        processo.kill()
    if falhas:
        print(f"PULSO DA TRAVA FALHOU — {len(falhas)} de {total} casos: " + "; ".join(falhas))
        return 1
    print(f"PULSO DA TRAVA OK — {total} casos: as fraudes e os descuidos foram barrados, e o trabalho certo passou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
