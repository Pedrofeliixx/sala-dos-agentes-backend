import os
import queue
from pathlib import Path


from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from app.gastos import teto_atingido
from app.limites import registrar_envio
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


LIMITE_CARACTERES = 500
LIMITE_MENSAGENS_POR_CONVERSA = 10


class NovaMensagem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    texto: str = Field(min_length=1, max_length=LIMITE_CARACTERES)


class Recusa(Exception):
    """Recusa com código estável no corpo. O front escolhe o texto que mostra."""

    def __init__(self, status: int, erro: str, **extras):
        self.status = status
        self.corpo = {"erro": erro, **extras}


@app.exception_handler(Recusa)
async def tratar_recusa(request: Request, recusa: Recusa):
    return JSONResponse(status_code=recusa.status, content=recusa.corpo)


@app.exception_handler(RequestValidationError)
async def tratar_texto_invalido(request: Request, erro: RequestValidationError):
    return JSONResponse(status_code=422, content={"erro": "texto_invalido"})


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
def enviar_mensagem(conversa_id: str, mensagem: NovaMensagem, tarefas: BackgroundTasks, request: Request):
    sessao = buscar_sessao(conversa_id)
    if teto_atingido():
        raise Recusa(503, "teto_diario")
    if len(sessao.historico) // 2 >= LIMITE_MENSAGENS_POR_CONVERSA:
        raise Recusa(429, "limite_conversa")
    if sessao.processando:
        raise HTTPException(status_code=409, detail="a conversa ainda está processando a mensagem anterior")
    ip = request.client.host if request.client else "desconhecido"
    espera = registrar_envio(ip)
    if espera:
        raise Recusa(429, "limite_ip", tentar_em_s=espera)
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