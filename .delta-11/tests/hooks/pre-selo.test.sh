#!/usr/bin/env bash
# Teste do vigia pre-selo.py (v6.3 — M4, C-160, C-130, D36)
source "$(dirname "$0")/_ajudante-hooks-python.sh" pre-selo
checagens_basicas
if grep -q "Mecanismo 6" "$HOOK"; then err "ainda chama o limite de 'Mecanismo 6' (C-160)"; else ok "nao fala em 'Mecanismo 6'"; fi
if grep -q "M4" "$HOOK"; then ok "chama o limite de M4 (D22)"; else err "nao cita M4"; fi

novo_projeto
MEM="$TEST_DIR/.delta-11/memoria"
GRANDE="$TEST_DIR/grande.md"; python3 -c "print('x' * 2400)" > "$GRANDE"   # ~600 tokens
espera 0 "BACK-produto.md pequeno: passa" "$(evento tool_name=Write tool_input.file_path=$MEM/BACK-produto.md 'tool_input.content=o que existe agora')"
espera 2 "BACK-produto.md com ~600 tokens (> 500): bloqueia" "$(evento tool_name=Write tool_input.file_path=$MEM/BACK-produto.md "tool_input.content=@$GRANDE")"
stderr_contem "M4"
espera 2 "caminho relativo tambem e vigiado" "$(evento tool_name=Write tool_input.file_path=.delta-11/memoria/BACK-produto.md "tool_input.content=@$GRANDE")"
espera 0 "ATLAS-produto.md grande: isento" "$(evento tool_name=Write tool_input.file_path=$MEM/ATLAS-produto.md "tool_input.content=@$GRANDE")"
espera 0 "CRONOS-produto.md grande: isento" "$(evento tool_name=Write tool_input.file_path=$MEM/CRONOS-produto.md "tool_input.content=@$GRANDE")"
espera 0 "BACK-historia.md grande: sem limite" "$(evento tool_name=Write tool_input.file_path=$MEM/BACK-historia.md "tool_input.content=@$GRANDE")"

python3 -c "print('y' * 1900)" > "$MEM/PIXEL-produto.md"   # ~475 tokens
espera 2 "Edit que faz o arquivo FINAL passar do limite: bloqueia (simula o Edit)" "$(evento tool_name=Edit tool_input.file_path=$MEM/PIXEL-produto.md tool_input.old_string=yyyy "tool_input.new_string=@$GRANDE")"
espera 0 "Edit pequeno que mantem o arquivo no limite: passa" "$(evento tool_name=Edit tool_input.file_path=$MEM/PIXEL-produto.md tool_input.old_string=yyyy tool_input.new_string=zz)"

echo '{"produto_max_tokens": 800}' > .delta-11/.config-limites.json
espera 0 "produto_max_tokens=800 (D36): ~600 tokens passa" "$(evento tool_name=Write tool_input.file_path=$MEM/BACK-produto.md "tool_input.content=@$GRANDE")"
fim
