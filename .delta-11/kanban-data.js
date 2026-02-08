// KANBAN DATA — Formação Δ-11
// Este arquivo é atualizado pelos agentes junto com o kanban.md
// O painel.html lê este arquivo para exibir o dashboard visual
// FORMATO: não altere a estrutura, apenas o conteúdo dentro dos arrays

window.KANBAN_DATA = {
  projeto: "",
  complexidade: "",
  fase_atual: "",
  ultima_atualizacao: "",
  agente_atualizador: "",

  // Colunas "a fazer" por agente
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
  // Formato: { id: "T-001", desc: "Descrição", agente: "NOME", inicio: "HH:MM" }
  fazendo: [],

  // Tarefas aguardando revisão
  // Formato: { id: "T-001", desc: "Descrição", por: "NOME", revisor: "NOME" }
  revisao: [],

  // Tarefas concluídas
  // Formato: { id: "T-001", desc: "Descrição", por: "NOME", aprovado: "NOME", data: "DD/MM" }
  concluido: [],

  // Tarefas bloqueadas
  // Formato: { id: "T-001", desc: "Descrição", agente: "NOME", motivo: "texto", precisa: "ATLAS/comandante" }
  bloqueado: []
};
