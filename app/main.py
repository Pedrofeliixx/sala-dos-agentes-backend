import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="Sala dos Agentes - Backend", version="0.1.0")


@app.get("/saude")
def saude():
    return {
        "status": "ok",
        "chave_api_configurada": bool(os.getenv("ANTHROPIC_API_KEY")),
    }