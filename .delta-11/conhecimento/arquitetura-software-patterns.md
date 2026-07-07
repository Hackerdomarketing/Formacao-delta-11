# Base de Conhecimento: Arquitetura de Software e Descoberta de Projeto — ATLAS

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Contratos e esquemas nascem já na convenção: rotas, campos JSON e colunas de banco em inglês; descrições e regras de negócio em português.


Referencia pratica para decisoes arquiteturais, descoberta de projeto, classificacao de complexidade e design de contratos.

## 1. Descoberta de Projeto — Perguntas Essenciais

### 1.1 Perguntas sobre o Avatar (usuario final)

Antes de qualquer decisao tecnica, entender QUEM vai usar:

```
1. Quem e o usuario final? (perfil, idade, nivel tecnico)
2. Qual problema ele tem HOJE? (dor real, nao imaginada)
3. O que ele ja tentou antes? (solucoes existentes que frustraram)
4. O que ele ODEIA nas alternativas? (pontos de dor prioritarios)
5. O que faria ele dizer "isso e de outra categoria"? (experiencia wow)
```

### 1.2 Perguntas sobre o Produto

```
1. O que o sistema precisa fazer? (funcionalidades core — maximo 5)
2. Quais integrações externas? (pagamentos, email, auth, storage)
3. Quantos usuarios simultaneos? (10, 100, 1000, 10000+)
4. Dados sensiveis? (financeiros, saude, pessoais → impacta seguranca)
5. Existe deadline real? (lancamento, evento, contrato)
```

### 1.3 Anti-Padroes de Descoberta

```
ERRADO: Aceitar "quero um app de delivery" e comecar a planejar
CERTO: Perguntar "delivery de que? para quem? onde? qual o diferencial?"

ERRADO: Assumir que o cliente sabe o que quer tecnicamente
CERTO: Traduzir desejos em requisitos concretos

ERRADO: Planejar todas as features de uma vez
CERTO: Identificar o nucleo minimo que ja entrega valor (MVP real)
```

## 2. Classificacao de Complexidade (Score)

### 2.1 Criterios de Pontuacao

| Criterio | 1-3 (Baixo) | 4-6 (Medio) | 7-10 (Alto) |
|----------|-------------|-------------|-------------|
| Paginas | 1-5 telas | 6-15 telas | 16+ telas |
| Roles de usuario | 1 tipo | 2-3 tipos | 4+ tipos (admin, moderador, etc) |
| Integrações | 0-1 servico | 2-3 servicos | 4+ servicos |
| Dados | CRUD simples | Relacoes complexas | Real-time, filas, cache |
| Autenticacao | Login basico | Multi-role + permissoes | SSO, MFA, tokens por recurso |
| Pagamento | Nenhum | Checkout unico | Assinaturas, split, metering |
| Deploy | Vercel simples | Vercel + Supabase | Multi-servico + CI/CD |

### 2.2 Impacto do Score na Equipe

```
Score 1-3: BACK acumula ENGINE + VAULT, FRONT acumula PIXEL + FORM
Score 4-6: BACK lidera ENGINE, FRONT lidera PIXEL + FORM
Score 7-10: Todos os 10 agentes ativos, Phase 2.5 obrigatoria
```

### 2.3 Erros Comuns na Classificacao

```
ERRADO: Score baixo porque "so tem 3 telas" — mas cada tela tem 10 estados
CERTO: Contar estados de UI, nao apenas telas

ERRADO: Score baixo porque "e so um CRUD" — mas tem 8 tabelas relacionadas
CERTO: Avaliar complexidade do schema, nao apenas operacoes

ERRADO: Score alto porque "o cliente pediu muitas features"
CERTO: Separar MVP (score real) de roadmap futuro (score projetado)
```

## 3. Padroes de Arquitetura por Complexidade

### 3.1 Projeto Simples (Score 1-3)

```
Stack:
- Monolito Next.js (App Router)
- Supabase como backend completo (auth + database + storage)
- Sem camada de API intermediaria (acesso direto via RLS)
- Deploy: Vercel

Estrutura de pastas:
src/
  app/
    (app)/          ← paginas autenticadas
    (public)/       ← paginas publicas (landing, login)
    layout.tsx
  components/       ← componentes reutilizaveis
  lib/
    supabase.ts     ← client do Supabase
    utils.ts        ← funcoes utilitarias
  types/
    database.ts     ← tipos gerados do Supabase
```

### 3.2 Projeto Medio (Score 4-6)

```
Stack:
- Next.js com API Routes como camada intermediaria
- Supabase para dados + auth
- Servicos externos (Stripe, Resend) chamados APENAS pelo servidor
- Separacao clara: paginas → API routes → Supabase
- Deploy: Vercel + Supabase Cloud

Estrutura de pastas:
src/
  app/
    (app)/          ← paginas autenticadas
    (admin)/        ← paginas administrativas
    (public)/       ← paginas publicas
    api/            ← rotas de API
      users/
        route.ts
      payments/
        route.ts
  components/
    ui/             ← componentes base (Button, Input, Card)
    forms/          ← componentes de formulario
    layouts/        ← layouts compartilhados
  lib/
    supabase.ts
    stripe.ts       ← client Stripe (on-demand)
    validations.ts  ← schemas Zod compartilhados
  types/
```

### 3.3 Projeto Complexo (Score 7-10)

```
Stack:
- Next.js + API Routes + filas de processamento (Inngest/BullMQ)
- Supabase para dados + auth + real-time
- Cache layer (Redis/Upstash) para dados frequentes
- Servicos externos com circuit breaker e retry
- Deploy: Vercel + Supabase + servicos adicionais

Adicoes na estrutura:
src/
  app/api/
    webhooks/       ← endpoints para webhooks (Stripe, etc)
    cron/           ← endpoints para cron jobs
  lib/
    cache.ts        ← camada de cache
    queue.ts        ← filas de processamento
    circuit-breaker.ts
  workers/          ← processamento assincrono
```

## 4. Design de Contratos de API

### 4.1 Formato Padrao de Rota

```
ROTA: [METODO] /api/[recurso]
AUTENTICACAO: [sim/nao] [tipo: JWT/session/API key]
RATE LIMIT: [N requests/minuto]
ENTRADA:
  - campo (tipo) [obrigatorio/opcional] — descricao
  - campo.max(N) — limite de caracteres (obrigatorio para strings)
VALIDACAO:
  - regra 1
  - regra 2
SAIDA SUCESSO (200/201):
  { campo: tipo }
SAIDA ERRO:
  400 — { error: "mensagem" } — validacao falhou
  401 — { error: "nao autenticado" }
  403 — { error: "sem permissao" }
  404 — { error: "nao encontrado" }
  409 — { error: "conflito" } — recurso ja existe
  429 — { error: "muitas requisicoes" }
  500 — { error: "erro interno" }
```

### 4.2 Regras Inviolaveis de Contrato

```
1. TODO campo string TEM .max() definido (previne DoS via payload gigante)
2. TODO campo em WHERE/ORDER BY/JOIN TEM indice no banco
3. TODA foreign key declara ON DELETE explicitamente
4. TODA rota com escrita valida no SERVIDOR (nunca confiar no cliente)
5. Servicos externos inicializados ON-DEMAND dentro da funcao
6. TODA rota autenticada verifica sessao ANTES de qualquer logica
7. Campos monetarios usam integer (centavos), NUNCA float
8. URLs de usuario filtram protocolos (bloquear javascript:, data:)
```

### 4.3 Anti-Padroes de Contrato

```
ERRADO: Retornar objeto inteiro do banco na API
CERTO: Retornar APENAS os campos que o frontend precisa

ERRADO: Aceitar { role: "admin" } do frontend para mudar permissao
CERTO: Permissao e verificada no servidor, nunca enviada pelo cliente

ERRADO: Validar no frontend e confiar que chegou validado no servidor
CERTO: Validar em AMBOS (frontend para UX, servidor para seguranca)

ERRADO: Usar o mesmo endpoint para admin e usuario normal
CERTO: Endpoints separados com middlewares de permissao diferentes
```

## 5. Padroes de Schema de Banco

### 5.1 Tabelas Obrigatorias

```sql
-- Estende auth.users com dados do app
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Registra acoes criticas (quem, quando, o que)
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  details JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.2 Campos Obrigatorios em Toda Tabela

```
id         — UUID primary key (default gen_random_uuid())
created_at — TIMESTAMPTZ (default now())
updated_at — TIMESTAMPTZ atualizado via trigger
```

### 5.3 Convencoes de Nomenclatura

```
Tabelas:      plural, snake_case       → user_profiles
Colunas:      singular, snake_case     → first_name
Foreign keys: [tabela_singular]_id     → organization_id
Indexes:      idx_[tabela]_[coluna]    → idx_profiles_user_id
RLS Policies: [tabela]_[operacao]_[quem] → profiles_select_own
Triggers:     trg_[tabela]_[acao]      → trg_profiles_updated_at
Functions:    fn_[descricao]           → fn_handle_new_user
```

### 5.4 RLS — Padroes Seguros

```sql
-- Padrao: usuario so ve seus proprios dados
CREATE POLICY profiles_select_own ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Padrao: usuario so edita seus proprios dados
CREATE POLICY profiles_update_own ON profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- ERRADO: policy que permite tudo
CREATE POLICY profiles_select_all ON profiles
  FOR SELECT USING (true);  -- NUNCA FAZER ISSO sem justificativa
```

## 6. Padroes de Resiliencia

### 6.1 Timeout + Retry + Circuit Breaker

```typescript
// Configuracao padrao por tipo de servico
const TIMEOUTS = {
  database: 5000,      // 5s — query lenta = problema
  payment: 30000,      // 30s — Stripe pode demorar
  email: 10000,        // 10s — envio de email
  external_api: 10000, // 10s — APIs de terceiros
  file_upload: 60000,  // 60s — uploads podem ser grandes
}

const RETRY = {
  max_attempts: 3,
  backoff: 'exponential', // 1s, 2s, 4s
  retryable_codes: [408, 429, 500, 502, 503, 504],
  non_retryable: [400, 401, 403, 404, 409],
}
```

### 6.2 Inicializacao Segura de Servicos

```typescript
// ERRADO — crash se variavel ausente (executa no import)
const stripe = new Stripe(process.env.STRIPE_KEY!)

// CERTO — inicializacao on-demand, erro claro
let _stripe: Stripe | null = null
function getStripe(): Stripe {
  if (!_stripe) {
    const key = process.env.STRIPE_KEY
    if (!key) throw new Error('STRIPE_KEY nao configurada')
    _stripe = new Stripe(key)
  }
  return _stripe
}
```

### 6.3 Graceful Degradation

```
Principio: funcionalidade parcial > erro total

Exemplo — sistema de notificacoes:
- Email falhou? → Logar erro, continuar operacao principal
- Cache indisponivel? → Buscar direto do banco (mais lento, mas funciona)
- Servico de analytics fora? → Enfileirar para processar depois

Exemplo — checkout:
- Calculo de frete falhou? → PARAR (e parte critica do fluxo)
- Geração de nota fiscal falhou? → CONTINUAR (processar depois)
```

## 7. Decisoes de Stack — Quando Usar o Que

### 7.1 Banco de Dados

```
Supabase (padrao D-11):
- Projetos web com auth integrado
- Real-time necessario
- RLS para multi-tenancy
- PostgreSQL como base solida

Quando NAO usar Supabase:
- App mobile-only (considerar Firebase)
- Dados nao-relacionais massivos (considerar MongoDB)
- Projeto sem auth (overhead desnecessario)
```

### 7.2 Framework Frontend

```
Next.js App Router (padrao D-11):
- SEO importa (SSR/SSG)
- Precisa de API routes
- Projeto web completo

Quando considerar alternativas:
- SPA pura sem SEO → Vite + React
- Site estatico → Astro
- App mobile → React Native / Expo
```

### 7.3 Estilizacao

```
Tailwind CSS (padrao D-11):
- Produtividade alta
- Design system consistente
- Sem CSS custom na maioria dos casos

Shadcn/ui (complemento):
- Componentes acessiveis prontos
- Customizaveis via Tailwind
- Nao e dependencia — copia o codigo
```

## 8. Checklist de Arquitetura (antes de finalizar Fase 2)

### 8.1 Contratos

```
- [ ] Todas as rotas definidas com formato padrao completo
- [ ] Todos os campos string com .max() definido
- [ ] Todos os status HTTP corretos por operacao
- [ ] Formato de erro padronizado em todas as rotas
- [ ] Rate limiting definido para rotas publicas
```

### 8.2 Banco de Dados

```
- [ ] Todas as tabelas com RLS habilitado
- [ ] Todas as FK com ON DELETE definido
- [ ] Campos em WHERE/ORDER BY com indice
- [ ] Trigger de updated_at em todas as tabelas
- [ ] Tabela profiles criada e ligada a auth.users
```

### 8.3 Seguranca

```
- [ ] Servicos externos com inicializacao on-demand
- [ ] Variaveis de ambiente listadas com descricao
- [ ] Fluxo de autenticacao completo (signup, login, logout, refresh)
- [ ] Tratamento de 401 → refresh → retry definido
- [ ] Validacao no servidor para TODA escrita
```

### 8.4 Infraestrutura

```
- [ ] Ordem de implementacao definida (banco → API → UI)
- [ ] Servicos externos listados com timeout e retry
- [ ] Webhooks com verificacao de assinatura
- [ ] Variaveis de ambiente para cada ambiente (dev, staging, prod)
- [ ] Score de complexidade calculado e documentado
```

### 8.5 Experiencia do Usuario

```
- [ ] Fluxos criticos mapeados passo a passo
- [ ] Estados de loading, erro e vazio definidos por tela
- [ ] Feedback visual para TODA acao do usuario
- [ ] Responsividade definida (mobile-first ou desktop-first)
- [ ] Acessibilidade basica (labels, contraste, navegacao por teclado)
```
