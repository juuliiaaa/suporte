"""
Estado do grafo (enunciado §3). Cada campo tem um dono e uma regra de junção.

Campos que ACUMULAM (reducer operator.add): quem escreve só entrega o que é
novo e o LangGraph concatena/soma. São os que mais de um nó podem tocar.
Campos que SUBSTITUEM (sem reducer): cada um tem um único escritor, então
a substituição é a regra certa. Se dois nós em paralelo escrevessem um campo
sem reducer, o LangGraph levanta InvalidUpdateError (scripts/demo_reducer.py).
"""
import operator
from typing import Annotated, List, Optional, TypedDict


class EstadoAtendimento(TypedDict, total=False):
    # entrada: escrita uma vez, nunca pelo modelo
    thread_id: str
    contrato: str
    mensagem: str
    hoje: str

    # acumulam
    mensagens: Annotated[List[dict], operator.add]     # conversa no formato do modelo, sem o system
    trajetoria: Annotated[List[dict], operator.add]    # o que aconteceu, para log e memória
    tokens: Annotated[int, operator.add]               # orçamento de tokens
    segundos_ativos: Annotated[float, operator.add]    # tempo de máquina, sem a espera humana

    # substituem (um escritor cada)
    memoria_contexto: str       # carregar_memoria
    rota: str                   # triagem
    voltas: int                 # agente
    passos_ferramenta: int      # ferramentas
    visita_proposta: Optional[dict]   # ferramentas escreve, agendar limpa
    decisao_humana: Optional[dict]    # aprovacao
    motivo_parada: Optional[str]      # quem encerra
    resposta_texto: Optional[str]     # agente ou encaminhar_humano
    saida: Optional[dict]             # finalizar
