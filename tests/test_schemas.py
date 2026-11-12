import pytest
from pydantic import ValidationError

from src.schemas import EntradaAtendimento, Fonte, RespostaAtendimento


def test_entrada_valida_texto_e_identificadores_da_sessao():
    entrada = EntradaAtendimento(
        contrato="C001", mensagem="Minha internet caiu", thread_id="C001:abc12345"
    )
    assert entrada.mensagem == "Minha internet caiu"
    assert entrada.contrato == "C001"
    assert entrada.thread_id == "C001:abc12345"


@pytest.mark.parametrize("campo", ["contrato", "thread_id"])
def test_entrada_rejeita_identificador_vazio(campo):
    dados = {"contrato": "C001", "mensagem": "Minha internet caiu", "thread_id": "C001:abc12345"}
    dados[campo] = ""
    with pytest.raises(ValidationError):
        EntradaAtendimento.model_validate(dados)


def test_saida_suficiente_exige_fonte_conferivel():
    with pytest.raises(ValidationError):
        RespostaAtendimento(
            resultado="A linha está normal.", fontes=[], suficiente=True, motivo_parada="resposta_final"
        )


def test_saida_insuficiente_exige_motivo():
    with pytest.raises(ValidationError):
        RespostaAtendimento(
            resultado="Não sei responder.", fontes=[], suficiente=False, motivo_parada="resposta_final"
        )


def test_recusa_e_saida_valida_do_contrato():
    resposta = RespostaAtendimento(
        resultado="Não encontrei essa informação no manual.",
        fontes=[], suficiente=False, motivo_insuficiencia="fora_do_corpus",
        motivo_parada="resposta_final", encaminhar_humano=True,
    )
    assert resposta.suficiente is False
    assert resposta.motivo_insuficiencia == "fora_do_corpus"
