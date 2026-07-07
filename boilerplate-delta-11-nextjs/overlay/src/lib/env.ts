// Validação de variáveis de ambiente na inicialização.
// Regra (regras-codigo.md §6): falhe RUIDOSAMENTE no boot, nunca silenciosamente em produção.
// Adicione aqui toda variável nova ANTES de usá-la no código (e o nome no .env.example, sem o valor).

const requiredEnvVars = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
] as const;

export function assertRequiredEnv(): void {
  const missing = requiredEnvVars.filter((name) => !process.env[name]);

  if (missing.length > 0) {
    throw new Error(
      `Variáveis de ambiente ausentes: ${missing.join(', ')}. ` +
        'Copie o .env.example para .env.local e preencha os valores.',
    );
  }
}
