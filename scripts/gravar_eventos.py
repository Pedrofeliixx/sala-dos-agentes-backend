"""Grava eventos reais dos agentes em docs/exemplos/eventos-reais.json para o front-end."""
import json
from datetime import date
from pathlib import Path

from app.conversa import rodar_conversa
from app.eventos import Emissor

SAIDA = Path("docs/exemplos/eventos-reais.json")

CASOS = [
    ("com ferramenta (pedidos)", ["Cadê meu pedido 50002?"]),
    ("dado faltando e memória (notas)", ["Me manda minha nota fiscal?", "É a 1001"]),
    ("fora do escopo", ["Qual o horário de funcionamento da loja?"]),
]


def gravar_caso(caso: str, mensagens: list[str]) -> dict:
    emissor = Emissor()
    historico: list[dict] = []
    for texto in mensagens:
        print(f"\n[{caso}] CLIENTE: {texto}")
        resposta = rodar_conversa(texto, emissor, historico)
        print(f"[{caso}] AGENTE: {resposta}")
        historico.append({"role": "user", "content": texto})
        historico.append({"role": "assistant", "content": resposta})
    return {
        "conversa": emissor.conversa,
        "caso": caso,
        "historico": historico,
        "eventos": [e.model_dump(by_alias=True, exclude_none=True) for e in emissor.eventos],
    }


if __name__ == "__main__":
    conversas = [gravar_caso(caso, mensagens) for caso, mensagens in CASOS]
    dados = {
        "origem": f"Execução real do back-end em {date.today():%d/%m/%Y} (py -m scripts.gravar_eventos), "
                  "agentes reais com Claude API sobre dados fictícios da Loja Exemplo. Formato EventoSala.",
        "conversas": conversas,
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(c["eventos"]) for c in conversas)
    print(f"\nGravado em {SAIDA}: {len(conversas)} conversas, {total} eventos")
    for c in conversas:
        print(f"  {c['caso']}: {len(c['eventos'])} eventos")