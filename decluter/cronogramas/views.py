from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Cronograma, EtapaCronograma
from .forms import CronogramaForm


@login_required
def lista_view(request):
    cronogramas = Cronograma.objects.filter(usuario=request.user)
    return render(request, "cronogramas/lista.html", {"cronogramas": cronogramas})


@login_required
def criar_view(request):
    if request.method == "POST":
        form = CronogramaForm(request.POST)
        if form.is_valid():
            cronograma = form.save(commit=False)
            cronograma.usuario = request.user
            cronograma.save()

            # Versão simplificada por hoje — etapas fixas, sem chamar a IA ainda
            EtapaCronograma.objects.create(cronograma=cronograma, titulo=f"Introdução a {cronograma.tema}", ordem=1)
            EtapaCronograma.objects.create(cronograma=cronograma, titulo="Aprofundamento", ordem=2)
            EtapaCronograma.objects.create(cronograma=cronograma, titulo="Revisão e prática", ordem=3)

            return redirect("cronogramas:detalhe", pk=cronograma.pk)
    else:
        form = CronogramaForm()

    return render(request, "cronogramas/criar.html", {"form": form})


@login_required
def detalhe_view(request, pk):
    cronograma = Cronograma.objects.get(pk=pk, usuario=request.user)
    return render(request, "cronogramas/detalhe.html", {"cronograma": cronograma})