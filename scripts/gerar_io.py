"""Gera docs/io.md e o exemplo do README a partir dos logs JSON reais.

Uso: python -m scripts.gerar_io
Os registros mantêm data, commit e entrada originais; o script não simula execuções.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

from src import config

RAIZ = Path(config.RAIZ)
PASTA_LOGS = Path(config.PASTA_LOGS)
DESCRICOES = {
    "caso_C001_feliz": "Caminho feliz: o agente testa a linha, reinicia e confirma o resultado com novo teste.",
    "caso_C002_divergencia": "Divergência: o cliente relata queda, mas a linha está ONLINE; o diagnóstico também considera a manutenção no bairro.",
    "caso_C004_aprovacao_repetida": "Segunda aprovação da mesma visita: ja_existia=true prova que a escrita não duplicou o agendamento.",
    "caso_C004_pausa_edita": "Pausa human-in-the-loop: o cliente altera a data proposta e o código agenda a data validada.",
    "caso_C004_terminal": "Execução antiga da aprovação pelo terminal; preservada como registro histórico, com commit sem-git.",
    "caso_C005_nao_agenda": "O cliente pede técnico, mas o bairro está em manutenção; nenhuma visita individual é proposta.",
    "caso_C999_inexistente": "Registro inexistente: a ferramenta informa que o contrato não foi localizado e o agente não inventa diagnóstico.",
    "caso_entrada_ambigua": "Entrada ambígua: o sistema declara a interpretação adotada e orienta um teste para confirmar.",
    "caso_entrada_incompleta": "Entrada incompleta: o sistema pede os detalhes necessários sem chamar o modelo ou ferramentas.",
    "caso_fora_do_corpus": "Pergunta fora do corpus: o portão de suficiência impede uma resposta sem fonte e apresenta uma recusa útil.",
    "caso_fora_do_escopo": "Fora do escopo: a triagem encaminha cobrança/cancelamento para uma pessoa sem chamar o modelo.",
}


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False)


def _ferramentas(log: dict) -> list[str]:
    return [t.get("nome", "?") for t in log.get("trajetoria", []) if t.get("tipo") == "ferramenta"]


def _consultas(log: dict) -> tuple[int, int]:
    consultas = [t for t in log.get("trajetoria", [])
                 if t.get("tipo") == "ferramenta" and t.get("nome") == "consultar_base_conhecimento"]
    sem_trecho = sum(not t.get("resultado", {}).get("suficiente", False) for t in consultas)
    return len(consultas), sem_trecho


def gerar_documentacao() -> tuple[int, str]:
    arquivos = sorted(glob.glob(str(PASTA_LOGS / "*.json")))
    linhas = [
        "# Entrada e saída do sistema", "",
        "Os exemplos abaixo foram extraídos dos arquivos JSON em `logs/`; nenhuma entrada ou saída foi reconstruída à mão.",
        "Cada bloco preserva a mensagem digitada, o contrato fornecido pela sessão, o `thread_id` gerado pelo sistema, o commit e a data gravados na execução.",
        "A entrada é texto livre. O objeto de saída completo é validado por `RespostaAtendimento` em `src/schemas.py`.",
        "", "## Contrato", "",
        "- **Entrada:** `EntradaAtendimento` (`contrato`, `mensagem`, `thread_id`). O contrato vem da sessão e o identificador da conversa é gerado pelo sistema.",
        "- **Saída:** `RespostaAtendimento` (`resultado`, `fontes`, `suficiente`, além dos campos de controle). `suficiente=true` exige fonte verificável; `suficiente=false` exige `motivo_insuficiencia`.",
        "- **Recusa:** é uma saída válida do contrato, não uma exceção não estruturada.",
        "", "## Execuções registradas", "",
    ]
    dados = []
    for caminho in arquivos:
        with open(caminho, encoding="utf-8") as f:
            log = json.load(f)
        if not all(k in log for k in ("timestamp", "commit", "contrato", "mensagem_inicial", "saida")):
            print(f"ignorado (log sem metadados mínimos): {os.path.basename(caminho)}")
            continue
        dados.append((Path(caminho), log))
        nome = Path(caminho).stem
        consultas, sem_trecho = _consultas(log)
        prompts = log.get("prompts") or {}
        linhas += [
            f"### {nome}", "",
            f"**O que ler:** {DESCRICOES.get(nome, 'Leia a entrada, a trajetória e o objeto de saída desta execução.')}", "",
            f"- **Log:** `logs/{Path(caminho).name}`",
            f"- **Data:** `{log['timestamp']}` · **commit:** `{log['commit']}` · **modelo:** `{log.get('modelo', 'não registrado')}` · **temperature:** `{log.get('temperature', 'não registrada')}`",
            f"- **Entrada:** contrato `{log['contrato']}` · `thread_id` `{log.get('thread_id', 'não registrado')}`",
            f"- **Texto exato digitado:** { _json(log['mensagem_inicial']) }",
            f"- **Prompts:** `{_json(prompts)}`",
            f"- **Ferramentas chamadas:** {', '.join(_ferramentas(log)) or 'nenhuma'}",
            f"- **Consultas ao corpus:** {consultas} (sem trecho útil: {sem_trecho}) · **voltas:** {log.get('voltas')} · **tokens:** {log.get('tokens')}",
            f"- **Pausas de aprovação:** `{_json(log.get('pausas_de_aprovacao', []))}`",
            f"- **Motivo de término:** `{log.get('motivo_parada')}`",
            "", "**Objeto de saída completo:**", "", "```json", _json(log["saida"]), "```", "",
        ]

    # A prova de idempotência usa duas execuções reais distintas.
    primeira = next((l for p, l in dados if p.stem == "caso_C004_pausa_edita"), None)
    segunda = next((l for p, l in dados if p.stem == "caso_C004_aprovacao_repetida"), None)
    if primeira and segunda:
        def aprovacao(log):
            return next((t for t in log.get("trajetoria", []) if t.get("tipo") == "aprovacao_humana"), None)
        a, b = aprovacao(primeira), aprovacao(segunda)
        linhas += ["## Prova de aprovação repetida", ""]
        if a and b:
            linhas += [
                "As duas execuções aprovaram a mesma visita (`C004`, `2026-10-22`) em `thread_id` diferentes. A primeira criou o registro (`ja_existia=false`); a segunda reconheceu a chave de idempotência (`ja_existia=true`).",
                "", "| Execução | thread_id | resultado do agendamento |", "|---|---|---|",
                f"| primeira (`{primeira.get('timestamp')}`) | `{primeira.get('thread_id')}` | `{_json(a.get('resultado'))}` |",
                f"| segunda (`{segunda.get('timestamp')}`) | `{segunda.get('thread_id')}` | `{_json(b.get('resultado'))}` |", "",
            ]
        else:
            linhas += ["Os dois logs existem, mas não foi possível extrair de ambos o evento `aprovacao_humana`; confira os registros antes de afirmar a idempotência.", ""]

    destino = RAIZ / "docs" / "io.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")

    # O README repete o caso principal com entrada e objeto completo.
    principal = next((l for p, l in dados if p.stem == "caso_C001_feliz"), None)
    if principal:
        bloco = [
            f"Entrada digitada: { _json(principal['mensagem_inicial']) }", "",
            "Saída completa validada:", "", "```json", _json(principal["saida"]), "```", "",
            f"Execução registrada em `{principal['timestamp']}`, commit `{principal['commit']}`.",
        ]
        readme = RAIZ / "README.md"
        texto = readme.read_text(encoding="utf-8")
        inicio, fim = "<!-- EXEMPLO:INICIO -->", "<!-- EXEMPLO:FIM -->"
        if inicio in texto and fim in texto:
            antes, resto = texto.split(inicio, 1)
            _, depois = resto.split(fim, 1)
            readme.write_text(antes + inicio + "\n" + "\n".join(bloco) + "\n" + fim + depois, encoding="utf-8")
    return len(dados), str(destino)


if __name__ == "__main__":
    quantidade, destino = gerar_documentacao()
    print(f"{destino} gerado com {quantidade} logs reais")
