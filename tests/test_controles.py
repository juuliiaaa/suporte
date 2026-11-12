"""Testes dos controles de segurança (docs/seguranca.md §3.2). Cada teste
tenta a ação indevida e verifica que foi bloqueada."""
import json
import os

import pytest

from src import config, db, llm, seguranca, tools
from src.llm import LLMSimulado, chamada, texto

from .conftest import AMANHA
from .test_grafo import rodar, roteiro_visita, visitas


# C1: canal x contrato (ASI03)
def test_c1_canal_de_outra_pessoa_nao_le_nada(checkpointer):
    simulado = LLMSimulado([])
    from src.agent import decisor_fixo, executar_atendimento
    r = executar_atendimento("C004", "sem internet", llm=simulado, decisor=decisor_fixo("aprovar"),
                             checkpointer=checkpointer, canal=db.canal_simulado("C001"), rotulo="t")
    assert r["motivo_parada"] == "identidade_nao_verificada"
    assert simulado.chamadas == 0
    assert not any(t.get("tipo") == "ferramenta" for t in r["trajetoria"])
    assert visitas() == []
    assert "sinal" not in r["saida"]["resultado"].lower()


@pytest.mark.parametrize("canal", [None, "", "abc", "5511999999999"])
def test_c1_canal_ausente_ou_invalido(checkpointer, canal):
    from src.agent import decisor_fixo, executar_atendimento
    r = executar_atendimento("C001", "sem internet", llm=LLMSimulado([]), decisor=decisor_fixo("rejeitar"),
                             checkpointer=checkpointer, canal=canal, rotulo="t")
    assert r["motivo_parada"] == "identidade_nao_verificada"


def test_c1_contrato_inexistente_e_canal_errado_sao_indistinguiveis(checkpointer):
    from src.agent import decisor_fixo, executar_atendimento
    a = executar_atendimento("C999", "sem internet", llm=LLMSimulado([]), decisor=decisor_fixo("rejeitar"),
                             checkpointer=checkpointer, canal="5511900000001", rotulo="t")
    b = executar_atendimento("C004", "sem internet", llm=LLMSimulado([]), decisor=decisor_fixo("rejeitar"),
                             checkpointer=checkpointer, canal="5511900000001", rotulo="t")
    assert a["saida"]["resultado"] == b["saida"]["resultado"]


def test_c1_nao_grava_memoria_do_contrato_alvo(checkpointer):
    from src import memoria
    from src.agent import decisor_fixo, executar_atendimento
    executar_atendimento("C004", "sem internet", llm=LLMSimulado([]), decisor=decisor_fixo("rejeitar"),
                         checkpointer=checkpointer, canal="5511999999999", rotulo="t")
    assert memoria.buscar_episodios("C004", "internet", "2026-10-18") == []


def test_c1_numero_em_claro_nao_vai_para_o_log(checkpointer, tmp_path):
    r, _ = rodar("C001", "sem internet", [chamada("testar_linha"), texto("ok")], checkpointer)
    assert db.canal_simulado("C001") not in open(r["arquivo_log"], encoding="utf-8").read()


def test_c1_banco_com_erro_nega(monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", "/nao/existe/provedor.db")
    assert seguranca.canal_confere("C001", db.canal_simulado("C001")) is False


# C2: host do provedor (ASI04)
@pytest.mark.parametrize("url", [
    "https://atacante.example/v1", "http://api.groq.com/openai/v1",
    "https://api.groq.com.atacante.example/v1", "", "https://localhost:8000/v1"])
def test_c2_host_fora_da_lista_e_recusado(url):
    with pytest.raises(llm.ErroLLMFatal):
        llm.verificar_host(url)


def test_c2_host_permitido_passa():
    assert llm.verificar_host("https://api.groq.com/openai/v1")


def test_c2_cliente_nao_envia_a_chave_para_host_hostil(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://atacante.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "chave-de-teste")
    with pytest.raises(llm.ErroLLMFatal) as e:
        llm.ClienteLLM().chamar([{"role": "user", "content": "oi"}], [])
    assert "host_nao_permitido" in str(e.value)


# C3: afirmação de agendamento (ASI09 / ASI01)
def test_c3_modelo_diz_que_agendou_sem_agendar(checkpointer):
    r, _ = rodar("C004", "sem internet", [
        chamada("testar_linha"), texto("Pronto, a visita foi agendada para amanhã.")], checkpointer)
    assert visitas() == []
    assert r["motivo_parada"] == "resposta_bloqueada"
    assert "para amanhã" not in r["saida"]["resultado"]
    assert "nenhuma visita foi agendada" in r["saida"]["resultado"]
    assert r["saida"]["encaminhar_humano"] is True
    assert any(t.get("controle") == "C3_afirmacao_de_agendamento" for t in r["trajetoria"])


def test_c3_cliente_rejeitou_e_modelo_diz_que_agendou(checkpointer):
    r, _ = rodar("C004", "sem internet", roteiro_visita("Agendei sua visita para amanhã."),
                 checkpointer, "rejeitar")
    assert r["motivo_parada"] == "resposta_bloqueada"


def test_c3_agendamento_real_pode_ser_afirmado(checkpointer):
    r, _ = rodar("C004", "sem internet", roteiro_visita("Visita agendada para amanhã."),
                 checkpointer, "aprovar")
    assert r["motivo_parada"] == "resposta_final"
    assert visitas() == [("C004", AMANHA, "AGENDADA")]


@pytest.mark.parametrize("frase", [
    "Não agendei nada, você recusou.", "Nenhuma visita foi agendada.",
    "Posso agendar uma visita se você aprovar."])
def test_c3_negacao_e_oferta_nao_bloqueiam(frase):
    assert seguranca.verificar_afirmacao_de_agendamento(frase, []) is None


# C4: suspensão (ASI10)
def test_c4_arquivo_de_suspensao_para_tudo(checkpointer, tmp_path, monkeypatch):
    caminho = tmp_path / "SUSPENSO"
    caminho.write_text("")
    monkeypatch.setattr(config, "CAMINHO_SUSPENSAO", str(caminho))
    r, simulado = rodar("C001", "sem internet", [], checkpointer)
    assert r["motivo_parada"] == "agente_suspenso" and simulado.chamadas == 0
    assert r["saida"]["encaminhar_humano"] is True


def test_c4_variavel_de_ambiente(checkpointer, monkeypatch):
    monkeypatch.setenv("AGENTE_SUSPENSO", "1")
    r, _ = rodar("C001", "sem internet", [], checkpointer)
    assert r["motivo_parada"] == "agente_suspenso"


# Interruptor de avaliação: sem controles, o comportamento é o da Parte 2
def test_sem_controles_o_comportamento_e_o_da_parte_2(checkpointer, monkeypatch):
    monkeypatch.setattr(config, "CONTROLES_ATIVOS", False)
    from src.agent import decisor_fixo, executar_atendimento
    r = executar_atendimento("C001", "sem internet", llm=LLMSimulado([chamada("testar_linha"), texto("ok")]),
                             decisor=decisor_fixo("rejeitar"), checkpointer=checkpointer,
                             canal="0", rotulo="t")
    assert r["motivo_parada"] == "resposta_final"


# ASI08: exceção de ferramenta vira erro como dado
def test_excecao_de_ferramenta_nao_derruba(checkpointer, monkeypatch):
    def quebra(**kw):
        raise RuntimeError("database is locked")
    monkeypatch.setitem(tools.FUNCOES, "testar_linha", quebra)
    r, _ = rodar("C001", "sem internet", [chamada("testar_linha"), texto("Não consegui testar agora.")], checkpointer)
    t = [x for x in r["trajetoria"] if x.get("nome") == "testar_linha"][0]
    assert t["resultado"]["erro"] == "ferramenta_indisponivel"
    assert r["motivo_parada"] == "resposta_final"


# Observabilidade: o trace tem a árvore e os atributos obrigatórios
def _spans(tmp_path):
    pasta = tmp_path / "logs" / "traces"
    linhas = []
    for arq in pasta.glob("spans-*.jsonl"):
        linhas += [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()]
    return linhas


def test_trace_tem_raiz_chat_e_ferramenta(checkpointer, tmp_path):
    r, _ = rodar("C001", "luz vermelha", [chamada("testar_linha"), texto("ok")], checkpointer)
    spans = _spans(tmp_path)
    raiz = [s for s in spans if s["name"].startswith("invoke_agent")]
    assert len(raiz) == 1 and raiz[0]["parent_span_id"] is None
    at = raiz[0]["attributes"]
    assert at["suporte.motivo_termino"] == "resposta_final"
    assert at["suporte.versao_sistema"] == config.VERSAO_SISTEMA
    assert at["gen_ai.operation.name"] == "invoke_agent"
    filhos = [s for s in spans if s["parent_span_id"] == raiz[0]["span_id"]]
    nomes = sorted(s["name"].split()[0] for s in filhos)
    assert nomes == ["chat", "chat", "execute_tool"]
    assert {s["trace_id"] for s in spans} == {raiz[0]["trace_id"]}


def test_trace_registra_a_aprovacao_humana(checkpointer, tmp_path):
    rodar("C004", "sem internet", roteiro_visita("Visita agendada."), checkpointer, "aprovar")
    raiz = [s for s in _spans(tmp_path) if s["name"].startswith("invoke_agent")][0]
    ev = [e for e in raiz["events"] if e["name"] == "aprovacao_humana"][0]["attributes"]
    assert ev["suporte.aprovacao.quem"] == "cliente"
    assert ev["suporte.aprovacao.decisao"] == "aprovar"
    assert AMANHA in ev["suporte.aprovacao.o_que_foi_proposto"]


def test_texto_do_bloqueio_nao_dispara_o_proprio_controle():
    from src.grafo import TEXTO_RESPOSTA_BLOQUEADA
    assert seguranca.verificar_afirmacao_de_agendamento(TEXTO_RESPOSTA_BLOQUEADA, []) is None
