# O contrato da esteira (a esteira é do motor; o BACK escreve só `esteira-comandos.txt`; o SHIELD dá o teste vermelho plantado)

A `esteira` da raiz vem do instalador, provada pelo motor; ninguém do produto a muda (defeito: achado para o Delta-11); roda a do último commit.

**Os comandos do produto,** em `esteira-comandos.txt`, um por linha: `testar:` (todos os testes; 0 só se passam), `testes:` (os padrões dos testes: `tests/ *.test.js`) e, opcionais, `instalar:`, `montar:`, `vermelho:` (o sentinela, só ou com os testes; ele falha só com `$DELTA11_VERMELHO`, dizendo-a), `publicar:`, `fluxo-principal:`; num app de Mac, `ambiente:` (onde grava, em `~/Applications/` ou `~/Library/`), `app:` e `atalho:`. Sem o arquivo, `testar:` ou `testes:`, `RECUSOU`.

**Como se chama:** na raiz, sozinha na linha:
- `sh esteira <nome-do-agente> <arquivos>`;
- a candidata escolhida: `sh esteira <nome> --copia <cópia> --descartar <cópias das outras>` (só `.claude/worktrees/<cópia>`);
- a entrega conjunta: `sh esteira <um>,<outro> <arquivos>`;
- o remoto: `sh esteira back --remoto <endereço>`.

Na tela, por último `ENTROU` ou `RECUSOU: <motivo, com a linha da falha>`; o relato em `.delta-11/esteira/`.

**Uma mudança por vez:**
1. Cada arquivo é do território de quem entrega (`.delta-11/regras/enderecos.txt`; fora de todos, do BACK; sem o arquivo, todo o código, `.gitignore` inclusive, de qualquer Construtor); na conjunta, cada nome lista os seus em `Entrego junto:` na própria linha, numa camada aberta. O SCOUT entrega sozinho, em qualquer um, e só ele em `.delta-11/alarmes/`; o resto de `.delta-11/`, `.claude/` e a `esteira` são do motor. A candidata leva as dependências: só arquivo novo numa pasta fora de todo território. Apagar é entregar o arquivo apagado; no Parar (`Parar do dono: <data>` na abertura da Camada 2 aberta), o BACK apaga em qualquer um, testes inclusive, sem montar nem testar.
2. Traz o remoto: avanço simples entra; o daqui só em `.delta-11/`, juntado por cima; código dos dois lados, choque ou arquivo do remoto pela metade aqui: `RECUSOU` (ao ARQUITETO).
3. Monta, numa cópia limpa em `$TMPDIR`, o último commit mais esses arquivos, com o `.env`; sem `espaco_livre_min`, `RECUSOU`.
4. Roda ali `instalar`, `montar`, `testar`, `vermelho` (sai diferente de 0, com a marca) e, sem `publicar:`, `fluxo-principal`, pela caixa do produto. Pede `Aval: <teste>` na linha do SHIELD (sem `enderecos.txt`, do Revisor) o teste apagado, ou mudado tirando mais do que põe, pondo `.skip`, mexendo numa linha que confere (assert, expect, XCTAssert) ou comentando-a; mudar um comando (fora `publicar:`, `ambiente:`, `app:`, `atalho:`) ou tirar padrão de `testes:` pede `Aval: esteira-comandos.txt` (no Parar, a abertura é o aval; na volta atrás do SCOUT, a versão reposta).
5. Passou: commit com a linha final `Esteira: entrou`; avança o ramo (outro entrou: refaz 3 e 4; no mesmo arquivo: `RECUSOU`); põe na pasta o que entrou; traz as linhas das cópias de candidatas para `.delta-11/quadro/<X>/candidatas/` e as apaga; envia ao remoto; roda `publicar` e depois `fluxo-principal` pela caixa, com o cofre, sem `.delta-11/`, `.claude/`, `.env` e `.git/` (falha ali é `ALERTA`).
6. Recusou: nada entra; a mudança fica na pasta. Lei nenhuma se desliga com o app do dono aberto.

**Na automação do repositório** (`sh esteira --automacao <antes>..<depois>`; ao ligar o remoto, a esteira diz o que o BACK copia) recusa commit do produto sem `Esteira: entrou` (junção e `Delta-11: instalado` não contam) ou que não passa nos testes.
