#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 — Hook PreToolUse: Verificar Lock de Arquivo
// ═══════════════════════════════════════════════════════════════
// Dispara ANTES de Write/Edit. Se o arquivo-alvo está travado
// por outro agente, BLOQUEIA a operação com mensagem clara.
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');

async function main() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  const data = JSON.parse(input);
  const toolName = data.tool_name;
  const toolInput = data.tool_input || {};
  const cwd = data.cwd || process.cwd();

  // Extrair o arquivo-alvo da operação
  let targetFile = null;
  if (toolName === 'Write' || toolName === 'Edit') {
    targetFile = toolInput.file_path || null;
  }

  if (!targetFile) {
    // Sem arquivo-alvo, permitir
    process.exit(0);
  }

  // Normalizar caminho relativo ao projeto
  const relativePath = path.relative(cwd, targetFile);

  // Verificar se existe lock para este arquivo
  const locksDir = path.join(cwd, '.delta-11', 'locks');
  if (!fs.existsSync(locksDir)) {
    process.exit(0);
  }

  // Converter caminho do arquivo em nome de lock seguro
  // ex: src/components/Card.tsx → src--components--Card.tsx.lock
  const lockFileName = relativePath.replace(/\//g, '--') + '.lock';
  const lockPath = path.join(locksDir, lockFileName);

  if (!fs.existsSync(lockPath)) {
    process.exit(0);
  }

  // Lock existe — verificar se é de outro agente
  const lockContent = fs.readFileSync(lockPath, 'utf-8');

  // Extrair agente do lock
  const agentMatch = lockContent.match(/^AGENTE:\s*(.+)$/m);
  const lockAgent = agentMatch ? agentMatch[1].trim() : 'DESCONHECIDO';

  // Extrair agente atual do contexto (se disponível via agent_type)
  const currentAgent = data.agent_type || '';

  // Se o lock é do mesmo agente, permitir
  if (currentAgent && lockAgent === currentAgent) {
    process.exit(0);
  }

  // Bloquear — arquivo está travado por outro agente
  const tarefaMatch = lockContent.match(/^TAREFA:\s*(.+)$/m);
  const fazendoMatch = lockContent.match(/^FAZENDO:\s*(.+)$/m);
  const lockTarefa = tarefaMatch ? tarefaMatch[1].trim() : '?';
  const lockFazendo = fazendoMatch ? fazendoMatch[1].trim() : '?';

  const output = {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason:
        `BLOQUEADO: O arquivo "${relativePath}" está travado pelo agente ${lockAgent} ` +
        `(tarefa ${lockTarefa}: ${lockFazendo}). ` +
        `Aguarde o agente finalizar ou trabalhe em outro arquivo. ` +
        `Lock em: ${lockPath}`
    }
  };

  process.stdout.write(JSON.stringify(output));
  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`Erro no hook check-lock: ${err.message}`);
  process.exit(1);
});
