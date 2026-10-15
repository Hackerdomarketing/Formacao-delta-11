#!/usr/bin/env bash
# Teste do vigia urls-validas.py (v6.3 — C-041, D34)
source "$(dirname "$0")/_ajudante-hooks-python.sh" urls-validas
checagens_basicas

novo_projeto
escreve() { evento tool_name=Write tool_input.file_path=$TEST_DIR/src/config.ts "tool_input.content=$1"; }

espera 0 "https://api.exemplo.com/v1: valida" "$(escreve 'ver https://api.exemplo.com/v1/users?x=1')"
espera 0 "http://localhost:3000: valida (D34)" "$(escreve 'abra http://localhost:3000/painel')"
espera 0 "http://127.0.0.1:8765: valida (D34)" "$(escreve 'API em http://127.0.0.1:8765/status')"
espera 0 "http://meu-mac.local: valida (D34)" "$(escreve 'http://meu-mac.local/teste')"
espera 0 "http://[::1]:8080: valida" "$(escreve 'http://[::1]:8080/')"
espera 0 "URL entre aspas duplas em codigo: valida (D34)" "$(escreve 'const API = "https://api.exemplo.com";')"
espera 0 "URL entre aspas simples: valida" "$(escreve "fetch('https://api.exemplo.com/x')")"
espera 0 "URL entre crases (markdown): valida" "$(escreve 'use `https://exemplo.com.br/a`')"
espera 0 "URL entre < >: valida" "$(escreve '<https://exemplo.com>')"
espera 0 "URL no fim da frase com ponto: valida" "$(escreve 'Veja https://exemplo.com.')"
espera 0 "link markdown [texto](url): valida" "$(escreve '[docs](https://docs.exemplo.com/x)')"
espera 0 "marcador \${HOST} em template literal: ignorado" "$(escreve 'fetch(`https://${HOST}/api`)')"
espera 0 "marcador {{dominio}}: ignorado" "$(escreve 'https://{{dominio}}/x')"
espera 0 "marcador [seu-dominio]: ignorado" "$(escreve 'https://[seu-dominio]/x')"
espera 0 "nome interno com porta (docker): valido" "$(escreve 'DATABASE=http://db:5432')"
espera 0 "texto sem URL: passa" "$(escreve 'nada aqui')"

espera 2 "https://exemplo (sem terminacao): bloqueia" "$(escreve 'ver https://exemplo/caminho')"
stderr_contem "sem terminacao"
espera 2 "terminacao numerica https://exemplo.123: bloqueia" "$(escreve 'https://exemplo.123/x')"
espera 2 "caractere invalido no dominio: bloqueia" "$(escreve 'https://exem_plo.com/x')"
espera 2 "Edit com URL quebrada no new_string: bloqueia" "$(evento tool_name=Edit tool_input.file_path=$TEST_DIR/a.md tool_input.old_string=a 'tool_input.new_string=https://dominio-sem-fim')"
fim
