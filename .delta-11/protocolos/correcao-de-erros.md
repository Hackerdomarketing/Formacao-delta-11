# PROTOCOLO DE CORREÇÃO DE ERROS — FORMAÇÃO Δ-11

## FLUXO

```
Erro detectado (SHIELD, comandante, ou qualquer agente)
    ↓
Comandante cola o prompt de ativação do SCOUT (gerado pelo agente que detectou o erro)
    ↓
SCOUT lê: project-core.md + estados dos agentes envolvidos
    ↓
SCOUT gera duas análises: conservadora e abrangente
    ↓
SCOUT executa a correção mais adequada
    ↓
SHIELD testa a correção
    ↓
Passou? → Concluído
Falhou? → Segunda tentativa (máximo 3)
    ↓
3 falhas? → Comandante reinicia janela do SCOUT
    ↓
Mais 3 falhas (6 total)? → Escalar para ATLAS
```

## CATEGORIAS DE ALTERAÇÃO

| Categoria | O que é | Quem aprova |
|-----------|---------|-------------|
| A — Apenas visual | Muda interface sem afetar dados | FRONT autoriza |
| B — Envolve dados | Muda formato de dados entre interface e servidor | ATLAS atualiza contrato |
| C — Estrutural | Muda banco, autenticação ou módulos | ATLAS obrigatoriamente |
