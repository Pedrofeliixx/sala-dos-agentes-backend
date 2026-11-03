import os
import time
from collections import defaultdict, deque
from threading import Lock

JANELA_SEGUNDOS = 3600
LIMITE_POR_IP = int(os.getenv("LIMITE_MENSAGENS_POR_IP", "20"))

_envios: dict[str, deque[float]] = defaultdict(deque)
_trava = Lock()


def registrar_envio(ip: str) -> bool:
    """Registra uma mensagem do IP. Devolve False se ele já usou o limite da última hora."""
    agora = time.monotonic()
    with _trava:
        envios = _envios[ip]
        while envios and agora - envios[0] > JANELA_SEGUNDOS:
            envios.popleft()
        if len(envios) >= LIMITE_POR_IP:
            return False
        envios.append(agora)
        return True