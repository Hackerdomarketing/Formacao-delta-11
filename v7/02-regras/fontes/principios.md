# Princípios (para quem mantém o Delta-11)

## Lei ≠ texto
Regra crítica vira lei: uma conferência que roda sozinha e trava. Ninguém precisa ler uma lei para obedecê-la. Há duas famílias: as leis do produto (construídas pelo BACK em cada produto) e as leis do processo (do próprio Delta-11). Cada lei tem pulso (definido em `territorios.md`). A tabela de uma lei descreve o que ela trava; isso é a conferência da regra, não a regra escrita de novo.

## Um fato, um lugar
O conteúdo de uma regra (condição, número, consequência) mora numa fonte só. Dizer quem faz algo, numa fronteira ("existe contra") ou numa lista de deveres, é referência, não repetição. As páginas dos papéis são montadas por `ferramentas/gerar-paginas.py`; a primeira linha de cada fonte de papel diz o que entra na página dela.

## O vigia das regras
`ferramentas/conferir-regras.py` roda a cada commit, a cada merge e a cada envio ao GitHub, sobre o que entra ou sobe, e `ferramentas/testar-vigia.py` é o pulso dele: planta cada quebra, exige que trave pelo motivo certo e confere que o gancho está instalado. Num clone novo, o gancho só vale depois de `git config core.hooksPath v7/02-regras/ferramentas/ganchos`. Confere as fontes, os modelos e os textos do motor que vão para os agentes (lugares, rotas, escolhas dos agentes, modelos e a porta de entrada); na Luz, nos arquivos de estado e no plano, só nomes e palavras proibidas. Ele trava: número com unidade fora de `valores.md` (também por extenso, em tabela ou com a unidade antes); trecho igual de `frase_repetida_palavras` palavras (entre fontes ou na mesma); nome de projeto em qualquer arquivo, com qualquer grafia ou número no lugar de letra; letra de outro alfabeto ou caractere invisível; palavra proibida, também com outras palavras comuns de empurrar o trabalho; página desatualizada, sem fonte, sem o núcleo, grande demais, citando arquivo que não está nela ou que estoura a leitura; fonte que nenhuma página inclui e que não é para quem mantém; arquivo fora do formato das fontes ou em outra codificação; qualquer arquivo fora dos lugares combinados (o plano, fontes/, modelos/ só com modelos .md, paginas/ só com as páginas dos papéis, ferramentas/ só com as ferramentas conhecidas, registro/ só com o aviso, e ao lado só o que é numerado das camadas); registro sem o aviso de que não vale; nome de valor que não existe, repetido em `valores.md` ou citado sem crase; fonte "para quem mantém" fora da lista combinada; a mesma fonte incluída em dobro.
O vigia pega o descuido honesto. Não pega a mesma regra dita com outras palavras, nem quem o engana de propósito (pular o gancho, alterar o próprio vigia): contra isso, o histórico do git e o Destruidor de cada rodada da Camada 2.

## Depois do Dia 7
A separação tende a voltar a se fundir sozinha. Continuam vivos: o Construtor contra a esteira; o produto contra o alarme; o ATLAS contra o pedido.

## Nenhum projeto nas regras
O Delta-11 e os projetos que ele constrói são coisas separadas (Luz do Delta-11). Os nomes que o vigia procura vêm do registro de projetos da máquina e de `~/.delta-11-nomes-de-projeto.txt`, nunca de dentro do Delta-11; sem nenhum dos dois, o vigia diz que não conferiu nomes.
