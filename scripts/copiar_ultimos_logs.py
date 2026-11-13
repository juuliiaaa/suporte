"""Copia, para uma pasta de destino, o log mais recente de cada cenário de rodar_casos.

  python -m scripts.copiar_ultimos_logs                 # copia para logs_teste/
  python -m scripts.copiar_ultimos_logs --destino logs  # sobrescreve logs/<cenário>.json

Os logs de rodar_casos têm o nome exec_AAAAMMDD_HHMMSS_<cenário>.json. O mais
recente de cada cenário (pelo nome, que carrega o carimbo) vai para
<destino>/<cenário>.json.
"""
import argparse
import re
import shutil
from pathlib import Path

from scripts.rodar_casos import CASOS
from src import config

PADRAO = re.compile(r"^exec_\d{8}_\d{6}_(?P<rotulo>.+)\.json$")


def mais_recentes(pasta: Path) -> dict:
    achados = {}
    for caminho in sorted(pasta.glob("exec_*.json")):
        m = PADRAO.match(caminho.name)
        if m:
            achados[m["rotulo"]] = caminho  # a ordem alfabética já é cronológica
    return achados


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--destino", default="logs_teste")
    a = p.parse_args()
    origem = Path(config.PASTA_LOGS)
    destino = Path(a.destino)
    destino.mkdir(parents=True, exist_ok=True)
    achados = mais_recentes(origem)
    for _, (rotulo, *_) in sorted(CASOS.items()):
        if rotulo not in achados:
            print(f"FALTA  {rotulo}: nenhum log exec_* encontrado")
            continue
        alvo = destino / f"{rotulo}.json"
        shutil.copyfile(achados[rotulo], alvo)
        print(f"ok     {achados[rotulo].name} -> {alvo}")


if __name__ == "__main__":
    main()
