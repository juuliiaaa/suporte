"""
Demonstração da remoção por titular (docs/memoria.md §4), sem modelo e sem
tocar em dados/: tudo acontece numa pasta temporária.

Passos, na ordem que o enunciado pede:
  1. gravar: dois atendimentos do contrato C001 (modelo simulado);
  2. verificar que o comportamento mudou: o prompt do segundo atendimento
     carrega o histórico do cliente;
  3. varrer antes de remover (o contrato aparece onde foi gravado);
  4. remover;
  5. verificar que voltou: a memória devolve vazio;
  6. varrer de novo (zero ocorrências).
Também mede o volume de escrita de um atendimento.

Uso: python -m scripts.demo_remocao
"""
import os
import sqlite3
import tempfile

from src import config, db, memoria, tools
from src.agent import decisor_fixo, executar_atendimento
from src.llm import LLMSimulado, chamada, texto

CONTRATO = "C001"


def atendimento(roteiro, rotulo):
    return executar_atendimento(CONTRATO, "A luz do modem está piscando vermelha e a internet caiu.",
                                llm=LLMSimulado(roteiro), decisor=decisor_fixo("rejeitar"), rotulo=rotulo)


def volume():
    conn = sqlite3.connect(config.CAMINHO_MEMORIA)
    saida = {}
    for tabela in ("semantica", "episodica"):
        linhas = conn.execute(f"SELECT * FROM {tabela}").fetchall()
        saida[tabela] = (len(linhas), sum(len(str(c)) for l in linhas for c in l))
    conn.close()
    return saida


def main():
    from scripts.varrer_contrato import varrer

    with tempfile.TemporaryDirectory() as pasta:
        os.makedirs(os.path.join(pasta, "dados"))
        config.RAIZ = pasta
        db.DB_PATH = os.path.join(pasta, "dados", "provedor.db")
        config.CAMINHO_MEMORIA = os.path.join(pasta, "dados", "memoria.db")
        config.CAMINHO_CHECKPOINTS = os.path.join(pasta, "dados", "checkpoints.db")
        config.PASTA_LOGS = os.path.join(pasta, "logs")
        db.inicializar()
        hoje = tools._hoje().isoformat()

        print("1. gravar")
        atendimento([chamada("testar_linha"), chamada("reiniciar_conexao"), chamada("testar_linha"),
                     texto("Reiniciei e a linha voltou.")], "demo_1")
        v = volume()
        print(f"   volume de escrita de um atendimento: semantica {v['semantica'][0]} registro(s), "
              f"{v['semantica'][1]} caracteres; episodica {v['episodica'][0]} registro(s), {v['episodica'][1]} caracteres")

        print("2. o comportamento mudou?")
        vistos = []

        def espiar(mensagens):
            vistos.append(mensagens[0]["content"])
            return texto("ok")
        atendimento([espiar], "demo_2")
        print("   prompt do 2o atendimento traz o histórico do cliente:", "Histórico deste cliente" in vistos[0])

        print("3. varrer antes de remover")
        antes = varrer(CONTRATO)
        print(f"   {len(antes)} ocorrência(s)")
        for a in antes:
            caminho, sep, resto = a.partition(": ")
            print("    ", os.path.relpath(caminho, pasta).replace(os.sep, "/") + sep + resto)

        print("4. remover")
        print("  ", memoria.remover_titular(CONTRATO))

        print("5. o comportamento voltou?")
        print("   memória devolve vazio:", memoria.montar_contexto(CONTRATO, "luz vermelha", hoje) == "")

        print("6. varrer depois de remover")
        depois = varrer(CONTRATO)
        print(f"   {len(depois)} ocorrência(s)")
        for a in depois:
            print("    ", a)


if __name__ == "__main__":
    main()
