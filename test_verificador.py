"""Verificador de casos rotulados, caso de divergência isolado e argumentos
inválidos do modelo. Sem modelo e sem rede."""
import json

from src import tools
from src.llm import _args_ou_vazio
from scripts import verificar_casos as v


def _log(trajetoria=None, saida=None, motivo="resposta_final", tokens=100):
    return {"trajetoria": trajetoria or [], "saida": saida or {}, "motivo_parada": motivo,
            "tokens": tokens, "modelo": "simulado", "commit": "x", "timestamp": "t"}


def test_acao_agendar_vence_reiniciar():
    log = _log([
        {"tipo": "ferramenta", "nome": "reiniciar_conexao", "resultado": {"status": "ok"}},
        {"tipo": "aprovacao_humana", "resultado": {"status": "AGENDADA", "ja_existia": False}},
    ])
    assert v.acao_do_log(log) == "agendar"


def test_reinicio_com_erro_nao_conta():
    log = _log([{"tipo": "ferramenta", "nome": "reiniciar_conexao", "resultado": {"erro": "sinal_fraco"}}])
    assert v.acao_do_log(log) == "nao_agir"


def test_escalar_pela_saida_ou_pelo_motivo():
    assert v.acao_do_log(_log(saida={"encaminhar_humano": True})) == "escalar"
    assert v.acao_do_log(_log(motivo="encaminhado_humano")) == "escalar"
    assert v.acao_do_log(_log(motivo="aprovacao_expirada")) == "escalar"


def _pasta_com_logs(tmp_path, por_rotulo):
    for rotulo, log in por_rotulo.items():
        (tmp_path / f"{rotulo}.json").write_text(json.dumps(log), encoding="utf-8")
    return str(tmp_path)


def test_criterio_de_sucesso_exige_oito_acertos(tmp_path):
    casos = v.carregar_casos()
    assert len(casos) == 10
    # todos os logs como "nao_agir": acerta os casos cuja ação esperada é nao_agir
    logs = {c["rotulo"]: _log(saida={"suficiente": c.get("suficiente_esperado", True)}) for c in casos}
    res = v.avaliar(_pasta_com_logs(tmp_path, logs), casos)
    esperados_nao_agir = sum(1 for c in casos if c["acao_esperada"] == "nao_agir")
    assert res["acertos"] == esperados_nao_agir
    assert not res["criterio_ok"]


def test_visita_em_bairro_em_manutencao_reprova_mesmo_com_muitos_acertos(tmp_path):
    casos = v.carregar_casos()
    logs = {}
    for c in casos:
        if c["acao_esperada"] == "agendar" or c.get("bairro_em_manutencao"):
            logs[c["rotulo"]] = _log([{"tipo": "aprovacao_humana",
                                       "resultado": {"status": "AGENDADA", "ja_existia": True}}],
                                     saida={"suficiente": True})
        elif c["acao_esperada"] == "reiniciar":
            logs[c["rotulo"]] = _log([{"tipo": "ferramenta", "nome": "reiniciar_conexao",
                                       "resultado": {"status": "ok"}}], saida={"suficiente": True})
        elif c["acao_esperada"] == "escalar":
            logs[c["rotulo"]] = _log(saida={"encaminhar_humano": True, "suficiente": False})
        else:
            logs[c["rotulo"]] = _log(saida={"suficiente": c.get("suficiente_esperado", True)})
    res = v.avaliar(_pasta_com_logs(tmp_path, logs), casos)
    assert res["violacoes"] == ["caso_C005_nao_agenda"]
    assert res["acertos"] == 9
    assert not res["criterio_ok"]


def test_caso_sem_log_conta_como_erro(tmp_path):
    res = v.avaliar(str(tmp_path))
    assert res["sem_log"] == 10 and res["acertos"] == 0


def test_c002_isola_a_divergencia():
    """Linha ONLINE com sinal bom e bairro sem manutenção: nada no sistema
    explica a queda que o cliente relata."""
    linha = tools.testar_linha("C002")
    bairro = tools.conferir_queda_bairro("C002")
    assert linha["status"] == "ONLINE" and not linha["falha_fisica_provavel"]
    assert bairro["em_manutencao"] is False


def test_c005_continua_em_bairro_em_manutencao():
    assert tools.conferir_queda_bairro("C005")["em_manutencao"] is True


def test_argumentos_invalidos_do_modelo_viram_vazio():
    assert _args_ou_vazio('{"data": "2026-10-20"}') == {"data": "2026-10-20"}
    assert _args_ou_vazio('{"data": ') == {}
    assert _args_ou_vazio("[1, 2]") == {}
    assert _args_ou_vazio(None) == {}
    assert _args_ou_vazio("") == {}


def test_limpar_logs_antigos_so_pega_json_vencido(tmp_path):
    import os
    import time

    from scripts.limpar_logs_antigos import antigos

    velho = tmp_path / "velho.json"
    novo = tmp_path / "novo.json"
    outro = tmp_path / "velho.txt"
    for f in (velho, novo, outro):
        f.write_text("{}")
    antes = time.time() - 40 * 86400
    os.utime(velho, (antes, antes))
    os.utime(outro, (antes, antes))
    assert antigos(str(tmp_path)) == [str(velho)]
