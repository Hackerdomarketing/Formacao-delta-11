// Limites estruturais de código — Formação Δ-11
// Fonte: .delta-11/protocolos/regras-codigo.md seção 8 (pesquisa 2026: defaults ESLint/SonarQube/Clean Code/era-IA)
// NÃO afrouxar valores sem aprovação do comandante. O build-validator trata violação como BLOCKER.
export default {
  files: ['src/**/*.{ts,tsx,js,jsx}'],
  rules: {
    'max-params': ['error', 3],
    'max-lines-per-function': ['error', { max: 50, skipBlankLines: true, skipComments: true }],
    'max-lines': ['error', { max: 400, skipBlankLines: true, skipComments: true }],
    'max-classes-per-file': ['error', 1],
    'max-depth': ['error', 3],
    complexity: ['error', 10],
  },
};
