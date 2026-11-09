# Territórios

| Território | Responsável | Inclui |
|---|---|---|
| Dados | VAULT | o banco na estrutura combinada: tabelas, campos, migrações com caminho de volta, quem lê cada dado, backup e recuperação |
| Servidor | ENGINE | rotas, lógica de negócio, login e sessão, quem cria, muda ou apaga cada coisa, integrações com serviços de fora |
| Estrutura da tela | FRONT | quais telas existem, áreas e colunas, navegação, componentes que se repetem, textos fixos |
| Aparência | PIXEL | cor, tipografia, espaçamento, tamanho, movimento, temas (inclusive nos formulários e na mensagem de erro) |
| Formulários | FORM | campos, o que cada um aceita, o texto das mensagens de erro, o envio e a resposta ao envio |
| Leis do produto | BACK | os comandos da esteira, dependências e montagem, o teste de que cada serviço de fora responde, publicação com volta atrás, alarmes, canal de avisos, contador de intervenções e de padrões de uso, a estrutura do cofre |
| Contratos, pulsos e provas | SHIELD | testes de contrato entre as partes, o pulso de cada lei do produto (o teste que provoca o que ela trava), teste de ponta a ponta do coração e de cada funcionalidade, a medição do teste supremo |

- A estrutura combinada muda quando entra uma tabela, relação ou parte que ela não prevê; um campo novo numa tabela que existe não a muda.
- Duas partes precisam da mesma coisa: o responsável pelo território dela faz; a outra recebe um brief que depende disso.
- Arquivo fora de qualquer território é do BACK (montagem).
- Segredos só moram no cofre, preenchido pelo ATLAS; a estrutura do cofre (BACK) os leva, pelo nome, aos lugares onde o produto roda (inclusive o `.env` que ela gera aqui); o código os chama pelo nome.
- O SCOUT é o único que corrige em qualquer território, e só um erro em produção.
- **Exceção, as candidatas do coração (Camada 3):** vários agentes do mesmo território, cada um na sua cópia isolada, com a linha dentro dela; as que não forem escolhidas são descartadas sem entrar.
- **Fundamentos:** segurança é do ENGINE e do VAULT (Camadas 3 e 6); privacidade dos dados e o registro de quem fez o quê, do VAULT e do ENGINE (6); desempenho, do ENGINE (4); acessibilidade, do FRONT, do PIXEL e do FORM (o mínimo no coração; completa na 5).
