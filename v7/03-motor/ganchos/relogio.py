#!/usr/bin/env python3
"""Relógio do motor (gancho depois de cada ferramenta): dá a hora a quem não tem terminal (ATLAS, ARQUITETO, CRONOS,
Documentador), para medir as esperas das regras e anotar o tempo no quadro. Ao ATLAS, diz também o que o motor sabe
de cada CRONOS desta conversa: com sinal (a conversa dele, ou a dos agentes que ele chamou, mudou há menos de
`silencio_max`) ou sem sinal, e travado (a linha de um agente dele parada há mais de `travado_max`); é por isso, e não
pelo quadro, que o vigia decide se um CRONOS caiu. Ao CRONOS e ao ATLAS, diz o trabalho do time em cada quadro aberto
(o tempo dos CRONOS trabalhando, sem a espera pelo dono e pelo tempo), para o freio do tempo; ao ARQUITETO, o de todos
os quadros, também os selados, para o limite que sobra a cada bloco. Todo tempo é o do Mac acordado: depois de um sono, diz ao
ATLAS quanto o Mac dormiu, para ele conferir o vigia na hora; e diz a ele o quadro com linhas "trabalhando" sem CRONOS vivo
(o trabalho parado no meio). Ao Documentador, que não tem terminal, diz quantas palavras e tokens tem o arquivo que ele
acabou de escrever, para `estado_max` e `luz_compacta_max`."""
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

try:
    import motor
    pedido = motor.ler(aceita_vazio=True)  # pelo tradutor do programa dito no comando; sem ele, o relógio cala
    agentes = json.loads((AQUI / "lugares.json").read_text(encoding="utf-8"))["agentes"]
    papel = pedido["papel"]
    import registro_de_cronos as reg
    reg.anotar_sono()
    if agentes.get(papel, {}).get("terminal") == "—":
        texto = "Hora agora (motor do Delta-11): " + time.strftime("%Y-%m-%d %H:%M %z")
        raiz = (motor.raiz(obrigatoria=False) or Path(".")).resolve()
        if papel == "documentador" and pedido["ferramenta"] in ("Write", "Edit"):
            for escrito in (Path(a) for a in pedido["arquivos"]):  # todo arquivo que ele escreveu (no Claude Code, um só)
                if escrito.is_file():
                    conteudo = escrito.read_text(encoding="utf-8", errors="replace")
                    texto += f". {escrito.name}: {len(conteudo.split())} palavras, cerca de {round(len(conteudo) / 4)} tokens (caracteres ÷ 4)"
        if papel == "cronos":
            import registro_de_cronos as reg
            meu = next((r for r in reg.registros() if r.get("agente") and r.get("agente") == pedido["agente_id"]), None)
            if meu and meu.get("quadro"):
                texto += ". " + reg.frase_do_trabalho([meu["quadro"]])
                pasta = raiz / ".delta-11" / "quadro" / meu["quadro"]
                quadro_md = (pasta / "quadro.md").read_text(encoding="utf-8", errors="replace") if (pasta / "quadro.md").is_file() else ""
                import re
                situ = re.search(r"situa[cç][aã]o\W*:\W*([^\n|]+)", quadro_md, re.IGNORECASE)
                rodando = [l.name for l in (pasta / "linhas").glob("*.md") if reg.papel_da_linha(l) != "cronos" and reg.trabalhando_na_linha(l)
                           and reg.acordado_desde(l.stat().st_mtime) < int(reg.mapa()["silencio_max_minutos"]) * 60]
                if situ and situ.group(1).strip().strip("*_ ").lower().startswith("esperando o dono") and rodando:
                    texto += (f". O quadro diz esperando o dono com agentes trabalhando ({', '.join(rodando)}): esperando o dono só quando nenhum "
                              "trabalha; até lá, a situação é aberto")
        if papel == "arquiteto":
            import registro_de_cronos as reg
            todos = reg.quadros_com_trabalho()
            if todos:
                texto += ". " + reg.frase_do_trabalho(todos)
        if papel == "atlas":
            import registro_de_cronos as reg
            sessao = pedido["sessao"]

            def estado(r: dict) -> str:
                if not reg.ativo(r):
                    return "trabalhando, SEM SINAL há silencio_max: caiu"
                parados = reg.travados(r, raiz)
                if parados and reg.quadro_se_mexe(r, raiz):
                    return (f"trabalhando, com agente parado ({', '.join(parados)}) e outros vivos: mande ao CRONOS, por mensagem, que troque só esse "
                            "agente; não pare o CRONOS (pará-lo para os agentes vivos dele)")
                return f"trabalhando, TRAVADO (linha parada há mais de travado_max: {', '.join(parados)}): caiu" if parados else "trabalhando, com sinal"
            estados = [f"{r.get('quadro')} (agentId {r.get('agente')}): " + estado(r)
                       for r in reg.registros() if r.get("sessao") == sessao and r.get("agente") and r.get("trabalhando") and reg.roda(r.get("pid", 0))]
            if estados:
                texto += ". CRONOS desta conversa, pelo motor: " + "; ".join(estados) + "."
            abertos = [q for q in reg.quadros_com_trabalho() if reg.quadro_aberto(raiz, q)]
            if abertos:
                texto += ". " + reg.frase_do_trabalho(abertos)
            no_meio = reg.parados_no_meio(raiz)
            if no_meio:
                texto += (". Trabalho parado no meio (ligue um CRONOS do quadro, que segue por ele, mesmo que o quadro diga que espera o dono): "
                          + "; ".join(no_meio) + ".")
            acordou, dormiu = reg.ultimo_sono()
            avisado = reg.SONO.parent / "avisado"
            ja = avisado.read_text(encoding="utf-8").strip() if avisado.is_file() else ""
            if dormiu >= 300 and time.time() - acordou < 3600 and ja != str(acordou):
                avisado.write_text(str(acordou), encoding="utf-8")
                texto += (f". O Mac dormiu {int(dormiu // 60)} min, até {time.strftime('%H:%M', time.localtime(acordou))}: o sono não conta como "
                          "silêncio, linha parada nem trabalho do time; confira agora o vigia (CronList) e, se ele não aparece, agende-o de novo.")
        motor.avisar(texto)  # no Claude Code, o additionalContext do gancho depois da ferramenta
except Exception:
    pass
sys.exit(0)
