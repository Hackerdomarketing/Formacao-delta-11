> REGISTRO: versão antiga das regras (Camada 2, versão 1), derrubada pelo Destruidor. Não vale; vale só o que está em fontes/.

# Contexto e leis (Delta-11 v7)

## O que cada papel carrega ao começar
| Papel | Carrega | Não carrega |
|---|---|---|
| Construtor | Página do seu papel (`papeis.md`) + Luz compactada (1 página) + brief (2–4 páginas) + o trecho do arquivo de estado anterior que lhe cabe | O manual inteiro, o quadro de tarefas, o histórico, as outras camadas, o plano das próximas |
| CRONOS | Página do seu papel + Luz + arquivos de estado das duas camadas anteriores + critério da camada atual | O próprio diário, o código, os relatórios longos (lê só o aviso curto de cada agente) |
| Revisor | Só o resultado montado | Brief, plano, autocrítica, contratos |
| Destruidor | Resultado montado + critério da camada + inimigo de fase | Como foi feito |
| Selador | Tudo da camada atual | As camadas anteriores além do arquivo de estado |
| Documentador | O que existe ao fim da camada | A história de como se chegou lá |

**Teto:** o que um Construtor lê ao começar cabe em ~6 páginas. Se o trabalho não cabe nisso, a tarefa é grande demais: divide-se a tarefa, não se aumenta a leitura.

## Produto ≠ história
- **Produto** (o que existe agora) vai no arquivo de estado da camada: até 500 tokens.
- **História** (como se chegou lá, tentativas, conversas) fica no registro do projeto. Ninguém a lê para trabalhar.

## Lei ≠ texto
- **Lei** é uma conferência que roda sozinha e trava quando algo está errado (um teste, um vigia, um script). Regra crítica só existe como lei.
- **Texto** é orientação para o agente. Se uma regra pode ser lei, ela vira lei e sai do texto. Se uma lição não cabe em lei nem em uma linha de texto, ela não vira regra.

## Duas famílias de leis
1. **Leis do produto** — nascem no esqueleto do projeto (Camadas 2 e 4) e rodam sem nenhum agente: a cada mudança, montar e rodar os testes (inclusive os de contrato); relato de erros em produção; alarmes; publicação automática com volta atrás.
2. **Leis do processo** — poucos vigias, só os que protegem um fruto. Cada uma tem **pulso**: um teste periódico provoca o que ela deveria travar e confere que travou; se não travou, avisa por outro canal.

## Um fato, um lugar
Cada regra está escrita em **um** documento destas regras; os outros só apontam para ela. Um vigia falha se o mesmo número ou a mesma regra aparecer em dois lugares com valores diferentes.

## Nenhum projeto nas regras
Nome, número ou caso de um projeto nunca entra nestes documentos. A lição vira regra genérica; a origem fica no histórico do Delta-11.