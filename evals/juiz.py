"""Juiz LLM para uma propriedade sem gabarito: clareza da resposta para um
cliente leigo (rubrica em evals/dados_juiz/rubrica_clareza_v1.md). Saída
estruturada (JSON), critério binário. Validado em evals/validar_juiz.py."""
import json
import os
import re
from typing import Optional

RUBRICA_VERSAO = "1.0.0"
CAMINHO_RUBRICA = os.path.join(os.path.dirname(__file__), "dados_juiz", "rubrica_clareza_v1.md")


def _rubrica() -> str:
    with open(CAMINHO_RUBRICA, encoding="utf-8") as f:
        return f.read()


def _extrair_json(texto: str) -> Optional[dict]:
    try:
        return json.loads(texto)
    except (TypeError, json.JSONDecodeError):
        m = re.search(r"\{.*\}", texto or "", re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def julgar(cliente, modelo: str, mensagem: str, resposta: str) -> dict:
    """Devolve {"aprovado": bool|None, "motivo": str}. aprovado=None quando o
    juiz não devolveu JSON válido: conta como falha do juiz, nunca como nota."""
    try:
        r = cliente.chat.completions.create(
            model=modelo, temperature=0, max_tokens=300,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _rubrica()},
                {"role": "user", "content": f'Cliente: "{mensagem}"\nResposta do assistente: "{resposta}"'},
            ],
        )
        dado = _extrair_json(r.choices[0].message.content)
    except Exception as erro:  # rede, limite de taxa
        return {"aprovado": None, "motivo": f"erro_do_juiz: {type(erro).__name__}"}
    if not isinstance(dado, dict) or not isinstance(dado.get("aprovado"), bool):
        return {"aprovado": None, "motivo": "saida_invalida"}
    return {"aprovado": dado["aprovado"], "motivo": str(dado.get("motivo", ""))[:300]}
