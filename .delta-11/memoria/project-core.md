# MEMÓRIA CENTRAL DO PROJETO — FORMAÇÃO Δ-11

> TODOS os agentes leem este documento antes de iniciar qualquer tarefa.
> Somente o ATLAS cria e atualiza este documento.
> Este documento é a VERDADE ABSOLUTA sobre o projeto.

---

## PROJETO

**Nome:** [preenchido pelo ATLAS]
**Descrição:** [o que o sistema faz, em 2-3 frases]
**Usuários-alvo:** [para quem é]
**Problema que resolve:** [qual dor resolve]

---

## VISÃO DO PRODUTO (preenchido pelo ATLAS na Fase 0)

**Avatar (usuário final):**
[Quem é essa pessoa, o que ela está passando, o que já tentou, o que a frustra nas soluções atuais]

**Diferencial competitivo:**
[O que torna este produto diferente e superior ao que existe no mercado. O que faria o usuário abandonar o que usa hoje.]

**Telas e experiências:**
[Para cada tela do projeto:]
```
TELA: [nome]
EXPERIÊNCIA: [o que o usuário vê, faz, e sente]
PROMPT DE DESIGN: [prompt aprovado para geração visual]
REFERÊNCIAS: [links ou descrições de inspiração]
```

## CLASSIFICAÇÃO

**Complexidade:** [BAIXA / MÉDIA / ALTA]
**Pontuação detalhada:**
- Telas e rotas: [X] pontos — [justificativa]
- Integrações externas: [X] pontos — [justificativa]
- Modelo de dados: [X] pontos — [justificativa]
- Tempo real: [X] pontos — [justificativa]
- Segurança: [X] pontos — [justificativa]
- **Total: [X] pontos**

**Agentes ativados:** [lista]

## STACK TECNOLÓGICA

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Interface de Usuário | | |
| Estilização | | |
| Servidor | | |
| Banco de Dados | | |
| Autenticação | | |
| Hospedagem | | |

## ARQUITETURA

[Diagrama de módulos e suas conexões — preenchido pelo ATLAS]

---

## DECISÕES TÉCNICAS CRÍTICAS (preenchido pelo ATLAS na Fase 2)

**Autenticação:**
- Login e registro são feitos pelo: [navegador (código do lado do cliente) / servidor (rotas de interface de programação de aplicações)]
- Gestão de cookies de sessão: [quem gerencia e como]
- Confirmação de email: [habilitada/desabilitada, página de destino do link]
- Fallback se perfil ainda não existe no primeiro login: [como tratar]

**Serviços externos:**
- Padrão de inicialização: [sob demanda dentro de funções, NUNCA no nível do módulo]
- Comportamento com variáveis de ambiente ausentes: [como tratar]
- Fluxo completo de webhooks: [descrição de cada etapa e tratamento de falha]

**Framework:**
- Rotas do servidor e cookies: [repassam automaticamente ou precisam de configuração]
- Renderização: [quais páginas no servidor, quais no navegador]
- Middleware: [o que protege, e quais defesas existem se ele falhar]

**Armadilhas conhecidas das tecnologias escolhidas:**
1. [Tecnologia]: [armadilha e como evitar]
2. [Tecnologia]: [armadilha e como evitar]
3. [Tecnologia]: [armadilha e como evitar]

---

## PADRÕES DE IMPLEMENTAÇÃO (preenchido pelo ATLAS na Fase 2, obrigatório para TODOS os agentes)

- Serviços externos: inicialização sob demanda, nunca no nível do módulo
- Defesa em profundidade: layouts protegidos devem verificar autenticação independente do middleware
- Tratamento de erros: toda chamada ao banco deve verificar o campo de erro antes de usar os dados
- Tratamento de erros: toda chamada de interface de programação de aplicações no frontend deve ter catch com feedback visível ao usuário (nunca catch vazio)
- Validação: toda string deve ter .max() definido
- Validação: toda URL deve rejeitar protocolos perigosos (javascript:, data:, file:, ftp:)
- Componentes: todo componente que recebe dados do servidor deve tratar null e undefined
- Atomicidade: operações que envolvem mais de uma escrita no banco devem ser atômicas
- [Adicionar regras específicas do projeto aqui]

---

## IDENTIDADE VISUAL

**Tom visual:** [minimalista refinado / futurista ousado / editorial sofisticado / etc. — preenchido pelo ATLAS]

**Paleta de cores:**
```css
--cor-dominante: ;
--cor-acento: ;
--cor-fundo: ;
--cor-fundo-card: ;
--cor-texto-principal: ;
--cor-texto-secundario: ;
--cor-borda: ;
--cor-sucesso: ;
--cor-erro: ;
--cor-aviso: ;
```

**Tipografia:**
- Fonte de títulos: [nome — importar do Google Fonts]
- Fonte de corpo: [nome — importar do Google Fonts]
- Fonte de código (se aplicável): [nome]

**Estilo de componentes:**
- Bordas: [arredondadas / retas / mistas]
- Sombras: [suaves / dramáticas / nenhuma]
- Espaçamento: [generoso / compacto]
- Animações: [tipo de revelação, transições, micro-interações]

## CONTRATOS DE INTERFACE DE PROGRAMAÇÃO DE APLICAÇÕES

[Cada rota no formato padrão — preenchido pelo ATLAS]

<!--
ROTA: [MÉTODO] [/caminho]
DESCRIÇÃO: [o que faz]
AUTENTICAÇÃO: [público / requer token / apenas administrador]

ENTRADA:
{
  campo: tipo (obrigatório/opcional) — descrição
}

SAÍDA SUCESSO (código [número]):
{
  campo: tipo — descrição
}

SAÍDA ERRO (código [número]):
{
  error: texto — quando acontece
}
-->

## ESQUEMA DO BANCO DE DADOS

[Cada tabela com colunas, tipos, relacionamentos — preenchido pelo ATLAS]

<!--
TABELA: [nome]
| Coluna | Tipo | Restrições | Descrição |
|--------|------|-----------|-----------|
-->

## REGRAS DE NEGÓCIO

[Regras fundamentais que nunca podem ser violadas — preenchido pelo ATLAS]

## DECISÕES ARQUITETURAIS

| Data | Decisão | Justificativa | Impacto |
|------|---------|---------------|---------|
