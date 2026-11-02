import json
import unicodedata
from functools import lru_cache
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent / "data" / "catalogo.json"
LIMITE = 8


def _normalizar(texto):
    """Minúsculas e sem acentos, para 'sao paulo' achar 'São Paulo'."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acentos.casefold().strip()


@lru_cache(maxsize=1)
def _carregar():
    with open(ARQUIVO, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return {
        tipo: [(nome, _normalizar(nome)) for nome in nomes]
        for tipo, nomes in dados.items()
    }


def buscar_sugestoes(tipo, termo):
    catalogo = _carregar()
    if tipo not in catalogo:
        return []

    alvo = _normalizar(termo)
    if len(alvo) < 2:
        return []

    comecam, contem = [], []
    for nome, normalizado in catalogo[tipo]:
        if normalizado.startswith(alvo):
            comecam.append(nome)
        elif alvo in normalizado:
            contem.append(nome)
    return (comecam + contem)[:LIMITE]