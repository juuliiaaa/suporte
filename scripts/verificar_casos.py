"""Verificador do case (docs/case.md §6 e §7).

Compara, para cada caso rotulado à mão em dados/casos_rotulados.json, a ação
esperada com a ação lida do log de trajetória, sem chamar o modelo.

Vocabulário de ações (a mais forte vence):
  agendar   o nó de agendamento gravou uma visita (aprovacao_humana com status AGENDADA)
  reiniciar reiniciar_conexao rodou sem erro
  escalar   a saída encaminha para atendente humano
  nao_agir  nenhuma das anteriores

Critério de sucesso: pelo menos 8 de 10 acertos e nenhuma visita em bairro
em manutenção. A saída é o código de retorno (0 = critério atendido).

Uso:
  python -m scripts.verificar_casos                 # lê logs/
  python -m scripts.verificar_casos --pasta X       # lê outra pasta de logs
  python -m scripts.verificar_casos --escrever      # grava docs/verificacao.md
"""
import argparse
import json
import os

from src import config

CASOS = os.path.join(config.PASTA_DADOS, "casos_rotulados.json")
MINIMO_ACERTOS = 8


def carregar_casos(caminho=CASOS):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def acao_do_log(log: dict) -> str:
    """Ação realizada, lida só da trajetória e da saída gravadas no log."""
    trajetoria = log.get("trajetoria", [])
    saida = log.get("saida") or {}
    for t in trajetoria:
        r = t.get("resultado")
        if t.get("tipo") == "aprovacao_humana" and isinstance(r, dict) and r.get("status") == "AGENDADA":
            return "agendar"
    for t in trajetoria:
        r = t.get("resultado")
        if (t.get("tipo") == "ferramenta" and t.get("nome") == "reiniciar_conexao"
                and isinstance(r, dict) and "erro" not in r):
            return "reiniciar"
    if saida.get("encaminhar_humano") or log.get("motivo_parada") in ("encaminhado_humano", "aprovacao_expirada"):
        return "escalar"
    return "nao_agir"


def _ja_existia(log: dict):
    for t in log.get("trajetoria", []):
        r = t.get("resultado")
        if t.get("tipo") == "aprovacao_humana" and isinstance(r, dict) and "ja_existia" in r:
            return r["ja_existia"]
    return None


def avaliar(pasta_logs: str, casos=None) -> dict:
    casos = casos or carregar_casos()
    linhas, acertos, violacoes, sem_log = [], 0, [], 0
    tokens = []
    for c in casos:
        caminho = os.path.join(pasta_logs, c["rotulo"] + ".json")
        if not os.path.exists(caminho):
            sem_log += 1
            linhas.append({"id": c["id"], "rotulo": c["rotulo"], "esperada": c["acao_esperada"],
                           "lida": "sem log", "ok": False, "extra": ""})
            continue
        with open(caminho, encoding="utf-8") as f:
            log = json.load(f)
        lida = acao_do_log(log)
        ok = lida == c["acao_esperada"]
        extras = []
        if "suficiente_esperado" in c:
            suf = (log.get("saida") or {}).get("suficiente")
            if suf != c["suficiente_esperado"]:
                ok = False
                extras.append(f"suficiente={suf}, esperado {c['suficiente_esperado']}")
        if "ja_existia_esperado" in c:
            ja = _ja_existia(log)
            if ja != c["ja_existia_esperado"]:
                ok = False
                extras.append(f"ja_existia={ja}, esperado {c['ja_existia_esperado']}")
        if c.get("bairro_em_manutencao") and lida == "agendar":
            violacoes.append(c["rotulo"])
            ok = False
            extras.append("visita agendada em bairro em manutenção")
        if log.get("tokens"):
            tokens.append(log["tokens"])
        acertos += ok
        linhas.append({"id": c["id"], "rotulo": c["rotulo"], "esperada": c["acao_esperada"],
                       "lida": lida, "ok": ok, "extra": "; ".join(extras)})
    return {
        "linhas": linhas, "acertos": acertos, "total": len(casos), "violacoes": violacoes,
        "sem_log": sem_log, "tokens_medios": round(sum(tokens) / len(tokens)) if tokens else 0,
        "criterio_ok": acertos >= MINIMO_ACERTOS and not violacoes,
    }


def tabela_md(res: dict) -> str:
    out = ["| # | Caso (log) | Ação esperada | Ação lida do log | Resultado |", "|---|---|---|---|---|"]
    for l in res["linhas"]:
        marca = "acerto" if l["ok"] else "erro" + (f" ({l['extra']})" if l["extra"] else "")
        out.append(f"| {l['id']} | `{l['rotulo']}` | {l['esperada']} | {l['lida']} | {marca} |")
    return "\n".join(out)


def resumo(res: dict) -> str:
    v = "nenhuma" if not res["violacoes"] else ", ".join(res["violacoes"])
    return (f"Acertos: {res['acertos']} de {res['total']} (mínimo {MINIMO_ACERTOS}). "
            f"Visitas em bairro em manutenção: {v}. "
            f"Critério de sucesso: {'atendido' if res['criterio_ok'] else 'NÃO atendido'}.")


def escrever_md(res: dict, destino: str, pasta_logs: str):
    primeiro = None
    for l in res["linhas"]:
        caminho = os.path.join(pasta_logs, l["rotulo"] + ".json")
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                d = json.load(f)
            primeiro = d
            break
    cab = ""
    if primeiro:
        cab = f"Modelo: {primeiro.get('modelo')}, commit {primeiro.get('commit')}, primeira execução em {primeiro.get('timestamp')}.\n\n"
    with open(destino, "w", encoding="utf-8") as f:
        f.write("# Verificação dos casos rotulados\n\n")
        f.write("Gerado por `python -m scripts.verificar_casos --escrever` a partir dos logs.\n")
        f.write("Cada linha compara a ação esperada (`dados/casos_rotulados.json`) com a ação lida do log de trajetória.\n\n")
        f.write(cab + tabela_md(res) + "\n\n" + resumo(res) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pasta", default=config.PASTA_LOGS)
    p.add_argument("--escrever", action="store_true")
    a = p.parse_args()
    res = avaliar(a.pasta)
    print(tabela_md(res))
    print()
    print(resumo(res))
    if res["sem_log"]:
        print(f"{res['sem_log']} caso(s) sem log em {a.pasta}: rode `python -m scripts.rodar_casos --reset`.")
    if a.escrever:
        destino = os.path.join(config.RAIZ, "docs", "verificacao.md")
        escrever_md(res, destino, a.pasta)
        print(f"{destino} gerado")
    raise SystemExit(0 if res["criterio_ok"] else 1)


if __name__ == "__main__":
    main()
