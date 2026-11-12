"""
Instrumentação OpenTelemetry com as convenções semânticas GenAI
(docs/observabilidade.md §2).

Árvore de spans de uma execução:
  invoke_agent suporte_tecnico          raiz, uma por execução
    chat <modelo>                       a cada chamada ao modelo
    execute_tool <ferramenta>           a cada ferramenta tentada

Destino: arquivos JSON Lines em PASTA_TRACES, um por dia
(spans-AAAA-MM-DD.jsonl), uma linha por span. Cada linha tem trace_id,
span_id, parent_span_id, name, tempos em nanossegundos, status e attributes.
`evals/metricas.py` lê esses arquivos.
"""
import datetime
import json
import os
import threading
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from . import config

NOME_TRACER = "suporte_tecnico_domestico"
# Términos que são desfecho previsto do desenho, não falha do sistema.
TERMINOS_NORMAIS = {"resposta_final", "entrada_incompleta", "encaminhado_humano",
                    "aprovacao_expirada", "identidade_nao_verificada", "agente_suspenso"}


class ExportadorJsonl(SpanExporter):
    def __init__(self):
        self._trava = threading.Lock()

    def export(self, spans):
        pasta = config.PASTA_TRACES
        os.makedirs(pasta, exist_ok=True)
        with self._trava:
            for s in spans:
                dia = datetime.datetime.fromtimestamp(s.end_time / 1e9).date().isoformat()
                ctx = s.get_span_context()
                pai = s.parent.span_id if s.parent else None
                linha = {
                    "trace_id": f"{ctx.trace_id:032x}",
                    "span_id": f"{ctx.span_id:016x}",
                    "parent_span_id": f"{pai:016x}" if pai else None,
                    "name": s.name,
                    "start_time_unix_nano": s.start_time,
                    "end_time_unix_nano": s.end_time,
                    "status": s.status.status_code.name,
                    "attributes": dict(s.attributes or {}),
                    "events": [{"name": e.name, "time_unix_nano": e.timestamp,
                                "attributes": dict(e.attributes or {})} for e in s.events],
                    "resource": dict(s.resource.attributes),
                }
                with open(os.path.join(pasta, f"spans-{dia}.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


_provedor = None


def tracer():
    global _provedor
    if _provedor is None:
        _provedor = TracerProvider(resource=Resource.create({
            "service.name": "suporte-tecnico-domestico",
            "service.version": config.VERSAO_SISTEMA,
        }))
        _provedor.add_span_processor(SimpleSpanProcessor(ExportadorJsonl()))
    return _provedor.get_tracer(NOME_TRACER, config.VERSAO_SISTEMA)


def _json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False, default=str)


def raiz(thread_id: str, contrato: str):
    return tracer().start_as_current_span(
        f"invoke_agent {config.NOME_AGENTE}",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": config.NOME_AGENTE,
            "gen_ai.provider.name": config.PROVEDOR,
            "gen_ai.conversation.id": thread_id,
            "suporte.contrato": contrato,
            "suporte.versao_sistema": config.VERSAO_SISTEMA,
            "suporte.controles_ativos": config.CONTROLES_ATIVOS,
        },
    )


@contextmanager
def chat(modelo: str):
    with tracer().start_as_current_span(
        f"chat {modelo}",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": config.PROVEDOR,
            "gen_ai.request.model": modelo,
            "gen_ai.request.temperature": config.TEMPERATURE,
            "gen_ai.request.max_tokens": config.MAX_TOKENS_RESPOSTA,
        },
    ) as span:
        yield span


def anotar_chat(span, resp, modelo: str) -> None:
    span.set_attribute("gen_ai.response.model", modelo)
    span.set_attribute("gen_ai.usage.input_tokens", resp.tokens_entrada)
    span.set_attribute("gen_ai.usage.output_tokens", resp.tokens_saida)
    span.set_attribute("suporte.tokens_total", resp.tokens)
    span.set_attribute("gen_ai.response.finish_reasons",
                       ["tool_calls" if resp.tool_calls else "stop"])


@contextmanager
def ferramenta(nome: str, chamada_id: str = ""):
    with tracer().start_as_current_span(
        f"execute_tool {nome}",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": nome,
            "gen_ai.tool.call.id": chamada_id or "",
        },
    ) as span:
        yield span


def anotar_ferramenta(args: dict, resultado: dict) -> None:
    span = trace.get_current_span()
    span.set_attribute("gen_ai.tool.call.arguments", _json(args))
    span.set_attribute("gen_ai.tool.call.result", _json(resultado))
    erro = resultado.get("erro") if isinstance(resultado, dict) else None
    span.set_attribute("suporte.ferramenta.erro", bool(erro))
    if erro:
        span.set_attribute("error.type", str(erro))
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(erro)))
    if isinstance(resultado, dict) and "trechos" in resultado:
        span.set_attribute("suporte.trechos_ids", [t["id"] for t in resultado["trechos"]])


def fechar_raiz(span, registro: dict, prompts: dict, commit: str) -> None:
    """Atributos próprios da raiz: o que o §2.3 do enunciado pede para
    reconstruir a decisão só pelo trace."""
    saida = registro.get("saida") or {}
    traj = registro.get("trajetoria") or []
    trechos = sorted({i for t in traj if t.get("tipo") == "ferramenta"
                      and t["nome"] == "consultar_base_conhecimento"
                      for i in [x["id"] for x in t["resultado"].get("trechos", [])]})
    a = span.set_attribute
    a("suporte.motivo_termino", registro.get("motivo_parada") or "desconhecido")
    a("suporte.versao_sistema", config.VERSAO_SISTEMA)
    a("suporte.commit", commit)
    a("suporte.entrada", registro.get("mensagem_inicial", ""))
    a("suporte.saida", saida.get("resultado", ""))
    a("suporte.suficiente", bool(saida.get("suficiente")))
    a("suporte.encaminhar_humano", bool(saida.get("encaminhar_humano")))
    a("suporte.trechos_recuperados", trechos)
    a("suporte.prompt.sistema", f"{prompts['sistema']['arquivo']}@{prompts['sistema']['sha256']}")
    a("suporte.prompt.procedural", f"{prompts['procedural']['arquivo']}@{prompts['procedural']['sha256']}")
    a("suporte.voltas", registro.get("voltas") or 0)
    a("suporte.tokens_total", registro.get("tokens") or 0)
    a("suporte.segundos_ativos", registro.get("segundos_ativos") or 0.0)
    a("suporte.espera_humana_s", registro.get("espera_humana_s") or 0.0)
    a("suporte.ferramentas_chamadas", _json([t["nome"] for t in traj if t.get("tipo") == "ferramenta"]))
    motivo = registro.get("motivo_parada")
    if motivo not in TERMINOS_NORMAIS:
        span.set_status(trace.Status(trace.StatusCode.ERROR, motivo or "desconhecido"))
