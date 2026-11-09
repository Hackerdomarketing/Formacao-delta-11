# Leis que todo produto tem (o BACK as constrói; o pulso de cada uma é do SHIELD)

Toda lei do produto roda onde o produto roda, ou num serviço que roda sozinho; nunca depende do Claude, de uma sessão aberta nem do computador de quem construiu. O lugar sai do guia dos tipos de software. A lei que precisa chegar ao ATLAS deixa um arquivo no repositório: o alarme, em `.delta-11/alarmes/`; os padrões de uso e o contador de intervenções, em `.delta-11/pedidos-das-leis/` (o ATLAS os trata como pedido).

| Lei | O que trava | Camada |
|---|---|---|
| Esteira | Mudança que não monta, teste vermelho ou choque com a mudança de outro, conferida sobre o que já entrou mais só ela; mudança juntada fora da esteira (a automação do repositório confere de novo cada envio); teste ou publicação que roda fora da caixa do produto do motor | 2 |
| Testes não somem | O número de testes caiu, ou um teste que já existe foi alterado, afrouxado ou marcado para pular, sem o aval do SHIELD (`Aval: <teste>` na linha dele) | 2 |
| Territórios | Mudança fora da pasta do território de quem a fez (com a exceção que a tabela de territórios dá) | 2 |
| Segredo fora do código | Senha ou chave escrita no código em vez de chamada do cofre | 2 |
| Ambiente do dono | A esteira publica cada mudança no ambiente do dono; trava publicação ao público antes do selo da Camada 4 (produto já público: vai ao público o que passou no ambiente do dono) | 2 |
| Alarme e relato de erros | Erro em produção, ou esteira fora do ar, que não acorda o SCOUT nem chega ao canal de avisos; o alarme repete enquanto o erro continuar | 4 |
| Volta atrás | Versão publicada quebrada que continua no ar; migração sem caminho de volta | 4 |
| Registro de eventos | Evento importante que não fica registrado de forma consultável | 4 |
| Sinais de saúde | Lentidão, erros ou uso de recursos fora do normal, ou tendência de piora, sem aviso; conferência declarada (o que cada máquina confere por dia, semana e mês) que não rodou; painel de saúde que não se lê em `painel_leitura_max` | 4 |
| Contador de intervenções | Conserto feito à mão ou chamada ao dono, depois do Dia 7, sem entrar na conta do mês | 7 |
| Padrões de uso | O que o uso real mostra não é juntado, ou chega a `padroes_min` sem abrir o pedido ao ATLAS | 6 |
| Pulso | Uma lei desta tabela sem pulso, com pulso que deixou passar, ou que parou de dar sinal de vida sem avisar por outro canal | 2 e 4 |

**O SCOUT na automação do produto** (o alarme o liga, fora deste computador): bubblewrap e socat (no Ubuntu 24.04 ou mais novo, com o perfil do AppArmor da documentação); `claude -p "<o aviso>" --agent scout "--allowedTools=<permissions.allow, com vírgulas>,Bash"`; sem `sandbox-exec`, a caixa roda solta (máquina descartável).
