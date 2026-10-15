#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste das ferramentas dos agentes (.delta-11/ferramentas/*.sh) — v6.3
# ════════════════════════════════════════════════════════════════
# Cada ferramenta roda de verdade num PROJETO FALSO criado em
# .delta-11/scratch/ (D21 — nada em /tmp), com git próprio. Nada do
# projeto real é tocado; a pasta falsa é apagada no fim.
#
# Conferido:
#   0. bash -n em todas; nenhuma usa /tmp, eval ou "grep -c ... || echo 0".
#   1. cronos-status (C-133, C-134): roda até o fim; vê travas que são
#      PASTAS; trava órfã só depois de 2 h (igual ao gc-locks); vê a trava
#      da Fase 3.5; --resumo mostra só o resultado; rodando de dentro de
#      uma worktree, lê a pasta PRINCIPAL (D25).
#   2. back-review (C-134): não aborta em arquivo sem .max(); conta os
#      campos sem .max(); acusa 422 (D13); rota limpa sai com 0.
#   3. engine-test-api (C-135): rota maliciosa do project-core NÃO executa
#      comando e é ignorada; lê a fatia project-core/contratos.md (D6);
#      GET protegido (401) passa; POST só com --incluir-escrita e exige o
#      formato VALIDATION_ERROR (D13); DELETE nunca é chamado.
#   4. scout-lighthouse (C-136): sem o Lighthouse sai INCOMPLETO (2), bem visível.
#   5. shield-scan (C-137): acha senha entre aspas SIMPLES; sem semgrep o
#      resultado não é PASS.
#   6. vault-validate-sql (C-138): RLS em minúsculas conta; ON DELETE é
#      conferido por chave estrangeira; timestamp duplicado = FAIL.
#   7. verificar-dependencias: roda para um agente conhecido e um desconhecido.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/framework/test-helpers.sh"

FERRAMENTAS="$DELTA_DIR/ferramentas"

# ─── 0. Sintaxe e padrões proibidos ──────────────────────────
echo "[0] sintaxe e padrões proibidos"
for ferramenta in "$FERRAMENTAS"/*.sh; do
    nome=$(basename "$ferramenta")
    if bash -n "$ferramenta" 2>/dev/null; then
        pass "bash -n $nome"
    else
        fail "bash -n $nome: $(bash -n "$ferramenta" 2>&1 | head -1)"
    fi
    expect_no_match "$ferramenta" '(^|[^.a-z])/tmp/' "$nome não usa /tmp (D21)"
    expect_no_match "$ferramenta" '(^|[[:space:];(])eval[[:space:]]' "$nome não usa eval"
    expect_no_match "$ferramenta" 'grep -c[^|]*\|\|[[:space:]]*echo' "$nome não usa 'grep -c ... || echo 0' (C-134)"
done

# ─── Projeto falso ───────────────────────────────────────────
mkdir -p "$DELTA_DIR/scratch"
FAKE="$(mktemp -d "$DELTA_DIR/scratch/$(date +%Y-%m-%d)-teste-ferramentas-XXXXXX")"
cleanup() {
    if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi
    if [ -n "${FAKE:-}" ] && [ -d "$FAKE" ] && [[ "$FAKE" == "$DELTA_DIR/scratch/"*-teste-ferramentas-* ]]; then
        rm -rf "$FAKE"
    fi
    if [ -n "${WORKTREE:-}" ] && [ -d "$WORKTREE" ] && [[ "$WORKTREE" == "$DELTA_DIR/scratch/"*-teste-ferramentas-*-worktree ]]; then
        rm -rf "$WORKTREE"
    fi
}
trap cleanup EXIT

GIT=(git -c user.name=teste -c user.email=teste@exemplo.invalid -c init.defaultBranch=main)
"${GIT[@]}" init -q "$FAKE"
mkdir -p "$FAKE/.delta-11/ativacoes" "$FAKE/.delta-11/locks" "$FAKE/.delta-11/memoria/project-core"
printf '# Kanban\n- [ ] T-001 tarefa aberta\n- [x] T-002 tarefa feita\n' > "$FAKE/.delta-11/kanban.md"
echo '{"agent":"BACK","timestamp":"2026-10-14T12:00:00Z"}' > "$FAKE/.delta-11/ativacoes/ack-BACK.txt"
mkdir "$FAKE/.delta-11/locks/src--novo.ts.lock"
printf 'AGENTE: FRONT\nTAREFA: T-010\n' > "$FAKE/.delta-11/locks/src--novo.ts.lock/meta"
mkdir "$FAKE/.delta-11/locks/src--velho.ts.lock"
printf 'AGENTE: PIXEL\nTAREFA: T-011\n' > "$FAKE/.delta-11/locks/src--velho.ts.lock/meta"
mkdir "$FAKE/.delta-11/locks/src--meia-hora.ts.lock"
# Datas no formato certo do touch -t: AAAAMMDDhhmm (3 h e 45 min atrás).
touch -t "$(date -v-3H +%Y%m%d%H%M 2>/dev/null || date -d '3 hours ago' +%Y%m%d%H%M)" "$FAKE/.delta-11/locks/src--velho.ts.lock"
touch -t "$(date -v-45M +%Y%m%d%H%M 2>/dev/null || date -d '45 minutes ago' +%Y%m%d%H%M)" "$FAKE/.delta-11/locks/src--meia-hora.ts.lock"
mkdir "$FAKE/.delta-11/ativacoes/.trava-fase-3.5"
echo "CRONOS" > "$FAKE/.delta-11/ativacoes/.trava-fase-3.5/owner"
mkdir -p "$FAKE/src"
"${GIT[@]}" -C "$FAKE" add -A >/dev/null
"${GIT[@]}" -C "$FAKE" commit -q -m "projeto falso"

# ─── 1. cronos-status ────────────────────────────────────────
echo ""
echo "[1] cronos-status.sh"
status_code=0
saida=$(cd "$FAKE/src" && bash "$FERRAMENTAS/cronos-status.sh" 2>&1) || status_code=$?
if grep -q "RESULTADO:" <<< "$saida"; then pass "roda até o fim (antes morria na seção 2)"; else fail "não chegou ao RESULTADO (código $status_code)"; fi
if grep -q "ORFA   src/velho.ts" <<< "$saida"; then pass "trava-PASTA de 3 h é órfã"; else fail "não viu a trava-pasta órfã de 3 h"; fi
if grep -q "ATIVA  src/meia-hora.ts" <<< "$saida"; then pass "trava de 45 min NÃO é órfã (limite 2 h do gc-locks)"; else fail "trava de 45 min marcada errado"; fi
if grep -q "Agente: FRONT | Tarefa: T-010" <<< "$saida"; then pass "lê AGENTE/TAREFA do meta da trava-pasta"; else fail "não leu o meta da trava-pasta"; fi
if grep -q "Fase 3.5" <<< "$saida"; then pass "vê a trava da Fase 3.5"; else fail "não viu a trava da Fase 3.5"; fi
if grep -q "Total: 2 tarefa" <<< "$saida" && grep -q "Concluidas: 1" <<< "$saida"; then pass "conta o kanban sem o erro \"0 0\" (C-134)"; else fail "contagem do kanban errada"; fi
if grep -q "ATIVO   BACK" <<< "$saida"; then pass "vê o ACK do BACK"; else fail "não viu o ACK"; fi
[ "$status_code" -eq 0 ] && pass "ALERTA não bloqueia (saída 0)" || fail "saída $status_code com só alertas"
resumo=$(cd "$FAKE" && bash "$FERRAMENTAS/cronos-status.sh" --resumo 2>&1 || true)
if grep -q "RESULTADO:" <<< "$resumo" && ! grep -q "TRAVAS DE ARQUIVO" <<< "$resumo"; then
    pass "--resumo mostra só o resultado"
else
    fail "--resumo não funciona"
fi
WORKTREE="$DELTA_DIR/scratch/$(basename "$FAKE")-worktree"
"${GIT[@]}" -C "$FAKE" worktree add -q "$WORKTREE" -b teste-wt >/dev/null 2>&1 || true
if [ -d "$WORKTREE" ]; then
    rm -rf "$WORKTREE/.delta-11/locks"   # a cópia da worktree não tem as travas
    saida_wt=$(cd "$WORKTREE" && bash "$FERRAMENTAS/cronos-status.sh" 2>&1 || true)
    if grep -q "ORFA   src/velho.ts" <<< "$saida_wt"; then
        pass "D25: de dentro da worktree, lê a pasta principal"
    else
        fail "D25: de dentro da worktree não leu a pasta principal"
    fi
    "${GIT[@]}" -C "$FAKE" worktree remove --force "$WORKTREE" >/dev/null 2>&1 || true
    if [ -d "$WORKTREE" ] && [[ "$WORKTREE" == "$DELTA_DIR/scratch/"*-teste-ferramentas-*-worktree ]]; then rm -rf "$WORKTREE"; fi
else
    fail "não deu para criar a worktree de teste"
fi

# ─── 2. back-review ──────────────────────────────────────────
echo ""
echo "[2] back-review.sh"
mkdir -p "$FAKE/api-ruim/users" "$FAKE/api-boa/users"
cat > "$FAKE/api-ruim/users/route.ts" <<'TS'
import { z } from "zod";
const schema = z.object({ name: z.string(), email: z.string() });
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return Response.json({ error: "x" }, { status: 422 });
  return Response.json({ ok: true });
}
TS
cat > "$FAKE/api-boa/users/route.ts" <<'TS'
import { z } from "zod";
const schema = z.object({ name: z.string().max(100) });
export async function GET(request: Request) {
  const session = await getSession();
  return Response.json({ ok: true, session });
}
TS
status_code=0
saida=$(cd "$FAKE" && bash "$FERRAMENTAS/back-review.sh" api-ruim 2>&1) || status_code=$?
if grep -q "RESUMO" <<< "$saida"; then pass "não aborta em arquivo com z.string() sem .max() (C-134)"; else fail "abortou antes do RESUMO"; fi
if grep -q "2 campo(s) z.string() sem .max()" <<< "$saida"; then pass "conta os 2 campos sem .max()"; else fail "não contou os campos sem .max()"; fi
if grep -q "422" <<< "$saida"; then pass "D13: acusa o status 422"; else fail "D13: não acusou o 422"; fi
[ "$status_code" -eq 1 ] && pass "rota sem autenticação = FALHA (saída 1)" || fail "rota sem autenticação saiu com $status_code"
status_code=0
(cd "$FAKE" && bash "$FERRAMENTAS/back-review.sh" api-boa >/dev/null 2>&1) || status_code=$?
[ "$status_code" -eq 0 ] && pass "rota limpa sai com 0" || fail "rota limpa saiu com $status_code"
resumo=$(cd "$FAKE" && bash "$FERRAMENTAS/back-review.sh" api-ruim --resumo 2>&1 || true)
if grep -q "RESUMO" <<< "$resumo" && ! grep -q "\[1/7\]" <<< "$resumo"; then pass "--resumo funciona"; else fail "--resumo não funciona"; fi

# ─── 3. engine-test-api ──────────────────────────────────────
echo ""
echo "[3] engine-test-api.sh"
cat > "$FAKE/.delta-11/memoria/project-core/contratos.md" <<'MD'
# Contratos
- GET /api/users — lista (precisa de login)
- POST /api/users — cria
- DELETE /api/users/:id — apaga
- GET /api/x;touch${IFS}ARQUIVO_INVADIDO
- GET /api/$(touch ARQUIVO_INVADIDO_2)
MD
cat > "$FAKE/servidor.py" <<'PY'
import http.server, json, sys
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def reply(self, code, body=b"{}"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path == "/":
            self.reply(200)
        elif self.path == "/api/users":
            self.reply(401)
        else:
            self.reply(404)
    def do_POST(self):
        body = {"error": {"code": "VALIDATION_ERROR", "message": "campo faltando", "details": []}}
        self.reply(400, json.dumps(body).encode())
    def do_DELETE(self):
        open(sys.argv[2], "w").write("DELETE chamado")
        self.reply(200)
server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
open(sys.argv[1], "w").write(str(server.server_address[1]))
server.serve_forever()
PY
python3 "$FAKE/servidor.py" "$FAKE/porta.txt" "$FAKE/delete-chamado.txt" &
SERVER_PID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$FAKE/porta.txt" ] && break; sleep 0.3; done
PORTA=$(cat "$FAKE/porta.txt" 2>/dev/null || true)
if [ -z "$PORTA" ]; then
    fail "servidor de teste não subiu"
else
    status_code=0
    saida=$(cd "$FAKE" && bash "$FERRAMENTAS/engine-test-api.sh" "http://127.0.0.1:$PORTA" 2>&1) || status_code=$?
    if [ ! -e "$FAKE/ARQUIVO_INVADIDO" ] && [ ! -e "$FAKE/ARQUIVO_INVADIDO_2" ]; then
        pass "C-135: rota maliciosa NÃO executou comando"
    else
        fail "C-135: rota maliciosa executou comando!"
    fi
    if grep -q "IGNORADA" <<< "$saida"; then pass "rota com caractere proibido é ignorada com aviso"; else fail "rota maliciosa não foi sinalizada"; fi
    if grep -q "project-core/contratos.md" <<< "$saida"; then pass "D6: lê a fatia project-core/contratos.md"; else fail "D6: não leu a fatia de contratos"; fi
    if grep -q "PASS  GET /api/users → 401" <<< "$saida"; then pass "GET protegido (401) passa"; else fail "GET protegido não passou"; fi
    if grep -q "PULADO POST /api/users" <<< "$saida"; then pass "POST pulado sem --incluir-escrita"; else fail "POST rodou sem --incluir-escrita"; fi
    if [ ! -e "$FAKE/delete-chamado.txt" ]; then pass "DELETE nunca é chamado"; else fail "DELETE foi chamado!"; fi
    [ "$status_code" -eq 0 ] && pass "resultado PASS (saída 0)" || fail "saída $status_code: $(grep FAIL <<< "$saida" | head -2)"
    saida=$(cd "$FAKE" && bash "$FERRAMENTAS/engine-test-api.sh" "http://127.0.0.1:$PORTA" --incluir-escrita 2>&1 || true)
    if grep -q "PASS  POST /api/users → 400" <<< "$saida" && ! grep -q "fora do formato D13" <<< "$saida"; then
        pass "D13: POST com {} recebe 400 no formato VALIDATION_ERROR"
    else
        fail "D13: POST com --incluir-escrita não conferiu o 400"
    fi
fi

# ─── 4. scout-lighthouse ─────────────────────────────────────
echo ""
echo "[4] scout-lighthouse.sh"
if command -v lighthouse >/dev/null 2>&1; then
    skip "lighthouse instalado nesta máquina — o caso 'programa ausente' não pode ser simulado"
else
    status_code=0
    saida=$(cd "$FAKE" && bash "$FERRAMENTAS/scout-lighthouse.sh" "http://127.0.0.1:${PORTA:-1}" 2>&1) || status_code=$?
    if [ "$status_code" -eq 2 ] && grep -q "INCOMPLETO" <<< "$saida"; then
        pass "C-136: sem Lighthouse sai INCOMPLETO (2), não 'pulado com 0'"
    else
        fail "C-136: sem Lighthouse saiu com $status_code"
    fi
fi

# ─── 5. shield-scan ──────────────────────────────────────────
echo ""
echo "[5] shield-scan.sh"
mkdir -p "$FAKE/codigo-com-senha" "$FAKE/codigo-limpo"
echo "const password = 'senha-super-secreta-123';" > "$FAKE/codigo-com-senha/config.ts"
echo 'export const greeting = "ola";' > "$FAKE/codigo-limpo/index.ts"
status_code=0
saida=$(bash "$FERRAMENTAS/shield-scan.sh" "$FAKE/codigo-com-senha" 2>&1) || status_code=$?
if grep -q "config.ts" <<< "$saida" && [ "$status_code" -eq 1 ]; then
    pass "C-137: acha password='...' (aspas simples) e reprova"
else
    fail "C-137: senha entre aspas simples passou (saída $status_code)"
fi
status_code=0
(bash "$FERRAMENTAS/shield-scan.sh" "$FAKE/codigo-limpo" >/dev/null 2>&1) || status_code=$?
if command -v semgrep >/dev/null 2>&1; then
    [ "$status_code" -ne 1 ] && pass "código limpo não reprova" || fail "código limpo reprovou"
else
    [ "$status_code" -eq 2 ] && pass "C-137: sem semgrep o resultado é INCOMPLETO (2), não PASS" || fail "sem semgrep saiu com $status_code"
fi

# ─── 6. vault-validate-sql ───────────────────────────────────
echo ""
echo "[6] vault-validate-sql.sh"
mkdir -p "$FAKE/banco/supabase/migrations"
cat > "$FAKE/banco/supabase/migrations/20261014000001_users.sql" <<'SQL'
-- tabela de usuarios (minusculas de proposito)
create table if not exists public.users (
  id uuid primary key,
  name text not null
);
alter table public.users enable row level security;
create table orders (
  id uuid primary key,
  user_id uuid references users(id) on delete cascade,
  coupon_id uuid references coupons(id),
  total numeric(10, 2)
);
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
SQL
status_code=0
saida=$(bash "$FERRAMENTAS/vault-validate-sql.sh" "$FAKE/banco" 2>&1) || status_code=$?
if grep -q "todas as tabelas com RLS" <<< "$saida"; then pass "C-138: RLS em minúsculas e maiúsculas reconhecido"; else fail "C-138: RLS em minúsculas não reconhecido"; fi
if grep -q "1 FK(s) sem ON DELETE" <<< "$saida"; then pass "C-138: ON DELETE conferido por chave estrangeira (1 de 2 sem)"; else fail "C-138: contagem de FK sem ON DELETE errada"; fi
[ "$status_code" -eq 0 ] && pass "só avisos = saída 0" || fail "só avisos saiu com $status_code"
echo "create table extra (id int);" > "$FAKE/banco/supabase/migrations/20261014000001_extra.sql"
status_code=0
(bash "$FERRAMENTAS/vault-validate-sql.sh" "$FAKE/banco" >/dev/null 2>&1) || status_code=$?
[ "$status_code" -eq 1 ] && pass "timestamp duplicado = FAIL (saída 1)" || fail "timestamp duplicado saiu com $status_code"
mkdir -p "$FAKE/sem-sql/migrations"
status_code=0
(bash "$FERRAMENTAS/vault-validate-sql.sh" "$FAKE/sem-sql" >/dev/null 2>&1) || status_code=$?
[ "$status_code" -eq 0 ] && pass "pasta de migrations vazia não derruba o script" || fail "pasta vazia saiu com $status_code"

# ─── 7. verificar-dependencias ───────────────────────────────
echo ""
echo "[7] verificar-dependencias.sh"
status_code=0
saida=$(bash "$FERRAMENTAS/verificar-dependencias.sh" CRONOS 2>&1) || status_code=$?
if grep -q "RESULTADO:" <<< "$saida"; then pass "roda para CRONOS"; else fail "não rodou para CRONOS (saída $status_code)"; fi
status_code=0
(bash "$FERRAMENTAS/verificar-dependencias.sh" AGENTE-QUE-NAO-EXISTE >/dev/null 2>&1) || status_code=$?
[ "$status_code" -eq 0 ] && pass "agente sem ferramentas: saída 0" || fail "agente sem ferramentas saiu com $status_code"

finish_test "ferramentas dos agentes"
