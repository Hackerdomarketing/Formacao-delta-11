#!/usr/bin/env bash
# Teste do vigia topologia-deploy.py (v6.3 — C-040)
source "$(dirname "$0")/_ajudante-hooks-python.sh" topologia-deploy
checagens_basicas

novo_projeto
bash_ev() { evento tool_name=Bash "tool_input.command=$1"; }
TOPO="$TEST_DIR/.delta-11/memoria/topologia.json"

espera 2 "wrangler deploy sem topologia: bloqueia" "$(bash_ev 'npm run build && npx wrangler deploy')"
stderr_contem "topologia.json"
espera 2 "vercel --prod sem topologia: bloqueia" "$(bash_ev 'vercel --prod')"
espera 2 "npm run deploy sem topologia: bloqueia" "$(bash_ev 'CI=1 npm run deploy')"
espera 0 "--dry-run nao e deploy" "$(bash_ev 'wrangler deploy --dry-run')"
espera 0 "git commit com a palavra deploy nao e deploy" "$(bash_ev "git commit -m 'ajusta deploy do worker'")"
espera 0 "grep deploy nao e deploy" "$(bash_ev 'grep -rn deploy docs/')"
espera 0 "echo de texto com deploy nao e deploy" "$(bash_ev 'echo "rode wrangler deploy depois"')"

# Texto com a palavra deploy em documento/kanban NAO bloqueia mais (N-005)
espera 0 "Write de doc com 'deploy': passa" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/docs/deploy.md 'tool_input.content=# Como fazer o deploy')"
espera 0 "Edit do kanban com 'deploy': passa" "$(evento tool_name=Edit tool_input.file_path=.delta-11/kanban.md tool_input.old_string=a 'tool_input.new_string=T-9 deploy automatico')"
espera 0 "artefato descanso-04-deploy-auto: passa" "$(evento tool_name=Write tool_input.file_path=$TEST_DIR/.delta-11/memoria/decisoes/2026-10-14-descanso-04-deploy-auto.md 'tool_input.content=deploy auto')"

echo '{"app_url": "https://app.exemplo.com"}' > "$TOPO"
espera 0 "topologia com UMA url (app de uma parte so): passa" "$(bash_ev 'npx wrangler deploy')"
echo '{"worker_url": "https://api.exemplo.com", "pages_url": "https://admin.exemplo.com"}' > "$TOPO"
espera 0 "topologia worker + pages: passa" "$(bash_ev 'wrangler pages deploy dist')"
echo '{"tipo": "worker"}' > "$TOPO"
espera 2 "topologia sem nenhuma url: bloqueia" "$(bash_ev 'wrangler deploy')"
echo 'quebrado' > "$TOPO"
espera 2 "topologia.json invalido: bloqueia" "$(bash_ev 'firebase deploy')"
fim
