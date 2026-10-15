import json

import json
import time
from anthropic import Anthropic
from dotenv import load_dotenv

from app.tools.notas import buscar_nota

from app.eventos import Emissor

load_dotenv()

MODELO = "claude-haiku-4-5-20251001"  # confira o ID atual em docs.claude.com (Models)
MAX_VOLTAS = 5

SYSTEM = """Você é o agente de Notas Fiscais da Loja Exemplo, uma loja fictícia.
Sua função é entregar a segunda via de notas fiscais.
- Quando o cliente informar o número da nota, use a ferramenta buscar_nota.
- Quando o cliente não informar o número, peça o número da nota.
- Responda somente com os dados que a ferramenta devolveu.
- Quando segunda_via_disponivel for true: informe número da nota, situação, valor, data de emissão e link do PDF.
- Quando segunda_via_disponivel for false: informe que a nota está cancelada e que não possui segunda via disponível, e ofereça falar com um atendente.
- Quando a nota não for encontrada: peça para o cliente conferir o número ou ofereça falar com um atendente.
Formato: texto simples, sem markdown e sem emoji, em até 3 frases, em português."""

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

AGENTE_ID = "notas"
OBJETO_DA_FERRAMENTA = {"buscar_nota": "arquivo"}

cliente = Anthropic()


def executar_ferramenta(nome: str, parametros: dict) -> dict:
    executor = EXECUTORES.get(nome)
    if executor is None:
        return {"ok": False, "status": "erro", "mensagem": f"ferramenta desconhecida: {nome}"}
    try:
        return executor(**parametros)
    except Exception as erro:
        return {"ok": False, "status": "erro", "mensagem": str(erro)}


def rodar_agente_notas(mensagem: str, emissor: Emissor) -> str:
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
            emissor.emitir("resposta_agente", agente=AGENTE_ID, status="ok")
            return "".join(bloco.text for bloco in resposta.content if bloco.type == "text")

        mensagens.append({"role": "assistant", "content": resposta.content})

        resultados = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue
            print(f"  -> {bloco.name}({bloco.input})")
            inicio = time.perf_counter()
            resultado = executar_ferramenta(bloco.name, bloco.input)
            duracao_ms = round((time.perf_counter() - inicio) * 1000)
            emissor.emitir(
                "ferramenta",
                agente=AGENTE_ID,
                ferramenta=OBJETO_DA_FERRAMENTA.get(bloco.name, bloco.name),
                status=resultado["status"],
                duracao_ms=duracao_ms,
            )
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

    emissor.emitir("resposta_agente", agente=AGENTE_ID, status="erro")

    return "Não consegui concluir o atendimento. Vou te passar para um atendente."


