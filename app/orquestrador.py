from app.agentes.base import MODELO_ECONOMICO, cliente
from app.agentes.notas import AGENTE_NOTAS
from app.agentes.pedidos import AGENTE_PEDIDOS
from app.eventos import Emissor

ORQUESTRADOR_ID = "recepcao"
MENSAGEM_TRANSFERENCIA = "Não consegui concluir o atendimento. Vou te passar para um atendente."
MENSAGEM_FORA_DO_ESCOPO = "Por aqui eu atendo notas fiscais e pedidos. Quer falar com um atendente?"
SEM_ESPECIALISTA = "nenhum"

ESPECIALISTAS = {agente.id: agente for agente in [AGENTE_NOTAS, AGENTE_PEDIDOS]}

SYSTEM_RECEPCAO = """Você é a recepção da Loja Exemplo, uma loja fictícia.
Sua função é escolher qual especialista atende a mensagem do cliente, sempre usando a ferramenta encaminhar.
- Escolha o especialista do pedido principal do cliente: o que ele quer receber agora, e não o contexto que ele conta.
- Encaminhe mesmo quando faltar algum dado, como o número da nota ou do pedido. Quem pede os dados é o especialista.
- Quando a mensagem não for sobre o assunto de nenhum especialista, escolha "nenhum"."""


def montar_ferramenta_encaminhar() -> dict:
    lista = "\n".join(f"- {agente.id}: {agente.descricao}" for agente in ESPECIALISTAS.values())
    lista += f"\n- {SEM_ESPECIALISTA}: a mensagem não é sobre o assunto de nenhum especialista."
    return {
        "name": "encaminhar",
        "description": "Encaminha a mensagem do cliente para o especialista certo. Opções:\n" + lista,
        "input_schema": {
            "type": "object",
            "properties": {
                "especialista": {
                    "type": "string",
                    "enum": list(ESPECIALISTAS.keys()) + [SEM_ESPECIALISTA],
                    "description": "Id do especialista que deve atender.",
                },
                "motivo": {
                    "type": "string",
                    "description": "Em poucas palavras, por que este especialista.",
                },
            },
            "required": ["especialista", "motivo"],
        },
    }


FERRAMENTA_ENCAMINHAR = montar_ferramenta_encaminhar()


def rotear(mensagem: str) -> dict:
    resposta = cliente.messages.create(
        model=MODELO_ECONOMICO,
        max_tokens=300,
        system=SYSTEM_RECEPCAO,
        tools=[FERRAMENTA_ENCAMINHAR],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": mensagem}],
    )
    print(
        f"  [recepcao] stop_reason={resposta.stop_reason} "
        f"tokens entrada={resposta.usage.input_tokens} saída={resposta.usage.output_tokens}"
    )

    for bloco in resposta.content:
        if bloco.type == "tool_use" and bloco.name == "encaminhar":
            especialista = bloco.input.get("especialista")
            motivo = bloco.input.get("motivo", "")
            print(f"  [recepcao] -> {especialista} ({motivo})")
            if especialista == SEM_ESPECIALISTA:
                return {"tipo": "fora_do_escopo", "texto": MENSAGEM_FORA_DO_ESCOPO}
            if especialista not in ESPECIALISTAS:
                return {"tipo": "erro"}
            return {"tipo": "encaminhar", "especialista": especialista}

    return {"tipo": "erro"}


def conferir(resultado: dict, emissor: Emissor) -> tuple[str, str]:
    aprovado = resultado["status"] == "ok" and resultado["texto"].strip() != ""
    emissor.emitir("conferencia", agente=ORQUESTRADOR_ID, status="ok" if aprovado else "erro")
    if aprovado:
        return resultado["texto"], "ok"
    return MENSAGEM_TRANSFERENCIA, "erro"