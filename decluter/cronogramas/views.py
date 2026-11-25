from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .catalogo import buscar_sugestoes
from .forms import CronogramaForm, EnemForm, FaculdadeForm
from .models import Cronograma, EtapaCronograma
from .services import GeracaoCronogramaError, criar_cronograma_com_ia


def _gerar_e_redirecionar(request, cronograma, form, template):
    try:
        criar_cronograma_com_ia(cronograma)
    except GeracaoCronogramaError as erro:
        messages.error(request, str(erro))
        return render(request, template, {"form": form})
    return redirect("cronogramas:detalhe", pk=cronograma.pk)


@login_required
def lista_view(request):
    cronogramas = Cronograma.objects.filter(usuario=request.user).order_by("-criado_em")
    return render(request, "cronogramas/lista.html", {"cronogramas": cronogramas})


@login_required
def criar_view(request):
    if request.method == "POST":
        form = CronogramaForm(request.POST)
        if form.is_valid():
            cronograma = form.save(commit=False)
            cronograma.usuario = request.user
            cronograma.tipo = Cronograma.Tipo.TEMA
            return _gerar_e_redirecionar(request, cronograma, form, "cronogramas/criar.html")
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
            cronograma.tema = f"Grade curricular de {cronograma.curso} ({cronograma.instituicao})"[:200]
            return _gerar_e_redirecionar(
                request, cronograma, form, "cronogramas/criar_faculdade.html"
            )
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
            return _gerar_e_redirecionar(
                request, cronograma, form, "cronogramas/criar_enem.html"
            )
    else:
        form = EnemForm()

    return render(request, "cronogramas/criar_enem.html", {"form": form})


@login_required
def sugestoes_view(request):
    resultados = buscar_sugestoes(request.GET.get("tipo", ""), request.GET.get("q", ""))
    return JsonResponse({"resultados": resultados})


@login_required
def detalhe_view(request, pk):
    cronograma = get_object_or_404(
        Cronograma.objects.prefetch_related("etapas"),
        pk=pk,
        usuario=request.user,
    )
    etapas = list(cronograma.etapas.all())
    return render(request, "cronogramas/detalhe.html", {
        "cronograma": cronograma,
        "etapas": etapas,
        "total": len(etapas),
        "concluidas": sum(1 for e in etapas if e.concluida),
    })


@login_required
@require_POST
def etapa_alternar_view(request, pk):
    etapa = get_object_or_404(
        EtapaCronograma.objects.select_related("cronograma"),
        pk=pk,
        cronograma__usuario=request.user,
    )
    etapa.concluida = not etapa.concluida
    etapa.save(update_fields=["concluida", "atualizado_em"])
    return redirect("cronogramas:detalhe", pk=etapa.cronograma_id)