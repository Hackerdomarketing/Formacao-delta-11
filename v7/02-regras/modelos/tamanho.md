# O tamanho do produto e o caminho (o ARQUITETO mede)

**Quando:** ao abrir a Camada 1, pela entrada do dono; com a Luz selada, de novo, pela Luz, que diz o tamanho. Um pedido que acende um sinal novo faz medir de novo: o produto segue pelo caminho maior dali em diante, sem refazer o que já funciona.

## Os sinais (sim ou não)
| Sinal | Sim quando |
|---|---|
| Quem usa | outras pessoas além do dono usam o produto |
| Dinheiro | cobra, paga ou mexe em dinheiro de alguém |
| Dados de outros | guarda dado pessoal de outras pessoas |
| Ação sem volta | apaga dados de outras pessoas ou em massa, envia em massa ou publica em nome do dono (o dono apagar um item dele, confirmando, não conta) |
| Partes | mais de `partes_pequeno_max` |
| De fora | depende de serviço de fora (conta, pagamento, outro sistema) |
| Sempre no ar | precisa rodar sem parar fora do computador do dono |

**Pequeno:** nenhum sinal. **Médio:** até `sinais_medio_max`, sem Dinheiro nem Ação sem volta. **Grande:** Dinheiro, Ação sem volta, ou mais de `sinais_medio_max`.

## Os caminhos
| | Pequeno | Médio | Grande |
|---|---|---|---|
| Blocos (a pasta do quadro) | Luz, Camada 1 (`camada-1`) → Coração, 2 e 3 (`camada-2`) → Pronto, 4 a 7 (`camada-7`) | Os do pequeno; o último se chama O resto | As 7 camadas, uma a uma |
| Quem constrói | Um Construtor só, o do território com mais do coração, com todo o código (sem `enderecos.txt`) | Até `paralelo_max` ao mesmo tempo | Até `paralelo_max` ao mesmo tempo |
| Quem confere (passo 5) | O Revisor, no Coração e no Pronto; nada do Destruidor | Quem os testes do fruto das camadas do bloco pedem, no Coração e no Resto | Quem o teste do fruto da camada pede |
| Candidatas do coração | Não | Não | Sim |
| Limite de tempo | `pequeno_primeira_versao_max` até a primeira versão; `pequeno_pronto_max` até o fim | `medio_primeira_versao_max`; `medio_pronto_max` | `grande_camada_max` por camada |

## Em todo caminho
- O que só o dono dá é pedido antes de construir (o modelo da Luz).
- A esteira é a do motor (o guia dos tipos de software).
- Nunca se corta: voltar atrás com os dados junto, o teste do fluxo principal na esteira, o registro de erros, o dono confirmando ação sem volta.
- O limite conta o trabalho do time, que o relógio do motor mede por quadro; a espera pelo dono e pelo tempo não conta. A primeira versão é o primeiro `ENTROU` com o teste do fluxo principal passando; o fim, o selo do último bloco.
- O freio do tempo (o CRONOS te chama): meça de novo e escreva na abertura o limite novo (o tamanho mudou: o do caminho maior; não mudou: o mesmo do bloco, contado de agora, e anote o defeito para quem mantém o Delta-11); devolva o porquê.
- Camada aberta quando o caminho muda (a medida nova, ou o motor atualizado com camada aberta, que o aviso de abertura conta): ela vira uma reabertura no bloco do caminho novo (`<pasta do bloco>-r<n>`); o que já entrou fica, e o que estava pela metade (mudança sem entrega, entrega sem fim) volta como brief. A abertura da nova traz, para o CRONOS, a linha `Substitui: <pasta antiga>: marque o quadro dela encerrado (substituída por <nova>) antes de tudo e não volte a ela` (a marca é `REABRA: <nova>`, porque a antiga está aberta). O motor atualizado sem mudar o caminho não abre pasta nova: o que estava pela metade volta como brief na própria camada. Nos dois casos, a abertura diz também `Motor atualizado: tratado`, e o aviso de abertura para de falar da atualização.
- A abertura de cada bloco dá o limite que sobra: o do produto menos o trabalho dos blocos já selados (o relógio do motor te dá o de cada quadro).

## A abertura de cada bloco diz
O tamanho e o bloco; as camadas que ele junta e o critério de cada uma; quantos Construtores (no pequeno, qual); quem confere no passo 5; o limite de tempo; o momento do dono no fim dele (o 2, no fim do Coração; o 3, no fim do último bloco).
