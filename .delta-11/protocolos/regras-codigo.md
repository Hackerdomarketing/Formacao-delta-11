# REGRAS DE QUALIDADE DE CÓDIGO — Formação Δ-11

> **Este protocolo é OBRIGATÓRIO para todos os agentes que escrevem código:** ENGINE, BACK, FRONT, PIXEL, FORM, VAULT, SCOUT.
> Leia esta seção inteira antes de codificar qualquer funcionalidade nova.

---

## 1. INTERLIGAÇÕES ENTRE CAMADAS

> Regra fundamental: quando você muda UMA camada, quase sempre precisa mudar OUTRA. Se não mudar todas, ficam "pontas soltas" e o sistema quebra.

### Checklist de efeito em cascata (use antes de qualquer mudança)

Ao alterar qualquer coisa, pergunte: **"Isso é um contrato entre camadas?"**

Contratos são: endpoints de API, formatos de dados, schemas de banco, nomes de eventos, filas, variáveis de ambiente.

Se SIM, atualize TODAS as camadas afetadas:

```
□ Frontend: componentes, páginas, rotas, navegação, tipos TypeScript
□ Backend: endpoints, controllers, services, middleware, validações
□ Banco de dados: tabelas, campos, migrations, índices, foreign keys
□ Automações: cron jobs, workers, filas, webhooks, event listeners
□ Autenticação: tokens, permissões, middleware de auth
□ Configuração: variáveis de ambiente (.env.example), arquivos de config
□ Testes: unitários, integração, E2E — atualizar ou criar para o que mudou
```

### Tabela de efeitos em cascata

| Você muda... | Frontend? | Backend? | Banco? | Automações? |
|-------------|-----------|----------|--------|-------------|
| Nome de campo na API | Sim | Sim | Não | Se usa a API |
| Tipo de campo (string→number) | Sim | Sim | Sim (migration) | Sim |
| URL de endpoint | Sim | Sim | Não | Se chama o endpoint |
| Schema do banco | Não diretamente | Sim (model) | Sim (migration) | Se consulta o campo |
| Regra de autenticação | Sim | Sim | Talvez (campo role) | Sim (workers autenticados?) |

### Regra para remoção de funcionalidade

Ao REMOVER qualquer funcionalidade, verifique se existem:
- Cron jobs ou workers relacionados
- Filas de mensagens que processam eventos dessa feature
- Webhooks que acionam essa feature
- Tabelas ou campos no banco exclusivos dela
- Variáveis de ambiente exclusivas dela

**Nunca remova apenas a parte visual e deixe backend/banco com pontas soltas.**

---

## 2. SEGURANÇA

### Validação de dados

- **SEMPRE valide no servidor.** Validação client-side é UX, não segurança.
- Todo campo `string` recebe `.max()` — previne DoS por payload gigante.
- Campos de senha recebem `.max(128)` — previne DoS por hash lento.
- URLs rejeitam protocolos perigosos: `javascript:`, `data:`, `file:`, `ftp:`.
- Uploads de arquivo: whitelist de tipos MIME + tamanho máximo + sanitização do nome.
- Formulários: desabilitar botão de submit após clique. Usar chave de idempotência.

### Autenticação e sessões

- Verifique autenticação **dentro da própria rota**, não apenas no middleware.
- Não retorne mensagens diferentes para "email não existe" vs "senha errada" — evita enumeração.
- Tokens JWT: expiration obrigatório. Refresh token em cookie `httpOnly`.
- Frontend: interceptor que detecta `401`, faz refresh automático, re-executa o request original. Se refresh também falhou, redireciona para login com mensagem de sessão expirada.

### Rate limiting

Obrigatório em rotas públicas que podem ser abusadas:
- Login, registro, recuperação de senha
- Qualquer rota que consuma crédito, envie email ou SMS

---

## 3. RESILIÊNCIA (não travar quando serviço externo cai)

### Timeout + retry obrigatórios em APIs externas

```typescript
// Padrão obrigatório para Stripe, Resend, qualquer API externa
const resultado = await retryComBackoff(
  () => stripe.charges.create(payload),
  { tentativas: 3, timeoutMs: 5000 }
)
```

- **Timeout:** 5 segundos por chamada. Nunca deixar request travar indefinidamente.
- **Retry:** máximo 3 tentativas com backoff exponencial (1s, 2s, 4s).
- **Circuit breaker:** se uma API externa falhar 5x seguidas, pare de chamar por 60s.

### Graceful degradation (degradação graciosa)

O sistema NUNCA pode ficar completamente parado por falha de serviço externo:
- Se email falha → usuário vê "enviaremos em breve", operação continua.
- Se Stripe falha → pedido entra em fila para retry, usuário recebe confirmação pendente.
- Se serviço de notificação falha → log do erro, fluxo principal continua.

### Idempotência em webhooks

Webhooks e retries automáticos DEVEM ser idempotentes:
- Usar chave única por evento (ex: `stripe_event_id`, `webhook_id`).
- Verificar se o evento já foi processado antes de processar novamente.
- Guardar registro de eventos processados na tabela `webhook_events`.

### Logging obrigatório

```typescript
// Em toda falha significativa:
console.error('[ENGINE] falha ao processar pagamento', {
  userId,
  operacao: 'criar_assinatura',
  erro: error.message,
  // NUNCA logar: senha, token, cartão, dados pessoais sensíveis
})

// Em eventos críticos de negócio:
console.info('[ENGINE] assinatura criada', { userId, planoId })
```

---

## 4. PERFORMANCE DE BANCO DE DADOS

### Problema N+1 — o mais comum e mais perigoso

**Errado (N+1):**
```typescript
const posts = await db.posts.findMany()
for (const post of posts) {
  // UMA query por post = N+1 queries!
  post.author = await db.users.findUnique({ where: { id: post.userId } })
}
```

**Correto (JOIN/eager loading):**
```typescript
const posts = await db.posts.findMany({
  include: { author: true }  // 1 única query
})
```

**Regra:** Se você está consultando o banco dentro de um loop, está cometendo N+1. Use `include`, `join` ou busque os dados em batch antes do loop.

### Índices obrigatórios

O VAULT cria índices para todos os campos usados em:
- `WHERE` (filtros)
- `ORDER BY` (ordenação)
- `JOIN` (relacionamentos — foreign keys)
- Campos com `UNIQUE`

Se ENGINE ou BACK perceber query lenta (>200ms em dev), reportar ao VAULT para adicionar índice.

### Migration safety (segurança em mudanças de banco)

Nunca remova uma coluna antes de remover o código que a usa. Ordem obrigatória:
1. Atualiza código para parar de usar a coluna → deploya
2. Cria migration para remover a coluna → deploya

Toda `foreign key` deve declarar `ON DELETE` explicitamente: `CASCADE`, `SET NULL`, ou `RESTRICT` (com comentário justificando).

---

## 5. QUALIDADE DE INTERFACE

### Memory leaks em React/Next.js

Todo `useEffect` que registra listeners, timers ou subscriptions DEVE ter cleanup:

```typescript
useEffect(() => {
  const subscription = socket.on('mensagem', handleMensagem)
  const timer = setInterval(tick, 1000)
  const controller = new AbortController()

  return () => {
    subscription.off('mensagem', handleMensagem)  // cleanup obrigatório
    clearInterval(timer)
    controller.abort()
  }
}, [])
```

### Loading states obrigatórios

Todo componente que faz fetch de dados DEVE ter 3 estados visuais:
1. **Loading:** skeleton que imita o layout real da página (não spinner genérico)
2. **Error:** mensagem clara + botão de retry
3. **Success:** dados renderizados

### Dados null/undefined na renderização

Nunca renderizar dados da API diretamente sem fallback:

```typescript
// Errado — quebra se API retornar null
<p>{user.name}</p>

// Correto
<p>{user?.name ?? 'Carregando...'}</p>
```

### Acessibilidade mínima obrigatória

- Toda `<img>` tem `alt` descritivo.
- Todo `<input>` tem `<label>` associado via `htmlFor`.
- Contraste de texto: mínimo WCAG AA (ratio 4.5:1 para texto normal).
- Navegação por teclado: todos os elementos interativos acessíveis via Tab.

### Imagens otimizadas (Next.js)

Usar `next/image` em vez de `<img>` para:
- Lazy loading automático
- Formatos modernos (WebP/AVIF) automáticos
- Tamanhos responsivos

---

## 6. VARIÁVEIS DE AMBIENTE

Se uma funcionalidade precisa de configuração (chave de API, URL, segredo):
1. Adicione ao `.env.example` **sem o valor real**, com comentário explicando para que serve.
2. Use no código via `process.env.NOME_DA_VARIAVEL`.
3. Valide na inicialização do servidor — se a variável não existe, falhe ruidosamente na startup, não silenciosamente em runtime.

```typescript
// Validação na startup (src/lib/env.ts)
if (!process.env.STRIPE_SECRET_KEY) {
  throw new Error('STRIPE_SECRET_KEY não configurada. Ver .env.example')
}
```

---

## 7. TESTES ENTRE CAMADAS

Ao criar funcionalidade nova, criar testes que validem a cadeia completa:

```
"frontend envia X → backend valida Y → banco salva Z → resposta contém W"
```

Tipos de teste por situação:
- **Unitário:** funções de lógica de negócio isoladas
- **Integração:** endpoint + banco (testar o caminho feliz e os principais erros)
- **E2E:** fluxo completo do ponto de vista do usuário

Para cada feature, criar ao menos:
1. Teste do caminho feliz (sucesso)
2. Teste com input inválido (deve retornar erro adequado)
3. Teste de acesso não autorizado (deve retornar 401/403)

---

## Fonte

Extraído e adaptado de:
- `pesquisa-ia-programacao/fases/fase-03-interligacoes-camadas.md`
- `pesquisa-ia-programacao/fases/fase-04-problemas-comuns.md`
- Repositório: `github.com/Hackerdomarketing/tarefas-pessoais` (branch: `main`)
