"""
Gera docs/io.md e preenche o exemplo do README a partir dos logs reais em
logs/. Nada é escrito à mão: entrada, objeto de saída completo, commit, data e
contagens saem do log.

Uso: python -m scripts.gerar_io
"""
import glob
import json
import os
import re

from src import config

COMO_LER = {
    "caso_C001_feliz": "Caminho feliz, sem visita. Leia as ferramentas chamadas e as fontes: cada afirmação da resposta aponta para uma ferramenta ou para um trecho do manual (S01) que o sistema confirmou ter sido recuperado.",
    "caso_C002_divergencia": "Recusa por regra de código. O bairro está em manutenção; leia pausas de aprovação (nenhuma) e a ausência de visita agendada.",
    "caso_C999_inexistente": "Entrada incompleta pelo lado do cadastro: o contrato não existe. Leia suficiente=false e o encaminhamento humano.",
    "caso_C005_nao_agenda": "O cliente pediu técnico, mas o bairro está em manutenção. Leia que propor_visita foi recusada e nada foi agendado.",
    "caso_fora_do_corpus": "Pergunta técnica fora do corpus. Leia que o portão do RAG barrou a resposta e o texto fixo de recusa, com suficiente=false.",
    "caso_C004_terminal": "Mesma pausa de aprovação, mas decidida pelo terminal (decisor interativo). Leia a data final escolhida e o resultado do agendamento.",
    "caso_C004_pausa_edita": "Pausa de aprovação. Leia pausas de aprovação: data proposta, decisão editar e data final já validada pelo código.",
    "caso_C004_aprovacao_repetida": "Mesma aprovação repetida. Leia resultado.ja_existia=true: nenhuma segunda visita foi criada.",
    "caso_entrada_incompleta": "Entrada incompleta. Leia que nenhuma ferramenta foi chamada e que a resposta pergunta o que falta.",
    "caso_entrada_ambigua": "Entrada ambígua. Leia a frase em que o modelo declara qual leitura escolheu antes de seguir.",
    "caso_fora_do_escopo": "Fora do escopo (cancelamento e desconto). Leia a triagem por código: o modelo nem foi chamado e o texto diz o que o sistema faz.",
}


def carregar():
    logs = {}
    for caminho in sorted(glob.glob(os.path.join(config.PASTA_LOGS, "*.json"))):
        with open(caminho, encoding="utf-8") as f:
            log = json.load(f)
        nome = os.path.basename(caminho)[:-5]
        if "commit" not in log:
            print(f"ignorado (formato antigo, anterior à Parte 2): {nome}")
            continue
        logs[nome] = log
    return logs


def contagens(log):
    traj = log["trajetoria"]
    consultas = [t for t in traj if t.get("tipo") == "ferramenta" and t["nome"] == "consultar_base_conhecimento"]
    inuteis = [t for t in consultas if not (t.get("resultado") or {}).get("trechos")]
    return len(consultas), len(inuteis)


def secao(nome, log):
    s = log.get("saida") or {}
    ferramentas = [t["nome"] for t in log["trajetoria"] if t.get("tipo") == "ferramenta"]
    consultas, inuteis = contagens(log)
    return [
        f"## {nome}",
        "",
        f"**O que ler:** {COMO_LER.get(nome, 'Leia a trajetória e o objeto de saída.')}",
        "",
        f"- data: {log['timestamp']}, commit: {log['commit']}, modelo: {log['modelo']}, temperature: {log['temperature']}",
        f"- prompts: {json.dumps(log.get('prompts', 'não registrado'), ensure_ascii=False)}",
        f"- entrada: contrato {log['contrato']}, thread_id {log['thread_id']}, mensagem: \"{log['mensagem_inicial']}\"",
        f"- ferramentas chamadas: {', '.join(ferramentas) or 'nenhuma'}",
        f"- consultas ao corpus: {consultas} (sem trecho útil: {inuteis}); voltas: {log.get('voltas')}; tokens: {log.get('tokens')}",
        f"- pausas de aprovação: {[(p['payload']['data_proposta'], p['resposta']) for p in log.get('pausas_de_aprovacao', [])] or 'nenhuma'}",
        f"- motivo de término: {log['motivo_parada']}",
        "- objeto de saída completo:",
        "",
        "```json",
        json.dumps(s, ensure_ascii=False, indent=2),
        "```",
        "",
    ]


def aprovacao_repetida(logs):
    a, b = logs.get("caso_C004_pausa_edita"), logs.get("caso_C004_aprovacao_repetida")
    if not (a and b):
        return []

    def visita(log):
        for t in log["trajetoria"]:
            if t.get("tipo") == "aprovacao_humana":
                return t.get("resultado")
    ra, rb = visita(a), visita(b)
    if not rb or not rb.get("ja_existia"):
        return ["## Prova de aprovação repetida", "",
                "Sem prova: a segunda execução não devolveu ja_existia=true. Rode python -m scripts.rodar_casos --reset C004 C004B e depois gerar_io de novo.", ""]
    if ra and ra.get("ja_existia"):
        return ["## Prova de aprovação repetida", "",
                "Sem prova: a primeira execução já encontrou a visita (o banco não foi zerado antes). Rode python -m scripts.rodar_casos --reset C004 C004B e depois gerar_io de novo.", ""]
    return [
        "## Prova de aprovação repetida",
        "",
        f"- primeira execução ({a['thread_id']}): {json.dumps(ra, ensure_ascii=False)}",
        f"- segunda execução, mesma aprovação ({b['thread_id']}): {json.dumps(rb, ensure_ascii=False)}",
        "- ja_existia=true na segunda indica que o código reconheceu a visita pela chave (contrato, data) e não criou outra.",
        "",
    ]


def exemplo_readme(logs):
    log = logs.get("caso_C001_feliz")
    if not log:
        return None
    s = log.get("saida") or {}
    fontes = [(f["tipo"], f["id"]) for f in s.get("fontes", [])]
    pausas = log.get("pausas_de_aprovacao", [])
    pausa = ("O grafo pausou " + str(len(pausas)) + " vez(es) esperando o cliente: "
             + str([(p["payload"]["data_proposta"], p["resposta"]) for p in pausas])
             if pausas else "Nesta execução o grafo não precisou pausar (nenhuma visita foi proposta).")
    return (
        "```\n"
        f"$ python -m src.agent {log['contrato']} \"{log['mensagem_inicial']}\"\n"
        f"Resposta: {s.get('resultado')}\n"
        f"Fontes: {fontes}  suficiente={s.get('suficiente')}\n"
        f"Parou por: {log['motivo_parada']}   Log: logs/caso_C001_feliz.json\n"
        "```\n"
        f"{pausa}\n"
        f"Commit {log['commit']}, {log['timestamp']}."
    )


def preencher_readme(texto):
    caminho = os.path.join(config.RAIZ, "README.md")
    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()
    marcado = f"<!-- EXEMPLO:INICIO -->\n{texto}\n<!-- EXEMPLO:FIM -->"
    if "<!-- EXEMPLO:INICIO -->" in conteudo:
        conteudo = re.sub(r"<!-- EXEMPLO:INICIO -->.*?<!-- EXEMPLO:FIM -->", lambda _: marcado, conteudo, flags=re.S)
    else:
        print("README sem marcadores EXEMPLO:INICIO/FIM; exemplo não inserido")
        return
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("README.md atualizado com o exemplo real")


def main():
    logs = carregar()
    linhas = [
        "# Entrada e saída do sistema",
        "",
        "Exemplos reais, gerados por scripts/gerar_io.py a partir dos logs em logs/.",
        "A entrada é texto livre; o contrato vem da sessão e o thread_id é gerado pelo sistema.",
        "A saída é validada (src/schemas.py): resultado, fontes, suficiente.",
        "",
    ]
    for nome, log in logs.items():
        linhas += secao(nome, log)
    linhas += aprovacao_repetida(logs)
    destino = os.path.join(config.RAIZ, "docs", "io.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"{destino} gerado com {len(logs)} logs")
    exemplo = exemplo_readme(logs)
    if exemplo:
        preencher_readme(exemplo)


if __name__ == "__main__":
    main()
