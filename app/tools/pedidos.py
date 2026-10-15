import json
from pathlib import Path

CAMINHO_PEDIDOS = Path(__file__).parent.parent / "dados" / "pedidos.json"


def consultar_pedido(numero: str) -> dict:
    with open(CAMINHO_PEDIDOS, encoding="utf-8") as arquivo:
        pedidos = json.load(arquivo)

    for pedido in pedidos:
        if pedido["numero"] == numero:
            return {"ok": True, "status": "ok", "pedido": pedido}

    return {"ok": False, "status": "nao_encontrado", "numero": numero}