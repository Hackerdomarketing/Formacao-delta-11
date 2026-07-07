# Rubrica de Avaliação — Golden Baselines Δ-11

A mesma régua para toda execução, de qualquer versão. Nota final de 0 a 100.

## As 5 dimensões (pesos)

| Dimensão | Peso | O que mede |
|---|---|---|
| **Corretude** | 30 | O gabarito da tarefa foi cumprido? (checklist da própria tarefa, item a item) |
| **Segurança** | 25 | Validação no servidor, `.max()` em strings, auth verificada na rota, RLS, sem segredo exposto |
| **Convenções Δ-11** | 20 | Limites estruturais (regras-codigo §8), idioma (nomes EN / conteúdo PT — §9), zoneamento de arquivos |
| **Processo** | 15 | Autocrítica com bugs/casos CONCRETOS? Casos extremos viraram teste? Cadeia de sub-agentes rodou? |
| **Legibilidade** | 10 | Nomes descritivos sem abreviação, sem código morto, sem hardcoded que deveria ser config |

## Como pontuar cada dimensão

- **100%** — todos os itens do checklist da dimensão cumpridos
- **70%** — falhas menores que não quebram funcionamento nem segurança
- **40%** — falha relevante (item do gabarito faltando, limite estourado sem justificativa)
- **0%** — falha grave (vulnerabilidade, gabarito ignorado, processo pulado)

`Nota final = Σ (percentual da dimensão × peso)`

## Regra do veto (importada do padrão de 4 dimensões)

**Segurança abaixo de 40% → nota final máxima = 39**, independente das outras dimensões. Código bonito e inseguro é reprovado.

## Formato do resultado (salvar junto da execução)

```markdown
# Avaliação — [tarefa] · versão Δ-11 [X.X] · AAAA-MM-DD
- Corretude: [%] × 30 = [pts] — [1 linha de evidência]
- Segurança: [%] × 25 = [pts] — [1 linha]
- Convenções: [%] × 20 = [pts] — [1 linha]
- Processo: [%] × 15 = [pts] — [1 linha]
- Legibilidade: [%] × 10 = [pts] — [1 linha]
**NOTA FINAL: [0-100]** (anterior da mesma tarefa: [nota] na versão [X.X])
Veredito: melhorou | manteve | REGREDIU
Observações: [o que mudou de comportamento entre versões — 2-3 linhas]
```
