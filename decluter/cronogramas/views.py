import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .agenda import replanejar_atrasos, sincronizar_etapa
from .catalogo import buscar_sugestoes
from .forms import CronogramaForm, EnemForm, FaculdadeForm
from .models import Cronograma, EtapaCronograma, SessaoEstudo
from .services import MENSAGEM_FALHA_GERACAO
from .tasks import gerar_cronograma_task

logger = logging.getLogger(__name__)

TEMPO_LIMITE_GERACAO = timedelta(minutes=5)
MENSAGEM_GERACAO_TRAVADA = (
    "A geração está demorando mais do que o esperado. Você pode tentar novamente."
)


def _cronograma_travado(cronograma):
    return (
        cronograma.status == Cronograma.Status.GERANDO
        and cronograma.atualizado_em
        < timezone.now() - TEMPO_LIMITE_GERACAO
    )


def _estado_para_exibicao(cronograma):
    if _cronograma_travado(cronograma):
        return Cronograma.Status.FALHOU, MENSAGEM_GERACAO_TRAVADA
    return cronograma.status, cronograma.erro


def _enfileirar_cronograma(cronograma_id):
    try:
        gerar_cronograma_task.delay(str(cronograma_id))
    except Exception as erro:
        logger.error(
            "Falha ao enfileirar cronograma %s (%s)",
            cronograma_id,
            type(erro).__name__,
        )
        Cronograma.objects.filter(pk=cronograma_id).update(
            status=Cronograma.Status.FALHOU,
            erro=MENSAGEM_FALHA_GERACAO,
            atualizado_em=timezone.now(),
        )


def _salvar_e_enfileirar(cronograma):
    cronograma.status = Cronograma.Status.GERANDO
    cronograma.erro = ""
    cronograma.save()
    transaction.on_commit(
        lambda: _enfileirar_cronograma(cronograma.pk)
    )
    return redirect("cronogramas:detalhe", pk=cronograma.pk)


@login_required
def lista_view(request):
    cronogramas = Cronograma.objects.filter(usuario=request.user).order_by("-criado_em")
    return render(request, "cronogramas/lista.html", {"cronogramas": cronogramas})


@login_required
@require_http_methods(["GET", "POST"])
def excluir_view(request, pk):
    cronograma = get_object_or_404(
        Cronograma,
        pk=pk,
        usuario=request.user,
    )
    if request.method == "POST":
        nome = cronograma.nome
        cronograma.delete()
        messages.success(request, f"Cronograma '{nome}' excluído com sucesso.")
        return redirect("cronogramas:lista")

    return render(request, "cronogramas/excluir_confirmacao.html", {
        "cronograma": cronograma,
    })


@login_required
def criar_view(request):
    if request.method == "POST":
        form = CronogramaForm(request.POST)
        if form.is_valid():
            cronograma = form.save(commit=False)
            cronograma.usuario = request.user
            cronograma.tipo = Cronograma.Tipo.TEMA
            return _salvar_e_enfileirar(cronograma)
    else:
        form = CronogramaForm()

    return render(request, "cronogramas/criar.html", {"form": form})


@login_required
def criar_faculdade_view(request):
    if request.method == "POST":
        form = FaculdadeForm(request.POST)
        if form.is_valid():
            cronograma = form.save(commit=False)
            cronograma.usuario = request.user
            cronograma.tipo = Cronograma.Tipo.FACULDADE
            cronograma.instituicao = cronograma.instituicao.strip()
            cronograma.curso = cronograma.curso.strip()
            cronograma.nome = f"{cronograma.curso} — {cronograma.instituicao}"[:200]
            cronograma.tema = (
                f"Grade curricular de {cronograma.curso} "
                f"({cronograma.instituicao})"
            )[:200]
            return _salvar_e_enfileirar(cronograma)
    else:
        form = FaculdadeForm()

    return render(request, "cronogramas/criar_faculdade.html", {"form": form})


@login_required
def criar_enem_view(request):
    if request.method == "POST":
        form = EnemForm(request.POST)
        if form.is_valid():
            cronograma = form.save(commit=False)
            cronograma.usuario = request.user
            cronograma.tipo = Cronograma.Tipo.ENEM
            cronograma.nome = "Preparação para o ENEM"
            cronograma.tema = "ENEM: Matriz de Referência oficial"
            return _salvar_e_enfileirar(cronograma)
    else:
        form = EnemForm()

    return render(request, "cronogramas/criar_enem.html", {"form": form})


@login_required
def sugestoes_view(request):
    resultados = buscar_sugestoes(request.GET.get("tipo", ""), request.GET.get("q", ""))
    return JsonResponse({"resultados": resultados})


@login_required
@require_GET
def status_view(request, pk):
    cronograma = get_object_or_404(
        Cronograma,
        pk=pk,
        usuario=request.user,
    )
    status, erro = _estado_para_exibicao(cronograma)
    return JsonResponse({"status": status, "erro": erro})


@login_required
@require_POST
def tentar_novamente_view(request, pk):
    cronograma = get_object_or_404(
        Cronograma,
        pk=pk,
        usuario=request.user,
    )
    if (
        cronograma.status != Cronograma.Status.FALHOU
        and not _cronograma_travado(cronograma)
    ):
        messages.error(request, "Este cronograma não precisa de uma nova tentativa.")
        return redirect("cronogramas:detalhe", pk=cronograma.pk)

    cronograma.status = Cronograma.Status.GERANDO
    cronograma.erro = ""
    cronograma.save(update_fields=["status", "erro", "atualizado_em"])
    transaction.on_commit(
        lambda: _enfileirar_cronograma(cronograma.pk)
    )
    return redirect("cronogramas:detalhe", pk=cronograma.pk)


@login_required
def detalhe_view(request, pk):
    cronograma = get_object_or_404(
        Cronograma.objects.prefetch_related("etapas"),
        pk=pk,
        usuario=request.user,
    )
    if cronograma.status == Cronograma.Status.PRONTO:
        try:
            replanejar_atrasos(cronograma)
        except Exception as erro:
            logger.error(
                "Falha ao replanejar cronograma %s (%s)",
                cronograma.pk,
                type(erro).__name__,
            )

    cronograma.status, cronograma.erro = _estado_para_exibicao(cronograma)
    etapas = list(cronograma.etapas.all())
    sessoes = (
        SessaoEstudo.objects.filter(etapa__cronograma=cronograma)
        .select_related("etapa")
        .order_by("data", "etapa__ordem")
    )
    return render(request, "cronogramas/detalhe.html", {
        "cronograma": cronograma,
        "etapas": etapas,
        "sessoes": sessoes,
        "total": len(etapas),
        "concluidas": sum(1 for etapa in etapas if etapa.concluida),
    })


@login_required
@require_POST
def sessao_alternar_view(request, pk):
    sessao = get_object_or_404(
        SessaoEstudo.objects.select_related("etapa__cronograma"),
        pk=pk,
        etapa__cronograma__usuario=request.user,
    )
    sessao.concluida = not sessao.concluida
    sessao.save(update_fields=["concluida", "atualizado_em"])
    sincronizar_etapa(sessao.etapa)
    destino = request.POST.get("next", "")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)
    return redirect("dashboard")


@login_required
@require_POST
def etapa_alternar_view(request, pk):
    etapa = get_object_or_404(
        EtapaCronograma.objects.select_related("cronograma"),
        pk=pk,
        cronograma__usuario=request.user,
    )
    novo_estado = not etapa.concluida
    etapa.sessoes.update(
        concluida=novo_estado,
        atualizado_em=timezone.now(),
    )
    sincronizar_etapa(etapa)
    return redirect("cronogramas:detalhe", pk=etapa.cronograma_id)
