"""Núcleo do planejamento de estudos.

Funções puras (sem Django e sem banco), fáceis de testar. A camada que conversa
com o banco fica em agenda.py.
"""
import re
from collections import defaultdict
from datetime import timedelta
from itertools import islice

FATOR_PLANEJAMENTO = 0.75   # o plano usa só 75% do tempo diário; o resto é folga
TAMANHO_PEDACO = 15         # tamanho das sessões de reposição, em minutos
MIN_PEDACO = 5              # sobra menor que isso é somada ao pedaço anterior
MIN_SESSAO = 10             # não cria sessões minúsculas no plano inicial
JANELA_REPOSICAO = 14       # quantos dias de estudo à frente são comparados
LIMITE_DIAS = 730           # trava de segurança contra laços infinitos
DIAS_UTEIS = (0, 1, 2, 3, 4)  # segunda a sexta


class SemDiasDisponiveisError(Exception):
    """Não há dias de estudo suficientes para encaixar o conteúdo."""


def interpretar_minutos(texto, padrao=60):
    """Converte textos como '1h', '2 horas', '1h30', '45 min' em minutos (mínimo 30)."""
    t = (texto or "").lower().replace(",", ".")
    total = 0.0

    horas_e_minutos = re.search(r"(\d+)\s*h(?:oras?)?\s*(\d{1,2})\b", t)
    if horas_e_minutos:
        total = int(horas_e_minutos.group(1)) * 60 + int(horas_e_minutos.group(2))
    else:
        horas = re.search(r"(\d+(?:\.\d+)?)\s*h(?:oras?)?\b", t)
        minutos = re.search(r"(\d+)\s*m(?:in(?:utos?)?)?\b", t)
        if horas:
            total += float(horas.group(1)) * 60
        if minutos:
            total += int(minutos.group(1))

    if total == 0:
        solto = re.search(r"\d+(?:\.\d+)?", t)
        if solto:
            valor = float(solto.group())
            total = valor * 60 if valor <= 12 else valor

    if total == 0:
        total = padrao
    return int(max(30, min(total, 720)))


def dias_de_estudo(dias_semana, a_partir_de):
    """Gera, em ordem, as datas que caem nos dias da semana escolhidos (0=segunda)."""
    permitidos = set(dias_semana or ()) or set(DIAS_UTEIS)
    dia = a_partir_de
    for _ in range(LIMITE_DIAS):
        if dia.weekday() in permitidos:
            yield dia
        dia += timedelta(days=1)


def meta_diaria(capacidade):
    return max(MIN_SESSAO, int(capacidade * FATOR_PLANEJAMENTO))


def dividir(minutos, tamanho=TAMANHO_PEDACO):
    pedacos = [tamanho] * (minutos // tamanho)
    resto = minutos % tamanho
    if resto:
        if resto < MIN_PEDACO and pedacos:
            pedacos[-1] += resto
        else:
            pedacos.append(resto)
    return pedacos


def planejar_etapas(etapas, *, inicio, dias_semana, capacidade, carga=None):
    """Distribui as etapas em sequência pelos dias de estudo.

    etapas: lista de (etapa_id, minutos), na ordem de estudo.
    carga: minutos já ocupados por dia ({data: minutos}).
    Devolve uma lista de (etapa_id, data, minutos).
    """
    carga = defaultdict(int, carga or {})
    meta = meta_diaria(capacidade)
    dias = dias_de_estudo(dias_semana, inicio)
    dia = next(dias, None)
    sessoes = []

    for etapa_id, total in etapas:
        restante = total
        while restante > 0:
            if dia is None:
                raise SemDiasDisponiveisError("Não há dias de estudo suficientes.")
            livre = meta - carga[dia]
            if livre < min(MIN_SESSAO, restante):
                dia = next(dias, None)
                continue
            minutos = min(livre, restante)
            sessoes.append((etapa_id, dia, minutos))
            carga[dia] += minutos
            restante -= minutos
    return sessoes


def _dia_mais_livre(carga, capacidade, hoje, dias_semana, pedaco):
    dias = dias_de_estudo(dias_semana, hoje)
    janela = list(islice(dias, JANELA_REPOSICAO))
    cabem = [d for d in janela if capacidade - carga[d] >= pedaco]
    if cabem:
        # o mais livre; em caso de empate, o mais cedo
        return max(cabem, key=lambda d: (capacidade - carga[d], -d.toordinal()))
    for dia in dias:  # continua depois da janela, no primeiro dia que couber
        if capacidade - carga[dia] >= pedaco:
            return dia
    raise SemDiasDisponiveisError("Não há dias livres suficientes para reorganizar.")


def planejar_reposicao(atrasos, *, hoje, dias_semana, capacidade, carga=None):
    """Reparte o conteúdo atrasado em sessões menores, nos dias mais livres.

    atrasos: lista de (etapa_id, minutos_atrasados), na ordem das etapas.
    carga: minutos já ocupados por dia, de hoje em diante.
    Devolve {(etapa_id, data): minutos}. Nenhum dia passa da capacidade diária.
    """
    carga = defaultdict(int, carga or {})
    agenda = defaultdict(int)

    for etapa_id, minutos in atrasos:
        for pedaco in dividir(minutos):
            dia = _dia_mais_livre(carga, capacidade, hoje, dias_semana, pedaco)
            carga[dia] += pedaco
            agenda[(etapa_id, dia)] += pedaco
    return dict(agenda)