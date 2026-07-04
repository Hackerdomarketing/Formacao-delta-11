# CONTRATOS DE API — [NOME DO PROJETO]

> **Template v5.2 — Fatia de domínio "contratos" (v4.0.1).**
> Documento complementar ao project-core.md. Gerado por ATLAS na Fase 2. Salvo em
> `.delta-11/memoria/contratos-api.md` (ou `.delta-11/memoria/project-core/contratos.md`).
> VERDADE ABSOLUTA — todos os agentes de código seguem estas definições.
> O sub-agente `contract-tester` converte cada rota em testes executáveis — mantenha o formato EXATO
> (ROTA/ENTRADA/SAÍDA) para o parser reconhecer.
> Somente o ATLAS edita. Toda edição dispara regeneração automática de testes (hook PostToolUse).

## Convenções Globais

| Convenção | Regra |
|-----------|-------|
| Autenticação | [mecanismo — ex: cookie httpOnly via Supabase Auth server-side. Rotas `authenticated`/`admin` retornam 401 sem cookie válido] |
| Rate limit | [por perfil — ex: 60 req/min público, 120 autenticado, 300 admin] |
| Paginação | [params + limites — ex: `pagina` (min 1, max 1000), `por_pagina` (min 1, max 100, padrão 20)] |
| Erros genéricos | `400` validação · `401` não autenticado · `403` sem permissão · `404` não encontrado · `429` rate limit · `500` interno |
| Strings | Toda string tem `.trim()` antes de validar. Nenhuma aceita apenas espaços. TODA string tem `.max()`. |
| URLs | Apenas `http://` e `https://`. Rejeitar `javascript:`, `data:`, `vbscript:`, `file:`, `ftp:`. |
| Dinheiro | Centavos (inteiro). Rejeitar negativos exceto contexto de reembolso explícito. |
| IDs | [formato + validação — ex: UUID v4 com regex] |

---

## [N]. [GRUPO DE ROTAS — ex: AUTH]

```
ROTA: [MÉTODO] [/caminho]
DESCRIÇÃO: [o que esta rota faz — 1 frase]
AUTENTICAÇÃO: [public / authenticated / admin]

ENTRADA:
{
  campo: tipo (required/optional) — descrição
  VALIDAÇÃO: [OBRIGATÓRIO para CADA campo: min, max, regex, transformações (.trim(), .toLowerCase()), protocolos aceitos]
}

SAÍDA SUCESSO ([código]):
{
  campo: tipo — descrição
}

SAÍDA ERRO ([código]):
{ error: "[mensagem exata]" — [quando acontece] }

FLUXO: [se parte de fluxo multi-etapas: TODAS as rotas e páginas na ordem, incluindo e-mails e redirects]
```

[... repetir por rota ...]

---

## Resumo de Rotas

| Grupo | Rotas | Total |
|---|---|---|
| [Auth] | [lista curta] | [N] |
| **TOTAL** | | **[N]** |

> Ao adicionar/remover rota: atualizar esta tabela NO MESMO commit. A contagem oficial vive aqui.

## Exceções às convenções

[Toda exceção ganha nota explícita — ex: "GET /auth/callback foge da convenção Base URL /api porque
o fluxo PKCE do Supabase exige path fixo. Exceção pontual — convenção continua válida para as demais rotas."]
