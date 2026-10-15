// KANBAN DATA — Formação Δ-11 (v6.3 — 2026-10-14)
// QUEM ESCREVE: SOMENTE o CRONOS (D10). Executores avisam o CRONOS por SendMessage e pelo próprio
// memoria/[NOME]-produto.md; nunca editam este arquivo nem o kanban.md (evita uma edição apagar a outra).
// O CRONOS atualiza este arquivo junto com o kanban.md. O painel.html lê este arquivo a cada 5 s.
// Sinal de vida dos agentes NÃO é escrito aqui à mão: o vigia heartbeat.sh grava pulsos-data.js sozinho.
// FORMATO: não altere a estrutura, apenas o conteúdo. Todo horário é ISO completo com fuso,
// ex.: "2026-10-14T13:05:00-03:00" (o painel ainda aceita "HH:MM" de quadros antigos, como hora de hoje).

window.KANBAN_DATA = {
  projeto: "",
  complexidade: "",          // "BAIXA" (5–8) / "MÉDIA" (9–12) / "ALTA" (13–15)
  fase_atual: "",            // ex.: "Fase 3 · onda 2 de 4" (o painel lê "onda N de M")
  total_ondas: null,         // número de ondas da fase atual, quando fase_atual só diz "onda N"
  ultima_atualizacao: "",    // ISO — o painel mostra a idade dos dados a partir daqui
  agente_atualizador: "",    // sempre "CRONOS"

  // Voz do gerente para o comandante (só o CRONOS). precisa_comandante: null ou o texto do que precisa dele.
  mensagem_cronos: {
    texto: "",
    timestamp: "",
    precisa_comandante: null
  },

  // Colunas "a fazer" por agente
  // Formato: { id: "T-001", desc: "Descrição", resumo_humano: "Frase simples para o comandante" }
  a_fazer: {
    ATLAS: [],
    CRONOS: [],
    FRONT: [],
    PIXEL: [],
    FORM: [],
    BACK: [],
    ENGINE: [],
    VAULT: [],
    SHIELD: [],
    SCOUT: []
  },

  // Tarefas em execução
  // Formato: { id: "T-001", desc: "Descrição", agente: "NOME", inicio: "2026-10-14T13:05:00-03:00",
  //            resumo_humano: "Frase simples para o comandante" }
  fazendo: [],

  // Tarefas aguardando revisão
  // Formato: { id: "T-001", desc: "Descrição", por: "NOME", revisor: "SHIELD", resumo_humano: "..." }
  revisao: [],

  // Tarefas concluídas
  // Formato: { id: "T-001", desc: "Descrição", por: "NOME", aprovado: "SHIELD",
  //            data: "2026-10-14T15:40:00-03:00", resumo_humano: "..." }
  concluido: [],

  // Tarefas bloqueadas
  // Formato: { id: "T-001", desc: "Descrição", agente: "NOME", motivo: "texto", precisa: "ATLAS/comandante",
  //            resumo_humano: "..." }
  bloqueado: [],

  // Reserva de compatibilidade: sinais de vida antigos, escritos à mão. A fonte automática agora é
  // pulsos-data.js. Formato: { agente: "NOME", ultima_atividade: "ISO", tarefa_atual: "T-001" }
  heartbeats: []
};
