import os
from datetime import datetime, timezone
from threading import Lock

from dotenv import load_dotenv

load_dotenv()

# Preços do Claude Haiku 4.5 em US$ por milhão de tokens.
# Fonte: platform.claude.com/docs/en/about-claude/pricing (conferido em 03/11/2026).
PRECO_ENTRADA_POR_MILHAO = 1.00
PRECO_SAIDA_POR_MILHAO = 5.00
TETO_DIARIO_USD = float(os.getenv("TETO_GASTO_DIARIO_USD", "1.00"))

_trava = Lock()
_estado = {"dia": "", "gasto_usd": 0.0}


def _zerar_se_virou_o_dia() -> None:
    hoje = datetime.now(timezone.utc).date().isoformat()
    if _estado["dia"] != hoje:
        _estado["dia"] = hoje
        _estado["gasto_usd"] = 0.0


def registrar_uso(uso) -> float:
    """Soma o custo de uma chamada ao modelo e devolve o gasto do dia em US$."""
    custo = (uso.input_tokens * PRECO_ENTRADA_POR_MILHAO + uso.output_tokens * PRECO_SAIDA_POR_MILHAO) / 1_000_000
    with _trava:
        _zerar_se_virou_o_dia()
        _estado["gasto_usd"] += custo
        return _estado["gasto_usd"]


def teto_atingido() -> bool:
    with _trava:
        _zerar_se_virou_o_dia()
        return _estado["gasto_usd"] >= TETO_DIARIO_USD