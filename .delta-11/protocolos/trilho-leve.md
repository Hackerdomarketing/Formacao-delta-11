# TRILHO LEVE — ajustes só visuais (v6.4.1, 2026-10-15)

> Decisão do comandante. Origem: no Selo do salvahacks, uma troca de 3 linhas de estilo levou ~30 min e 6 sessões
> de agente (worktree, autocrítica, 2 validadores, SHIELD recompilando e rodando ~850 testes, QA com fotos pela
> terceira vez). O tamanho do processo tem que acompanhar o tamanho do RISCO.

## Quando usar

Só para mudança **só visual**:
- estilos (`.css`, `.scss`, `.less`...): cor, tamanho, espaçamento, largura, fonte, borda, sombra;
- imagens, ícones e fontes (`.png`, `.svg`, `.woff2`...);
- HTML **sem** `<script>` e sem `onclick=`/`on...=` novos (trocar uma classe, um texto, a ordem de dois elementos);
- textos em `.md`.

**Não é trilho leve** (vai para o trilho completo, com SHIELD): qualquer mudança em JavaScript/TypeScript, regras do
banco, testes, contratos, configuração, dados, autenticação — mesmo que o objetivo seja visual (ex.: uma dica flutuante
que precisa de JS). Na dúvida, trilho completo.

## Os riscos e quem cuida de cada um

| Risco | Quem cuida |
|---|---|
| "Ficou bonito? Era isso que eu queria?" | O **comandante**, ao ver o resultado |
| "É mesmo só visual, ou mexeu em lógica?" | O vigia **`trilho-leve.py`**, no merge (automático) |
| "Quebrou outra tela?" | O **executor**: fotos das telas principais, antes e depois, nos 2 temas |

## Passo a passo

1. **CRONOS agrupa.** Achados visuais da mesma área viram UMA tarefa (lote), marcada `[AJUSTE]` no kanban:
   `**T-271** — [AJUSTE] colunas com a mesma largura + fonte da barrinha | Agente: FRONT`
2. **CRONOS dispara UM executor** (FRONT ou PIXEL) em worktree, com brief curto. Sem build-validator, sem
   contract-tester, sem SHIELD.
3. **Executor:**
   - faz a mudança;
   - compila **uma vez**;
   - fotografa as **telas principais** (não só a tocada) **antes e depois**, nos **2 temas**, em
     `.delta-11/evidencias/screenshots/AAAA-MM-DD/`, e **lê** as fotos;
   - grava o `-produto.md` (o que mudou + onde estão as fotos + 3 linhas de autocrítica) e avisa o CRONOS.
4. **CRONOS faz o merge com a marca na mensagem:**
   `git merge --no-ff <branch-da-worktree> -m "[AJUSTE] T-271 <resumo>"`
   O vigia `trilho-leve.py` confere os arquivos da branch:
   - só visuais → libera e grava `VISUAL-OK T-271` no activity-log;
   - algum arquivo não visual → **bloqueia**: tirar o `[AJUSTE]` da tarefa e seguir o trilho completo.
5. **Comandante confere** (recarrega a extensão / abre a página). O ATLAS ou o CRONOS mostram as fotos das outras
   telas, com as diferenças.
6. **Decisão do comandante, gravada no activity-log** pelo ATLAS ou pelo CRONOS — SÓ depois de o comandante dizer:
   - `- [AAAA-MM-DDTHH:MM:SSZ] [COMANDANTE] APROVADO T-271`
   - ou `- [AAAA-MM-DDTHH:MM:SSZ] [COMANDANTE] REPROVADO T-271 <o que ele pediu>` → nova rodada no mesmo trilho.
   **Nunca** gravar `[COMANDANTE] APROVADO` sem a palavra dele na conversa.
7. **CRONOS conclui no kanban.** O vigia `shield-aprovado.py` aceita a conclusão de `[AJUSTE]` com as duas provas
   (`VISUAL-OK` + `[COMANDANTE] APROVADO`, dentro da janela de `janela_horas`); o `forca-despacho.py` não exige
   validadores para `[AJUSTE]`.

## Custo

Trilho completo: ~6 sessões de agente por achado. Trilho leve: 2 (CRONOS + 1 executor) por LOTE de achados.
