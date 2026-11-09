import math
import os
import time
from collections import defaultdict, deque
from threading import Lock

from dotenv import load_dotenv

load_dotenv()

JANELA_SEGUNDOS = 3600
LIMITE_POR_IP = int(os.getenv("LIMITE_MENSAGENS_POR_IP", "20"))

_envios: dict[str, deque[float]] = defaultdict(deque)
_trava = Lock()


def registrar_envio(ip: str) -> int:
    """Registra uma mensagem do IP. Devolve 0 se aceitou, ou quantos segundos faltam para liberar."""
    agora = time.monotonic()
    with _trava:
        envios = _envios[ip]
        while envios and agora - envios[0] > JANELA_SEGUNDOS:
            envios.popleft()
        if len(envios) >= LIMITE_POR_IP:
            return math.ceil(JANELA_SEGUNDOS - (agora - envios[0]))
        envios.append(agora)
        return 0