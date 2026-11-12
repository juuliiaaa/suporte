"""Compara duas rodadas, por classe.

  python -m evals.comparar evals/resultados/<rodada-A> evals/resultados/<rodada-B>
"""
import json
import os
import sys
from collections import OrderedDict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARQ_JUIZ = os.path.join(RAIZ, "evals", "resultados", "juiz", "validacao.json")


def ler(pasta):
    meta = json.load(open(os.path.join(pasta, "meta.json"), encoding="utf-8"))
    linhas = [json.loads(l) for l in open(os.path.join(pasta, "resultados.jsonl"), encoding="utf-8") if l.strip()]
    return meta, linhas


def por_classe(linhas):
    acc = OrderedDict()
    for l in linhas:
        acc.setdefault(l["classe"], []).append(l["ok"])
    return acc


def pct(oks):
    return 100.0 * sum(oks) / len(oks) if oks else float("nan")


def ultimos(linhas):
    """Vale a última linha de cada caso (evals/mesclar.py acrescenta a reexecução)."""
    d = OrderedDict()
    for l in linhas:
        d[l["id"]] = l
    return list(d.values())


def relatorio(pasta_a, pasta_b) -> str:
    ma, la = ler(pasta_a)
    mb, lb = ler(pasta_b)
    la, lb = ultimos(la), ultimos(lb)
    inval = {l["id"] for l in la + lb if l.get("invalido")}
    da = {l["id"]: l for l in la if l["id"] not in inval}
    db_ = {l["id"]: l for l in lb if l["id"] not in inval}
    comuns = [i for i in da if i in db_]
    la, lb = [da[i] for i in comuns], [db_[i] for i in comuns]
    ca, cb = por_classe(la), por_classe(lb)
    o = mb["origens"]
    out = [f"DATASET v{mb['dataset_versao']}   {len(comuns)} casos comparados de {mb['n_casos']}   "
           f"(producao {o['producao']} · desenvolvimento {o['desenvolvimento']} · sintetico {o['sintetico']})"]
    if inval or len(comuns) < max(len(da), len(db_)):
        out.append(f"AVISO: excluídos por limite do provedor ou não executados nas duas rodadas: "
                   f"{sorted(inval | (set(da) ^ set(db_))) or 'nenhum'}. Só os {len(comuns)} casos válidos nas duas entram.")
    if os.path.exists(ARQ_JUIZ):
        j = json.load(open(ARQ_JUIZ, encoding="utf-8"))
        out.append(f"JUIZ rubrica v{j['rubrica_versao']}   concordância {100 * j['concordancia']:.0f}%   "
                   f"limiar {100 * j['limiar_concordancia']:.0f}%   {'adotado' if j['adotado'] else 'NÃO adotado'}")
    else:
        out.append("JUIZ sem validação registrada (rode python -m evals.validar_juiz)")
    out += ["", f"{'classe':<14}{'casos':>6}{'versão A':>10}{'versão B':>10}{'delta':>8}",
            f"{'':<14}{'':>6}{ma['versao_sistema']:>10}{mb['versao_sistema']:>10}"]
    for classe in OrderedDict.fromkeys(list(ca) + list(cb)):
        a, b = pct(ca.get(classe, [])), pct(cb.get(classe, []))
        out.append(f"{classe:<14}{len(cb.get(classe, [])):>6}{a:>9.0f}%{b:>9.0f}%{b - a:>+8.0f}")
    ta, tb = pct([l["ok"] for l in la]), pct([l["ok"] for l in lb])
    out.append(f"{'MÉDIA':<14}{len(comuns):>6}{ta:>9.0f}%{tb:>9.0f}%{tb - ta:>+8.0f}")
    mudou = [(i, da[i]["ok"], db_[i]["ok"]) for i in comuns if da[i]["ok"] != db_[i]["ok"]]
    if mudou:
        out += ["", "Casos que mudaram:"] + [f"  {i}: {'ok' if a else 'FALHA'} -> {'ok' if b else 'FALHA'}" for i, a, b in mudou]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python -m evals.comparar <rodada-A> <rodada-B>")
    print(relatorio(sys.argv[1], sys.argv[2]))
