# Arquitetura do sistema (Parte 2)

## 1. Visão geral

Um grafo LangGraph com estado tipado (docs/grafo.md) em que o modelo decide só o que o modelo sabe decidir: qual ferramenta chamar e como falar com o cliente. O código decide o resto: o que é permitido, quanto custa continuar, o que vira memória, o que é fonte válida e quando uma pessoa precisa aprovar.

## 2. Mapa de arquivos

| Arquivo | Papel |
|---|---|
| src/grafo.py | nós, arestas e condições |
| src/estado.py | estado tipado e reducers |
| src/guardas.py | taxonomia de términos, orçamento, laço, validação de data |
| src/llm.py | fronteira com o modelo, tentativas, LLMSimulado para testes |
| src/tools.py, src/db.py | ferramentas e SQLite do provedor (idempotência, migração) |
| src/rag.py | BM25, corte, portão de suficiência |
| src/memoria.py | três memórias, escrita por regra, remoção |
| src/schemas.py | contrato de entrada e de saída (Pydantic) |
| src/agent.py | executa o grafo, trata a pausa, grava o log |
| src/prompts/ | suporte_v2.md e procedural.md, carregados em tempo de execução |

## 3. O que mudou em relação à Parte 1

| Antes | Agora |
|---|---|
| laço while no agent.py | grafo com nós e arestas condicionais |
| confirmação por varredura da palavra "sim" | interrupt: o modelo não tem a ferramenta que agenda |
| contrato digitado pelo modelo nas chamadas | contrato da sessão, que substitui o do modelo |
| resposta em texto livre | saída validada com fontes e suficiência |
| sem conhecimento de domínio | RAG sobre manuais e políticas |
| sem memória entre atendimentos | memória semântica, episódica e procedural |
| prompt dentro do código | src/prompts/, com versão |

## 4. Contrato de saída

RespostaAtendimento exige resultado, fontes e suficiente. Regras aplicadas em código no nó finalizar: suficiente=true exige ao menos uma fonte (ferramenta que rodou sem erro, ou trecho do corpus citado e de fato recuperado naquela execução); uma citação de id que a ferramenta não devolveu é separada em citacoes_invalidas e não vira fonte; se o modelo consultou o manual, o portão barrou e não há outra fonte, a resposta do modelo é substituída por uma recusa fixa, com suficiente=false e encaminhar_humano=true. A recusa faz parte do contrato, não é exceção.

## 5. Fluxo de dados de um atendimento com visita

mensagem e contrato entram; a triagem libera; o modelo chama testar_linha e vê falha física; chama obter_data_atual e propor_visita; o grafo pausa; a pessoa responde; agendar executa e devolve o resultado como mensagem de ferramenta; o modelo escreve a resposta com o que de fato aconteceu; finalizar valida; registrar_memoria grava; o log JSON é escrito com commit, modelo, temperatura, trajetória e saída.

## 6. Segurança

.env nunca é versionado (.gitignore). A chave do Groq fica só no .env. Dados pessoais no log são só o contrato e a mensagem do cliente; a remoção por titular está em docs/memoria.md §4. Detalhes de retenção e escopo de chave estão no model-card.
