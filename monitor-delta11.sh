#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# FORMAÇÃO Δ-11 — Monitor Invisível (v6.3)
# ═══════════════════════════════════════════════════════════════
#
# Executado pelo LaunchAgent do macOS a cada 5 minutos (o plist é gerado
# pelo instalar.sh com o caminho real deste arquivo — C-062).
# NUNCA abre janela. NUNCA mexe no cursor. Só lê arquivos e manda uma
# notificação discreta no canto da tela.
#
# Para cada projeto com Δ-11 (registro central + varredura de pastas):
#   1. "morte-*.json"  → avisa UMA vez e arquiva em .delta-11/logs/mortes/ (C-064)
#   2. pulso velho     → agente ativo sem sinal há mais de 15 min = travado
#                        (avisa uma vez por pulso, não a cada 5 min)
#   3. tarefa órfã     → tarefa em FAZENDO sem ACK e sem pulso recente
#   4. operação autônoma (Dia 7 / Fase 7 da Metodologia Genesis, Teste
#      Supremo de 2 semanas): THRESHOLD_DIAS=14 dias sem atividade, ZERO
#      tarefas em FAZENDO (somando todos os agentes), nenhuma órfã e o
#      projeto na Fase 7. Parado fora disso é ABANDONO, não consagração (C-065).
#
# Cada projeto recebe SÓ o próprio status (C-149, D28):
#   .delta-11/monitor-status.json   (JSON)
#   .delta-11/monitor-data.js       (window.D11_MONITOR = {...}; para o painel)
#
# Pastas que não existem, worktrees de agentes e cópias do próprio sistema
# são ignoradas (C-065, C-057).
#
# Variáveis opcionais (usadas pelos testes — C-129):
#   DELTA11_REGISTRY         caminho do registro (padrão ~/.delta-11-registry.json)
#   DELTA11_SEARCH_PATHS     pastas de varredura separadas por ":"
#   DELTA11_SEM_NOTIFICACAO  =1 para não mostrar notificações
#
# ═══════════════════════════════════════════════════════════════

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

if ! command -v python3 > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERRO: python3 não encontrado — monitor não rodou" >&2
    exit 1
fi

exec python3 - "$@" << 'PYTHON_MONITOR'
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

LIMITE_SILENCIO = 900   # 15 minutos sem pulso = agente travado
THRESHOLD_DIAS = 14     # Teste Supremo do Dia 7 = 2 semanas
AGENTES = ["ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM", "BACK", "ENGINE", "VAULT", "SHIELD", "SCOUT"]

AGORA = time.time()
HOME = os.path.expanduser("~")
REGISTRO = os.environ.get("DELTA11_REGISTRY") or os.path.join(HOME, ".delta-11-registry.json")
if os.environ.get("DELTA11_SEARCH_PATHS"):
    CAMINHOS_BUSCA = [p for p in os.environ["DELTA11_SEARCH_PATHS"].split(":") if p]
else:
    CAMINHOS_BUSCA = [os.path.join(HOME, "Documents", "VSCODE"), os.path.join(HOME, "projetos"), os.path.join(HOME, "Downloads")]
SEM_NOTIFICACAO = os.environ.get("DELTA11_SEM_NOTIFICACAO") == "1"
ESTADO_NOTIFICACOES = os.path.join(HOME, ".delta-11", "monitor-notificados.json")


def iso(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def ler_texto(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def gravar_atomico(caminho, conteudo):
    pasta = os.path.dirname(caminho)
    fd, tmp = tempfile.mkstemp(dir=pasta, prefix=".monitor-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        os.replace(tmp, caminho)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def e_copia_do_sistema(pasta):
    if os.path.isdir(os.path.join(pasta, "boilerplate-delta-11-nextjs")):
        return True
    if os.path.isfile(os.path.join(pasta, ".delta-11", "CHANGELOG.md")) and os.path.isfile(os.path.join(pasta, "sincronizar.sh")):
        return True
    if os.path.isfile(os.path.join(pasta, ".delta-11", ".e-copia-do-sistema")):
        return True
    return "/construcao-delta-11/sistema-atual" in pasta


# ─── Descobrir projetos ────────────────────────────────────────
dados_registro = ler_json(REGISTRO) or {}
fonte = dados_registro.get("source") if isinstance(dados_registro, dict) else None
fonte_real = os.path.realpath(os.path.expanduser(fonte)) if fonte else None

candidatos = []
lista_registro = dados_registro.get("projects", []) if isinstance(dados_registro, dict) else []
for item in lista_registro if isinstance(lista_registro, list) else []:
    if isinstance(item, dict):
        item = item.get("path")
    if isinstance(item, str) and item:
        candidatos.append(os.path.expanduser(item))
for base in CAMINHOS_BUSCA:
    if os.path.isdir(base):
        for pasta in sorted(glob.glob(os.path.join(base, "*", ""))):
            candidatos.append(pasta.rstrip("/"))

projetos, vistos = [], set()
for c in candidatos:
    real = os.path.realpath(c)
    if real in vistos:
        continue
    vistos.add(real)
    if not os.path.isdir(os.path.join(real, ".delta-11")):
        continue                      # pasta sumiu ou não usa Δ-11 (C-065)
    if "/.claude/worktrees/" in real + "/":
        continue
    if fonte_real and real == fonte_real:
        continue
    if e_copia_do_sistema(real):
        continue                      # C-057
    projetos.append(real)


# ─── Funções de leitura do kanban ──────────────────────────────
def secao(texto, nome):
    """Linhas da seção '## ... NOME ...' até a próxima '## '."""
    linhas, dentro = [], False
    for linha in texto.splitlines():
        if linha.startswith("## "):
            dentro = nome in linha.upper()
            continue
        if dentro:
            limpa = linha.strip()
            if not limpa or limpa.startswith("<!--") or limpa == "---":
                continue
            linhas.append(limpa)
    return linhas


def tarefas_fazendo_por_agente(kanban):
    contagem = {a: 0 for a in AGENTES}
    for linha in secao(kanban, "FAZENDO"):
        m = re.search(r"Agente:\s*\**\s*\[?\s*([A-Za-z]+)", linha)
        nomes = [m.group(1).upper()] if m else [a for a in AGENTES if re.search(r"\b%s\b" % a, linha)]
        for nome in nomes:
            if nome in contagem:
                contagem[nome] += 1
    return contagem


def fase_atual(delta):
    kanban = ler_texto(os.path.join(delta, "kanban.md"))
    m = re.search(r"\*\*Fase atual:\*\*\s*(.+)", kanban)
    if m and "[" not in m.group(1)[:1]:
        return m.group(1).strip()
    dados = ler_texto(os.path.join(delta, "kanban-data.js"))
    m = re.search(r"fase_atual\s*:\s*\"([^\"]*)\"", dados)
    return m.group(1).strip() if m else ""


def epoch_do_pulso(caminho, dados):
    if isinstance(dados, dict):
        if isinstance(dados.get("epoch"), (int, float)):
            return float(dados["epoch"])
        texto = dados.get("ultimo_sinal") or dados.get("timestamp")
        if isinstance(texto, str):
            try:
                return datetime.datetime.fromisoformat(texto.replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass
    try:
        return os.path.getmtime(caminho)
    except OSError:
        return None


# ─── Estado das notificações (para não repetir a cada 5 min) ───
estado_antigo = ler_json(ESTADO_NOTIFICACOES) or {}
estado_novo = {}
mortes_msg, travados_msg, falhas_gravacao = [], [], []

for projeto in projetos:
    delta = os.path.join(projeto, ".delta-11")
    ativacoes = os.path.join(delta, "ativacoes")
    nome = os.path.basename(projeto)
    alertas = []

    # 1. Mortes: avisa uma vez e arquiva (C-064)
    pasta_mortes = os.path.join(delta, "logs", "mortes")
    for morte in sorted(glob.glob(os.path.join(ativacoes, "morte-*.json"))):
        dados = ler_json(morte) or {}
        agente = str(dados.get("agente") or os.path.basename(morte)[6:-5])
        motivo = str(dados.get("motivo") or "sem motivo registrado")
        mortes_msg.append("%s morreu em %s (%s)" % (agente, nome, motivo))
        alertas.append({"tipo": "morte", "agente": agente, "quando": dados.get("morreu_em"), "motivo": motivo})
        try:
            os.makedirs(pasta_mortes, exist_ok=True)
            shutil.move(morte, os.path.join(pasta_mortes, os.path.basename(morte)))
        except OSError as erro:
            falhas_gravacao.append("%s: não consegui arquivar %s (%s)" % (nome, os.path.basename(morte), erro))
    # mortes já avisadas nas últimas 24 h continuam no status (sem nova notificação)
    for morte in sorted(glob.glob(os.path.join(pasta_mortes, "morte-*.json"))):
        try:
            if AGORA - os.path.getmtime(morte) > 86400:
                continue
        except OSError:
            continue
        dados = ler_json(morte) or {}
        if any(a.get("tipo") == "morte" and a.get("quando") == dados.get("morreu_em") and a.get("agente") == dados.get("agente") for a in alertas):
            continue
        alertas.append({"tipo": "morte", "agente": dados.get("agente"), "quando": dados.get("morreu_em"),
                        "motivo": dados.get("motivo"), "ja_notificado": True})

    # 2. Pulsos e ACKs
    fazendo = tarefas_fazendo_por_agente(ler_texto(os.path.join(delta, "kanban.md")))
    total_fazendo = sum(fazendo.values())        # soma de TODOS os agentes (C-064)
    pulsos = {}
    for pulso in glob.glob(os.path.join(ativacoes, "pulso-*.json")):
        dados = ler_json(pulso)
        agente = str((dados or {}).get("agente") or os.path.basename(pulso)[6:-5]).upper()
        pulsos[agente] = epoch_do_pulso(pulso, dados)
    for agente, epoch in sorted(pulsos.items()):
        if epoch is None:
            continue
        silencio = AGORA - epoch
        ativo = os.path.exists(os.path.join(ativacoes, "ack-%s.txt" % agente)) or fazendo.get(agente, 0) > 0
        if silencio > LIMITE_SILENCIO and ativo:
            minutos = int(silencio // 60)
            alertas.append({"tipo": "travado", "agente": agente, "silencio_min": minutos})
            chave = "%s|%s|%d" % (projeto, agente, int(epoch))
            estado_novo[chave] = True
            if chave not in estado_antigo:
                travados_msg.append("%s sem pulso há %dmin em %s" % (agente, minutos, nome))

    # 3. Tarefas órfãs
    for agente, n in fazendo.items():
        if n == 0:
            continue
        tem_ack = os.path.exists(os.path.join(ativacoes, "ack-%s.txt" % agente))
        pulso_recente = pulsos.get(agente) is not None and AGORA - pulsos[agente] <= LIMITE_SILENCIO
        if not tem_ack and not pulso_recente:
            alertas.append({"tipo": "orfa", "agente": agente, "tarefas": n})

    # 4. Operação autônoma — Dia 7 (C-065)
    mais_recente = 0.0
    candidatos_atividade = glob.glob(os.path.join(ativacoes, "**", "*"), recursive=True)
    candidatos_atividade += [os.path.join(delta, f) for f in ("kanban.md", "kanban-data.js", "activity-log.md")]
    candidatos_atividade += glob.glob(os.path.join(delta, "memoria", "*.md"))
    for arquivo in candidatos_atividade:
        try:
            if os.path.isfile(arquivo):
                mais_recente = max(mais_recente, os.path.getmtime(arquivo))
        except OSError:
            pass
    DIAS_OPERACAO_AUTONOMA = int((AGORA - mais_recente) // 86400) if mais_recente else 0
    fase = fase_atual(delta)
    em_fase_7 = bool(re.search(r"(fase|f)\s*7\b|dia\s*7", fase, re.IGNORECASE))
    # Qualquer alerta pendente (órfã, morte, travado) impede a operação autônoma
    alertas_pendentes = sorted(set(a.get("tipo") for a in alertas))
    if not mais_recente:
        OPERACAO_AUTONOMA, motivo_autonomia = False, "sem nenhum registro de atividade"
    elif DIAS_OPERACAO_AUTONOMA < THRESHOLD_DIAS:
        OPERACAO_AUTONOMA, motivo_autonomia = False, "atividade há menos de %d dias" % THRESHOLD_DIAS
    elif total_fazendo > 0:
        OPERACAO_AUTONOMA, motivo_autonomia = False, "parado com tarefa em FAZENDO: é abandono, não operação autônoma"
    elif alertas_pendentes:
        OPERACAO_AUTONOMA, motivo_autonomia = False, "parado com alerta pendente (%s): é abandono, não operação autônoma" % ", ".join(alertas_pendentes)
    elif not em_fase_7:
        OPERACAO_AUTONOMA, motivo_autonomia = False, "parado fora da Fase 7: é abandono, não operação autônoma"
    else:
        OPERACAO_AUTONOMA, motivo_autonomia = True, "Fase 7 sem atividade há %d dias, sem tarefas abertas" % DIAS_OPERACAO_AUTONOMA

    status = {
        "versao": "6.3",
        "verificado_em": iso(AGORA),
        "epoch": int(AGORA),
        "projeto": nome,
        "fase_atual": fase,
        "tarefas_fazendo": total_fazendo,
        "alertas": alertas,
        "operacao_autonoma": OPERACAO_AUTONOMA,
        "dias_silencio": DIAS_OPERACAO_AUTONOMA,
        "motivo_operacao_autonoma": motivo_autonomia,
        "sinal": "OPERACAO_AUTONOMA_DETECTADA" if OPERACAO_AUTONOMA else None,
    }
    texto = json.dumps(status, ensure_ascii=False, indent=2)
    try:
        gravar_atomico(os.path.join(delta, "monitor-status.json"), texto + "\n")
        gravar_atomico(os.path.join(delta, "monitor-data.js"),
                       "// Gerado pelo monitor-delta11.sh — não edite.\nwindow.D11_MONITOR = %s;\n" % texto)
    except OSError as erro:
        falhas_gravacao.append("%s: não consegui gravar o status (%s)" % (nome, erro))

# Guardar estado das notificações (só das situações ainda abertas)
try:
    os.makedirs(os.path.dirname(ESTADO_NOTIFICACOES), exist_ok=True)
    gravar_atomico(ESTADO_NOTIFICACOES, json.dumps(estado_novo))
except OSError:
    pass


# ─── Notificações (sem roubar foco, sem montar texto de comando) ───
def notificar(titulo, mensagem, som):
    if SEM_NOTIFICACAO:
        return
    try:
        if sys.platform == "darwin" and shutil.which("osascript"):
            subprocess.run(["osascript", "-e", "on run argv", "-e",
                            "display notification (item 1 of argv) with title (item 2 of argv) sound name (item 3 of argv)",
                            "-e", "end run", mensagem, titulo, som],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", titulo, mensagem],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception:
        pass


if mortes_msg:
    notificar("Δ-11: Agente Morreu", "\n".join(mortes_msg[:3]), "Sosumi")
if travados_msg:
    notificar("Δ-11: Agente Travado", "\n".join(travados_msg[:3]), "Purr")
if falhas_gravacao:
    notificar("Δ-11: Monitor sem permissão", falhas_gravacao[0], "Basso")

# ─── Log ───────────────────────────────────────────────────────
print("[%s] Verificados %d projetos" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(projetos)))
for m in mortes_msg:
    print("  MORTE: " + m)
for m in travados_msg:
    print("  TRAVADO: " + m)
for m in falhas_gravacao:
    print("  ERRO: " + m)
    print("  ERRO: " + m, file=sys.stderr)
if falhas_gravacao:
    print("  Dica (macOS): Ajustes do Sistema > Privacidade e Segurança > Acesso Total ao Disco > ative o /bin/bash.")
elif not mortes_msg and not travados_msg:
    print("  OK - Sem alertas novos")
sys.exit(1 if falhas_gravacao else 0)
PYTHON_MONITOR
