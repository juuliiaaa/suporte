import json
p = r"evals\resultados\3.1.0_com-controles_20261111-220243\resultados.jsonl"
L = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
for d in L:
    d["invalido"] = (d["motivo_parada"] == "erro_fatal_llm")
    d["ok"] = d["ok"] and not d["invalido"]
open(p, "w", encoding="utf-8").write("\n".join(json.dumps(d, ensure_ascii=False) for d in L) + "\n")
print(sum(d["invalido"] for d in L), "inválidos:", [d["id"] for d in L if d["invalido"]])
