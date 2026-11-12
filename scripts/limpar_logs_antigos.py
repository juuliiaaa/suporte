"""Aplica a retenção local de logs; exige confirmação para apagar arquivos."""
import argparse
import datetime as dt
import json
from pathlib import Path

from src import config


def candidatos(dias: int, agora=None):
    agora = agora or dt.datetime.now()
    limite = agora - dt.timedelta(days=dias)
    encontrados = []
    pasta = Path(config.PASTA_LOGS)
    if not pasta.exists():
        return encontrados
    for caminho in sorted(pasta.glob("*.json")):
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            marca = dt.datetime.fromisoformat(dados["timestamp"])
            if marca.tzinfo is not None:
                marca = marca.astimezone().replace(tzinfo=None)
        except (OSError, ValueError, KeyError, TypeError):
            # Não apaga log sem timestamp legível: exige inspeção manual.
            continue
        if marca < limite:
            encontrados.append(caminho)
    return encontrados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dias", type=int, default=30)
    parser.add_argument("--confirmar", action="store_true", help="autoriza a exclusão dos arquivos listados")
    args = parser.parse_args()
    if args.dias < 1:
        parser.error("--dias precisa ser maior que zero")
    lista = candidatos(args.dias)
    print(f"{len(lista)} log(s) com mais de {args.dias} dias:")
    for caminho in lista:
        print(" ", caminho)
    if not args.confirmar:
        print("Simulação: nenhum arquivo foi apagado. Use --confirmar para excluir os listados.")
        return
    for caminho in lista:
        caminho.unlink()
    print(f"Removidos: {len(lista)}")


if __name__ == "__main__":
    main()
