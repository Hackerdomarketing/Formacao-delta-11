# Base de Conhecimento: Debugging e Prevencao — SCOUT

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Sua correção não pode violar os limites · se o arquivo já viola e sua correção o toca, refatore o trecho tocado.


Referencia pratica para diagnostico sistematico de bugs e varredura preventiva.
Foco: Next.js + Supabase. Do sintoma a causa raiz.

---

## 1. Metodologia de Diagnostico

### Regra fundamental

NUNCA trate o sintoma. Sempre busque a causa raiz.

```
Sintoma: "Pagina mostra dados vazios"
Tratamento de sintoma: Adicionar fallback "nenhum dado encontrado"
Causa raiz: RLS bloqueando query porque policy nao inclui o role do usuario
```

### Processo em 5 passos

1. **Reproduzir** — Consiga reproduzir o erro de forma consistente. Se nao reproduz, colete mais informacao.
2. **Isolar** — Elimine variaveis. E so no frontend? So no backend? So com este usuario? So nesta rota?
3. **Rastrear** — Siga o fluxo dos dados: frontend → API route → query → banco → resposta → frontend.
4. **Diagnosticar** — Identifique exatamente onde o fluxo quebra.
5. **Corrigir** — Corrija a causa raiz. Verifique se nao introduziu novos problemas.

### Regra dos 3 tentativas

Se nao resolver em 3 tentativas:
1. Salve tudo no arquivo de estado (o que tentou, por que falhou, hipotese atual)
2. Marque tarefa como "bloqueado" no kanban
3. Gere prompt com contexto completo para nova sessao com contexto limpo

---

## 2. Armadilhas Next.js

### Server/Client Boundary

**Sintoma:** `Error: useState is not a function` ou `Error: createContext is not a function`
**Causa:** Componente de servidor tentando usar hooks de cliente.

```typescript
// ERRADO — Server Component usando estado
export default function Page() {
  const [data, setData] = useState([]) // CRASH
}

// CERTO — Marcar como Client Component
'use client'
export default function Page() {
  const [data, setData] = useState([])
}
```

**Regra:** Se usa `useState`, `useEffect`, `useContext`, `onClick`, ou qualquer interatividade → precisa de `'use client'` no topo do arquivo.

### Hydration Mismatch

**Sintoma:** `Warning: Text content did not match` ou `Hydration failed`
**Causa:** Servidor renderiza HTML diferente do que o cliente tenta hidratar.

Causas comuns:
- `Date.now()` ou `Math.random()` no render (diferente no servidor e cliente)
- Extensoes de navegador injetando elementos no DOM
- Condicional baseada em `window` ou `localStorage` no render inicial

```typescript
// ERRADO — valor diferente no servidor vs cliente
<p>{new Date().toLocaleString()}</p>

// CERTO — renderizar no cliente apos mount
const [mounted, setMounted] = useState(false)
useEffect(() => setMounted(true), [])
if (!mounted) return null
return <p>{new Date().toLocaleString()}</p>
```

### Middleware Edge Runtime

**Sintoma:** `Error: Dynamic Code Evaluation not allowed in Edge Runtime`
**Causa:** Middleware Next.js roda no Edge Runtime, que nao suporta `eval()`, `new Function()`, e algumas bibliotecas Node.js.

```typescript
// O middleware NAO pode usar:
// - fs, path, crypto (modulos Node.js)
// - Bibliotecas que usam eval() internamente
// - Dynamic imports com variaveis

// Pode usar:
// - fetch
// - Headers, Request, Response (Web APIs)
// - Supabase Auth Helpers (sao compatíveis com Edge)
```

### API Route nao retorna Response

**Sintoma:** `Error: No response returned` ou timeout na rota
**Causa:** Algum caminho de codigo nao retorna `NextResponse.json()`.

```typescript
// ERRADO — if sem else, caminho sem return
export async function GET() {
  const { data } = await supabase.from('x').select('*')
  if (data) {
    return NextResponse.json({ data })
  }
  // Se data e null, nao retorna nada!
}

// CERTO — todo caminho retorna
export async function GET() {
  const { data, error } = await supabase.from('x').select('*')
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ data: data || [] })
}
```

---

## 3. Armadilhas Supabase

### RLS bloqueando queries silenciosamente

**Sintoma:** Query retorna array vazio, sem erro.
**Causa:** RLS ativo mas policy nao cobre o caso de uso.

```sql
-- Verificar: RLS esta ativado?
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Verificar: policies existem?
SELECT * FROM pg_policies WHERE tablename = 'sua_tabela';

-- Teste rapido: desativar RLS e re-rodar query
-- Se retorna dados → policy esta bloqueando
-- Se nao retorna → problema e na query ou nos dados
```

**Causas comuns de RLS silencioso:**
- Policy filtra por `auth.uid()` mas a query roda sem sessao autenticada
- Policy usa `auth.jwt() ->> 'role'` mas o JWT nao tem esse campo
- Policy para INSERT existe mas para SELECT nao (ou vice-versa)

### Auth timing (sessao nao pronta)

**Sintoma:** Primeira requisicao apos login retorna 401. Segunda funciona.
**Causa:** Cookie de sessao ainda nao foi gravado quando a primeira requisicao dispara.

```typescript
// ERRADO — redirecionar imediatamente apos login
const { error } = await supabase.auth.signInWithPassword({ email, password })
if (!error) router.push('/app') // Sessao pode nao estar pronta!

// CERTO — aguardar evento de sessao
const { error } = await supabase.auth.signInWithPassword({ email, password })
if (!error) {
  // Aguardar o cookie ser gravado
  await new Promise(resolve => setTimeout(resolve, 100))
  router.push('/app')
}
```

### Tipos Postgres vs TypeScript

**Sintoma:** Tipo retornado pelo Supabase nao bate com o esperado no TypeScript.
**Causa:** Mapeamento de tipos diferente.

| Postgres | Supabase retorna | TypeScript espera |
|----------|-----------------|-------------------|
| `integer` | `number` | `number` |
| `bigint` | `string` | `number` (precisa parseInt) |
| `timestamp` | `string` (ISO 8601) | `Date` (precisa new Date()) |
| `jsonb` | `object` | tipagem manual necessaria |
| `uuid` | `string` | `string` |
| `boolean` | `boolean` | `boolean` |
| `numeric` | `string` | `number` (precisa parseFloat) |

---

## 4. Anti-Padroes de Performance

### N+1 queries

**Como detectar:** Loop fazendo query ao banco dentro de `.map()` ou `for`.
**Como corrigir:** Usar JOIN ou `.select('*, relacao(*)')`.

### Re-renders excessivos no React

**Como detectar:** Componente re-renderiza sem os dados terem mudado.
**Como corrigir:**
- `useMemo` para calculos pesados
- `useCallback` para funcoes passadas como props
- Verificar se estado esta no nivel correto (nao subir demais)

### Bundle size inflado

**Como detectar:** `npm run build` mostra paginas > 200KB.
**Como corrigir:**
- `import dynamic from 'next/dynamic'` para componentes pesados
- Verificar se bibliotecas grandes nao estao sendo importadas inteiras
- `import { funcao } from 'lib'` em vez de `import lib from 'lib'`

### Missing indexes

**Como detectar:** Query demora >100ms em tabela com >1000 registros.
**Como corrigir:** Criar indice para cada campo em WHERE/ORDER BY/JOIN.

```sql
-- Ver queries lentas no Supabase
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- Ver tabelas sem indices
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN (SELECT tablename FROM pg_indexes WHERE schemaname = 'public');
```

---

## 5. Padroes de Resiliencia

### Timeout handling

Toda chamada externa DEVE ter timeout:

```typescript
const controller = new AbortController()
const timeout = setTimeout(() => controller.abort(), 5000)

try {
  const res = await fetch(url, { signal: controller.signal })
  clearTimeout(timeout)
  return res.json()
} catch (error) {
  clearTimeout(timeout)
  if (error.name === 'AbortError') {
    console.error('Timeout: servico nao respondeu em 5s')
  }
  throw error
}
```

### Race conditions

**Sintoma:** Operacao funciona sozinha mas falha quando dois usuarios fazem ao mesmo tempo.
**Causa:** Falta de atomicidade.

```sql
-- ERRADO — ler e atualizar separado (race condition)
SELECT estoque FROM produtos WHERE id = 1;  -- retorna 5
UPDATE produtos SET estoque = 4 WHERE id = 1; -- outro usuario ja atualizou para 3!

-- CERTO — operacao atomica
UPDATE produtos SET estoque = estoque - 1 WHERE id = 1 AND estoque > 0
RETURNING estoque;
```

### Idempotencia

**O que e:** Fazer a mesma requisicao 2x deve ter o mesmo resultado que fazer 1x.
**Por que importa:** Rede instavel pode enviar a mesma requisicao duplicada.

```typescript
// ERRADO — cria duplicata se requisicao for repetida
export async function POST(request: Request) {
  const { email } = await request.json()
  await supabase.from('newsletter').insert({ email }) // duplica!
}

// CERTO — usa upsert ou verifica antes
export async function POST(request: Request) {
  const { email } = await request.json()
  await supabase.from('newsletter').upsert({ email }, { onConflict: 'email' })
}
```

---

## 6. Scan Preventivo Pre-Deploy

Checklist completo para varredura antes do lancamento:

### Inicializacao e ambiente

- [ ] Todas as variaveis de ambiente listadas no `.env.example`?
- [ ] Nenhuma variavel sensivel com prefixo `NEXT_PUBLIC_`?
- [ ] Servicos externos inicializados on-demand (nao no topo do modulo)?
- [ ] App inicia sem nenhuma variavel opcional ausente (graceful degradation)?

### Conformidade com contratos

- [ ] Todas as rotas implementam EXATAMENTE o que o `project-core.md` define?
- [ ] Campos de entrada e saida batem com o contrato?
- [ ] Todos os codigos de erro listados no contrato sao retornados corretamente?
- [ ] Validacoes do contrato estao no SERVIDOR (nao so no cliente)?

### Validacao de entrada

- [ ] Todo campo string tem `.max()` definido?
- [ ] Todo campo numerico tem range validado?
- [ ] Todo campo obrigatorio e verificado antes de usar?
- [ ] Nenhuma query usa input do usuario sem sanitizar?

### Fluxos completos

- [ ] Login → acesso a area protegida → logout funciona?
- [ ] Criar → listar → editar → deletar funciona para cada recurso?
- [ ] Erro de rede mostra mensagem amigavel (nao tela branca)?
- [ ] Sessao expirada redireciona para login (nao mostra erro generico)?

### Seguranca

- [ ] RLS ativado em TODAS as tabelas?
- [ ] Queries filtram por `user_id` do usuario autenticado?
- [ ] Middleware protege rotas privadas?
- [ ] Nenhum secret em codigo-fonte ou logs?

### Performance

- [ ] Nenhuma query N+1?
- [ ] Paginacao em todas as listagens?
- [ ] Indices em campos de WHERE/ORDER BY?
- [ ] Payloads retornam so campos necessarios?

---

## 7. Protocolo de Escalacao

### Quando resolver sozinho (SCOUT)

- Bug em rota de API (logica, validacao, status code)
- Problema de rendering no frontend (hydration, state, props)
- Query retornando dados errados (filtro, join, ordenacao)
- Erro de importacao ou configuracao
- Performance lenta em query especifica

### Quando escalar para ATLAS

- Contrato no `project-core.md` esta inconsistente ou incompleto
- Arquitetura precisa mudar (nova tabela, nova rota, novo fluxo)
- Erro afeta multiplas camadas ao mesmo tempo (banco + API + frontend)
- Decisao de design que afeta o escopo do projeto

### Quando escalar para o comandante

- 3 tentativas falharam E nova sessao tambem falhou
- Bug depende de servico externo fora do controle (API de terceiros)
- Correcao exige credenciais ou acesso que o agente nao tem
- Erro pode indicar problema no proprio sistema D-11 (nao no projeto)

### Formato de escalacao

```
ESCALACAO: [SCOUT → ATLAS/COMANDANTE]
Erro: [descricao clara do que deveria acontecer vs o que acontece]
Arquivos: [lista de arquivos envolvidos]
Tentativas: [o que ja foi tentado e por que nao funcionou]
Hipotese: [o que voce acha que e a causa raiz]
Sugestao: [o que voce acha que precisa ser feito]
```

---

## 8. Erros Comuns de Diagnostico

### Tratar o sintoma em vez da causa

**Errado:** Pagina quebra ao renderizar → adicionar try/catch generico.
**Certo:** Investigar POR QUE o dado esta null/undefined e corrigir na fonte.

### Nao reproduzir antes de corrigir

**Errado:** "Acho que o erro e aqui" → muda o codigo → nao testa.
**Certo:** Reproduz o erro → confirma a causa → faz a correcao → verifica que o erro sumiu.

### Ignorar o contexto do erro

**Errado:** Ler "TypeError: Cannot read properties of null" e procurar null aleatorio.
**Certo:** Ler o STACK TRACE completo — ele diz o arquivo, a linha, e a cadeia de chamadas.

### Corrigir no lugar errado

**Errado:** Frontend mostra dado errado → corrigir no frontend adicionando transformacao.
**Certo:** Se a API retorna dado errado, corrigir na API. Se o banco tem dado errado, corrigir no banco. A correcao vai na camada onde o erro NASCE, nao onde ele APARECE.

### Nao verificar se a correcao nao quebrou outra coisa

**Errado:** Corrigir bug A → fechar tarefa → descobrir que bug B apareceu.
**Certo:** Apos corrigir, rodar Build Validator e testar fluxos relacionados.
