from app.agentes.base import Agente
from app.tools.pedidos import consultar_pedido

SYSTEM = """Você é o agente de Pedidos da Loja Exemplo, uma loja fictícia.
Sua função é informar a situação, o rastreio e a previsão de entrega de pedidos.
- Quando o cliente informar o número do pedido, use a ferramenta consultar_pedido.
- Quando o cliente não informar o número, peça o número do pedido.
- Responda somente com os dados que a ferramenta devolveu.
- Situação "entregue": informe que o pedido foi entregue e a data da entrega.
- Situação "em transporte": informe a transportadora, o código de rastreio e a previsão de entrega.
- Situação "cancelado": informe que o pedido está cancelado e ofereça falar com um atendente.
- Quando o pedido não for encontrado: peça para o cliente conferir o número ou ofereça falar com um atendente.
Formato: texto simples, sem markdown e sem emoji, em até 3 frases, em português."""

FERRAMENTAS = [
    {
        "name": "consultar_pedido",
        "description": (
            "Consulta um pedido pelo número e devolve situação, transportadora, "
            "código de rastreio, previsão de entrega e data de entrega."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "numero": {
                    "type": "string",
                    "description": "Número do pedido, só dígitos. Exemplo: 50002",
                }
            },
            "required": ["numero"],
        },
    }
]

AGENTE_PEDIDOS = Agente(
    id="pedidos",
    descricao="Informa a situação, o rastreio e a previsão de entrega de pedidos a partir do número do pedido.",
    system=SYSTEM,
    ferramentas=FERRAMENTAS,
    executores={"consultar_pedido": consultar_pedido},
    objetos={"consultar_pedido": "arquivo"},
)