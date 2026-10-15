from app.agentes.base import rodar_agente
from app.eventos import Emissor
from app.orquestrador import (
    ESPECIALISTAS,
    MENSAGEM_TRANSFERENCIA,
    ORQUESTRADOR_ID,
    conferir,
    rotear,
)


def rodar_conversa(mensagem: str, emissor: Emissor) -> str:
    emissor.emitir("cliente_chegou", agente=ORQUESTRADOR_ID)

    try:
        rota = rotear(mensagem)

        if rota["tipo"] == "encaminhar":
            especialista = ESPECIALISTAS[rota["especialista"]]
            emissor.emitir("delegacao", agente=especialista.id)
            resultado = rodar_agente(especialista, mensagem, emissor)
            resposta, status = conferir(resultado, emissor)
        elif rota["tipo"] == "fora_do_escopo":
            resposta, status = rota["texto"], "fora_do_escopo"
        else:
            resposta, status = MENSAGEM_TRANSFERENCIA, "erro"

    except Exception as erro:
        print(f"  ERRO: {erro}")
        resposta, status = MENSAGEM_TRANSFERENCIA, "erro"

    emissor.emitir("resposta_cliente", agente=ORQUESTRADOR_ID, status=status)
    emissor.emitir("conversa_encerrada")
    return resposta


if __name__ == "__main__":
    perguntas = [
        "Oi, preciso da nota fiscal 1001.",
        "Cadê meu pedido 50002?",
        "Me manda minha nota fiscal?",
        "Qual o horário de funcionamento da loja?",
        "Meu pedido 50001 chegou, mas preciso da nota fiscal dele.",
    ]
    for pergunta in perguntas:
        print(f"\nCLIENTE: {pergunta}")
        emissor = Emissor()
        resposta = rodar_conversa(pergunta, emissor)
        print(f"AGENTE: {resposta}")
        print(f"  ({len(emissor.eventos)} eventos: {[e.tipo for e in emissor.eventos]})")