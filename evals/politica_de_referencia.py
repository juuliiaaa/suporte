"""Modelo simulado de política fixa, só para verificar o arcabouço da suíte
sem chamar o provedor (`python -m evals.rodar --versao X --simulado`). Os
resultados dessa rodada NÃO são evidência sobre o modelo real: ela existe
para provar que o dataset é satisfazível e que o runner funciona."""
import json
import re

from src.llm import RespostaLLM, chamada, texto


class PoliticaDeReferencia:
    modelo = "politica-de-referencia"

    def chamar(self, mensagens, ferramentas) -> RespostaLLM:
        usuario = next(m["content"] for m in mensagens if m["role"] == "user")
        resultados = []
        for m in mensagens:
            if m["role"] == "tool":
                try:
                    resultados.append(json.loads(m["content"]))
                except json.JSONDecodeError:
                    pass
        nomes_chamados = [c["function"]["name"] for m in mensagens if m.get("tool_calls")
                          for c in m["tool_calls"]]
        baixo = usuario.lower()
        if not nomes_chamados:
            if re.search(r"significa|quantos dbm|abrir portas|quanto custa", baixo):
                return chamada("consultar_base_conhecimento", {"pergunta": usuario}, tokens=120)
            return chamada("testar_linha", tokens=120)
        ultimo = resultados[-1] if resultados else {}
        if nomes_chamados[-1] == "consultar_base_conhecimento":
            if ultimo.get("suficiente"):
                tr = ultimo["trechos"][0]
                return texto(f"Segundo o manual [{tr['id']}]: {tr['texto'][:120]}", tokens=150)
            return texto("O manual não cobre essa pergunta. Posso encaminhar você para um atendente.", tokens=100)
        if nomes_chamados[-1] == "testar_linha":
            if ultimo.get("falha_fisica_provavel"):
                return chamada("obter_data_atual", tokens=100)
            if ultimo.get("status") == "OFFLINE" and "reiniciar_conexao" not in nomes_chamados:
                return chamada("conferir_queda_bairro", tokens=100)
            return texto("Testei sua linha e ela está funcionando. Se cair de novo, me avise.", tokens=100)
        if nomes_chamados[-1] == "conferir_queda_bairro":
            if ultimo.get("em_manutencao"):
                return texto("Seu bairro está em manutenção e a equipe já está atuando. Não vou agendar visita individual.", tokens=100)
            return chamada("reiniciar_conexao", tokens=100)
        if nomes_chamados[-1] == "reiniciar_conexao":
            return chamada("testar_linha", tokens=100)
        if nomes_chamados[-1] == "obter_data_atual":
            return chamada("propor_visita", {"data": ultimo.get("amanha")}, tokens=100)
        if nomes_chamados[-1] == "propor_visita":
            if "decisao_do_cliente" in ultimo and ultimo["resultado"].get("status") == "AGENDADA":
                return texto(f"Visita agendada para {ultimo['resultado']['data']}. O técnico vai até a sua casa.", tokens=100)
            return texto("Entendi. Nada foi agendado. Se mudar de ideia, me avise.", tokens=100)
        return texto("Não consegui concluir. Vou encaminhar você para um atendente.", tokens=100)
