"""
Remove de logs/ os registros de atendimento mais antigos que o prazo de
retenção local.

Por que 30 dias: exercicios/model-card.md §6.2 lista o que cada log em
logs/caso_<contrato>.json pode conter (contrato, bairro e o texto da
mensagem do cliente). Os dados são simulados, mas não havia, até esta
versão, nenhum prazo declarado para esses arquivos — a lacuna L07. O
prazo escolhido aqui acompanha o que o Groq, o provedor do modelo, já faz
sozinho com os próprios logs de confiabilidade e abuso (até 30 dias,
ver docs/modelos.md §5): não faz sentido este repositório guardar por
mais tempo um dado que o próprio provedor do modelo já descarta.

Isto não é um job agendado — é um comando que quem mantém o repositório
roda manualmente ou a partir de uma rotina (cron, GitHub Action) de fora
deste projeto.

Uso:
    python3 -m scripts.limpar_logs_antigos             # remove o que venceu
    python3 -m scripts.limpar_logs_antigos --simular    # só lista, não apaga
    python3 -m scripts.limpar_logs_antigos --prazo 15   # outro prazo em dias
"""
import argparse
import datetime
import json
import os

PRAZO_DIAS_PADRAO = 30
PASTA_LOGS = os.path.join(os.path.dirname(__file__), "..", "logs")


def logs_vencidos(pasta: str = PASTA_LOGS, prazo_dias: int = PRAZO_DIAS_PADRAO) -> list:
    """Retorna o caminho dos logs mais antigos que o prazo. A data usada é
    o campo "timestamp" gravado pelo próprio src/agent.py; se o arquivo
    não tiver esse campo (log corrompido ou de formato antigo), cai para
    a data de modificação do arquivo no disco."""
    limite = datetime.datetime.now() - datetime.timedelta(days=prazo_dias)
    vencidos = []
    if not os.path.isdir(pasta):
        return vencidos
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".json"):
            continue
        caminho = os.path.join(pasta, nome)
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                registro = json.load(arquivo)
            timestamp = datetime.datetime.fromisoformat(registro["timestamp"])
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(caminho))
        if timestamp < limite:
            vencidos.append(caminho)
    return vencidos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--simular", action="store_true",
        help="lista os logs que seriam removidos, sem apagar nenhum",
    )
    parser.add_argument(
        "--prazo", type=int, default=PRAZO_DIAS_PADRAO,
        help=f"prazo de retenção em dias (padrão: {PRAZO_DIAS_PADRAO})",
    )
    args = parser.parse_args()

    vencidos = logs_vencidos(prazo_dias=args.prazo)
    if not vencidos:
        print(f"Nenhum log passou do prazo de {args.prazo} dias.")
        return

    for caminho in vencidos:
        if args.simular:
            print(f"removeria: {caminho}")
        else:
            os.remove(caminho)
            print(f"removido: {caminho}")


if __name__ == "__main__":
    main()
