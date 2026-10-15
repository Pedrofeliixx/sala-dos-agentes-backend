from app.agentes.base import rodar_agente
from app.agentes.notas import AGENTE_NOTAS
from app.eventos import Emissor

ORQUESTRADOR_ID = "recepcao"


def rodar_conversa(mensagem: str, emissor: Emissor) -> str:
    emissor.emitir("cliente_chegou", agente=ORQUESTRADOR_ID)
    emissor.emitir("delegacao", agente=AGENTE_NOTAS.id)

    try:
        resultado = rodar_agente(AGENTE_NOTAS, mensagem, emissor)
        resposta = resultado["texto"]
        status = resultado["status"]
    except Exception as erro:
        print(f"  ERRO: {erro}")
        resposta = "Tive um problema técnico. Vou te passar para um atendente."
        status = "erro"

    emissor.emitir("resposta_cliente", agente=ORQUESTRADOR_ID, status=status)
    emissor.emitir("conversa_encerrada")
    return resposta


if __name__ == "__main__":
    perguntas = [
        "Oi, preciso da nota fiscal 1001.",
        "Quero a segunda via da nota 1003.",
        "Me manda minha nota fiscal?",
    ]
    for pergunta in perguntas:
        print(f"\nCLIENTE: {pergunta}")
        emissor = Emissor()
        resposta = rodar_conversa(pergunta, emissor)
        print(f"AGENTE: {resposta}")
        print(f"  ({len(emissor.eventos)} eventos)")