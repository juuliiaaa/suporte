# RAG: recuperação de conhecimento

## 1. Formas de recuperar e qual pergunta usa qual

O agente tem duas formas de recuperar, e a escolha é decidida pela natureza da pergunta, não pelo gosto.

| Forma | Onde está | Para que serve |
|---|---|---|
| Consulta estruturada | testar_linha, conferir_queda_bairro (SQLite) | estado atual: sinal da linha, bairro em manutenção |
| Busca textual (BM25) | consultar_base_conhecimento (src/rag.py) | regras, limiares, sintomas, políticas |

As 12 perguntas de dados/perguntas_rag.json estão classificadas por forma (termo, assunto, registro). Duas delas (Q11 e Q12) são perguntas de registro: a resposta é o estado do cliente agora, e nenhum manual a contém. A descrição da ferramenta diz isso ao modelo. Três perguntas dependem de uma exceção do manual (Q03, Q06 e Q09), e uma (Q10) não tem resposta no corpus de propósito.

## 2. Decisão revisada: BM25 em vez de embeddings

A base-de-conhecimento-v1 previa embeddings com numpy. Esta versão usa BM25 implementado no projeto, sem dependência. Motivos: o corpus tem dezenas de trechos; as perguntas usam o vocabulário do domínio (dBm, luz vermelha, bairro em manutenção); e não há API de embedding gratuita e estável, o que a restrição do grupo (nada pago nem gratuito por tempo limitado) exclui. O custo está medido na seção 4: busca lexical não acha paráfrase sem palavra em comum, e o stemmer é só remoção de plural.

## 3. Corte e metadados

O corte segue a estrutura do documento: cada item "## ID — Título" vira um trecho. O trecho herda o título do documento no início do texto, porque uma frase como "no máximo 3 vezes" não faz sentido sozinha. Metadados no cabeçalho de cada documento: agente_aplicavel (cliente), vigente (true ou false), tipo, mantido_por. O filtro de vigência e de agente é aplicado em código, em construir_indice, e não pedido ao modelo.

## 4. Medição (python -m scripts.medir_rag --k 1 --k 3)

| Medida | Corpus vigente | Com o documento revogado |
|---|---|---|
| acerto@1 (9 perguntas com resposta no corpus) | 9/9 | 8/9 |
| acerto@3 | 9/9 | 9/9 |
| portão correto (corpus ou nenhuma) | 10/10 | 10/10 |

O portão de suficiência exige que o melhor trecho cubra ao menos 50% dos termos da pergunta (RAG_COBERTURA_MINIMA). A pergunta Q10 (preço do plano) tem cobertura 0,25 e é barrada: o modelo recebe suficiente=false e nenhum trecho para citar. Limite conhecido: as perguntas de registro (Q11, Q12) passam no portão porque compartilham palavras com o corpus; quem as desvia para as ferramentas de estado é a descrição da ferramenta, não o portão.

## 5. Experimento do documento revogado

O documento 04_manual_sintomas_v0 foi revogado em 2026-06-01 e contradiz o corpus atual em três números (limiar de -25 dBm, 5 reinícios, 3 dias úteis). Com ele no índice, a pergunta sobre prazo máximo de visita (Q07) passa a trazer V02 e V03 antes de P04, e a Q02 traz V01 em segundo. O sistema não descobre sozinho que um documento envelheceu: a correção é a curadoria (vigente: false), aplicada em código. tests/test_rag.py reproduz o experimento.

## 6. Recuperação dentro do agente

A ferramenta é chamada pelo modelo, devolve no máximo 3 trechos com id, e a saída final só aceita citações de ids que a ferramenta devolveu naquela execução (docs/arquitetura.md §4). O número de recuperações por execução aparece na trajetória do log (entradas consultar_base_conhecimento). Uma consulta com suficiente=false é registrada e conta como consulta inútil.
