from datetime import datetime, timezone
from typing import Callable, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

TipoEvento = Literal[
    "cliente_chegou",
    "delegacao",
    "ferramenta",
    "resposta_agente",
    "conferencia",
    "resposta_cliente",
    "conversa_encerrada",
]
StatusEvento = Literal["ok", "erro", "nao_encontrado", "fora_do_escopo"]


class EventoSala(BaseModel):
    """Espelho do EventoSala do front (packages/schema/src/eventos.ts)."""

    id: str
    andar_id: str = Field(alias="andarId")
    ambiente: Literal["producao", "homolog"]
    ts: str
    conversa: str
    tipo: TipoEvento
    agente: Optional[str] = None
    ferramenta: Optional[str] = None
    status: Optional[StatusEvento] = None
    duracao_ms: Optional[int] = Field(default=None, alias="duracaoMs")


def imprimir_evento(evento: EventoSala) -> None:
    print("  EVENTO", evento.model_dump_json(by_alias=True, exclude_none=True))


class Emissor:
    def __init__(
        self,
        andar_id: str = "modelo",
        ambiente: str = "homolog",
        destino: Callable[[EventoSala], None] = imprimir_evento,
        conversa: Optional[str] = None,
    ):
        self.andar_id = andar_id
        self.ambiente = ambiente
        self.destino = destino
        self.conversa = conversa or uuid4().hex[:12]
        self.eventos: list[EventoSala] = []

    def emitir(
        self,
        tipo: TipoEvento,
        agente: Optional[str] = None,
        ferramenta: Optional[str] = None,
        status: Optional[StatusEvento] = None,
        duracao_ms: Optional[int] = None,
    ) -> EventoSala:
        evento = EventoSala(
            id=uuid4().hex,
            andarId=self.andar_id,
            ambiente=self.ambiente,
            ts=datetime.now(timezone.utc).isoformat(),
            conversa=self.conversa,
            tipo=tipo,
            agente=agente,
            ferramenta=ferramenta,
            status=status,
            duracaoMs=duracao_ms,
        )
        self.eventos.append(evento)
        self.destino(evento)
        return evento