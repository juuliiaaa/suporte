# Entrada e saída do sistema

Os exemplos abaixo foram extraídos dos arquivos JSON em `logs/`; nenhuma entrada ou saída foi reconstruída à mão.
Cada bloco preserva a mensagem digitada, o contrato fornecido pela sessão, o `thread_id` gerado pelo sistema, o commit e a data gravados na execução.
A entrada é texto livre. O objeto de saída completo é validado por `RespostaAtendimento` em `src/schemas.py`.

## Contrato

- **Entrada:** `EntradaAtendimento` (`contrato`, `mensagem`, `thread_id`). O contrato vem da sessão e o identificador da conversa é gerado pelo sistema.
- **Saída:** `RespostaAtendimento` (`resultado`, `fontes`, `suficiente`, além dos campos de controle). `suficiente=true` exige fonte verificável; `suficiente=false` exige `motivo_insuficiencia`.
- **Recusa:** é uma saída válida do contrato, não uma exceção não estruturada.

## Execuções registradas

### caso_C001_feliz

**O que ler:** Caminho feliz: o agente testa a linha, reinicia e confirma o resultado com novo teste.

- **Log:** `logs/caso_C001_feliz.json`
- **Data:** `2026-10-19T01:38:50` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C001` · `thread_id` `C001:c73c6628`
- **Texto exato digitado:** "A luz do modem está piscando vermelha e a internet caiu."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro, reiniciar_conexao, testar_linha
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 4 · **tokens:** 6005
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "Pronto, a linha voltou a ficar ONLINE e o sinal está estável (-22 dBm). A luz vermelha deve apagar em alguns minutos.\n\nSe a internet cair de novo, me avise que eu rodo o teste outra vez.",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "conferir_queda_bairro",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "reiniciar_conexao",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C002_divergencia

**O que ler:** Divergência: o cliente relata queda, mas a linha está ONLINE; o diagnóstico também considera a manutenção no bairro.

- **Log:** `logs/caso_C002_divergencia.json`
- **Data:** `2026-10-19T01:39:17` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C002` · `thread_id` `C002:7c4c69e3`
- **Texto exato digitado:** "Minha internet caiu, nada navega aqui em casa."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro, consultar_base_conhecimento
- **Consultas ao corpus:** 1 (sem trecho útil: 0) · **voltas:** 3 · **tokens:** 4513
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "A linha do seu contrato está online e o sinal está bom (-18 dBm). O problema é que o seu bairro, Jardim Ipê, está em manutenção geral de rede — a equipe já está atuando no local.\n\nPor isso não vou agendar visita individual. Enquanto a manutenção não termina, pode ser que a navegação fique instável.\n\nEnquanto isso, teste em outro aparelho e reinicie o roteador. Se o problema persistir mesmo assim, me avise.",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "conferir_queda_bairro",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C004_aprovacao_repetida

**O que ler:** Segunda aprovação da mesma visita: ja_existia=true prova que a escrita não duplicou o agendamento.

- **Log:** `logs/caso_C004_aprovacao_repetida.json`
- **Data:** `2026-10-19T01:42:10` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C004` · `thread_id` `C004:23eb916f`
- **Texto exato digitado:** "Sem internet nenhuma, a luz está vermelha."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro, obter_data_atual, propor_visita
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 4 · **tokens:** 6498
- **Pausas de aprovação:** `[
  {
    "payload": {
      "acao": "agendar_visita_tecnico",
      "contrato": "C004",
      "data_proposta": "2026-10-20",
      "consequencia": "desloca um técnico até a casa do cliente; tem custo e não é desfeito sozinho",
      "opcoes": [
        "aprovar",
        "rejeitar",
        "editar"
      ],
      "janela_edicao": [
        "2026-10-19",
        "2026-11-02"
      ],
      "prazo_segundos": 900
    },
    "resposta": {
      "decisao": "editar",
      "data": "2026-10-22"
    }
  }
]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "A visita técnica foi agendada para **22/10/2026**. Um técnico irá até o seu endereço para verificar a falha física na linha.",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "conferir_queda_bairro",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "obter_data_atual",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "propor_visita",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "agendar_visita_tecnico",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C004_pausa_edita

**O que ler:** Pausa human-in-the-loop: o cliente altera a data proposta e o código agenda a data validada.

- **Log:** `logs/caso_C004_pausa_edita.json`
- **Data:** `2026-10-19T01:41:16` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C004` · `thread_id` `C004:3c17344b`
- **Texto exato digitado:** "Sem internet nenhuma, a luz está vermelha."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, obter_data_atual, propor_visita
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 4 · **tokens:** 5924
- **Pausas de aprovação:** `[
  {
    "payload": {
      "acao": "agendar_visita_tecnico",
      "contrato": "C004",
      "data_proposta": "2026-10-20",
      "consequencia": "desloca um técnico até a casa do cliente; tem custo e não é desfeito sozinho",
      "opcoes": [
        "aprovar",
        "rejeitar",
        "editar"
      ],
      "janela_edicao": [
        "2026-10-19",
        "2026-11-02"
      ],
      "prazo_segundos": 900
    },
    "resposta": {
      "decisao": "editar",
      "data": "2026-10-22"
    }
  }
]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "A visita técnica foi **agendada para 22/10/2026**. A equipe técnica vai até você para resolver a falha física na linha.\n\nSe o problema voltar antes disso, me avise.",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "obter_data_atual",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "propor_visita",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "agendar_visita_tecnico",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C004_terminal

**O que ler:** Execução antiga da aprovação pelo terminal; preservada como registro histórico, com commit sem-git.

- **Log:** `logs/caso_C004_terminal.json`
- **Data:** `2026-10-18T12:17:18` · **commit:** `sem-git` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C004` · `thread_id` `C004:9a2bbe3e`
- **Texto exato digitado:** "Sem internet nenhuma, a luz está vermelha."
- **Prompts:** `{}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro, obter_data_atual, propor_visita
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 4 · **tokens:** 6472
- **Pausas de aprovação:** `[
  {
    "payload": {
      "acao": "agendar_visita_tecnico",
      "contrato": "C004",
      "data_proposta": "2026-10-19",
      "consequencia": "desloca um técnico até a casa do cliente; tem custo e não é desfeito sozinho",
      "opcoes": [
        "aprovar",
        "rejeitar",
        "editar"
      ],
      "janela_edicao": [
        "2026-10-18",
        "2026-11-01"
      ],
      "prazo_segundos": 900
    },
    "resposta": {
      "decisao": "editar",
      "data": "2026-10-22"
    }
  }
]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "A visita técnica foi **agendada para 22/10/2026**. Um técnico irá até você para resolver a falha física na linha.\n\nEnquanto isso, não há nada que você possa fazer por sua conta — a luz vermelha e o sinal de -30 dBm indicam um problema no cabo ou no equipamento que só a visita resolve.\n\nPosso ajudar em mais alguma coisa?",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "conferir_queda_bairro",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "obter_data_atual",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "propor_visita",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "agendar_visita_tecnico",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C005_nao_agenda

**O que ler:** O cliente pede técnico, mas o bairro está em manutenção; nenhuma visita individual é proposta.

- **Log:** `logs/caso_C005_nao_agenda.json`
- **Data:** `2026-10-19T01:40:02` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C005` · `thread_id` `C005:2d48a346`
- **Texto exato digitado:** "Estou sem internet, quero que mandem um técnico hoje."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 2 · **tokens:** 2850
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "Sua linha está offline, mas o sinal está bom (-19 dBm), então não é falha física. O problema é que o seu bairro, Jardim Ipê, está em manutenção geral de rede.\n\nComo a equipe de rede já está atuando na região, não consigo agendar uma visita técnica individual. A manutenção deve resolver a queda para todos os clientes do bairro.\n\nPosso ajudar com mais alguma coisa?",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "conferir_queda_bairro",
      "detalhe": null
    },
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_C999_inexistente

**O que ler:** Registro inexistente: a ferramenta informa que o contrato não foi localizado e o agente não inventa diagnóstico.

- **Log:** `logs/caso_C999_inexistente.json`
- **Data:** `2026-10-19T01:39:39` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C999` · `thread_id` `C999:61c1f55c`
- **Texto exato digitado:** "Minha internet caiu."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha, conferir_queda_bairro
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 2 · **tokens:** 2781
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "O sistema não localizou o contrato C999, então não consegui testar a linha nem o bairro.\n\nPosso tentar de novo, ou prefere que eu encaminhe para um atendente humano?",
  "fontes": [],
  "suficiente": false,
  "motivo_insuficiencia": "sem_fonte",
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_entrada_ambigua

**O que ler:** Entrada ambígua: o sistema declara a interpretação adotada e orienta um teste para confirmar.

- **Log:** `logs/caso_entrada_ambigua.json`
- **Data:** `2026-10-19T01:42:36` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C001` · `thread_id` `C001:0051a4dd`
- **Texto exato digitado:** "A internet está ruim hoje, não sei se é o wifi ou a internet mesmo."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** testar_linha
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 2 · **tokens:** 3183
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "A linha está online e o sinal está bom (-22 dBm). Então o problema provavelmente é no wifi, não na internet.\n\nPra confirmar, me ajuda com um teste:\n- Conecta um aparelho direto no roteador por cabo de rede (ethernet) e tenta navegar.\n\nSe funcionar pelo cabo, o problema é no wifi. Se não funcionar nem pelo cabo, me avisa que eu confiro se há queda no bairro.\n\nTambém vale tentar reiniciar o roteador (desligar por 10 segundos e ligar de novo).\n\nQuer que eu já reinicie a conexão à distância?",
  "fontes": [
    {
      "tipo": "ferramenta",
      "id": "testar_linha",
      "detalhe": null
    }
  ],
  "suficiente": true,
  "motivo_insuficiencia": null,
  "encaminhar_humano": false,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_entrada_incompleta

**O que ler:** Entrada incompleta: o sistema pede os detalhes necessários sem chamar o modelo ou ferramentas.

- **Log:** `logs/caso_entrada_incompleta.json`
- **Data:** `2026-10-19T01:42:10` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C001` · `thread_id` `C001:f8c14d80`
- **Texto exato digitado:** "não funciona"
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** nenhuma
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 0 · **tokens:** 0
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `entrada_incompleta`

**Objeto de saída completo:**

```json
{
  "resultado": "Não consegui entender qual é o problema. Para eu poder ajudar, me conte: o que a luz do modem mostra (verde, vermelha, piscando ou apagada) e se a falha acontece em todos os aparelhos ou só em um.",
  "fontes": [],
  "suficiente": false,
  "motivo_insuficiencia": "entrada_incompleta",
  "encaminhar_humano": false,
  "motivo_parada": "entrada_incompleta",
  "citacoes_invalidas": []
}
```

### caso_fora_do_corpus

**O que ler:** Pergunta fora do corpus: o portão de suficiência impede uma resposta sem fonte e apresenta uma recusa útil.

- **Log:** `logs/caso_fora_do_corpus.json`
- **Data:** `2026-10-19T01:40:27` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C001` · `thread_id` `C001:003c0fce`
- **Texto exato digitado:** "Como faço para abrir portas no roteador para jogar online?"
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** consultar_base_conhecimento
- **Consultas ao corpus:** 1 (sem trecho útil: 1) · **voltas:** 2 · **tokens:** 3010
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `resposta_final`

**Objeto de saída completo:**

```json
{
  "resultado": "Não encontrei essa informação nos manuais do suporte técnico. Posso encaminhar você para um atendente humano.",
  "fontes": [],
  "suficiente": false,
  "motivo_insuficiencia": "fora_do_corpus",
  "encaminhar_humano": true,
  "motivo_parada": "resposta_final",
  "citacoes_invalidas": []
}
```

### caso_fora_do_escopo

**O que ler:** Fora do escopo: a triagem encaminha cobrança/cancelamento para uma pessoa sem chamar o modelo.

- **Log:** `logs/caso_fora_do_escopo.json`
- **Data:** `2026-10-19T01:42:36` · **commit:** `8b9fd3d` · **modelo:** `qwen/qwen3.8-27b` · **temperature:** `0.2`
- **Entrada:** contrato `C001` · `thread_id` `C001:fc6b9c98`
- **Texto exato digitado:** "Quero cancelar meu plano e pedir um desconto."
- **Prompts:** `{
  "sistema": {
    "arquivo": "suporte_v2.md",
    "sha256": "8ff597289d95"
  },
  "procedural": {
    "arquivo": "procedural.md",
    "sha256": "5ecc9d266e5f"
  }
}`
- **Ferramentas chamadas:** nenhuma
- **Consultas ao corpus:** 0 (sem trecho útil: 0) · **voltas:** 0 · **tokens:** 0
- **Pausas de aprovação:** `[]`
- **Motivo de término:** `encaminhado_humano`

**Objeto de saída completo:**

```json
{
  "resultado": "Esse assunto (cobrança, fatura, cancelamento ou pedido de atendente) não é do suporte técnico. Aqui eu testo a linha, confiro queda no bairro, reinicio a conexão e proponho visita técnica. Vou encaminhar você para um atendente humano.",
  "fontes": [],
  "suficiente": false,
  "motivo_insuficiencia": "encaminhado_humano",
  "encaminhar_humano": true,
  "motivo_parada": "encaminhado_humano",
  "citacoes_invalidas": []
}
```

## Prova de aprovação repetida

As duas execuções aprovaram a mesma visita (`C004`, `2026-10-22`) em `thread_id` diferentes. A primeira criou o registro (`ja_existia=false`); a segunda reconheceu a chave de idempotência (`ja_existia=true`).

| Execução | thread_id | resultado do agendamento |
|---|---|---|
| primeira (`2026-10-19T01:41:16`) | `C004:3c17344b` | `{
  "contrato": "C004",
  "data": "2026-10-22",
  "status": "AGENDADA",
  "ja_existia": false
}` |
| segunda (`2026-10-19T01:42:10`) | `C004:23eb916f` | `{
  "contrato": "C004",
  "data": "2026-10-22",
  "status": "AGENDADA",
  "ja_existia": true
}` |
