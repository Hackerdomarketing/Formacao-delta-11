# PROTOCOLO DE VALIDAÇÃO DE SCREENSHOTS

> **Aplicável a:** PIXEL, FRONT, FORM (qualquer agente que gere screenshots)
> **Criado em:** 2026-02-10
> **Origem:** Erro crítico na T-104 do projeto salvahacks

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
# ✅ Arquivos salvos em store-assets/screenshots/
```

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
1. Documente no arquivo de estado: "Screenshots validados visualmente"
2. ENTÃO marque tarefa como concluída

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

## EXEMPLO DE FALHA REAL (salvahacks T-104)

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
await page.screenshot({ path: 'screenshot.png' });

// Marca como concluído imediatamente
console.log('✅ Screenshot gerado!');
```

### ✅ CORRETO (o que fazer)

```javascript
// Gera screenshots
await page.screenshot({ path: 'screenshot.png' });

// Validação visual OBRIGATÓRIA
console.log('\n⚠️  VALIDAÇÃO VISUAL NECESSÁRIA');
console.log('ANTES de marcar como concluído:');
console.log('1. Abra: screenshot.png');
console.log('2. Verifique visualmente o conteúdo');
console.log('3. Confirme que tudo está correto\n');

// Pausa para inspeção (em modo interativo)
await page.pause(); // Ou aguardar confirmação manual
```

---

## INTEGRAÇÃO COM PROTOCOLO DE FINALIZAÇÃO

Quando a tarefa envolve screenshots, adicione ao Passo 3.5 (após validação de build, antes de marcar concluída):

```
3.5 — Validação de build (obrigatório para agentes que escrevem código)
3.6 — Validação visual de screenshots (obrigatório quando tarefa gera screenshots)
      Use Read tool para visualizar cada imagem
      Valide conteúdo, dados populados, renderização completa
      Só prossiga se TODOS os screenshots estiverem corretos
4 — Verifique se sua tarefa desbloqueia outro agente
...
```

---

## PADRÃO NO SISTEMA DE INTELIGÊNCIA PROGRESSIVA

Este protocolo foi capturado como padrão permanente:

**ID:** `gestao-projeto-ia_valida_o_visual_obrigat_ria_ap_s_captura_automatiz`
**Domínio:** gestao-projeto-ia
**Tipo:** situação
**Localização:** `~/.claude/inteligencia/dominios/gestao-projeto-ia/situacoes/`

---

**Formação Δ-11 — Versão 3.2**
**Protocolo adicionado em:** 2026-02-10
