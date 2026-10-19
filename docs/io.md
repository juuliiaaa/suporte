# Entrada e saída do sistema

Exemplos reais, gerados por scripts/gerar_io.py a partir dos logs em logs/.
A entrada é texto livre; o contrato vem da sessão e o thread_id é gerado pelo sistema.
A saída é validada (src/schemas.py): resultado, fontes, suficiente.

## caso_C001_feliz

- data: 2026-10-18T12:09:15, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C001, thread_id C001:036bdf3a, mensagem: "A luz do modem está piscando vermelha e a internet caiu."
- ferramentas chamadas: testar_linha, conferir_queda_bairro, reiniciar_conexao, testar_linha
- pausas de aprovação: nenhuma
- voltas: 4, tokens: 5982, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'reiniciar_conexao'), ('ferramenta', 'testar_linha')], citações inválidas=[]
- resultado: Reiniciamos a conexão e o teste voltou a mostrar a linha ONLINE, com sinal normal (-22 dBm).

Pode testar a navegação aí? Se a luz do modem continuar piscando vermelha ou a internet cair de novo, me avise que eu abro uma visita técnica.

## caso_C002_divergencia

- data: 2026-10-18T12:09:27, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C002, thread_id C002:e9ab7cd0, mensagem: "Minha internet caiu, nada navega aqui em casa."
- ferramentas chamadas: testar_linha, conferir_queda_bairro
- pausas de aprovação: nenhuma
- voltas: 2, tokens: 2817, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'testar_linha')], citações inválidas=[]
- resultado: O teste da sua linha está normal (sinal -18 dBm, online), mas o bairro Jardim Ipê está em manutenção geral. A equipe de rede já está atuando na região, então não vou agendar visita individual.

Enquanto isso, pode testar a navegação em outro aparelho (celular via Wi‑Fi, notebook) e me contar o resultado?

## caso_C004_aprovacao_repetida

- data: 2026-10-18T12:12:35, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C004, thread_id C004:65638349, mensagem: "Sem internet nenhuma, a luz está vermelha."
- ferramentas chamadas: testar_linha, conferir_queda_bairro, obter_data_atual, propor_visita
- pausas de aprovação: [('2026-10-19', {'decisao': 'editar', 'data': '2026-10-21'})]
- voltas: 4, tokens: 6516, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'obter_data_atual'), ('ferramenta', 'propor_visita'), ('ferramenta', 'testar_linha'), ('ferramenta', 'agendar_visita_tecnico')], citações inválidas=[]
- resultado: A visita técnica foi **agendada para 21/10/2026**. Um técnico irá até você para verificar a falha física na linha.

Se o problema voltar antes disso, me avise.

## caso_C004_pausa_edita

- data: 2026-10-18T12:11:41, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C004, thread_id C004:477f15b9, mensagem: "Sem internet nenhuma, a luz está vermelha."
- ferramentas chamadas: testar_linha, conferir_queda_bairro, obter_data_atual, propor_visita
- pausas de aprovação: [('2026-10-19', {'decisao': 'editar', 'data': '2026-10-21'})]
- voltas: 4, tokens: 6074, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'obter_data_atual'), ('ferramenta', 'propor_visita'), ('ferramenta', 'testar_linha'), ('ferramenta', 'agendar_visita_tecnico')], citações inválidas=[]
- resultado: A visita técnica foi agendada para **21/10/2026**. Um técnico irá até você para verificar a linha e resolver o problema do sinal.

## caso_C004_terminal

- data: 2026-10-18T12:17:18, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C004, thread_id C004:9a2bbe3e, mensagem: "Sem internet nenhuma, a luz está vermelha."
- ferramentas chamadas: testar_linha, conferir_queda_bairro, obter_data_atual, propor_visita
- pausas de aprovação: [('2026-10-19', {'decisao': 'editar', 'data': '2026-10-22'})]
- voltas: 4, tokens: 6472, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'obter_data_atual'), ('ferramenta', 'propor_visita'), ('ferramenta', 'testar_linha'), ('ferramenta', 'agendar_visita_tecnico')], citações inválidas=[]
- resultado: A visita técnica foi **agendada para 22/10/2026**. Um técnico irá até você para resolver a falha física na linha.

Enquanto isso, não há nada que você possa fazer por sua conta — a luz vermelha e o sinal de -30 dBm indicam um problema no cabo ou no equipamento que só a visita resolve.

Posso ajudar em mais alguma coisa?

## caso_C005_nao_agenda

- data: 2026-10-18T12:10:39, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C005, thread_id C005:e7e05177, mensagem: "Estou sem internet, quero que mandem um técnico hoje."
- ferramentas chamadas: testar_linha, conferir_queda_bairro
- pausas de aprovação: nenhuma
- voltas: 2, tokens: 2866, motivo de término: resposta_final
- saída: suficiente=True, encaminhar_humano=False, fontes=[('ferramenta', 'conferir_queda_bairro'), ('ferramenta', 'testar_linha')], citações inválidas=[]
- resultado: Sua linha está offline, mas o sinal está bom (-19 dBm), então não é falha física. O problema é que seu bairro, Jardim Ipê, está em manutenção geral de rede.

A equipe de rede já está atuando na região, então não consigo agendar uma visita individual. A previsão é que o serviço volte assim que a manutenção for concluída.

Posso te ajudar com mais alguma coisa?

## caso_C999_inexistente

- data: 2026-10-18T12:10:15, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C999, thread_id C999:cf9bbd9d, mensagem: "Minha internet caiu."
- ferramentas chamadas: testar_linha, testar_linha, conferir_queda_bairro
- pausas de aprovação: nenhuma
- voltas: 4, tokens: 5791, motivo de término: resposta_final
- saída: suficiente=False, encaminhar_humano=False, fontes=[], citações inválidas=[]
- resultado: Infelizmente, o sistema não está conseguindo localizar o seu contrato (C999) para eu rodar os testes de linha e verificar a situação do bairro.

Isso impede que eu diagnostique o problema agora. Para eu conseguir ajudar, preciso que o sistema reconheça o seu contrato.

Posso te encaminhar para um atendente humano que consiga verificar a situação do contrato e resolver essa questão?

## caso_fora_do_corpus

- data: 2026-10-18T12:15:57, commit: sem-git, modelo: qwen/qwen3.8-27b, temperature: 0.2
- entrada: contrato C001, thread_id C001:eecbf9f9, mensagem: "Como faço para abrir portas no roteador para jogar online?"
- ferramentas chamadas: consultar_base_conhecimento
- pausas de aprovação: nenhuma
- voltas: 2, tokens: 3085, motivo de término: resposta_final
- saída: suficiente=False, encaminhar_humano=True, fontes=[], citações inválidas=[]
- resultado: Não encontrei essa informação nos manuais do suporte técnico. Posso encaminhar você para um atendente humano.
