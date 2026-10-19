"""
Imprime nós e arestas do grafo COMPILADO pela mesma função que o sistema usa
(src.grafo.obter_grafo, a mesma que src/agent.py chama). A topologia não
depende do modelo nem do checkpointer; por isso os dois são só de enchimento.
Aresta condicional aparece marcada.

Uso: python conferir_grafo.py
"""
from langgraph.checkpoint.memory import InMemorySaver

from src.grafo import obter_grafo
from src.llm import LLMSimulado

grafo = obter_grafo(LLMSimulado([]), InMemorySaver()).get_graph()
print("NÓS")
for nome in grafo.nodes:
    print(f"  {nome}")
print("ARESTAS")
for e in grafo.edges:
    print(f"  {e.source} -> {e.target}" + ("   [condicional]" if e.conditional else ""))
