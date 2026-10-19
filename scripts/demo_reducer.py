"""
Demonstra a regra de junção do estado (enunciado §3.1): dois nós em paralelo
escrevendo o mesmo campo.
  com reducer (operator.add): as duas escritas são preservadas
  sem reducer: o LangGraph recusa (InvalidUpdateError), não perde dado em silêncio

Uso: python -m scripts.demo_reducer
"""
import operator
from typing import Annotated, List, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph


class ComReducer(TypedDict):
    achados: Annotated[List[str], operator.add]


class SemReducer(TypedDict):
    achados: List[str]


def montar(estado):
    g = StateGraph(estado)
    g.add_node("busca_manual", lambda e: {"achados": ["trecho do manual"]})
    g.add_node("busca_bairro", lambda e: {"achados": ["status do bairro"]})
    g.add_edge(START, "busca_manual")
    g.add_edge(START, "busca_bairro")
    g.add_edge("busca_manual", END)
    g.add_edge("busca_bairro", END)
    return g.compile()


print("COM reducer:", montar(ComReducer).invoke({"achados": []}))
try:
    montar(SemReducer).invoke({"achados": []})
except InvalidUpdateError as erro:
    print("SEM reducer: InvalidUpdateError ->", str(erro).splitlines()[0])
