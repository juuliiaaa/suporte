"""Acrescenta à rodada-base os casos reexecutados em outra rodada (resultados, traces e logs).

  python -m evals.mesclar <rodada-base> <rodada-reexecucao>

O comparar e o metricas passam a usar a última linha de cada caso; execuções
marcadas `invalido` na rodada-base continuam fora das métricas.
"""
import glob
import os
import shutil
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__)
base, novo = sys.argv[1], sys.argv[2]
with open(os.path.join(novo, "resultados.jsonl"), encoding="utf-8") as f:
    novas = [l for l in f if l.strip()]
with open(os.path.join(base, "resultados.jsonl"), "a", encoding="utf-8") as f:
    f.writelines(l if l.endswith("\n") else l + "\n" for l in novas)
os.makedirs(os.path.join(base, "traces"), exist_ok=True)
os.makedirs(os.path.join(base, "logs"), exist_ok=True)
for arq in glob.glob(os.path.join(novo, "traces", "spans-*.jsonl")):
    shutil.copy(arq, os.path.join(base, "traces", "spans-reexec-" + os.path.basename(arq)[len("spans-"):]))
for arq in glob.glob(os.path.join(novo, "logs", "*.json")):
    shutil.copy(arq, os.path.join(base, "logs", "reexec-" + os.path.basename(arq)))
print(f"{len(novas)} casos acrescentados a {base}")
