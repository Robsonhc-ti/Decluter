from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import ProjetoMembro
from .forms import ProjetoForm
from boards.models import Board, Coluna


@login_required
def lista_view(request):
    participacoes = ProjetoMembro.objects.filter(usuario=request.user).select_related("projeto")
    return render(request, "projetos/lista.html", {"participacoes": participacoes})


@login_required
def criar_view(request):
    if request.method == "POST":
        form = ProjetoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                projeto = form.save()
                ProjetoMembro.objects.create(projeto=projeto, usuario=request.user, papel="admin")
                board = Board.objects.create(projeto=projeto)
                for ordem, nome in enumerate(["A fazer", "Fazendo", "Concluído"]):
                    Coluna.objects.create(board=board, nome=nome, ordem=ordem)
            return redirect("projetos:lista")
    else:
        form = ProjetoForm()

    return render(request, "projetos/criar.html", {"form": form})