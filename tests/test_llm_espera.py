"""Espera entre tentativas em erro 429 (sem rede)."""
import httpx
import openai
import pytest

from src import config
from src.llm import ClienteLLM, ErroLLMFatal, _limite_diario, _segundos_de_espera

MSG_MINUTO = ("Rate limit reached for model `m` on input tokens per minute (ITPM): Limit 7000, "
              "Used 5751, Requested 1406. Please try again in 1.345714285s.")
MSG_DIA = ("Rate limit reached for model `m` on tokens per day (TPD): Limit 200000, Used 198331, "
           "Requested 3017. Please try again in 9m42.336s.")


def _erro_429(msg):
    req = httpx.Request("POST", "https://api.groq.com/x")
    return openai.RateLimitError(msg, response=httpx.Response(429, request=req), body=None)


def test_espera_usa_a_dica_do_provedor_mais_folga():
    assert _segundos_de_espera(MSG_MINUTO, 1) == pytest.approx(2.345714285)
    assert _segundos_de_espera("sem dica", 3) == 8.0
    assert _segundos_de_espera("try again in 9m42.3s", 1) == 60.0  # teto


def test_limite_diario_e_reconhecido():
    assert _limite_diario(MSG_DIA) and not _limite_diario(MSG_MINUTO)


class _Falha:
    def __init__(self, erros):
        self.erros, self.chamadas = list(erros), 0
        self.chat = self

    @property
    def completions(self):
        return self

    def create(self, **kw):
        self.chamadas += 1
        raise self.erros.pop(0)


def test_limite_por_minuto_espera_o_tempo_informado_e_tenta_de_novo():
    esperas = []
    falha = _Falha([_erro_429(MSG_MINUTO)] * config.TENTATIVAS_LLM)
    c = ClienteLLM(client=falha, esperar=esperas.append)
    with pytest.raises(ErroLLMFatal):
        c.chamar([{"role": "user", "content": "x"}], [])
    assert falha.chamadas == config.TENTATIVAS_LLM
    assert esperas and all(e == pytest.approx(2.345714285) for e in esperas)


def test_limite_diario_falha_na_hora():
    esperas = []
    falha = _Falha([_erro_429(MSG_DIA)] * 5)
    c = ClienteLLM(client=falha, esperar=esperas.append)
    with pytest.raises(ErroLLMFatal, match="limite_diario"):
        c.chamar([{"role": "user", "content": "x"}], [])
    assert falha.chamadas == 1 and esperas == []
