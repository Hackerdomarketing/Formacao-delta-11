# PROTOCOLO DE VALIDAÇÃO DE SCREENSHOTS

> **Aplicável a:** PIXEL, FRONT, FORM e qualquer agente ou sub-agente que gere screenshots (inclusive verify-app, fresh-reviewer e qa-ui-tandem)
> **Criado em:** 2026-02-10 · **Atualizado em:** 2026-10-14 (v6.3)
> **Origem:** Erro crítico em tarefa de validação visual de projeto real

---

## CONTEXTO

Screenshots gerados automaticamente (Puppeteer, Playwright, Selenium) podem ter:
- ✅ Dimensões corretas
- ✅ Formato correto (PNG)
- ✅ Tamanho de arquivo razoável
- ❌ **Conteúdo completamente errado ou vazio**

**Validação técnica ≠ Validação de conteúdo**

---

## PROTOCOLO OBRIGATÓRIO

Quando gerar screenshots automaticamente para qualquer finalidade (Chrome Web Store, App Store, documentação, marketing, testes visuais):

### Passo 1: Geração Automática
```bash
# Script executa sem erro
node auto-screenshots.js
# ✅ 5 arquivos PNG gerados
# ✅ Dimensões verificadas: 1280x800px
# ✅ Arquivos salvos em .delta-11/evidencias/screenshots/AAAA-MM-DD/
```

**Onde salvar (Regra 16):** toda screenshot de evidência vai para `.delta-11/evidencias/screenshots/AAAA-MM-DD/` (a data do dia da captura). Se a tarefa for gerar imagens para uma loja (Chrome Web Store, App Store), a versão final aprovada é copiada depois para a pasta que a loja exige no projeto; a evidência continua em `evidencias/`.

### Passo 2: **VALIDAÇÃO VISUAL OBRIGATÓRIA**

**ANTES de marcar tarefa como concluída**, execute:

```
1. Use Read tool para visualizar CADA screenshot individualmente
2. Para CADA imagem, valide:
   □ Conteúdo correto aparece?
   □ Dados foram populados?
   □ UI está completamente renderizada?
   □ Elementos esperados estão visíveis?
   □ Sem elementos cortados/fora de vista?
   □ Cores/tema aplicados corretamente?
   □ Texto legível?
   □ Sem placeholders vazios?
```

### Passo 3: Correção ou Aprovação

**SE algum problema for encontrado:**
1. Liste TODOS os problemas de TODOS os screenshots
2. Corrija os problemas (script, timing, seletores, dados)
3. Regere os screenshots
4. **Repita Passo 2** (validação visual)

**SE todos os screenshots estiverem corretos:**
1. Registre no seu `-produto.md`: "Screenshots validados visualmente" + o caminho da pasta em `evidencias/screenshots/AAAA-MM-DD/`
2. ENTÃO siga a finalização (build-validator, contract-tester, aviso ao CRONOS)

---

## PROBLEMAS COMUNS (e por que validação visual é crítica)

### 1. Dados não populados
- **Sintoma:** Screenshot mostra interface vazia ou com placeholders
- **Causa:** `chrome.storage.local` não foi populado ou timing errado
- **Detecção:** Só validação visual detecta

### 2. Seletor CSS errado
- **Sintoma:** Screenshot captura elemento diferente do esperado
- **Causa:** `.column-header button` capturou dropdown ao invés de modal
- **Detecção:** Script não dá erro, mas conteúdo está errado

### 3. Timing issues
- **Sintoma:** Screenshot capturado antes do render completo
- **Causa:** `await wait(1000)` insuficiente ou animações não terminaram
- **Detecção:** Elementos aparecem cortados ou faltando

### 4. Extensão não carregada
- **Sintoma:** Screenshot mostra página em branco ou chrome://newtab padrão
- **Causa:** `--load-extension` não funcionou ou extensão com erro
- **Detecção:** Só olhando a imagem

### 5. Tema não aplicado
- **Sintoma:** Screenshot mostra tema errado (ex: escuro quando deveria ser claro)
- **Causa:** Toggle de tema não funcionou ou estado não persistiu
- **Detecção:** Cores erradas, só validação visual detecta

---

## EXEMPLO DE FALHA REAL

```
Script executou: ✅
Dimensões corretas: ✅ (1280x800px)
Arquivos salvos: ✅ (5 arquivos PNG)
Tamanho razoável: ✅ (30-350KB)

❌ Screenshot 1: Extensão VAZIA (só 1 coluna com Google)
❌ Screenshot 2: Busca sem resultados
❌ Screenshot 3: Sidebar MINÚSCULA (invisível)
❌ Screenshot 4: Dropdown ao invés de modal (elemento errado)
❌ Screenshot 5: COMPLETAMENTE ESCURO (nada visível)

Impacto se submetido: Rejeição imediata da Chrome Web Store
```

---

## REGRA MNEMÔNICA

```
📸 Screenshot = 🎬 Cinema

Você não aprovaria um filme checando apenas:
- ✅ Duração: 90 minutos (correto)
- ✅ Resolução: 4K (correto)
- ✅ Arquivo: .mp4 (correto)
- ❌ MAS sem assistir o filme

Screenshot é igual: precisa VER o conteúdo.
```

---

## CHECKLIST DE VALIDAÇÃO VISUAL

```
Para cada screenshot gerado:

Visual Básico:
□ A imagem carregou completamente?
□ Resolução está nítida (não borrada)?
□ Cores corretas (não muito escuro/claro)?

Conteúdo Esperado:
□ Elementos principais estão visíveis?
□ Dados de exemplo foram populados?
□ Texto está legível?
□ Ícones/imagens carregaram?

Layout e Composição:
□ Elementos estão no lugar certo?
□ Sem cortes inesperados?
□ Espaçamento correto?
□ Sem sobreposições estranhas?

Contexto:
□ Screenshot representa o que deveria?
□ Útil para quem vai ver (usuário final, Google)?
□ Não tem dados sensíveis/temporários?
```

---

## IMPLEMENTAÇÃO NO CÓDIGO

### ❌ ERRADO (o que NÃO fazer)

```javascript
// Gera screenshots
await page.screenshot({ path: '.delta-11/evidencias/screenshots/2026-10-14/home.png' });

// Marca como concluído imediatamente, sem olhar a imagem
console.log('✅ Screenshot gerado!');
```

### ✅ CORRETO (o que fazer)

```javascript
// Gera screenshots na pasta de evidências do dia
const screenshotPath = '.delta-11/evidencias/screenshots/2026-10-14/home.png';
await page.screenshot({ path: screenshotPath });

// O script NÃO pausa nem espera humano: ele só lista o que precisa ser olhado
console.log(`VALIDAÇÃO VISUAL NECESSÁRIA: ${screenshotPath}`);

// Em seguida, o PRÓPRIO AGENTE abre cada imagem com a ferramenta Read,
// confere o checklist acima e só então segue para a finalização.
```

---

## INTEGRAÇÃO COM PROTOCOLO DE FINALIZAÇÃO

Quando a tarefa envolve screenshots, o Passo 3.5.1 entra logo depois do build-validator. A sequência completa da finalização fica assim:

```
1a    — Atualizar [NOME]-produto.md (com a linha "autocritica: <caminho>")
1b    — Acrescentar ao [NOME]-historia.md
3.4   — Autocrítica (2 paradas) em .delta-11/logs/autocritica/
3.5   — build-validator
3.5.1 — Validação visual de screenshots (obrigatório quando a tarefa gera screenshots)
        Use a ferramenta Read para ver cada imagem em .delta-11/evidencias/screenshots/AAAA-MM-DD/
        Valide conteúdo, dados populados, renderização completa
        Só prossiga se TODAS as screenshots estiverem corretas
3.7   — contract-tester (gera E roda os testes de contrato do que mudou)
3.8   — SendMessage ao CRONOS pedindo a revisão do SHIELD
3.9   — Liberar as travas
```

---

## LIÇÃO ENTRE PROJETOS

Esta é uma lição que vale para qualquer projeto. A partir da v6.3, lições assim ficam em `~/.delta-11/aprendizados-entre-projetos.md` (escrito pelo CRONOS, lido pelo ATLAS nas Fases 0 e 2):

```markdown
## [2026-02-10] [projeto de extensão do Chrome] — Validação visual obrigatória após captura automatizada
- Situação: screenshots geradas por script (Puppeteer, Playwright, Selenium)
- Faça: abrir cada imagem com a ferramenta Read e conferir o checklist deste protocolo
- Nunca faça: aprovar só por dimensão, formato ou tamanho do arquivo
- Por quê: o script roda sem erro e a imagem sai vazia ou errada
- Origem: protocolo validacao-screenshots.md
```

---

**Formação Δ-11 — v6.3 (2026-10-14)**
**Protocolo adicionado em:** 2026-02-10
