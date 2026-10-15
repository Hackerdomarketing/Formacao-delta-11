#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 v6.3 — Hook PreToolUse: Verificar trava de arquivo
// ═══════════════════════════════════════════════════════════════
// Registro (templates/settings-hooks.json):
//   PreToolUse  matcher "Write|Edit"  →  node "$CLAUDE_PROJECT_DIR/.delta-11/hooks/check-lock.js"
//
// Dispara ANTES de Write/Edit. Se o arquivo-alvo está travado por
// OUTRO agente, BLOQUEIA (código 2; o texto do stderr vira o motivo
// que o agente lê).
//
// v6.3:
//   - As travas são procuradas na PASTA PRINCIPAL do projeto (D25:
//     pai do `git rev-parse --git-common-dir`; senão CLAUDE_PROJECT_DIR;
//     senão o cwd), mesmo quando o agente trabalha numa worktree. O
//     caminho da trava é relativo à raiz da cópia em que o arquivo está
//     (src/a.ts → locks/src--a.ts.lock), igual para principal e worktree.
//   - Dono da trava (C-022): o agente é identificado pelo `agent_id`
//     (sub-agente) ou pelo `session_id` (sessão principal) do evento,
//     via vínculos gravados pelo heartbeat em
//     `ativacoes/agentes-sessao.json`, ou pelo `agent_type` quando é um
//     nome Delta-11. Não adivinha pelo "ACK mais recente". O campo
//     SESSION da trava também vale (agent_id ou session_id).
//   - Entrada malformada: BLOQUEIA com mensagem clara (antes quebrava
//     e liberava em silêncio).
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const NOMES_DELTA11 = new Set(['ATLAS', 'CRONOS', 'FRONT', 'PIXEL', 'FORM', 'BACK',
  'ENGINE', 'VAULT', 'SHIELD', 'SCOUT']);

function git(pasta, args) {
  try {
    return execFileSync('git', ['-C', pasta, ...args], {
      encoding: 'utf-8', timeout: 3000, stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return '';
  }
}

// Caminho real (resolve links como /tmp → /private/tmp no macOS),
// mesmo quando o arquivo ainda não existe (Write de arquivo novo).
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

// Raiz da cópia (principal ou worktree) em que o cwd está, respeitando
// projetos que moram numa subpasta do repositório git.
function raizDaCopia(cwd, raiz) {
  let topoCopia = git(cwd, ['rev-parse', '--show-toplevel']);
  let topoPrincipal = git(raiz, ['rev-parse', '--show-toplevel']);
  if (!topoCopia || !topoPrincipal) return raiz;
  topoCopia = caminhoReal(topoCopia);
  topoPrincipal = caminhoReal(topoPrincipal);
  const prefixo = path.relative(topoPrincipal, raiz);
  return path.join(topoCopia, prefixo.startsWith('..') ? '' : prefixo);
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

// Identificação estrita (sem "ACK mais recente"): vínculo ou agent_type.
function identificarAgente(ev, raiz) {
  const tipo = String(ev.agent_type || '').trim().toUpperCase();
  if (NOMES_DELTA11.has(tipo)) return tipo;
  const vinculo = lerVinculos(raiz)[chaveDoEvento(ev)];
  return (vinculo && vinculo.agente) || '';
}

function lerMetadadosTrava(caminho) {
  const stats = fs.statSync(caminho);
  if (stats.isDirectory()) {
    const meta = path.join(caminho, 'meta');
    return fs.existsSync(meta) ? fs.readFileSync(meta, 'utf-8') : '';
  }
  return fs.readFileSync(caminho, 'utf-8');
}

function campo(texto, nome) {
  const m = texto.match(new RegExp(`^${nome}:\\s*(.+)$`, 'm'));
  return m ? m[1].trim() : '';
}

function bloquear(mensagem) {
  process.stderr.write(mensagem + '\n');
  process.exit(2);
}

async function main() {
  let entrada = '';
  for await (const pedaco of process.stdin) entrada += pedaco;

  let ev;
  try {
    ev = JSON.parse(entrada);
    if (!ev || typeof ev !== 'object') throw new Error('não é um objeto JSON');
  } catch (erro) {
    bloquear(
      `[check-lock] BLOQUEADO por segurança: o Claude Code mandou uma entrada que não é JSON ` +
      `válido (${erro.message}), então não dá para saber se o arquivo está travado por outro ` +
      `agente. Tente a mesma edição de novo; se repetir, é defeito do vigia — avise o CRONOS.`);
  }

  if (ev.tool_name !== 'Write' && ev.tool_name !== 'Edit') process.exit(0);
  const cwd = caminhoReal(ev.cwd || process.cwd());
  const alvoInformado = (ev.tool_input || {}).file_path;
  if (!alvoInformado) process.exit(0);
  const alvo = caminhoReal(path.resolve(cwd, alvoInformado));

  const raiz = raizPrincipal(cwd);
  if (!raiz) process.exit(0);
  const copia = raizDaCopia(cwd, raiz);

  // Caminho relativo à raiz da cópia; se o alvo é da pasta principal
  // (caminho absoluto a partir de uma worktree), relativo à principal.
  let relativo = path.relative(copia, alvo);
  if (relativo.startsWith('..') || path.isAbsolute(relativo)) relativo = path.relative(raiz, alvo);
  if (!relativo || relativo.startsWith('..') || path.isAbsolute(relativo)) process.exit(0);

  const nomeTrava = relativo.split(path.sep).join('--') + '.lock';
  const pastas = [...new Set([
    path.join(raiz, '.delta-11', 'locks'),
    path.join(copia, '.delta-11', 'locks'),   // travas antigas criadas dentro da worktree
  ])];

  const agenteAtual = identificarAgente(ev, raiz);
  const chavesSessao = [ev.agent_id, ev.agent_id ? '' : ev.session_id].filter(Boolean);

  for (const pasta of pastas) {
    const caminhoTrava = path.join(pasta, nomeTrava);
    if (!fs.existsSync(caminhoTrava)) continue;
    let meta = '';
    try {
      meta = lerMetadadosTrava(caminhoTrava);
    } catch {
      meta = '';
    }
    const dono = campo(meta, 'AGENTE') || 'DESCONHECIDO';
    const sessaoDono = campo(meta, 'SESSION');
    if (agenteAtual && dono === agenteAtual) continue;
    if (sessaoDono && chavesSessao.includes(sessaoDono)) continue;

    const tarefa = campo(meta, 'TAREFA') || '?';
    const fazendo = campo(meta, 'FAZENDO') || '?';
    const desde = campo(meta, 'INICIOU') || '?';
    const quem = agenteAtual ? `Você foi identificado como ${agenteAtual}.`
      : 'Não foi possível identificar você como agente Delta-11 (sem ACK vinculado a esta sessão).';
    bloquear(
      `[check-lock] BLOQUEADO: o arquivo "${relativo}" está travado pelo agente ${dono} ` +
      `(tarefa ${tarefa}: ${fazendo}; desde ${desde}). ${quem} ` +
      `Trabalhe em outro arquivo e espere a trava ser liberada (o dono libera no passo 3.9; ` +
      `ao terminar, o vigia release-locks libera sozinho). ` +
      `Se você é o comandante e sabe que essa trava ficou esquecida, apague a pasta: ${caminhoTrava}`);
  }
  process.exit(0);
}

main().catch((erro) => {
  bloquear(`[check-lock] BLOQUEADO por erro interno do vigia: ${erro.message}. ` +
    `Tente de novo; se repetir, avise o CRONOS.`);
});
