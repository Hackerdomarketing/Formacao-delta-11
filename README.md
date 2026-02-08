# FORMAÇÃO Δ-11

Sistema operacional de desenvolvimento de software por inteligência artificial.

10 agentes especializados + 1 comandante humano trabalhando em paralelo no Claude Code.

---

## Início Rápido

```bash
# Instalação (uma vez)
chmod +x instalar.sh
./instalar.sh

# Para cada novo projeto
./novo-projeto.sh ~/projetos/meu-app
```

Depois, no VS Code com Claude Code:

```
d11

Quero construir [descreva seu projeto]
```

O sistema planeja, classifica, e te entrega os prompts prontos para cada janela.

---

## Documentação

- **[GUIA-DO-COMANDANTE.md](GUIA-DO-COMANDANTE.md)** — Manual completo de uso
- **[CLAUDE.md](CLAUDE.md)** — Instruções que o Claude Code lê automaticamente

---

## Estrutura

```
.delta-11/
├── operativos/          ← Identidade dos 10 agentes
├── memoria/             ← Memória do projeto e estados individuais
├── protocolos/          ← Regras e procedimentos
├── templates/           ← Modelos em branco
├── kanban.md            ← Quadro de tarefas (markdown)
├── kanban-data.js       ← Dados do quadro (alimenta o painel)
└── painel.html          ← Painel visual de acompanhamento
```
