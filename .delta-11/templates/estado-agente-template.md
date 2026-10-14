# ⚠️ LEGADO — `[NOME]-estado.md` (não use mais)

> **v6.3 (2026-10-14) — D8.** O arquivo único de estado `memoria/[NOME]-estado.md` foi substituído por DOIS
> arquivos:
>
> | Arquivo | O que guarda | Limite | Modelo |
> |---|---|---|---|
> | `memoria/[NOME]-produto.md` | O que EXISTE agora (lido pela próxima fase e pelo cold-start-tester) | ≤ 500 tokens para executores; ATLAS e CRONOS isentos | `templates/estado-produto-template.md` |
> | `memoria/[NOME]-historia.md` | Diário: tentativas, decisões descartadas, notas para o eu do futuro | sem limite | `templates/estado-historia-template.md` |
>
> **Regras:**
> - NUNCA crie nem escreva um `[NOME]-estado.md` novo.
> - Se um projeto antigo ainda tiver `[NOME]-estado.md`, ele pode ser LIDO uma vez para migrar o conteúdo:
>   o que descreve o sistema vai para o `-produto.md`; o resto (sessões, erros, notas) vai para o `-historia.md`.
>   Depois disso, ninguém mais o atualiza.
> - Este arquivo continua na pasta `templates/` só para quem procurar o nome antigo encontrar o caminho novo.

## Mapa do formato antigo para o novo

| Seção antiga (`-estado.md`) | Vai para |
|---|---|
| ÚLTIMA ATUALIZAÇÃO / sessão | `-historia.md` (cabeçalho de cada entrada do diário) |
| O QUE FIZ NA ÚLTIMA SESSÃO | `-historia.md` |
| ARQUIVOS QUE CRIEI OU ALTEREI | `-produto.md` → "COMO ESTÁ ESTRUTURADO" (só o que existe agora) |
| DECISÕES QUE TOMEI | `-produto.md` → "PORQUÊS-CHAVE" (até 3); o resto no `-historia.md` |
| ONDE PAREI / próxima tarefa | `-produto.md` → "PRÓXIMA TAREFA" |
| ERROS ENCONTRADOS | `-historia.md` → "Tentativas que não funcionaram" |
| NOTAS PARA A PRÓXIMA SESSÃO | `-historia.md` → "Notas para meu eu-do-futuro" |
