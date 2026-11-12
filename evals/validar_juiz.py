"""Valida o juiz contra rótulos humanos.

  python -m evals.validar_juiz

Entrada: evals/dados_juiz/amostras.jsonl (20 saídas com `rotulo_humano` true/false e
`nota_humana` escritos à mão) e evals/dados_juiz/limiar.json (declarado antes de medir).
Saída: evals/resultados/juiz/validacao.json, com a matriz de concordância, o
percentual, o kappa e cada desacordo para ser lido e classificado em
evals/dados_juiz/classificacao_desacordos.jsonl (id, classe, comentario), onde
classe é defeito_do_juiz, defeito_da_rubrica ou defeito_do_rotulo_humano.
"""
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASTA = os.path.join(RAIZ, "evals", "dados_juiz")
SAIDA = os.path.join(RAIZ, "evals", "resultados", "juiz", "validacao.json")


def matriz(pares):
    """pares: lista de (humano, juiz) booleanos."""
    m = {"humano_aprova_juiz_aprova": 0, "humano_aprova_juiz_reprova": 0,
         "humano_reprova_juiz_aprova": 0, "humano_reprova_juiz_reprova": 0}
    for h, j in pares:
        m[f"humano_{'aprova' if h else 'reprova'}_juiz_{'aprova' if j else 'reprova'}"] += 1
    return m


def concordancia(m):
    n = sum(m.values())
    return (m["humano_aprova_juiz_aprova"] + m["humano_reprova_juiz_reprova"]) / n if n else float("nan")


def kappa(m):
    n = sum(m.values())
    if not n:
        return float("nan")
    po = concordancia(m)
    h_apr = (m["humano_aprova_juiz_aprova"] + m["humano_aprova_juiz_reprova"]) / n
    j_apr = (m["humano_aprova_juiz_aprova"] + m["humano_reprova_juiz_aprova"]) / n
    pe = h_apr * j_apr + (1 - h_apr) * (1 - j_apr)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main():
    from . import juiz as juiz_mod

    amostras = [json.loads(l) for l in open(os.path.join(PASTA, "amostras.jsonl"), encoding="utf-8") if l.strip()]
    sem_rotulo = [a["id"] for a in amostras if not isinstance(a.get("rotulo_humano"), bool) or not a.get("nota_humana")]
    if sem_rotulo:
        sys.exit(f"Faltam rotulo_humano (true/false) e nota_humana em: {', '.join(sem_rotulo)}. "
                 "Rotule à mão em evals/dados_juiz/amostras.jsonl antes de validar.")
    limiar = json.load(open(os.path.join(PASTA, "limiar.json"), encoding="utf-8"))
    sys.path.insert(0, RAIZ)
    from src import config
    from src.llm import ClienteLLM

    cliente = ClienteLLM()._cliente()
    modelo = os.environ.get("LLM_JUIZ_MODEL") or config.MODELO
    pares, linhas = [], []
    for a in amostras:
        v = juiz_mod.julgar(cliente, modelo, a["mensagem"], a["resposta"])
        linhas.append({**a, "juiz": v})
        if v["aprovado"] is not None:
            pares.append((a["rotulo_humano"], v["aprovado"]))
    m = matriz(pares)
    conc, k = concordancia(m), kappa(m)
    classificados = {}
    arq_cls = os.path.join(PASTA, "classificacao_desacordos.jsonl")
    if os.path.exists(arq_cls):
        for l in open(arq_cls, encoding="utf-8"):
            if l.strip():
                d = json.loads(l)
                classificados[d["id"]] = d
    desacordos = [{"id": l["id"], "humano": l["rotulo_humano"], "juiz": l["juiz"]["aprovado"],
                   "nota_humana": l["nota_humana"], "motivo_do_juiz": l["juiz"]["motivo"],
                   "classificacao": classificados.get(l["id"])}
                  for l in linhas if l["juiz"]["aprovado"] != l["rotulo_humano"]]
    resultado = {
        "rubrica_versao": juiz_mod.RUBRICA_VERSAO, "juiz_modelo": modelo, "n": len(amostras),
        "falhas_do_juiz": sum(1 for l in linhas if l["juiz"]["aprovado"] is None),
        "matriz": m, "concordancia": conc, "kappa": k,
        "limiar_concordancia": limiar["concordancia_minima"], "limiar_kappa": limiar["kappa_minimo"],
        "adotado": bool(conc >= limiar["concordancia_minima"] and k >= limiar["kappa_minimo"]),
        "desacordos": desacordos,
        "desacordos_sem_classificacao": [d["id"] for d in desacordos if not d["classificacao"]],
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump(resultado, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"concordância {100 * conc:.0f}% (limiar {100 * limiar['concordancia_minima']:.0f}%)  "
          f"kappa {k:.2f} (limiar {limiar['kappa_minimo']})  {'ADOTADO' if resultado['adotado'] else 'NÃO ADOTADO'}")
    print(json.dumps(m, indent=2))
    for d in desacordos:
        print(f"desacordo {d['id']}: humano={d['humano']} juiz={d['juiz']}  juiz disse: {d['motivo_do_juiz']}")
    if resultado["desacordos_sem_classificacao"]:
        print("Classifique em evals/dados_juiz/classificacao_desacordos.jsonl:", resultado["desacordos_sem_classificacao"])


if __name__ == "__main__":
    main()
