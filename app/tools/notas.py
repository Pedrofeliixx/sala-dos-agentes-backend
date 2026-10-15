import json
from pathlib import Path

CAMINHO_NOTAS = Path(__file__).parent.parent / "dados" / "notas.json"


def buscar_nota(numero: str) -> dict:
    with open(CAMINHO_NOTAS, encoding="utf-8") as arquivo:
        notas = json.load(arquivo)

    for nota in notas:
        if nota["numero"] == numero:
            return {"ok": True, "status": "ok", "nota": nota}

    return {"ok": False, "status": "nao_encontrado", "numero": numero}    # dicionário do "não achou"