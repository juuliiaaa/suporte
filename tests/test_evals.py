import json
import os
from collections import Counter
from types import SimpleNamespace

from evals import comparar, juiz, metricas, validar_juiz, verificacoes as vf
from evals.rodar import ARQ_DATASET, carregar_dataset


def test_dataset_cumpre_a_composicao_do_enunciado():
    casos = carregar_dataset()
    assert len(casos) >= 20 and len({c["id"] for c in casos}) == len(casos)
    for c in casos:
        assert c["origem"] in ("producao", "desenvolvimento", "sintetico")
        assert c["classe"] and c["por_que_existe"] and c["esperado"]
    classes = Counter(c["classe"] for c in casos)
    assert len([k for k, n in classes.items() if n > 1]) >= 3
    assert any(c["classe"] == "recusa" for c in casos)


def test_dataset_sinteticos_tem_campo_de_revisao():
    for c in carregar_dataset():
        if c["origem"] == "sintetico":
            assert "revisado_por" in c


def test_percentil_e_kappa():
    assert metricas.percentil([1, 2, 3, 4, 5], 50) == 3
    assert abs(metricas.percentil([1, 2, 3, 4, 5], 95) - 4.8) < 1e-9
    m = validar_juiz.matriz([(True, True)] * 8 + [(False, False)] * 8 + [(True, False)] * 2 + [(False, True)] * 2)
    assert validar_juiz.concordancia(m) == 16 / 20
    assert abs(validar_juiz.kappa(m) - 0.6) < 1e-9


def _cliente(conteudo):
    def criar(**kw):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=conteudo))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=criar)))


def test_juiz_le_json_valido_e_recusa_o_invalido():
    assert juiz.julgar(_cliente('{"aprovado": true, "motivo": "claro"}'), "m", "x", "y")["aprovado"] is True
    assert juiz.julgar(_cliente('texto {"aprovado": false, "motivo": "jargão"} fim'), "m", "x", "y")["aprovado"] is False
    assert juiz.julgar(_cliente("aprovado"), "m", "x", "y")["aprovado"] is None
    assert juiz.julgar(_cliente('{"aprovado": "sim"}'), "m", "x", "y")["aprovado"] is None


def test_verificacoes_de_trajetoria_e_resultado():
    reg = {"trajetoria": [{"tipo": "ferramenta", "nome": "reiniciar_conexao"},
                          {"tipo": "ferramenta", "nome": "testar_linha"}], "tokens": 0}
    assert vf.trajetoria({"reteste_apos_reinicio": True, "ordem": [["testar_linha", "reiniciar_conexao"]]}, reg)
    assert not vf.trajetoria({"reteste_apos_reinicio": True}, reg)
    assert vf.trajetoria({"max_chamadas": {"reiniciar_conexao": 0}}, reg)
    mundo = {"visitas": [("C004", "2026-11-12")], "modems": {"C001": {"reinicios_hoje": 1}}}
    import datetime
    hoje = datetime.date(2026, 11, 11)
    assert not vf.resultado({"visitas": [["C004", "amanha"]], "reinicios": {"C001": 1}}, mundo, hoje, "C004")
    assert vf.resultado({"visitas": []}, mundo, hoje, "C004")


def test_comparar_imprime_classes_e_delta(tmp_path):
    def rodada(nome, versao, oks):
        p = tmp_path / nome
        p.mkdir()
        meta = {"versao_sistema": versao, "dataset_versao": "1.0.0", "n_casos": len(oks),
                "origens": {"producao": 0, "desenvolvimento": len(oks), "sintetico": 0}}
        (p / "meta.json").write_text(json.dumps(meta))
        (p / "resultados.jsonl").write_text("\n".join(
            json.dumps({"id": f"X{i}", "classe": "seguranca", "ok": ok}) for i, ok in enumerate(oks)))
        return str(p)
    txt = comparar.relatorio(rodada("a", "3.0.0", [True, False]), rodada("b", "3.1.0", [True, True]))
    assert "seguranca" in txt and "+50" in txt and "MÉDIA" in txt and "X1: FALHA -> ok" in txt
