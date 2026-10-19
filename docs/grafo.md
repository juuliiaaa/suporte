# Grafo de execução

Conferido contra o grafo compilado com python conferir_grafo.py.

## 1. Nós

| Nó | O que faz | Escreve |
|---|---|---|
| entrada | fixa a data de hoje, zera contadores, grava a mensagem | hoje, voltas, passos_ferramenta, mensagens |
| carregar_memoria | decaimento e bloco de memória do contrato | memoria_contexto |
| triagem | regra de palavras-chave: cobrança, fatura, cancelamento ou pedido de atendente vai para humano | rota, motivo_parada |
| agente | uma chamada ao modelo por visita, depois de checar o orçamento | mensagens, voltas, tokens |
| ferramentas | executa as chamadas do modelo com guardas | trajetoria, passos_ferramenta, visita_proposta |
| aprovacao | pausa com interrupt e espera uma pessoa | decisao_humana |
| agendar | único lugar que agenda; só com decisão aprovar ou editar | trajetoria, visita_proposta |
| encaminhar_humano | texto fixo de transbordo | resposta_texto |
| finalizar | monta e valida a saída (Pydantic) | saida |
| registrar_memoria | grava episódio e fato | trajetoria |

## 2. Arestas

Fixas: START para entrada; carregar_memoria para triagem; aprovacao para agendar; encaminhar_humano para finalizar; finalizar para registrar_memoria; registrar_memoria para END.

Condicionais: entrada (mensagem vazia vai para humano); triagem (suporte para agente, humano para encaminhar_humano); agente (resposta final para finalizar, limite atingido para encaminhar_humano, senão ferramentas); ferramentas (proposta de visita para aprovacao, limite ou laço para encaminhar_humano, senão agente); agendar (aprovação expirada para encaminhar_humano, senão agente, que escreve a mensagem final).

## 3. Estado e regras de junção

Campos que acumulam, com reducer operator.add: mensagens, trajetoria, tokens, segundos_ativos. Campos que substituem, cada um com um único escritor: rota, voltas, passos_ferramenta, visita_proposta, decisao_humana, motivo_parada, resposta_texto, saida, memoria_contexto. Entrada: thread_id, contrato, mensagem, hoje.

python -m scripts.demo_reducer mostra a regra: dois nós em paralelo escrevendo o mesmo campo com reducer preservam as duas escritas; sem reducer o LangGraph levanta InvalidUpdateError ("Can receive only one value per step") em vez de perder uma delas em silêncio. O grafo atual é sequencial, então a demonstração é de um grafo mínimo à parte, que mostra por que cada campo tem a regra que tem.

## 4. Decisão que o framework esconderia: o limite de passos

O padrão do LangGraph para recursion_limit é 25 e o valor aqui também é 25, mas está declarado em config.RECURSION_LIMIT e passado em cada execução, porque coincidir com o padrão não é o mesmo que ter decidido. Cada nó executado gasta um passo. Com o limite de 6 voltas, o caminho mais longo é: 3 nós iniciais (entrada, carregar_memoria, triagem), 6 visitas ao agente, até 6 às ferramentas, aprovacao, agendar, finalizar e registrar_memoria, ou seja, cerca de 19 passos. O 25 deixa folga sobre esse máximo e só estoura se um limite do orçamento falhar. O estouro não derruba o programa: vira o motivo de término recursion_limit, com encaminhamento ao humano (tests/test_grafo.py, teste do recursion_limit, com o limite reduzido para 6).

## 5. Taxonomia de términos

| Motivo | Condição | Encaminha humano |
|---|---|---|
| resposta_final | o modelo respondeu sem pedir ferramenta | não |
| encaminhado_humano | triagem ou entrada vazia | sim |
| limite_de_voltas | 6 chamadas ao modelo | sim |
| limite_de_ferramentas | 8 chamadas de ferramenta | sim |
| laco_detectado | mesma ferramenta e mesmos argumentos 3 vezes sem escrita no meio | sim |
| tempo_esgotado | 120 s de tempo de máquina (a espera humana não conta) | sim |
| tokens_esgotados | 12000 tokens acumulados | sim |
| aprovacao_expirada | sem resposta no prazo | sim |
| erro_fatal_llm | erro que repetir não resolve | sim |
| recursion_limit | mais de 25 passos | sim |

## 6. Erros: recuperáveis e fatais

Limite de taxa, falha de conexão e timeout do modelo são recuperáveis: até 3 tentativas com espera crescente. Qualquer outro erro (chave inválida, requisição inválida) é fatal e vira erro_fatal_llm. Erro de ferramenta é dado: volta ao modelo como resultado com o campo erro. Chamada de ferramenta inexistente, argumento inválido e contrato sobrescrito pelo modelo (o contrato vem da sessão e substitui o que o modelo digitar, registrado como contrato_sobrescrito) também viram dado.

## 7. Checkpoints

Cada atendimento tem thread_id contrato:id. Os checkpoints ficam em dados/checkpoints.db (SqliteSaver), e a pausa de aprovação sobrevive a uma reinicialização do processo. A remoção de um titular apaga os checkpoints do contrato.
