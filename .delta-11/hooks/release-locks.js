#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 v6.3 — Hooks SubagentStop + SessionEnd: liberar travas
// ═══════════════════════════════════════════════════════════════
// Registro (templates/settings-hooks.json):
//   SubagentStop  matcher ""  →  node "$CLAUDE_PROJECT_DIR/.delta-11/hooks/release-locks.js"
//   SessionEnd    matcher ""  →  node "$CLAUDE_PROJECT_DIR/.delta-11/hooks/release-locks.js"
//
// Remove as travas (`.delta-11/locks/*.lock`, diretório com `meta` ou
// arquivo antigo) do agente que TERMINOU, na PASTA PRINCIPAL do
// projeto (D25) e, se houver, na cópia (worktree) em que ele estava.
//
//   - SubagentStop: só as travas do sub-agente que terminou. Ele é
//     identificado pelo `agent_id` (vínculo gravado pelo heartbeat em
//     `ativacoes/agentes-sessao.json`) ou pelo `agent_type` quando é um
//     nome Delta-11; o campo SESSION da trava também vale se for o
//     agent_id. (C-008: antes as travas de sub-agente ficavam
//     penduradas até o gc-locks, 2 h depois.)
//   - SessionEnd: a sessão inteira acabou → travas de todos os agentes
//     vinculados a ESTA sessão e travas cujo SESSION é este session_id.
//   - Stop (ou qualquer outro evento): NÃO faz nada. O Stop acontece no
//     fim de cada resposta (C-007); liberar ali soltava, a cada turno,
//     as travas de agentes que ainda estavam trabalhando. Essa guarda
//     protege projetos que ainda tenham o registro antigo no Stop.
//
// Travas ilegíveis (sem meta) só são removidas se forem mais velhas que
// `lock_horas` de `.delta-11/.config-limites.json` (D36; padrão 2 h).
// Registro no activity-log no formato único D25 (hora UTC).
// Sai sempre com 0: no SubagentStop o código 2 impediria o sub-agente
// de terminar.
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const NOME_DO_HOOK = 'release-locks';
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

function horasDeTrava(raiz) {
  try {
    const limites = JSON.parse(fs.readFileSync(path.join(raiz, '.delta-11', '.config-limites.json'), 'utf-8'));
    const horas = Number(limites.lock_horas);
    return horas > 0 ? horas : 2;
  } catch {
    return 2;
  }
}

function agoraIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function logar(raiz, agente, mensagem) {
  try {
    const caminho = path.join(raiz, '.delta-11', 'activity-log.md');
    fs.appendFileSync(caminho, `- [${agoraIso()}] [${NOME_DO_HOOK}] [${agente || 'SISTEMA'}] ${mensagem}\n`, 'utf-8');
  } catch {
    // sem como registrar
  }
}

// Sem vínculo: o operativo citado no início da transcrição do sub-agente
// (o prompt de ativação manda ler `.delta-11/operativos/NOME.md`).
function operativoDaTranscricao(caminho) {
  if (!caminho) return '';
  try {
    const real = caminho.startsWith('~') ? path.join(require('os').homedir(), caminho.slice(1)) : caminho;
    const fd = fs.openSync(real, 'r');
    const buffer = Buffer.alloc(200000);
    const lidos = fs.readSync(fd, buffer, 0, buffer.length, 0);
    fs.closeSync(fd);
    const inicio = buffer.toString('utf-8', 0, lidos).split('\n').slice(0, 5).join('\n');
    const m = inicio.match(/operativos\/([A-Z]+)\.md/);
    return m && NOMES_DELTA11.has(m[1]) ? m[1] : '';
  } catch {
    return '';
  }
}

// Quem terminou: { nomes: Set<NOME>, sessoes: Set<valor aceito no campo SESSION> }
function quemTerminou(ev, raiz) {
  const nomes = new Set();
  const sessoes = new Set();
  const vinculos = lerVinculos(raiz);
  if (ev.hook_event_name === 'SubagentStop') {
    const tipo = String(ev.agent_type || '').trim().toUpperCase();
    if (NOMES_DELTA11.has(tipo)) nomes.add(tipo);
    const vinculo = ev.agent_id ? vinculos[`agente:${ev.agent_id}`] : null;
    if (vinculo && vinculo.agente) nomes.add(vinculo.agente);
    if (nomes.size === 0) {
      const operativo = operativoDaTranscricao(ev.agent_transcript_path);
      if (operativo) nomes.add(operativo);
    }
    if (ev.agent_id) sessoes.add(ev.agent_id);
  } else if (ev.hook_event_name === 'SessionEnd' && ev.session_id) {
    sessoes.add(ev.session_id);
    const marcaDestaSessao = `SessionEnd:${ev.session_id}`;
    for (const vinculo of Object.values(vinculos)) {
      if (!vinculo || vinculo.session_id !== ev.session_id || !vinculo.agente) continue;
      // Ainda ativo, ou encerrado agora mesmo pelo on-stop deste SessionEnd
      // (os dois vigias rodam em paralelo). Quem já saiu por SubagentStop
      // teve as travas liberadas naquela hora.
      if (!vinculo.encerrado_em || vinculo.encerrado_por === marcaDestaSessao) {
        nomes.add(vinculo.agente);
        if (vinculo.agent_id) sessoes.add(vinculo.agent_id);
      }
    }
  }
  return { nomes, sessoes };
}

function lerMetadados(caminho, stats) {
  if (stats.isDirectory()) {
    const meta = path.join(caminho, 'meta');
    return fs.existsSync(meta) ? fs.readFileSync(meta, 'utf-8') : '';
  }
  return fs.readFileSync(caminho, 'utf-8');
}

function remover(caminho, stats) {
  if (stats.isDirectory()) fs.rmSync(caminho, { recursive: true, force: true });
  else fs.unlinkSync(caminho);
}

async function main() {
  let entrada = '';
  for await (const pedaco of process.stdin) entrada += pedaco;
  let ev;
  try {
    ev = JSON.parse(entrada);
  } catch {
    process.exit(0);
  }
  if (!ev || !['SubagentStop', 'SessionEnd'].includes(ev.hook_event_name)) process.exit(0);

  const cwd = caminhoReal(ev.cwd || process.cwd());
  const raiz = raizPrincipal(cwd);
  if (!raiz) process.exit(0);

  try {
    const { nomes, sessoes } = quemTerminou(ev, raiz);
    const limiteMs = horasDeTrava(raiz) * 60 * 60 * 1000;
    const pastas = [...new Set([path.join(raiz, '.delta-11', 'locks'), path.join(cwd, '.delta-11', 'locks')])];
    const liberadas = [];

    for (const pasta of pastas) {
      let entradas = [];
      try {
        entradas = fs.readdirSync(pasta).filter((f) => f.endsWith('.lock'));
      } catch {
        continue;
      }
      for (const nomeTrava of entradas) {
        const caminho = path.join(pasta, nomeTrava);
        let stats;
        try {
          stats = fs.statSync(caminho);
        } catch {
          continue; // sumiu entre listar e ler
        }
        try {
          const meta = lerMetadados(caminho, stats);
          if (!meta.trim()) throw new Error('trava sem metadados');
          const dono = ((meta.match(/^AGENTE:\s*(.+)$/m) || [])[1] || '').trim();
          const sessao = ((meta.match(/^SESSION:\s*(.+)$/m) || [])[1] || '').trim();
          if ((dono && nomes.has(dono)) || (sessao && sessoes.has(sessao))) {
            remover(caminho, stats);
            liberadas.push(nomeTrava);
          }
        } catch {
          try {
            if (Date.now() - stats.mtimeMs > limiteMs) {
              remover(caminho, stats);
              liberadas.push(`${nomeTrava} (ilegível e velha)`);
            }
          } catch {
            // ignorar
          }
        }
      }
    }

    if (liberadas.length > 0) {
      logar(raiz, [...nomes].join(',') || ev.agent_type,
        `${liberadas.length} trava(s) liberada(s) automaticamente no ${ev.hook_event_name}: ${liberadas.join(', ')}`);
    }
  } catch (erro) {
    logar(raiz, 'SISTEMA', `ERRO INTERNO (${erro.name}): ${erro.message}`);
  }
  process.exit(0);
}

main().catch(() => process.exit(0));
