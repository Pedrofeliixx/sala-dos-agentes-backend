from app.agentes.base import Agente
from app.tools.notas import buscar_nota

SYSTEM = """Você é o agente de Notas Fiscais da Loja Exemplo, uma loja fictícia.
Sua função é entregar a segunda via de notas fiscais.
- Quando o cliente informar o número da nota, use buscar_nota com o campo numero.
- Quando o cliente informar só o número do pedido, use buscar_nota com o campo pedido.
- Quando o cliente não informar nenhum dos dois, peça o número da nota ou do pedido.
- Responda somente com os dados que a ferramenta devolveu.
- Quando segunda_via_disponivel for true: informe número da nota, situação, valor, data de emissão e link do PDF.
- Quando segunda_via_disponivel for false: informe que a nota está cancelada e que não possui segunda via disponível, e ofereça falar com um atendente.
- Quando a nota não for encontrada: peça para o cliente conferir o número ou ofereça falar com um atendente.
Formato: texto simples, sem markdown e sem emoji, em até 3 frases, em português."""

FERRAMENTAS = [
    {
        "name": "buscar_nota",
        "description": (
            "Busca uma nota fiscal pelo número da nota ou pelo número do pedido "
            "e devolve situação, valor, data de emissão e link do PDF."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "numero": {
                    "type": "string",
                    "description": "Número da nota fiscal, só dígitos. Exemplo: 1001",
                },
                "pedido": {
                    "type": "string",
                    "description": "Número do pedido, só dígitos. Exemplo: 50001",
                },
            },
        },
    }
]

AGENTE_NOTAS = Agente(
    id="notas",
    descricao="Entrega a segunda via de notas fiscais a partir do número da nota ou do número do pedido.",
    system=SYSTEM,
    ferramentas=FERRAMENTAS,
    executores={"buscar_nota": buscar_nota},
    objetos={"buscar_nota": "arquivo"},
)