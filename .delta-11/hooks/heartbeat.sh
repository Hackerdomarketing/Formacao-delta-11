#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DELTA-11 v6.3 — Hook PostToolUse: Heartbeat (sinal de vida)
#                 + motor único dos sinais de agente
# ═══════════════════════════════════════════════════════════════
# Registro (templates/settings-hooks.json):
#   PostToolUse  matcher "*"  →  bash "$CLAUDE_PROJECT_DIR/.delta-11/hooks/heartbeat.sh"
#
# O que faz a cada ação do agente (PostToolUse):
#   1. Descobre a PASTA PRINCIPAL do projeto (D25): `git rev-parse
#      --git-common-dir` → diretório pai; senão $CLAUDE_PROJECT_DIR;
#      senão o cwd. Só age se essa pasta tiver `.delta-11/`.
#      Por isso o sinal de quem trabalha numa worktree vai para a
#      pasta principal, onde o painel e o monitor olham (N-002).
#   2. Identifica o agente (D28), nesta ordem:
#        a) a própria ação é a escrita do ACK (`ativacoes/ack-NOME.txt`)
#           → grava o vínculo agent_id/session_id → NOME em
#             `ativacoes/agentes-sessao.json`;
#        b) `agent_type` do evento é um nome Delta-11 (BACK, FRONT...);
#        c) vínculo já gravado para o `agent_id` (sub-agente) ou para o
#           `session_id` (sessão principal);
#        d) senão, o ACK MAIS RECENTE (por data de modificação).
#   3. Grava `ativacoes/pulso-NOME.json` (JSON montado com json.dumps,
#      sem perder campos já existentes — C-031/C-033).
#   4. Regenera `.delta-11/pulsos-data.js` (lido pelo painel em file://):
#        window.D11_PULSOS = {"atualizado_em":"ISO","agentes":{"NOME":
#          {"ultimo_sinal":"ISO","ferramenta":"...","worktree":"caminho-ou-null"}}};
#
# Este arquivo também é o MOTOR usado pelos outros vigias de sinal,
# que só repassam o evento para cá (um fato, um lugar):
#   on-stop.sh       Stop → só renova o pulso (status "aguardando").
#                    SessionEnd → registro de "morte", apaga ACK/pulso
#                    dos agentes DESTA sessão (C-007).
#   pre-compact.sh   PreCompact → pulso com status "contexto_critico".
#                    SessionStart(compact) → devolve additionalContext
#                    (o único canal que chega ao modelo — C-033).
#   fim-subagente.sh SubagentStop → log em logs/sub-agentes/ (D32) e
#                    limpeza de ACK/pulso do sub-agente que terminou.
#
# Nunca bloqueia: sai sempre com 0 (em Stop/SubagentStop o código 2
# impediria o agente de parar). Erro interno vira linha
# "ERRO INTERNO" no activity-log (C-016), não silêncio.
# ═══════════════════════════════════════════════════════════════

PAPEL="${1:-heartbeat}"

command -v python3 >/dev/null 2>&1 || exit 0

IFS= read -r -d '' MOTOR_PULSO <<'PYEOF' || true
import datetime
import json
import os
import re
import subprocess
import sys
import time

PAPEL = sys.argv[1] if len(sys.argv) > 1 else "heartbeat"
NOMES_DELTA11 = {"ATLAS", "CRONOS", "FRONT", "PIXEL", "FORM", "BACK",
                 "ENGINE", "VAULT", "SHIELD", "SCOUT"}
ACK_ESCRITA_RE = re.compile(
    r"""(?:>>?|\btee\b(?:\s+-a)?)\s*["']?[^\s"'<>|;&]*ativacoes/ack-([A-Za-z0-9_-]+)\.txt""")
ACK_REMOCAO_RE = re.compile(
    r"""\brm\b[^\n;&|]*ativacoes/ack-([A-Za-z0-9_-]+)\.txt""")
ACK_ARQUIVO_RE = re.compile(r"ativacoes[\\/]ack-([A-Za-z0-9_-]+)\.txt$")
OPERATIVO_RE = re.compile(r"operativos/([A-Z]+)\.md")
SUBAGENTE_RE = re.compile(r"sub-agentes/([a-z0-9-]+)\.md")
DIAS_GUARDAR_VINCULO = 7


def agora_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def agora_compacto():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_para_epoch(texto):
    try:
        return datetime.datetime.strptime(texto, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except (TypeError, ValueError):
        return 0


def git_info(pasta):
    """Devolve (git_dir, git_common_dir, toplevel) absolutos ou (None, None, None)."""
    try:
        r = subprocess.run(
            ["git", "-C", pasta, "rev-parse", "--path-format=absolute",
             "--git-dir", "--git-common-dir", "--show-toplevel"],
            capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None, None, None
    linhas = r.stdout.strip().splitlines()
    if r.returncode != 0 or len(linhas) < 3:
        return None, None, None
    return [os.path.normpath(x) for x in linhas[:3]]


def raiz_principal(cwd):
    """D25: pasta pai do --git-common-dir; senão CLAUDE_PROJECT_DIR; senão cwd."""
    candidatos = []
    _, comum, _ = git_info(cwd)
    if comum:
        candidatos.append(os.path.dirname(comum))
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidatos.append(os.environ["CLAUDE_PROJECT_DIR"])
    candidatos.append(cwd)
    for c in candidatos:
        if c and os.path.isdir(os.path.join(c, ".delta-11")):
            return os.path.realpath(c)
    return None


def worktree_do_evento(cwd):
    """Caminho da worktree quando o cwd está numa cópia isolada; senão None."""
    git_dir, comum, topo = git_info(cwd)
    if git_dir and comum and git_dir != comum:
        return topo
    return None


def ler_json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def gravar_atomico(caminho, texto):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = "%s.tmp-%d" % (caminho, os.getpid())
    with open(temporario, "w", encoding="utf-8") as f:
        f.write(texto)
    os.replace(temporario, caminho)


def gravar_json(caminho, dados):
    gravar_atomico(caminho, json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n")


def logar_atividade(raiz, agente, mensagem):
    """Formato único D25: - [AAAA-MM-DDTHH:MM:SSZ] [nome-do-hook] [AGENTE] mensagem"""
    try:
        caminho = os.path.join(raiz, ".delta-11", "activity-log.md")
        linha = "- [%s] [%s] [%s] %s\n" % (agora_iso(), PAPEL, agente or "SISTEMA",
                                           " ".join(str(mensagem).split()))
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(linha)
    except OSError:
        pass


class Mutex:
    """Trava curta por mkdir (atômico) para o arquivo de vínculos."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.ok = False

    def __enter__(self):
        os.makedirs(os.path.dirname(self.caminho), exist_ok=True)
        limite = time.time() + 2
        while time.time() < limite:
            try:
                os.mkdir(self.caminho)
                self.ok = True
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.caminho) > 10:
                        os.rmdir(self.caminho)  # trava esquecida por processo morto
                        continue
                except OSError:
                    pass
                time.sleep(0.05)
        return self

    def __exit__(self, *erro):
        if self.ok:
            try:
                os.rmdir(self.caminho)
            except OSError:
                pass


def caminho_vinculos(raiz):
    return os.path.join(raiz, ".delta-11", "ativacoes", "agentes-sessao.json")


def ler_vinculos(raiz):
    dados = ler_json(caminho_vinculos(raiz), {})
    if not isinstance(dados, dict) or not isinstance(dados.get("chaves"), dict):
        dados = {"versao": 1, "chaves": {}}
    return dados


def alterar_vinculos(raiz, funcao):
    """Lê, altera e grava o arquivo de vínculos sob mutex. Limpa vínculos velhos."""
    with Mutex(os.path.join(raiz, ".delta-11", "locks", "agentes-sessao.mutex")):
        dados = ler_vinculos(raiz)
        funcao(dados["chaves"])
        limite = time.time() - DIAS_GUARDAR_VINCULO * 86400
        dados["chaves"] = {k: v for k, v in dados["chaves"].items()
                           if iso_para_epoch(v.get("visto_em")) >= limite}
        dados["versao"] = 1
        dados["atualizado_em"] = agora_iso()
        gravar_json(caminho_vinculos(raiz), dados)


def chave_do_evento(ev):
    if ev.get("agent_id"):
        return "agente:%s" % ev["agent_id"]
    return "principal:%s" % (ev.get("session_id") or "desconhecida")


def ack_escrito_no_evento(ev):
    entrada = ev.get("tool_input") or {}
    ferramenta = ev.get("tool_name") or ""
    if ferramenta == "Bash":
        m = ACK_ESCRITA_RE.search(entrada.get("command") or "")
        return m.group(1) if m else None
    if ferramenta in ("Write", "Edit"):
        m = ACK_ARQUIVO_RE.search(entrada.get("file_path") or "")
        return m.group(1) if m else None
    return None


def ack_removido_no_evento(ev):
    if (ev.get("tool_name") or "") != "Bash":
        return None
    m = ACK_REMOCAO_RE.search((ev.get("tool_input") or {}).get("command") or "")
    return m.group(1) if m else None


def ack_mais_recente(raiz, ignorar=()):
    pasta = os.path.join(raiz, ".delta-11", "ativacoes")
    melhor, melhor_data = None, -1.0
    try:
        nomes = os.listdir(pasta)
    except OSError:
        return None
    for nome in nomes:
        m = re.match(r"^ack-([A-Za-z0-9_-]+)\.txt$", nome)
        if not m or m.group(1) in ignorar:
            continue
        try:
            data = os.path.getmtime(os.path.join(pasta, nome))
        except OSError:
            continue
        if data > melhor_data:
            melhor, melhor_data = m.group(1), data
    return melhor


def identificar(ev, raiz, aceitar_ack_recente=True):
    """D28. Devolve (NOME ou None, fonte)."""
    nome = ack_escrito_no_evento(ev)
    if nome:
        return nome, "ack-escrito"
    tipo = (ev.get("agent_type") or "").strip().upper()
    if tipo in NOMES_DELTA11:
        return tipo, "agent_type"
    chaves = ler_vinculos(raiz)["chaves"]
    chave = chave_do_evento(ev)
    vinculo = chaves.get(chave)
    if vinculo and vinculo.get("agente"):
        return vinculo["agente"], "vinculo"
    if aceitar_ack_recente:
        # ACK de agente já vinculado a OUTRA sessão/sub-agente ativo não é
        # deste evento (evita a sessão principal renovar o pulso do BACK).
        de_outros = {v.get("agente") for k, v in chaves.items()
                     if k != chave and v.get("agente") and not v.get("encerrado_em")}
        nome = ack_mais_recente(raiz, de_outros)
        if nome:
            return nome, "ack-recente"
    return None, None


def caminho_pulso(raiz, nome):
    return os.path.join(raiz, ".delta-11", "ativacoes", "pulso-%s.json" % nome)


def renovar_pulso(raiz, nome, ev, status, ferramenta=None):
    caminho = caminho_pulso(raiz, nome)
    pulso = ler_json(caminho, {})
    if not isinstance(pulso, dict):
        pulso = {}
    agora = agora_iso()
    pulso.update({
        "agente": nome,
        "status": status,
        "ultimo_sinal": agora,
        "ultimo_update": agora,          # nome antigo, lido pelo monitor
        "epoch": int(time.time()),
        "projeto": os.path.basename(raiz),
    })
    if ferramenta:
        pulso["ultima_tool"] = ferramenta
    for campo in ("session_id", "agent_id", "agent_type"):
        if ev.get(campo):
            pulso[campo] = ev[campo]
    cwd = ev.get("cwd") or os.getcwd()
    if ev.get("hook_event_name") in ("PostToolUse", "PreToolUse"):
        pulso["worktree"] = worktree_do_evento(cwd)
    pulso.setdefault("worktree", None)
    gravar_json(caminho, pulso)


def regenerar_pulsos_data(raiz):
    pasta = os.path.join(raiz, ".delta-11", "ativacoes")
    agentes = {}
    try:
        nomes = sorted(os.listdir(pasta))
    except OSError:
        nomes = []
    for arquivo in nomes:
        m = re.match(r"^pulso-([A-Za-z0-9_-]+)\.json$", arquivo)
        if not m:
            continue
        pulso = ler_json(os.path.join(pasta, arquivo), None)
        if not isinstance(pulso, dict):
            continue
        # Chave em MAIÚSCULAS e datas ISO com fuso (Z = UTC): formato lido pelo painel.
        agentes[str(pulso.get("agente") or m.group(1)).upper()] = {
            "ultimo_sinal": pulso.get("ultimo_sinal") or pulso.get("ultimo_update"),
            "ferramenta": pulso.get("ultima_tool"),
            "worktree": pulso.get("worktree"),
            "status": pulso.get("status"),
        }
    dados = {"atualizado_em": agora_iso(), "agentes": agentes}
    texto = ("// Gerado automaticamente pelo hook heartbeat.sh (Delta-11 v6.3). Não editar.\n"
             "window.D11_PULSOS = %s;\n" % json.dumps(dados, ensure_ascii=False))
    gravar_atomico(os.path.join(raiz, ".delta-11", "pulsos-data.js"), texto)


def apagar(caminho):
    try:
        os.remove(caminho)
    except OSError:
        pass


def encerrar_agente(raiz, nome, motivo, registrar_morte, ev):
    pasta = os.path.join(raiz, ".delta-11", "ativacoes")
    if registrar_morte:
        pulso = ler_json(caminho_pulso(raiz, nome), {})
        gravar_json(os.path.join(pasta, "morte-%s.json" % nome), {
            "agente": nome,
            "morreu_em": agora_iso(),
            "motivo": motivo,
            "ultima_tool": (pulso or {}).get("ultima_tool", ""),
            "session_id": ev.get("session_id", ""),
            "projeto": os.path.basename(raiz),
        })
    apagar(os.path.join(pasta, "ack-%s.txt" % nome))
    apagar(caminho_pulso(raiz, nome))


# ─── Tratamento por evento ─────────────────────────────────────

def ao_usar_ferramenta(ev, raiz):
    removido = ack_removido_no_evento(ev)
    if removido:
        apagar(caminho_pulso(raiz, removido))

        def marcar(chaves):
            vinculo = chaves.get(chave_do_evento(ev))
            if vinculo and vinculo.get("agente") == removido:
                vinculo["encerrado_em"] = agora_iso()
                vinculo["encerrado_por"] = "ack-removido"
        alterar_vinculos(raiz, marcar)
        regenerar_pulsos_data(raiz)
        return
    nome, fonte = identificar(ev, raiz)
    if not nome:
        return
    if fonte == "ack-escrito":
        cwd = ev.get("cwd") or os.getcwd()

        def vincular(chaves):
            chaves[chave_do_evento(ev)] = {
                "agente": nome,
                "session_id": ev.get("session_id"),
                "agent_id": ev.get("agent_id"),
                "agent_type": ev.get("agent_type"),
                "worktree": worktree_do_evento(cwd),
                "visto_em": agora_iso(),
                "fonte": fonte,
                "encerrado_em": None,
                "encerrado_por": None,
            }
        alterar_vinculos(raiz, vincular)
    renovar_pulso(raiz, nome, ev, "ativo", ev.get("tool_name"))
    regenerar_pulsos_data(raiz)


def ao_fim_de_resposta(ev, raiz):
    """Stop dispara no fim de CADA resposta: só renova o pulso (C-007)."""
    nome, _ = identificar(ev, raiz)
    if nome:
        renovar_pulso(raiz, nome, ev, "aguardando")
        regenerar_pulsos_data(raiz)


def ao_compactar(ev, raiz):
    nome, _ = identificar(ev, raiz)
    if nome:
        renovar_pulso(raiz, nome, ev, "contexto_critico")
        regenerar_pulsos_data(raiz)


def apos_compactar(ev, raiz):
    """SessionStart(source=compact): additionalContext chega ao modelo (C-033)."""
    if ev.get("source") != "compact":
        return
    nome, _ = identificar(ev, raiz)
    quem = nome or "[SEU-NOME]"
    texto = (
        "[ALERTA DELTA-11] Sua conversa acabou de ser compactada e detalhes podem ter se perdido. "
        "Antes de continuar: (1) releia .delta-11/memoria/%s-produto.md e .delta-11/planos/%s-plan.md; "
        "(2) atualize %s-produto.md (o que existe agora) e %s-historia.md (o que você fez) com o "
        "estado atual; (3) se é executor, avise o CRONOS por SendMessage caso tenha perdido o fio "
        "da tarefa. Não peça nada ao comandante por causa disso." % (quem, quem, quem, quem))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": texto}}, ensure_ascii=False))
    if nome:
        renovar_pulso(raiz, nome, ev, "ativo")
        regenerar_pulsos_data(raiz)


def ao_fim_de_sessao(ev, raiz):
    """SessionEnd: a sessão inteira acabou. Encerra só os agentes DESTA sessão."""
    sessao = ev.get("session_id")
    motivo = "sessao_encerrada:%s" % (ev.get("reason") or "other")
    encerrados = []

    def marcar(chaves):
        for chave, vinculo in chaves.items():
            if sessao and vinculo.get("session_id") == sessao and not vinculo.get("encerrado_em"):
                vinculo["encerrado_em"] = agora_iso()
                vinculo["encerrado_por"] = "SessionEnd:%s" % sessao
                if vinculo.get("agente") and vinculo["agente"] not in encerrados:
                    encerrados.append(vinculo["agente"])
    alterar_vinculos(raiz, marcar)
    for nome in encerrados:
        encerrar_agente(raiz, nome, motivo, True, ev)
    regenerar_pulsos_data(raiz)
    if encerrados:
        logar_atividade(raiz, ",".join(encerrados),
                        "sessão encerrada (%s): ACK e pulso apagados, registro de morte gravado"
                        % (ev.get("reason") or "other"))
    else:
        logar_atividade(raiz, None, "sessão encerrada (%s) sem agente Delta-11 vinculado"
                        % (ev.get("reason") or "other"))


def ler_inicio_transcricao(caminho, limite_bytes=200000):
    """As 5 primeiras linhas da transcrição (o prompt de ativação do sub-agente)."""
    if not caminho:
        return ""
    try:
        with open(os.path.expanduser(caminho), encoding="utf-8", errors="replace") as f:
            return "\n".join(f.read(limite_bytes).splitlines()[:5])
    except OSError:
        return ""


def ao_fim_de_subagente(ev, raiz):
    """SubagentStop: log D32 + limpeza do sub-agente que terminou."""
    agente_id = ev.get("agent_id") or "sem-id"
    tipo = ev.get("agent_type") or "desconhecido"
    tipo_arquivo = re.sub(r"[^A-Za-z0-9_.-]+", "-", tipo).strip("-") or "desconhecido"
    inicio = ler_inicio_transcricao(ev.get("agent_transcript_path"))
    operativo = OPERATIVO_RE.search(inicio)
    subagente = SUBAGENTE_RE.search(inicio)

    nome, fonte = identificar(ev, raiz, aceitar_ack_recente=False)
    if not nome and operativo and operativo.group(1) in NOMES_DELTA11:
        nome, fonte = operativo.group(1), "transcricao"

    pasta_logs = os.path.join(raiz, ".delta-11", "logs", "sub-agentes")
    os.makedirs(pasta_logs, exist_ok=True)
    caminho_log = os.path.join(pasta_logs, "%s-%s.log" % (agora_compacto(), tipo_arquivo))
    with open(caminho_log, "a", encoding="utf-8") as f:
        f.write("evento: SubagentStop\n")
        f.write("quando: %s\n" % agora_iso())
        f.write("agent_type: %s\n" % tipo)
        f.write("agent_id: %s\n" % agente_id)
        f.write("agente_delta11: %s\n" % (nome or "-"))
        f.write("subagente_detectado: %s\n" % (subagente.group(1) if subagente else "-"))
        f.write("session_id: %s\n" % (ev.get("session_id") or "-"))
        f.write("transcricao: %s\n" % (ev.get("agent_transcript_path") or "-"))
        f.write("--- ultima mensagem ---\n%s\n\n" % (ev.get("last_assistant_message") or ""))

    def marcar(chaves):
        chave = chave_do_evento(ev)
        vinculo = chaves.setdefault(chave, {
            "agente": nome, "session_id": ev.get("session_id"), "agent_id": ev.get("agent_id"),
            "agent_type": ev.get("agent_type"), "worktree": None, "fonte": fonte})
        vinculo["visto_em"] = agora_iso()
        vinculo["encerrado_em"] = agora_iso()
        vinculo["encerrado_por"] = "SubagentStop"
    alterar_vinculos(raiz, marcar)
    if nome:
        encerrar_agente(raiz, nome, "subagente_terminou", False, ev)
    regenerar_pulsos_data(raiz)
    logar_atividade(raiz, nome or tipo,
                    "sub-agente terminou (agent_type=%s, agent_id=%s); log: %s"
                    % (tipo, agente_id, os.path.relpath(caminho_log, raiz)))


def main():
    try:
        ev = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(ev, dict):
        return 0
    cwd = ev.get("cwd") or os.getcwd()
    raiz = raiz_principal(cwd)
    if not raiz:
        return 0
    try:
        evento = ev.get("hook_event_name") or "PostToolUse"
        if evento in ("PostToolUse", "PostToolUseFailure"):
            ao_usar_ferramenta(ev, raiz)
        elif evento == "Stop":
            ao_fim_de_resposta(ev, raiz)
        elif evento == "PreCompact":
            ao_compactar(ev, raiz)
        elif evento == "SessionStart":
            apos_compactar(ev, raiz)
        elif evento == "SessionEnd":
            ao_fim_de_sessao(ev, raiz)
        elif evento == "SubagentStop":
            ao_fim_de_subagente(ev, raiz)
    except Exception as erro:  # nunca derrubar a sessão; deixar rastro visível
        logar_atividade(raiz, None, "ERRO INTERNO (%s): %s" % (type(erro).__name__, erro))
    return 0


sys.exit(main())
PYEOF

python3 -c "$MOTOR_PULSO" "$PAPEL"
exit 0
