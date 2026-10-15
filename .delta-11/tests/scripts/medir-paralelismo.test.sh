#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# Teste do medir-paralelismo.py (v6.4 — V12)
# ════════════════════════════════════════════════════════════════
#
# Monta projetos FALSOS numa pasta temporária, com HOME temporário (as
# transcrições falsas do Claude Code ficam em $HOME/.claude/projects), e
# confere as contas em 3 cenários + casos de borda:
#   S1 tudo em série (3 agentes, 2 buracos de 5 min) → média 0,83, 0 agentes 16,7%
#   S2 3 em paralelo                                  → média 3,00, pico 3
#   S3 buraco de 2 h                                  → descontado 2 h; média 1,00
#                                                       (--sem-descontar: 0,33)
#   Cada cenário roda por TRANSCRIÇÃO e por LOGS (início no activity-log, nos
#   2 formatos, + fim no log do SubagentStop).
#   S2 com logs E transcrições: o mesmo sub-agente não conta 2 vezes.
#   S2: o CRONOS fica fora da conta (--incluir-orquestrador o conta).
#   S4 pareamento conservador: início sem fim fica fora; fim pega o início mais
#      recente; despacho sem fim + pulso vira trecho até o último sinal.
#   S5 agente retomado 1 h depois vira 2 trechos; o que espera um filho, não;
#      --sem-aninhados tira o filho da conta.
#   Somente leitura: os projetos e o HOME não mudam. Uso errado sai com 2.
# ════════════════════════════════════════════════════════════════

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FERRAMENTA="$RAIZ/.delta-11/ferramentas/medir-paralelismo.py"

falhou=0
ok() { echo -e "  ${GREEN}[OK]${NC}   $1"; }
err() { echo -e "  ${RED}[FALTA]${NC} $1"; falhou=$((falhou + 1)); }

[ -f "$FERRAMENTA" ] || { echo -e "${RED}[FALTA]${NC} ferramenta não encontrada: $FERRAMENTA"; exit 1; }

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/delta11-medir-paralelismo-XXXXXX")"
SANDBOX="$(cd "$SANDBOX" && pwd -P)"
cleanup() {
    if [ -n "${SANDBOX:-}" ] && [ -d "$SANDBOX" ] && [[ "$SANDBOX" == *delta11-medir-paralelismo-* ]]; then
        rm -rf "$SANDBOX"
    fi
}
trap cleanup EXIT
export HOME="$SANDBOX/home"; mkdir -p "$HOME"
unset CLAUDE_CONFIG_DIR CLAUDE_PROJECT_DIR || true

# ─── Gerador dos projetos falsos ─────────────────────────────
python3 - "$SANDBOX" <<'PY'
import json, os, re, sys, datetime as dt

SANDBOX = sys.argv[1]
HOME = os.path.join(SANDBOX, "home")
DIA = "2026-10-14"

def t(hhmm):
    return dt.datetime.strptime(DIA + " " + hhmm, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)

def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def slug(caminho):
    return re.sub(r"[^A-Za-z0-9]", "-", caminho)

def novo_projeto(nome):
    p = os.path.join(SANDBOX, nome)
    for sub in ("ativacoes", "logs/sub-agentes", "sub-agentes"):
        os.makedirs(os.path.join(p, ".delta-11", sub), exist_ok=True)
    open(os.path.join(p, ".delta-11", "sub-agentes", "build-validator.md"), "w").write("# bv\n")
    return p

def pasta_sessao(p, sessao):
    d = os.path.join(HOME, ".claude", "projects", slug(p), sessao)
    os.makedirs(os.path.join(d, "subagents"), exist_ok=True)
    return d

def linhas_por_minuto(ini, fim, primeira):
    linhas = [{"type": "user", "timestamp": iso(ini), "message": {"role": "user", "content": primeira}}]
    agora = ini + dt.timedelta(minutes=1)
    while agora < fim:
        linhas.append({"type": "assistant", "timestamp": iso(agora),
                       "message": {"role": "assistant", "content": [{"type": "text", "text": "trabalhando"}]}})
        agora += dt.timedelta(minutes=1)
    linhas.append({"type": "assistant", "timestamp": iso(fim),
                   "message": {"role": "assistant", "content": [{"type": "text", "text": "pronto"}]}})
    return linhas

def gravar_jsonl(caminho, linhas):
    with open(caminho, "w") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")

def transcricao_subagente(p, sessao, agent_id, nome, ini, fim, descricao=None):
    d = pasta_sessao(p, sessao)
    caminho = os.path.join(d, "subagents", "agent-%s.jsonl" % agent_id)
    gravar_jsonl(caminho, linhas_por_minuto(ini, fim, "Formação Δ-11 v6.4 — Ativação de agente.\n\nAgente: %s\nTarefa: T-1" % nome))
    meta = {"agentType": "general-purpose", "description": descricao or ("Ativação %s" % nome)}
    json.dump(meta, open(caminho[:-6] + ".meta.json", "w"))
    return caminho

def sessao_principal(p, sessao, trechos):
    """Conversa do comandante: uma linha por minuto nos trechos dados (sinal de atividade)."""
    d = pasta_sessao(p, sessao)
    linhas = []
    for ini, fim in trechos:
        linhas += linhas_por_minuto(ini, fim, "d11")
    gravar_jsonl(d + ".jsonl", linhas)

def despacho(p, quando, nome, formato_novo):
    with open(os.path.join(p, ".delta-11", "activity-log.md"), "a") as f:
        if formato_novo:
            f.write("- [%s] [pre-despacho] [MAIN] Despacho de %s OK (651 tokens ≤ 4000)\n" % (quando.strftime("%Y-%m-%dT%H:%M:%SZ"), nome))
        else:
            f.write("[%s] pre-despacho: Despacho de %s OK (651 tokens ≤ 2000)\n" % (quando.strftime("%Y-%m-%dT%H:%M:%SZ"), nome))

def fim_log(p, arquivo, quando, nome, agent_id="-", transcricao="-"):
    caminho = os.path.join(p, ".delta-11", "logs", "sub-agentes", arquivo)
    with open(caminho, "a") as f:
        f.write("evento: SubagentStop\nquando: %s\nagent_type: general-purpose\nagent_id: %s\n"
                "agente_delta11: %s\nsubagente_detectado: -\nsession_id: S1\ntranscricao: %s\n"
                "--- ultima mensagem ---\npronto: %s\n\n"
                % (quando.strftime("%Y-%m-%dT%H:%M:%SZ"), agent_id, nome, transcricao, nome))

CENARIOS = {
    "s1": [("FRONT", "13:00", "13:20"), ("PIXEL", "13:25", "13:45"), ("FORM", "13:50", "14:00")],
    "s2": [("FRONT", "13:00", "13:30"), ("PIXEL", "13:00", "13:30"), ("FORM", "13:00", "13:30")],
    "s3": [("FRONT", "13:00", "13:30"), ("PIXEL", "15:30", "16:00")],
}
JANELA = {"s1": ("13:00", "14:00"), "s2": ("13:00", "13:30"), "s3": ("13:00", "16:00")}

for cen, agentes in CENARIOS.items():
    # (a) só transcrições
    p = novo_projeto(cen + "-transcricoes")
    for i, (nome, a, b) in enumerate(agentes):
        transcricao_subagente(p, "sessao-1", "a%s%d" % (cen, i), nome, t(a), t(b))
    if cen == "s3":
        sessao_principal(p, "sessao-1", [(t("13:00"), t("13:30")), (t("15:30"), t("16:00"))])
    else:
        sessao_principal(p, "sessao-1", [(t(JANELA[cen][0]), t(JANELA[cen][1]))])
    if cen == "s2":
        # O CRONOS fica a janela toda vivo (só coordena) — não entra na conta.
        transcricao_subagente(p, "sessao-1", "acronos", "CRONOS", t("13:00"), t("13:30"), "CRONOS conduz o Ciclo 1")
    # (b) só logs: início no activity-log (2 formatos) + fim no SubagentStop
    p = novo_projeto(cen + "-logs")
    for i, (nome, a, b) in enumerate(agentes):
        despacho(p, t(a), nome, formato_novo=(i % 2 == 1))
        # Dois fins no MESMO arquivo (mesmo segundo, mesmo tipo) também são lidos.
        fim_log(p, "%sT000000Z-general-purpose.log" % DIA.replace("-", "") if i else "fim-%d.log" % i, t(b), nome)
    with open(os.path.join(p, ".delta-11", "activity-log.md"), "a") as f:
        f.write("- [2026-10-14T13:05:00Z] [pre-despacho] [MAIN] BLOQUEIO: despacho de VAULT com 9000 tokens > 4000\n")

# S2 com logs E transcrições: cada sub-agente aparece nas duas fontes.
p = novo_projeto("s2-ambos")
for i, (nome, a, b) in enumerate(CENARIOS["s2"]):
    caminho = transcricao_subagente(p, "sessao-1", "ab%d" % i, nome, t(a), t(b))
    despacho(p, t(a), nome, formato_novo=True)
    fim_log(p, "fim-%d.log" % i, t(b), nome, agent_id="ab%d" % i, transcricao=caminho)
sessao_principal(p, "sessao-1", [(t("13:00"), t("13:30"))])

# S4: pareamento conservador e pulso (só logs).
p = novo_projeto("s4-pareamento")
despacho(p, t("13:00"), "FRONT", True)      # morreu sem fim registrado
despacho(p, t("14:00"), "FRONT", True)
fim_log(p, "fim-front.log", t("14:30"), "FRONT")
despacho(p, t("14:10"), "PIXEL", False)     # ainda sem fim; o pulso diz que viveu até 14:50
json.dump({"agente": "PIXEL", "status": "ativo", "ultimo_sinal": "2026-10-14T14:50:00Z"},
          open(os.path.join(p, ".delta-11", "ativacoes", "pulso-PIXEL.json"), "w"))

# S5: agente retomado horas depois vira 2 trechos; agente esperando um filho não.
p = novo_projeto("s5-retomada")
d = pasta_sessao(p, "sessao-1")
gravar_jsonl(os.path.join(d, "subagents", "agent-aengine.jsonl"),
             linhas_por_minuto(t("13:00"), t("13:20"), "Agente: ENGINE")
             + linhas_por_minuto(t("14:20"), t("14:30"), "retome"))
json.dump({"description": "Ativação ENGINE"}, open(os.path.join(d, "subagents", "agent-aengine.meta.json"), "w"))
gravar_jsonl(os.path.join(d, "subagents", "agent-ashield.jsonl"),
             linhas_por_minuto(t("13:00"), t("13:05"), "Agente: SHIELD") + linhas_por_minuto(t("13:50"), t("14:00"), "x"))
json.dump({"description": "SHIELD revisa a onda"}, open(os.path.join(d, "subagents", "agent-ashield.meta.json"), "w"))
# O filho termina 2 min antes de o pai voltar a escrever (folga curta não divide).
gravar_jsonl(os.path.join(d, "subagents", "agent-abv.jsonl"),
             linhas_por_minuto(t("13:05"), t("13:48"), "Leia .delta-11/sub-agentes/build-validator.md e siga"))
json.dump({"description": "Validar build", "parentAgentId": "ashield"}, open(os.path.join(d, "subagents", "agent-abv.meta.json"), "w"))
sessao_principal(p, "sessao-1", [(t("13:00"), t("14:30"))])

os.makedirs(os.path.join(SANDBOX, "sem-delta"), exist_ok=True)
PY

# ─── Foto da pasta (para provar que nada foi gravado) ────────
foto() {
    python3 - "$SANDBOX" <<'PY'
import hashlib, os, sys
for raiz, pastas, arquivos in sorted(os.walk(sys.argv[1])):
    pastas.sort()
    for a in sorted(arquivos):
        c = os.path.join(raiz, a)
        print(c, os.path.getmtime(c), hashlib.md5(open(c, "rb").read()).hexdigest())
    for d in pastas:
        print(os.path.join(raiz, d) + "/")
PY
}
FOTO_ANTES="$(foto)"

medir() {   # medir <projeto> <desde HH:MM> <ate HH:MM> [opções...] → JSON
    local p="$1" a="$2" b="$3"; shift 3
    python3 "$FERRAMENTA" "$SANDBOX/$p" --desde "2026-10-14T${a}:00Z" --ate "2026-10-14T${b}:00Z" --json "$@"
}

# confere <rótulo> <json> <expressão python sobre d>
confere() {
    if python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if eval(sys.argv[2]) else 1)' "$2" "$3"; then
        ok "$1"
    else
        err "$1 — esperado: $3 | obtido: $(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print({k: d[k] for k in ("tempo_ativo_s","tempo_com_zero_s","tempo_com_zero_pct","media_simultaneos","pico","sub_agentes","descontado","buracos")})' "$2" 2>&1 | head -c 900)"
    fi
}

echo "[0] sintaxe"
# ast.parse em vez de py_compile: não grava __pycache__ ao lado da ferramenta.
python3 -c 'import ast,sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$FERRAMENTA" && ok "sintaxe Python" || err "erro de sintaxe"
grep -qE '(^|[^.a-z])/tmp/' "$FERRAMENTA" && err "usa /tmp (D21)" || ok "não usa /tmp (D21)"
grep -qE '^\s*(import|from)\s+(requests|numpy|pandas|dateutil)' "$FERRAMENTA" && err "usa biblioteca externa" || ok "só Python puro"

for modo in transcricoes logs; do
    echo ""
    echo "[S1 — tudo em série, por $modo]"
    j="$(medir "s1-$modo" 13:00 14:00)"
    confere "3 sub-agentes" "$j" 'd["sub_agentes"]["total"] == 3'
    confere "média 0,83 (50 de 60 min com 1 agente)" "$j" 'd["media_simultaneos"] == 0.83'
    confere "0 agentes: 10 min = 16,7%" "$j" 'd["tempo_com_zero_s"] == 600 and d["tempo_com_zero_pct"] == 16.7'
    confere "pico 1" "$j" 'd["pico"]["agentes"] == 1'
    confere "2 buracos de 5 min, às 13:20 e 13:45" "$j" '[(b["inicio"][11:16], b["duracao_s"]) for b in d["buracos"]] in ([("13:20", 300), ("13:45", 300)], [("13:45", 300), ("13:20", 300)])'
    confere "nada descontado" "$j" 'd["descontado"]["total_s"] == 0'

    echo ""
    echo "[S2 — 3 em paralelo, por $modo]"
    j="$(medir "s2-$modo" 13:00 13:30)"
    confere "3 sub-agentes" "$j" 'd["sub_agentes"]["total"] == 3'
    confere "média 3,00" "$j" 'd["media_simultaneos"] == 3.0'
    confere "pico 3" "$j" 'd["pico"]["agentes"] == 3'
    confere "0 agentes: 0%" "$j" 'd["tempo_com_zero_s"] == 0 and d["buracos"] == []'

    echo ""
    echo "[S3 — buraco de 2 h, por $modo]"
    j="$(medir "s3-$modo" 13:00 16:00)"
    confere "2 h descontadas (máquina dormindo / comandante ausente)" "$j" 'd["descontado"]["total_s"] == 7200 and len(d["descontado"]["trechos"]) == 1 and d["descontado"]["trechos"][0]["inicio"][11:16] == "13:30"'
    confere "tempo ativo 1 h; média 1,00; 0 agentes 0%" "$j" 'd["tempo_ativo_s"] == 3600 and d["media_simultaneos"] == 1.0 and d["tempo_com_zero_s"] == 0'
    j="$(medir "s3-$modo" 13:00 16:00 --sem-descontar)"
    confere "--sem-descontar: média 0,33 e 2 h paradas (66,7%)" "$j" 'd["descontado"]["total_s"] == 0 and d["media_simultaneos"] == 0.33 and d["tempo_com_zero_s"] == 7200 and d["tempo_com_zero_pct"] == 66.7'
    confere "--sem-descontar: o maior buraco é o de 2 h" "$j" 'd["buracos"][0]["duracao_s"] == 7200'
done

echo ""
echo "[S2 — logs E transcrições juntos]"
j="$(medir s2-ambos 13:00 13:30)"
confere "cada sub-agente conta 1 vez (3, não 6)" "$j" 'd["sub_agentes"]["total"] == 3 and d["sub_agentes"]["por_fonte"] == {"transcricao": 3}'
confere "média 3,00 e nenhum aviso de início/fim solto" "$j" 'd["media_simultaneos"] == 3.0 and d["avisos"] == []'

echo ""
echo "[S2 — orquestrador]"
j="$(medir s2-transcricoes 13:00 13:30)"
confere "CRONOS fora da conta por padrão" "$j" '"CRONOS" not in d["sub_agentes"]["por_nome"] and d["orquestrador_fora_da_conta"] == ["CRONOS"]'
j="$(medir s2-transcricoes 13:00 13:30 --incluir-orquestrador)"
confere "--incluir-orquestrador: 4 agentes, média 4,00" "$j" 'd["sub_agentes"]["total"] == 4 and d["media_simultaneos"] == 4.0'

echo ""
echo "[S4 — pareamento conservador e pulso]"
j="$(medir s4-pareamento 13:00 15:00)"
confere "fim das 14:30 pega o início MAIS RECENTE (14:00), não o das 13:00" "$j" 'd["sub_agentes"]["por_fonte"].get("logs") == 1'
confere "início das 13:00 sem fim fica fora e vira aviso" "$j" '[x["agente"] for x in d["fora_da_conta"]["inicio_sem_fim"]] == ["FRONT"] and d["fora_da_conta"]["inicio_sem_fim"][0]["quando"][11:16] == "13:00"'
confere "despacho sem fim + pulso: trecho até o último sinal (14:50)" "$j" 'd["sub_agentes"]["por_fonte"].get("pulso") == 1'
confere "1 h descontada (13:00→14:00 sem nada); média 1,17; pico 2" "$j" 'd["descontado"]["total_s"] == 3600 and d["media_simultaneos"] == 1.17 and d["pico"]["agentes"] == 2 and d["tempo_com_zero_s"] == 600'

echo ""
echo "[S5 — agente retomado e agente esperando um filho]"
j="$(medir s5-retomada 13:00 14:30)"
confere "3 agentes (ENGINE, SHIELD, build-validator pelo prompt)" "$j" 'd["sub_agentes"]["por_nome"] == {"ENGINE": 1, "SHIELD": 1, "build-validator": 1}'
confere "ENGINE parado 1 h na própria transcrição não conta; SHIELD esperando o filho conta" "$j" 'd["media_simultaneos"] == 1.48 and d["tempo_com_zero_s"] == 1200 and d["buracos"][0]["inicio"][11:16] == "14:00"'

j="$(medir s5-retomada 13:00 14:30 --sem-aninhados)"
confere "--sem-aninhados: o build-validator do SHIELD sai da conta (média 1,00)" "$j" 'd["sub_agentes"]["por_nome"] == {"ENGINE": 1, "SHIELD": 1} and d["media_simultaneos"] == 1.0'

echo ""
echo "[Saída para leigo e opções]"
saida="$(python3 "$FERRAMENTA" "$SANDBOX/s1-logs" --desde 2026-10-14T10:00:00-03:00 --ate 2026-10-14T11:00:00-03:00)"
for trecho in "Período analisado: 14/10/2026 10:00 → 14/10/2026 11:00 (horário -03:00)" "Tempo com 0 agentes trabalhando: 10 min = 17% do tempo ativo" \
              "Média de agentes trabalhando ao mesmo tempo: 0,83" "Pico: 1 agente" "maiores buracos" "14/10 10:20 → 10:25" "Descontado: 0 s" "Sub-agentes que rodaram: 3"; do
    grep -qF -- "$trecho" <<< "$saida" && ok "texto: $trecho" || err "texto ausente: $trecho"
done
j="$(python3 "$FERRAMENTA" "$SANDBOX/s1-logs" --ultimas-horas 2 --json)"
confere "--ultimas-horas 2: período de 2 h" "$j" 'd["tempo_total_s"] == 7200'
j="$(python3 "$FERRAMENTA" "$SANDBOX/s1-transcricoes" --json)"
confere "sem --desde/--ate: período = da primeira à última atividade" "$j" 'd["tempo_total_s"] == 3600 and d["sub_agentes"]["total"] == 3'
j="$(medir s2-transcricoes 13:00 13:30 --sem-transcricoes)"
confere "--sem-transcricoes: sem logs, nenhum sub-agente" "$j" 'd["sub_agentes"]["total"] == 0'

echo ""
echo "[Uso errado → saída 2]"
for args in "$SANDBOX/nao-existe" "$SANDBOX/sem-delta" "$SANDBOX/s1-logs --desde ontem" "$SANDBOX/s1-logs --desde 2026-10-14T14:00:00Z --ate 2026-10-14T13:00:00Z"; do
    codigo=0
    # shellcheck disable=SC2086
    python3 "$FERRAMENTA" $args >/dev/null 2>&1 || codigo=$?
    [ "$codigo" -eq 2 ] && ok "saída 2: ${args//$SANDBOX\//}" || err "saída $codigo (esperado 2): $args"
done

echo ""
echo "[Somente leitura]"
FOTO_DEPOIS="$(foto)"
[ "$FOTO_ANTES" = "$FOTO_DEPOIS" ] && ok "nenhum arquivo criado ou alterado nos projetos nem no HOME" || {
    err "a ferramenta mexeu em arquivos:"; diff <(echo "$FOTO_ANTES") <(echo "$FOTO_DEPOIS") | head -10; }

echo ""
if [ "$falhou" -eq 0 ]; then
    echo -e "${GREEN}OK — medir-paralelismo.py${NC}"
    exit 0
fi
echo -e "${RED}FALTA $falhou item(ns) — medir-paralelismo.py${NC}"
exit 1
