# Humano no laço: aprovação da visita técnica

## 1. Onde o grafo pausa e por quê

A visita técnica desloca um técnico, tem custo e não se desfaz sozinha, e o case (§2.1) exige confirmação explícita. A pausa é estrutural: o modelo não tem a ferramenta que agenda. Ele tem propor_visita, que só valida (data entre hoje e amanhã, contrato existente, bairro fora de manutenção, teste de linha feito antes). Quem agenda é o nó agendar, depois do nó aprovacao.

## 2. O que a pessoa vê

O interrupt entrega a ação exata, não um resumo do modelo: ação (agendar_visita_tecnico), contrato, data proposta, consequência ("desloca um técnico até a casa do cliente; tem custo e não é desfeito sozinho"), opções (aprovar, rejeitar, editar), janela de edição e prazo.

## 3. As quatro saídas

| Resposta | O que o código faz |
|---|---|
| aprovar | agenda na data proposta |
| rejeitar | não agenda; o modelo informa o cliente e não insiste (propor de novo é recusado com cliente_ja_recusou_a_visita) |
| editar com data | valida a data (entre hoje e hoje + 14 dias); válida, agenda nela; inválida, vira rejeitar com motivo edicao_invalida |
| expirou | não agenda, encaminha para humano com o motivo aprovacao_expirada |

Qualquer resposta fora dessas quatro vira rejeitar. A edição existe porque a política P04 permite ao cliente escolher uma data posterior à proposta.

## 4. Prazo

O terminal espera a resposta por config.PRAZO_APROVACAO_SEGUNDOS (900 s). Passado o prazo, a execução retoma com expirou. O tempo de espera não conta no teto de tempo do atendimento (segundos_ativos mede só tempo de máquina).

## 5. Aprovação repetida

O agendamento é idempotente: a chave deriva de contrato e data, há índice único no banco, e a segunda aprovação devolve ja_existia=True sem criar outra linha. python -m scripts.demo_idempotencia mostra duas aprovações e uma linha; tests/test_grafo.py repete o caso passando pelo grafo inteiro.

## 6. Como demonstrar

python -m src.agent C004 "Sem internet nenhuma" pergunta no terminal. Para scripts: --decisao aprovar, --decisao rejeitar, --decisao editar --data AAAA-MM-DD, --decisao expirou.
