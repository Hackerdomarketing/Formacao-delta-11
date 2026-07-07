# Supabase RLS Patterns — Referencia Pratica para VAULT

> **LIMITES ESTRUTURAIS E IDIOMA (obrigatório — `.delta-11/protocolos/regras-codigo.md` seções 8 e 9):**
> Função ≤ 50 linhas e ≤ 3 parâmetros · arquivo ≤ 400 linhas · aninhamento ≤ 3 · 1 classe por arquivo · complexidade ciclomática ≤ 10.
> Código em INGLÊS (nomes de variáveis, funções, tabelas, campos JSON) · conteúdo em PORTUGUÊS (comentários, textos de UI, mensagens ao usuário, descrições de teste). Nomes descritivos, sem abreviação.
> Tabelas e colunas em inglês · 1 assunto por migration · comentários SQL em português.


Referencia de Row Level Security para o agente VAULT criar e revisar schemas no Supabase/PostgreSQL.

---

## 1. Fundamentos

RLS e um filtro automatico no banco de dados. Cada tabela pode ter "politicas" que definem QUEM pode ver ou modificar CADA LINHA. O PostgreSQL aplica essas regras em toda query, mesmo as vindas da API do Supabase.

```sql
-- Ativar RLS numa tabela (OBRIGATORIO antes de criar politicas)
ALTER TABLE minha_tabela ENABLE ROW LEVEL SECURITY;

-- Funcoes uteis do Supabase dentro de politicas:
-- auth.uid()        → ID do usuario logado (UUID)
-- auth.jwt()        → Token JWT completo (contem role, metadata, etc)
-- auth.role()       → 'authenticated' ou 'anon'
```

**Regra fundamental:** Com RLS ativado e ZERO politicas, NINGUEM consegue ler ou escrever. Cada permissao precisa ser explicitamente criada.

---

## 2. Padroes de Politica

### 2.1 Usuario so acessa seus proprios dados

```sql
ALTER TABLE pedidos ENABLE ROW LEVEL SECURITY;

-- Leitura: usuario ve apenas seus pedidos
CREATE POLICY "usuario_le_seus_pedidos"
  ON pedidos FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Insercao: usuario so cria pedidos para si mesmo
CREATE POLICY "usuario_cria_seus_pedidos"
  ON pedidos FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- Atualizacao: usuario so edita seus pedidos
CREATE POLICY "usuario_edita_seus_pedidos"
  ON pedidos FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Exclusao: usuario so deleta seus pedidos
CREATE POLICY "usuario_deleta_seus_pedidos"
  ON pedidos FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());
```

### 2.2 Admin acessa tudo

```sql
-- Opcao A: via claim no JWT (recomendado)
CREATE POLICY "admin_acessa_tudo"
  ON pedidos FOR ALL
  TO authenticated
  USING ((auth.jwt() ->> 'user_role') = 'admin')
  WITH CHECK ((auth.jwt() ->> 'user_role') = 'admin');

-- Opcao B: via tabela de perfis
CREATE POLICY "admin_acessa_tudo"
  ON pedidos FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM perfis
      WHERE perfis.id = auth.uid()
      AND perfis.role = 'admin'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM perfis
      WHERE perfis.id = auth.uid()
      AND perfis.role = 'admin'
    )
  );
```

### 2.3 Leitura publica, escrita autenticada

```sql
ALTER TABLE artigos ENABLE ROW LEVEL SECURITY;

-- Qualquer pessoa (ate sem login) pode ler
CREATE POLICY "leitura_publica"
  ON artigos FOR SELECT
  TO anon, authenticated
  USING (true);

-- Somente usuarios logados podem criar
CREATE POLICY "escrita_autenticada"
  ON artigos FOR INSERT
  TO authenticated
  WITH CHECK (autor_id = auth.uid());
```

### 2.4 Acesso por equipe/organizacao

```sql
-- Tabela de membros: quem pertence a qual organizacao
-- membros_organizacao (user_id, org_id, role)

ALTER TABLE projetos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "membro_ve_projetos_da_org"
  ON projetos FOR SELECT
  TO authenticated
  USING (
    org_id IN (
      SELECT org_id FROM membros_organizacao
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "membro_cria_projeto_na_org"
  ON projetos FOR INSERT
  TO authenticated
  WITH CHECK (
    org_id IN (
      SELECT org_id FROM membros_organizacao
      WHERE user_id = auth.uid()
    )
  );
```

### 2.5 RBAC — Controle por papel

```sql
-- Funcao auxiliar para verificar permissao (evita repetir subquery)
CREATE OR REPLACE FUNCTION tem_permissao_na_org(
  p_org_id UUID,
  p_roles TEXT[]
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM membros_organizacao
    WHERE user_id = auth.uid()
    AND org_id = p_org_id
    AND role = ANY(p_roles)
  );
$$;

-- Somente owner e admin da org podem deletar projetos
CREATE POLICY "admin_deleta_projetos"
  ON projetos FOR DELETE
  TO authenticated
  USING (tem_permissao_na_org(org_id, ARRAY['owner', 'admin']));

-- Qualquer membro pode ler
CREATE POLICY "membro_le_projetos"
  ON projetos FOR SELECT
  TO authenticated
  USING (tem_permissao_na_org(org_id, ARRAY['owner', 'admin', 'member', 'viewer']));
```

---

## 3. Erros Comuns e Como Evitar

### 3.1 Esqueceu de ativar RLS

```sql
-- PERIGO: sem RLS, qualquer usuario da API le TODAS as linhas
-- CHECKLIST: toda tabela nova DEVE ter esta linha
ALTER TABLE nome_da_tabela ENABLE ROW LEVEL SECURITY;

-- Verificar quais tabelas NAO tem RLS ativado (query de auditoria)
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false;
```

### 3.2 Politica permissiva demais

```sql
-- ERRADO: permite qualquer usuario autenticado ler TUDO
CREATE POLICY "permissiva_demais"
  ON dados_sensiveis FOR SELECT
  TO authenticated
  USING (true);  -- NUNCA faca isso em tabelas com dados privados

-- CORRETO: restrinja por usuario
CREATE POLICY "restritiva_correta"
  ON dados_sensiveis FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());
```

### 3.3 Politica so para SELECT (esqueceu INSERT/UPDATE/DELETE)

```sql
-- ERRADO: criou politica so de leitura, tabela fica somente-leitura
-- VAULT deve SEMPRE criar politicas para todas as operacoes necessarias

-- Template completo (copiar e adaptar para cada tabela):
-- SELECT → USING (condicao)
-- INSERT → WITH CHECK (condicao)
-- UPDATE → USING (condicao) + WITH CHECK (condicao)
-- DELETE → USING (condicao)
```

### 3.4 Service role e bypass de RLS

```sql
-- O service_role key do Supabase IGNORA RLS por padrao
-- Usar APENAS no backend (server-side), NUNCA no frontend

-- Se precisar que ate o service role respeite RLS:
ALTER TABLE tabela_critica FORCE ROW LEVEL SECURITY;

-- Quando usar service_role (bypassa RLS):
--   - Migrations e seeds
--   - Webhooks e cron jobs do servidor
--   - Operacoes administrativas do backend
--
-- Quando NAO usar service_role:
--   - Qualquer codigo que roda no navegador
--   - Edge Functions que recebem input do usuario sem validar
```

### 3.5 UPDATE com WITH CHECK diferente de USING

```sql
-- USING = quais linhas o usuario PODE acessar
-- WITH CHECK = quais valores o usuario PODE escrever

-- ERRADO: usuario pode transferir pedido para outro usuario
CREATE POLICY "edita_pedido"
  ON pedidos FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid());
  -- sem WITH CHECK, o usuario pode mudar user_id para outro!

-- CORRETO: impede transferencia
CREATE POLICY "edita_pedido"
  ON pedidos FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());
```

---

## 4. Performance

```sql
-- REGRA: colunas usadas em politicas RLS DEVEM ter indice
CREATE INDEX idx_pedidos_user_id ON pedidos (user_id);
CREATE INDEX idx_membros_org_user_org ON membros_organizacao (user_id, org_id);

-- Funcoes SECURITY DEFINER com STABLE sao cacheaveis pelo planner
-- Usar STABLE quando a funcao nao modifica dados
-- Usar VOLATILE somente se a funcao modifica dados

-- Evitar subqueries complexas em politicas de tabelas com muitas linhas
-- Preferir funcoes auxiliares (como tem_permissao_na_org) que o PostgreSQL otimiza melhor

-- Se a politica faz JOIN com outra tabela, ambas precisam de indice
-- nas colunas do JOIN
```

---

## 5. Migration — Adicionar RLS a Tabelas Existentes

```sql
-- PASSO 1: Ativar RLS (a partir daqui, NINGUEM acessa sem politica)
ALTER TABLE tabela_existente ENABLE ROW LEVEL SECURITY;

-- PASSO 2: Criar politica temporaria permissiva (evita downtime)
CREATE POLICY "temporaria_acesso_total"
  ON tabela_existente FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- PASSO 3: Criar as politicas corretas
CREATE POLICY "usuario_le_seus_dados"
  ON tabela_existente FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());
-- ... demais politicas ...

-- PASSO 4: Remover a politica temporaria (SOMENTE apos testar as novas)
DROP POLICY "temporaria_acesso_total" ON tabela_existente;
```

**Ordem segura numa migration Supabase:**
1. `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
2. `CREATE POLICY` (todas as necessarias)
3. Testar via API do Supabase com usuario real
4. Remover politicas temporarias se existirem

---

## 6. Testando Politicas RLS

```sql
-- Simular um usuario especifico no SQL Editor do Supabase
SET request.jwt.claim.sub = 'uuid-do-usuario-aqui';
SET request.jwt.claim.role = 'authenticated';

-- Executar query como se fosse esse usuario
SELECT * FROM pedidos;  -- deve retornar apenas os pedidos desse usuario

-- Resetar
RESET request.jwt.claim.sub;
RESET request.jwt.claim.role;
```

### Checklist de teste para cada tabela

```
[ ] RLS esta ativado (rowsecurity = true)
[ ] Usuario logado ve apenas seus dados
[ ] Usuario logado NAO ve dados de outro usuario
[ ] Usuario anonimo NAO ve dados privados
[ ] INSERT respeita user_id = auth.uid()
[ ] UPDATE nao permite trocar user_id
[ ] DELETE so funciona nos proprios dados
[ ] Admin consegue acessar tudo (se aplicavel)
[ ] Service role bypassa quando necessario
[ ] Colunas usadas em politicas tem indice
```

### Query de auditoria — tabelas sem protecao

```sql
-- Rodar ao final de cada fase de banco para garantir cobertura
SELECT
  t.tablename,
  t.rowsecurity AS rls_ativado,
  COUNT(p.policyname) AS total_politicas
FROM pg_tables t
LEFT JOIN pg_policies p
  ON t.tablename = p.tablename
  AND t.schemaname = p.schemaname
WHERE t.schemaname = 'public'
GROUP BY t.tablename, t.rowsecurity
ORDER BY t.rowsecurity ASC, total_politicas ASC;
-- Tabelas com rls_ativado=false ou total_politicas=0 precisam de atencao
```
