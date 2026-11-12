"""Demonstra gravação, efeito, remoção e varredura em diretório temporário."""
import json
import sqlite3
import tempfile
from pathlib import Path

from src import memoria
from scripts.varrer_contrato import varrer

CONTRATO = "DEMO-REMOVER"
HOJE = "2026-11-12"

with tempfile.TemporaryDirectory(prefix="demo_remocao_") as tmp:
    raiz = Path(tmp)
    memoria_db = raiz / "memoria.db"
    checkpoint_db = raiz / "checkpoints.db"
    logs = raiz / "logs"
    logs.mkdir()

    trajetoria = [{
        "tipo": "ferramenta", "nome": "testar_linha", "args": {"contrato": CONTRATO},
        "resultado": {"status": "OFFLINE", "sinal_dbm": -30.0, "falha_fisica_provavel": True},
    }]
    gravacao = memoria.gravar_atendimento(
        CONTRATO, HOJE, "Minha internet caiu e a luz do modem ficou vermelha.",
        trajetoria, caminho=str(memoria_db),
    )

    conn = sqlite3.connect(checkpoint_db)
    conn.execute("CREATE TABLE checkpoints (thread_id TEXT)")
    conn.execute("CREATE TABLE writes (thread_id TEXT)")
    conn.execute("INSERT INTO checkpoints VALUES (?)", (f"{CONTRATO}:abc12345",))
    conn.execute("INSERT INTO writes VALUES (?)", (f"{CONTRATO}:abc12345",))
    conn.commit(); conn.close()
    (logs / "execucao.json").write_text(
        json.dumps({"contrato": CONTRATO, "mensagem_inicial": "internet caiu"}), encoding="utf-8"
    )

    contexto_antes = memoria.montar_contexto(
        CONTRATO, "internet caiu luz vermelha", HOJE, caminho=str(memoria_db)
    )
    conn = sqlite3.connect(memoria_db)
    tamanho_episodio = conn.execute("SELECT length(texto) FROM episodica WHERE contrato=?", (CONTRATO,)).fetchone()[0]
    tamanho_fato = conn.execute("SELECT length(valor) FROM semantica WHERE contrato=?", (CONTRATO,)).fetchone()[0]
    conn.close()

    print("1. gravar")
    print("   resultado:", gravacao)
    print(f"   volume: 1 episódio ({tamanho_episodio} caracteres) + 1 fato semântico ({tamanho_fato} caracteres)")
    print("2. o comportamento mudou?")
    print("   contexto recupera histórico do titular:", bool(contexto_antes))
    print("3. varrer antes de remover")
    antes = varrer(CONTRATO, raiz)
    print(f"   {len(antes)} ocorrência(s)")
    for item in antes:
        print("  ", item)

    print("4. remover")
    removidos = memoria.remover_titular(CONTRATO, str(memoria_db), str(checkpoint_db), str(logs))
    print("  ", removidos)

    print("5. o comportamento voltou?")
    contexto_depois = memoria.montar_contexto(
        CONTRATO, "internet caiu luz vermelha", HOJE, caminho=str(memoria_db)
    )
    print("   memória devolve vazio:", not contexto_depois)

    print("6. varrer depois de remover")
    depois = varrer(CONTRATO, raiz)
    print(f"   {len(depois)} ocorrência(s)")
    for item in depois:
        print("  ", item)
    if depois or contexto_depois:
        raise SystemExit("A remoção não eliminou todos os dados ou o comportamento não foi revertido")
