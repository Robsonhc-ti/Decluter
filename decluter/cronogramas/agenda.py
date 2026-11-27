from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from .models import Cronograma, EtapaCronograma, SessaoEstudo
from .planejamento import (
    interpretar_minutos,
    planejar_etapas,
    planejar_reposicao,
)


@transaction.atomic
def agendar_pendentes(cronograma):
    """Cria sessões para etapas sem agenda; erros de planejamento cabem ao chamador."""
    cronograma = Cronograma.objects.select_for_update().get(pk=cronograma.pk)
    etapas = list(
        EtapaCronograma.objects.filter(
            cronograma=cronograma,
            sessoes__isnull=True,
        ).order_by("ordem")
    )
    if not etapas:
        return []

    carga = defaultdict(int)
    sessoes_existentes = (
        SessaoEstudo.objects.filter(etapa__cronograma=cronograma)
        .values_list("data", "minutos")
    )
    for data, minutos in sessoes_existentes:
        carga[data] += minutos

    plano = planejar_etapas(
        [(etapa.pk, etapa.minutos_estimados) for etapa in etapas],
        inicio=max(cronograma.data_inicio, timezone.localdate()),
        dias_semana=cronograma.dias_estudo,
        capacidade=interpretar_minutos(cronograma.tempo_por_dia),
        carga=carga,
    )
    return SessaoEstudo.objects.bulk_create(
        [
            SessaoEstudo(etapa_id=etapa_id, data=data, minutos=minutos)
            for etapa_id, data, minutos in plano
        ]
    )


@transaction.atomic
def replanejar_atrasos(cronograma, hoje=None):
    hoje = hoje or timezone.localdate()
    sessoes = SessaoEstudo.objects.select_for_update(of=("self",)).filter(
        etapa__cronograma=cronograma
    )
    atrasadas = list(
        sessoes.filter(concluida=False, data__lt=hoje)
        .select_related("etapa")
        .order_by("etapa__ordem", "data", "pk")
    )
    if not atrasadas:
        return

    minutos_por_etapa = defaultdict(int)
    etapas_afetadas = {}
    for sessao in atrasadas:
        minutos_por_etapa[sessao.etapa_id] += sessao.minutos
        etapas_afetadas[sessao.etapa_id] = sessao.etapa

    futuras = list(sessoes.filter(data__gte=hoje))
    carga = defaultdict(int)
    existentes_por_etapa_data = defaultdict(list)
    for sessao in futuras:
        carga[sessao.data] += sessao.minutos
        if not sessao.concluida:
            existentes_por_etapa_data[(sessao.etapa_id, sessao.data)].append(sessao)

    reposicao = planejar_reposicao(
        list(minutos_por_etapa.items()),
        hoje=hoje,
        dias_semana=cronograma.dias_estudo,
        capacidade=interpretar_minutos(cronograma.tempo_por_dia),
        carga=carga,
    )

    SessaoEstudo.objects.filter(pk__in=[sessao.pk for sessao in atrasadas]).delete()

    novas = []
    for (etapa_id, data), minutos in reposicao.items():
        existentes = existentes_por_etapa_data.get((etapa_id, data))
        if existentes:
            sessao = existentes[0]
            sessao.minutos += minutos
            sessao.save(update_fields=["minutos", "atualizado_em"])
        else:
            novas.append(SessaoEstudo(etapa_id=etapa_id, data=data, minutos=minutos))

    if novas:
        SessaoEstudo.objects.bulk_create(novas)

    for etapa in etapas_afetadas.values():
        sincronizar_etapa(etapa)


def sincronizar_etapa(etapa):
    sessoes = etapa.sessoes.all()
    concluida = sessoes.exists() and not sessoes.filter(concluida=False).exists()
    if etapa.concluida != concluida:
        etapa.concluida = concluida
        etapa.save(update_fields=["concluida", "atualizado_em"])
    return etapa.concluida
