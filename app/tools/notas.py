import json
from pathlib import Path

CAMINHO_NOTAS = Path(__file__).parent.parent / "dados" / "notas.json"


def buscar_nota(numero: str | None = None, pedido: str | None = None) -> dict:
    if not numero and not pedido:
        return {"ok": False, "status": "erro", "mensagem": "informe o número da nota ou do pedido"}

    with open(CAMINHO_NOTAS, encoding="utf-8") as arquivo:
        notas = json.load(arquivo)

    for nota in notas:
        if (numero and nota["numero"] == numero) or (pedido and nota["pedido"] == pedido):
            nota["segunda_via_disponivel"] = nota["link_pdf"] is not None
            return {"ok": True, "status": "ok", "nota": nota}

    return {"ok": False, "status": "nao_encontrado", "numero": numero, "pedido": pedido}