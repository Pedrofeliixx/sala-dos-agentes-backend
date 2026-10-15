import json

from anthropic import Anthropic
from dotenv import load_dotenv

from app.tools.notas import buscar_nota

load_dotenv()

MODELO = "claude-haiku-4-5-20251001"  # confira o ID atual em docs.claude.com (Models)
MAX_VOLTAS = 5

SYSTEM = """Você é o agente de Notas Fiscais da Loja Exemplo, uma loja fictícia.
Sua função é entregar a segunda via de notas fiscais.
- Quando o cliente informar o número da nota, use a ferramenta buscar_nota.
- Quando o cliente não informar o número, peça o número da nota.
- Responda somente com os dados que a ferramenta devolveu.
- Nota com situação "cancelada": informe que ela está cancelada e ofereça falar com um atendente.
- Nota não encontrada: peça para o cliente conferir o número ou ofereça falar com um atendente.
Responda em português, em até 3 frases.
- Texto simples, sem markdown e sem emoji.
- Resposta precisa conter numero da nota, situação, valor, data de emissão e link do PDF """

FERRAMENTAS = [
    {
        "name": "buscar_nota",
        "description": "Busca uma nota fiscal pelo número e devolve situação, valor, data de emissão e link do PDF.",
        "input_schema": {
            "type": "object",
            "properties": {
                "numero": {
                    "type": "string",
                    "description": "Número da nota fiscal, só dígitos. Exemplo: 1001",
                }
            },
            "required": ["numero"],
        },
    }
]

EXECUTORES = {"buscar_nota": buscar_nota}

cliente = Anthropic()


def executar_ferramenta(nome: str, parametros: dict) -> dict:
    executor = EXECUTORES.get(nome)
    if executor is None:
        return {"ok": False, "status": "erro", "mensagem": f"ferramenta desconhecida: {nome}"}
    try:
        return executor(**parametros)
    except Exception as erro:
        return {"ok": False, "status": "erro", "mensagem": str(erro)}


def rodar_agente_notas(mensagem: str) -> str:
    mensagens = [{"role": "user", "content": mensagem}]

    for volta in range(1, MAX_VOLTAS + 1):
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=500,
            system=SYSTEM,
            tools=FERRAMENTAS,
            messages=mensagens,
        )
        print(
            f"  [volta {volta}] stop_reason={resposta.stop_reason} "
            f"tokens entrada={resposta.usage.input_tokens} saída={resposta.usage.output_tokens}"
        )

        if resposta.stop_reason != "tool_use":
            return "".join(bloco.text for bloco in resposta.content if bloco.type == "text")

        mensagens.append({"role": "assistant", "content": resposta.content})

        resultados = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue
            print(f"  -> {bloco.name}({bloco.input})")
            resultado = executar_ferramenta(bloco.name, bloco.input)
            print(f"  <- status={resultado['status']}")
            resultados.append(
                {
                    "type": "tool_result",
                    "tool_use_id": bloco.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                    "is_error": resultado["status"] == "erro",
                }
            )

        mensagens.append({"role": "user", "content": resultados})

    return "Não consegui concluir o atendimento. Vou te passar para um atendente."


if __name__ == "__main__":
    perguntas = [
        "Oi, preciso da nota fiscal 1001.",
        "Quero a segunda via da nota 1003.",
        "Me manda minha nota fiscal?",
    ]
    for pergunta in perguntas:
        print(f"\nCLIENTE: {pergunta}")
        print(f"AGENTE: {rodar_agente_notas(pergunta)}")