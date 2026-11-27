import logging

from celery import shared_task
from django.utils import timezone

from .models import Cronograma
from .services import MENSAGEM_FALHA_GERACAO, gerar_etapas_do_cronograma

logger = logging.getLogger(__name__)


@shared_task
def gerar_cronograma_task(cronograma_id):
    try:
        gerar_etapas_do_cronograma(cronograma_id)
    except Exception as erro:
        logger.error(
            "Erro inesperado na tarefa do cronograma %s (%s)",
            cronograma_id,
            type(erro).__name__,
        )
        Cronograma.objects.filter(pk=cronograma_id).update(
            status=Cronograma.Status.FALHOU,
            erro=MENSAGEM_FALHA_GERACAO,
            atualizado_em=timezone.now(),
        )
    return str(cronograma_id)