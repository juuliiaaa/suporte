"""Executa os dez cenários com o modelo configurado, em bancos temporários.

O estado local do projeto (provedor.db, memoria.db e checkpoints.db) não é apagado.
Os novos logs recebem sufixo temporal para preservar as execuções anteriores.
"""
import argparse
import datetime
import os
import tempfile
import time

from src import config, db
from src.agent import decisor_fixo, executar_atendimento

HOJE = datetime.date.today()
EM_3_DIAS = (HOJE + datetime.timedelta(days=3)).isoformat()

CASOS = {
    "C001": ("caso_C001_feliz", "C001", "A luz do modem está piscando vermelha e a internet caiu.", ("rejeitar", None)),
    "C002": ("caso_C002_divergencia", "C002", "Minha internet caiu, nada navega aqui em casa.", ("rejeitar", None)),
    "C999": ("caso_C999_inexistente", "C999", "Minha internet caiu.", ("rejeitar", None)),
    "C005": ("caso_C005_nao_agenda", "C005", "Estou sem internet, quero que mandem um técnico hoje.", ("aprovar", None)),
    "FORA": ("caso_fora_do_corpus", "C001", "Como faço para abrir portas no roteador para jogar online?", ("rejeitar", None)),
    "C004": ("caso_C004_pausa_edita", "C004", "Sem internet nenhuma, a luz está vermelha.", ("editar", EM_3_DIAS)),
    "C004B": ("caso_C004_aprovacao_repetida", "C004", "Sem internet nenhuma, a luz está vermelha.", ("editar", EM_3_DIAS)),
    "INC": ("caso_entrada_incompleta", "C001", "não funciona", ("rejeitar", None)),
    "AMB": ("caso_entrada_ambigua", "C001", "A internet está ruim hoje, não sei se é o wifi ou a internet mesmo.", ("rejeitar", None)),
    "ESC": ("caso_fora_do_escopo", "C001", "Quero cancelar meu plano e pedir um desconto.", ("rejeitar", None)),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("casos", nargs="*", choices=sorted(CASOS))
    p.add_argument("--pausa", type=int, default=0,
                   help="segundos de espera entre cenários (evita o limite por minuto do provedor)")
    a = p.parse_args()

    # Isola os bancos para que a demonstração não apague nem altere dados locais.
    originais = (db.DB_PATH, config.CAMINHO_MEMORIA, config.CAMINHO_CHECKPOINTS)
    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory(prefix="agente_casos_") as pasta:
        db.DB_PATH = os.path.join(pasta, "provedor.db")
        config.CAMINHO_MEMORIA = os.path.join(pasta, "memoria.db")
        config.CAMINHO_CHECKPOINTS = os.path.join(pasta, "checkpoints.db")
        try:
            db.inicializar()
            for i, chave in enumerate(a.casos or CASOS):
                if i and a.pausa:
                    print(f"(aguardando {a.pausa}s)")
                    time.sleep(a.pausa)
                rotulo_base, contrato, mensagem, (decisao, data) = CASOS[chave]
                rotulo = f"exec_{carimbo}_{rotulo_base}"
                print(f"\n### {rotulo_base}")
                r = executar_atendimento(
                    contrato, mensagem,
                    decisor=decisor_fixo(decisao, data),
                    rotulo=rotulo,
                )
                s = r["saida"]
                print(f"parou por: {r['motivo_parada']} | suficiente={s['suficiente']} | fontes={[f['id'] for f in s['fontes']]}")
                print(f"resposta: {s['resultado']}")
                print(f"log: {r['arquivo_log']}")
        finally:
            db.DB_PATH, config.CAMINHO_MEMORIA, config.CAMINHO_CHECKPOINTS = originais


if __name__ == "__main__":
    main()
