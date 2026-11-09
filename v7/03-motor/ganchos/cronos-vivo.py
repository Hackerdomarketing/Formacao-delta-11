#!/usr/bin/env python3
"""Gancho de início e fim do CRONOS e do ARQUITETO (no Claude Code, SubagentStart e SubagentStop): marca no registro quando o
CRONOS trabalha e soma a vez dele (com o Mac acordado) no trabalho do time do quadro; do ARQUITETO, só que ele trabalha (um por
vez). Lê o evento pelo tradutor (motor.py) do programa dito no comando."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registro_de_cronos as reg  # noqa: E402
import motor  # noqa: E402


def main() -> None:
    pedido = motor.ler(aceita_vazio=True)
    agente, sessao = pedido["agente_id"], pedido["sessao"]
    inicio = pedido["evento"] == "inicio-de-agente"
    reg.anotar_sono()
    if pedido["papel"] == "arquiteto":
        reg.arquiteto(agente, sessao, inicio, pedido["conversa_do_agente"])
        return
    conhecido = next((r for r in reg.registros() if r.get("agente") == agente), None)
    if conhecido is None and inicio:
        pendentes = sorted(reg.pedidos_recentes(sessao), key=lambda r: r["_arquivo"])  # pedido velho que não começou não conta
        if pendentes:
            conhecido = pendentes[0]
            os.remove(conhecido["_arquivo"])
            conhecido["_arquivo"] = ""
    if conhecido is None:
        return
    if conhecido.get("_arquivo"):
        os.remove(conhecido["_arquivo"])
    conversa = pedido["conversa_do_agente"]
    agora = time.time()
    if not inicio and conhecido.get("trabalhando") and conhecido.get("inicio_da_vez"):
        reg.somar_trabalho(conhecido.get("quadro", ""), reg.acordado_desde(conhecido["inicio_da_vez"]))
    conhecido.update({"agente": agente, "trabalhando": inicio, "mudou": agora, "pid": reg.processo_da_conversa() or conhecido.get("pid", 0),
                      "conversa_do_agente": conversa, "inicio_da_vez": agora if inicio else 0})
    reg.gravar(f"{agente}.json", conhecido)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
