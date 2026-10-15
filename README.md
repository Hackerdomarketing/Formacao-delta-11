# FORMAÇÃO Δ-11 (v6.3)

Sistema de desenvolvimento de software por inteligência artificial, que roda dentro do Claude Code.

**10 agentes especializados + 1 comandante humano.** Você digita um comando (`d11`) e descreve o que quer construir.
O ATLAS conversa com você e desenha o sistema; depois o CRONOS, o gerente do time, chama os outros agentes sozinho,
vários ao mesmo tempo, cada um na sua cópia isolada do projeto. Você acompanha tudo por um painel que abre sozinho
no navegador e só é chamado para decisões de negócio, contas e pagamentos, ou antes de publicar algo.

| Agente | Papel |
|---|---|
| ATLAS | Arquiteto |
| CRONOS | Gerente e orquestrador |
| VAULT · BACK · ENGINE | Banco de dados · Servidor · Regras e integrações |
| FRONT · PIXEL · FORM | Telas · Visual · Formulários |
| SHIELD · SCOUT | Qualidade e segurança · Diagnóstico e correção |

---

## Requisitos

- **Claude Code**
- **git**
- **python3** (vigias automáticos e monitor)
- **node** (vigias em JavaScript e o próprio projeto)
- **jq** — opcional; só o `sincronizar.sh` precisa dele
- **Sistema:** macOS (completo); Linux; Windows pelo Git Bash ou WSL. O monitor automático a cada 5 minutos é só do
  macOS.

## Instalação (uma vez)

```bash
cd ~/Documents/VSCODE/Formacao-delta-11     # a pasta onde está a Formação Δ-11
bash instalar.sh
```

O instalador confere os requisitos, protege senhas e chaves no `.gitignore`, anota a pasta como fonte oficial, liga
o monitor (macOS, com a sua confirmação) e, se você quiser, guarda uma cópia privada no GitHub.

## Primeiro uso

```bash
bash ~/Documents/VSCODE/Formacao-delta-11/novo-projeto.sh ~/projetos/meu-app
```

Abra a pasta `~/projetos/meu-app` no Claude Code e digite:

```
d11

Quero construir [descreva seu projeto]
```

O painel (`.delta-11/painel.html`) abre sozinho e o ATLAS começa a conversa. O modo padrão é `automatico`: as fases
avançam sozinhas quando as revisões ficam verdes. Para aprovar cada fase, digite `modo manual`.

## Atualizar os projetos

```bash
cd ~/Documents/VSCODE/Formacao-delta-11
git pull
bash sincronizar.sh --dry-run    # mostra o que mudaria, sem gravar
bash sincronizar.sh              # leva os arquivos de sistema a todos os projetos
```

O `sincronizar.sh` nunca mexe nos dados dos projetos (quadro de tarefas, memória, planos, modo de trabalho).

## Testes do sistema

```bash
HOME="$(mktemp -d)" bash .delta-11/tests/rodar-todos.sh
```

## Documentação

- **[GUIA-DO-COMANDANTE.md](GUIA-DO-COMANDANTE.md)** — manual de uso em linguagem simples (comece por aqui)
- **[.delta-11/CHANGELOG.md](.delta-11/CHANGELOG.md)** — história das versões e decisões D1–D39 da v6.3
- **[CLAUDE.md](CLAUDE.md)** — manual completo que os agentes leem automaticamente

## Estrutura

```
CLAUDE.md                ← manual dos agentes
instalar.sh              ← instalação (uma vez)
novo-projeto.sh          ← cria um projeto novo
sincronizar.sh           ← leva atualizações a todos os projetos
.delta-11/
├── operativos/          ← identidade dos 10 agentes
├── protocolos/          ← regras e procedimentos (13 fases)
├── sub-agentes/         ← ajudantes chamados pelo CRONOS e pelo SHIELD
├── hooks/               ← os 36 vigias automáticos
├── conhecimento/        ← bases de conhecimento por papel
├── templates/           ← modelos de documentos
├── tests/               ← testes do próprio sistema
├── memoria/             ← memória do projeto (por projeto)
├── kanban.md            ← quadro de tarefas (só o CRONOS escreve)
└── painel.html          ← painel visual do comandante
```
