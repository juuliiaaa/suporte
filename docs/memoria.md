# Memória: o que foi implementado do projeto de memória

Implementação em src/memoria.py. O desenho está em Memória — Agente de Suporte Técnico Doméstico (Exercício 8).

## 1. Três memórias, cada uma na estrutura que o acesso pede

| Memória | Estrutura | Como é lida | Onde |
|---|---|---|---|
| Semântica | chave-valor por contrato | por chave exata (ultimo_sinal_dbm) | tabela semantica |
| Episódica | um resumo por atendimento | similaridade lexical (BM25) dentro do contrato | tabela episodica |
| Procedural | texto curado | sempre no prompt | src/prompts/procedural.md |

## 2. Quem escreve, e o quê

Só o código escreve, no nó registrar_memoria, no fim do atendimento. O modelo não decide o que vira memória. O que entra vem do que as ferramentas retornaram: um episódio (sintoma, causa, ação, resultado) e o último sinal medido. O que o cliente apenas afirmou não vira fato (tests/test_memoria.py, teste de escrita extraída). Atendimento com contrato inexistente não grava nada.

## 3. Idempotência

A chave de cada registro deriva do conteúdo (contrato, chave, valor, data). Gravar duas vezes o mesmo fato devolve ja_existia=True e não cria outra linha.

## 4. As três causas de esquecimento

- Contradição: dois valores para a mesma chave. Vence o de vigente_desde mais recente, o perdedor vai para a tabela descartes com o motivo. Um fato antigo que chega depois não vence.
- Decaimento: episódio com mais de 180 dias é rebaixado (ativo=0), não apagado. Roda no início de cada atendimento.
- Remoção: remover_titular apaga o contrato da semântica, dos descartes, da episódica, dos checkpoints do LangGraph (thread_id começa por contrato:) e dos logs.

## 5. Verificação da remoção por outro programa

scripts/varrer_contrato.py não usa o código de remoção. Percorre o projeto procurando o contrato em qualquer coluna de qualquer banco .db e em .json, .md e .txt. O resultado esperado depois da remoção é zero ocorrências, com a exceção declarada de dados/provedor.db, que é a fonte de verdade do provedor e não é memória do agente.

## 6. Orçamento de contexto

O bloco de memória entra no prompt com teto de 500 tokens (config.ORCAMENTO_TOKENS). Se estourar, o episódio mais antigo sai primeiro. O bloco é marcado como "não confirmado pelo cliente agora", e o prompt manda confirmar com as ferramentas.

## 7. Limites

Estimativa de tokens por caracteres (4 por token), sem tokenizador. Backups externos não são alcançados pela remoção. A recuperação episódica é lexical: um relato com outras palavras cai para o episódio mais recente do mesmo contrato.
