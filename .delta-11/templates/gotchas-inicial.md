# Gotchas do Projeto

> Mais novo no topo. CRONOS: injete os da zona relevante em cada mini-plano.
> Arquivo criado pelo `novo-projeto.sh` no dia 1 do projeto (v5.4 — Estágio 0, F5).
> Quem escreve aqui: SCOUT (após correção), SHIELD (2ª reprovação do mesmo padrão),
> qualquer agente que perdeu mais de 30 min numa armadilha não documentada.

## G-001: Supabase retorna lista vazia sem erro quando RLS bloqueia
- **Data:** 2026-07-07 · **Registrado por:** exemplo · **Zona:** API
- **EVITE:** tratar `data: []` como "não existem registros" sem verificar política RLS
- **PORQUE:** query com RLS ativo e política ausente retorna vazio SILENCIOSAMENTE — parece bug de dados, é permissão
- **FAÇA:** ao receber vazio inesperado, rodar a mesma query com service role em ambiente dev; se retornar dados, o problema é política RLS
- **Ocorrências:** 1