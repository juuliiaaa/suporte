"""
Imprime nós e arestas do grafo COMPILADO (o mesmo que src/agent.py executa),
para conferir contra docs/grafo.md. Aresta condicional aparece marcada.

Uso: python conferir_grafo.py
"""
from langgraph.checkpoint.memory import InMemorySaver

from src.grafo import construir_grafo
from src.llm import LLMSimulado

grafo = construir_grafo(LLMSimulado([]), InMemorySaver()).get_graph()
print("NÓS")
for nome in grafo.nodes:
    print(f"  {nome}")
print("ARESTAS")
for e in grafo.edges:
    print(f"  {e.source} -> {e.target}" + ("   [condicional]" if e.conditional else ""))
