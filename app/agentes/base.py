import json
import time
from dataclasses import dataclass, field
from typing import Callable

from anthropic import Anthropic
from dotenv import load_dotenv

from app.eventos import Emissor

load_dotenv()

cliente = Anthropic()

MODELO_ECONOMICO = "claude-haiku-4-5-20251001"  # confira o ID atual em docs.claude.com (Models)


@dataclass
class Agente:
    id: str
    descricao: str
    system: str
    ferramentas: list[dict]
    executores: dict[str, Callable[..., dict]]
    objetos: dict[str, str] = field(default_factory=dict)
    modelo: str = MODELO_ECONOMICO
    max_tokens: int = 500
    max_voltas: int = 5


def executar_ferramenta(agente: Agente, nome: str, parametros: dict) -> dict:
    executor = agente.executores.get(nome)
    if executor is None:
        return {"ok": False, "status": "erro", "mensagem": f"ferramenta desconhecida: {nome}"}
    try:
        return executor(**parametros)
    except Exception as erro:
        return {"ok": False, "status": "erro", "mensagem": str(erro)}


def rodar_agente(agente: Agente, mensagem: str, emissor: Emissor) -> dict:
    mensagens = [{"role": "user", "content": mensagem}]

    for volta in range(1, agente.max_voltas + 1):
        resposta = cliente.messages.create(
            model=agente.modelo,
            max_tokens=agente.max_tokens,
            system=agente.system,
            tools=agente.ferramentas,
            messages=mensagens,
        )
        print(
            f"  [{agente.id} volta {volta}] stop_reason={resposta.stop_reason} "
            f"tokens entrada={resposta.usage.input_tokens} saída={resposta.usage.output_tokens}"
        )

        if resposta.stop_reason != "tool_use":
            emissor.emitir("resposta_agente", agente=agente.id, status="ok")
            texto = "".join(bloco.text for bloco in resposta.content if bloco.type == "text")
            return {"status": "ok", "texto": texto}

        mensagens.append({"role": "assistant", "content": resposta.content})

        resultados = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue
            print(f"  -> {bloco.name}({bloco.input})")
            inicio = time.perf_counter()
            resultado = executar_ferramenta(agente, bloco.name, bloco.input)
            duracao_ms = round((time.perf_counter() - inicio) * 1000)
            emissor.emitir(
                "ferramenta",
                agente=agente.id,
                ferramenta=agente.objetos.get(bloco.name, bloco.name),
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

    emissor.emitir("resposta_agente", agente=agente.id, status="erro")
    return {"status": "erro", "texto": "Não consegui concluir o atendimento. Vou te passar para um atendente."}