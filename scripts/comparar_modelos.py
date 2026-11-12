"""Roda os 10 casos rotulados em cada modelo candidato e compara com o
verificador (docs/case.md §6 e §7). Precisa do .env preenchido.

Os candidatos são os modelos liberados na conta gratuita da Groq usada pelo
grupo (docs/modelos.md §3). Cada modelo grava seus logs em
logs_modelos/<modelo>/ e o resultado vai para docs/comparacao_modelos.md.

Uso:
  python -m scripts.comparar_modelos
  python -m scripts.comparar_modelos --modelos qwen/qwen3.8-27b openai/gpt-oss-120b
"""
import argparse
import glob
import json
import os
import subprocess
import sys

from src import config
from scripts import verificar_casos as v

MODELOS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]

# US$ por 1M tokens (entrada, saída), Groq, consultados em nov/2026 (docs/fontes.md).
PRECOS = {
    "qwen/qwen3.8-27b": (0.80, 4.00),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
}
PARTE_ENTRADA = 0.8  # o log guarda só o total de tokens; 80% entrada e 20% saída, como na estimativa do case
CHAMADOS_MES = 5400


def custo_por_execucao(modelo: str, tokens: float):
    if modelo not in PRECOS or not tokens:
        return None
    entrada, saida = PRECOS[modelo]
    return (tokens * PARTE_ENTRADA * entrada + tokens * (1 - PARTE_ENTRADA) * saida) / 1e6


def rodar(modelo: str, base: str) -> str:
    pasta = os.path.join(base, modelo.replace("/", "_"))
    os.makedirs(pasta, exist_ok=True)
    for antigo in glob.glob(os.path.join(pasta, "*.json")):
        os.remove(antigo)
    env = dict(os.environ, LLM_MODEL=modelo, PASTA_LOGS=pasta)
    print(f"\n=== {modelo}: rodando os 10 casos ===", flush=True)
    r = subprocess.run([sys.executable, "-m", "scripts.rodar_casos", "--reset"], env=env, cwd=config.RAIZ)
    if r.returncode != 0:
        print(f"{modelo}: rodar_casos terminou com código {r.returncode}", flush=True)
    return pasta


def fatais(pasta: str) -> int:
    n = 0
    for caminho in glob.glob(os.path.join(pasta, "*.json")):
        with open(caminho, encoding="utf-8") as f:
            if json.load(f).get("motivo_parada") == "erro_fatal_llm":
                n += 1
    return n


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modelos", nargs="*", default=MODELOS)
    p.add_argument("--base", default=os.path.join(config.RAIZ, "logs_modelos"))
    a = p.parse_args()

    resultados = {}
    for modelo in a.modelos:
        pasta = rodar(modelo, a.base)
        resultados[modelo] = (v.avaliar(pasta), fatais(pasta))

    destino = os.path.join(config.RAIZ, "docs", "comparacao_modelos.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("# Comparação dos modelos nos 10 casos rotulados\n\n")
        f.write("Gerado por `python -m scripts.comparar_modelos`. Cada modelo roda os mesmos 10 casos "
                "(`dados/casos_rotulados.json`) e o verificador compara a ação esperada com a ação lida do log. "
                "Os logs ficam em `logs_modelos/<modelo>/`.\n\n")
        f.write("| Modelo | Acertos | Visita em bairro em manutenção | Execuções com erro fatal do modelo "
                "| Tokens médios por execução | Custo por execução (US$) | Custo por mês, 5.400 chamados (US$) | Critério |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for modelo, (res, nfatal) in resultados.items():
            c = custo_por_execucao(modelo, res["tokens_medios"])
            viol = ", ".join(res["violacoes"]) or "nenhuma"
            f.write(f"| `{modelo}` | {res['acertos']} de {res['total']} | {viol} | {nfatal} | "
                    f"{res['tokens_medios']} | {'%.4f' % c if c else 'n/d'} | "
                    f"{'%.2f' % (c * CHAMADOS_MES) if c else 'n/d'} | "
                    f"{'atendido' if res['criterio_ok'] else 'não atendido'} |\n")
        f.write("\nCusto: tokens médios dos logs, 80% a preço de entrada e 20% a preço de saída "
                "(o log guarda só o total), com os preços de `docs/modelos.md` §1.\n\n")
        for modelo, (res, _) in resultados.items():
            f.write(f"## {modelo}\n\n{v.tabela_md(res)}\n\n")
    print(f"\n{destino} gerado")


if __name__ == "__main__":
    main()
