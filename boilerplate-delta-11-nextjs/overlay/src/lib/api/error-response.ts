import { NextResponse } from 'next/server';

// Formato ÚNICO de erro da API (nextjs-api-patterns §3 + regras-codigo §9):
// nomes de campos em inglês, mensagens (valores) em português — o usuário lê a mensagem.
// Toda rota usa este helper; erro fora do formato reprova no contract-tester.

type ErrorDetails = Record<string, string[] | string>;

export function errorResponse(status: number, message: string, details?: ErrorDetails) {
  return NextResponse.json({ error: true, message, details }, { status });
}

// Uso típico:
//   return errorResponse(422, 'Dados inválidos', validation.error.flatten().fieldErrors);
//   return errorResponse(401, 'Sessão expirada — entre novamente');
//   return errorResponse(404, 'Produto não encontrado');
