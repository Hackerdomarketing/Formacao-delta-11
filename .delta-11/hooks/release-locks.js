#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 — Hook Stop: Liberar Locks Automaticamente
// ═══════════════════════════════════════════════════════════════
// Dispara quando um agente PARA (sessão encerra, contexto esgota,
// ou parada explícita). Remove todos os locks criados por esse
// agente para que outros possam trabalhar nos mesmos arquivos.
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');

async function main() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  const data = JSON.parse(input);
  const cwd = data.cwd || process.cwd();
  const agente = data.agent_type || data.session_id?.substring(0, 8) || '';

  const locksDir = path.join(cwd, '.delta-11', 'locks');

  if (!fs.existsSync(locksDir)) {
    process.exit(0);
  }

  // Listar todos os .lock files
  const lockFiles = fs.readdirSync(locksDir).filter(f => f.endsWith('.lock'));
  let removidos = 0;

  for (const lockFile of lockFiles) {
    const lockPath = path.join(locksDir, lockFile);

    try {
      const content = fs.readFileSync(lockPath, 'utf-8');
      const agentMatch = content.match(/^AGENTE:\s*(.+)$/m);
      const lockAgent = agentMatch ? agentMatch[1].trim() : '';

      // Se o lock é deste agente OU se o agente não é identificável
      // (sessão principal), remover locks que parecem ser desta sessão
      const sessionMatch = content.match(/^SESSION:\s*(.+)$/m);
      const lockSession = sessionMatch ? sessionMatch[1].trim() : '';

      const isDonoDoLock =
        (agente && lockAgent === agente) ||
        (data.session_id && lockSession === data.session_id);

      if (isDonoDoLock) {
        fs.unlinkSync(lockPath);
        removidos++;
      }
    } catch {
      // Se não conseguir ler, tentar remover locks velhos (mais de 2 horas)
      try {
        const stats = fs.statSync(lockPath);
        const idadeMs = Date.now() - stats.mtimeMs;
        const duasHoras = 2 * 60 * 60 * 1000;

        if (idadeMs > duasHoras) {
          fs.unlinkSync(lockPath);
          removidos++;
        }
      } catch {
        // Ignorar
      }
    }
  }

  // Logar liberação no activity-log
  if (removidos > 0) {
    const logPath = path.join(cwd, '.delta-11', 'activity-log.md');
    if (fs.existsSync(logPath)) {
      const agora = new Date();
      const hora = agora.toTimeString().substring(0, 5);
      const linha = `| ${hora} | ${agente || 'SYSTEM'} | — | (locks) | Release | ${removidos} lock(s) liberado(s) automaticamente |\n`;
      fs.appendFileSync(logPath, linha, 'utf-8');
    }
  }

  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`Aviso hook release-locks: ${err.message}`);
  process.exit(1);
});
