"""
Controles de segurança aplicados em código (docs/seguranca.md §3.2). Nenhum
deles depende do prompt: o texto injetado chega pelo mesmo canal do prompt,
então só um teste em código garante o limite.

  C1  canal_confere                 ASI03  o contrato só vale com o canal do titular
  C2  llm.verificar_host            ASI04  a chave só sai para o host permitido
  C3  verificar_afirmacao_de_agendamento  ASI09/ASI01  a resposta não pode
                                    dizer "agendada" sem agendamento na trajetória
  C4  agente_suspenso               ASI10  interruptor de suspensão
"""
import hmac
import os
import re
import sqlite3
from typing import List, Optional

from . import config, db

# --------------------------------------------------------------------- C1


def canal_confere(contrato: Optional[str], canal: Optional[str]) -> bool:
    """True só se o canal informado é o registrado para o contrato. Contrato
    inexistente, canal ausente e erro de banco dão False (fail-closed), e o
    chamador não consegue distinguir contrato inexistente de canal errado."""
    return canal_hash_confere(contrato, db.hash_canal(canal))


def canal_hash_confere(contrato: Optional[str], informado: Optional[str]) -> bool:
    """Mesma regra, com o hash do canal. É o que o grafo usa, para que o
    número em claro não entre no estado nem nos checkpoints."""
    esperado = hash_registrado(contrato)
    if not esperado or not informado:
        return False
    return hmac.compare_digest(esperado, informado)


def hash_registrado(contrato: Optional[str]) -> str:
    if not contrato:
        return ""
    try:
        conn = db.conectar()
        try:
            linha = conn.execute("SELECT canal_hash FROM canais WHERE contrato = ?",
                                 (contrato,)).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return ""
    return linha["canal_hash"] if linha else ""


# --------------------------------------------------------------------- C4


def agente_suspenso() -> bool:
    """Suspenso se existe o arquivo dados/SUSPENSO ou a variável
    AGENTE_SUSPENSO=1. Quem tem acesso de escrita ao ambiente do sistema
    suspende; remover o arquivo reativa."""
    return os.path.exists(config.CAMINHO_SUSPENSAO) or os.environ.get("AGENTE_SUSPENSO") == "1"


# --------------------------------------------------------------------- C3

PADRAO_AFIRMA_AGENDAMENTO = re.compile(
    r"\b(agendei|agendamos|agendou|agendad[ao]s?|marquei|marcamos|marcad[ao]s?)\b"
    r"|visita\s+(?:t[eé]cnica\s+)?(?:est[aá]|foi|ficou)\s+(?:confirmad|garantid)\w*"
    r"|t[eé]cnico\s+(?:vai|ir[aá])\s+(?:at[eé]\s+a\s+sua|na\s+sua)\s+casa",
    re.IGNORECASE,
)
PADRAO_NEGACAO = re.compile(
    r"\b(n[aã]o|nenhum\w*|nada)\b[^.!?\n]{0,40}\b(agend\w+|marc\w+)\b"
    r"|\b(agend\w+|marc\w+)\b[^.!?\n]{0,25}\b(n[aã]o|sem)\b"
    r"|\bse\s+(?:voc[eê]\s+)?(?:aprovar|confirmar)\b"
    r"|\bpara\s+(?:agendar|marcar)\b|\bposso\s+(?:agendar|marcar)\b",
    re.IGNORECASE,
)


def visita_agendada_na_trajetoria(trajetoria: List[dict]) -> bool:
    return any(
        t.get("tipo") == "aprovacao_humana"
        and t.get("decisao") in ("aprovar", "editar")
        and t.get("resultado", {}).get("status") == "AGENDADA"
        for t in trajetoria
    )


def verificar_afirmacao_de_agendamento(texto: str, trajetoria: List[dict]) -> Optional[str]:
    """Devolve o motivo da violação ou None. A resposta só pode afirmar
    agendamento se a trajetória tem um agendamento feito pelo nó de aprovação.
    Frases negativas ("não agendei", "nada foi agendado") passam."""
    if visita_agendada_na_trajetoria(trajetoria):
        return None
    for frase in re.split(r"(?<=[.!?])\s+|\n", texto or ""):
        if PADRAO_AFIRMA_AGENDAMENTO.search(frase) and not PADRAO_NEGACAO.search(frase):
            return "agendamento_afirmado_sem_registro"
    return None
