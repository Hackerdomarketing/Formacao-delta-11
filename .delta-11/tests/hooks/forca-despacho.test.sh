#!/usr/bin/env bash
# Teste do vigia forca-despacho.py (v6.3 — C-029, C-036, D32)
source "$(dirname "$0")/_ajudante-hooks-python.sh" forca-despacho
checagens_basicas

novo_projeto
LOGS="$TEST_DIR/.delta-11/logs/sub-agentes"
BASE=$'# Kanban\n## ⚡ FAZENDO\n**T-012** — rota de pedidos | Agente: BACK | Início: 2026-10-14T10:00:00-03:00\n**T-013** — tela | Agente: PIXEL\n## ✅ CONCLUÍDO\n**T-001** — antiga | Por: BACK | Aprovado: SHIELD | Data: 2026-10-01'
kanban "$BASE"
conclui() { evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE"$'\n'"$1"; }
log_sub() { # log_sub ARQUIVO SUBAGENTE DONO
    printf 'evento: SubagentStop\nagent_type: general-purpose\nagent_id: a1\nagente_delta11: %s\nsubagente_detectado: %s\n--- ultima mensagem ---\nPASS\n' "$3" "$2" > "$LOGS/$1"
}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

espera 0 "reescrever o kanban com a tarefa antiga ja concluida: passa (C-036)" "$(evento tool_name=Write tool_input.file_path=.delta-11/kanban.md "tool_input.content=$BASE")"
espera 2 "BACK conclui T-012 sem log de sub-agente: bloqueia" "$(conclui '**T-012** — rota de pedidos | Por: BACK | Aprovado: SHIELD')"
stderr_contem "build-validator"
espera 2 "tarefa concluida SEM dono: bloqueia (nao da para fugir tirando a etiqueta)" "$(conclui '**T-012** — rota de pedidos | Aprovado: SHIELD')"
stderr_contem "sem dono"

log_sub "$STAMP-general-purpose.log" build-validator BACK
espera 2 "so build-validator: BACK ainda precisa do contract-tester" "$(conclui '**T-012** — rota de pedidos | Por: BACK')"
stderr_contem "contract-tester"
log_sub "${STAMP}-general-purpose-2.log" contract-tester BACK
espera 0 "build-validator + contract-tester do BACK na janela: passa" "$(conclui '**T-012** — rota de pedidos | Por: BACK')"

espera 2 "log de OUTRO dono (BACK) nao vale para PIXEL" "$(conclui '**T-013** — tela | Por: PIXEL')"
log_sub "${STAMP}-general-purpose-3.log" build-validator -
espera 0 "log de build-validator SEM dono identificado vale para PIXEL" "$(conclui '**T-013** — tela | Por: PIXEL')"

# log antigo (5 h) nao conta — horario vem do nome do arquivo
novo_projeto
LOGS="$TEST_DIR/.delta-11/logs/sub-agentes"
kanban "$BASE"
VELHO=$(python3 -c "import datetime; print((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=5)).strftime('%Y%m%dT%H%M%SZ'))")
log_sub "$VELHO-general-purpose.log" build-validator PIXEL
espera 2 "log de 5 h atras: fora da janela de 4 h" "$(conclui '**T-013** — tela | Por: PIXEL')"
echo '{"janela_horas": 6}' > .delta-11/.config-limites.json
espera 0 "janela_horas=6 no .config-limites.json: o mesmo log vale (D36)" "$(conclui '**T-013** — tela | Por: PIXEL')"

# relatorio antigo, sem as linhas estruturadas: reconhece pelo conteudo
novo_projeto
LOGS="$TEST_DIR/.delta-11/logs/sub-agentes"
kanban "$BASE"
printf '## Build Validation Report\nAgente: PIXEL\nReady for Deploy: YES\n' > "$LOGS/$STAMP-general-purpose.log"
espera 0 "relatorio 'Build Validation Report' citando PIXEL: passa" "$(conclui '- [x] T-013 tela [PIXEL]')"
espera 0 "ATLAS e isento" "$(conclui '**T-090** — arquitetura | Por: ATLAS')"
# Trilho leve (v6.4.1): [AJUSTE] nao exige validadores
rm -f "$LOGS"/*  # sem nenhum log de sub-agente daqui em diante
espera 0 "[AJUSTE] de PIXEL sem log de validador: isento" "$(conclui '**T-290** — [AJUSTE] cor do selo | Por: PIXEL')"
log_contem "forca-despacho.*ISENTO.*trilho leve"
espera 2 "a mesma tarefa SEM [AJUSTE]: continua exigindo o validador" "$(conclui '**T-291** — cor do selo | Por: PIXEL')"
fim
