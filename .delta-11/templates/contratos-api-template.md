# CONTRATOS DE API — [NOME DO PROJETO]

> **Template v6.3 (2026-10-14) — Fatia de domínio "contratos".**
> Salvo em `.delta-11/memoria/project-core/contratos.md` (fatia do project-core lida por ENGINE, BACK, FRONT e
> FORM — D6). Gerado pelo ATLAS na Fase 2. É a verdade do CONTRATO — o que a API DEVE fazer (D24).
> O sub-agente `contract-tester` converte cada rota em testes executáveis e os RODA — mantenha o formato EXATO
> (ROTA/ENTRADA/SAÍDA) para ele reconhecer.
> Somente o ATLAS edita (D7). Quando o ATLAS edita, o vigia `regenerar-contratos.py` grava o aviso
> `ativacoes/contratos-desatualizados.txt`; o CRONOS dispara o contract-tester UMA vez quando o ATLAS termina
> todas as edições (D31).
> Nomes de rota e de campo em inglês, sem abreviação (D20): `/api/users`, `createdAt`, `perPage`.

## Convenções Globais

| Convenção | Regra |
|-----------|-------|
| Autenticação | [mecanismo — ex: cookie httpOnly via Supabase Auth server-side. Rotas `authenticated`/`admin` retornam 401 sem cookie válido] |
| Rate limit | [por perfil — ex: 60 req/min público, 120 autenticado, 300 admin] |
| Paginação | [params + limites — ex: `page` (min 1, max 1000), `perPage` (min 1, max 100, padrão 20)] |
| Erros genéricos | `400` validação (inclui campo faltando) · `401` não autenticado · `403` sem permissão · `404` não encontrado · `409` conflito · `429` rate limit · `500` interno |
| Formato do erro (D13) | Único para TODA rota: `{ "error": { "code": "VALIDATION_ERROR", "message": "texto para humano", "details": [...] } }`. `code` em MAIÚSCULAS_COM_SUBLINHADO (`VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `RATE_LIMITED`, `INTERNAL_ERROR`); `details` só em erro de validação (lista de `{ "field": "...", "message": "..." }`). Nunca devolver stack trace |
| Tempos-limite (D19) | banco 5 s · API externa 10 s · chamada interna 3 s · 3 novas tentativas com espera crescente · circuit breaker abre após 5 falhas e fecha após 60 s |
| Strings | Toda string tem `.trim()` antes de validar. Nenhuma aceita apenas espaços. TODA string tem `.max()`. |
| URLs | Apenas `http://` e `https://`. Rejeitar `javascript:`, `data:`, `vbscript:`, `file:`, `ftp:`. |
| Dinheiro | Centavos (inteiro). Rejeitar negativos exceto contexto de reembolso explícito. |
| IDs | [formato + validação — ex: UUID v4 com regex] |

---

## [N]. [GRUPO DE ROTAS — ex: AUTH]

```
ROTA: [MÉTODO] [/api/resource]
DESCRIÇÃO: [o que esta rota faz — 1 frase]
AUTENTICAÇÃO: [public / authenticated / admin]

ENTRADA:
{
  fieldName: tipo (required/optional) — descrição
  VALIDAÇÃO: [OBRIGATÓRIO para CADA campo: min, max, regex, transformações (.trim(), .toLowerCase()), protocolos aceitos]
}

SAÍDA SUCESSO ([código]):
{
  fieldName: tipo — descrição
}

SAÍDA ERRO (400 — validação ou campo faltando):
{ "error": { "code": "VALIDATION_ERROR", "message": "[mensagem exata]", "details": [{ "field": "[fieldName]", "message": "[...]" }] } }

SAÍDA ERRO ([401/403/404/409] — erro de domínio):
{ "error": { "code": "[UNAUTHORIZED|FORBIDDEN|NOT_FOUND|CONFLICT]", "message": "[mensagem exata]" } } — [quando acontece]

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
