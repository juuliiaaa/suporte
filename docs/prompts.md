# Prompts

Os prompts vivem em src/prompts/ e são lidos em tempo de execução, não ficam dentro do código.

## suporte_v2.md (prompt do agente)

Mudanças em relação à v1 e por quê:

| Mudança | Motivo |
|---|---|
| O modelo usa propor_visita, não agendar | a confirmação passou a ser estrutural (docs/humano.md); o texto não precisa mais pedir "só agende com sim" |
| Regra de citar o id do trecho entre colchetes | a saída é validada contra os trechos realmente recuperados |
| Se a ferramenta disser suficiente=false, recusar e oferecer humano | o portão do RAG existe, o prompt diz como se comportar diante dele |
| Contrato da sessão informado, o modelo não o pergunta nem o digita | o contrato vem da sessão e substitui qualquer valor digitado pelo modelo |
| Histórico do cliente é contexto, não afirmação do cliente | a memória não pode virar fato sem confirmação por ferramenta |
| Informar o resultado exato da proposta | o modelo só fala de agendamento depois que o nó agendar devolve o resultado |

Técnica: zero-shot com contrato explícito, como na v1. A temperatura é 0.2 fixa em config.TEMPERATURE e vai carimbada em cada log.

## procedural.md (memória procedural)

Quatro regras curtas aprendidas na operação (internet que vai e volta, ONLINE com cliente dizendo que não navega, retestar depois de reiniciar, citar o id). Entra no prompt de toda execução. Mudar esse arquivo é mudar o comportamento do agente, então a mudança passa por revisão como qualquer código.

## Triagem

A triagem é uma regra de código (palavras-chave de cobrança, fatura, cancelamento, pedido de atendente), sem chamada ao modelo: é determinística, de custo zero e testável. Limite: um pedido de cobrança sem nenhuma dessas palavras chega ao agente, e o prompt e a política P02 ainda o desviam para humano.

## Versões

v1 (prompts/suporte_v1.md, Parte 1) e v2 (src/prompts/suporte_v2.md). O arquivo da v1 deve ser movido com git mv para src/prompts/ para preservar o histórico.
