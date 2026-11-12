# Como Funciona o Robô de Suporte Técnico

## 1. O que entra

- **De onde vêm as mensagens:**
  - A maioria vem do WhatsApp do próprio cliente reclamando de um problema.
  - Uma pequena parte vem de um aviso automático do sistema quando ele percebe sozinho que a internet caiu em um bairro inteiro.
- **O que as pessoas costumam pedir:**
  - 70% — problemas simples de internet ("caiu", "está lenta", "luz vermelha no aparelho").
  - 15% — pedidos de ajuda para configurar algo (ex.: trocar a senha do Wi-Fi).
  - 10% — assuntos que não são do suporte técnico (cobrança, cancelamento, pedir desconto).
  - 5% — avisos automáticos de queda geral no bairro.

Como chegam coisas muito diferentes, o robô precisa separar as mensagens no início para não tentar resolver um problema de cobrança usando um teste de internet.

## 2. As regras do robô

**O papel do robô (em uma frase):** "Você é um assistente que testa a internet do cliente e resolve coisas simples à distância (reiniciar a conexão, trocar a senha do Wi-Fi). Se o problema for físico no cabo ou na rede, você explica o que houve e ajuda a agendar um técnico. Você nunca resolve dúvidas sobre dinheiro/faturas e não cobra nada do cliente sem a aprovação dele."

**As ferramentas do robô:**

- **Testar a linha:** não altera nada, só lê a situação atual da internet.
- **Conferir queda no bairro:** checa se mais pessoas perto estão sem internet.
- **Reiniciar a conexão:** tenta arrumar a internet à distância (pode ser feito quantas vezes precisar).
- **Mudar a senha do Wi-Fi:** altera o Wi-Fi do cliente.
- **Agendar visita do técnico:** só faz se o cliente confirmar, pois gera custo de deslocamento.
- **Abrir pedido de desconto:** o robô não dá o desconto; ele só cria um pedido para um funcionário humano analisar.

**A memória do robô (o que ele precisa guardar durante a conversa):**

- O número do contrato do cliente.
- O resultado dos últimos testes.
- Se já tentou reiniciar a internet.
- Se o bairro todo está sem sinal.
- Se está esperando a resposta do cliente para agendar a visita.

**Limites de segurança:**

- No máximo 3 testes de linha por atendimento (para não entrar em loop infinito).
- No máximo 6 mensagens trocadas. Se não resolver até aí, passa para um atendente humano.
- No máximo 5 minutos de tempo total de atendimento.

## 3. O passo a passo da solução

```
1. MENSAGEM DO CLIENTE
   O cliente escreve no WhatsApp ou o sistema avisa de uma queda.
        ↓
2. SEPARAÇÃO
   O robô lê e decide o caminho:
     • Técnico? Vai para o passo 3.
     • Configuração simples? Troca a senha direto.
     • Cobrança/Outros? Manda para um atendente humano.
     • Queda no bairro? Avisa direto no passo 6 sem testar um por um.
        ↓
3. TESTE E DIAGNÓSTICO
   Faz testes na linha e descobre o problema (máximo 3 testes).
        ↓
4. AÇÃO À DISTÂNCIA
   Tenta resolver sozinho (ex.: reinicia o sinal).
        ↓
5. VERIFICAÇÃO
   Checa se a internet voltou:
     • Voltou? Vai para o encerramento (passo 7/8).
     • Não voltou? Decide se precisa de técnico ou de atendente.
        ↓
6. AGENDAMENTO
   Se a internet não voltou, sugere datas e horários para o técnico ir até
   a casa (só com o "SIM" do cliente).
        ↓
7. REGISTRO
   Salva tudo o que aconteceu no sistema.
        ↓
8. RESPOSTA FINAL
   Responde ao cliente no WhatsApp de forma simples.
```

**Exemplo de conversa (o que o cliente vê no final):**

> "Pronto! O sinal voltou ao normal e seu aparelho já conectou. Pode tentar usar a internet agora?"

## Por que o sistema foi feito desse jeito?

1. **Separação no início:** as pessoas escrevem de jeitos muito diferentes. Um filtro inteligente entende a intenção do cliente em vez de só procurar palavras soltas.
2. **Testes inteligentes:** o robô decide qual teste fazer com base no resultado do teste anterior (se a luz está apagada, não adianta tentar mudar a senha do Wi-Fi).
3. **Checagem dupla:** depois de reiniciar o aparelho, o robô confere se a internet realmente voltou antes de dizer ao cliente que está tudo resolvido.
4. **Proteção contra custos:** agendar técnico e pedir desconto custam dinheiro para a empresa. Por isso, o robô nunca faz isso sozinho sem a autorização do cliente ou sem passar para um humano.

---

# Arquitetura — Agente de Apoio ao Técnico de Campo

## 1. Entrada

- **Quem dispara:** o técnico de rua (via WhatsApp/Telegram do trabalho ou app interno) ao chegar no endereço do cliente ou durante o atendimento.
- **O que envia:**
  - Áudios e textos rápidos ("Cheguei na casa do cliente", "A luz PON da ONT tá piscando rápido").
  - Fotos e imagens (foto do conector óptico, foto dos LEDs do modem, foto do medidor de sinal/Power Meter).
  - Comandos curtos ("muda a Vlan", "provisiona a ONT nova").

## 2. System prompt e ferramentas

**Papel do agente (em uma frase):** "Você é o assistente técnico de campo: apoia o técnico na rua rodando testes avançados de fibra/sinal, executando provisionamento de equipamentos e validando o serviço antes do encerramento da visita."

**Ferramentas do agente do técnico:**

- `consultar_historico_atendimento(id_chamado)`: lê o que o robô do cliente testou antes da visita.
- `medir_sinal_optico_porta(id_caixa)`: checa se a caixa da rua (CTO) tem perda de sinal antes de mexer na casa do cliente.
- `provisionar_novo_modem(mac_antigo, mac_novo)`: troca o equipamento no sistema sem o técnico precisar ligar para a central/NOC.
- `validar_qualidade_pos_instalacao()`: roda uma bateria de testes rigorosos de sinal e velocidade para garantir que o conserto funcionou.
- `fechar_chamado_tecnico(id_chamado, relatorio_foto)`: encerra a visita no sistema.

## 3. O passo a passo no campo

```
1. CHEGADA
   Técnico avisa que chegou. O robô resume o histórico:
   "Cliente reclamou de sinal fraco. Teste remoto indicou perda na fibra."

2. DIAGNÓSTICO LOCAL
   Técnico manda foto da medição de sinal ou foto do cabo dobrado.
   O robô identifica a falha visual/técnica e sugere o reparo.

3. TROCA / CONFIG
   Técnico troca o modem e envia a foto da etiqueta com o código MAC.
   O robô cadastra o equipamento novo no sistema automaticamente.

4. VALIDAÇÃO DE SAÍDA
   O robô roda o teste final de sinal na linha.
   Se der tudo ok (ex.: "Status: ONLINE, Sinal: -19dBm"), autoriza o fecho.

5. BAIXA E FECHAMENTO
   O robô grava a foto da instalação concluída e encerra a visita.
```

## 4. Por que essa dupla (Agente Cliente + Agente Técnico) funciona tão bem?

- **Elimina o "atendimento da central" (NOC):** o técnico na rua não perde 15 a 20 minutos no telefone esperando a central liberar ou cadastrar um modem novo. Ele faz tudo conversando direto com o robô, em segundos.
- **Validação de qualidade com visão computacional:** o técnico envia a foto da fusão de fibra ou do conector, e o robô valida se a instalação segue o padrão de qualidade da empresa antes de fechar o chamado.
- **Garante o fechamento do ciclo:** o robô do cliente detectou a falha ➔ agendou a visita ➔ o robô do técnico ajudou a consertar e testou ➔ o robô do cliente envia uma mensagem final para o cliente: "Seu técnico finalizou o conserto! A internet já está operando 100%."
