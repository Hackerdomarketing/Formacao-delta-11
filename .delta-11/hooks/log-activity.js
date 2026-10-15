#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 v6.3 — Hook PostToolUse: registrar atividade
// ═══════════════════════════════════════════════════════════════
// Registro (templates/settings-hooks.json):
//   PostToolUse  matcher "Write|Edit|Bash"  →  node "$CLAUDE_PROJECT_DIR/.delta-11/hooks/log-activity.js"
//
// Dispara DEPOIS de cada Write/Edit/Bash e acrescenta UMA linha no
// `.delta-11/activity-log.md` da PASTA PRINCIPAL do projeto (D25:
// pai do `git rev-parse --git-common-dir`; senão CLAUDE_PROJECT_DIR;
// senão o cwd) — também quando o agente trabalha numa worktree.
//
// Formato único (D25, C-032), hora sempre em UTC:
//   - [AAAA-MM-DDTHH:MM:SSZ] [log-activity] [AGENTE] Edit src/a.ts (T-012) — "trecho..."
// (antes: tabela markdown com hora local e data UTC, misturada com as
// linhas soltas dos outros vigias.)
//
// AGENTE: nome Delta-11 pelo vínculo agent_id/session_id gravado pelo
// heartbeat (`ativacoes/agentes-sessao.json`) ou pelo agent_type;
// senão "PRINCIPAL" (sessão principal) ou "SUBAGENTE-<agent_type>".
//
// Nunca bloqueia (sai com 0). Erro interno vira linha "ERRO INTERNO".
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const NOME_DO_HOOK = 'log-activity';
const NOMES_DELTA11 = new Set(['ATLAS', 'CRONOS', 'FRONT', 'PIXEL', 'FORM', 'BACK',
  'ENGINE', 'VAULT', 'SHIELD', 'SCOUT']);
const CABECALHO =
  '# Activity Log — Delta-11\n\n' +
  '> Gerado automaticamente pelos vigias (hooks). Não editar à mão.\n' +
  '> Formato de cada linha (v6.3): `- [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem` — hora em UTC.\n\n';

function git(pasta, args) {
  try {
    return execFileSync('git', ['-C', pasta, ...args], {
      encoding: 'utf-8', timeout: 3000, stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return '';
  }
}

function caminhoReal(p) {
  const absoluto = path.resolve(p);
  let existente = absoluto;
  const resto = [];
  while (!fs.existsSync(existente)) {
    const pai = path.dirname(existente);
    if (pai === existente) return absoluto;
    resto.unshift(path.basename(existente));
    existente = pai;
  }
  try {
    return path.join(fs.realpathSync(existente), ...resto);
  } catch {
    return absoluto;
  }
}

function raizPrincipal(cwd) {
  const candidatos = [];
  const comum = git(cwd, ['rev-parse', '--path-format=absolute', '--git-common-dir']);
  if (comum) candidatos.push(path.dirname(path.normalize(comum)));
  if (process.env.CLAUDE_PROJECT_DIR) candidatos.push(process.env.CLAUDE_PROJECT_DIR);
  candidatos.push(cwd);
  for (const c of candidatos) {
    if (c && fs.existsSync(path.join(c, '.delta-11'))) return caminhoReal(c);
  }
  return null;
}

function lerVinculos(raiz) {
  try {
    const dados = JSON.parse(fs.readFileSync(
      path.join(raiz, '.delta-11', 'ativacoes', 'agentes-sessao.json'), 'utf-8'));
    return (dados && typeof dados.chaves === 'object' && dados.chaves) || {};
  } catch {
    return {};
  }
}

function chaveDoEvento(ev) {
  return ev.agent_id ? `agente:${ev.agent_id}` : `principal:${ev.session_id || 'desconhecida'}`;
}

function identificarAgente(ev, raiz) {
  const tipo = String(ev.agent_type || '').trim().toUpperCase();
  if (NOMES_DELTA11.has(tipo)) return tipo;
  const vinculo = lerVinculos(raiz)[chaveDoEvento(ev)];
  return (vinculo && vinculo.agente) || '';
}

function agoraIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function umaLinha(texto, limite) {
  const limpo = String(texto || '').replace(/\s+/g, ' ').trim();
  return limpo.length > limite ? limpo.substring(0, limite) + '…' : limpo;
}

function acrescentarNoLog(raiz, agente, mensagem) {
  const caminho = path.join(raiz, '.delta-11', 'activity-log.md');
  try {
    fs.writeFileSync(caminho, CABECALHO, { encoding: 'utf-8', flag: 'wx' }); // só se não existe
  } catch {
    // já existe (ou outro vigia criou ao mesmo tempo)
  }
  // Uma linha pequena com O_APPEND: não se mistura com linhas de outros vigias.
  fs.appendFileSync(caminho, `- [${agoraIso()}] [${NOME_DO_HOOK}] [${agente}] ${umaLinha(mensagem, 400)}\n`, 'utf-8');
}

function tarefaDoAgente(raiz, agente) {
  if (!agente) return '';
  const pasta = path.join(raiz, '.delta-11', 'locks');
  let entradas = [];
  try {
    entradas = fs.readdirSync(pasta).filter((f) => f.endsWith('.lock'));
  } catch {
    return '';
  }
  for (const entrada of entradas) {
    const caminho = path.join(pasta, entrada);
    try {
      const stats = fs.statSync(caminho);
      const meta = stats.isDirectory()
        ? (fs.existsSync(path.join(caminho, 'meta')) ? fs.readFileSync(path.join(caminho, 'meta'), 'utf-8') : '')
        : fs.readFileSync(caminho, 'utf-8');
      const dono = (meta.match(/^AGENTE:\s*(.+)$/m) || [])[1];
      if (dono && dono.trim() === agente) {
        const tarefa = (meta.match(/^TAREFA:\s*(.+)$/m) || [])[1];
        if (tarefa) return tarefa.trim();
      }
    } catch {
      // trava sumiu ou ilegível: ignorar
    }
  }
  return '';
}

async function main() {
  let entrada = '';
  for await (const pedaco of process.stdin) entrada += pedaco;
  let ev;
  try {
    ev = JSON.parse(entrada);
  } catch {
    process.exit(0); // sem evento legível não há o que registrar
  }
  if (!ev || !['Write', 'Edit', 'Bash'].includes(ev.tool_name)) process.exit(0);

  const cwd = caminhoReal(ev.cwd || process.cwd());
  const raiz = raizPrincipal(cwd);
  if (!raiz) process.exit(0);

  try {
    const agente = identificarAgente(ev, raiz) ||
      (ev.agent_id ? `SUBAGENTE-${ev.agent_type || ev.agent_id.substring(0, 8)}` : 'PRINCIPAL');
    const entradaFerramenta = ev.tool_input || {};
    const tarefa = tarefaDoAgente(raiz, agente);
    const sufixoTarefa = tarefa ? ` (${tarefa})` : '';

    let mensagem;
    if (ev.tool_name === 'Bash') {
      mensagem = `Bash${sufixoTarefa}: ${umaLinha(entradaFerramenta.command, 160)}`;
    } else {
      const alvo = caminhoReal(path.resolve(cwd, entradaFerramenta.file_path || ''));
      let exibido = path.relative(cwd, alvo);
      if (exibido.startsWith('..')) exibido = path.relative(raiz, alvo);
      if (exibido.startsWith('..')) exibido = alvo;
      mensagem = ev.tool_name === 'Edit'
        ? `Edit ${exibido}${sufixoTarefa} — "${umaLinha(entradaFerramenta.old_string, 50)}"`
        : `Write ${exibido}${sufixoTarefa} — arquivo criado/reescrito`;
    }
    acrescentarNoLog(raiz, agente, mensagem);
  } catch (erro) {
    try {
      acrescentarNoLog(raiz, 'SISTEMA', `ERRO INTERNO (${erro.name}): ${erro.message}`);
    } catch {
      // sem como registrar
    }
  }
  process.exit(0);
}

main().catch(() => process.exit(0));
