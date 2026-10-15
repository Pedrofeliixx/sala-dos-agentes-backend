import queue
from dataclasses import dataclass, field
from uuid import uuid4

from app.conversa import rodar_conversa
from app.eventos import Emissor, EventoSala, imprimir_evento

LIMITE_HISTORICO = 10


@dataclass
class Sessao:
    id: str
    historico: list[dict] = field(default_factory=list)
    fila: queue.Queue = field(default_factory=queue.Queue)
    processando: bool = False


SESSOES: dict[str, Sessao] = {}


def criar_sessao() -> Sessao:
    sessao = Sessao(id=uuid4().hex[:12])
    SESSOES[sessao.id] = sessao
    return sessao


def processar_mensagem(sessao: Sessao, texto: str) -> None:
    def destino(evento: EventoSala) -> None:
        imprimir_evento(evento)
        sessao.fila.put(evento)

    emissor = Emissor(conversa=sessao.id, destino=destino)
    try:
        historico_recente = sessao.historico[-LIMITE_HISTORICO:]
        resposta = rodar_conversa(texto, emissor, historico_recente)
        sessao.historico.append({"role": "user", "content": texto})
        sessao.historico.append({"role": "assistant", "content": resposta})
    finally:
        sessao.processando = False