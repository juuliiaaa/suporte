"""Conversa interativa com o agente no terminal, para demonstração.

  python -m scripts.conversar            # começa no contrato C001
  python -m scripts.conversar C004

Cada mensagem digitada é um atendimento (o desenho do sistema é uma mensagem
por atendimento, com a memória de longo prazo ligando um ao seguinte). Quando
o agente propõe uma visita, o terminal pausa e pede a sua decisão: aprovar,
rejeitar ou editar AAAA-MM-DD.

Comandos: /contrato C004   /canal 5511900000001   /suspender   /reativar   /sair
"""
import os
import sys

from src import config, db, seguranca
from src.agent import decisor_terminal, executar_atendimento


def main():
    contrato = sys.argv[1] if len(sys.argv) > 1 else "C001"
    canal = db.canal_simulado(contrato)
    print(f"Contrato {contrato}, canal {canal}. Digite o problema, ou /sair.")
    while True:
        try:
            texto = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto:
            continue
        if texto == "/sair":
            break
        if texto.startswith("/contrato "):
            contrato = texto.split()[1]
            canal = db.canal_simulado(contrato)
            print(f"(contrato {contrato}, canal {canal})")
            continue
        if texto.startswith("/canal "):
            canal = texto.split()[1]
            print(f"(canal {canal}; o titular de {contrato} usa {db.canal_simulado(contrato)})")
            continue
        if texto == "/suspender":
            open(config.CAMINHO_SUSPENSAO, "w").close()
            print("(agente suspenso)")
            continue
        if texto == "/reativar":
            if os.path.exists(config.CAMINHO_SUSPENSAO):
                os.remove(config.CAMINHO_SUSPENSAO)
            print(f"(suspenso: {seguranca.agente_suspenso()})")
            continue
        r = executar_atendimento(contrato, texto, decisor=decisor_terminal, canal=canal)
        usadas = [t["nome"] for t in r["trajetoria"] if t.get("tipo") == "ferramenta"]
        print(f"\nAgente: {r['saida']['resultado']}")
        print(f"[ferramentas: {usadas or 'nenhuma'} | término: {r['motivo_parada']}]")


if __name__ == "__main__":
    main()
