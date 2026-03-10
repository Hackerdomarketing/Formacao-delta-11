#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// DELTA-11 — Hook PostToolUse: Logar Atividade em Tempo Real
// ═══════════════════════════════════════════════════════════════
// Dispara APÓS cada Write/Edit/Bash. Registra automaticamente
// o que foi feito no activity-log.md para visibilidade de todos
// os agentes trabalhando em paralelo.
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

  // Só logar operações relevantes (Write, Edit, Bash)
  const toolsParaLogar = ['Write', 'Edit', 'Bash'];
  if (!toolsParaLogar.includes(toolName)) {
    process.exit(0);
  }

  // Extrair informações relevantes
  let arquivo = '';
  let descricao = '';

  if (toolName === 'Write' || toolName === 'Edit') {
    const filePath = toolInput.file_path || '';
    arquivo = path.relative(cwd, filePath);

    if (toolName === 'Edit') {
      const oldStr = (toolInput.old_string || '').substring(0, 50);
      descricao = `Edit: "${oldStr}..."`;
    } else {
      descricao = 'Write: arquivo criado/reescrito';
    }
  } else if (toolName === 'Bash') {
    const cmd = (toolInput.command || '').substring(0, 80);
    arquivo = '(terminal)';
    descricao = `Bash: ${cmd}`;
  }

  // Determinar agente (agent_type ou session_id como fallback)
  const agente = data.agent_type || data.session_id?.substring(0, 8) || 'MAIN';

  // Montar linha de log
  const agora = new Date();
  const hora = agora.toTimeString().substring(0, 5);
  const dataStr = agora.toISOString().substring(0, 10);

  // Ler lock ativo para extrair tarefa (se existir)
  let tarefa = '—';
  const locksDir = path.join(cwd, '.delta-11', 'locks');
  if (fs.existsSync(locksDir)) {
    try {
      const lockFiles = fs.readdirSync(locksDir).filter(f => f.endsWith('.lock'));
      for (const lockFile of lockFiles) {
        const lockContent = fs.readFileSync(path.join(locksDir, lockFile), 'utf-8');
        const agentMatch = lockContent.match(/^AGENTE:\s*(.+)$/m);
        if (agentMatch && agentMatch[1].trim() === agente) {
          const tarefaMatch = lockContent.match(/^TAREFA:\s*(.+)$/m);
          if (tarefaMatch) {
            tarefa = tarefaMatch[1].trim();
          }
          break;
        }
      }
    } catch {
      // Ignorar erros de leitura de lock
    }
  }

  // Caminho do activity-log
  const logPath = path.join(cwd, '.delta-11', 'activity-log.md');

  // Criar arquivo se não existir
  if (!fs.existsSync(logPath)) {
    const header =
      `# Activity Log — Delta-11\n\n` +
      `> Gerado automaticamente por hooks. Não editar manualmente.\n\n`;
    fs.writeFileSync(logPath, header, 'utf-8');
  }

  // Verificar se precisa adicionar cabeçalho do dia
  const conteudo = fs.readFileSync(logPath, 'utf-8');
  const marcadorDia = `## ${dataStr}`;

  let linhaParaAdicionar = '';

  if (!conteudo.includes(marcadorDia)) {
    linhaParaAdicionar +=
      `\n${marcadorDia}\n\n` +
      `| Hora  | Agente | Tarefa | Arquivo | Ação | Descrição |\n` +
      `|-------|--------|--------|---------|------|-----------|\n`;
  }

  // Escapar pipes no conteúdo da descrição
  const descricaoSafe = descricao.replace(/\|/g, '\\|');
  const arquivoSafe = arquivo.replace(/\|/g, '\\|');

  linhaParaAdicionar += `| ${hora} | ${agente} | ${tarefa} | ${arquivoSafe} | ${toolName} | ${descricaoSafe} |\n`;

  // Append ao arquivo
  fs.appendFileSync(logPath, linhaParaAdicionar, 'utf-8');

  process.exit(0);
}

main().catch((err) => {
  // Erros de logging não devem bloquear execução
  process.stderr.write(`Aviso hook log-activity: ${err.message}`);
  process.exit(1);
});
