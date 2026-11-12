"""Mostra os traces gravados como árvore de spans.

  python -m scripts.ver_trace                      # a última execução em logs/traces
  python -m scripts.ver_trace --todos              # todas
  python -m scripts.ver_trace --pasta <rodada>/traces --caso D05
"""
import argparse
import glob
import json
import os
from collections import defaultdict

from src import config

CHAVES_RAIZ = ["suporte.versao_sistema", "suporte.motivo_termino", "suporte.entrada", "suporte.saida",
               "suporte.ferramentas_chamadas", "suporte.trechos_recuperados", "suporte.prompt.sistema",
               "suporte.tokens_total", "suporte.segundos_ativos"]


def carregar(pasta):
    spans = []
    for arq in sorted(glob.glob(os.path.join(pasta, "spans-*.jsonl"))):
        spans += [json.loads(l) for l in open(arq, encoding="utf-8") if l.strip()]
    return spans


def imprimir(spans):
    filhos = defaultdict(list)
    for s in spans:
        filhos[s["parent_span_id"]].append(s)

    def no(s, nivel):
        dur = (s["end_time_unix_nano"] - s["start_time_unix_nano"]) / 1e9
        a = s["attributes"]
        extra = ""
        if s["name"].startswith("chat "):
            extra = f"  tokens in/out {a.get('gen_ai.usage.input_tokens')}/{a.get('gen_ai.usage.output_tokens')}"
        if s["name"].startswith("execute_tool "):
            extra = f"  args={a.get('gen_ai.tool.call.arguments')}  erro={a.get('suporte.ferramenta.erro')}"
        print(f"{'  ' * nivel}{s['name']}  [{dur:.2f}s] {s['status']}{extra}")
        for e in s["events"]:
            print(f"{'  ' * (nivel + 1)}evento {e['name']}: {json.dumps(e['attributes'], ensure_ascii=False)}")
        for f in sorted(filhos.get(s["span_id"], []), key=lambda x: x["start_time_unix_nano"]):
            no(f, nivel + 1)

    raizes = [s for s in spans if s["parent_span_id"] is None]
    for r in sorted(raizes, key=lambda x: x["start_time_unix_nano"]):
        print(f"\ntrace {r['trace_id']}  caso={r['attributes'].get('suporte.caso_id', '-')}")
        for k in CHAVES_RAIZ:
            if k in r["attributes"]:
                print(f"  {k} = {r['attributes'][k]}")
        no(r, 0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pasta", default=config.PASTA_TRACES)
    p.add_argument("--todos", action="store_true")
    p.add_argument("--caso")
    a = p.parse_args()
    spans = carregar(a.pasta)
    if not spans:
        raise SystemExit(f"nenhum span em {a.pasta}")
    por_trace = defaultdict(list)
    for s in spans:
        por_trace[s["trace_id"]].append(s)
    ids = list(por_trace)
    if a.caso:
        ids = [t for t in ids if any(s["attributes"].get("suporte.caso_id") == a.caso for s in por_trace[t])]
    elif not a.todos:
        ids = ids[-1:]
    imprimir([s for t in ids for s in por_trace[t]])


if __name__ == "__main__":
    main()
