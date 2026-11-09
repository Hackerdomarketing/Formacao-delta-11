#!/usr/bin/env python3
"""Pulso dos perfis de IA (agentes/perfis-de-ia.json, ferramentas/perfil_de_ia.py, instalar.py --ia e trocar-ia.py).

Prova, em pastas descartáveis e com um cofre de mentira (nunca o cofre do dono, nunca uma chamada paga a uma IA):
(a) cada perfil tem endereço https, três modelos, a entrada do cofre, a fonte (URL oficial) e a data da leitura, ou `conferido: false` com o motivo;
(b) aplicar um perfil escreve as variáveis certas e o `apiKeyHelper` (só o COMANDO que lê do cofre), e o arquivo não tem nada com cara de chave;
(c) voltar para `claude` deixa a configuração local como estava antes de qualquer perfil;
(d) a atualização mantém a IA da pasta (e `--atualizar --ia claude` volta ao Claude);
(e) a configuração local fica fora do git;
(f) o `gateway` sem endereço e um perfil desconhecido recusam com frase clara, sem mexer em nada;
(g) chave ausente do cofre: o `trocar-ia.py` recusa com a frase combinada;
(h) as proteções do instalador continuam (ele ainda tira o modo fork e mantém as instruções pessoais de fora).
Uso: python3 testar-perfis-de-ia.py   (sai com 1 se algo não sair como deve)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
FERRAMENTAS = MOTOR / "ferramentas"
PERFIS = MOTOR / "agentes" / "perfis-de-ia.json"
INSTALAR = FERRAMENTAS / "instalar.py"
TROCAR = FERRAMENTAS / "trocar-ia.py"
AJUDANTE = FERRAMENTAS / "chave-do-cofre.py"
MODULO = FERRAMENTAS / "perfil_de_ia.py"
VALOR_FALSO = "valor-falso-de-"  # o que o cofre de mentira devolve: nunca pode aparecer em arquivo
# Sem as variáveis GIT_* de um commit em andamento: dentro do gancho, elas apontariam o git do teste para o repositório real.
AMBIENTE = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "DELTA11_SECRETCTL"}
VARIAVEIS_DA_IA = ("ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                   "ANTHROPIC_DEFAULT_HAIKU_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL")
FRASE_DA_CHAVE_AUSENTE = "não achei a chave do DeepSeek no cofre (entrada API_DEEPSEEK); guarde-a no cofre e rode de novo"


def carregar_modulo():
    especificacao = importlib.util.spec_from_file_location("perfil_de_ia_do_pulso", MODULO)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def montar_cofre_de_mentira(pasta: Path, nomes: list[str]) -> Path:
    """Um `secretctl` de mentira: `list` mostra os nomes, `get` devolve um valor falso. O cofre de verdade nunca é tocado."""
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "nomes.txt").write_text("\n".join(nomes) + "\n", encoding="utf-8")
    programa = pasta / "secretctl"
    programa.write_text('#!/bin/sh\npasta="$(dirname "$0")"\ncase "$1" in\n  list) cat "$pasta/nomes.txt" ;;\n'
                        f'  get) if grep -qx "$2" "$pasta/nomes.txt"; then echo "{VALOR_FALSO}$2"; else echo "chave nao encontrada" >&2; exit 1; fi ;;\n'
                        '  *) exit 2 ;;\nesac\n', encoding="utf-8")
    programa.chmod(0o755)
    return programa


def rodar(*argumentos: str, ambiente: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", *argumentos], capture_output=True, text=True, env=ambiente)


def ler(arquivo: Path) -> dict:
    return json.loads(arquivo.read_text(encoding="utf-8"))


def tem_cara_de_chave(texto: str) -> bool:
    """`sk-` seguido de letras e números, ou qualquer sequência de mais de 30 letras e números seguidos fora de endereço e caminho."""
    sem_enderecos = re.sub(r"https?://\S+|[/~][^\s\"]*", " ", texto)
    return bool(re.search(r"sk-[A-Za-z0-9]{16,}", texto) or re.search(r"[A-Za-z0-9]{31,}", sem_enderecos))


def main() -> int:
    falhas: list[str] = []

    def conferir(nome: str, certo: bool) -> None:
        print(f"  {'ok' if certo else 'ERRADO'} — {nome}")
        if not certo:
            falhas.append(nome)

    def tentar(nome: str, prova) -> None:
        """Roda a prova; qualquer erro (arquivo que ainda não existe, frase diferente) é um caso que falhou, não um pulso que quebrou."""
        try:
            conferir(nome, bool(prova()))
        except Exception as erro:  # noqa: BLE001 — o motivo vai na linha do caso
            print(f"  ERRADO — {nome}  [{type(erro).__name__}: {str(erro)[:120]}]")
            falhas.append(nome)

    perfis: dict = {}
    try:
        perfis = json.loads(PERFIS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    desta_vez = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        cofre = montar_cofre_de_mentira(tmp / "cofre-de-mentira", ["API_MINIMAX", "API_KIMI_K", "API_DEEPSEEK", "API_GATEWAY"])
        cofre_sem_deepseek = montar_cofre_de_mentira(tmp / "cofre-sem-deepseek", ["API_MINIMAX", "API_KIMI_K"])
        ambiente = {**AMBIENTE, "DELTA11_SECRETCTL": str(cofre)}
        ambiente_sem_deepseek = {**AMBIENTE, "DELTA11_SECRETCTL": str(cofre_sem_deepseek)}
        os.environ["DELTA11_SECRETCTL"] = str(cofre)  # para as funções do módulo, chamadas aqui dentro

        # (a) Os perfis: cada nome e endereço tem fonte oficial e data, ou diz que não foi conferido.
        def perfis_completos() -> bool:
            esperados = {"claude", "deepseek", "minimax", "kimi", "glm", "gateway"}
            if set(perfis) != esperados:
                return False
            for nome, perfil in perfis.items():
                fonte, lido_em = str(perfil.get("fonte", "")), str(perfil.get("lido_em", ""))
                if perfil.get("conferido") is False:
                    if not str(perfil.get("motivo", "")).strip():
                        return False
                elif not (fonte.startswith("https://") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", lido_em)):
                    return False
                if nome in ("claude", "gateway"):
                    continue  # o claude não troca nada; o gateway pede o endereço e os modelos na linha de comando
                if not (str(perfil.get("endereco", "")).startswith("https://") and str(perfil.get("entrada_do_cofre", "")).strip()
                        and all(str(perfil.get(c, "")).strip() for c in ("modelo_forte", "modelo_medio", "modelo_leve"))):
                    return False
            return bool(str(perfis["gateway"].get("entrada_do_cofre", "")).strip())
        tentar("a) cada perfil (claude, deepseek, minimax, kimi, glm, gateway) tem a fonte oficial e a data (ou diz que não foi conferido), e os de fornecedor têm endereço https, três modelos e a entrada do cofre",
               perfis_completos)

        # (b) Aplicar um perfil: as variáveis certas, o comando do cofre, e nada com cara de chave.
        pasta_b = tmp / "produto-b"
        (pasta_b / ".claude").mkdir(parents=True)
        (pasta_b / ".claude" / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}, "env": {"PATH": "/usr/bin"}}))

        def aplicar_deepseek() -> bool:
            modulo = carregar_modulo()
            resumo = modulo.aplicar_perfil_de_ia(pasta_b, "deepseek")
            local = ler(pasta_b / ".claude" / "settings.local.json")
            texto = (pasta_b / ".claude" / "settings.local.json").read_text(encoding="utf-8")
            ambiente_local, perfil = local.get("env", {}), perfis["deepseek"]
            desta_vez["resumo_b"] = str(resumo)
            return (ambiente_local.get("ANTHROPIC_BASE_URL") == perfil["endereco"] and ambiente_local.get("ANTHROPIC_MODEL") == perfil["modelo_forte"]
                    and ambiente_local.get("ANTHROPIC_DEFAULT_OPUS_MODEL") == perfil["modelo_forte"]
                    and ambiente_local.get("ANTHROPIC_DEFAULT_SONNET_MODEL") == perfil["modelo_medio"]
                    and ambiente_local.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") == perfil["modelo_leve"]
                    and ambiente_local.get("CLAUDE_CODE_SUBAGENT_MODEL") == perfil["modelo_medio"]
                    and ambiente_local.get("PATH") == "/usr/bin" and local.get("permissions") == {"allow": ["Bash(ls)"]}
                    and "chave-do-cofre.py" in str(local.get("apiKeyHelper")) and "API_DEEPSEEK" in str(local.get("apiKeyHelper")))
        tentar("b) aplicar o DeepSeek escreve o endereço, os modelos de cada apelido e o apiKeyHelper, e mantém o que já estava na configuração local", aplicar_deepseek)

        def sem_chave_no_arquivo() -> bool:
            texto = (pasta_b / ".claude" / "settings.local.json").read_text(encoding="utf-8")
            return (not tem_cara_de_chave(texto) and VALOR_FALSO not in texto and "ANTHROPIC_API_KEY" not in texto and "ANTHROPIC_AUTH_TOKEN" not in texto
                    and VALOR_FALSO not in desta_vez.get("resumo_b", VALOR_FALSO))
        tentar("b) o arquivo não tem nada com cara de chave (sk-..., mais de 30 letras e números seguidos, nem o valor do cofre) nem ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN", sem_chave_no_arquivo)

        def ajudante_imprime_so_a_chave() -> bool:
            feito = subprocess.run([sys.executable, "-B", str(AJUDANTE), "API_DEEPSEEK"], capture_output=True, text=True, env=ambiente)
            ausente = subprocess.run([sys.executable, "-B", str(AJUDANTE), "API_NAO_EXISTE"], capture_output=True, text=True, env=ambiente)
            return feito.returncode == 0 and feito.stdout.strip() == VALOR_FALSO + "API_DEEPSEEK" and ausente.returncode != 0 and not ausente.stdout.strip()
        tentar("b) o ajudante do cofre imprime só a chave (e nada na saída quando a chave não existe, com erro)", ajudante_imprime_so_a_chave)

        # (c) Instalação de verdade com o Claude; depois DeepSeek; depois de volta ao Claude: a configuração local volta ao que era.
        esteira_marca = Path(os.environ.get("DELTA11_PULSO_DA_ESTEIRA_FEITO") or "/nenhuma")
        digital = hashlib.sha256((MOTOR / "esteira" / "esteira").read_bytes() + (FERRAMENTAS / "testar-esteira.py").read_bytes()).hexdigest()
        if not (esteira_marca.name == ".pulso-da-esteira-passou" and esteira_marca.is_file() and esteira_marca.read_text(encoding="utf-8").strip() == digital):
            esteira = subprocess.run([sys.executable, "-I", "-B", str(FERRAMENTAS / "testar-esteira.py")], capture_output=True, text=True, env=AMBIENTE)
            conferir("a esteira do motor passa no pulso dela (o instalador só instala com ela passando)", esteira.returncode == 0)
            esteira_marca = tmp / ".pulso-da-esteira-passou"
            if esteira.returncode == 0:
                esteira_marca.write_text(digital)
        ambiente["DELTA11_PULSO_DA_ESTEIRA_FEITO"] = str(esteira_marca)
        ambiente_sem_deepseek["DELTA11_PULSO_DA_ESTEIRA_FEITO"] = str(esteira_marca)

        produto = tmp / "produto"
        feito = rodar(str(INSTALAR), str(produto), ambiente=ambiente)
        conferir("instalar sem --ia instala com o Claude (o padrão) e não escreve variável nem apiKeyHelper de IA", feito.returncode == 0
                 and not any(v in ler(produto / ".claude" / "settings.local.json").get("env", {}) for v in VARIAVEIS_DA_IA)
                 and "apiKeyHelper" not in ler(produto / ".claude" / "settings.local.json")
                 and json.loads((produto / ".delta-11/motor/VERSAO").read_text()).get("ia") == "claude")
        local_do_claude = ler(produto / ".claude" / "settings.local.json") if (produto / ".claude" / "settings.local.json").is_file() else {}
        trocou = rodar(str(TROCAR), str(produto), "deepseek", ambiente=ambiente)
        local_deepseek = ler(produto / ".claude" / "settings.local.json") if (produto / ".claude" / "settings.local.json").is_file() else {}
        saida = trocou.stdout
        tentar("c) trocar-ia.py para o DeepSeek diz a IA, os modelos, a fonte e a data lidas, que a chave vem do cofre na hora, e que é preciso fechar e abrir a conversa",
               lambda: trocou.returncode == 0 and saida.startswith("OK — a IA deste produto agora é DeepSeek") and perfis["deepseek"]["modelo_forte"] in saida
               and perfis["deepseek"]["lido_em"] in saida and "API_DEEPSEEK" in saida and "nada foi gravado em arquivo" in saida
               and "Feche e abra a conversa" in saida and "a qualidade do trabalho é a da IA escolhida" in saida
               and local_deepseek.get("env", {}).get("ANTHROPIC_BASE_URL") == perfis["deepseek"]["endereco"]
               and json.loads((produto / ".delta-11/motor/VERSAO").read_text()).get("ia") == "deepseek")
        trocou_de_volta = rodar(str(TROCAR), str(produto), "claude", ambiente=ambiente)
        local_de_volta = ler(produto / ".claude" / "settings.local.json") if (produto / ".claude" / "settings.local.json").is_file() else {}
        tentar("c) voltar para o claude deixa o settings.local.json igual ao de antes (como JSON) e a VERSAO diz claude",
               lambda: trocou_de_volta.returncode == 0 and local_de_volta == local_do_claude and local_do_claude != {}
               and json.loads((produto / ".delta-11/motor/VERSAO").read_text()).get("ia") == "claude")
        status = subprocess.run(["git", "-C", str(produto), "status", "--short"], capture_output=True, text=True, env=AMBIENTE).stdout
        trocou = rodar(str(TROCAR), str(produto), "deepseek", ambiente=ambiente)
        status_com_ia = subprocess.run(["git", "-C", str(produto), "status", "--short"], capture_output=True, text=True, env=AMBIENTE).stdout
        ignorado = subprocess.run(["git", "-C", str(produto), "check-ignore", "-q", ".claude/settings.local.json"], env=AMBIENTE).returncode == 0
        rastreados = subprocess.run(["git", "-C", str(produto), "ls-files"], capture_output=True, text=True, env=AMBIENTE).stdout.split()
        tentar("e) o .gitignore do produto ignora .claude/settings.local.json; com a IA trocada, o git status não o lista (nem deixa a pasta suja) e ele não está no git",
               lambda: trocou.returncode == 0 and ignorado and ".claude/settings.local.json" not in status_com_ia and ".claude/settings.local.json" not in rastreados
               and not status.strip() and not status_com_ia.strip())

        # (d) A atualização mantém a IA da pasta; com --ia claude, volta; (h) as proteções continuam.
        produto_minimax = tmp / "produto-minimax"
        feito = rodar(str(INSTALAR), "--ia", "minimax", str(produto_minimax), ambiente=ambiente)
        arquivo_local = produto_minimax / ".claude" / "settings.local.json"
        local_minimax = ler(arquivo_local) if arquivo_local.is_file() else {}
        tentar("d) instalar com --ia minimax grava o MiniMax na configuração local e na VERSAO (campo ia), sem chave em arquivo",
               lambda: feito.returncode == 0 and local_minimax.get("env", {}).get("ANTHROPIC_BASE_URL") == perfis["minimax"]["endereco"]
               and "API_MINIMAX" in str(local_minimax.get("apiKeyHelper")) and json.loads((produto_minimax / ".delta-11/motor/VERSAO").read_text()).get("ia") == "minimax"
               and not tem_cara_de_chave(arquivo_local.read_text()) and "ia: minimax" in feito.stdout)
        if arquivo_local.is_file():
            com_fork = ler(arquivo_local)
            com_fork["env"]["CLAUDE_CODE_FORK_SUBAGENT"] = "1"  # algo que o instalador tira de propósito
            arquivo_local.write_text(json.dumps(com_fork))
        atualizou = rodar(str(INSTALAR), "--atualizar", str(produto_minimax), ambiente=ambiente)
        local_depois = ler(arquivo_local) if arquivo_local.is_file() else {}
        tentar("d) --atualizar sem --ia mantém o MiniMax (variáveis, apiKeyHelper e a VERSAO)",
               lambda: atualizou.returncode == 0 and local_depois.get("env", {}).get("ANTHROPIC_BASE_URL") == perfis["minimax"]["endereco"]
               and local_depois.get("env", {}).get("ANTHROPIC_DEFAULT_OPUS_MODEL") == perfis["minimax"]["modelo_forte"]
               and "API_MINIMAX" in str(local_depois.get("apiKeyHelper"))
               and json.loads((produto_minimax / ".delta-11/motor/VERSAO").read_text()).get("ia") == "minimax")
        tentar("h) depois de aplicar um perfil, a atualização ainda tira CLAUDE_CODE_FORK_SUBAGENT e mantém as instruções pessoais fora da conversa (claudeMdExcludes) e o caminho de busca",
               lambda: "CLAUDE_CODE_FORK_SUBAGENT" not in local_depois.get("env", {}) and str(Path.home() / ".claude" / "CLAUDE.md") in local_depois.get("claudeMdExcludes", [])
               and bool(local_depois.get("env", {}).get("PATH")))
        voltou = rodar(str(INSTALAR), "--atualizar", "--ia", "claude", str(produto_minimax), ambiente=ambiente)
        local_claude = ler(arquivo_local) if arquivo_local.is_file() else {}
        tentar("d) --atualizar --ia claude volta ao Claude (sem variáveis de IA nem apiKeyHelper; VERSAO diz claude)",
               lambda: voltou.returncode == 0 and not any(v in local_claude.get("env", {}) for v in VARIAVEIS_DA_IA) and "apiKeyHelper" not in local_claude
               and json.loads((produto_minimax / ".delta-11/motor/VERSAO").read_text()).get("ia") == "claude" and bool(local_claude.get("env", {}).get("PATH")))

        # (f) As recusas: gateway sem endereço, perfil desconhecido, pasta sem o v7. Nada é mexido.
        antes = (produto / ".claude" / "settings.local.json").read_text()
        sem_endereco = rodar(str(TROCAR), str(produto), "gateway", ambiente=ambiente)
        desconhecido = rodar(str(TROCAR), str(produto), "gpt-nao-existe", ambiente=ambiente)
        sem_v7 = tmp / "pasta-sem-v7"
        sem_v7.mkdir()
        sem_v7_feito = rodar(str(TROCAR), str(sem_v7), "deepseek", ambiente=ambiente)
        tentar("f) o gateway sem endereço e sem os três modelos recusa com frase clara, sem mexer em nada",
               lambda: sem_endereco.returncode != 0 and "gateway" in sem_endereco.stdout and "--endereco" in sem_endereco.stdout and "--modelo-forte" in sem_endereco.stdout
               and (produto / ".claude" / "settings.local.json").read_text() == antes)
        tentar("f) um perfil desconhecido recusa listando os conhecidos, sem mexer em nada",
               lambda: desconhecido.returncode != 0 and all(n in desconhecido.stdout for n in ("claude", "deepseek", "minimax", "kimi", "glm", "gateway"))
               and (produto / ".claude" / "settings.local.json").read_text() == antes)
        tentar("f) trocar a IA de uma pasta sem o v7 recusa e não cria nada", lambda: sem_v7_feito.returncode != 0 and "v7" in sem_v7_feito.stdout and not (sem_v7 / ".claude").exists())
        gateway = rodar(str(TROCAR), str(produto), "gateway", "--endereco", "https://gateway.exemplo.invalid/anthropic", "--modelo-forte", "forte-x",
                        "--modelo-medio", "medio-y", "--modelo-leve", "leve-z", ambiente=ambiente)
        local_gateway = ler(produto / ".claude" / "settings.local.json")
        tentar("f) o gateway com endereço e os três modelos escreve o que foi dito (a chave vem da entrada API_GATEWAY)",
               lambda: gateway.returncode == 0 and local_gateway["env"]["ANTHROPIC_BASE_URL"] == "https://gateway.exemplo.invalid/anthropic"
               and local_gateway["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "forte-x" and local_gateway["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "medio-y"
               and local_gateway["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "leve-z" and "API_GATEWAY" in local_gateway["apiKeyHelper"])
        instalar_desconhecido = rodar(str(INSTALAR), "--ia", "gpt-nao-existe", str(tmp / "produto-ia-desconhecida"), ambiente=ambiente)
        instalar_gateway_vazio = rodar(str(INSTALAR), "--ia", "gateway", str(tmp / "produto-gateway-vazio"), ambiente=ambiente)
        tentar("f) o instalador também recusa --ia desconhecido e gateway sem endereço, antes de mexer na pasta",
               lambda: instalar_desconhecido.returncode != 0 and "minimax" in instalar_desconhecido.stdout and not (tmp / "produto-ia-desconhecida").exists()
               and instalar_gateway_vazio.returncode != 0 and "--endereco" in instalar_gateway_vazio.stdout and not (tmp / "produto-gateway-vazio").exists())

        # (g) Chave ausente do cofre: a frase combinada, e nada é mexido.
        trocar_de_volta = rodar(str(TROCAR), str(produto), "claude", ambiente=ambiente)
        antes = (produto / ".claude" / "settings.local.json").read_text()
        sem_chave = rodar(str(TROCAR), str(produto), "deepseek", ambiente=ambiente_sem_deepseek)
        instalar_sem_chave = rodar(str(INSTALAR), "--ia", "deepseek", str(tmp / "produto-sem-chave"), ambiente=ambiente_sem_deepseek)
        tentar("g) chave ausente no cofre: o trocar-ia.py recusa com a frase combinada e não muda a configuração",
               lambda: trocar_de_volta.returncode == 0 and sem_chave.returncode != 0 and FRASE_DA_CHAVE_AUSENTE in sem_chave.stdout
               and (produto / ".claude" / "settings.local.json").read_text() == antes)
        tentar("g) chave ausente no cofre: o instalador recusa com a mesma frase, antes de mexer na pasta",
               lambda: instalar_sem_chave.returncode != 0 and FRASE_DA_CHAVE_AUSENTE in instalar_sem_chave.stdout and not (tmp / "produto-sem-chave").exists())

        # Perfil não conferido na fonte oficial: o trocar-ia.py avisa o dono.
        nao_conferido = tmp / "perfis-nao-conferidos.json"
        if perfis:
            copia = json.loads(json.dumps(perfis))
            copia["kimi"].pop("lido_em", None)
            copia["kimi"]["conferido"] = False
            copia["kimi"]["motivo"] = "a página oficial não foi achada"
            nao_conferido.write_text(json.dumps(copia))
        trocou = rodar(str(TROCAR), str(produto), "kimi", ambiente={**ambiente, "DELTA11_PERFIS_DE_IA": str(nao_conferido)})
        tentar("um perfil com `conferido: false` funciona, mas o trocar-ia.py avisa o dono, com o motivo",
               lambda: trocou.returncode == 0 and "AVISO" in trocou.stdout and "a página oficial não foi achada" in trocou.stdout)

    if falhas:
        print(f"PULSO DOS PERFIS DE IA FALHOU — {len(falhas)}: " + "; ".join(falhas))
        return 1
    print("PULSO DOS PERFIS DE IA OK — a IA de cada produto troca por perfil, a chave nunca vai para arquivo, e as proteções do instalador ficam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
