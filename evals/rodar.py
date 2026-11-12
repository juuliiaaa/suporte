"""Roda o golden dataset contra o sistema entregue (o mesmo
`executar_atendimento` que `python -m src.agent` usa).

  python -m evals.rodar --versao 3.1.0
  python -m evals.rodar --versao 3.0.0 --controles off
  python -m evals.rodar --versao 3.1.0 --casos D01 S04 --sem-juiz

Cada rodada vira uma pasta em evals/resultados/ com meta.json, resultados.jsonl,
logs/ e traces/ (os spans da rodada). Cada caso roda em banco e memória novos.
"""
import argparse
import datetime
import json
import os
import shutil
import sys
import time

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARQ_DATASET = os.path.join(RAIZ, "evals", "dataset.jsonl")
ARQ_META = os.path.join(RAIZ, "evals", "dataset.meta.json")


def carregar_dataset(caminho: str = ARQ_DATASET):
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def e_cota(texto) -> bool:
    """O erro do modelo é limite do provedor (429), não falha do sistema."""
    t = str(texto or "").lower()
    return "429" in t or "ratelimit" in t or "limite_diario" in t or "per day" in t


def e_cota_diaria(texto) -> bool:
    t = str(texto or "").lower()
    return "limite_diario" in t or "per day" in t or "(tpd)" in t


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--versao", required=True, help="versão do sistema sob teste, carimbada no trace")
    p.add_argument("--controles", choices=["on", "off"], default="on")
    p.add_argument("--casos", nargs="*")
    p.add_argument("--sem-juiz", action="store_true")
    p.add_argument("--juiz-modelo", help="modelo do juiz (padrão: LLM_JUIZ_MODEL ou o do sistema)")
    p.add_argument("--simulado", action="store_true",
                   help="usa a política de referência no lugar do modelo (verifica o arcabouço, não é evidência)")
    p.add_argument("--pausa", type=float, default=0.0, help="segundos entre casos (limite de taxa)")
    p.add_argument("--saida", default=os.path.join(RAIZ, "evals", "resultados"))
    a = p.parse_args(argv)

    os.environ["CONTROLES"] = a.controles
    os.environ["SISTEMA_VERSAO"] = a.versao
    rodada = f"{a.versao}_{'com' if a.controles == 'on' else 'sem'}-controles_{datetime.datetime.now():%Y%m%d-%H%M%S}"
    pasta = os.path.join(a.saida, rodada)
    os.makedirs(pasta, exist_ok=True)
    os.environ["PASTA_TRACES"] = os.path.join(pasta, "traces")
    os.environ["PASTA_LOGS"] = os.path.join(pasta, "logs")

    sys.path.insert(0, RAIZ)
    from src import config, db, memoria, tools
    from src.agent import decisor_fixo, executar_atendimento
    from src.llm import ClienteLLM

    from . import juiz as juiz_mod, verificacoes as vf

    casos = carregar_dataset()
    if a.casos:
        casos = [c for c in casos if c["id"] in a.casos]
    meta = json.load(open(ARQ_META, encoding="utf-8"))
    if a.simulado:
        from .politica_de_referencia import PoliticaDeReferencia
        a.sem_juiz = True
    llm = PoliticaDeReferencia() if a.simulado else None
    cliente_juiz = None if a.sem_juiz else ClienteLLM()._cliente()
    modelo_juiz = a.juiz_modelo or os.environ.get("LLM_JUIZ_MODEL") or config.MODELO
    hoje = tools._hoje()
    trabalho = os.path.join(pasta, "_mundo")

    def mundo_novo():
        shutil.rmtree(trabalho, ignore_errors=True)
        os.makedirs(trabalho)
        db.DB_PATH = os.path.join(trabalho, "provedor.db")
        config.CAMINHO_MEMORIA = os.path.join(trabalho, "memoria.db")
        config.CAMINHO_CHECKPOINTS = os.path.join(trabalho, "checkpoints.db")
        db.inicializar()

    def canal_de(caso):
        c = caso["canal"]
        return db.canal_simulado(caso["contrato"]) if c == "titular" else db.canal_simulado(c.split(":", 1)[1])

    def decisor_de(d):
        if not d:
            return decisor_fixo("rejeitar")
        return decisor_fixo(d["decisao"], vf.resolver_data(d["data"], hoje) if d.get("data") else None)

    saidas, nao_executados = [], []
    for caso in casos:
        mundo_novo()
        attrs = {"suporte.rodada": rodada, "suporte.caso_id": caso["id"], "suporte.caso_classe": caso["classe"]}
        for i, pre in enumerate(caso.get("preludio") or []):
            executar_atendimento(caso["contrato"], pre["mensagem"], decisor=decisor_de(pre["decisao"]),
                                 canal=canal_de(caso), rotulo=f"{caso['id']}_preludio{i}", llm=llm,
                                 atributos_trace={**attrs, "suporte.preludio": True})
        reg = executar_atendimento(caso["contrato"], caso["mensagem"], decisor=decisor_de(caso.get("decisao")),
                                   canal=canal_de(caso), rotulo=caso["id"], atributos_trace=attrs, llm=llm)
        mundo = vf.estado_do_mundo()
        esp = caso["esperado"]
        niveis = {
            "deterministico": vf.deterministico(esp, reg),
            "trajetoria": vf.trajetoria(esp, reg),
            "resultado": vf.resultado(esp, mundo, hoje, caso["contrato"]),
        }
        verdito_juiz = None
        if caso.get("juiz") and cliente_juiz is not None:
            verdito_juiz = juiz_mod.julgar(cliente_juiz, modelo_juiz, caso["mensagem"],
                                           (reg.get("saida") or {}).get("resultado", ""))
            niveis["juiz"] = [] if verdito_juiz["aprovado"] else [f"juiz: {verdito_juiz['motivo']}"]
        ok = all(not f for f in niveis.values())
        det = vf.detalhe_do_erro(reg) if reg["motivo_parada"] == "erro_fatal_llm" else ""
        invalido = bool(det) and e_cota(det)
        if invalido:
            ok = False
        saidas.append({"id": caso["id"], "classe": caso["classe"], "origem": caso["origem"], "ok": ok,
                       "invalido": invalido,
                       "falhas": {k: v for k, v in niveis.items() if v}, "juiz": verdito_juiz,
                       "motivo_parada": reg["motivo_parada"], "trace_id": reg["trace_id"],
                       "tokens": reg["tokens"], "resposta": (reg.get("saida") or {}).get("resultado")})
        if invalido:
            print(f"INVÁLIDO {caso['id']:4} {caso['classe']:12} limite do provedor (não é falha do sistema)")
            if e_cota_diaria(det):
                nao_executados = [c["id"] for c in casos[casos.index(caso) + 1:]]
                print("       limite DIÁRIO esgotado: rodada interrompida. Rode o resto depois com --casos.")
                break
        else:
            print(f"{'ok  ' if ok else 'FALHA'} {caso['id']:4} {caso['classe']:12} {reg['motivo_parada']}")
            if reg["motivo_parada"] == "erro_fatal_llm":
                print(f"       (erro do modelo) {det}")
            for nivel, falhas in niveis.items():
                for f in falhas:
                    print(f"       [{nivel}] {f}")
        if a.pausa:
            time.sleep(a.pausa)

    shutil.rmtree(trabalho, ignore_errors=True)
    with open(os.path.join(pasta, "resultados.jsonl"), "w", encoding="utf-8") as f:
        for s in saidas:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(os.path.join(pasta, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"rodada": rodada, "versao_sistema": a.versao, "controles": a.controles,
                   "dataset_versao": meta["versao"], "n_casos": len(saidas),
                   "invalidos": [x["id"] for x in saidas if x["invalido"]], "nao_executados": nao_executados,
                   "modelo": "politica-de-referencia (simulado)" if a.simulado else config.MODELO, "juiz_modelo": None if a.sem_juiz else modelo_juiz,
                   "juiz_rubrica": None if a.sem_juiz else juiz_mod.RUBRICA_VERSAO,
                   "data": datetime.datetime.now().isoformat(timespec="seconds"),
                   "origens": {o: sum(1 for c in casos if c["origem"] == o)
                               for o in ("producao", "desenvolvimento", "sintetico")}},
                  f, ensure_ascii=False, indent=2)
    validos = [s for s in saidas if not s["invalido"]]
    print(f"\n{sum(s['ok'] for s in validos)}/{len(validos)} casos ok ({len(saidas) - len(validos)} inválidos por limite do provedor, "
          f"{len(nao_executados)} não executados). Resultado em {os.path.relpath(pasta, RAIZ)}")
    return pasta


if __name__ == "__main__":
    main()
