"""Métricas sobre os traces (docs/observabilidade.md §3 e §5).

  python -m evals.metricas evals/resultados/<rodada> [<rodada> ...]
  python -m evals.metricas evals/resultados/<rodada> ... --escrever

Lê spans-*.jsonl de <rodada>/traces, corta por versão do sistema e imprime:
latência p50/p95 (sem a espera humana), custo por execução, distribuição dos
motivos de término, taxa de erro por ferramenta e o SLI/SLO de qualidade.
Com --escrever, grava o relatório em docs/observabilidade.md, entre os
marcadores METRICAS.
"""
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC = os.path.join(RAIZ, "docs", "observabilidade.md")
INI, FIM = "<!-- METRICAS:INICIO -->", "<!-- METRICAS:FIM -->"
PRECOS = {"qwen/qwen3.8-27b": (0.80, 4.00), "openai/gpt-oss-20b": (0.075, 0.30),
          "openai/gpt-oss-120b": (0.15, 0.60)}
SLO_ALVO = 0.90
# Desfechos previstos pelo desenho (mesma lista de src/observabilidade.TERMINOS_NORMAIS)
BONS = {"resposta_final", "entrada_incompleta", "encaminhado_humano", "aprovacao_expirada",
        "identidade_nao_verificada", "agente_suspenso"}


def percentil(valores, p):
    if not valores:
        return float("nan")
    v = sorted(valores)
    k = (len(v) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return v[f] + (v[c] - v[f]) * (k - f)


def ler_spans(pastas):
    spans = []
    for pasta in pastas:
        for arq in sorted(glob.glob(os.path.join(pasta, "traces", "spans-*.jsonl"))):
            spans += [json.loads(l) for l in open(arq, encoding="utf-8") if l.strip()]
    return spans


def trace_ids_invalidos(pastas):
    """trace_id das execuções marcadas `invalido` (limite do provedor) em resultados.jsonl."""
    ids = set()
    for p in pastas:
        arq = os.path.join(p, "resultados.jsonl")
        if os.path.exists(arq):
            for l in open(arq, encoding="utf-8"):
                if l.strip():
                    d = json.loads(l)
                    if d.get("invalido"):
                        ids.add(d["trace_id"])
    return ids


def custo(modelo, entrada, saida):
    if modelo not in PRECOS:
        return None
    pe, ps = PRECOS[modelo]
    return (entrada * pe + saida * ps) / 1e6


def calcular(spans, invalidos=frozenset()):
    por_trace = defaultdict(list)
    for s in spans:
        por_trace[s["trace_id"]].append(s)
    versoes = defaultdict(lambda: {"lat": [], "custos": [], "motivos": Counter(), "ferr": defaultdict(lambda: [0, 0]),
                                   "sem_preco": 0, "tokens": []})
    for trace_id, filhos in por_trace.items():
        if trace_id in invalidos:
            continue
        raiz = next((s for s in filhos if s["parent_span_id"] is None and s["name"].startswith("invoke_agent")), None)
        if raiz is None:
            continue
        a = raiz["attributes"]
        v = versoes[a.get("suporte.versao_sistema", "?")]
        dur = (raiz["end_time_unix_nano"] - raiz["start_time_unix_nano"]) / 1e9
        v["lat"].append(max(0.0, dur - a.get("suporte.espera_humana_s", 0.0)))
        v["motivos"][a.get("suporte.motivo_termino", "?")] += 1
        total, pendente = 0.0, False
        for s in filhos:
            sa = s["attributes"]
            if s["name"].startswith("chat "):
                c = custo(sa.get("gen_ai.request.model"), sa.get("gen_ai.usage.input_tokens", 0),
                          sa.get("gen_ai.usage.output_tokens", 0))
                if c is None:
                    pendente = True
                else:
                    total += c
            elif s["name"].startswith("execute_tool "):
                par = v["ferr"][sa["gen_ai.tool.name"]]
                par[0] += 1
                par[1] += 1 if sa.get("suporte.ferramenta.erro") else 0
        if pendente:
            v["sem_preco"] += 1
        else:
            v["custos"].append(total)
        v["tokens"].append(a.get("suporte.tokens_total", 0))
    return versoes


def relatorio(versoes) -> str:
    out = []
    for versao in sorted(versoes):
        v = versoes[versao]
        n = len(v["lat"])
        bons = sum(c for m, c in v["motivos"].items() if m in BONS)
        sli = bons / n if n else float("nan")
        orcamento = (1 - sli) / (1 - SLO_ALVO) if n else float("nan")
        out += [f"### Versão {versao} ({n} execuções)", "",
                f"- Latência (sem a espera humana): p50 {percentil(v['lat'], 50):.1f} s, p95 {percentil(v['lat'], 95):.1f} s",
                f"- Tokens por execução: média {sum(v['tokens']) / n:.0f}" if n else "",
                (f"- Custo por execução: US$ {sum(v['custos']) / len(v['custos']):.5f}" if v["custos"]
                 else "- Custo por execução: sem preço cadastrado para o modelo desta rodada")
                + (f" ({v['sem_preco']} execuções sem preço de modelo)" if v["sem_preco"] and v["custos"] else ""),
                "", "| Motivo de término | Execuções | % |", "|---|---|---|"]
        out += [f"| {m} | {c} | {100 * c / n:.0f}% |" for m, c in v["motivos"].most_common()]
        out += ["", "| Ferramenta | Chamadas | Com erro | Taxa de erro |", "|---|---|---|---|"]
        out += [f"| {t} | {c} | {e} | {100 * e / c:.0f}% |" for t, (c, e) in sorted(v["ferr"].items())]
        out += ["", f"SLI de qualidade: {bons}/{n} = {100 * sli:.1f}%. SLO: {100 * SLO_ALVO:.0f}%. "
                    f"Orçamento de erro consumido: {100 * orcamento:.0f}% "
                    f"({'SLO VIOLADO' if sli < SLO_ALVO else 'dentro do SLO'}).", ""]
    return "\n".join(l for l in out if l is not None)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit("uso: python -m evals.metricas <rodada> [<rodada> ...] [--escrever]")
    spans = ler_spans(args)
    texto = relatorio(calcular(spans, trace_ids_invalidos(args)))
    print(texto)
    if "--escrever" in sys.argv:
        doc = open(DOC, encoding="utf-8").read()
        i, j = doc.index(INI) + len(INI), doc.index(FIM)
        gerado = f"\nGerado por `python -m evals.metricas {' '.join(os.path.relpath(a, RAIZ) for a in args)}`.\n\n{texto}\n"
        open(DOC, "w", encoding="utf-8").write(doc[:i] + gerado + doc[j:])
        print(f"escrito em {os.path.relpath(DOC, RAIZ)}")


if __name__ == "__main__":
    main()
