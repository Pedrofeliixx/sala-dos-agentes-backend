import os
import queue
from pathlib import Path


from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.sessoes import SESSOES, Sessao, criar_sessao, processar_mensagem

load_dotenv()

app = FastAPI(title="Sala dos Agentes - Backend", version="0.2.0")

ORIGENS_PERMITIDAS = [
    origem.strip()
    for origem in os.getenv("ORIGENS_CORS", "http://localhost:3000").split(",")
    if origem.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

PAGINA_TESTE = Path(__file__).parent / "pagina_teste.html"


class NovaMensagem(BaseModel):
    texto: str


def buscar_sessao(conversa_id: str) -> Sessao:
    sessao = SESSOES.get(conversa_id)
    if sessao is None:
        raise HTTPException(status_code=404, detail="conversa não encontrada")
    return sessao


@app.get("/saude")
def saude():
    return {
        "status": "ok",
        "chave_api_configurada": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


@app.post("/conversas", status_code=201)
def nova_conversa():
    sessao = criar_sessao()
    return {"conversa": sessao.id}


@app.post("/conversas/{conversa_id}/mensagens", status_code=202)
def enviar_mensagem(conversa_id: str, mensagem: NovaMensagem, tarefas: BackgroundTasks):
    sessao = buscar_sessao(conversa_id)
    if sessao.processando:
        raise HTTPException(status_code=409, detail="a conversa ainda está processando a mensagem anterior")
    sessao.processando = True
    tarefas.add_task(processar_mensagem, sessao, mensagem.texto)
    return {"conversa": sessao.id, "status": "recebida"}


@app.get("/conversas/{conversa_id}")
def ver_conversa(conversa_id: str):
    sessao = buscar_sessao(conversa_id)
    return {"conversa": sessao.id, "processando": sessao.processando, "historico": sessao.historico}


@app.get("/conversas/{conversa_id}/eventos")
def transmitir_eventos(conversa_id: str):
    sessao = buscar_sessao(conversa_id)

    def gerar():
        while True:
            try:
                evento = sessao.fila.get(timeout=15)
            except queue.Empty:
                yield ": ping\n\n"
                continue
            dados = evento.model_dump_json(by_alias=True, exclude_none=True)
            yield f"id: {evento.id}\ndata: {dados}\n\n"

    return StreamingResponse(
        gerar(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )

@app.get("/teste", response_class=HTMLResponse, include_in_schema=False)
def pagina_teste():
    return PAGINA_TESTE.read_text(encoding="utf-8")